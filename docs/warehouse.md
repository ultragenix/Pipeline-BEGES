# Entrepôt DuckDB — couche `raw`

> Documentation de la couche physique écrite par l'ingestion.
> Source de vérité du DDL : `src/beges/ingest.py` (`RAW_COLUMNS`, `_ensure_schema`).
> Base locale : `data/warehouse/beges.duckdb`, ignorée par git.
> Dernière vérification : 2026-10-21 — 8 263 lignes, 0 quarantaine.

## 1. Vocabulaire

Deux objets différents portent le nom `raw` :

| Nom | Sens |
|---|---|
| `DATA_RAW_DIR` | Répertoire des **fichiers d'entrée** : `donnees-sources-fictives/raw` |
| schéma `raw` | **Tables de sortie** dans DuckDB |

Autres termes :

- `company_code` : code entreprise (`KAY`, `FAN`, `VAC`).
- `source_id` : identifiant de la source dans `config/companies/<CODE>.yml`.
- `ingestion_id` : UUID d'un chargement de source.
- `raw_row` : ligne source complète, conservée en JSON.

## 2. Principes

- Un seul schéma `raw` partagé par toutes les entreprises : pas une table par client.
- Une table par **type de source**, pas par fichier.
- Chaque ligne porte `company_code`, `source_id` et les métadonnées de traçabilité.
- 17 sources sont ramenées à 6 tables de données.
- Le rechargement est idempotent par source : `DELETE` ciblé puis `INSERT` en transaction.
- La couche raw est fidèle : aucun dédoublonnage, aucune correction, aucun calcul d'émissions.
- Les tables d'audit (`ingestion_log`, `quarantine`) sont append-only.

## 3. Cartographie des sources

| Type(s) de source | Table | Sources chargées | Lignes | Grain |
|---|---|---|---:|---|
| `fec` | `raw.fec` | KAY, FAN, VAC | 1 999 | Une ligne d'écriture FEC |
| `electricity`, `electricity_xlsx` | `raw.electricity` | KAY, FAN, VAC | 95 | Un relevé mensuel par site |
| `fuel` | `raw.fuel` | KAY, FAN, VAC `fuel_s1`, VAC `fuel_s2` | 5 879 | Une transaction carburant |
| `refrigerants` | `raw.refrigerants` | KAY, FAN, VAC | 57 | Une intervention frigoriste |
| `flights` | `raw.flights` | KAY, FAN, VAC | 187 | Un billet d'avion |
| `vehicle_registry` | `raw.vehicles` | KAY | 46 | Un véhicule du parc |

Volumes par entreprise :

| Table | KAY | FAN | VAC | Total |
|---|---:|---:|---:|---:|
| `raw.fec` | 647 | 690 | 662 | 1 999 |
| `raw.electricity` | 26 | 36 | 33 | 95 |
| `raw.fuel` | 4 889 | 623 | 367 | 5 879 |
| `raw.refrigerants` | 8 | 17 | 32 | 57 |
| `raw.flights` | 25 | 40 | 122 | 187 |
| `raw.vehicles` | 46 | 0 | 0 | 46 |
| **Total** | **5 641** | **1 406** | **1 216** | **8 263** |

## 4. Colonnes communes

Chaque table de données termine par les mêmes colonnes de traçabilité :

| Colonne | Type | Nullable | Description |
|---|---|---:|---|
| `company_code` | `VARCHAR` | Non | KAY, FAN ou VAC |
| `source_id` | `VARCHAR` | Non | Identifiant de la source dans la configuration |
| `source_file` | `VARCHAR` | Non | Chemin du fichier, relatif à `DATA_RAW_DIR` |
| `source_sheet` | `VARCHAR` | Oui | Feuille Excel, sinon `NULL` |
| `source_row` | `INTEGER` | Oui | Ligne physique dans le fichier source |
| `ingestion_id` | `VARCHAR` | Non | UUID du chargement de cette source |
| `ingested_at` | `TIMESTAMPTZ` | Non | Horodatage du chargement |
| `raw_row` | `JSON` | Oui | Ligne source complète, colonnes non mappées incluses |

Précisions :

- `source_row` vaut le numéro de ligne CSV (en-tête = ligne 1, première donnée = ligne 2)
  ou le numéro de ligne Excel (en-tête ligne 4 pour FAN, première donnée ligne 5).
- `source_row` est `NULL` pour une quarantaine au niveau fichier.
- `raw_row` conserve les colonnes non mappées, par exemple `JournalCode` et
  `EcritureLet` du FEC. C'est la garantie de non-perte silencieuse.
- `ingestion_id` relie une ligne de données à sa ligne de `raw.ingestion_log`.

## 5. Tables de données

### 5.1 `raw.fec`

Grain : une ligne d'écriture comptable. Plusieurs lignes peuvent partager le même
`entry_id`.

| Colonne | Type | Description |
|---|---|---|
| `entry_id` | `VARCHAR` | `EcritureNum`, non unique |
| `entry_date` | `DATE` | `EcritureDate` |
| `account` | `VARCHAR` | `CompteNum`, texte pour préserver les zéros de tête |
| `account_label` | `VARCHAR` | `CompteLib` |
| `supplier_id` | `VARCHAR` | `CompAuxNum`, souvent vide |
| `supplier_label` | `VARCHAR` | `CompAuxLib`, souvent vide |
| `piece_ref` | `VARCHAR` | `PieceRef` |
| `piece_date` | `DATE` | `PieceDate` |
| `label` | `VARCHAR` | `EcritureLib` |
| `debit` | `DECIMAL(18,2)` | `Debit` |
| `credit` | `DECIMAL(18,2)` | `Credit` |
| `valid_date` | `DATE` | `ValidDate` |

Les 6 autres colonnes source (`JournalCode`, `JournalLib`, `EcritureLet`, `DateLet`,
`Montantdevise`, `Idevise`) restent dans `raw_row`.

### 5.2 `raw.electricity`

Grain : un relevé mensuel par site. Les sources délimitées et Excel sont fusionnées.

| Colonne | Type | Description |
|---|---|---|
| `site_code` | `VARCHAR` | Code site résolu (KAY : nom source converti en code) |
| `site_code_raw` | `VARCHAR` | Valeur brute de la colonne site |
| `pdl` | `VARCHAR` | Point de livraison, si présent dans la source |
| `month` | `DATE` | Premier jour du mois de consommation |
| `period_start` | `DATE` | Début de période, si présent |
| `period_end` | `DATE` | Fin de période, si présent |
| `consumption_kwh` | `DECIMAL(18,3)` | Consommation en kWh, MWh converti ×1000 |
| `amount_ht_eur` | `DECIMAL(18,2)` | Montant HT en euros |
| `reading_type` | `VARCHAR` | Réel, Estimé, Régularisation (KAY) |
| `unit_raw` | `VARCHAR` | `kWh` ou `MWh` pour l'Excel, `NULL` sinon |

Règles appliquées :

- KAY n'a pas de colonne `month` : le mois est dérivé de `period_start`.
- KAY fournit des noms de sites : `site_code` est résolu, `site_code_raw` garde le nom.
- FAN `PIE-FRO` est en MWh : `consumption_kwh` est converti, `unit_raw` garde `MWh`.
- Les montants et consommations négatifs sont conservés (régularisation KAY de mai).

### 5.3 `raw.fuel`

Grain : une transaction carburant. Les quatre sources sont fusionnées.

| Colonne | Type | Description |
|---|---|---|
| `transaction_date` | `DATE` | Date de transaction |
| `card_id` | `VARCHAR` | Identifiant de carte |
| `vehicle_id` | `VARCHAR` | Immatriculation ou véhicule, si présent |
| `product_raw` | `VARCHAR` | Libellé produit brut (`GAZOLE`, `ADBLUE`, `PRODUIT 47`, etc.) |
| `quantity_l` | `DECIMAL(18,3)` | Litres, `NULL` si absent (FAN) |
| `amount_ttc_eur` | `DECIMAL(18,2)` | Montant TTC |
| `station` | `VARCHAR` | Station, si présent (KAY) |

`product_code` n'existe pas dans raw : la classification métier
(`GAZOLE`, `SP95`, `INCONNU`, `NON_CARBURANT`) appartient à la couche dbt.

### 5.4 `raw.refrigerants`

Grain : une intervention frigoriste.

| Colonne | Type | Description |
|---|---|---|
| `intervention_date` | `DATE` | Date d'intervention |
| `site_code` | `VARCHAR` | Code site |
| `equipment` | `VARCHAR` | Équipement |
| `fluid_code` | `VARCHAR` | Code fluide, `NULL` si vide (FAN) |
| `nominal_charge_kg` | `DECIMAL(18,3)` | Charge nominale en kg |
| `recharge_kg` | `DECIMAL(18,3)` | Quantité rechargée en kg |

Les codes vides et `R-?` sont conservés tels quels ; ils seront signalés en qualité.

### 5.5 `raw.flights`

Grain : un billet d'avion.

| Colonne | Type | Description |
|---|---|---|
| `ticket_id` | `VARCHAR` | Numéro de billet |
| `emission_date` | `DATE` | Date d'émission |
| `departure_date` | `DATE` | Date de départ |
| `traveler_id` | `VARCHAR` | Code voyageur |
| `origin_iata` | `VARCHAR` | Aéroport d'origine |
| `destination_iata` | `VARCHAR` | Aéroport de destination, `NULL` si vide (KAY) |
| `trip_type` | `VARCHAR` | `AR` ou `AS` |
| `cabin_class` | `VARCHAR` | Économique ou Affaires |
| `status` | `VARCHAR` | Émis ou Annulé |
| `amount_ttc_eur` | `DECIMAL(18,2)` | Montant TTC |

Les billets annulés et les doublons VAC restent dans raw ; ils ne sont pas corrigés.

### 5.6 `raw.vehicles`

Grain : un véhicule du parc. Seule l'entreprise KAY fournit un parc.

| Colonne | Type | Description |
|---|---|---|
| `vehicle_id` | `VARCHAR` | Immatriculation |
| `vehicle_type` | `VARCHAR` | Type de véhicule |
| `tank_capacity_l` | `DECIMAL(18,3)` | Capacité du réservoir en litres |

## 6. Tables d'audit

### 6.1 `raw.ingestion_log`

Une ligne par source et par exécution. Un run complet ajoute 17 lignes.
Le journal est append-only : il n'est pas vidé par un rechargement.

| Colonne | Type | Description |
|---|---|---|
| `ingestion_id` | `VARCHAR` | UUID du chargement |
| `company_code` | `VARCHAR` | Entreprise |
| `source_id` | `VARCHAR` | Source |
| `source_type` | `VARCHAR` | Type de source configuré |
| `source_file` | `VARCHAR` | Fichier source |
| `source_sheet` | `VARCHAR` | Feuilles Excel, séparées par des virgules |
| `source_sha256` | `VARCHAR` | Empreinte SHA-256 du fichier |
| `file_size_bytes` | `BIGINT` | Taille du fichier |
| `rows_read` | `INTEGER` | Lignes de données lues, hors en-tête et lignes vides |
| `rows_loaded` | `INTEGER` | Lignes écrites dans la table raw |
| `rows_quarantined` | `INTEGER` | Lignes isolées |
| `status` | `VARCHAR` | `success`, `partial` ou `failed` |
| `error` | `VARCHAR` | Message d'erreur si échec |
| `duration_ms` | `INTEGER` | Durée du chargement |
| `started_at` | `TIMESTAMPTZ` | Début |
| `finished_at` | `TIMESTAMPTZ` | Fin |

Statuts :

| Statut | Signification |
|---|---|
| `success` | Toutes les lignes lues sont chargées, aucune quarantaine |
| `partial` | Au moins une ligne chargée et au moins une ligne en quarantaine |
| `failed` | Fichier illisible, erreur de schéma ou aucune ligne chargeable |

### 6.2 `raw.quarantine`

Une ligne par donnée isolée. Aucune ligne sur le jeu fictif actuel.

| Colonne | Type | Description |
|---|---|---|
| `ingestion_id` | `VARCHAR` | Chargement concerné |
| `company_code` | `VARCHAR` | Entreprise |
| `source_id` | `VARCHAR` | Source |
| `source_file` | `VARCHAR` | Fichier |
| `source_sheet` | `VARCHAR` | Feuille Excel, si applicable |
| `source_row` | `INTEGER` | Ligne source, `NULL` pour une erreur fichier |
| `reason_code` | `VARCHAR` | Code raison |
| `reason_detail` | `VARCHAR` | Détail lisible |
| `raw_row` | `JSON` | Ligne brute, si disponible |
| `quarantined_at` | `TIMESTAMPTZ` | Horodatage |

Codes raison utilisés par l'ingestion :

```text
fichier_illisible       fichier absent ou illisible
encodage_invalide       décodage impossible avec l'encodage configuré
fichier_vide            aucune ligne d'en-tête ou aucune donnée
colonne_manquante       colonne mappée absente de l'en-tête
colonne_dupliquee       nom de colonne présent plusieurs fois
ligne_malformee         nombre de colonnes incorrect ou erreur CSV
date_invalide           date non parsable avec le date_format de la source
nombre_invalide         nombre non parsable avec le séparateur décimal
valeur_requise_vide     date ou nombre obligatoire vide
site_inconnu            code ou nom de site absent de la configuration
mois_indetermine        month absent et period_start vide
unite_inconnue          unité Excel absente ou inconnue
unite_incoherente       unité de ligne différente de l'unité de feuille
```

## 7. Clés naturelles

Les clés sont déclarées dans `config/sources.yml`, mais **aucune contrainte
d'unicité n'est imposée dans raw** : les anomalies doivent rester visibles.

| Table | Clé déclarée | Remarque |
|---|---|---|
| `raw.fec` | `entry_id` | Non unique : plusieurs lignes par écriture |
| `raw.electricity` | `site_code`, `month` | Doublon KAY de juillet conservé |
| `raw.fuel` | `transaction_date`, `card_id`, `amount_ttc_eur` | — |
| `raw.refrigerants` | `intervention_date`, `site_code`, `equipment` | Plusieurs interventions possibles |
| `raw.flights` | `ticket_id` | Doublons VAC conservés |
| `raw.vehicles` | `vehicle_id` | — |

Les décisions de dédoublonnage, d'exclusion et de périmètre appartiennent aux
étapes dbt et qualité, pas à l'ingestion.

## 8. Requêtes utiles

```sql
-- Volumes par entreprise et par table
SELECT 'fec' AS table_name, company_code, count(*) FROM raw.fec GROUP BY 2
UNION ALL
SELECT 'electricity', company_code, count(*) FROM raw.electricity GROUP BY 2
UNION ALL
SELECT 'fuel', company_code, count(*) FROM raw.fuel GROUP BY 2
UNION ALL
SELECT 'refrigerants', company_code, count(*) FROM raw.refrigerants GROUP BY 2
UNION ALL
SELECT 'flights', company_code, count(*) FROM raw.flights GROUP BY 2
UNION ALL
SELECT 'vehicles', company_code, count(*) FROM raw.vehicles GROUP BY 2
ORDER BY 1, 2;
```

```sql
-- Dernier chargement de chaque source
SELECT company_code, source_id, status, rows_loaded, rows_quarantined,
       started_at, finished_at
FROM raw.ingestion_log
QUALIFY row_number() OVER (
    PARTITION BY company_code, source_id
    ORDER BY started_at DESC
) = 1
ORDER BY company_code, source_id;
```

```sql
-- Lignes en quarantaine
SELECT company_code, source_id, source_file, source_row,
       reason_code, reason_detail
FROM raw.quarantine
ORDER BY quarantined_at DESC;
```

```sql
-- Remonter une ligne agrégée à sa ligne source
SELECT company_code, source_file, source_row, raw_row
FROM raw.electricity
WHERE company_code = 'KAY' AND site_code = 'LPT-ENT'
LIMIT 1;
```

```sql
-- Schéma physique d'une table
DESCRIBE raw.fuel;
```

## 9. Rechargement et reconstruction

```bash
make ingest                        # toutes les entreprises
make ingest-company CODE=KAY       # une seule entreprise
uv run python -m beges.ingest --all --rebuild
```

- Chaque source est rechargée dans une transaction : `DELETE` ciblé sur
  `(company_code, source_id)` puis `INSERT`.
- Un échec de lecture ou d'écriture ne laisse pas de chargement partiel et ne
  supprime pas les données précédentes de la source.
- `--rebuild` supprime les six tables de données puis les recrée. Le journal et
  la quarantaine sont conservés.
- Si les colonnes d'une table existante ne correspondent plus au DDL, l'ingestion
  s'arrête avec un message demandant `--rebuild`.
- DuckDB est mono-écrivain : ne pas lancer `make ingest` et dbt en parallèle.

## 10. Limites

- Pas de clé primaire ni de clé étrangère imposée.
- Pas de dédoublonnage, pas de correction, pas de calcul d'émissions.
- Les tables sont partagées entre entreprises : `company_code` filtre, mais
  n'isole pas physiquement. Pour de vrais clients, utiliser un schéma ou une
  base par client, ou de la row-level security.
- `raw.ingestion_log` est append-only : le dashboard devra filtrer le dernier run.
- `raw_row` duplique la ligne source : volume négligeable à 8 263 lignes, gain de
  traçabilité important.
- La couche raw n'est pas le bilan BEGES : le staging, les règles de périmètre et
  les marts sont construits à l'étape dbt.

## 11. Vérification

```bash
make ingest
# 3 entreprises, 17 fichiers, 8 263 lignes, 0 quarantaine

uv run pytest
# 40 passed
```

Contrôle rapide des volumes :

```sql
SELECT (SELECT count(*) FROM raw.fec)
     + (SELECT count(*) FROM raw.electricity)
     + (SELECT count(*) FROM raw.fuel)
     + (SELECT count(*) FROM raw.refrigerants)
     + (SELECT count(*) FROM raw.flights)
     + (SELECT count(*) FROM raw.vehicles) AS total_lignes;
-- 8263
```
