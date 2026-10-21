import os
from pathlib import Path

import pandas as pd
import yaml


def model(dbt, session):
    """Facteurs et paramètres lus depuis config/emission_factors.yml."""
    dbt.config(materialized="table")

    config_dir = Path(os.environ["BEGES_CONFIG_DIR"])
    with (config_dir / "emission_factors.yml").open(encoding="utf-8") as handle:
        factors = yaml.safe_load(handle)

    rows = []

    def add(category, code, value, unit, label, source, max_km=None):
        rows.append(
            {
                "factor_key": f"{category}:{code}",
                "category": category,
                "code": code,
                "value": float(value),
                "unit": unit,
                "label": label,
                "source": source,
                "max_km": max_km,
            }
        )

    electricity = factors["electricity"]["ELEC_REUNION"]
    add(
        "electricity",
        "ELEC_REUNION",
        electricity["value"],
        electricity["unit"],
        electricity["label"],
        electricity["source"],
    )

    for code, factor in factors["fuel"].items():
        add(
            "fuel",
            code,
            factor["value"],
            factor["unit"],
            factor["label"],
            factor["source"],
        )

    for code, gwp in factors["refrigerants"].items():
        add("refrigerant", code, gwp, "kgCO2e/kg", f"PRG {code}", "F-gas")

    for band in factors["flights"]["bands"]:
        add(
            "flight",
            band["code"],
            band["value"],
            band["unit"],
            band["code"],
            "Démonstration",
            band["max_km"],
        )

    add(
        "flight_param",
        "distance_correction_km",
        factors["flights"]["distance_correction_km"],
        "km",
        "Correction ADEME",
        "ADEME",
    )

    for code, price in factors["prices"].items():
        if code == "vat_rate":
            unit = "ratio"
        elif code.endswith("_l"):
            unit = "EUR/L"
        else:
            unit = "EUR/kWh"
        add("price", code, price, unit, code, "config")

    return pd.DataFrame(rows)
