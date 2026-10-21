from pathlib import Path

import pytest

from beges.config import CONFIG_DIR, DATA_RAW_DIR, load_config, load_source_types


@pytest.fixture(scope="session")
def config_dir() -> Path:
    return CONFIG_DIR


@pytest.fixture(scope="session")
def data_raw_dir() -> Path:
    return DATA_RAW_DIR


@pytest.fixture(scope="session")
def source_types(config_dir: Path):
    return load_source_types(config_dir / "sources.yml")


@pytest.fixture(scope="session")
def config(config_dir: Path, data_raw_dir: Path):
    return load_config(config_dir, data_raw_dir)
