from motor.motor_asyncio import AsyncIOMotorClient
import logging

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

            self._is_connected = True
            logger.info(" MongoDB connected successfully")
            return True

        except Exception as e:
            logger.error(f" Failed to connect to MongoDB: {e}")
            self._is_connected = False
            return False

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
