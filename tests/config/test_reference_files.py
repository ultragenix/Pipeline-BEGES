import csv
from pathlib import Path

import yaml

ACCOUNT_COLUMNS = [
    "prefixe",
    "libelle",
    "poste",
    "scope",
    "ratio_kgco2e_par_keur",
    "remplace_par",
    "type",
]
REPLACEMENTS = {"", "electricite", "carburant", "vols", "hors_perimetre"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == ACCOUNT_COLUMNS
        rows = list(reader)
    assert rows
    assert all(
        value is not None for row in rows for value in row.values()
    ), "ligne CSV incomplète"
    return rows


def test_account_mapping_is_well_formed(config_dir: Path):
    rows = _read_csv(config_dir / "account_mapping.csv")
    assert len(rows) == 28
    assert len({row["prefixe"] for row in rows}) == len(rows)

    for row in rows:
        assert row["prefixe"]
        assert row["poste"]
        assert row["remplace_par"] in REPLACEMENTS

        if row["type"] in {"charge", "immobilisation"}:
            assert row["scope"] in {"1", "2", "3"}
            if row["remplace_par"]:
                assert row["ratio_kgco2e_par_keur"] == ""
            else:
                assert float(row["ratio_kgco2e_par_keur"]) > 0
        else:
            assert row["type"] == ""
            assert row["remplace_par"] == "hors_perimetre"
            assert row["scope"] == ""
            assert row["ratio_kgco2e_par_keur"] == ""


def test_airports_reference(config_dir: Path):
    with (config_dir / "airports.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 9
    assert len({row["iata"] for row in rows}) == len(rows)
    for row in rows:
        assert row["iata"]
        assert -90 <= float(row["latitude"]) <= 90
        assert -180 <= float(row["longitude"]) <= 180


def test_emission_factors_reference(config_dir: Path):
    with (config_dir / "emission_factors.yml").open(encoding="utf-8") as handle:
        factors = yaml.safe_load(handle)

    electricity = factors["electricity"]["ELEC_REUNION"]
    assert electricity["value"] == 0.780
    assert electricity["unit"] == "kgCO2e/kWh"

    assert set(factors["fuel"]) == {"GAZOLE", "SP95"}
    assert set(factors["refrigerants"]) == {
        "R404A",
        "R410A",
        "R407C",
        "R134a",
        "R449A",
        "R32",
    }
    assert factors["flights"]["distance_correction_km"] == 95
    assert [band["code"] for band in factors["flights"]["bands"]] == [
        "AVION_COURT",
        "AVION_MOYEN",
        "AVION_LONG",
    ]
    assert set(factors["prices"]) == {
        "electricity_ht_eur_per_kwh",
        "gazole_ttc_eur_per_l",
        "sp95_ttc_eur_per_l",
        "vat_rate",
    }
    assert all(value > 0 for value in factors["refrigerants"].values())
