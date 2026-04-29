import unicodedata
from typing import Any

from src.domain.entities.municipio import MunicipioCatalogItem, MunicipioResumo
from src.domain.repository.municipio_repository import IMunicipioRepository
from src.infrastructure.database.mapper.territorial_aggregation_mapper import (
    TerritorialAggregationMapper,
)
from src.infrastructure.database.repository.mongo_territorial_aggregation_repository import (
    MongoTerritorialAggregationRepository,
)


class MongoMunicipioRepository(MongoTerritorialAggregationRepository, IMunicipioRepository):
    def __init__(
        self,
        municipio_collection: Any,
        bairro_collection: Any,
        setor_collection: Any,
    ):
        super().__init__(municipio_collection, bairro_collection, setor_collection)

    async def list_municipios(
        self,
        sg_uf: str | None = None,
    ) -> list[MunicipioCatalogItem]:
        normalized_uf = sg_uf.upper() if sg_uf else None

        query: dict[str, Any] = {}
        if normalized_uf:
            query = {
                "$or": [
                    {"sg_uf": normalized_uf},
                    {"uf": normalized_uf},
                    {"estado_sigla": normalized_uf},
                    {"estadoSigla": normalized_uf},
                ]
            }

        projection = {
            "co_municipio": 1,
            "municipioIdIbge": 1,
            "municipio_id_ibge": 1,
            "idIbge": 1,
            "municipio": 1,
            "nm_municipio": 1,
            "municipio_nome": 1,
            "municipioNome": 1,
            "sg_uf": 1,
            "uf": 1,
            "estado_sigla": 1,
            "estadoSigla": 1,
        }

        docs = await self.municipio_collection.find(query, projection).to_list(length=None)
        items = [
            item
            for item in (
                self._map_municipio_catalog_item(doc)
                for doc in docs
            )
            if item is not None
        ]

        items.sort(key=lambda item: self._sort_key(item.nome))
        return items

    async def get_resumo(
        self,
        municipio_id_ibge: str,
    ) -> MunicipioResumo | None:
        primary_doc = await self._find_primary_municipio_doc(municipio_id_ibge)
        if primary_doc:
            return self._build_municipio_resumo(
                primary_doc,
                source="municipio_indicadores",
            )

        fallback_docs = await self._aggregate_city_from_setor(
            co_municipio=municipio_id_ibge,
            sg_uf=None,
        )
        if not fallback_docs:
            return None

        resumo = self._build_municipio_resumo(
            fallback_docs[0],
            source="setor_indicadores",
        )
        return resumo

    async def _find_primary_municipio_doc(self, municipio_id_ibge: str) -> dict[str, Any] | None:
        candidates: list[Any] = [municipio_id_ibge]
        if municipio_id_ibge.isdigit():
            candidates.append(int(municipio_id_ibge))

        for candidate in candidates:
            for field in (
                "municipioIdIbge",
                "municipio_id_ibge",
                "co_municipio",
                "idIbge",
            ):
                doc = await self.municipio_collection.find_one({field: candidate})
                if doc:
                    return doc

        return None

    async def _count_official_neighborhoods(
        self,
        *,
        municipio_id_ibge: str,
        municipio_nome: str | None = None,
    ) -> int:
        code_query = self._municipio_match_query(municipio_id_ibge)
        code_count = await self.bairro_collection.count_documents(code_query)
        if code_count > 0:
            return code_count

        if not municipio_nome:
            return 0

        name_candidates = self._municipio_name_candidates(municipio_nome)
        if not name_candidates:
            return 0

        name_query = {
            "$or": [
                {"municipio": candidate} for candidate in name_candidates
            ]
            + [
                {"nm_municipio": candidate} for candidate in name_candidates
            ]
            + [
                {"municipio_nome": candidate} for candidate in name_candidates
            ]
            + [
                {"municipioNome": candidate} for candidate in name_candidates
            ]
        }
        return await self.bairro_collection.count_documents(name_query)

    async def _aggregate_city_from_setor(
        self,
        *,
        co_municipio: str,
        sg_uf: str | None,
    ) -> list[dict[str, Any]]:
        match_conditions: list[dict[str, Any]] = [self._municipio_match_query(co_municipio)]
        if sg_uf:
            match_conditions.append(
                {
                    "$or": [
                        {"sg_uf": sg_uf},
                        {"uf": sg_uf},
                        {"estado_sigla": sg_uf},
                        {"estadoSigla": sg_uf},
                    ]
                }
            )

        pipeline = [
            {"$match": {"$and": match_conditions}},
            {
                "$project": {
                    "co_municipio": {"$ifNull": ["$co_municipio", "$municipioIdIbge"]},
                    "municipio": {"$ifNull": ["$nm_municipio", "$municipio"]},
                    "uf": {"$ifNull": ["$sg_uf", "$uf"]},
                    "total_escolas": {
                        "$ifNull": ["$total_escolas", {"$ifNull": ["$qtd_escolas", 0]}]
                    },
                    "total_alunos": {
                        "$ifNull": [
                            "$total_alunos",
                            {"$ifNull": ["$total_matriculas", {"$ifNull": ["$qtd_alunos", 0]}]},
                        ]
                    },
                    "mediaIdebAnosIniciais": {
                        "$ifNull": [
                            "$educacao.mediaIdebAnosIniciais",
                            {"$ifNull": ["$mediaIdebAnosIniciais", "$avg_ideb"]},
                        ]
                    },
                    "pct_com_biblioteca": "$pct_com_biblioteca",
                    "pct_com_internet": "$pct_com_internet",
                    "pct_com_lab_informatica": "$pct_com_lab_informatica",
                    "pct_sem_acessibilidade": "$pct_sem_acessibilidade",
                    "socioeconomico": "$socioeconomico",
                    "educacao": "$educacao",
                    "lon": {
                        "$ifNull": [
                            "$longitude",
                            {
                                "$ifNull": [
                                    "$lon",
                                    {
                                        "$ifNull": [
                                            {"$arrayElemAt": ["$centroide.coordinates", 0]},
                                            {"$arrayElemAt": ["$geometria.coordinates.0.0.0", 0]},
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                    "lat": {
                        "$ifNull": [
                            "$latitude",
                            {
                                "$ifNull": [
                                    "$lat",
                                    {
                                        "$ifNull": [
                                            {"$arrayElemAt": ["$centroide.coordinates", 1]},
                                            {"$arrayElemAt": ["$geometria.coordinates.0.0.0", 1]},
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                }
            },
            {
                "$group": {
                    "_id": "$co_municipio",
                    "co_municipio": {"$first": "$co_municipio"},
                    "municipio": {"$first": "$municipio"},
                    "uf": {"$first": "$uf"},
                    "total_escolas": {"$sum": "$total_escolas"},
                    "total_alunos": {"$sum": "$total_alunos"},
                    "mediaIdebAnosIniciais": {"$avg": "$mediaIdebAnosIniciais"},
                    "pct_com_biblioteca": {"$avg": "$pct_com_biblioteca"},
                    "pct_com_internet": {"$avg": "$pct_com_internet"},
                    "pct_com_lab_informatica": {"$avg": "$pct_com_lab_informatica"},
                    "pct_sem_acessibilidade": {"$avg": "$pct_sem_acessibilidade"},
                    "avg_lon": {"$avg": "$lon"},
                    "avg_lat": {"$avg": "$lat"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "co_municipio": 1,
                    "municipio": 1,
                    "uf": 1,
                    "total_escolas": 1,
                    "total_alunos": 1,
                    "mediaIdebAnosIniciais": 1,
                    "pct_com_biblioteca": 1,
                    "pct_com_internet": 1,
                    "pct_com_lab_informatica": 1,
                    "pct_sem_acessibilidade": 1,
                    "avg_lon": 1,
                    "avg_lat": 1,
                }
            },
        ]

        return await self.setor_collection.aggregate(pipeline).to_list(length=None)

    def _build_municipio_resumo(
        self,
        doc: dict[str, Any],
        *,
        source: str,
    ) -> MunicipioResumo:
        city = TerritorialAggregationMapper.city_from_doc(
            doc,
            source=source,
            include_geometria=False,
        )

        total_bairros = TerritorialAggregationMapper._as_int(
            TerritorialAggregationMapper._pick_nested(
                doc,
                ("educacao", "totalBairros"),
                default=TerritorialAggregationMapper._pick(
                    doc,
                    "totalBairros",
                    "total_bairros",
                    default=0,
                ),
            )
        ) or 0

        media_ideb_anos_iniciais = TerritorialAggregationMapper._as_float(
            TerritorialAggregationMapper._pick_nested(
                doc,
                ("educacao", "mediaIdebAnosIniciais"),
                default=TerritorialAggregationMapper._pick(
                    doc,
                    "mediaIdebAnosIniciais",
                    "avg_ideb",
                    "ideb_medio",
                    "ideb",
                    default=None,
                ),
            )
        )

        return MunicipioResumo(
            municipioIdIbge=city.co_municipio,
            municipio=city.municipio,
            sg_uf=city.uf,
            total_escolas=city.total_escolas,
            total_matriculas=city.total_alunos,
            total_bairros=total_bairros,
            pct_com_biblioteca=city.pct_com_biblioteca,
            pct_com_internet=city.pct_com_internet,
            pct_com_lab_informatica=city.pct_com_lab_informatica,
            pct_sem_acessibilidade=city.pct_sem_acessibilidade,
            mediaIdebAnosIniciais=media_ideb_anos_iniciais,
            tem_bairros_oficiais=total_bairros > 0,
            source=source,
        )

    @staticmethod
    def _municipio_match_query(municipio_id_ibge: str) -> dict[str, Any]:
        candidates: list[Any] = [municipio_id_ibge]
        if municipio_id_ibge.isdigit():
            candidates.append(int(municipio_id_ibge))

        return {
            "$or": [
                {"municipioIdIbge": candidate} for candidate in candidates
            ]
            + [
                {"municipio_id_ibge": candidate} for candidate in candidates
            ]
            + [
                {"co_municipio": candidate} for candidate in candidates
            ]
            + [
                {"idIbge": candidate} for candidate in candidates
            ]
        }

    @staticmethod
    def _municipio_name_candidates(municipio_nome: str) -> list[str]:
        normalized = municipio_nome.strip()
        if not normalized:
            return []

        candidates = {normalized}
        ascii_name = unicodedata.normalize("NFKD", normalized)
        ascii_name = "".join(
            char for char in ascii_name if not unicodedata.combining(char)
        )
        if ascii_name:
            candidates.add(ascii_name)

        return [candidate for candidate in candidates if candidate]

    @staticmethod
    def _resolve_municipality_name(doc: dict[str, Any]) -> str | None:
        name = TerritorialAggregationMapper._pick(
            doc,
            "municipio",
            "nm_municipio",
            "municipio_nome",
            "municipioNome",
            default=None,
        )
        return str(name) if name else None
