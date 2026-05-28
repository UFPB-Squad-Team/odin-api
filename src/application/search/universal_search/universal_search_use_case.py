import asyncio
import re
import unicodedata
from typing import Any

from src.application.search.universal_search.universal_search_dto import (
    SearchResultItem,
    UniversalSearchInputDTO,
    UniversalSearchOutputDTO,
)
from src.domain.repository.universal_search_repository import (
    IUniversalSearchRepository,
)


class UniversalSearchUseCase:
    def __init__(self, repository: IUniversalSearchRepository):
        self._repository = repository

    async def execute(self, dto: UniversalSearchInputDTO) -> UniversalSearchOutputDTO:
        query = dto.q.strip()
        normalized_query = self._normalize_text(query)
        clean_digits = re.sub(r"\D", "", query)
        is_cep_query = len(clean_digits) == 8
        source_limit = max(dto.limit, 20)

        tasks: list[asyncio.Task[list[SearchResultItem]]] = []

        if is_cep_query:
            tasks.append(asyncio.create_task(self._search_cep(dto, source_limit)))
        else:
            tasks.append(asyncio.create_task(self._search_schools(dto, source_limit)))
            tasks.append(asyncio.create_task(self._search_logradouros(dto, source_limit)))
            tasks.append(asyncio.create_task(self._search_bairros(dto, source_limit)))
            tasks.append(asyncio.create_task(self._search_municipios(dto, source_limit)))
            if any(char.isdigit() for char in query):
                tasks.append(asyncio.create_task(self._search_cep(dto, source_limit)))

        all_results = await asyncio.gather(*tasks)

        merged: list[SearchResultItem] = []
        seen_ids: set[str] = set()

        for result_list in all_results:
            for item in result_list:
                if item.id in seen_ids:
                    continue
                seen_ids.add(item.id)
                merged.append(item)

        if not is_cep_query:
            merged.sort(
                key=lambda item: self._ranking_key(item, normalized_query),
                reverse=True,
            )

        final_results = merged[: dto.limit]
        return UniversalSearchOutputDTO(
            results=final_results,
            total=len(final_results),
            query=query,
        )

    async def _search_schools(
        self,
        dto: UniversalSearchInputDTO,
        limit: int,
    ) -> list[SearchResultItem]:
        docs = await self._repository.search_schools(
            dto.q,
            sg_uf=dto.sg_uf,
            municipio_id=dto.municipio_id,
            limit=limit,
        )
        return [item for doc in docs if (item := self._build_school_item(doc)) is not None]

    async def _search_logradouros(
        self,
        dto: UniversalSearchInputDTO,
        limit: int,
    ) -> list[SearchResultItem]:
        docs = await self._repository.search_logradouros(
            dto.q,
            sg_uf=dto.sg_uf,
            municipio_id=dto.municipio_id,
            limit=limit,
        )
        return [item for doc in docs if (item := self._build_logradouro_item(doc)) is not None]

    async def _search_cep(
        self,
        dto: UniversalSearchInputDTO,
        limit: int,
    ) -> list[SearchResultItem]:
        docs = await self._repository.search_by_cep(
            dto.q,
            sg_uf=dto.sg_uf,
            municipio_id=dto.municipio_id,
            limit=limit,
        )
        return [item for doc in docs if (item := self._build_cep_item(doc)) is not None]

    async def _search_municipios(
        self,
        dto: UniversalSearchInputDTO,
        limit: int,
    ) -> list[SearchResultItem]:
        docs = await self._repository.search_municipios(
            dto.q,
            sg_uf=dto.sg_uf,
            limit=limit,
        )
        return [item for doc in docs if (item := self._build_municipio_item(doc)) is not None]

    async def _search_bairros(
        self,
        dto: UniversalSearchInputDTO,
        limit: int,
    ) -> list[SearchResultItem]:
        docs = await self._repository.search_bairros(
            dto.q,
            sg_uf=dto.sg_uf,
            municipio_id=dto.municipio_id,
            limit=limit,
        )
        return [item for doc in docs if (item := self._build_bairro_item(doc)) is not None]

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
        return re.sub(r"\s+", " ", without_accents).casefold().strip()

    def _match_strength(self, item: SearchResultItem, normalized_query: str) -> int:
        label = self._normalize_text(item.label)
        subtitle = self._normalize_text(item.subtitle)

        if not normalized_query:
            return 0
        if label == normalized_query:
            return 3000
        if label.startswith(normalized_query):
            return 2200
        if normalized_query in label:
            return 1500
        if normalized_query in subtitle:
            return 600
        return 0

    @staticmethod
    def _kind_priority(kind: str) -> int:
        return {
            "escola": 5,
            "logradouro": 4,
            "bairro": 3,
            "municipio": 2,
            "cep": 1,
        }.get(kind, 0)

    def _ranking_key(self, item: SearchResultItem, normalized_query: str) -> tuple[int, int, int]:
        return (
            self._match_strength(item, normalized_query),
            self._kind_priority(item.kind),
            len(item.label),
        )

    @staticmethod
    def _pick(doc: dict[str, Any], *keys: str, default: Any = None) -> Any:
        for key in keys:
            if key in doc and doc[key] is not None:
                return doc[key]
        return default

    @classmethod
    def _pick_nested(cls, doc: dict[str, Any], path: tuple[str, ...], default: Any = None) -> Any:
        current: Any = doc
        for key in path:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
        return default if current is None else current

    @staticmethod
    def _as_str(value: Any, default: str = "") -> str:
        if value is None:
            return default
        return str(value)

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _first_coordinate_pair(cls, value: Any) -> tuple[float, float] | None:
        if isinstance(value, dict):
            coordinates = value.get("coordinates")
            if coordinates is not None:
                return cls._first_coordinate_pair(coordinates)
            return None

        if isinstance(value, (list, tuple)):
            if len(value) >= 2:
                lon = cls._as_float(value[0])
                lat = cls._as_float(value[1])
                if lon is not None and lat is not None:
                    return (lon, lat)

            for item in value:
                pair = cls._first_coordinate_pair(item)
                if pair is not None:
                    return pair

        return None

    @classmethod
    def _extract_coordinates(cls, doc: dict[str, Any]) -> tuple[float, float] | None:
        coordinates = cls._first_coordinate_pair(doc.get("coordinates"))
        if coordinates is not None:
            return coordinates

        for path in (
            ("localizacao", "coordinates"),
            ("centroide", "coordinates"),
            ("geometria", "coordinates"),
            ("geometry", "coordinates"),
        ):
            nested = cls._pick_nested(doc, path)
            coordinates = cls._first_coordinate_pair(nested)
            if coordinates is not None:
                return coordinates

        lon = cls._as_float(cls._pick(doc, "avg_lon", "longitude", "lon"))
        lat = cls._as_float(cls._pick(doc, "avg_lat", "latitude", "lat"))
        if lon is not None and lat is not None:
            return (lon, lat)
        return None

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", without_accents).strip("-").lower()
        return slug or "item"

    @staticmethod
    def _strip_accents(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        return "".join(char for char in normalized if not unicodedata.combining(char))

    @classmethod
    def _accent_class(cls, char: str) -> str:
        variants = {
            "a": "aAáÁàÀâÂãÃäÄ",
            "c": "cCçÇ",
            "e": "eEéÉèÈêÊëË",
            "i": "iIíÍìÌîÎïÏ",
            "n": "nNñÑ",
            "o": "oOóÓòÒôÔõÕöÖ",
            "u": "uUúÚùÙûÛüÜ",
        }
        return f"[{re.escape(variants[char.lower()])}]" if char.lower() in variants else re.escape(char)

    @classmethod
    def _accent_insensitive_pattern(cls, value: str) -> str:
        stripped = cls._strip_accents(value)
        return "".join(cls._accent_class(char) for char in stripped)

    @classmethod
    def _build_school_item(cls, doc: dict[str, Any]) -> SearchResultItem | None:
        coordinates = cls._extract_coordinates(doc)
        if coordinates is None:
            return None

        school_id = cls._pick(doc, "escolaIdInep", "escola_id_inep", "id", "_id")
        label = cls._as_str(cls._pick(doc, "escolaNome", "escola_nome"))
        municipio_id = cls._as_str(
            cls._pick(doc, "municipioIdIbge", "municipio_id_ibge", "co_municipio", "idIbge")
        )
        municipio_nome = cls._as_str(cls._pick(doc, "municipioNome", "municipio_nome", "municipio", "nm_municipio"))
        bairro = cls._as_str(cls._pick_nested(doc, ("endereco", "bairro"), default=cls._pick(doc, "bairro")))

        subtitle_parts = [part for part in [municipio_nome, bairro] if part]
        subtitle = " • ".join(subtitle_parts)

        return SearchResultItem(
            id=cls._as_str(school_id, default=label or "school"),
            kind="escola",
            label=label,
            subtitle=subtitle,
            coordinates=coordinates,
            municipio_id_ibge=municipio_id,
            metadata={
                "bairro": bairro,
                "municipioNome": municipio_nome,
                "dependenciaAdm": cls._pick(doc, "dependenciaAdm", "dependencia_adm"),
                "tipoLocalizacao": cls._pick(doc, "tipoLocalizacao", "tipo_localizacao"),
            },
        )

    @classmethod
    def _build_logradouro_item(cls, doc: dict[str, Any]) -> SearchResultItem | None:
        coordinates = cls._extract_coordinates(doc)
        if coordinates is None:
            return None

        logradouro = cls._as_str(cls._pick(doc, "logradouro", "endereco.logradouro"))
        municipio_id = cls._as_str(cls._pick(doc, "municipioIdIbge", "municipio_id_ibge", "co_municipio", "idIbge"))
        municipio_nome = cls._as_str(cls._pick(doc, "municipioNome", "municipio_nome", "municipio", "nm_municipio"))
        bairros = doc.get("bairros") if isinstance(doc.get("bairros"), list) else []
        count = cls._pick(doc, "count", default=0)

        subtitle_parts = [part for part in [municipio_nome, f"{count} escolas" if count else ""] if part]
        subtitle = " • ".join(subtitle_parts)

        return SearchResultItem(
            id=f"logradouro:{cls._slugify(logradouro)}-{municipio_id or 'sem-municipio'}",
            kind="logradouro",
            label=logradouro,
            subtitle=subtitle,
            coordinates=coordinates,
            municipio_id_ibge=municipio_id,
            metadata={
                "bairros": bairros,
                "count": count,
            },
        )

    @classmethod
    def _build_cep_item(cls, doc: dict[str, Any]) -> SearchResultItem | None:
        coordinates = cls._extract_coordinates(doc)
        if coordinates is None:
            return None

        cep = cls._as_str(cls._pick(doc, "cep", "_id"))
        municipio_id = cls._as_str(cls._pick(doc, "municipioIdIbge", "municipio_id_ibge", "co_municipio", "idIbge"))
        municipio_nome = cls._as_str(cls._pick(doc, "municipioNome", "municipio_nome", "municipio", "nm_municipio"))
        logradouro = cls._as_str(cls._pick(doc, "logradouro", "endereco.logradouro"))
        bairro = cls._as_str(cls._pick(doc, "bairro", "endereco.bairro"))
        count = cls._pick(doc, "count", default=0)

        subtitle_parts = [part for part in [municipio_nome, logradouro, bairro] if part]
        subtitle = " • ".join(subtitle_parts)

        clean_cep = re.sub(r"\D", "", cep)
        return SearchResultItem(
            id=f"cep:{clean_cep or cep}",
            kind="cep",
            label=cep,
            subtitle=subtitle,
            coordinates=coordinates,
            municipio_id_ibge=municipio_id,
            metadata={
                "logradouro": logradouro,
                "bairro": bairro,
                "count": count,
            },
        )

    @classmethod
    def _build_municipio_item(cls, doc: dict[str, Any]) -> SearchResultItem | None:
        coordinates = cls._extract_coordinates(doc)
        if coordinates is None:
            return None

        municipio_id = cls._as_str(cls._pick(doc, "co_municipio", "municipioIdIbge", "municipio_id_ibge", "idIbge"))
        municipio_nome = cls._as_str(cls._pick(doc, "municipio", "nm_municipio", "municipioNome", "municipio_nome"))
        uf = cls._as_str(cls._pick(doc, "sg_uf", "uf", "estadoSigla", "estado_sigla"))
        population = cls._pick_nested(doc, ("socioeconomico", "populacao", "total"))

        subtitle_parts = [part for part in [uf, f"População: {population}" if population is not None else ""] if part]
        subtitle = " • ".join(subtitle_parts)

        return SearchResultItem(
            id=f"municipio:{municipio_id or cls._slugify(municipio_nome)}",
            kind="municipio",
            label=municipio_nome,
            subtitle=subtitle,
            coordinates=coordinates,
            municipio_id_ibge=municipio_id,
            metadata={
                "uf": uf,
                "population": population,
            },
        )

    @classmethod
    def _build_bairro_item(cls, doc: dict[str, Any]) -> SearchResultItem | None:
        coordinates = cls._extract_coordinates(doc)
        if coordinates is None:
            return None

        bairro = cls._as_str(cls._pick(doc, "bairro", "bairro_oficial", "nm_bairro", "nome_area", "situacao"))
        municipio_id = cls._as_str(cls._pick(doc, "municipioIdIbge", "municipio_id_ibge", "co_municipio", "idIbge"))
        municipio_nome = cls._as_str(cls._pick(doc, "municipio", "nm_municipio", "municipioNome", "municipio_nome"))
        bairro_code = cls._pick(doc, "cd_bairro_ibge", "cd_bairro")

        subtitle = " • ".join([part for part in [municipio_nome, municipio_id] if part])

        if bairro_code is not None:
            item_id = f"bairro:{bairro_code}"
        else:
            item_id = f"bairro:{cls._slugify(bairro)}-{municipio_id or 'sem-municipio'}"

        return SearchResultItem(
            id=cls._as_str(item_id),
            kind="bairro",
            label=bairro,
            subtitle=subtitle,
            coordinates=coordinates,
            municipio_id_ibge=municipio_id,
            metadata={
                "cd_bairro_ibge": bairro_code,
                "municipioNome": municipio_nome,
            },
        )