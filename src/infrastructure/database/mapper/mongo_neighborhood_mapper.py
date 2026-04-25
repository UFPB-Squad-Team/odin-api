from typing import Any


class MongoNeighborhoodMapper:
    @staticmethod
    def _pick(doc: dict[str, Any], *keys: str, default: Any = None) -> Any:
        for key in keys:
            if key in doc and doc[key] is not None:
                return doc[key]
        return default

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _round_percentage(cls, value: Any) -> float | None:
        numeric_value = cls._as_float(value)
        if numeric_value is None:
            return None
        return round(numeric_value, 2)

    @classmethod
    def _extract_geometry(cls, doc: dict[str, Any]) -> dict[str, Any] | None:
        geometry = cls._pick(doc, "geometria", "geometry")
        if isinstance(geometry, dict) and geometry:
            return geometry

        centroid = cls._pick(doc, "centroide", "centroid", "localizacao")
        if isinstance(centroid, dict):
            coordinates = centroid.get("coordinates")
            if coordinates is not None:
                return {"type": centroid.get("type", "Point"), "coordinates": coordinates}

        lon = cls._as_float(cls._pick(doc, "longitude", "lon", "avg_lon"))
        lat = cls._as_float(cls._pick(doc, "latitude", "lat", "avg_lat"))
        if lon is not None and lat is not None:
            return {"type": "Point", "coordinates": [lon, lat]}

        return None

    @classmethod
    def from_doc(
        cls,
        doc: dict[str, Any],
        *,
        source: str,
        include_geometria: bool = False,
    ) -> dict[str, Any]:
        tem_bairro_official = bool(
            cls._pick(doc, "tem_bairro_official", "tem_bairro_oficial", default=True)
        )

        bairro = cls._pick(doc, "bairro", "nm_bairro", "nome_area")
        if not bairro and not tem_bairro_official:
            bairro = cls._pick(doc, "situacao")

        municipio_id_ibge = cls._pick(
            doc,
            "municipioIdIbge",
            "municipio_id_ibge",
            "co_municipio",
            "idIbge",
            default="",
        )

        total_matriculas = cls._pick(
            doc,
            "total_matriculas",
            "total_alunos",
            "qtd_alunos",
            default=0,
        )

        geometry = cls._extract_geometry(doc) if include_geometria else None

        return {
            "_id": str(doc.get("_id")) if doc.get("_id") else None,
            "municipio": str(cls._pick(doc, "municipio", "nm_municipio", default="")),
            "bairro": str(bairro or ""),
            "cd_bairro_ibge": cls._pick(doc, "cd_bairro_ibge", "cd_bairro"),
            "geometria": geometry,
            "municipioIdIbge": str(municipio_id_ibge),
            "pct_com_biblioteca": cls._round_percentage(cls._pick(doc, "pct_com_biblioteca")),
            "pct_com_internet": cls._round_percentage(cls._pick(doc, "pct_com_internet")),
            "pct_com_lab_informatica": cls._round_percentage(
                cls._pick(doc, "pct_com_lab_informatica")
            ),
            "pct_sem_acessibilidade": cls._round_percentage(
                cls._pick(doc, "pct_sem_acessibilidade")
            ),
            "sg_uf": cls._pick(doc, "sg_uf", "uf"),
            "total_escolas": int(
                cls._pick(doc, "total_escolas", "qtd_escolas", default=0)
            ),
            "total_matriculas": int(total_matriculas or 0),
            "tem_bairro_official": tem_bairro_official,
            "source": source,
        }