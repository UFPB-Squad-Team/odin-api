import unicodedata
from typing import Any

from src.domain.entities.municipio import (
    EducacaoStats,
    MunicipioCatalogItem,
    MunicipioResumo,
    SocioeconomicoStats,
)
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
            resumo = self._build_municipio_resumo(
                primary_doc,
                source="municipio_indicadores",
            )
            total_bairros = resumo.total_bairros
            if total_bairros <= 0:
                total_bairros = await self._count_official_neighborhoods(
                    municipio_id_ibge=municipio_id_ibge,
                    municipio_nome=resumo.municipio,
                )
            return resumo.model_copy(
                update={
                    "total_bairros": total_bairros,
                    "tem_bairros_oficiais": total_bairros > 0,
                }
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
        total_bairros = resumo.total_bairros
        if total_bairros <= 0:
            total_bairros = await self._count_official_neighborhoods(
                municipio_id_ibge=municipio_id_ibge,
                municipio_nome=resumo.municipio,
            )
        return resumo.model_copy(
            update={
                "total_bairros": total_bairros,
                "tem_bairros_oficiais": total_bairros > 0,
            }
        )

    async def _find_primary_municipio_doc(self, municipio_id_ibge: str) -> dict[str, Any] | None:
        candidates: list[Any] = [municipio_id_ibge]
        if municipio_id_ibge.isdigit():
            candidates.append(int(municipio_id_ibge))

        projection = {
            "_id": 1,
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
            "total_bairros": 1,
            "totalBairros": 1,
            "educacao.totalEscolas": 1,
            "educacao.totalMatriculas": 1,
            "educacao.totalBairros": 1,
            "educacao.pctComBiblioteca": 1,
            "educacao.pctComInternet": 1,
            "educacao.pctComLabInformatica": 1,
            "educacao.pctSemAcessibilidade": 1,
            "educacao.mediaIdebAnosIniciais": 1,
            "educacao.mediaIdebAnosFinals": 1,
            "socioeconomico.anoReferencia": 1,
            "socioeconomico.fonte": 1,
            "socioeconomico.populacao": 1,
            "socioeconomico.estruturaEtaria": 1,
            "socioeconomico.raca": 1,
            "socioeconomico.saneamento": 1,
            "socioeconomico.educacaoPopulacao": 1,
            "socioeconomico.familia": 1,
            "socioeconomico.mortalidade": 1,
            "socioeconomico.habitacao": 1,
        }

        for candidate in candidates:
            for field in (
                "municipioIdIbge",
                "municipio_id_ibge",
                "co_municipio",
                "idIbge",
            ):
                doc = await self.municipio_collection.find_one({field: candidate}, projection)
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

        educacao_doc = doc.get("educacao") if isinstance(doc.get("educacao"), dict) else {}
        educacao_payload: dict[str, Any] = dict(educacao_doc) if educacao_doc else {}
        educacao_payload.setdefault("totalEscolas", city.total_escolas)
        educacao_payload.setdefault("totalMatriculas", city.total_alunos)
        educacao_payload.setdefault("pctComBiblioteca", city.pct_com_biblioteca)
        educacao_payload.setdefault("pctComInternet", city.pct_com_internet)
        educacao_payload.setdefault("pctComLabInformatica", city.pct_com_lab_informatica)
        educacao_payload.setdefault("pctSemAcessibilidade", city.pct_sem_acessibilidade)
        educacao_payload.setdefault(
            "mediaIdebAnosIniciais",
            TerritorialAggregationMapper._as_float(
                TerritorialAggregationMapper._pick_nested(
                    doc,
                    ("educacao", "mediaIdebAnosIniciais"),
                    default=TerritorialAggregationMapper._pick(
                        doc,
                        "mediaIdebAnosIniciais",
                        default=None,
                    ),
                )
            ),
        )
        educacao_payload.setdefault(
            "mediaIdebAnosFinals",
            TerritorialAggregationMapper._as_float(
                TerritorialAggregationMapper._pick_nested(
                    doc,
                    ("educacao", "mediaIdebAnosFinals"),
                    default=TerritorialAggregationMapper._pick(
                        doc,
                        "mediaIdebAnosFinals",
                        default=None,
                    ),
                )
            ),
        )
        educacao = EducacaoStats.model_validate(educacao_payload)

        socioeconomico_doc = (
            doc.get("socioeconomico") if isinstance(doc.get("socioeconomico"), dict) else {}
        )
        socioeconomico_payload: dict[str, Any] = dict(socioeconomico_doc) if socioeconomico_doc else {}
        socioeconomico = SocioeconomicoStats.model_validate(socioeconomico_payload)

        total_bairros = TerritorialAggregationMapper._as_int(
            TerritorialAggregationMapper._pick_nested(
                doc,
                ("educacao", "totalBairros"),
                ("educacao", "total_bairros"),
                default=TerritorialAggregationMapper._pick(
                    doc,
                    "totalBairros",
                    "total_bairros",
                    default=0,
                ),
            )
        ) or 0

        return MunicipioResumo(
            municipioIdIbge=city.co_municipio,
            municipio=city.municipio,
            sg_uf=city.uf,
            total_bairros=total_bairros,
            tem_bairros_oficiais=total_bairros > 0,
            educacao=educacao,
            socioeconomico=socioeconomico,
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
    def _sort_key(value: str | None) -> str:
        if not value:
            return ""
        normalized = unicodedata.normalize("NFKD", value)
        return "".join(char for char in normalized if not unicodedata.combining(char)).casefold()
