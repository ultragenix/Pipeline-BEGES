SHELL := /bin/bash

UV ?= uv
DATA_DIR ?= donnees-sources-fictives/raw
export DATA_RAW_DIR := $(CURDIR)/$(DATA_DIR)

.PHONY: help sync lock lint format test test-company config-check config-check-company clean

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
	$(UV) run pytest tests/config/test_companies.py -k "$(CODE)"

config-check:
	$(UV) run python -m beges.config --check

config-check-company:
	@test -n "$(CODE)" || (echo "Usage: make config-check-company CODE=KAY" && exit 1)
	$(UV) run python -m beges.config --check --company "$(CODE)"

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
