import hashlib
import shutil
from pathlib import Path

import duckdb
import yaml

from beges.config import CONFIG_DIR, load_config
from beges.ingest import ingest

TABLES = ("fec", "electricity", "fuel", "refrigerants", "flights", "vehicles")
TOTAL_ROWS = 8_263
TOTAL_SOURCES = 17


def _counts(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    return {
        table: con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]
        for table in TABLES
    }


def _electricity_source(source_id: str = "elec", path: str = "elec.csv") -> dict:
    return {
        "id": source_id,
        "type": "electricity",
        "path": path,
        "encoding": "utf-8",
        "delimiter": ";",
        "decimal": ",",
        "date_format": "%d/%m/%Y",
        "column_map": {
            "month": "month",
            "site_code": "site",
            "consumption_kwh": "kwh",
            "amount_ht_eur": "amount",
        },
    }


def _write_config(
    tmp_path: Path,
    sources: list[dict],
    files: dict[str, str],
) -> tuple[Path, Path]:
    config_dir = tmp_path / "config"
    companies_dir = config_dir / "companies"
    companies_dir.mkdir(parents=True)
    shutil.copy(CONFIG_DIR / "sources.yml", config_dir / "sources.yml")

    company = {
        "code": "TEST",
        "name": "Test SAS",
        "city": "Test",
        "sector": "Test",
        "employees": 1,
        "exercise": 2025,
        "sites": {"S1": {"name": "Site 1", "pdl": "PDL-S1"}},
        "sources": sources,
    }
    (companies_dir / "TEST.yml").write_text(
        yaml.safe_dump(company, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for name, content in files.items():
        (data_dir / name).write_text(content, encoding="utf-8")
    return config_dir, data_dir


def test_unparseable_rows_are_quarantined(tmp_path: Path):
    config_dir, data_dir = _write_config(
        tmp_path,
        [_electricity_source()],
        {
            "elec.csv": (
                "month;site;kwh;amount\n"
                "01/01/2025;S1;10,5;2,0\n"
                "not-a-date;S1;10,5;2,0\n"
                "02/01/2025;S1;abc;2,0\n"
                "03/01/2025;S1;12,5;3,0\n"
                "04/01/2025;XX;12,5;3,0\n"
            )
        },
    )
    db_path = tmp_path / "quarantine.duckdb"
    config = load_config(config_dir, data_dir)
    summary = ingest(config, data_raw_dir=data_dir, db_path=db_path)

    assert summary.failures == 0
    assert summary.rows_loaded == 2
    assert summary.rows_quarantined == 3

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        assert con.execute("SELECT count(*) FROM raw.electricity").fetchone()[0] == 2
        reasons = {
            row[0]
            for row in con.execute(
                "SELECT reason_code FROM raw.quarantine"
            ).fetchall()
        }
        assert reasons == {"date_invalide", "nombre_invalide", "site_inconnu"}
        assert con.execute(
            "SELECT status, rows_loaded, rows_quarantined FROM raw.ingestion_log"
        ).fetchone() == ("partial", 2, 3)
        assert con.execute(
            "SELECT min(source_row), max(source_row) FROM raw.quarantine"
        ).fetchone() == (3, 6)
    finally:
        con.close()


def test_failed_source_keeps_previous_rows_and_isolates_error(tmp_path: Path):
    config_dir, data_dir = _write_config(
        tmp_path,
        [_electricity_source("good", "good.csv"), _electricity_source("bad", "bad.csv")],
        {
            "good.csv": (
                "month;site;kwh;amount\n"
                "01/01/2025;S1;10,5;2,0\n"
                "02/01/2025;S1;11,5;2,5\n"
            ),
            "bad.csv": (
                "month;site;kwh;amount\n"
                "01/01/2025;S1;20,0;4,0\n"
            ),
        },
    )
    db_path = tmp_path / "failure.duckdb"
    config = load_config(config_dir, data_dir)

    first = ingest(config, data_raw_dir=data_dir, db_path=db_path)
    assert first.failures == 0
    assert first.rows_loaded == 3

    (data_dir / "bad.csv").write_text(
        "month;site;amount\n01/02/2025;S1;4,0\n", encoding="utf-8"
    )
    second = ingest(config, data_raw_dir=data_dir, db_path=db_path)
    assert second.failures == 1
    assert second.rows_loaded == 2

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        assert con.execute("SELECT count(*) FROM raw.electricity").fetchone()[0] == 3
        latest = dict(
            con.execute(
                """
                SELECT source_id, status
                FROM raw.ingestion_log
                QUALIFY row_number() OVER (
                    PARTITION BY source_id ORDER BY started_at DESC
                ) = 1
                """
            ).fetchall()
        )
        assert latest == {"good": "success", "bad": "failed"}
        assert con.execute(
            "SELECT count(*) FROM raw.quarantine WHERE reason_code = 'colonne_manquante'"
        ).fetchone()[0] == 1
    finally:
        con.close()


def test_ingestion_is_idempotent(tmp_path: Path, config):
    db_path = tmp_path / "idempotent.duckdb"
    first = ingest(config, db_path=db_path)
    second = ingest(config, db_path=db_path)

    assert first.rows_loaded == second.rows_loaded == TOTAL_ROWS
    assert first.rows_quarantined == second.rows_quarantined == 0

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        assert sum(_counts(con).values()) == TOTAL_ROWS
        assert con.execute("SELECT count(*) FROM raw.ingestion_log").fetchone()[0] == (
            2 * TOTAL_SOURCES
        )
        rows = con.execute(
            """
            WITH data AS (
                SELECT company_code, source_id, ingestion_id FROM raw.fec
                UNION ALL
                SELECT company_code, source_id, ingestion_id FROM raw.electricity
                UNION ALL
                SELECT company_code, source_id, ingestion_id FROM raw.fuel
                UNION ALL
                SELECT company_code, source_id, ingestion_id FROM raw.refrigerants
                UNION ALL
                SELECT company_code, source_id, ingestion_id FROM raw.flights
                UNION ALL
                SELECT company_code, source_id, ingestion_id FROM raw.vehicles
            )
            SELECT company_code, source_id, count(*), count(DISTINCT ingestion_id)
            FROM data
            GROUP BY company_code, source_id
            """
        ).fetchall()
        assert len(rows) == TOTAL_SOURCES
        for company_code, source_id, count, ingestion_ids in rows:
            expected = con.execute(
                """
                SELECT rows_loaded
                FROM raw.ingestion_log
                WHERE company_code = ? AND source_id = ?
                ORDER BY started_at DESC
                LIMIT 1
                """,
                [company_code, source_id],
            ).fetchone()[0]
            assert count == expected
            assert ingestion_ids == 1
    finally:
        con.close()


def test_rebuild_recreates_data_tables(tmp_path: Path, config):
    db_path = tmp_path / "rebuild.duckdb"
    ingest(config, db_path=db_path)
    summary = ingest(config, db_path=db_path, rebuild=True)

    assert summary.failures == 0
    assert summary.rows_loaded == TOTAL_ROWS
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        assert sum(_counts(con).values()) == TOTAL_ROWS
        assert con.execute("SELECT count(*) FROM raw.ingestion_log").fetchone()[0] == (
            2 * TOTAL_SOURCES
        )
    finally:
        con.close()


def test_log_hashes_match_source_files(con, data_raw_dir: Path):
    rows = con.execute(
        "SELECT source_file, source_sha256, file_size_bytes FROM raw.ingestion_log"
    ).fetchall()
    assert len(rows) == TOTAL_SOURCES
    for source_file, sha256, size in rows:
        content = (data_raw_dir / source_file).read_bytes()
        assert sha256 == hashlib.sha256(content).hexdigest()
        assert size == len(content)


def test_log_covers_every_source(con):
    assert con.execute(
        """
        SELECT count(*), sum(rows_loaded), sum(rows_quarantined),
               count(*) FILTER (WHERE status = 'failed')
        FROM raw.ingestion_log
        """
    ).fetchone() == (TOTAL_SOURCES, TOTAL_ROWS, 0, 0)
