"""Rapport des constats qualité calculés par dbt."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.environ.get("BEGES_DB_PATH", ROOT / "data" / "warehouse" / "beges.duckdb"))

FAMILY_LABELS = {
    "conformite_format": "conformité format",
    "unicite": "unicité",
    "completude": "complétude",
    "validite": "validité",
    "homogeneite_unites": "unités",
    "valeurs_aberrantes": "valeurs aberrantes",
    "integrite_referentielle": "intégrité référentielle",
    "coherence_interne": "cohérence interne",
    "coherence_entre_sources": "cohérence entre sources",
    "fraicheur": "fraîcheur",
}

SEVERITY_LABELS = {"bloquant": "bloquant", "alerte": "alerte", "info": "info"}

CERTITUDE_LABELS = {"certain": "certain", "a_confirmer": "à confirmer"}

STATUT_LABELS = {
    "ouvert": "ouvert",
    "a_confirmer": "à confirmer",
    "repondu": "répondu",
    "integre": "intégré",
    "ecarte": "écarté",
}

TRAITEMENT_LABELS = {
    "converti": "converti",
    "mappe": "mappé",
    "exclu": "exclu",
    "estime": "estimé",
    "conserve": "conservé",
    "aucun": "aucun",
}

IMPACT_LABELS = {
    "compte": "compté",
    "non_compte": "non compté",
    "exposition": "exposé",
    "estimation": "est.",
    "non_calculable": "",
}


def fmt_number(value: float, decimals: int = 2) -> str:
    """Formate un nombre à la française."""
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def plural(count: int, singular: str, plural_form: str) -> str:
    """Accorde un libellé simple."""
    return singular if count == 1 else plural_form


def fmt_impact(tco2e: float | None, eur: float | None, impact_type: str) -> str:
    """Résume l'impact carbone et financier d'un constat."""
    parts = []
    if tco2e is not None and not pd.isna(tco2e):
        parts.append(f"{fmt_number(tco2e)} tCO2e")
    if eur is not None and not pd.isna(eur):
        parts.append(f"{fmt_number(eur)} €")
    if not parts:
        return "n.c."
    suffix = IMPACT_LABELS.get(impact_type, "")
    return " / ".join(parts) + (f" {suffix}" if suffix else "")


def filter_findings(
    frame: pd.DataFrame,
    company: str | None = None,
    severity: str | None = None,
    family: str | None = None,
) -> pd.DataFrame:
    """Filtre le registre sans modifier l'ordre de lecture."""
    result = frame
    if company:
        result = result[result["company_code"].str.upper() == company.upper()]
    if severity:
        result = result[result["severity"] == severity]
    if family:
        result = result[result["family"] == family]
    return result


def summarize_findings(frame: pd.DataFrame) -> dict[str, int]:
    """Compte les constats par sévérité, certitude et statut."""
    return {
        "total": len(frame),
        "bloquant": int((frame["severity"] == "bloquant").sum()),
        "alerte": int((frame["severity"] == "alerte").sum()),
        "info": int((frame["severity"] == "info").sum()),
        "certitude_certain": int((frame["certitude"] == "certain").sum()),
        "certitude_a_confirmer": int((frame["certitude"] == "a_confirmer").sum()),
        "statut_a_confirmer": int((frame["statut"] == "a_confirmer").sum()),
        "statut_ouvert": int((frame["statut"] == "ouvert").sum()),
    }


def display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Prépare le tableau lisible du rapport."""
    display = pd.DataFrame(
        {
            "ID": frame["constat_id"],
            "Société": frame["company_code"],
            "Famille": frame["family"].map(FAMILY_LABELS).fillna(frame["family"]),
            "Sévérité": frame["severity"].map(SEVERITY_LABELS),
            "Certitude": frame["certitude"].map(CERTITUDE_LABELS),
            "Statut": frame["statut"].map(STATUT_LABELS),
            "Traitement": frame["traitement"].map(TRAITEMENT_LABELS),
            "Impact": [
                fmt_impact(tco2e, eur, impact_type)
                for tco2e, eur, impact_type in zip(
                    frame["impact_tco2e"],
                    frame["impact_eur"],
                    frame["impact_type"],
                    strict=True,
                )
            ],
            "Titre": frame["title"],
        }
    )
    return display.reset_index(drop=True)


def to_markdown(display: pd.DataFrame) -> str:
    """Rend un tableau Markdown sans dépendance externe."""
    columns = list(display.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for _, row in display.iterrows():
        values = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def load_findings(
    con: duckdb.DuckDBPyConnection,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Charge le registre et la synthèse depuis DuckDB."""
    findings = con.execute(
        """
        select *
        from analytics.quality_constats
        order by severity_rank, company_code, constat_id
        """
    ).fetchdf()
    summary = con.execute(
        """
        select *
        from analytics.quality_summary
        order by company_code
        """
    ).fetchdf()
    return findings, summary


def print_summary(
    findings: pd.DataFrame,
    summary: pd.DataFrame,
    show_companies: bool = True,
) -> None:
    """Affiche les compteurs et la synthèse par entreprise."""
    counts = summarize_findings(findings)
    label = plural(counts["total"], "constat", "constats")
    print(f"Constats qualité — {counts['total']} {label}")
    print(
        f"Blocants : {counts['bloquant']} | "
        f"Alertes : {counts['alerte']} | "
        f"Infos : {counts['info']}"
    )
    print(
        f"Certitude : {counts['certitude_certain']} certains | "
        f"{counts['certitude_a_confirmer']} à confirmer"
    )
    print(
        f"Statut    : {counts['statut_a_confirmer']} à confirmer | "
        f"{counts['statut_ouvert']} ouverts"
    )
    if not show_companies:
        print("\nSynthèse par entreprise : masquée par le filtre sévérité/famille.")
        return

    print("\nPar entreprise (impacts dédupliqués par groupe)")
    for _, row in summary.iterrows():
        nb_constats = int(row["nb_constats"])
        nb_bloquants = int(row["nb_bloquants"])
        print(
            f"  {row['company_code']:<4} {row['company_name']:<28} "
            f"{nb_constats:>2} {plural(nb_constats, 'constat', 'constats')}  "
            f"{nb_bloquants:>2} {plural(nb_bloquants, 'bloquant', 'bloquants')}  "
            f"{fmt_number(row['impact_tco2e']):>10} tCO2e  "
            f"{fmt_number(row['impact_eur']):>12} €"
        )


def print_details(frame: pd.DataFrame) -> None:
    """Affiche preuve et question métier pour chaque constat filtré."""
    print("\nDétail des constats")
    for _, row in frame.iterrows():
        print(f"\n{row['constat_id']} — {row['title']}")
        print(f"  Preuve   : {row['proof']}")
        print(f"  Question : {row['business_question']}")
        impact = fmt_impact(
            row["impact_tco2e"],
            row["impact_eur"],
            row["impact_type"],
        )
        print(f"  Impact   : {impact}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rapport des constats qualité BEGES.")
    parser.add_argument("--company", help="Filtrer sur un code entreprise (KAY, FAN, VAC, ALL).")
    parser.add_argument(
        "--severity",
        choices=["bloquant", "alerte", "info"],
        help="Filtrer sur une sévérité.",
    )
    parser.add_argument("--family", choices=sorted(FAMILY_LABELS), help="Filtrer sur une famille.")
    parser.add_argument("--detail", action="store_true", help="Afficher preuve et question métier.")
    parser.add_argument("--markdown", action="store_true", help="Sortir le tableau en Markdown.")
    parser.add_argument(
        "--top",
        type=int,
        metavar="N",
        help="Afficher les N constats au plus fort impact.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if not DB_PATH.exists():
        print(f"Base absente : {DB_PATH}. Lancer make ingest puis make quality.", file=sys.stderr)
        return 1

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        findings, summary = load_findings(con)
    except duckdb.CatalogException:
        print(
            "Tables qualité absentes. Lancer make quality ou make dbt-build.",
            file=sys.stderr,
        )
        return 1
    finally:
        con.close()

    filtered = filter_findings(findings, args.company, args.severity, args.family)
    if args.top:
        filtered = filtered.reindex(
            filtered["impact_tco2e"].abs().sort_values(ascending=False).index
        ).head(args.top)

    if args.company:
        summary = summary[summary["company_code"].str.upper() == args.company.upper()]

    print_summary(
        filtered,
        summary,
        show_companies=not (args.severity or args.family),
    )
    print()
    display = display_frame(filtered)
    if args.markdown:
        print(to_markdown(display))
    else:
        with pd.option_context("display.max_colwidth", 52, "display.width", 240):
            print(display.to_string(index=False))
    if args.detail:
        print_details(filtered)

    print(
        "\nRappel : les impacts partagés (KAY-ELEC-GAP, VAC-ELEC-GAP) "
        "sont dédupliqués dans la synthèse et ne sont pas additifs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
