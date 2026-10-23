"""Validates the multi-state index set created by provisioning (ODIN-B08).

Uses fake collections that capture ``create_index`` calls so the tests run
without a real MongoDB connection.
"""

import pytest

from src.infrastructure.database.config.connect_db import MongoDB


class FakeIndexCursor:
    async def to_list(self, length=None):
        return []


class FakeIndexCollection:
    def __init__(self, name: str):
        self.name = name
        self.created_indexes: list[tuple[list, str | None, dict | None]] = []

    async def create_index(self, fields, **kwargs):
        self.created_indexes.append(
            (fields, kwargs.get("name"), kwargs.get("collation"))
        )
        return kwargs.get("name")

    async def list_indexes(self):
        return FakeIndexCursor()

    async def drop_index(self, name: str) -> None:
        pass


class FakeDatabase:
    def __init__(self):
        self.collections = {
            "escolas": FakeIndexCollection("escolas"),
            "municipio_indicadores": FakeIndexCollection("municipio_indicadores"),
            "bairro_indicadores": FakeIndexCollection("bairro_indicadores"),
            "setor_indicadores": FakeIndexCollection("setor_indicadores"),
        }

    def __getitem__(self, name):
        return self.collections[name]


def _index_names(collection: FakeIndexCollection) -> set[str]:
    return {name for _, name, _ in collection.created_indexes if name}


@pytest.mark.asyncio
async def test_ensure_indexes_creates_state_filter_and_sort_index():
    mongo = MongoDB()
    db = FakeDatabase()
    mongo.database = db

    await mongo._ensure_indexes()

    escolas = db.collections["escolas"]
    assert "idx_escolas_estado_inep" in _index_names(escolas)

    estado_inep = next(
        entry
        for entry in escolas.created_indexes
        if entry[1] == "idx_escolas_estado_inep"
    )
    assert estado_inep[0] == [("estadoSigla", 1), ("escolaIdInep", 1)]


@pytest.mark.asyncio
async def test_ensure_indexes_creates_municipio_estado_index_with_collation():
    mongo = MongoDB()
    db = FakeDatabase()
    mongo.database = db

    await mongo._ensure_indexes()

    escolas = db.collections["escolas"]
    municipio_estado = next(
        entry
        for entry in escolas.created_indexes
        if entry[1] == "idx_escolas_municipio_estado"
    )
    assert municipio_estado[0] == [("municipioNome", 1), ("estadoSigla", 1)]
    assert municipio_estado[2] == {"locale": "pt", "strength": 1}


@pytest.mark.asyncio
async def test_ensure_indexes_centralizes_geojson_composite_indexes():
    mongo = MongoDB()
    db = FakeDatabase()
    mongo.database = db

    await mongo._ensure_indexes()

    escolas = db.collections["escolas"]
    names = _index_names(escolas)
    assert "idx_geojson_municipio" in names
    assert "idx_geojson_municipio_legacy" in names


@pytest.mark.asyncio
async def test_ensure_indexes_creates_uf_indexes_on_aggregation_collections():
    mongo = MongoDB()
    db = FakeDatabase()
    mongo.database = db

    await mongo._ensure_indexes()

    for collection_name in (
        "municipio_indicadores",
        "bairro_indicadores",
        "setor_indicadores",
    ):
        collection = db.collections[collection_name]
        names = _index_names(collection)
        assert f"idx_{collection_name}_sg_uf" in names
        assert f"idx_{collection_name}_uf" in names
        assert f"idx_{collection_name}_estado_sigla" in names


@pytest.mark.asyncio
async def test_connect_bounds_pool_and_does_not_provision_indexes(monkeypatch):
    from src.infrastructure.database.config import connect_db

    options = {}

    class Client:
        def __init__(self, uri, **kwargs):
            options.update(kwargs)
            self.admin = self

        def get_database(self, name):
            return FakeDatabase()

        async def command(self, command):
            assert command == "ping"

        def close(self):
            pass

    monkeypatch.setattr(connect_db, "AsyncIOMotorClient", Client)
    mongo = MongoDB()

    async def forbidden():
        pytest.fail("startup must not create indexes")

    monkeypatch.setattr(mongo, "_ensure_indexes", forbidden)
    assert await mongo.connect()
    assert options["minPoolSize"] == 0
    assert options["maxPoolSize"] == 10
    await mongo.disconnect()


@pytest.mark.asyncio
async def test_provisioning_reuses_equivalent_index_without_dropping():
    from pymongo.errors import OperationFailure

    class IndexCursor:
        async def to_list(self, length):
            return [{"name": "old_name", "key": {"sg_uf": 1}}]

    class Collection:
        async def create_index(self, *args, **kwargs):
            raise OperationFailure("IndexOptionsConflict", code=85)

        def list_indexes(self):
            return IndexCursor()

        async def drop_index(self, *args):
            pytest.fail("provisioning must not drop indexes")

    await MongoDB()._create_or_replace_index(Collection(), [("sg_uf", 1)], "new_name")


@pytest.mark.asyncio
async def test_incompatible_index_options_fail_without_dropping():
    from pymongo.errors import OperationFailure

    class IndexCursor:
        async def to_list(self, length):
            return [{"name": "old_name", "key": {"sg_uf": 1}, "unique": False}]

    class Collection:
        async def create_index(self, *args, **kwargs):
            raise OperationFailure("IndexOptionsConflict", code=85)

        def list_indexes(self):
            return IndexCursor()

    with pytest.raises(RuntimeError, match="manual review"):
        await MongoDB()._create_or_replace_index(
            Collection(), [("sg_uf", 1)], "new_name", unique=True
        )
