"""Chargement et validation de la configuration d'ingestion."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = Path(os.environ.get("BEGES_CONFIG_DIR", ROOT / "config"))
DATA_RAW_DIR = Path(
    os.environ.get("DATA_RAW_DIR", ROOT / "donnees-sources-fictives" / "raw")
)

DATE_SOURCE_TYPES = {
    "fec",
    "electricity",
    "electricity_xlsx",
    "fuel",
    "refrigerants",
    "flights",
}


class ConfigError(ValueError):
    """Erreur de configuration."""


@dataclass(frozen=True)
class SourceType:
    name: str
    format: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()
    default_column_map: dict[str, str] = field(default_factory=dict)
    key: tuple[str, ...] = ()


@dataclass(frozen=True)
class Site:
    code: str
    name: str
    pdl: str


@dataclass(frozen=True)
class Source:
    id: str
    type: str
    path: str
    encoding: str = "utf-8"
    delimiter: str = ","
    decimal: str = "."
    date_format: str | None = None
    periodicity: str = "event"
    column_map: dict[str, str] = field(default_factory=dict)
    sheets: dict[str, dict[str, str]] = field(default_factory=dict)
    header_row: int | None = None


@dataclass(frozen=True)
class Company:
    code: str
    name: str
    city: str
    sector: str
    employees: int
    exercise: int
    sites: dict[str, Site]
    sources: tuple[Source, ...]

    @property
    def source_count(self) -> int:
        return len(self.sources)


@dataclass(frozen=True)
class Config:
    companies: dict[str, Company]
    source_types: dict[str, SourceType]

    @property
    def site_count(self) -> int:
        return sum(len(company.sites) for company in self.companies.values())

    @property
    def source_count(self) -> int:
        return sum(company.source_count for company in self.companies.values())


def _require(mapping: dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping or mapping[key] in (None, ""):
        raise ConfigError(f"{context}: champ obligatoire manquant: {key}")
    return mapping[key]


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except OSError as exc:
        raise ConfigError(f"Impossible de lire {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML invalide dans {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: la racine doit être un objet YAML")
    return data


def load_source_types(path: Path) -> dict[str, SourceType]:
    data = _read_yaml(path)
    raw_types = data.get("source_types")
    if not isinstance(raw_types, dict) or not raw_types:
        raise ConfigError(f"{path}: 'source_types' doit être un objet non vide")

    result: dict[str, SourceType] = {}
    for name, raw in raw_types.items():
        if not isinstance(raw, dict):
            raise ConfigError(f"{path}: type de source invalide: {name}")
        required = tuple(raw.get("required_fields", []))
        optional = tuple(raw.get("optional_fields", []))
        default_map = dict(raw.get("default_column_map", {}))
        key = tuple(raw.get("key", []))
        if not required:
            raise ConfigError(f"{path}: {name}: 'required_fields' est vide")
        if not set(key).issubset(set(required) | set(optional)):
            raise ConfigError(f"{path}: {name}: 'key' contient un champ non déclaré")
        result[name] = SourceType(
            name=name,
            format=str(_require(raw, "format", f"{path}:{name}")),
            required_fields=required,
            optional_fields=optional,
            default_column_map=default_map,
            key=key,
        )
    return result


def _validate_source_path(source: Source, data_raw_dir: Path) -> None:
    path = data_raw_dir / source.path
    if not path.exists():
        raise ConfigError(f"Source {source.id}: fichier introuvable: {path}")


def _validate_column_map(
    source: Source,
    source_type: SourceType,
    column_map: dict[str, str],
    context: str,
) -> None:
    missing = [field for field in source_type.required_fields if field not in column_map]

    if (
        source_type.name == "electricity"
        and "month" not in column_map
        and "period_start" not in column_map
    ):
        missing.append("month ou period_start")

    if source_type.name == "electricity_xlsx":
        if not source.sheets:
            raise ConfigError(f"{context}: 'sheets' est obligatoire pour electricity_xlsx")
        for sheet, config in source.sheets.items():
            if not isinstance(config, dict):
                raise ConfigError(f"{context}: feuille {sheet} invalide")
            if "site_code" not in config:
                raise ConfigError(f"{context}: feuille {sheet}: 'site_code' manquant")
            if config.get("unit") not in {"kWh", "MWh"}:
                raise ConfigError(f"{context}: feuille {sheet}: unité invalide")

    if source_type.name in DATE_SOURCE_TYPES and not source.date_format:
        raise ConfigError(f"{context}: 'date_format' est obligatoire")

    if missing:
        raise ConfigError(
            f"{context}: champs canoniques non mappés: {', '.join(missing)}"
        )


def load_company(
    path: Path,
    source_types: dict[str, SourceType],
    data_raw_dir: Path,
) -> Company:
    data = _read_yaml(path)
    code = str(_require(data, "code", str(path)))
    if code != path.stem:
        raise ConfigError(
            f"{path}: code '{code}' différent du nom de fichier '{path.stem}'"
        )

    sites_raw = data.get("sites")
    if not isinstance(sites_raw, dict) or not sites_raw:
        raise ConfigError(f"{path}: 'sites' doit être un objet non vide")
    sites: dict[str, Site] = {}
    for site_code, site_raw in sites_raw.items():
        if not isinstance(site_raw, dict):
            raise ConfigError(f"{path}: site {site_code} invalide")
        sites[site_code] = Site(
            code=site_code,
            name=str(_require(site_raw, "name", f"{path}:{site_code}")),
            pdl=str(_require(site_raw, "pdl", f"{path}:{site_code}")),
        )

    sources_raw = data.get("sources")
    if not isinstance(sources_raw, list) or not sources_raw:
        raise ConfigError(f"{path}: 'sources' doit être une liste non vide")

    sources: list[Source] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(sources_raw, start=1):
        if not isinstance(raw, dict):
            raise ConfigError(f"{path}: source #{index} invalide")
        source_id = str(_require(raw, "id", f"{path}:source#{index}"))
        if source_id in seen_ids:
            raise ConfigError(f"{path}: identifiant de source dupliqué: {source_id}")
        seen_ids.add(source_id)

        type_name = str(_require(raw, "type", f"{path}:{source_id}"))
        if type_name not in source_types:
            raise ConfigError(f"{path}:{source_id}: type inconnu: {type_name}")
        source_type = source_types[type_name]

        column_map = dict(source_type.default_column_map)
        column_map.update(raw.get("column_map", {}) or {})

        source = Source(
            id=source_id,
            type=type_name,
            path=str(_require(raw, "path", f"{path}:{source_id}")),
            encoding=str(raw.get("encoding", "utf-8")),
            delimiter=str(raw.get("delimiter", ",")),
            decimal=str(raw.get("decimal", ".")),
            date_format=raw.get("date_format"),
            periodicity=str(raw.get("periodicity", "event")),
            column_map=column_map,
            sheets=dict(raw.get("sheets", {}) or {}),
            header_row=raw.get("header_row"),
        )
        _validate_source_path(source, data_raw_dir)
        _validate_column_map(source, source_type, column_map, f"{path}:{source_id}")
        sources.append(source)

    return Company(
        code=code,
        name=str(_require(data, "name", str(path))),
        city=str(_require(data, "city", str(path))),
        sector=str(_require(data, "sector", str(path))),
        employees=int(_require(data, "employees", str(path))),
        exercise=int(_require(data, "exercise", str(path))),
        sites=sites,
        sources=tuple(sources),
    )


def load_config(
    config_dir: Path | None = None,
    data_raw_dir: Path | None = None,
) -> Config:
    config_dir = config_dir or CONFIG_DIR
    data_raw_dir = data_raw_dir or DATA_RAW_DIR

    source_types = load_source_types(config_dir / "sources.yml")
    company_files = sorted((config_dir / "companies").glob("*.yml"))
    if not company_files:
        raise ConfigError(f"Aucune entreprise trouvée dans {config_dir / 'companies'}")

    companies: dict[str, Company] = {}
    for path in company_files:
        company = load_company(path, source_types, data_raw_dir)
        if company.code in companies:
            raise ConfigError(f"Code entreprise dupliqué: {company.code}")
        companies[company.code] = company

    return Config(companies=companies, source_types=source_types)


def format_summary(config: Config, company_code: str | None = None) -> str:
    if company_code:
        company = config.companies.get(company_code)
        if company is None:
            raise ConfigError(f"Entreprise inconnue: {company_code}")
        lines = [
            f"Entreprise : {company.code} — {company.name}",
            f"Sites      : {len(company.sites)}",
            f"Sources    : {company.source_count}",
        ]
        for source in company.sources:
            lines.append(f"  - {source.id}: {source.type} ({source.path})")
        return "\n".join(lines)

    lines = [
        "Configuration OK",
        f"Entreprises : {len(config.companies)}",
        f"Sites       : {config.site_count}",
        f"Sources     : {config.source_count}",
        f"Types       : {len(config.source_types)}",
    ]
    for code, company in sorted(config.companies.items()):
        lines.append(
            f"  - {code}: {len(company.sites)} sites, {company.source_count} sources"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Valide la configuration d'ingestion BEGES"
    )
    parser.add_argument("--check", action="store_true", help="Valide la configuration")
    parser.add_argument("--company", help="Valide une seule entreprise")
    parser.add_argument("--config-dir", type=Path, default=CONFIG_DIR)
    parser.add_argument("--data-raw-dir", type=Path, default=DATA_RAW_DIR)
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config_dir, args.data_raw_dir)
        print(format_summary(config, args.company))
    except ConfigError as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
