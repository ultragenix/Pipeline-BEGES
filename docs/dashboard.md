# Dashboard et observabilité

> Site statique généré depuis DuckDB et les artefacts dbt.
> Dernière vérification : 2026-10-21 — 42 constats, 17 sources, 275 tests dbt PASS.
> Données fictives.

## 1. Rôle

Le dashboard répond à deux questions :

1. **Le bilan** : combien, où, avec quelle méthode, pour quelle entreprise ?
2. **La confiance** : quelles données sont incomplètes, suspectes ou à confirmer ?

Il ne remplace ni les tests dbt ni le registre qualité. Il les rend lisibles pour
un consultant RSE qui ne connaît ni SQL ni dbt.

## 2. Pages

### 2.1 `site/index.html` — bilan

| Section | Contenu |
|---|---|
| Hero | total 16 231,298 tCO₂e, part physique 44,7 % |
| Scopes | scope 1, 2, 3 et leur poids |
| Entreprises | KAY, FAN, VAC : total, scopes, part physique, constats |
| Postes | émissions par poste, avec barres de répartition |
| Méthodes | physique, physique estimée, monétaire |
| Top 10 | activités les plus émettrices |
| Qualité | appel vers les 42 constats et les 13 bloquants |
| Méthode | physique vs monétaire, traçabilité, limites |

### 2.2 `site/observabilite.html` — ops et qualité

| Section | Contenu |
|---|---|
| Synthèse | 42 constats, 13 bloquants, 21 alertes, 8 infos |
| Constats | 42 cartes filtrables par entreprise, sévérité, famille, statut et recherche |
| Détail d'un constat | preuve, question métier, impact, certitude, traitement |
| Ingestion | dernier run par source, lignes, statut, durée, horodatage |
| Fraîcheur | date min/max, lignes, mois couverts, alerte décembre VAC |
| Tests dbt | 275 PASS, 0 échec, durée du dernier build |
| Quarantaine | 0 ligne sur le jeu fictif, table prête si besoin |
| Lecture | impacts non additifs, journal append-only, statuts ouverts |

Les constats sont rendus côté Python. Le JavaScript ne sert qu'à filtrer les
cartes : si JavaScript est désactivé, tout le contenu reste lisible.

### 2.3 `make status` — console

```text
Pipeline BEGES — statut
Bilan       : 16 231,298 tCO2e | physique 44,7 %
Entreprises : FAN 7 894,347 | KAY 4 094,673 | VAC 4 242,278
Qualité     : 42 constats | 13 bloquants | 21 alertes | 8 infos
Statuts     : 38 à confirmer | 4 ouverts
Ingestion   : 17 sources | 8 263 lignes | 0 quarantaine | dernier run 21/10/2026 06:24
dbt         : 275 PASS | 0 échec | 6,6 s
Site        : site/index.html
```

## 3. Données lues

| Source | Usage |
|---|---|
| `analytics.mart_beges` | Bilan agrégé par entreprise, scope, poste, activité, méthode |
| `analytics.quality_constats` | Registre des 42 constats |
| `analytics.quality_summary` | Synthèse et impacts dédupliqués par entreprise |
| `analytics.ops_ingestion_last_run` | Dernier run par source |
| `analytics.ops_quarantine_summary` | Lignes en quarantaine agrégées |
| `analytics.ops_freshness` | Couverture temporelle des sources |
| `dbt/target/run_results.json` | Résultats du dernier `dbt build` |

Aucune donnée n'est écrite par le dashboard. Les requêtes sont en lecture seule.

## 4. Choix techniques

- **Site statique** : aucun serveur, aucun compte, aucun port à ouvrir.
- **Jinja2** : déjà une dépendance du projet, pas de nouveau paquet.
- **CSS et JavaScript vanilla** : pas de framework, pas de build front-end.
- **Barres CSS** : pas de bibliothèque de graphiques, pas de dépendance externe.
- **Rendu serveur** : les tableaux et cartes existent dans le HTML ; le JS ajoute
  les filtres.
- **Site généré et ignoré** : `site/` est dans `.gitignore`, l'étape 7 publiera
  ce dossier sur GitHub Pages.
- **Aucune écriture** : le dashboard lit DuckDB en `read_only`.

## 5. Génération

```bash
make dashboard   # dbt build + génération du site
make status      # synthèse console
make all         # ingest + dbt build + dashboard + status
```

`make dashboard` dépend de `dbt-build` : le site est toujours aligné sur le
dernier build et `run_results.json` est frais.

Sortie :

```text
Site généré : site
  index.html             Bilan 2025, 3 entreprises
  observabilite.html     42 constats, 17 sources
  assets/                style.css, app.js
```

Pour ouvrir le site :

```bash
xdg-open site/index.html
# ou
python -m http.server 8000 --directory site
```

Le site fonctionne aussi en `file://` : les liens sont relatifs et les données
sont dans le HTML.

## 6. Vérifications

```bash
uv run pytest                 # 67 passed
uv run ruff check .           # OK
make dbt-build                # PASS=303, 28 modèles, 275 tests
make dashboard                # site généré
make status                   # synthèse console
grep -o "16 231,298" site/index.html
grep -o "KAY-01" site/observabilite.html
grep -o "0 quarantaine" site/observabilite.html
```

Le site contient :

- `index.html` : 2 tableaux, 3 cartes entreprises, 3 cartes scopes ;
- `observabilite.html` : 42 `<details>`, 4 sélecteurs, une recherche, 2 tableaux ops ;
- `assets/style.css` et `assets/app.js` ;
- aucune valeur `NaN` ou `None` visible.

## 7. Accessibilité et lisibilité

- HTML sémantique : `header`, `nav`, `main`, `section`, `table`, `details`.
- Lien d'évitement vers le contenu.
- Filtres avec `label` explicite.
- Compteur de résultats en `aria-live="polite"`.
- Navigation clavier et `:focus-visible`.
- Contrastes vérifiés sur les badges et les textes.
- Responsive jusqu'à 560 px.
- Feuille d'impression simple.

## 8. Limites

- **Pas de capture navigateur** : aucun navigateur headless n'est disponible dans
  l'environnement. La preuve locale est le HTML généré, `grep`, `make status`.
  L'URL GitHub Pages sera ajoutée à l'étape 7.
- **Pas de temps réel** : le site est régénéré par `make dashboard`.
- **Pas d'authentification** : données fictives uniquement.
- **Pas de filtre serveur** : les 42 constats sont dans le HTML ; les filtres
  sont côté navigateur.
- **Pas de graphique interactif** : les barres CSS sont suffisantes pour la démo.
- **`run_results.json`** : `make status` affiche « dbt indisponible » si le
  fichier manque ; `make dashboard` le régénère via `dbt build`.
- **DuckDB mono-écrivain** : `make all` est séquentiel (`.NOTPARALLEL: all`).

## 9. Tests

- `tests/dashboard/test_reporting.py` : agrégations bilan/qualité/ingestion,
  parsing de `run_results.json`, formatage français.
- `tests/dashboard/test_dashboard.py` : rendu des deux pages, assets, filtres et
  absence de template non rendu.
- `tests/dashboard/test_status.py` : contenu de `make status`, cas sans dbt.

## 10. Prochaine étape

Étape 7 : Docker, CI et GitHub Pages. Le workflow publiera `site/` généré par
`make dashboard`, avec le badge CI et l'URL publique.
