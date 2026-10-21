"""Génération du site statique de démonstration."""

from __future__ import annotations

import argparse
import shutil
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from beges.reporting import (
    SITE_DIR,
    build_bilan_view,
    build_ingestion_view,
    build_quality_view,
    fmt_date,
    fmt_datetime,
    fmt_duration_ms,
    fmt_number,
    fmt_pct,
    fmt_tco2e,
    load_dashboard_data,
)

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = ROOT / "dashboard" / "templates"
STATIC_DIR = ROOT / "dashboard" / "static"


def build_environment() -> Environment:
    """Prépare Jinja2 avec les filtres de formatage français."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["tco2e"] = fmt_tco2e
    env.filters["pct"] = fmt_pct
    env.filters["number"] = lambda value, decimals=0: fmt_number(value, decimals)
    env.filters["eur"] = lambda value: fmt_number(value, 2)
    env.filters["date"] = fmt_date
    env.filters["datetime"] = fmt_datetime
    env.filters["duration_ms"] = fmt_duration_ms
    env.filters["duration_s"] = lambda value: f"{value:.1f} s".replace(".", ",")
    return env


def render_site(
    output_dir: Path,
    bilan: dict,
    quality: dict,
    ingestion: dict,
    generated_at: datetime | None = None,
) -> list[Path]:
    """Écrit les pages HTML et copie les assets statiques."""
    output_dir = Path(output_dir)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    for asset in ("style.css", "app.js"):
        shutil.copy2(STATIC_DIR / asset, assets_dir / asset)

    env = build_environment()
    generated_at = generated_at or datetime.now().astimezone()
    common = {"generated_at": generated_at, "nb_constats": quality["total"]}

    pages = [
        (
            "index.html",
            "index.html",
            "bilan",
            {"bilan": bilan, "quality": quality},
        ),
        (
            "observabilite.html",
            "observabilite.html",
            "ops",
            {"quality": quality, "ingestion": ingestion},
        ),
    ]

    written = []
    for filename, template_name, page, extra in pages:
        template = env.get_template(template_name)
        html = template.render(page=page, **common, **extra)
        path = output_dir / filename
        path.write_text(html, encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Génère le site statique BEGES.")
    parser.add_argument(
        "--output",
        type=Path,
        default=SITE_DIR,
        help="Répertoire de sortie du site.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Ouvre le site dans le navigateur après génération.",
    )
    args = parser.parse_args()

    try:
        data = load_dashboard_data()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    bilan = build_bilan_view(data)
    quality = build_quality_view(data)
    ingestion = build_ingestion_view(data)
    written = render_site(args.output, bilan, quality, ingestion)

    print(f"Site généré : {args.output}")
    print(f"  {written[0].name:<22} Bilan 2025, {len(bilan['companies'])} entreprises")
    print(
        f"  {written[1].name:<22} {quality['total']} constats, "
        f"{ingestion['nb_sources']} sources"
    )
    print("  assets/                style.css, app.js")

    if args.open:
        webbrowser.open(written[0].as_uri())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
