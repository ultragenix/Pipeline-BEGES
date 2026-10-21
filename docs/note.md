# Carnet de bord — Pipeline BEGES

> Projet de démonstration data engineering.
> Données fictives. Ce document n'est pas un audit réglementaire.

## 0. Pourquoi ce projet

Je voulais un cas qui relie la data et la transition environnementale.
Le BEGES est un bon prétexte : données hétérogènes, enjeux de périmètre,
double comptage, utilisateurs métier non techniques.

La démo est un bonus pour un entretien. Elle montre la curiosité, la méthode
et la capacité à apprendre Azure, pas une expertise réglementaire.

## 1. Ce que je savais / ce que je ne savais pas

**Je savais :** Python, SQL, dbt, culture data, GCP.

**Je ne savais pas :** BEGES, FEC, Azure, managed identity, Terraform azurerm.

**J'ai appris :** un pipeline fiable commence par le profiling des fichiers ;
les doublons apparents ne sont pas toujours des doublons ; les règles métier
non documentées doivent être signalées, pas devinées.

## 2. Méthode de travail

- Je pilote, l'assistant propose.
- Aucune écriture sans validation explicite.
- Une étape = un livrable = une preuve.
- Le carnet est rempli au fil de l'eau, pas après coup.
- La correction n'est pas ouverte avant la comparaison.

## 3. Journal

### 2026-10-21 — Cadrage et reset

**Objectif :** poser les règles et le plan avant de construire.

**Ce qu'on a fait :**
- retour au commit initial après une première tentative trop large ;
- création de `AGENTS.md` ;
- décision d'un dictionnaire avec un fichier par entreprise ;
- ajout d'un registre d'anomalies par entreprise, orienté questions métier ;
- décision de Terraform pour Azure ;
- définition des quality gates.

**Difficulté :** la première tentative a sauté l'étape de cadrage et produit
trop de structure d'un coup.

**Décision :** on réduit le périmètre, pas la rigueur. Chaque écriture est
proposée, validée, puis vérifiée.

**À retenir :** un projet réel commence par le cadre et les preuves, pas par le code.

### 2026-10-21 — Fiches KAY et VAC

**Objectif :** compléter le dictionnaire et le registre d'anomalies pour les deux autres
entreprises.

**Livrables :**
- `docs/dictionnaire-donnees/KAY.md`, `VAC.md`
- `docs/anomalies/KAY.md`, `VAC.md`

**Décision :** KAY a 14 anomalies, VAC 11 ; les contrôles positifs sont documentés.

**À retenir :** KAY concentre les problèmes de périmètre et de doublons ; VAC les dérives
de schéma et les annulations.

### 2026-10-21 — Étape 2 : configuration d'ingestion

**Objectif :** décrire les 17 fichiers dans une configuration validable.

**Livrables :**
- `config/sources.yml` et `config/companies/{KAY,FAN,VAC}.yml`
- `config/emission_factors.yml`, `config/account_mapping.csv`, `config/airports.csv`
- `src/beges/config.py`
- tests séparés : loader, types de sources, entreprises paramétrées

**Résultats :**
- `uv run pytest` : 11 tests passés
- `make config-check` : 3 entreprises, 9 sites, 17 sources, 0 erreur
- `make test-company CODE=FAN` : 1 test, 2 désélectionnés

**Décision :** tests paramétrés par entreprise ; ajouter un client ne réécrit pas les tests.

**À retenir :** la configuration est la source de vérité pour l'ingestion.

### 2026-10-21 — Étape 3 : ingestion config-driven

**Objectif :** lire les 17 fichiers via la configuration et écrire des tables brutes
dans DuckDB, avec journal et quarantaine.

**Livrables :**
- `src/beges/ingest.py`
- `tests/ingestion/` : conftest, entreprises, sources, pipeline
- `make ingest` et `make ingest-company CODE=...`
- `raw.fec`, `raw.electricity`, `raw.fuel`, `raw.refrigerants`, `raw.flights`,
  `raw.vehicles`
- `raw.ingestion_log`, `raw.quarantine`
- `docs/warehouse.md` : référence de la couche physique `raw`

**Résultats :**
- `make ingest` : 3 entreprises, 17 fichiers, 8 263 lignes, 0 quarantaine.
- `uv run pytest` : 40 tests passés.
- `make test-company CODE=KAY` : 5 tests passés, 10 désélectionnés.
- `make lint` : OK.
- Tables : 1 999 FEC, 95 électricité, 5 879 carburant, 57 fluides, 187 vols,
  46 véhicules.

**Décision :** les tables brutes gardent les colonnes canoniques typées, les
métadonnées de traçabilité et la ligne source complète en JSON ; les corrections
métier restent en aval.

**Difficulté :** deux fichiers `test_companies.py` entraient en collision à
l'import ; `tests/ingestion/__init__.py` isole les modules. `executemany` était
lent sur DuckDB ; une insertion multi-lignes par paquets de 500 ramène
l'ingestion complète sous 2 secondes.

**À retenir :** l'ingestion ne corrige rien : elle charge, trace et isole. Les
doublons, les écarts FEC et les règles métier seront traités en dbt et en qualité.

### 2026-10-21 — Étape 4 : modèles dbt

**Objectif :** construire le bilan à partir de `raw`, séparer méthode physique et
méthode monétaire, produire des marts et tester l'anti-double comptage.

**Livrables :**
- `dbt/` : projet, profil DuckDB, macro haversine, 20 modèles, 181 tests
- `docs/dbt.md` : documentation des couches, règles et résultats
- `make dbt-build`, `make dbt-test`, `make dbt-docs`
- correction de `config/account_mapping.csv` (BOM, 7 lignes incomplètes)
- `tests/config/test_reference_files.py`

**Résultats :**
- `dbt build` : 20 modèles, 181 tests, PASS=201, 0 erreur.
- `fct_emissions` : 6 191 lignes ; `fct_exclusions` : 693 ; `mart_beges` : 48.
- Bilan : **16 231,298 tCO₂e**, dont **44,7 % en méthode physique**.
- KAY 4 094,673 ; FAN 7 894,347 ; VAC 4 242,278.
- Exclusions : 412 `ADBLUE`, 9 `PRODUIT 47`, 3 doublons, 3 annulations,
  2 GWP inconnus, 12 comptes non mappés, 176 remplacements physiques,
  75 lignes hors périmètre.
- `uv run pytest` : 43 tests passés.

**Décision :** le physique remplace le monétaire sur `60611/60622/62511` ; les
comptes hors périmètre, non mappés, doublons et annulations sont exclus mais
listés dans `fct_exclusions` ; les choix métier provisoires sont flagués.

**Difficulté :** les feuilles Excel partagent les mêmes numéros de ligne ; la
feuille est maintenant incluse dans `emission_id`. dbt 1.12 exige `arguments`
pour `accepted_values`. Le CSV de mapping avait un BOM et 7 lignes à 6 colonnes :
corrigé et couvert par un test.

**À retenir :** un `dbt build` vert ne signifie pas des données parfaites : 693
lignes sont écartées et listées, et les questions métier restent ouvertes.

## 4. Décisions

| Date | Décision | Pourquoi |
|---|---|---|
| 21/10 | `AGENTS.md` avec validation obligatoire | garder le contrôle, éviter les dérives |
| 21/10 | Un fichier de dictionnaire par entreprise | lisibilité, passage à l'échelle |
| 21/10 | Un registre d'anomalies par entreprise | séparer la structure des données des questions métier |
| 21/10 | Tests de configuration paramétrés par entreprise | ajouter un client sans réécrire les tests |
| 21/10 | Schémas communs séparés | éviter la duplication |
| 21/10 | Terraform pour Azure | rigueur, plan/apply, reproductibilité |
| 21/10 | uv + Docker | reproductibilité locale et cloud |
| 21/10 | Dashboard statique + observabilité | demo portable, pas de serveur |
| 21/10 | Tables raw fidèles + `raw_row` JSON | aucune colonne source perdue |
| 21/10 | Rechargement par source en transaction | idempotence, pas de chargement partiel |
| 21/10 | Sites et MWh normalisés à l'ingestion | raw exploitable, valeur brute conservée |
| 21/10 | Aucun dédoublonnage ni correction à l'ingestion | les constats restent visibles en qualité |
| 21/10 | Physique remplace le monétaire sur `60611/60622/62511` | éviter le double comptage |
| 21/10 | Lignes écartées visibles dans `fct_exclusions` | aucune correction silencieuse |
| 21/10 | Choix métier provisoires flagués | ne pas trancher sans retour métier |
| 21/10 | Référentiels dbt lus depuis `config/` | la configuration reste la source de vérité |

## 5. Difficultés

| Difficulté | Leçon |
|---|---|
| Première tentative trop large | cadrer avant de coder |
| Docker Desktop non intégré à WSL | vérifier l'environnement avant de bâtir |
| Données hétérogènes | profiler avant d'écrire l'ingestion |
| Deux `test_companies.py` en collision | isoler les modules de test par paquet |
| `executemany` lent sur DuckDB | insérer par paquets multi-lignes |
| Lignes Excel répétées entre feuilles | inclure la feuille dans la clé d'émission |
| `accepted_values` sans `arguments` sous dbt 1.12 | suivre la syntaxe des tests génériques |
| CSV de mapping avec BOM et lignes incomplètes | valider les référentiels avant dbt |

## 6. Questions ouvertes

- KAY : site LPT-ATL sans relevé électrique.
- KAY : doublon de juillet et régularisation de mai.
- VAC : décembre manquant.
- VAC : billets annulés et doublons.
- KAY : ADBLUE et PRODUIT 47.
- FAN : carburant sans litres.
- FAN : fluide `R-?`.
- KAY : compte `6288000` non mappé.
- FAN : écriture `AC000042` déséquilibrée.

Ces questions restent ouvertes ; elles seront formalisées à l'étape 5 (qualité),
avec une preuve, une question métier et un statut.

## 7. À retenir pour l'entretien

- « Je réduis le périmètre, pas la rigueur. »
- « Un fichier par entreprise ; à 300, on génère depuis un catalogue. »
- « Le dictionnaire décrit, le registre d'anomalies questionne. »
- « Les règles métier manquées sont des règles métier, pas de l'ingénierie data. »
- « Un build vert ne veut pas dire des données parfaites : 693 lignes écartées et listées. »
- « Terraform, plan avant apply, destroy après la démo. »

## 8. Prochaine étape

Étape 4 terminée : 20 modèles dbt, 181 tests, bilan à 16 231,298 tCO₂e et
693 lignes écartées listées.
Prochaine étape : étape 5, contrôles qualité et formalisation des constats.
