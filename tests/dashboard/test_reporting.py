from datetime import datetime

import pandas as pd

from beges.reporting import (
    build_bilan_view,
    build_ingestion_view,
    build_quality_view,
    fmt_date,
    fmt_datetime,
    fmt_duration_ms,
    fmt_pct,
    fmt_tco2e,
    parse_dbt_results,
)


def test_build_bilan_view(dashboard_data) -> None:
    view = build_bilan_view(dashboard_data)
    assert view["total_tco2e"] == 100.0
    assert view["total_physique"] == 50.0
    assert view["part_physique"] == 50.0
    assert [scope["scope"] for scope in view["scopes"]] == [1, 2, 3]
    assert len(view["companies"]) == 2

    kay = next(company for company in view["companies"] if company["code"] == "KAY")
    assert kay["tco2e"] == 50.0
    assert kay["scope1"] == 40.0
    assert kay["scope2"] == 10.0
    assert kay["scope3"] == 0.0
    assert kay["nb_constats"] == 1
    assert kay["nb_bloquants"] == 1


def test_build_quality_view(dashboard_data) -> None:
    view = build_quality_view(dashboard_data)
    assert view["total"] == 2
    assert view["bloquants"] == 1
    assert view["alertes"] == 1
    assert view["infos"] == 0
    assert view["certains"] == 1
    assert view["a_confirmer"] == 1
    assert view["statut_a_confirmer"] == 1
    assert view["statut_ouverts"] == 1
    assert view["impact_tco2e"] == 7.0
    assert view["impact_eur"] == 1000.0
    assert view["company_options"] == ["FAN", "KAY"]

    fan = next(constat for constat in view["constats"] if constat["constat_id"] == "FAN-01")
    assert fan["impact_group"] is None
    assert fan["family_label"] == "unités"
    assert fan["statut_label"] == "ouvert"


def test_build_ingestion_view(dashboard_data) -> None:
    view = build_ingestion_view(dashboard_data)
    assert view["nb_sources"] == 3
    assert view["rows_loaded"] == 41
    assert view["quarantine_total"] == 1
    assert view["nb_failures"] == 1
    assert view["dbt"].pass_count == 2

    freshness = {(row["company_code"], row["source_type"]): row for row in view["freshness"]}
    assert freshness[("VAC", "electricity")]["note"] == "Mois manquants"
    assert freshness[("KAY", "vehicles")]["note"] == "Référentiel"


def test_parse_dbt_results(run_results_file) -> None:
    results = parse_dbt_results(run_results_file)
    assert results is not None
    assert results.pass_count == 3
    assert results.success_count == 2
    assert results.warn_count == 1
    assert results.error_count == 1
    assert results.skip_count == 0
    assert results.elapsed_seconds == 1.2


def test_parse_dbt_results_missing(tmp_path) -> None:
    assert parse_dbt_results(tmp_path / "absent.json") is None


def test_formatters() -> None:
    assert fmt_tco2e(16231.298) == "16 231,298"
    assert fmt_pct(44.72) == "44,7 %"
    assert fmt_date(pd.Timestamp("2025-12-01")) == "01/12/2025"
    assert fmt_date(None) == "—"
    assert fmt_datetime(datetime(2025, 12, 31, 10, 0)) == "31/12/2025 10:00"
    assert fmt_duration_ms(950) == "950 ms"
    assert fmt_duration_ms(1500) == "1,5 s"
