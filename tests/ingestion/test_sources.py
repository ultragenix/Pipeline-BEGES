from datetime import date
from decimal import Decimal


def test_row_counts_by_type(con):
    counts = {
        table: con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]
        for table in (
            "fec",
            "electricity",
            "fuel",
            "refrigerants",
            "flights",
            "vehicles",
        )
    }
    assert counts == {
        "fec": 1_999,
        "electricity": 95,
        "fuel": 5_879,
        "refrigerants": 57,
        "flights": 187,
        "vehicles": 46,
    }
    assert sum(counts.values()) == 8_263


def test_kay_electricity_derives_month_and_resolves_site(con):
    row = con.execute(
        """
        SELECT count(*), min(month), max(month), sum(consumption_kwh),
               sum(amount_ht_eur)
        FROM raw.electricity
        WHERE company_code = 'KAY'
        """
    ).fetchone()
    assert row == (
        26,
        date(2025, 1, 1),
        date(2025, 12, 1),
        Decimal("590197.000"),
        Decimal("100333.49"),
    )

    sites = con.execute(
        """
        SELECT DISTINCT site_code, site_code_raw
        FROM raw.electricity
        WHERE company_code = 'KAY'
        ORDER BY site_code
        """
    ).fetchall()
    assert sites == [
        ("LPT-ENT", "Entrepôt Le Port"),
        ("LPT-SIE", "Siège Le Port"),
    ]


def test_kay_electricity_keeps_negative_regularisation(con):
    row = con.execute(
        """
        SELECT consumption_kwh, amount_ht_eur, reading_type
        FROM raw.electricity
        WHERE company_code = 'KAY' AND reading_type = 'Régularisation'
        """
    ).fetchone()
    assert row == (Decimal("-11751.000"), Decimal("-1997.67"), "Régularisation")


def test_kay_fec_preserves_account_as_text_and_source_columns(con):
    first = con.execute(
        """
        SELECT entry_id, account, entry_date,
               json_extract_string(raw_row, '$.JournalCode')
        FROM raw.fec
        WHERE company_code = 'KAY'
        ORDER BY source_row
        LIMIT 1
        """
    ).fetchone()
    assert first == ("AC000001", "6155000", date(2025, 1, 1), "AC")
    assert (
        con.execute(
            "SELECT count(*) FROM raw.fec WHERE company_code = 'KAY'"
        ).fetchone()[0]
        == 647
    )


def test_fan_xlsx_converts_mwh_and_keeps_unit(con):
    rows = con.execute(
        """
        SELECT site_code, unit_raw, count(*), sum(consumption_kwh)
        FROM raw.electricity
        WHERE company_code = 'FAN'
        GROUP BY site_code, unit_raw
        ORDER BY site_code
        """
    ).fetchall()
    assert rows == [
        ("PIE-FRO", "MWh", 12, Decimal("728316.000")),
        ("SPI-ADM", "kWh", 12, Decimal("69044.000")),
        ("SPI-USI", "kWh", 12, Decimal("1698589.000")),
    ]


def test_fan_fuel_has_no_quantity(con):
    assert con.execute(
        """
        SELECT count(*), count(quantity_l)
        FROM raw.fuel
        WHERE company_code = 'FAN'
        """
    ).fetchone() == (623, 0)


def test_fan_refrigerants_keep_empty_and_unknown_codes(con):
    row = con.execute(
        """
        SELECT count(*), count(fluid_code),
               count(*) FILTER (WHERE fluid_code IS NULL),
               count(*) FILTER (WHERE fluid_code = 'R-?')
        FROM raw.refrigerants
        WHERE company_code = 'FAN'
        """
    ).fetchone()
    assert row == (17, 16, 1, 1)


def test_vac_fuel_merges_two_source_schemas(con):
    rows = con.execute(
        """
        SELECT source_id, count(*), count(quantity_l), sum(quantity_l)
        FROM raw.fuel
        WHERE company_code = 'VAC'
        GROUP BY source_id
        ORDER BY source_id
        """
    ).fetchall()
    assert rows == [
        ("fuel_s1", 182, 182, Decimal("10625.610")),
        ("fuel_s2", 185, 185, Decimal("10576.320")),
    ]


def test_vac_electricity_has_eleven_months(con):
    assert con.execute(
        """
        SELECT count(*), count(DISTINCT month), count(DISTINCT site_code),
               min(month), max(month)
        FROM raw.electricity
        WHERE company_code = 'VAC'
        """
    ).fetchone() == (33, 11, 3, date(2025, 1, 1), date(2025, 11, 1))


def test_kay_flights_keep_empty_destination(con):
    assert con.execute(
        """
        SELECT count(*), count(destination_iata),
               count(*) FILTER (WHERE destination_iata IS NULL)
        FROM raw.flights
        WHERE company_code = 'KAY'
        """
    ).fetchone() == (25, 24, 1)


def test_vehicle_registry_is_complete(con):
    rows = con.execute(
        """
        SELECT tank_capacity_l, count(*)
        FROM raw.vehicles
        GROUP BY tank_capacity_l
        ORDER BY tank_capacity_l
        """
    ).fetchall()
    assert rows == [(Decimal("80.000"), 6), (Decimal("300.000"), 40)]
