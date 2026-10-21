from pathlib import Path

import pytest
import yaml

from beges.config import ConfigError, load_company


def test_load_config(config):
    assert set(config.companies) == {"KAY", "FAN", "VAC"}
    assert config.site_count == 9
    assert config.source_count == 17


def test_company_source_counts(config):
    assert config.companies["KAY"].source_count == 6
    assert config.companies["FAN"].source_count == 5
    assert config.companies["VAC"].source_count == 6


def _company_payload(source: dict) -> dict:
    return {
        "code": "TST",
        "name": "Test",
        "city": "Test",
        "sector": "Test",
        "employees": 1,
        "exercise": 2025,
        "sites": {"S1": {"name": "Site", "pdl": "PDL-S1"}},
        "sources": [source],
    }


def test_missing_file_is_rejected(tmp_path: Path, source_types, data_raw_dir: Path):
    path = tmp_path / "TST.yml"
    payload = _company_payload(
        {
            "id": "flights",
            "type": "flights",
            "path": "TST/missing.csv",
            "date_format": "%d/%m/%Y",
        }
    )
    path.write_text(yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8")

    with pytest.raises(ConfigError, match="introuvable"):
        load_company(path, source_types, data_raw_dir)


def test_unknown_source_type_is_rejected(
    tmp_path: Path, source_types, data_raw_dir: Path
):
    path = tmp_path / "TST.yml"
    payload = _company_payload(
        {
            "id": "unknown",
            "type": "unknown",
            "path": "KAY/vols/export_agence_voyages_2025.csv",
        }
    )
    path.write_text(yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8")

    with pytest.raises(ConfigError, match="type inconnu"):
        load_company(path, source_types, data_raw_dir)
