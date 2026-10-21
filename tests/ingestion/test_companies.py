from pathlib import Path

import pytest

from beges.config import CONFIG_DIR

COMPANY_FILES = sorted((CONFIG_DIR / "companies").glob("*.yml"))
EXPECTED_ROWS = {"KAY": 5_641, "FAN": 1_406, "VAC": 1_216}
TABLES = ("fec", "electricity", "fuel", "refrigerants", "flights", "vehicles")


def _count_rows(con, table: str, company_code: str) -> int:
    return con.execute(
        f"SELECT count(*) FROM raw.{table} WHERE company_code = ?", [company_code]
    ).fetchone()[0]


@pytest.mark.parametrize("path", COMPANY_FILES, ids=lambda item: item.stem)
def test_company_ingestion(path: Path, config, summary, con):
    code = path.stem
    company = config.companies[code]
    expected = EXPECTED_ROWS[code]

    assert sum(_count_rows(con, table, code) for table in TABLES) == expected

    entries = [entry for entry in summary.entries if entry.company_code == code]
    assert len(entries) == company.source_count
    assert {entry.source_id for entry in entries} == {
        source.id for source in company.sources
    }
    assert all(entry.status == "success" for entry in entries)
    assert sum(entry.rows_loaded for entry in entries) == expected
    assert sum(entry.rows_quarantined for entry in entries) == 0


@pytest.mark.parametrize("path", COMPANY_FILES, ids=lambda item: item.stem)
def test_company_metadata_is_complete(path: Path, con):
    code = path.stem
    for table in TABLES:
        missing = con.execute(
            f"""
            SELECT count(*)
            FROM raw.{table}
            WHERE company_code = ?
              AND (
                source_id IS NULL
                OR source_file IS NULL
                OR source_row IS NULL
                OR ingestion_id IS NULL
                OR ingested_at IS NULL
                OR raw_row IS NULL
              )
            """,
            [code],
        ).fetchone()[0]
        assert missing == 0, f"métadonnées incomplètes dans raw.{table}"


@pytest.mark.parametrize("path", COMPANY_FILES, ids=lambda item: item.stem)
def test_company_site_codes_are_known(path: Path, config, con):
    code = path.stem
    known = set(config.companies[code].sites)
    sites = {
        row[0]
        for row in con.execute(
            """
            SELECT DISTINCT site_code FROM raw.electricity WHERE company_code = ?
            UNION
            SELECT DISTINCT site_code FROM raw.refrigerants WHERE company_code = ?
            """,
            [code, code],
        ).fetchall()
    }
    assert sites
    assert sites <= known


@pytest.mark.parametrize("path", COMPANY_FILES, ids=lambda item: item.stem)
def test_company_quarantine_is_empty(path: Path, con):
    code = path.stem
    assert (
        con.execute(
            "SELECT count(*) FROM raw.quarantine WHERE company_code = ?", [code]
        ).fetchone()[0]
        == 0
    )
