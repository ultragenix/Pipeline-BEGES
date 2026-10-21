import os
from pathlib import Path

import pandas as pd
import yaml


def model(dbt, session):
    """Référentiel entreprises lu depuis config/companies/*.yml."""
    dbt.config(materialized="table")

    companies_dir = Path(os.environ["BEGES_CONFIG_DIR"]) / "companies"
    rows = []
    for path in sorted(companies_dir.glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "company_code": data["code"],
                "company_name": data["name"],
                "city": data["city"],
                "sector": data["sector"],
                "employees": data["employees"],
                "exercise": data["exercise"],
            }
        )
    return pd.DataFrame(rows)
