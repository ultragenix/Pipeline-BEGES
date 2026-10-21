from collections import Counter
from pathlib import Path

import pytest
import yaml

from beges.config import CONFIG_DIR

QUALITY_DIR = CONFIG_DIR / "quality"

FAMILIES = {
    "conformite_format",
    "unicite",
    "completude",
    "validite",
    "homogeneite_unites",
    "valeurs_aberrantes",
    "integrite_referentielle",
    "coherence_interne",
    "coherence_entre_sources",
    "fraicheur",
}
SEVERITIES = {"bloquant", "alerte", "info"}
CERTITUDES = {"certain", "a_confirmer"}
STATUTS = {"ouvert", "a_confirmer", "repondu", "integre", "ecarte"}
TRAITEMENTS = {"converti", "mappe", "exclu", "estime", "conserve", "aucun"}
IMPACT_TYPES = {"compte", "non_compte", "exposition", "estimation", "non_calculable"}

REQUIRED_FIELDS = (
    "id",
    "source",
    "family",
    "severity",
    "certitude",
    "statut",
    "traitement",
    "check_key",
    "title",
    "proof",
    "question",
    "impact_type",
)


@pytest.fixture(scope="module")
def register() -> list[dict]:
    rows = []
    for path in sorted(QUALITY_DIR.glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for item in data["constats"]:
            rows.append({**item, "company_code": data["company"], "file": path.name})
    return rows


def test_register_has_at_least_15_constats(register: list[dict]) -> None:
    assert len(register) >= 15


def test_register_ids_are_unique(register: list[dict]) -> None:
    ids = [row["id"] for row in register]
    assert len(ids) == len(set(ids))


def test_register_covers_registry_questions(register: list[dict]) -> None:
    registry_ids = [row["registry_id"] for row in register if row.get("registry_id")]
    assert len(registry_ids) >= 38
    assert len(registry_ids) == len(set(registry_ids))

    by_company = Counter(row["company_code"] for row in register if row.get("registry_id"))
    minimums = {"KAY": 14, "FAN": 13, "VAC": 11}
    for company_code, minimum in minimums.items():
        assert by_company[company_code] >= minimum, company_code


def test_register_required_fields(register: list[dict]) -> None:
    for row in register:
        missing = [field for field in REQUIRED_FIELDS if not row.get(field)]
        assert not missing, f"{row['file']} / {row.get('id')} : {missing}"


def test_register_enums(register: list[dict]) -> None:
    for row in register:
        assert row["family"] in FAMILIES, row["id"]
        assert row["severity"] in SEVERITIES, row["id"]
        assert row["certitude"] in CERTITUDES, row["id"]
        assert row["statut"] in STATUTS, row["id"]
        assert row["traitement"] in TRAITEMENTS, row["id"]
        assert row["impact_type"] in IMPACT_TYPES, row["id"]


def test_register_check_keys_are_unique_per_company(register: list[dict]) -> None:
    keys = [
        (row["company_code"], row["check_key"], row.get("match_key") or "")
        for row in register
    ]
    assert len(keys) == len(set(keys))


def test_register_impact_groups_have_two_members(register: list[dict]) -> None:
    groups = Counter(row["impact_group"] for row in register if row.get("impact_group"))
    for impact_group, count in groups.items():
        assert count >= 2, impact_group


def test_register_registry_id_matches_id(register: list[dict]) -> None:
    for row in register:
        if row.get("registry_id"):
            assert row["registry_id"] == row["id"]


def test_register_has_a_file_per_company() -> None:
    company_codes = set()
    for path in (CONFIG_DIR / "companies").glob("*.yml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        company_codes.add(data["code"])

    quality_codes = set()
    for path in Path(QUALITY_DIR).glob("*.yml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        quality_codes.add(data["company"])

    assert company_codes <= quality_codes


def test_register_each_company_has_at_least_one_constat(register: list[dict]) -> None:
    counts = Counter(row["company_code"] for row in register)
    for company_code in {row["company_code"] for row in register}:
        assert counts[company_code] >= 1, company_code
