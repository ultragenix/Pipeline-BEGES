from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from beges.reporting import DashboardData, DbtResults


@pytest.fixture
def dashboard_data() -> DashboardData:
    bilan = pd.DataFrame(
        [
            {
                "company_code": "KAY",
                "company_name": "Kayamb Logistique SAS",
                "scope": 1,
                "poste": "Combustion mobile",
                "activity": "Carburants",
                "method": "physique",
                "lignes": 10,
                "tco2e": 40.0,
                "tco2e_physique": 40.0,
                "tco2e_monetaire": 0.0,
            },
            {
                "company_code": "KAY",
                "company_name": "Kayamb Logistique SAS",
                "scope": 2,
                "poste": "Électricité",
                "activity": "Électricité",
                "method": "physique",
                "lignes": 2,
                "tco2e": 10.0,
                "tco2e_physique": 10.0,
                "tco2e_monetaire": 0.0,
            },
            {
                "company_code": "FAN",
                "company_name": "Fanjan Agro SA",
                "scope": 1,
                "poste": "Achats de biens",
                "activity": "Matières premières",
                "method": "monetaire",
                "lignes": 5,
                "tco2e": 20.0,
                "tco2e_physique": 0.0,
                "tco2e_monetaire": 20.0,
            },
            {
                "company_code": "FAN",
                "company_name": "Fanjan Agro SA",
                "scope": 3,
                "poste": "Achats de biens",
                "activity": "Matières premières",
                "method": "monetaire",
                "lignes": 5,
                "tco2e": 30.0,
                "tco2e_physique": 0.0,
                "tco2e_monetaire": 30.0,
            },
        ]
    )

    quality = pd.DataFrame(
        [
            {
                "constat_id": "KAY-01",
                "company_code": "KAY",
                "company_name": "Kayamb Logistique SAS",
                "family": "completude",
                "severity": "bloquant",
                "certitude": "certain",
                "statut": "a_confirmer",
                "traitement": "aucun",
                "title": "Site manquant",
                "proof": "Un site déclaré n'a pas de relevé.",
                "business_question": "Le site a-t-il consommé ?",
                "impact_tco2e": 5.0,
                "impact_eur": 1000.0,
                "impact_group": "KAY-ELEC-GAP",
                "impact_type": "estimation",
            },
            {
                "constat_id": "FAN-01",
                "company_code": "FAN",
                "company_name": "Fanjan Agro SA",
                "family": "homogeneite_unites",
                "severity": "alerte",
                "certitude": "a_confirmer",
                "statut": "ouvert",
                "traitement": "converti",
                "title": "MWh",
                "proof": "Une feuille est en MWh.",
                "business_question": "Confirmez-vous l'unité ?",
                "impact_tco2e": 2.0,
                "impact_eur": None,
                "impact_group": None,
                "impact_type": "compte",
            },
        ]
    )

    quality_summary = pd.DataFrame(
        [
            {
                "company_code": "KAY",
                "company_name": "Kayamb Logistique SAS",
                "nb_constats": 1,
                "nb_bloquants": 1,
                "impact_tco2e": 5.0,
                "impact_eur": 1000.0,
            },
            {
                "company_code": "FAN",
                "company_name": "Fanjan Agro SA",
                "nb_constats": 1,
                "nb_bloquants": 0,
                "impact_tco2e": 2.0,
                "impact_eur": 0.0,
            },
        ]
    )

    ingestion = pd.DataFrame(
        [
            {
                "company_code": "KAY",
                "source_id": "fec",
                "source_type": "fec",
                "rows_read": 10,
                "rows_loaded": 10,
                "rows_quarantined": 0,
                "status": "success",
                "duration_ms": 100,
                "finished_at": pd.Timestamp("2025-12-31 10:00:00"),
            },
            {
                "company_code": "FAN",
                "source_id": "electricity",
                "source_type": "electricity",
                "rows_read": 20,
                "rows_loaded": 20,
                "rows_quarantined": 0,
                "status": "success",
                "duration_ms": 1500,
                "finished_at": pd.Timestamp("2025-12-31 10:05:00"),
            },
            {
                "company_code": "VAC",
                "source_id": "electricity",
                "source_type": "electricity",
                "rows_read": 11,
                "rows_loaded": 11,
                "rows_quarantined": 1,
                "status": "partial",
                "duration_ms": 200,
                "finished_at": pd.Timestamp("2025-12-30 10:00:00"),
            },
        ]
    )

    quarantine = pd.DataFrame(
        [
            {
                "company_code": "VAC",
                "source_id": "electricity",
                "reason_code": "valeur_invalide",
                "nb_lignes": 1,
                "first_seen_at": pd.Timestamp("2025-12-30 10:00:00"),
                "last_seen_at": pd.Timestamp("2025-12-30 10:00:00"),
            }
        ]
    )

    freshness = pd.DataFrame(
        [
            {
                "company_code": "KAY",
                "source_type": "electricity",
                "min_date": pd.Timestamp("2025-01-01"),
                "max_date": pd.Timestamp("2025-12-01"),
                "nb_lignes": 12,
                "nb_mois": 12,
            },
            {
                "company_code": "VAC",
                "source_type": "electricity",
                "min_date": pd.Timestamp("2025-01-01"),
                "max_date": pd.Timestamp("2025-11-01"),
                "nb_lignes": 11,
                "nb_mois": 11,
            },
            {
                "company_code": "KAY",
                "source_type": "vehicles",
                "min_date": None,
                "max_date": None,
                "nb_lignes": 46,
                "nb_mois": 0,
            },
        ]
    )

    dbt = DbtResults(
        pass_count=2,
        warn_count=0,
        error_count=0,
        skip_count=0,
        success_count=2,
        elapsed_seconds=1.2,
        generated_at=datetime(2025, 12, 31, 10, 0),
    )

    return DashboardData(
        bilan=bilan,
        quality=quality,
        quality_summary=quality_summary,
        ingestion=ingestion,
        quarantine=quarantine,
        freshness=freshness,
        dbt=dbt,
    )


@pytest.fixture
def run_results_file(tmp_path: Path) -> Path:
    path = tmp_path / "run_results.json"
    path.write_text(
        """
        {
          "elapsed_time": 1.2,
          "results": [
            {"status": "success"},
            {"status": "success"},
            {"status": "pass"},
            {"status": "pass"},
            {"status": "pass"},
            {"status": "warn"},
            {"status": "error"}
          ]
        }
        """,
        encoding="utf-8",
    )
    return path
