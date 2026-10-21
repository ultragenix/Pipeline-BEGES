import os
from pathlib import Path

import pandas as pd
import yaml

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


def model(dbt, session):
    """Registre des constats qualité, un fichier YAML par entreprise."""
    dbt.config(materialized="table")

    quality_dir = Path(os.environ["BEGES_CONFIG_DIR"]) / "quality"
    rows = []

    for path in sorted(quality_dir.glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        company_code = data["company"]

        for item in data["constats"]:
            missing = [field for field in REQUIRED_FIELDS if not item.get(field)]
            if missing:
                raise ValueError(f"{path.name} / {item.get('id')} : champs manquants {missing}")

            rows.append(
                {
                    "constat_id": item["id"],
                    "registry_id": item.get("registry_id"),
                    "company_code": company_code,
                    "source_type": item["source"],
                    "family": item["family"],
                    "severity": item["severity"],
                    "certitude": item["certitude"],
                    "statut": item["statut"],
                    "traitement": item["traitement"],
                    "title": item["title"],
                    "proof_detail": item["proof"],
                    "business_question": item["question"],
                    "impact_type": item["impact_type"],
                    "impact_group": item.get("impact_group"),
                    "impact_basis": item.get("impact_basis"),
                    "check_key": item["check_key"],
                    "match_key": item.get("match_key"),
                }
            )

    frame = pd.DataFrame(rows)
    return frame.astype(object).where(pd.notnull(frame), None)
