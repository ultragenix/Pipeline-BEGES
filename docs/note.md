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

### 2026-10-21 — Étape 5 : qualité et constats

**Objectif :** transformer les 38 questions du registre et les 693 exclusions en
constats calculés, avec preuve, statut, traitement et impact.

**Livrables :**
- `config/quality/{KAY,FAN,VAC,_common}.yml` : 42 constats, un fichier par entreprise.
- `dbt/models/quality/` : `int_quality_findings`, `quality_constats`, `quality_summary`.
- 7 tests dbt de cohérence du registre.
- `src/beges/quality.py` et `make quality`.
- `docs/quality.md` : taxonomie, architecture, résultats, deux constats racontés.
- Sections 5 dans `docs/anomalies/KAY.md`, `FAN.md`, `VAC.md`.

**Résultats :**
- `dbt build` : **PASS=267**, 25 modèles, 242 tests, 0 erreur.
- 42 constats : **13 bloquants, 21 alertes, 8 infos**.
- 23 constats certains et 19 avec une certitude à confirmer ; 38 au statut
  à confirmer et 4 ouverts.
- Les 10 familles du cahier des charges sont couvertes.
- KAY 16, FAN 13, VAC 12, transverse 1.
- `uv run pytest` : **58 passed**.
- `make lint` : OK.
- 4 nouveaux constats : `KAY-15` CET, `KAY-16` réservoir, `VAC-12` avoirs,
  `GEN-01` classe Affaires.
- Écarts de preuve de l'étape 1 documentés : `KAY-06`, `KAY-07`, `KAY-08`,
  `KAY-11`, `FAN-09`.

**Décision :** le registre est machine-readable et séparé par entreprise. Le
YAML porte la question et la taxonomie ; le SQL détecte et calcule ; les tests
vérifient qu'aucun constat n'est orphelin.

**Difficulté :** les impacts de `KAY-01`/`KAY-09` et `VAC-01`/`VAC-02` décrivent
le même problème ; ils sont dédupliqués par `impact_group`. Certains chiffres
narratifs de l'étape 1 ne se reproduisaient pas exactement.

**À retenir :** un build vert ne suffit pas. Chaque exclusion doit pouvoir être
reliée à une question métier et à un impact, sans correction silencieuse.

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
| 21/10 | Registre qualité par entreprise dans `config/quality/` | même principe que le dictionnaire et les anomalies |
| 21/10 | Constat = YAML + contrôle SQL + test de couverture | aucun constat orphelin, ajout sans réécrire les tests |
| 21/10 | Impacts partagés via `impact_group` | éviter le double comptage KAY et VAC |
| 21/10 | Certitude, statut et traitement séparés | ne pas confondre fait observé, réponse métier et traitement |

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
| Chiffres narratifs de l'étape 1 non reproductibles | recalculer, documenter l'écart, ne pas réécrire l'historique |
| `format()` DuckDB utilise `{}` et non `%s` | utiliser `printf` pour les preuves chiffrées |
| Écriture déséquilibrée comptée trois fois | agréger par écriture avant de sommer l'impact |
| Impacts KAY-01/KAY-09 et VAC-01/VAC-02 partagés | `impact_group` et déduplication dans la synthèse |

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
- KAY : CET `6351100` hors périmètre ?
- KAY : transaction de 400 L pour un réservoir de 300 L.
- VAC : avoirs négatifs sur achats alimentaires.
- Toutes : facteur d'émission de la classe Affaires.

Les 38 questions du registre sont désormais formalisées dans 42 constats
calculés (`docs/quality.md`), avec une preuve, un statut, un traitement et un
impact. Les réponses métier restent à recevoir.

## 7. À retenir pour l'entretien

- « Je réduis le périmètre, pas la rigueur. »
- « Un fichier par entreprise ; à 300, on génère depuis un catalogue. »
- « Le dictionnaire décrit, le registre d'anomalies questionne. »
- « Les règles métier manquées sont des règles métier, pas de l'ingénierie data. »
- « Un build vert ne veut pas dire des données parfaites : 693 lignes écartées et listées. »
- « Un constat, c'est une preuve, une question métier et un impact. »
- « Les impacts partagés ne s'additionnent pas : KAY-ELEC-GAP et VAC-ELEC-GAP. »
- « Terraform, plan avant apply, destroy après la démo. »

## 8. Prochaine étape

Étape 5 terminée : 42 constats calculés, 13 bloquants, 10 familles couvertes,
`make quality` opérationnel et deux constats racontés de bout en bout.
Prochaine étape : étape 6, dashboard bilan et page d'observabilité.
