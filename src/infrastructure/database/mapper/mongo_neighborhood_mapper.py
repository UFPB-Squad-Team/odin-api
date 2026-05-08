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

    @staticmethod
    def _pick_nested(doc: dict[str, Any], *paths: tuple[str, ...], default: Any = None) -> Any:
        for path in paths:
            current: Any = doc
            found = True
            for key in path:
                if isinstance(current, dict) and key in current and current[key] is not None:
                    current = current[key]
                else:
                    found = False
                    break
            if found:
                return current
        return default

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

        cd_setor = cls._pick(doc, "cd_setor", "co_setor", "setor", "id_setor")

        total_matriculas = cls._pick(
            doc,
            "total_matriculas",
            "total_alunos",
            "qtd_alunos",
            default=0,
        )

        geometry = cls._extract_geometry(doc) if include_geometria else None

        tem_oficial = bool(cls._pick(doc, "tem_bairro_official", "tem_bairro_oficial", default=True))
        nivel = "setor" if source == "setor_indicadores" else "bairro"

        socioeconomico = doc.get("socioeconomico") if isinstance(doc.get("socioeconomico"), dict) else None
        educacao = doc.get("educacao") if isinstance(doc.get("educacao"), dict) else None

        total_escolas = int(
            cls._pick_nested(
                doc,
                ("educacao", "totalEscolas"),
                ("educacao", "total_escolas"),
                default=cls._pick(doc, "total_escolas", "qtd_escolas", default=0),
            )
            or 0
        )
        total_matriculas = int(
            cls._pick_nested(
                doc,
                ("educacao", "totalMatriculas"),
                ("educacao", "total_matriculas"),
                default=total_matriculas,
            )
            or 0
        )

        pct_com_biblioteca = cls._round_percentage(
            cls._pick_nested(
                doc,
                ("educacao", "pctComBiblioteca"),
                ("educacao", "pct_com_biblioteca"),
                default=cls._pick(doc, "pct_com_biblioteca"),
            )
        )
        pct_com_internet = cls._round_percentage(
            cls._pick_nested(
                doc,
                ("educacao", "pctComInternet"),
                ("educacao", "pct_com_internet"),
                default=cls._pick(doc, "pct_com_internet"),
            )
        )
        pct_com_lab_informatica = cls._round_percentage(
            cls._pick_nested(
                doc,
                ("educacao", "pctComLabInformatica"),
                ("educacao", "pct_com_lab_informatica"),
                default=cls._pick(doc, "pct_com_lab_informatica"),
            )
        )
        pct_sem_acessibilidade = cls._round_percentage(
            cls._pick_nested(
                doc,
                ("educacao", "pctSemAcessibilidade"),
                ("educacao", "pct_sem_acessibilidade"),
                default=cls._pick(doc, "pct_sem_acessibilidade"),
            )
        )

        return {
            "_id": str(doc.get("_id")) if doc.get("_id") else None,
            "municipio": str(cls._pick(doc, "municipio", "nm_municipio", default="")),
            "bairro": str(bairro or ""),
            "cd_bairro_ibge": cls._pick(doc, "cd_bairro_ibge", "cd_bairro"),
            "geometria": geometry,
            "municipioIdIbge": str(municipio_id_ibge),
            "pct_com_biblioteca": pct_com_biblioteca,
            "pct_com_internet": pct_com_internet,
            "pct_com_lab_informatica": pct_com_lab_informatica,
            "pct_sem_acessibilidade": pct_sem_acessibilidade,
            "sg_uf": cls._pick(doc, "sg_uf", "uf"),
            "total_escolas": total_escolas,
            "total_matriculas": int(total_matriculas or 0),
            "tem_bairro_oficial": tem_oficial,
            "nivel": nivel,
            "cd_setor": str(cd_setor) if cd_setor is not None else None,
            "socioeconomico": socioeconomico,
            "educacao": educacao,
            "source": source,
        }