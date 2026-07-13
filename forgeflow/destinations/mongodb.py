from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from forgeflow.core.exceptions import SinkException
from forgeflow.core.sink import BaseSink


class MongoDBSink(BaseSink):
    """Sink for writing data to MongoDB."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.client: AsyncIOMotorClient | None = None
        self.collection = None

    def validate_config(self) -> None:
        """Validate required configuration parameters."""
        required = ["database", "collection"]
        missing = [key for key in required if key not in self.config]
        if missing:
            raise SinkException(f"Missing required config: {missing}")

    async def write(self, data: dict[str, Any]) -> None:
        """Write data to MongoDB collection."""
        if not self.client:
            await self._connect()

        try:
            # Determine write mode
            upsert = self.config.get("upsert", False)
            upsert_key = self.config.get("upsert_key", "_id")

            if upsert and upsert_key in data:
                # Upsert based on key
                filter_query = {upsert_key: data[upsert_key]}
                await self.collection.replace_one(
                    filter_query,
                    data,
                    upsert=True
                )
            else:
                # Simple insert
                await self.collection.insert_one(data)

        except PyMongoError as e:
            raise SinkException(f"MongoDB write failed: {e}") from e

    async def _connect(self) -> None:
        """Initialize MongoDB client and collection."""
        try:
            connection_string = self.config.get("connection_string")

            if not connection_string:
                # Build connection string from components
                host = self.config.get("host", "localhost")
                port = self.config.get("port", 27017)
                username = self.config.get("username")
                password = self.config.get("password")

                if username and password:
                    connection_string = f"mongodb://{username}:{password}@{host}:{port}"
                else:
                    connection_string = f"mongodb://{host}:{port}"

            # Create async client
            self.client = AsyncIOMotorClient(
                connection_string,
                serverSelectionTimeoutMS=self.config.get("timeout", 5000)
            )

            # Get database and collection
            database_name = self.config["database"]
            collection_name = self.config["collection"]

            db = self.client[database_name]
            self.collection = db[collection_name]

            # Create indexes if specified
            await self._create_indexes()

        except PyMongoError as e:
            raise SinkException(f"MongoDB connection failed: {e}") from e

    async def _create_indexes(self) -> None:
        """Create indexes if specified in config."""
        indexes = self.config.get("indexes", [])

        for index_spec in indexes:
            if isinstance(index_spec, str):
                # Simple field index
                await self.collection.create_index(index_spec)
            elif isinstance(index_spec, dict):
                # Compound or custom index
                fields = index_spec.get("fields", [])
                unique = index_spec.get("unique", False)
                name = index_spec.get("name")

                if fields:
                    await self.collection.create_index(
                        fields,
                        unique=unique,
                        name=name
                    )

    async def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
