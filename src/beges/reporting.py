"""Chargement et agrégation des données du dashboard et du statut."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import duckdb
import pandas as pd

from beges.quality import (
    CERTITUDE_LABELS,
    FAMILY_LABELS,
    STATUT_LABELS,
    TRAITEMENT_LABELS,
    fmt_impact,
    fmt_number,
    plural,
)

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.environ.get("BEGES_DB_PATH", ROOT / "data" / "warehouse" / "beges.duckdb"))
RUN_RESULTS_PATH = ROOT / "dbt" / "target" / "run_results.json"
SITE_DIR = Path(os.environ.get("BEGES_SITE_DIR", ROOT / "site"))


@dataclass(frozen=True)
class DbtResults:
    pass_count: int
    warn_count: int
    error_count: int
    skip_count: int
    success_count: int
    elapsed_seconds: float
    generated_at: datetime | None


@dataclass
class DashboardData:
    bilan: pd.DataFrame
    quality: pd.DataFrame
    quality_summary: pd.DataFrame
    ingestion: pd.DataFrame
    quarantine: pd.DataFrame
    freshness: pd.DataFrame
    dbt: DbtResults | None


def fmt_tco2e(value: float, decimals: int = 3) -> str:
    """Formate une valeur carbone."""
    return fmt_number(value, decimals)


def fmt_pct(value: float) -> str:
    """Formate un pourcentage à la française."""
    return f"{value:.1f} %".replace(".", ",")


def fmt_date(value: object) -> str:
    """Formate une date ou un mois."""
    if value is None or pd.isna(value):
        return "—"
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return str(value)


def fmt_datetime(value: object) -> str:
    """Formate un horodatage."""
    if value is None or pd.isna(value):
        return "—"
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    return str(value)


def fmt_duration_ms(value: float | int | None) -> str:
    """Formate une durée courte."""
    if value is None or pd.isna(value):
        return "—"
    milliseconds = float(value)
    if milliseconds < 1000:
        return f"{milliseconds:.0f} ms"
    return f"{milliseconds / 1000:.1f} s".replace(".", ",")


def parse_dbt_results(path: Path) -> DbtResults | None:
    """Lit le dernier run_results.json de dbt, s'il existe."""
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    results = payload.get("results", [])
    statuses = [result.get("status", "") for result in results]
    generated_at = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    return DbtResults(
        pass_count=sum(status == "pass" for status in statuses),
        warn_count=sum(status == "warn" for status in statuses),
        error_count=sum(status in {"error", "fail"} for status in statuses),
        skip_count=sum(status in {"skipped", "skip"} for status in statuses),
        success_count=sum(status == "success" for status in statuses),
        elapsed_seconds=float(payload.get("elapsed_time", 0)),
        generated_at=generated_at,
    )


def load_dashboard_data(
    db_path: Path = DB_PATH,
    run_results_path: Path = RUN_RESULTS_PATH,
) -> DashboardData:
    """Charge les tables du bilan, de la qualité et de l'observabilité."""
    if not db_path.exists():
        raise FileNotFoundError(f"Base absente : {db_path}. Lancer make ingest.")

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        bilan = con.execute("select * from analytics.mart_beges").fetchdf()
        quality = con.execute(
            """
            select *
            from analytics.quality_constats
            order by severity_rank, company_code, constat_id
            """
        ).fetchdf()
        quality_summary = con.execute(
            "select * from analytics.quality_summary order by company_code"
        ).fetchdf()
        ingestion = con.execute(
            """
            select *
            from analytics.ops_ingestion_last_run
            order by company_code, source_id
            """
        ).fetchdf()
        quarantine = con.execute(
            "select * from analytics.ops_quarantine_summary order by company_code, source_id"
        ).fetchdf()
        freshness = con.execute(
            """
            select *
            from analytics.ops_freshness
            order by company_code, source_type
            """
        ).fetchdf()
    finally:
        con.close()

    return DashboardData(
        bilan=bilan,
        quality=quality,
        quality_summary=quality_summary,
        ingestion=ingestion,
        quarantine=quarantine,
        freshness=freshness,
        dbt=parse_dbt_results(run_results_path),
    )


def build_bilan_view(data: DashboardData) -> dict:
    """Agrège le bilan par entreprise, scope, poste et méthode."""
    bilan = data.bilan
    total = float(bilan["tco2e"].sum())
    total_physique = float(bilan["tco2e_physique"].sum())
    part_physique = 100 * total_physique / total if total else 0

    by_scope = (
        bilan.groupby("scope", as_index=False)["tco2e"]
        .sum()
        .sort_values("scope")
    )
    scopes = [
        {
            "scope": int(row.scope),
            "tco2e": float(row.tco2e),
            "part": 100 * float(row.tco2e) / total if total else 0,
        }
        for row in by_scope.itertuples()
    ]

    company_scope = (
        bilan.pivot_table(
            index=["company_code", "company_name"],
            columns="scope",
            values="tco2e",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
        .rename(columns={1: "scope1", 2: "scope2", 3: "scope3"})
    )
    for column in ("scope1", "scope2", "scope3"):
        if column not in company_scope:
            company_scope[column] = 0.0

    by_company = (
        bilan.groupby(["company_code", "company_name"], as_index=False)
        .agg(
            tco2e=("tco2e", "sum"),
            physique=("tco2e_physique", "sum"),
            monetaire=("tco2e_monetaire", "sum"),
        )
        .merge(company_scope, on=["company_code", "company_name"], how="left")
        .merge(
            data.quality_summary[
                ["company_code", "nb_constats", "nb_bloquants"]
            ],
            on="company_code",
            how="left",
        )
    )
    by_company["part_physique"] = by_company.apply(
        lambda row: 100 * row["physique"] / row["tco2e"] if row["tco2e"] else 0,
        axis=1,
    )
    companies = [
        {
            "code": row.company_code,
            "name": row.company_name,
            "tco2e": float(row.tco2e),
            "physique": float(row.physique),
            "monetaire": float(row.monetaire),
            "part_physique": float(row.part_physique),
            "scope1": float(row.scope1),
            "scope2": float(row.scope2),
            "scope3": float(row.scope3),
            "nb_constats": int(row.nb_constats) if pd.notna(row.nb_constats) else 0,
            "nb_bloquants": int(row.nb_bloquants) if pd.notna(row.nb_bloquants) else 0,
        }
        for row in by_company.itertuples()
    ]

    by_poste = (
        bilan.groupby("poste", as_index=False)["tco2e"]
        .sum()
        .sort_values("tco2e", ascending=False)
    )
    postes = [
        {
            "poste": row.poste,
            "tco2e": float(row.tco2e),
            "part": 100 * float(row.tco2e) / total if total else 0,
        }
        for row in by_poste.itertuples()
    ]

    by_method = (
        bilan.groupby("method", as_index=False)
        .agg(tco2e=("tco2e", "sum"), lignes=("lignes", "sum"))
        .sort_values("tco2e", ascending=False)
    )
    methods = [
        {
            "method": row.method,
            "tco2e": float(row.tco2e),
            "lignes": int(row.lignes),
            "part": 100 * float(row.tco2e) / total if total else 0,
        }
        for row in by_method.itertuples()
    ]

    top = (
        bilan.groupby(["poste", "activity"], as_index=False)["tco2e"]
        .sum()
        .sort_values("tco2e", ascending=False)
        .head(10)
    )
    top_activities = [
        {
            "poste": row.poste,
            "activity": row.activity,
            "tco2e": float(row.tco2e),
            "part": 100 * float(row.tco2e) / total if total else 0,
        }
        for row in top.itertuples()
    ]

    return {
        "total_tco2e": total,
        "total_physique": total_physique,
        "part_physique": part_physique,
        "scopes": scopes,
        "companies": companies,
        "postes": postes,
        "methods": methods,
        "top_activities": top_activities,
        "nb_constats": int(len(data.quality)),
        "nb_bloquants": int((data.quality["severity"] == "bloquant").sum()),
    }


def build_quality_view(data: DashboardData) -> dict:
    """Agrège les constats et prépare leur affichage."""
    quality = data.quality
    summary = data.quality_summary
    constats = []
    for row in quality.itertuples():
        constats.append(
            {
                "constat_id": row.constat_id,
                "company_code": row.company_code,
                "company_name": row.company_name,
                "family": row.family,
                "family_label": FAMILY_LABELS.get(row.family, row.family),
                "severity": row.severity,
                "certitude": row.certitude,
                "certitude_label": CERTITUDE_LABELS.get(row.certitude, row.certitude),
                "statut": row.statut,
                "statut_label": STATUT_LABELS.get(row.statut, row.statut),
                "traitement": row.traitement,
                "traitement_label": TRAITEMENT_LABELS.get(
                    row.traitement, row.traitement
                ),
                "title": row.title,
                "proof": row.proof,
                "question": row.business_question,
                "impact_text": fmt_impact(
                    row.impact_tco2e, row.impact_eur, row.impact_type
                ),
                "impact_tco2e": float(row.impact_tco2e)
                if pd.notna(row.impact_tco2e)
                else None,
                "impact_eur": float(row.impact_eur) if pd.notna(row.impact_eur) else None,
                "impact_group": row.impact_group
                if pd.notna(row.impact_group)
                else None,
                "impact_type": row.impact_type,
            }
        )

    by_family = (
        quality.groupby("family", as_index=False)
        .size()
        .rename(columns={"size": "nb"})
        .sort_values("nb", ascending=False)
    )
    families = [
        {
            "code": row.family,
            "label": FAMILY_LABELS.get(row.family, row.family),
            "nb": int(row.nb),
        }
        for row in by_family.itertuples()
    ]

    by_company = summary.copy()
    by_company["company_name"] = by_company["company_name"].fillna("Toutes les entreprises")
    companies = [
        {
            "code": row.company_code,
            "name": row.company_name,
            "nb_constats": int(row.nb_constats),
            "nb_bloquants": int(row.nb_bloquants),
            "impact_tco2e": float(row.impact_tco2e),
            "impact_eur": float(row.impact_eur),
        }
        for row in by_company.itertuples()
    ]

    return {
        "total": int(len(quality)),
        "bloquants": int((quality["severity"] == "bloquant").sum()),
        "alertes": int((quality["severity"] == "alerte").sum()),
        "infos": int((quality["severity"] == "info").sum()),
        "certains": int((quality["certitude"] == "certain").sum()),
        "a_confirmer": int((quality["certitude"] == "a_confirmer").sum()),
        "statut_a_confirmer": int((quality["statut"] == "a_confirmer").sum()),
        "statut_ouverts": int((quality["statut"] == "ouvert").sum()),
        "constats": constats,
        "families": families,
        "companies": companies,
        "impact_tco2e": float(summary["impact_tco2e"].sum()),
        "impact_eur": float(summary["impact_eur"].sum()),
        "company_options": sorted(quality["company_code"].unique().tolist()),
        "family_options": sorted(families, key=lambda item: item["label"]),
        "status_options": [
            {"code": code, "label": STATUT_LABELS.get(code, code)}
            for code in sorted(quality["statut"].unique().tolist())
        ],
    }


def build_ingestion_view(data: DashboardData) -> dict:
    """Prépare la vue ingestion, quarantaine et fraîcheur."""
    ingestion = data.ingestion
    quarantine = data.quarantine
    freshness = data.freshness

    sources = []
    for row in ingestion.itertuples():
        sources.append(
            {
                "company_code": row.company_code,
                "source_id": row.source_id,
                "source_type": row.source_type,
                "rows_read": int(row.rows_read),
                "rows_loaded": int(row.rows_loaded),
                "rows_quarantined": int(row.rows_quarantined),
                "status": row.status,
                "duration": fmt_duration_ms(row.duration_ms),
                "finished_at": fmt_datetime(row.finished_at),
            }
        )

    freshness_rows = []
    for row in freshness.itertuples():
        note = ""
        if row.source_type == "vehicles":
            note = "Référentiel"
        elif (
            row.source_type == "electricity"
            and pd.notna(row.max_date)
            and pd.Timestamp(row.max_date) < pd.Timestamp("2025-12-01")
        ):
            note = "Mois manquants"
        freshness_rows.append(
            {
                "company_code": row.company_code,
                "source_type": row.source_type,
                "min_date": fmt_date(row.min_date),
                "max_date": fmt_date(row.max_date),
                "nb_lignes": int(row.nb_lignes),
                "nb_mois": int(row.nb_mois),
                "note": note,
            }
        )

    quarantine_rows = [
        {
            "company_code": row.company_code,
            "source_id": row.source_id,
            "reason_code": row.reason_code,
            "nb_lignes": int(row.nb_lignes),
            "first_seen_at": fmt_datetime(row.first_seen_at),
            "last_seen_at": fmt_datetime(row.last_seen_at),
        }
        for row in quarantine.itertuples()
    ]

    last_run = ingestion["finished_at"].max() if not ingestion.empty else None
    return {
        "sources": sources,
        "nb_sources": int(len(ingestion)),
        "rows_loaded": int(ingestion["rows_loaded"].sum()),
        "rows_quarantined": int(ingestion["rows_quarantined"].sum()),
        "nb_failures": int((ingestion["status"] != "success").sum()),
        "last_run": fmt_datetime(last_run),
        "quarantine_total": int(quarantine["nb_lignes"].sum()),
        "quarantine": quarantine_rows,
        "freshness": freshness_rows,
        "dbt": data.dbt,
    }


def build_status_text(data: DashboardData) -> str:
    """Construit la synthèse console de `make status`."""
    bilan = build_bilan_view(data)
    quality = build_quality_view(data)
    ingestion = build_ingestion_view(data)

    company_text = " | ".join(
        f"{row['code']} {fmt_tco2e(row['tco2e'])}" for row in bilan["companies"]
    )
    quality_label = plural(quality["total"], "constat", "constats")
    bloquant_label = plural(quality["bloquants"], "bloquant", "bloquants")
    alerte_label = plural(quality["alertes"], "alerte", "alertes")
    info_label = plural(quality["infos"], "info", "infos")
    source_label = plural(ingestion["nb_sources"], "source", "sources")
    lines = [
        "Pipeline BEGES — statut",
        f"Bilan       : {fmt_tco2e(bilan['total_tco2e'])} tCO2e | "
        f"physique {fmt_pct(bilan['part_physique'])}",
        f"Entreprises : {company_text}",
        f"Qualité     : {quality['total']} {quality_label} | "
        f"{quality['bloquants']} {bloquant_label} | "
        f"{quality['alertes']} {alerte_label} | "
        f"{quality['infos']} {info_label}",
        f"Statuts     : {quality['statut_a_confirmer']} à confirmer | "
        f"{quality['statut_ouverts']} ouverts",
        f"Ingestion   : {ingestion['nb_sources']} {source_label} | "
        f"{fmt_number(ingestion['rows_loaded'], 0)} lignes | "
        f"{ingestion['quarantine_total']} quarantaine | "
        f"dernier run {ingestion['last_run']}",
    ]

    if data.dbt is None:
        lines.append("dbt         : indisponible (lancer make dbt-build)")
    else:
        lines.append(
            f"dbt         : {data.dbt.pass_count} PASS | "
            f"{data.dbt.error_count} échec | "
            f"{data.dbt.elapsed_seconds:.1f} s".replace(".", ",")
        )

    site_index = SITE_DIR / "index.html"
    if site_index.exists():
        generated = datetime.fromtimestamp(site_index.stat().st_mtime)
        lines.append(f"Site        : {site_index} (généré le {fmt_datetime(generated)})")
    else:
        lines.append("Site        : absent (lancer make dashboard)")

    return "\n".join(lines)
