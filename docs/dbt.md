# Couche dbt — bilan BEGES

> Modèles dbt construits au-dessus du schéma `raw` de DuckDB.
> Base : `data/warehouse/beges.duckdb`, schéma `analytics`.
> Documentation de la couche brute : [`warehouse.md`](warehouse.md).
> Dernière vérification : 2026-10-21 — `dbt build` PASS=201, 16 231,298 tCO₂e.

## 1. Rôle

La couche dbt transforme les lignes brutes en bilan BEGES :

- nettoie et type les sources dans `staging` ;
- applique les règles physiques et monétaires dans `intermediate` ;
- sépare les émissions retenues des lignes écartées ;
- produit un bilan agrégé par entreprise, scope, poste, activité et méthode ;
- conserve la trace de chaque ligne jusqu'à son fichier et sa ligne source.

Principe central : **une donnée physique remplace la méthode monétaire sur son poste**.
Un même poste ne doit jamais être compté deux fois.

## 2. Architecture

```text
raw
 └── staging
       ├── référentiels : facteurs, entreprises, comptes, aéroports, paramètres
       └── stg_* : typage, flags, aucune perte
             └── intermediate
                   ├── int_fec_monetaire
                   ├── int_electricity_physique
                   ├── int_fuel_physique
                   ├── int_refrigerants_physique
                   ├── int_flights_physique
                   └── int_emissions_candidates
                         ├── fct_emissions    (lignes incluses)
                         ├── fct_exclusions   (lignes écartées, listées)
                         └── mart_beges       (agrégat)
```

| Élément | Nombre |
|---|---:|
| Modèles dbt | 20 |
| Modèles en table | 5 |
| Modèles en vue | 15 |
| Sources `raw` | 6 |
| Tests dbt | 181 |
| Tâches `dbt build` | 201 |

## 3. Modèles

### 3.1 Référentiels et staging

| Modèle | Source | Rôle |
|---|---|---|
| `ref_emission_factors` | `config/emission_factors.yml` | Facteurs, PRG, bandes de vol, prix, TVA, correction 95 km |
| `ref_companies` | `config/companies/*.yml` | Codes, noms, villes, secteurs, effectifs |
| `ref_account_mapping` | `config/account_mapping.csv` | Préfixes comptables, postes, scopes, ratios, remplacements |
| `ref_airports` | `config/airports.csv` | Codes IATA et coordonnées |
| `ref_parameters` | `ref_emission_factors` | Paramètres scalaires : facteurs, prix, TVA, distance |
| `stg_fec` | `raw.fec` | FEC typé, montant HT, classe de compte, équilibre par écriture |
| `stg_electricity` | `raw.electricity` | Relevés typés, détection des doublons exacts |
| `stg_fuel` | `raw.fuel` | Carburant typé, `product_code`, `product_confidence` |
| `stg_refrigerants` | `raw.refrigerants` | Fluides typés, code normalisé, contrôle recharge/charge |
| `stg_flights` | `raw.flights` | Billets typés, doublons exacts, annulations, AR/AS |
| `stg_vehicles` | `raw.vehicles` | Parc véhicules, clé entreprise + immatriculation |

Les modèles `stg_*` ne suppriment aucune ligne. Ils ajoutent des flags :

- `is_exact_duplicate` pour l'électricité et les vols ;
- `is_cancelled` pour les vols ;
- `product_code` et `product_confidence` pour le carburant ;
- `fluid_code_norm` et `recharge_above_charge` pour les fluides ;
- `amount_ht_eur` et `entry_balance_eur` pour le FEC.

### 3.2 Intermediate

| Modèle | Calcul |
|---|---|
| `int_fec_monetaire` | Mapping par préfixe le plus long, montant HT × ratio / 10⁶ |
| `int_electricity_physique` | `kWh × 0,780 / 1000` |
| `int_fuel_physique` | `litres × 3,10 ou 2,80 / 1000` ; estimation FAN par prix repère |
| `int_refrigerants_physique` | `kg rechargés × PRG / 1000` |
| `int_flights_physique` | Orthodromie + 95 km, AR × 2, facteur de tranche |
| `int_emissions_candidates` | Union typée des cinq sources, avec `emission_id` unique |

Chaque ligne candidate porte :

- `scope`, `poste`, `activity`, `method` ;
- `activity_value`, `activity_unit`, `emission_factor`, `emission_factor_unit` ;
- `tco2e` quand calculable ;
- `is_included`, `exclusion_reason`, `quality_flag` ;
- `source_type`, `source_id`, `source_file`, `source_sheet`, `source_row`,
  `ingestion_id`, `source_reference`.

### 3.3 Marts

| Modèle | Grain | Usage |
|---|---|---|
| `fct_emissions` | Une ligne source incluse | Faits du bilan, traçables |
| `fct_exclusions` | Une ligne source écartée | Transparence, impacts non comptés |
| `mart_beges` | Entreprise × scope × poste × activité × méthode | Bilan agrégé, part physique |

`fct_exclusions` contient `tco2e_non_compte` : l'impact qui aurait été compté si la
ligne n'avait pas été écartée. Il n'entre jamais dans le bilan.

## 4. Règles de calcul

### 4.1 Méthode physique

| Source | Scope | Formule | Facteur |
|---|---:|---|---|
| Électricité | 2 | `consommation_kwh × 0,780 / 1000` | `kgCO2e/kWh` |
| Carburant | 1 | `litres × facteur / 1000` | GAZOLE 3,10 ; SP95 2,80 `kgCO2e/L` |
| Fluides | 1 | `recharge_kg × PRG / 1000` | PRG F-gas `kgCO2e/kg` |
| Vols | 3 | `distance_passager_km × facteur / 1000` | 0,258 / 0,187 / 0,152 `kgCO2e/passager.km` |

Règles complémentaires :

- vol : distance orthodromique + 95 km ; tranche choisie sur la distance d'un aller ;
  un aller-retour compte deux trajets ;
- fluides : la recharge est multipliée par le PRG du fluide ;
- électricité : les régularisations négatives sont conservées ;
- carburant : `ADBLUE` n'est pas un combustible ; `PRODUIT 47` reste inconnu ;
- FAN carburant : litres estimés par `montant TTC / prix repère`, méthode
  `physique_estimee`.

### 4.2 Méthode monétaire

Seules les classes 6 et 21 du FEC entrent dans le calcul. Chaque compte est rattaché
au **préfixe le plus long** de `config/account_mapping.csv`.

```text
tCO2e = montant HT × ratio kgCO2e/k€ / 1 000 000
```

Les comptes suivants sont remplacés par une source physique et exclus du monétaire :

| Compte | Poste | Remplacé par |
|---|---|---|
| `60611` | Électricité | `raw.electricity` |
| `60622` | Combustion mobile | `raw.fuel` |
| `62511` | Déplacements professionnels | `raw.flights` |

Les comptes `63` à `69` sont hors périmètre. Les comptes non mappés sont exclus et
listés. Exemple : `6288000` « Prestations diverses portuaires », 523 298,66 €.

### 4.3 Exclusions et flags

Une ligne écartée n'est jamais supprimée : elle passe dans `fct_exclusions`.

| Raison | Lignes | Exemple |
|---|---:|---|
| `couvert_par_physique` | 176 | FEC `60611`, `60622`, `62511` |
| `hors_perimetre` | 75 | Salaires, impôts, charges |
| `compte_non_mappe` | 12 | KAY `6288000` |
| `non_combustible` | 412 | KAY `ADBLUE` |
| `produit_inconnu` | 9 | KAY `PRODUIT 47` |
| `doublon_exact` | 3 | KAY juillet, VAC `TKT-0009`, `TKT-0061` |
| `billet_annule` | 3 | VAC |
| `gwp_inconnu` | 2 | FAN fluide vide et `R-?` |
| `destination_manquante` | 1 | KAY |

Flags de qualité, sans exclusion du calcul :

- `releve_estime`, `regularisation` (électricité) ;
- `litres_estimes` (FAN), `produit_a_confirmer` (B7/GO/Diesel) ;
- `recharge_superieure_charge`, `gwp_inconnu` (fluides) ;
- `aller_simple_a_confirmer`, `classe_affaires_facteur_standard` (vols) ;
- `montant_negatif` (FEC).

## 5. Anti-double comptage

Trois barrières :

1. **Remplacement physique** : les comptes `60611`, `60622`, `62511` sont exclus du
   monétaire. Le test `assert_comptes_fec_exclus_absents` vérifie qu'aucune ligne
   FEC exclue ne réapparaît dans `fct_emissions`.
2. **Activité commune** : les sources physiques et les comptes remplacés partagent
   la même `activity` (`Électricité`, `Carburants`, `Billets d'avion`). Le test
   `assert_no_double_comptage` vérifie qu'aucune activité ne mélange physique et
   monétaire.
3. **Séparation faits / exclusions** : `assert_candidates_split` vérifie que
   `int_emissions_candidates = fct_emissions + fct_exclusions`, sans perte.

Autres tests structurants :

- `unique` sur `emission_id` dans les faits et les exclusions ;
- `assert_traceabilite` : fichier, ligne et `ingestion_id` obligatoires ;
- `assert_mart_matches_fct` : le bilan agrégé retombe sur la somme des faits ;
- `assert_mapping_attendu` : verrouille les mappings comptables documentés ;
- `assert_distances_plausibles` : distances de vol réalistes, RUN–CDG cohérent.

## 6. Résultats vérifiés

`dbt build` : **PASS=201, WARN=0, ERROR=0, SKIP=0**.

### 6.1 Volumes

| Table | Lignes |
|---|---:|
| `analytics.fct_emissions` | 6 191 |
| `analytics.fct_exclusions` | 693 |
| `analytics.mart_beges` | 48 |
| `int_emissions_candidates` | 6 884 |

### 6.2 Bilan par entreprise et scope

| Entreprise | Scope 1 | Scope 2 | Scope 3 | Total | Part physique |
|---|---:|---:|---:|---:|---:|
| KAY | 2 712,714 | 435,601 | 946,357 | 4 094,673 | 78,2 % |
| FAN | 418,009 | 1 946,840 | 5 529,498 | 7 894,347 | 31,1 % |
| VAC | 129,771 | 1 211,282 | 2 901,225 | 4 242,278 | 37,8 % |
| **Total** | **3 260,494** | **3 593,724** | **9 377,080** | **16 231,298** | **44,7 %** |

### 6.3 Méthodes

| Méthode | Lignes | tCO₂e |
|---|---:|---:|
| `physique` | 5 165 | 7 163,300 |
| `physique_estimee` | 623 | 94,042 |
| `monetaire` | 403 | 8 973,956 |

Points vérifiés :

- KAY : doublon de juillet exclu, impact non compté 24,753 tCO₂e ;
- KAY : `6288000` non mappé, 12 lignes et 523 298,66 € listés ;
- FAN : 623 transactions carburant estimées, 31 075,64 L, 94,042 tCO₂e ;
- FAN : deux fluides à GWP inconnu listés ;
- VAC : trois billets annulés listés, 4,229 tCO₂e non comptés ;
- vols RUN–CDG : 9 464,3 km à l'aller, 18 928,6 km en aller-retour.

## 7. Commandes

```bash
make ingest        # construit ou rafraîchit raw
make dbt-build     # construit les modèles et exécute les 181 tests
make dbt-test      # exécute uniquement les tests
make dbt-docs      # génère manifest + catalog pour le lineage
```

`make dbt-build` vérifie que la base existe ; sinon, il demande `make ingest`.

Pour consulter le lineage :

```bash
BEGES_DB_PATH=$PWD/data/warehouse/beges.duckdb \
BEGES_CONFIG_DIR=$PWD/config \
uv run dbt docs serve --project-dir dbt --profiles-dir dbt
```

## 8. Choix à confirmer et limites

- **FAN carburant** : litres estimés par les prix repères, faute de volumes.
- **KAY B7, GO, Diesel** : traités comme du gazole, flag `produit_a_confirmer`.
- **AR / AS** : AR = deux trajets, AS = un trajet, flag `aller_simple_a_confirmer`.
- **Classe Affaires** : même facteur que l'Économique, faute de facteur dédié.
- **KAY `LPT-ATL`** : aucun relevé, aucune extrapolation ; scope 2 incomplet.
- **VAC décembre** : aucun relevé, aucune extrapolation ; scope 2 incomplet.
- **FEC supposé HT** : non confirmé par le métier.
- **Mappings comptables** : `601`, `6021`, `6022`, `6231` restent à confirmer.
- **FAN `AC000042`** : écriture déséquilibrée de 150 €, non corrigée.
- **Pas de constats formalisés** : `fct_exclusions` est la matière première de
  l'étape 5 ; les questions métier restent ouvertes.
- **Pas de dimension site dans les faits** : `site_code` est présent pour
  l'électricité et les fluides ; le carburant, les vols et le FEC ne sont pas
  rattachés à un site.
- **DuckDB mono-écrivain** : `make ingest` et dbt ne doivent pas tourner en parallèle.

## 9. Références

- [`warehouse.md`](warehouse.md) : couche brute, tables, journal, quarantaine.
- `config/emission_factors.yml` : facteurs, PRG, prix, TVA.
- `config/account_mapping.csv` : correspondance comptable.
- `config/airports.csv` : aéroports et coordonnées.
- `docs/anomalies/KAY.md`, `FAN.md`, `VAC.md` : questions métier.
- `docs/note.md` : carnet de bord.
