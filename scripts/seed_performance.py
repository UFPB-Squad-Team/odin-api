"""Synthetic, non-destructive capacity fixture. Never use on production data."""

import asyncio
import math
import os

from motor.motor_asyncio import AsyncIOMotorClient

STATES = [
    ("PB", "2507507", 6),
    ("PE", "2611606", 14),
    ("CE", "2304400", 14),
    ("RN", "2408102", 5),
    ("MA", "2111300", 10),
    ("PI", "2211001", 6),
    ("AL", "2704302", 5),
    ("SE", "2800308", 3),
    ("BA", "2927408", 27),
]


def geometry(lon, lat, vertices=1024):
    ring = [
        [
            lon + 0.01 * math.cos(i * 2 * math.pi / vertices),
            lat + 0.01 * math.sin(i * 2 * math.pi / vertices),
        ]
        for i in range(vertices)
    ]
    return {"type": "Polygon", "coordinates": [ring + [ring[0]]]}


async def main():
    name = os.environ["DATABASE_NAME"]
    if not name.startswith("odin_perf_"):
        raise ValueError("DATABASE_NAME must start with odin_perf_")
    from src.infrastructure.database.config.connect_db import MongoDB

    client = AsyncIOMotorClient(os.environ["MONGO_URI"])
    db = client[name]
    try:
        if await db.list_collection_names():
            raise ValueError(
                "Fixture requires an empty isolated database; existing data is never deleted"
            )
        total = 0
        for state_index, (uf, capital, weight) in enumerate(STATES):
            lon, lat = -45 + state_index, -10 + state_index * 0.2
            for city in range(200):
                code = str(int(capital) + city)
                doc = {
                    "co_municipio": code,
                    "sg_uf": uf,
                    "municipio": f"Municipio {uf} {city}",
                    "educacao": {
                        "totalEscolas": 50,
                        "totalMatriculas": 10000,
                        "mediaIdebAnosIniciais": 5.5,
                        "pctComInternet": 90.0,
                    },
                    "socioeconomico": {"populacao": {"total": 50000}},
                    "geometria": geometry(lon, lat),
                    "unrelated_census_payload": "x" * 8192,
                }
                if city % 3:  # Exercise both centroid projection and geometry fallback.
                    doc["centroide"] = {"type": "Point", "coordinates": [lon, lat]}
                await db.municipio_indicadores.insert_one(doc)
            for neighborhood in range(50):
                await db.bairro_indicadores.insert_one(
                    {
                        "municipioIdIbge": capital,
                        "sg_uf": uf,
                        "bairro": f"Bairro {neighborhood}",
                        "total_escolas": 10,
                        "geometria": geometry(lon, lat, 128),
                    }
                )
            # No official bairros for city 1, exercising the census-sector fallback.
            for sector in range(100):
                await db.setor_indicadores.insert_one(
                    {
                        "co_municipio": str(int(capital) + 1),
                        "sg_uf": uf,
                        "uf": uf,
                        "municipio": f"Municipio {uf} 1",
                        "bairro": f"Setor {sector}",
                        "cd_setor": str(int(capital) * 1000 + sector),
                        "tem_bairro_oficial": False,
                        "total_escolas": 1,
                        "total_alunos": 200,
                        "geometria": geometry(lon, lat, 128),
                    }
                )
            chunk = []
            for i in range(75000 * weight // 100):
                chunk.append(
                    {
                        "escolaIdInep": state_index * 1000000 + i + 1,
                        "escolaNome": f"Escola {uf} {i}",
                        "estadoSigla": uf,
                        "municipioIdIbge": str(int(capital) + i % 200),
                        "municipioNome": f"Municipio {uf} {i % 200}",
                        "dependenciaAdm": "Municipal",
                        "tipoLocalizacao": "Urbana",
                        "endereco": {"bairro": f"Bairro {i % 50}"},
                        "localizacao": {"type": "Point", "coordinates": [lon, lat]},
                        "indicadores": {
                            "totalAlunos": 200,
                            "ideb": 5.5,
                            "anoReferencia": 2025,
                            "porEtapa": {
                                str(k): {"ideb": 5.5, "aprovacao": 95.0}
                                for k in range(6)
                            },
                        },
                        "matriculas": {"totalAlunos": 200, "fundamentalTotal": 200},
                        "unrelated_census_payload": "x" * 4096,
                    }
                )
                total += 1
                if len(chunk) == 500:
                    await db.escolas.insert_many(chunk)
                    chunk.clear()
            if chunk:
                await db.escolas.insert_many(chunk)
        assert total == 75000
        mongo = MongoDB()
        mongo.client, mongo.database = client, db
        await mongo._ensure_indexes()
        print(
            f"Seeded {total} schools, 1800 cities, 450 bairros and 900 sectors in {name}"
        )
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
