# Docker, CI et GitHub Pages

> Rendre le pipeline reproductible depuis un clone propre et publier le dashboard.
> Dernière vérification locale : 2026-10-21.
> Données fictives, aucun secret.

## 1. Objectif

La démonstration doit pouvoir tourner sans installer Python, uv, dbt ou DuckDB
sur la machine : un clone, Docker, et `docker compose up --build`. La CI rejoue
la même chaîne et publie `site/` sur GitHub Pages.

## 2. Image Docker

### 2.1 Construction

Le `Dockerfile` est en deux étapes :

| Étape | Rôle |
|---|---|
| `builder` | Python 3.12 slim, uv 0.10.8, `uv sync --frozen --no-dev`, dépendances figées par `uv.lock` |
| `runtime` | Python 3.12 slim, `make`, `libgomp1`, utilisateur `app` (uid 1000), pas de dépendances de développement |

`uv sync --frozen` garantit que l'image utilise exactement `uv.lock`.
`UV_NO_SYNC=1` empêche `uv run` de tenter une synchronisation réseau au runtime.

L'entrypoint `docker/entrypoint.sh` prépare les volumes nommés, qui sont créés
`root:root` par Docker, puis abandonne les privilèges avec `setpriv` :

```text
uid=1000(app) gid=1000(app) groups=1000(app)
```

Le processus du pipeline ne tourne donc pas en root.

### 2.2 Variables

| Variable | Valeur dans l'image |
|---|---|
| `BEGES_DB_PATH` | `/app/data/warehouse/beges.duckdb` |
| `BEGES_CONFIG_DIR` | `/app/config` |
| `BEGES_SITE_DIR` | `/app/site` |
| `HOME` | `/home/app` |
| `UV_NO_SYNC` | `1` |

### 2.3 Commandes

```bash
make docker-build            # docker build -t pipeline-beges:local .
docker compose up --build    # pipeline + site sur http://localhost:8080
```

Taille observée de l'image locale : **966 Mo** (dbt, DuckDB, pandas, numpy et
openpyxl inclus). C'est le prix d'une image autonome ; ce n'est pas une image
de production minimale.

### 2.4 Contenu

L'image copie uniquement :

```text
Makefile  pyproject.toml  uv.lock  README.md
config/  dashboard/  dbt/  donnees-sources-fictives/  src/
```

`.dockerignore` exclut `.git`, `.github`, `.venv`, les caches, `data/`, `site/`,
`dbt/target`, `dbt/logs`, `tmp/`, `docs/`, `tests/` et les fichiers `.env*`.
Les tests ne sont pas dans l'image d'exécution : ils tournent en local ou en CI.

## 3. Docker Compose

```yaml
services:
  pipeline:   # one-shot : make all
    volumes:
      - beges-data:/app/data
      - beges-site:/app/site

  web:        # nginx:1.28-alpine, http://localhost:8080
    volumes:
      - beges-site:/usr/share/nginx/html:ro
    depends_on:
      pipeline:
        condition: service_completed_successfully
```

- `pipeline` exécute `make all` : ingestion, `dbt build`, dashboard, statut.
- `web` ne démarre qu'après le succès du pipeline.
- `beges-data` conserve DuckDB entre deux exécutions.
- `beges-site` partage le site généré avec nginx.
- Le port hôte est `8080` ; le port interne nginx reste `80`.

Commandes utiles :

```bash
docker compose up --build       # premier lancement ou rebuild
docker compose up -d --build    # en arrière-plan
docker compose logs -f pipeline # logs du pipeline
docker compose down             # arrête les conteneurs, garde les volumes
docker compose down -v          # arrête et supprime les volumes (destructif)
```

`docker compose down -v` ne touche ni `data/warehouse/` ni `site/` de l'hôte :
ce sont des volumes Docker nommés.

## 4. CI GitHub Actions

Workflow : `.github/workflows/ci.yml`.
Déclencheurs : `push` sur `main`, `pull_request` vers `main`, `workflow_dispatch`.

| Job | Contenu |
|---|---|
| `lint-test` | `uv sync --frozen`, `ruff check .`, `pytest` |
| `pipeline` | `uv sync --frozen`, `make all`, upload de `site/` en artefact Pages sur `main` |
| `docker` | `docker compose up -d --build`, attente HTTP, `docker compose down -v` |
| `deploy` | `actions/deploy-pages@v4` sur `main` uniquement |

Permissions :

- globales : `contents: read` ;
- job `pipeline` : `contents: read` (build et upload d'artefact) ;
- job `deploy` : `pages: write`, `id-token: write` ;
- aucun secret applicatif ; seul le `GITHUB_TOKEN` fourni par Actions est utilisé.

La concurrence `pages` n'annule pas un déploiement en cours. Les dépendances
sont mises en cache par `astral-sh/setup-uv` à partir de `uv.lock`.

## 5. GitHub Pages

Le site est publié comme artefact Pages, pas comme branche `gh-pages`.
GitHub Pages doit être activé **une fois manuellement** par un administrateur du
dépôt. Le `GITHUB_TOKEN` fourni à Actions ne peut pas créer le site Pages :
la tentative `actions/configure-pages@v5` avec `enablement: true` a échoué avec
`Resource not accessible by integration` et `Get Pages site failed. Error: Not Found`.

Activation :

```text
Settings → Pages → Build and deployment → Source : GitHub Actions
```

Cette étape est faite une seule fois. Ensuite, chaque push sur `main` publie
l'artefact produit par le job `pipeline`. Tant que Pages n'est pas activé, le job
`deploy` échoue, mais le build et l'upload du site restent verts.

URL attendue :

```text
https://ultragenix.github.io/Pipeline-BEGES/
```

Badge CI :

```text
https://github.com/ultragenix/Pipeline-BEGES/actions/workflows/ci.yml/badge.svg?branch=main
```

## 6. Limites

- DuckDB est mono-écrivain : `make all` est séquentiel, un seul pipeline à la fois.
- `pipeline` est un job one-shot, pas un orchestrateur ; pas de reprise automatique.
- Pas de données incrémentales : chaque exécution recharge les sources et reconstruit dbt.
- nginx sert un site statique local ; GitHub Pages est l'hébergement public.
- Pas d'authentification, pas de temps réel, pas de Power BI.
- L'image runtime ne contient pas les dépendances de développement : `pytest` et
  `ruff` se lancent hors image ou dans le job CI.
- Les actions GitHub sont épinglées par version majeure, pas par SHA.
- Azure et Terraform restent l'étape 8 ; aucun secret cloud ici.

## 7. Preuves locales

```text
uv run ruff check .                 All checks passed!
uv run pytest                       72 passed
make all                            PASS=303, 28 modèles, 275 tests, 0 erreur
docker build                        image pipeline-beges:local, 966 Mo
docker compose up -d --build        pipeline Exited (0), web healthy
curl http://localhost:8080/          HTTP 200, 14 248 octets
curl /observabilite.html             HTTP 200, 82 331 octets, 42 constats
curl /assets/style.css               HTTP 200, 13 212 octets
curl /assets/app.js                  HTTP 200, 2 146 octets
docker run --rm ... id               uid=1000(app)
docker compose down -v              volumes supprimés
```

Le clone propre du commit `8794db2` a été testé dans
`/tmp/opencode/beges-clean.jOVeWG` : `docker compose up -d --build` OK,
site HTTP 200, `docker compose down -v` OK.

### Premier run CI

Run `39535399267` sur `342b038` :

| Job | Résultat |
|---|---|
| `Lint et tests` | succès |
| `Image et compose` | succès |
| `Pipeline et site` | échec à `Configurer GitHub Pages` |
| `Déploiement GitHub Pages` | ignoré |

L'échec venait de l'activation automatique de Pages, pas du pipeline.
L'étape `actions/configure-pages@v5` a été retirée du workflow. Le job
`pipeline` construit et uploade désormais l'artefact ; le job `deploy` reste
conditionné à l'activation manuelle unique de Pages.
