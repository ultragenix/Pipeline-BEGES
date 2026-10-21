# Plan de construction — Pipeline BEGES

> Projet de démonstration data engineering.
> Les entreprises et les données sont fictives.
> Statut : étape 0 — cadrage.

## 0. Objectif

Construire un pipeline BEGES crédible pour un entretien data engineer :
- partir de fichiers clients hétérogènes ;
- produire un bilan traçable et testé ;
- signaler les anomalies sans les corriger en silence ;
- restituer le résultat dans un dashboard compréhensible par un consultant RSE ;
- montrer une démarche Azure avec Terraform.

La démo est un bonus. Elle doit montrer la curiosité, la rigueur et la capacité
à apprendre, pas prétendre à une expertise BEGES ou Azure.

## 1. Contraintes

- 10 h de construction, démo le soir.
- Docker comme mode d'exécution de référence.
- uv pour les dépendances Python.
- Terraform pour Azure.
- Repo public, données fictives uniquement.
- Correction comparée après coup, pas avant.
- Une étape = un livrable = une validation.

## 2. Principe de progression

1. Je propose un fichier, son but, son contenu et son rollback.
2. Tu valides explicitement.
3. J'écris.
4. Je montre `git status` et le résultat.
5. On passe à l'étape suivante.

Aucune étape suivante n'est lancée sans validation.

## 3. Étapes

### Étape 0 — Cadrage

Livrables :
- `AGENTS.md`
- `docs/plan.md`
- `docs/note.md`

Critère de sortie : le plan et le carnet sont validés, aucune autre écriture.

### Étape 1 — Dictionnaire par entreprise

Structure :

```text
docs/dictionnaire-donnees/
├── README.md
├── schemas-communs.md
├── _modele-entreprise.md
├── KAY.md
├── FAN.md
└── VAC.md
```

- `schemas-communs.md` : FEC, électricité, carburant, fluides, vols.
- Un fichier par entreprise : uniquement les spécificités.
- `_modele-entreprise.md` : modèle pour un nouveau client.
- `README.md` : index, conventions, stratégie à l'échelle.

Critère de sortie : 17/17 fichiers décrits, faits observés séparés des hypothèses.

### Étape 2 — Configuration d'ingestion

Livrables :
- `config/companies/KAY.yml`, `FAN.yml`, `VAC.yml`
- `config/sources.yml`
- script de validation de la configuration

Critère de sortie : chaque source a format, encodage, délimiteur, colonnes, clé.

### Étape 3 — Ingestion

Livrables :
- script d'ingestion config-driven ;
- journal d'ingestion ;
- quarantaine ;
- tests.

Critère de sortie : 17/17 fichiers ingérés, zéro perte silencieuse, idempotence.

### Étape 4 — dbt

Livrables :
- staging, intermediate, marts ;
- tests dbt ;
- documentation et lineage.

Critère de sortie : `dbt build` vert, anti-double comptage testé.

### Étape 5 — Qualité

Livrables :
- contrôles génériques ;
- registre de constats ;
- questions métier ;
- impacts tCO₂e quand calculables.

Critère de sortie : constats lisibles par un consultant RSE, aucune correction silencieuse.

### Étape 6 — Dashboard et observabilité

Livrables :
- dashboard bilan ;
- page observabilité (ingestion, fraîcheur, tests, constats) ;
- `make status`.

Critère de sortie : bilan et anomalies consultables, accessible et lisible.

### Étape 7 — Docker, CI, Pages

Livrables :
- image Docker validée ;
- `docker compose` ;
- workflow GitHub Actions ;
- GitHub Pages.

Critère de sortie : clone propre + `docker compose up` fonctionne, CI verte.

### Étape 8 — Azure et Terraform

Livrables :
- ADLS Gen2, ACR, ACI, Azure SQL serverless ;
- Terraform (`fmt`, `validate`, `plan`, `apply`, `destroy`) ;
- managed identity, pas de secret ;
- captures et coût documenté.

Critère de sortie : job vert, `terraform plan` relu, `destroy` vérifié.

### Étape 9 — Démo et correction

Livrables :
- script de démo 5-6 min ;
- Q&A ;
- comparaison avec la correction ;
- limites et next steps.

Critère de sortie : démo répétée deux fois, écarts expliqués.

## 4. Quality gates

| Étape | Gate | Preuve |
|---|---|---|
| 0 Cadrage | Plan et règles validés | `AGENTS.md`, `docs/plan.md`, `docs/note.md` |
| 1 Dictionnaire | 17/17 fichiers, un fichier par entreprise | dossier complet + relecture |
| 2 Configuration | Chaque source décrite | `config/sources.yml` + validation |
| 3 Ingestion | 17/17, journal, quarantaine | `make ingest`, tests |
| 4 dbt | Build vert, anti-double comptage | `dbt build`, lineage |
| 5 Qualité | Constats et questions métier | registre, impacts |
| 6 Dashboard | Bilan + observabilité | URL, captures |
| 7 Docker/CI | Clone propre, CI verte | badge, `docker compose up` |
| 8 Azure | IaC, identité, coût, destroy | `terraform plan`, captures |
| 9 Démo | 5-6 min, Q&A, limites | répétition |

## 5. Definition of Done

- 17/17 fichiers ingérés, journal et quarantaine vérifiés.
- `dbt build` vert, test anti-double comptage, lineage disponible.
- 15 constats minimum, dont 2 racontés de bout en bout.
- Dashboard bilan + observabilité accessible en ligne.
- `docker compose up` fonctionne depuis un clone propre.
- CI verte, aucun secret, licence et disclaimer.
- Azure : déploiement minimal, captures, coût < 5 €, destroy documenté.
- Démo de 5-6 minutes répétée deux fois, Q&A prêt.

## 6. Passage à l'échelle

À 3 entreprises, un fichier Markdown par entreprise est lisible.
À 300, on ne maintient pas 300 fichiers à la main :

1. catalogue machine-readable par entreprise (`config/companies/*.yml`) ;
2. schéma canonique commun + overrides ;
3. profiling automatisé ;
4. génération des fiches Markdown depuis le catalogue ;
5. data catalog (Purview, DataHub, OpenMetadata) pour recherche, lineage, ownership ;
6. data contracts et détection de dérive ;
7. revue par un data steward ;
8. cloisonnement des données clients dans un repo privé ou un namespace protégé.

## 7. Risques

| Risque | Mitigation |
|---|---|
| Périmètre trop large | couper Azure à 1 h, garder les captures |
| Démo live qui échoue | pré-run, captures, pages statiques |
| Règles métier inconnues | constats « à confirmer », journal des retours |
| Secrets dans le repo | `.gitignore`, managed identity, scan avant push |
| Coût Azure | budget, auto-pause, `destroy` |
| Surpromesse | limites explicites dans le README et la démo |

## 8. Hors périmètre

- Kafka, Spark, Airflow, Kubernetes.
- Temps réel.
- Multi-tenant complet.
- Power BI Embedded.
- Certification BEGES réglementaire.
