import re
import unicodedata
from typing import Any

from src.domain.repository.universal_search_repository import (
    IUniversalSearchRepository,
)


class MongoUniversalSearchRepository(IUniversalSearchRepository):
    _PT_COLLATION = {"locale": "pt", "strength": 1}

    def __init__(
        self,
        escolas_collection: Any,
        municipio_collection: Any,
        bairro_collection: Any,
    ):
        self._escolas = escolas_collection
        self._municipios = municipio_collection
        self._bairros = bairro_collection

    @staticmethod
    def _normalize_q(q: str) -> str:
        return " ".join(q.split()).strip()

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
    def _accent_insensitive_pattern(cls, value: str, *, prefix: bool = True) -> str:
        stripped = cls._strip_accents(value)
        core = "".join(cls._accent_class(char) for char in stripped)
        return f"^{core}" if prefix else core

    @staticmethod
    def _regex_clause(q: str, *, prefix: bool = True) -> dict[str, Any]:
        pattern = MongoUniversalSearchRepository._accent_insensitive_pattern(q, prefix=prefix)
        return {"$regex": pattern, "$options": "i"}

    @staticmethod
    def _municipio_id_clause(municipio_id: str) -> dict[str, Any]:
        values: list[str | int] = [municipio_id]
        if municipio_id.isdigit():
            values.append(int(municipio_id))
        return {
            "$or": [
                {"municipioIdIbge": {"$in": values}},
                {"municipio_id_ibge": {"$in": values}},
                {"co_municipio": {"$in": values}},
                {"idIbge": {"$in": values}},
            ]
        }

    @staticmethod
    def _sg_uf_clause(sg_uf: str) -> dict[str, Any]:
        normalized = sg_uf.upper()
        return {
            "$or": [
                {"sg_uf": normalized},
                {"uf": normalized},
                {"estadoSigla": normalized},
                {"estado_sigla": normalized},
            ]
        }

    @staticmethod
    def _merge_and_clauses(*clauses: dict[str, Any]) -> dict[str, Any]:
        filtered = [clause for clause in clauses if clause]
        if not filtered:
            return {}
        if len(filtered) == 1:
            return filtered[0]
        return {"$and": filtered}

    @staticmethod
    def _coordinates_projection() -> dict[str, int]:
        return {
            "localizacao": 1,
            "centroide": 1,
            "geometry": 1,
            "coordinates": 1,
            "avg_lon": 1,
            "avg_lat": 1,
            "longitude": 1,
            "latitude": 1,
            "lon": 1,
            "lat": 1,
        }

    async def search_schools(
        self,
        q: str,
        *,
        sg_uf: str | None = None,
        municipio_id: str | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        normalized_q = self._normalize_q(q)
        base_query: dict[str, Any] = {
            "escolaNome": self._regex_clause(normalized_q, prefix=True),
        }
        if sg_uf:
            base_query = self._merge_and_clauses(base_query, self._sg_uf_clause(sg_uf))
        if municipio_id:
            base_query = self._merge_and_clauses(base_query, self._municipio_id_clause(municipio_id))

        projection = {
            "_id": 1,
            "escolaIdInep": 1,
            "escolaNome": 1,
            "municipioNome": 1,
            "municipioIdIbge": 1,
            "municipio_id_ibge": 1,
            "co_municipio": 1,
            "idIbge": 1,
            "estadoSigla": 1,
            "dependenciaAdm": 1,
            "dependencia_adm": 1,
            "tipoLocalizacao": 1,
            "tipo_localizacao": 1,
            "endereco.bairro": 1,
        }
        projection.update(self._coordinates_projection())

        cursor = self._escolas.find(base_query, projection).collation(self._PT_COLLATION).sort(
            [("escolaNome", 1), ("escolaIdInep", 1)]
        ).limit(limit)
        docs = await cursor.to_list(length=limit)
        if docs:
            return docs

        fallback_query = {"escolaNome": self._regex_clause(normalized_q, prefix=False)}
        if sg_uf:
            fallback_query = self._merge_and_clauses(fallback_query, self._sg_uf_clause(sg_uf))
        if municipio_id:
            fallback_query = self._merge_and_clauses(fallback_query, self._municipio_id_clause(municipio_id))

        fallback_cursor = self._escolas.find(fallback_query, projection).collation(self._PT_COLLATION).sort(
            [("escolaNome", 1), ("escolaIdInep", 1)]
        ).limit(limit)
        return await fallback_cursor.to_list(length=limit)

    async def search_logradouros(
        self,
        q: str,
        *,
        sg_uf: str | None = None,
        municipio_id: str | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        normalized_q = self._normalize_q(q)

        async def run_pipeline(prefix: bool) -> list[dict[str, Any]]:
            match_stage: dict[str, Any] = {
                "endereco.logradouro": self._regex_clause(normalized_q, prefix=prefix),
                "localizacao.type": "Point",
            }
            if sg_uf:
                match_stage = self._merge_and_clauses(match_stage, self._sg_uf_clause(sg_uf))
            if municipio_id:
                match_stage = self._merge_and_clauses(match_stage, self._municipio_id_clause(municipio_id))

            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": {
                            "logradouro": "$endereco.logradouro",
                            "municipioNome": "$municipioNome",
                            "municipioIdIbge": "$municipioIdIbge",
                            "estadoSigla": "$estadoSigla",
                        },
                        "bairros": {"$addToSet": "$endereco.bairro"},
                        "count": {"$sum": 1},
                        "avg_lon": {"$avg": {"$arrayElemAt": ["$localizacao.coordinates", 0]}},
                        "avg_lat": {"$avg": {"$arrayElemAt": ["$localizacao.coordinates", 1]}},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "logradouro": "$_id.logradouro",
                        "municipioNome": "$_id.municipioNome",
                        "municipioIdIbge": "$_id.municipioIdIbge",
                        "estadoSigla": "$_id.estadoSigla",
                        "bairros": 1,
                        "count": 1,
                        "avg_lon": 1,
                        "avg_lat": 1,
                        "coordinates": ["$avg_lon", "$avg_lat"],
                    }
                },
                {"$match": {"logradouro": {"$type": "string", "$ne": ""}}},
                {"$sort": {"count": -1, "logradouro": 1}},
                {"$limit": limit},
            ]
            return await self._escolas.aggregate(pipeline).to_list(length=limit)

        docs = await run_pipeline(prefix=True)
        if docs:
            return docs
        return await run_pipeline(prefix=False)

    async def search_by_cep(
        self,
        q: str,
        *,
        sg_uf: str | None = None,
        municipio_id: str | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        normalized_q = re.sub(r"\D", "", self._normalize_q(q))

        async def run_pipeline(prefix: bool) -> list[dict[str, Any]]:
            match_query: dict[str, Any] = {
                "endereco.cep": self._regex_clause(normalized_q, prefix=prefix),
            }
            if sg_uf:
                match_query = self._merge_and_clauses(match_query, self._sg_uf_clause(sg_uf))
            if municipio_id:
                match_query = self._merge_and_clauses(match_query, self._municipio_id_clause(municipio_id))

            pipeline = [
                {"$match": match_query},
                {
                    "$group": {
                        "_id": "$endereco.cep",
                        "cep": {"$first": "$endereco.cep"},
                        "escolaNome": {"$first": "$escolaNome"},
                        "logradouro": {"$first": "$endereco.logradouro"},
                        "bairro": {"$first": "$endereco.bairro"},
                        "municipioNome": {"$first": "$municipioNome"},
                        "municipioIdIbge": {"$first": "$municipioIdIbge"},
                        "estadoSigla": {"$first": "$estadoSigla"},
                        "count": {"$sum": 1},
                        "avg_lon": {"$avg": {"$arrayElemAt": ["$localizacao.coordinates", 0]}},
                        "avg_lat": {"$avg": {"$arrayElemAt": ["$localizacao.coordinates", 1]}},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "cep": 1,
                        "escolaNome": 1,
                        "logradouro": 1,
                        "bairro": 1,
                        "municipioNome": 1,
                        "municipioIdIbge": 1,
                        "estadoSigla": 1,
                        "count": 1,
                        "avg_lon": 1,
                        "avg_lat": 1,
                        "coordinates": ["$avg_lon", "$avg_lat"],
                    }
                },
                {"$sort": {"count": -1, "cep": 1}},
                {"$limit": limit},
            ]
            return await self._escolas.aggregate(pipeline).to_list(length=limit)

        docs = await run_pipeline(prefix=True)
        if docs:
            return docs
        return await run_pipeline(prefix=False)

    async def search_municipios(
        self,
        q: str,
        *,
        sg_uf: str | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        normalized_q = self._normalize_q(q)
        base_query: dict[str, Any] = {
            "$or": [
                {"municipio": self._regex_clause(normalized_q, prefix=True)},
                {"nm_municipio": self._regex_clause(normalized_q, prefix=True)},
                {"municipioNome": self._regex_clause(normalized_q, prefix=True)},
            ]
        }
        if sg_uf:
            base_query = self._merge_and_clauses(base_query, self._sg_uf_clause(sg_uf))

        projection = {
            "_id": 1,
            "co_municipio": 1,
            "municipioIdIbge": 1,
            "municipio_id_ibge": 1,
            "idIbge": 1,
            "municipio": 1,
            "nm_municipio": 1,
            "municipioNome": 1,
            "sg_uf": 1,
            "uf": 1,
            "estadoSigla": 1,
            "estado_sigla": 1,
            "socioeconomico": 1,
            "centroide": 1,
            "geometry": 1,
            **self._coordinates_projection(),
        }

        cursor = self._municipios.find(base_query, projection).collation(self._PT_COLLATION).sort(
            [("municipio", 1), ("nm_municipio", 1), ("municipioNome", 1)]
        ).limit(limit)
        docs = await cursor.to_list(length=limit)
        if docs:
            return docs

        fallback_query = {
            "$or": [
                {"municipio": self._regex_clause(normalized_q, prefix=False)},
                {"nm_municipio": self._regex_clause(normalized_q, prefix=False)},
                {"municipioNome": self._regex_clause(normalized_q, prefix=False)},
            ]
        }
        if sg_uf:
            fallback_query = self._merge_and_clauses(fallback_query, self._sg_uf_clause(sg_uf))

        fallback_cursor = self._municipios.find(fallback_query, projection).collation(self._PT_COLLATION).sort(
            [("municipio", 1), ("nm_municipio", 1), ("municipioNome", 1)]
        ).limit(limit)
        return await fallback_cursor.to_list(length=limit)

    async def search_bairros(
        self,
        q: str,
        *,
        sg_uf: str | None = None,
        municipio_id: str | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        normalized_q = self._normalize_q(q)
        base_query: dict[str, Any] = {
            "$or": [
                {"bairro": self._regex_clause(normalized_q, prefix=True)},
                {"nm_bairro": self._regex_clause(normalized_q, prefix=True)},
                {"nome_area": self._regex_clause(normalized_q, prefix=True)},
            ]
        }
        if sg_uf:
            base_query = self._merge_and_clauses(base_query, self._sg_uf_clause(sg_uf))
        if municipio_id:
            base_query = self._merge_and_clauses(base_query, self._municipio_id_clause(municipio_id))

        projection = {
            "_id": 1,
            "cd_bairro_ibge": 1,
            "cd_bairro": 1,
            "bairro": 1,
            "nm_bairro": 1,
            "nome_area": 1,
            "municipio": 1,
            "nm_municipio": 1,
            "municipioNome": 1,
            "municipioIdIbge": 1,
            "municipio_id_ibge": 1,
            "co_municipio": 1,
            "sg_uf": 1,
            "uf": 1,
            "estadoSigla": 1,
            "estado_sigla": 1,
            **self._coordinates_projection(),
        }

        cursor = self._bairros.find(base_query, projection).collation(self._PT_COLLATION).sort(
            [("bairro", 1), ("nm_bairro", 1), ("nome_area", 1)]
        ).limit(limit)
        docs = await cursor.to_list(length=limit)
        if docs:
            return docs

        fallback_query = {
            "$or": [
                {"bairro": self._regex_clause(normalized_q, prefix=False)},
                {"nm_bairro": self._regex_clause(normalized_q, prefix=False)},
                {"nome_area": self._regex_clause(normalized_q, prefix=False)},
            ]
        }
        if sg_uf:
            fallback_query = self._merge_and_clauses(fallback_query, self._sg_uf_clause(sg_uf))
        if municipio_id:
            fallback_query = self._merge_and_clauses(fallback_query, self._municipio_id_clause(municipio_id))

        fallback_cursor = self._bairros.find(fallback_query, projection).collation(self._PT_COLLATION).sort(
            [("bairro", 1), ("nm_bairro", 1), ("nome_area", 1)]
        ).limit(limit)
        return await fallback_cursor.to_list(length=limit)