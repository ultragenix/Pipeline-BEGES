def test_source_types(source_types):
    assert set(source_types) == {
        "fec",
        "electricity",
        "electricity_xlsx",
        "fuel",
        "vehicle_registry",
        "refrigerants",
        "flights",
    }


def test_fec_default_mapping(source_types):
    source_type = source_types["fec"]
    assert source_type.default_column_map["entry_id"] == "EcritureNum"
    assert source_type.default_column_map["account"] == "CompteNum"
    assert source_type.key == ("entry_id",)


def test_fuel_quantity_is_optional(source_types):
    source_type = source_types["fuel"]
    assert "quantity_l" in source_type.optional_fields
    assert "amount_ttc_eur" in source_type.required_fields


def test_flights_default_mapping(source_types):
    source_type = source_types["flights"]
    assert source_type.default_column_map["ticket_id"] == "Numero billet"
    assert source_type.default_column_map["origin_iata"] == "Origine"
    assert source_type.key == ("ticket_id",)
