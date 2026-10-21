SHELL := /bin/bash

UV ?= uv
DBT ?= $(UV) run dbt
DATA_DIR ?= donnees-sources-fictives/raw
BEGES_DB ?= $(CURDIR)/data/warehouse/beges.duckdb
export DATA_RAW_DIR := $(CURDIR)/$(DATA_DIR)
export BEGES_DB_PATH := $(BEGES_DB)
export BEGES_CONFIG_DIR := $(CURDIR)/config

.PHONY: help sync lock lint format test test-company config-check config-check-company ingest ingest-company dbt-build dbt-test dbt-docs clean

help:
	@echo "Pipeline BEGES"
	@echo ""
	@echo "  make sync                  Installe les dépendances avec uv"
	@echo "  make lock                  Met à jour uv.lock"
	@echo "  make lint                  Vérifie le code avec Ruff"
	@echo "  make format                Formate le code avec Ruff"
	@echo "  make test                  Lance tous les tests"
	@echo "  make test-company CODE=KAY Lance les tests d'une entreprise"
	@echo "  make config-check          Valide toute la configuration"
	@echo "  make config-check-company CODE=KAY  Valide une entreprise"
	@echo "  make ingest                Ingère toutes les sources dans DuckDB"
	@echo "  make ingest-company CODE=KAY  Ingère une entreprise"
	@echo "  make dbt-build             Construit et teste les modèles dbt"
	@echo "  make dbt-test              Lance les tests dbt"
	@echo "  make dbt-docs              Génère la documentation et le lineage dbt"
	@echo "  make clean                 Nettoie les caches"

sync:
	$(UV) sync

lock:
	$(UV) lock

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff format .

test:
	$(UV) run pytest

test-company:
	@test -n "$(CODE)" || (echo "Usage: make test-company CODE=KAY" && exit 1)
	$(UV) run pytest tests/config/test_companies.py tests/ingestion/test_companies.py -k "$(CODE)"

config-check:
	$(UV) run python -m beges.config --check

config-check-company:
	@test -n "$(CODE)" || (echo "Usage: make config-check-company CODE=KAY" && exit 1)
	$(UV) run python -m beges.config --check --company "$(CODE)"

ingest:
	$(UV) run python -m beges.ingest --all

ingest-company:
	@test -n "$(CODE)" || (echo "Usage: make ingest-company CODE=KAY" && exit 1)
	$(UV) run python -m beges.ingest --company "$(CODE)"

dbt-build:
	@test -f "$(BEGES_DB)" || (echo "Base absente: lancer make ingest" && exit 1)
	$(DBT) build --project-dir dbt --profiles-dir dbt

dbt-test:
	@test -f "$(BEGES_DB)" || (echo "Base absente: lancer make ingest" && exit 1)
	$(DBT) test --project-dir dbt --profiles-dir dbt

dbt-docs:
	@test -f "$(BEGES_DB)" || (echo "Base absente: lancer make ingest" && exit 1)
	$(DBT) docs generate --project-dir dbt --profiles-dir dbt

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
