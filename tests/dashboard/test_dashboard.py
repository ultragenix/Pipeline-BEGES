from datetime import datetime

from beges.dashboard import render_site
from beges.reporting import (
    build_bilan_view,
    build_ingestion_view,
    build_quality_view,
)


def test_render_site_writes_pages_and_assets(dashboard_data, tmp_path) -> None:
    bilan = build_bilan_view(dashboard_data)
    quality = build_quality_view(dashboard_data)
    ingestion = build_ingestion_view(dashboard_data)

    written = render_site(
        tmp_path,
        bilan,
        quality,
        ingestion,
        generated_at=datetime(2025, 12, 31, 10, 0),
    )

    assert {path.name for path in written} == {"index.html", "observabilite.html"}
    assert (tmp_path / "assets" / "style.css").exists()
    assert (tmp_path / "assets" / "app.js").exists()

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    observability = (tmp_path / "observabilite.html").read_text(encoding="utf-8")

    assert "Bilan BEGES 2025" in index
    assert "100,000" in index
    assert "3 entreprises" in index
    assert "42 constats" not in index

    assert "Observabilité — BEGES 2025" in observability
    assert "KAY-01" in observability
    assert "FAN-01" in observability
    assert observability.count("<details") == 2
    assert 'id="filter-severity"' in observability
    assert 'id="filter-family"' in observability
    assert "{{" not in index
    assert "{{" not in observability
