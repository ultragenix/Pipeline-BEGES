import os
from pathlib import Path

import pandas as pd
import yaml


def model(dbt, session):
    """Référentiel des sites déclarés, lu depuis config/companies/*.yml."""
    dbt.config(materialized="table")

    companies_dir = Path(os.environ["BEGES_CONFIG_DIR"]) / "companies"
    rows = []

    for path in sorted(companies_dir.glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for site_code, site in sorted(data.get("sites", {}).items()):
            rows.append(
                {
                    "company_code": data["code"],
                    "site_key": f"{data['code']}:{site_code}",
                    "site_code": site_code,
                    "site_name": site.get("name"),
                    "pdl": site.get("pdl"),
                }
            )

    frame = pd.DataFrame(rows)
    return frame.astype(object).where(pd.notnull(frame), None)
