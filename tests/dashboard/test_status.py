from dataclasses import replace

from beges.reporting import build_status_text


def test_status_text_contains_key_sections(dashboard_data) -> None:
    text = build_status_text(dashboard_data)
    assert "Pipeline BEGES — statut" in text
    assert "Bilan       : 100,000 tCO2e | physique 50,0 %" in text
    assert "Qualité     : 2 constats | 1 bloquant | 1 alerte | 0 info" in text
    assert "Ingestion   : 3 sources | 41 lignes | 1 quarantaine" in text
    assert "dbt         : 2 PASS | 0 échec | 1,2 s" in text
    assert "Site        :" in text


def test_status_text_without_dbt(dashboard_data) -> None:
    text = build_status_text(replace(dashboard_data, dbt=None))
    assert "dbt         : indisponible" in text
