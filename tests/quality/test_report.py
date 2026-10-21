import pandas as pd

from beges.quality import (
    display_frame,
    filter_findings,
    fmt_impact,
    fmt_number,
    summarize_findings,
    to_markdown,
)


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "constat_id": "KAY-01",
                "company_code": "KAY",
                "family": "completude",
                "severity": "bloquant",
                "certitude": "certain",
                "statut": "a_confirmer",
                "traitement": "aucun",
                "impact_tco2e": 185.027,
                "impact_eur": 40326.43,
                "impact_type": "estimation",
                "title": "Site manquant",
            },
            {
                "constat_id": "KAY-06",
                "company_code": "KAY",
                "family": "conformite_format",
                "severity": "info",
                "certitude": "certain",
                "statut": "a_confirmer",
                "traitement": "exclu",
                "impact_tco2e": 25.544,
                "impact_eur": 7416.0,
                "impact_type": "non_compte",
                "title": "ADBLUE",
            },
            {
                "constat_id": "FAN-01",
                "company_code": "FAN",
                "family": "homogeneite_unites",
                "severity": "bloquant",
                "certitude": "certain",
                "statut": "a_confirmer",
                "traitement": "converti",
                "impact_tco2e": 568.086,
                "impact_eur": None,
                "impact_type": "compte",
                "title": "MWh",
            },
        ]
    )


def test_fmt_number_uses_french_separators() -> None:
    assert fmt_number(1234.5) == "1 234,50"


def test_fmt_impact_combines_carbon_and_euros() -> None:
    assert fmt_impact(185.027, 40326.43, "estimation") == "185,03 tCO2e / 40 326,43 € est."
    assert fmt_impact(None, 14000.0, "non_compte") == "14 000,00 € non compté"
    assert fmt_impact(None, None, "non_calculable") == "n.c."


def test_summarize_findings_counts() -> None:
    counts = summarize_findings(sample_frame())
    assert counts == {
        "total": 3,
        "bloquant": 2,
        "alerte": 0,
        "info": 1,
        "certitude_certain": 3,
        "certitude_a_confirmer": 0,
        "statut_a_confirmer": 3,
        "statut_ouvert": 0,
    }


def test_filter_findings_by_company_and_severity() -> None:
    frame = sample_frame()
    assert list(filter_findings(frame, company="kay")["constat_id"]) == ["KAY-01", "KAY-06"]
    assert list(filter_findings(frame, severity="bloquant")["constat_id"]) == ["KAY-01", "FAN-01"]
    assert len(filter_findings(frame, company="VAC")) == 0


def test_display_and_markdown() -> None:
    display = display_frame(sample_frame())
    assert list(display.columns) == [
        "ID",
        "Société",
        "Famille",
        "Sévérité",
        "Certitude",
        "Statut",
        "Traitement",
        "Impact",
        "Titre",
    ]
    markdown = to_markdown(display)
    assert markdown.startswith("| ID | Société |")
    assert "KAY-01" in markdown
