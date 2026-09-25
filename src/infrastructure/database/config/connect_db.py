import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, GEOSPHERE
from pymongo.errors import PyMongoError

from .app_config import config

logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient | None = None
        self.database: Any | None = None
        self._is_connected = False

    async def connect(self) -> bool:
        """
        Connect to MongoDB database
        Returns True if successful, False otherwise
        """
        try:
            mongo_uri = config.mongo_uri
            if not mongo_uri:
                logger.error("Mongo URI is not configured")
                return False

            client: AsyncIOMotorClient = AsyncIOMotorClient(mongo_uri)
            database = client.get_database(config.database_name)

            self.client = client
            self.database = database

            await client.admin.command("ping")
            await self._ensure_indexes()

            self._is_connected = True
            logger.info(" MongoDB connected successfully")
            return True

        except Exception as e:
            logger.error(f" Failed to connect to MongoDB: {e}")
            self._is_connected = False
            return False

    async def _ensure_indexes(self) -> None:
        database = self.database
        if database is None:
            raise RuntimeError("Database not connected")

        schools = database["escolas"]
        municipios = database["municipio_indicadores"]
        bairros = database["bairro_indicadores"]
        setores = database["setor_indicadores"]

        await schools.create_index(
            [
                ("estadoSigla", ASCENDING),
                ("municipioNome", ASCENDING),
                ("endereco.bairro", ASCENDING),
            ],
            name="idx_escolas_estado_municipio_bairro",
            background=True,
        )
        await schools.create_index(
            [("escolaIdInep", ASCENDING)],
            name="idx_escolas_inep",
            background=True,
        )
        await schools.create_index(
            [
                ("estadoSigla", ASCENDING),
                ("escolaIdInep", ASCENDING),
            ],
            name="idx_escolas_estado_inep",
            background=True,
        )
        # Municipality-first index for searches by municipio (optionally
        # combined with a UF filter to disambiguate homonymous municipalities).
        await self._create_or_replace_index(
            schools,
            [
                ("municipioNome", ASCENDING),
                ("estadoSigla", ASCENDING),
            ],
            "idx_escolas_municipio_estado",
            collation={"locale": "pt", "strength": 1},
        )
        # Composite indexes for state+municipality+school lookups (GeoJSON and
        # list queries). Same names as the lazy creation kept in
        # MongoSchoolRepository._ensure_geojson_indexes() so both paths are
        # idempotent.
        await self._create_or_replace_index(
            schools,
            [
                ("estadoSigla", ASCENDING),
                ("municipioIdIbge", ASCENDING),
                ("escolaIdInep", ASCENDING),
            ],
            "idx_geojson_municipio",
        )
        await self._create_or_replace_index(
            schools,
            [
                ("estadoSigla", ASCENDING),
                ("municipio_id_ibge", ASCENDING),
                ("escolaIdInep", ASCENDING),
            ],
            "idx_geojson_municipio_legacy",
        )

        # Build geospatial index only for valid coordinates.
        try:
            await schools.create_index(
                [("localizacao", GEOSPHERE)],
                name="idx_escolas_localizacao_2dsphere_valid_only",
                background=True,
                partialFilterExpression={
                    "localizacao.type": "Point",
                    "localizacao.coordinates.0": {
                        "$type": "number",
                        "$gte": -180,
                        "$lte": 180,
                    },
                    "localizacao.coordinates.1": {
                        "$type": "number",
                        "$gte": -90,
                        "$lte": 90,
                    },
                },
            )
        except PyMongoError as exc:
            logger.warning(
                "Skipping geospatial index creation due to invalid coordinate data: %s",
                exc,
            )

        # Indexes for territorial aggregation endpoints and fallback.
        # Handle potential conflicts from previously created indexes
        municipio_fields = [
            "co_municipio",
            "municipioIdIbge",
            "municipio_id_ibge",
            "idIbge",
        ]
        for field in municipio_fields:
            await self._create_or_replace_index(
                municipios,
                [(field, ASCENDING)],
                f"idx_municipio_indicadores_{field}",
            )
            await self._create_or_replace_index(
                setores,
                [(field, ASCENDING)],
                f"idx_setor_indicadores_{field}",
            )

        bairro_search_fields = ["bairro", "nm_bairro", "nome_area"]
        for municipio_field in municipio_fields:
            for bairro_field in bairro_search_fields:
                await self._create_or_replace_index(
                    bairros,
                    [(municipio_field, ASCENDING), (bairro_field, ASCENDING)],
                    f"idx_bairro_indicadores_{municipio_field}_{bairro_field}",
                )

        # UF filters on the aggregation collections. The `_uf_clause` used by
        # MongoTerritorialAggregationRepository queries via `$or` across
        # sg_uf / uf / estado_sigla, so each branch needs its own index.
        aggregation_collections = {
            "municipio_indicadores": municipios,
            "bairro_indicadores": bairros,
            "setor_indicadores": setores,
        }
        for collection_name, collection in aggregation_collections.items():
            for uf_field in ("sg_uf", "uf", "estado_sigla"):
                await self._create_or_replace_index(
                    collection,
                    [(uf_field, ASCENDING)],
                    f"idx_{collection_name}_{uf_field}",
                )

        try:
            await bairros.create_index(
                [("geometria", GEOSPHERE)],
                name="idx_bairro_indicadores_geometria",
                background=True,
            )
        except PyMongoError as exc:
            logger.warning(
                "Skipping bairro geospatial index creation due to invalid geometry data: %s",
                exc,
            )

        await self._create_or_replace_index(
            schools,
            [("escolaNome", ASCENDING)],
            "idx_escolas_nome_busca",
            collation={"locale": "pt", "strength": 1},
        )
        await self._create_or_replace_index(
            schools,
            [("endereco.logradouro", ASCENDING)],
            "idx_escolas_logradouro_busca",
            collation={"locale": "pt", "strength": 1},
        )
        await self._create_or_replace_index(
            schools,
            [("endereco.cep", ASCENDING)],
            "idx_escolas_cep_busca",
        )
        await self._create_or_replace_index(
            municipios,
            [("municipio", ASCENDING)],
            "idx_municipio_nome_busca",
            collation={"locale": "pt", "strength": 1},
        )
        await self._create_or_replace_index(
            bairros,
            [("bairro", ASCENDING)],
            "idx_bairro_nome_busca",
            collation={"locale": "pt", "strength": 1},
        )

    async def _create_or_replace_index(
        self,
        collection: Any,
        index_spec: list[tuple[str, int]],
        index_name: str,
        **kwargs: Any,
    ) -> None:
        """Create or replace index, handling conflicts gracefully."""
        try:
            await collection.create_index(
                index_spec,
                name=index_name,
                background=True,
                **kwargs,
            )
        except PyMongoError as exc:
            error_msg = str(exc)
            # Handle IndexOptionsConflict (error code 85)
            if (
                "IndexOptionsConflict" in error_msg
                or "already exists with a different name" in error_msg
            ):
                logger.warning(
                    f"Index with similar key exists; dropping old index and recreating: {index_name}"
                )
                try:
                    desired_key_pairs = list(index_spec)
                    # Drop indexes with the same key pattern except the one we want to create.
                    indexes = await collection.list_indexes().to_list(length=None)
                    for idx_info in indexes:
                        idx_key = idx_info.get("key")
                        existing_key_pairs = list(idx_key.items()) if idx_key else []
                        if existing_key_pairs == desired_key_pairs:
                            if idx_info.get("name") != index_name:
                                await collection.drop_index(idx_info.get("name"))
                                logger.info(
                                    f"Dropped old index: {idx_info.get('name')}"
                                )
                    # Now create the new index
                    await collection.create_index(
                        index_spec,
                        name=index_name,
                        background=True,
                        **kwargs,
                    )
                    logger.info(f"Created index: {index_name}")
                except Exception as inner_exc:
                    logger.error(
                        f"Failed to handle index conflict for {index_name}: {inner_exc}"
                    )
            else:
                logger.error(f"Failed to create index {index_name}: {exc}")
                raise

    async def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self._is_connected = False
            logger.info(" MongoDB connection closed")

    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._is_connected

    def get_collection(self, collection_name: str) -> Any:
        """Get a collection from the database"""
        if not self.is_connected:
            raise RuntimeError("Database not connected")
        database = self.database
        if database is None:
            raise RuntimeError("Database not connected")
        return database[collection_name]


mongodb = MongoDB()
