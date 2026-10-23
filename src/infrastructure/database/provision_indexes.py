"""Run once before deployment: python -m src.infrastructure.database.provision_indexes.

Creates missing indexes idempotently; never drops an existing index.
"""

import asyncio

from src.infrastructure.database.config.connect_db import MongoDB


async def main():
    mongo = MongoDB()
    if not await mongo.connect():
        raise RuntimeError("Could not connect to provision indexes")
    try:
        await mongo._ensure_indexes()
    finally:
        await mongo.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
