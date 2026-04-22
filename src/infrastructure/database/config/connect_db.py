from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pymongo import ASCENDING, GEOSPHERE
from pymongo.errors import PyMongoError
from typing import Any

from .app_config import config

logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self):
        self.client = None
        self.database = None
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

            self.client = AsyncIOMotorClient(mongo_uri)
            self.database = self.client.get_database(config.database_name)

            await self.client.admin.command('ping')
            await self._ensure_indexes()

            self._is_connected = True
            logger.info(" MongoDB connected successfully")
            return True

        except Exception as e:
            logger.error(f" Failed to connect to MongoDB: {e}")
            self._is_connected = False
            return False

    async def _ensure_indexes(self):
        schools = self.database["escolas"]
        municipios = self.database["municipio_indicadores"]
        bairros = self.database["bairro_indicadores"]
        setores = self.database["setor_indicadores"]

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
        municipio_fields = ["co_municipio", "municipioIdIbge", "municipio_id_ibge", "idIbge"]
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

    async def _create_or_replace_index(
        self,
        collection: Any,
        index_spec: list[tuple[str, int]],
        index_name: str,
    ):
        """Create or replace index, handling conflicts gracefully."""
        try:
            await collection.create_index(
                index_spec,
                name=index_name,
                background=True,
            )
        except PyMongoError as exc:
            error_msg = str(exc)
            # Handle IndexOptionsConflict (error code 85)
            if "IndexOptionsConflict" in error_msg or "already exists with a different name" in error_msg:
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
                                logger.info(f"Dropped old index: {idx_info.get('name')}")
                    # Now create the new index
                    await collection.create_index(
                        index_spec,
                        name=index_name,
                        background=True,
                    )
                    logger.info(f"Created index: {index_name}")
                except Exception as inner_exc:
                    logger.error(f"Failed to handle index conflict for {index_name}: {inner_exc}")
            else:
                logger.error(f"Failed to create index {index_name}: {exc}")
                raise

    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self._is_connected = False
            logger.info(" MongoDB connection closed")

    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._is_connected

    def get_collection(self, collection_name: str):
        """Get a collection from the database"""
        if not self.is_connected:
            raise RuntimeError("Database not connected")
        return self.database[collection_name]


mongodb = MongoDB()
