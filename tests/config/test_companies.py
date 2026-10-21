from pathlib import Path

import pytest

from beges.config import CONFIG_DIR, load_company

COMPANY_FILES = sorted((CONFIG_DIR / "companies").glob("*.yml"))


@pytest.mark.parametrize("path", COMPANY_FILES, ids=lambda item: item.stem)
def test_company_config(path: Path, source_types, data_raw_dir: Path):
    company = load_company(path, source_types, data_raw_dir)

    assert company.code == path.stem
    assert company.sites
    assert company.sources
    assert len({source.id for source in company.sources}) == len(company.sources)

    for source in company.sources:
        assert (Path(data_raw_dir) / source.path).exists()
        assert source.type in source_types
