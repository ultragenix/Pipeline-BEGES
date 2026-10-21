from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest

from beges.ingest import RunSummary, ingest


@pytest.fixture(scope="session")
def warehouse(tmp_path_factory: pytest.TempPathFactory, config) -> tuple[Path, RunSummary]:
    db_path = tmp_path_factory.mktemp("warehouse") / "beges.duckdb"
    summary = ingest(config, db_path=db_path)
    return db_path, summary


@pytest.fixture(scope="session")
def db_path(warehouse: tuple[Path, RunSummary]) -> Path:
    return warehouse[0]


@pytest.fixture(scope="session")
def summary(warehouse: tuple[Path, RunSummary]) -> RunSummary:
    return warehouse[1]


@pytest.fixture
def con(db_path: Path) -> Iterator[duckdb.DuckDBPyConnection]:
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        yield connection
    finally:
        connection.close()
