from typing import Any

from src.domain.entities.territorial_summary import CitySummary, NeighborhoodSummary


class TerritorialAggregationMapper:
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
    def _flatten_lon_lat_pairs(cls, value: Any) -> list[tuple[float, float]]:
        pairs: list[tuple[float, float]] = []

        if isinstance(value, (list, tuple)):
            if len(value) >= 2 and not isinstance(value[0], (list, tuple)):
                lon = cls._as_float(value[0])
                lat = cls._as_float(value[1])
                if lon is not None and lat is not None:
                    pairs.append((lon, lat))
                return pairs

            for item in value:
                pairs.extend(cls._flatten_lon_lat_pairs(item))

        return pairs

    @classmethod
    def _extract_coordinates(cls, doc: dict[str, Any]) -> tuple[float, float] | None:
        geometry = cls._pick(
            doc,
            "centroide",
            "centroid",
            "geometry",
            "localizacao",
            "geometria",
        )

        if isinstance(geometry, dict):
            coords = geometry.get("coordinates")
            pairs = cls._flatten_lon_lat_pairs(coords)
            if pairs:
                avg_lon = sum(item[0] for item in pairs) / len(pairs)
                avg_lat = sum(item[1] for item in pairs) / len(pairs)
                return (avg_lon, avg_lat)

        pairs = cls._flatten_lon_lat_pairs(geometry)
        if pairs:
            avg_lon = sum(item[0] for item in pairs) / len(pairs)
            avg_lat = sum(item[1] for item in pairs) / len(pairs)
            return (avg_lon, avg_lat)

        lon = cls._as_float(cls._pick(doc, "longitude", "lon", "avg_lon"))
        lat = cls._as_float(cls._pick(doc, "latitude", "lat", "avg_lat"))
        if lon is not None and lat is not None:
            return (lon, lat)

        return None

    @classmethod
    def _extract_full_geometry(cls, doc: dict[str, Any]) -> dict[str, Any] | None:
        geo = cls._pick(doc, "geometria", "geometry")
        if isinstance(geo, dict) and "type" in geo and "coordinates" in geo:
            return geo

        centroid = cls._pick(doc, "centroide", "centroid", "localizacao")
        if isinstance(centroid, dict) and "coordinates" in centroid:
            return {
                "type": centroid.get("type", "Point"),
                "coordinates": centroid["coordinates"],
            }

        coords = cls._extract_coordinates(doc)
        if coords:
            return {"type": "Point", "coordinates": [coords[0], coords[1]]}

        return None

    @classmethod
    def city_from_doc(
        cls,
        doc: dict[str, Any],
        *,
        source: str,
        include_geometria: bool = False,
    ) -> CitySummary:
        doc_id = str(doc.get("_id", "")) if doc.get("_id") else None

        return CitySummary(
            mongoId=doc_id,
            co_municipio=str(
                cls._pick(
                    doc,
                    "co_municipio",
                    "municipioIdIbge",
                    "municipio_id_ibge",
                    "idIbge",
                    "_id",
                    default="",
                )
            ),
            municipio=str(
                cls._pick(doc, "nm_municipio", "municipio", "municipio_nome", default="")
            ),
            uf=cls._pick(doc, "sg_uf", "estado_sigla", "uf"),
            total_escolas=int(
                cls._pick(doc, "total_escolas", "qtd_escolas", "escolas", default=0)
            ),
            total_alunos=int(
                cls._pick(
                    doc,
                    "total_alunos",
                    "total_matriculas",
                    "qtd_alunos",
                    "alunos",
                    default=0,
                )
            ),
            avg_ideb=cls._as_float(cls._pick(doc, "avg_ideb", "ideb_medio", "ideb")),
            pct_com_biblioteca=cls._as_float(cls._pick(doc, "pct_com_biblioteca")),
            pct_com_internet=cls._as_float(cls._pick(doc, "pct_com_internet")),
            pct_com_lab_informatica=cls._as_float(
                cls._pick(doc, "pct_com_lab_informatica")
            ),
            pct_sem_acessibilidade=cls._as_float(
                cls._pick(doc, "pct_sem_acessibilidade")
            ),
            full_geometry=cls._extract_full_geometry(doc) if include_geometria else None,
            coordinates=cls._extract_coordinates(doc),
            source=source,
        )

    @classmethod
    def neighborhood_from_doc(
        cls,
        doc: dict[str, Any],
        *,
        source: str,
    ) -> NeighborhoodSummary:
        doc_id = str(doc.get("_id", "")) if doc.get("_id") else None
        tem_bairro_official = bool(
            cls._pick(doc, "tem_bairro_official", "tem_bairro_oficial", default=True)
        )

        bairro = cls._pick(doc, "bairro", "nm_bairro")
        if not tem_bairro_official:
            bairro = cls._pick(doc, "nome_area", "situacao", "bairro", "nm_bairro")

        return NeighborhoodSummary(
            mongoId=doc_id,
            co_municipio=str(
                cls._pick(
                    doc,
                    "co_municipio",
                    "municipioIdIbge",
                    "municipio_id_ibge",
                    "idIbge",
                    default="",
                )
            ),
            bairro=str(bairro or ""),
            municipio=str(
                cls._pick(doc, "nm_municipio", "municipio", "municipio_nome", default="")
            ),
            uf=cls._pick(doc, "sg_uf", "estado_sigla", "uf"),
            total_escolas=int(
                cls._pick(doc, "total_escolas", "qtd_escolas", "escolas", default=0)
            ),
            total_alunos=int(
                cls._pick(
                    doc,
                    "total_alunos",
                    "total_matriculas",
                    "qtd_alunos",
                    "alunos",
                    default=0,
                )
            ),
            avg_ideb=cls._as_float(cls._pick(doc, "avg_ideb", "ideb_medio", "ideb")),
            pct_com_biblioteca=cls._as_float(cls._pick(doc, "pct_com_biblioteca")),
            pct_com_internet=cls._as_float(cls._pick(doc, "pct_com_internet")),
            pct_com_lab_informatica=cls._as_float(
                cls._pick(doc, "pct_com_lab_informatica")
            ),
            pct_sem_acessibilidade=cls._as_float(
                cls._pick(doc, "pct_sem_acessibilidade")
            ),
            tem_bairro_official=tem_bairro_official,
            coordinates=cls._extract_coordinates(doc),
            source=source,
        )

    @staticmethod
    def city_to_feature(city: CitySummary) -> dict[str, Any]:
        if city.full_geometry:
            geometry = city.full_geometry
        elif city.coordinates is not None:
            geometry = {
                "type": "Point",
                "coordinates": [float(city.coordinates[0]), float(city.coordinates[1])],
            }
        else:
            geometry = {"type": "Point", "coordinates": [0.0, 0.0]}

        feature = {
            "type": "Feature",
            "id": city.co_municipio,
            "geometry": geometry,
            "properties": {
                "municipioIdIbge": city.co_municipio,
                "co_municipio": city.co_municipio,
                "municipio": city.municipio,
                "uf": city.uf,
                "total_escolas": city.total_escolas,
                "total_alunos": city.total_alunos,
                "avg_ideb": city.avg_ideb,
                "pct_com_biblioteca": city.pct_com_biblioteca,
                "pct_com_internet": city.pct_com_internet,
                "pct_com_lab_informatica": city.pct_com_lab_informatica,
                "pct_sem_acessibilidade": city.pct_sem_acessibilidade,
                "source": city.source,
            },
        }
        if city.mongoId:
            feature["mongoId"] = city.mongoId
        return feature

    @staticmethod
    def neighborhood_to_feature(neighborhood: NeighborhoodSummary) -> dict[str, Any]:
        if neighborhood.coordinates is None:
            coordinates = [0.0, 0.0]
        else:
            coordinates = [
                float(neighborhood.coordinates[0]),
                float(neighborhood.coordinates[1]),
            ]

        feature = {
            "type": "Feature",
            "id": f"{neighborhood.co_municipio}:{neighborhood.bairro}",
            "geometry": {
                "type": "Point",
                "coordinates": coordinates,
            },
            "properties": {
                "municipioIdIbge": neighborhood.co_municipio,
                "co_municipio": neighborhood.co_municipio,
                "bairro": neighborhood.bairro,
                "municipio": neighborhood.municipio,
                "uf": neighborhood.uf,
                "total_escolas": neighborhood.total_escolas,
                "total_alunos": neighborhood.total_alunos,
                "avg_ideb": neighborhood.avg_ideb,
                "pct_com_biblioteca": neighborhood.pct_com_biblioteca,
                "pct_com_internet": neighborhood.pct_com_internet,
                "pct_com_lab_informatica": neighborhood.pct_com_lab_informatica,
                "pct_sem_acessibilidade": neighborhood.pct_sem_acessibilidade,
                "tem_bairro_official": neighborhood.tem_bairro_official,
                "source": neighborhood.source,
            },
        }
        if neighborhood.mongoId:
            feature["mongoId"] = neighborhood.mongoId
        return feature
