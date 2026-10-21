# Qualité des données — constats

> Couche qualité construite au-dessus des marts dbt.
> Base : `data/warehouse/beges.duckdb`, schéma `analytics`.
> Dernière vérification : 2026-10-21 — `dbt build` **PASS=303**, **42 constats**.
> Données fictives. Ce document n'est pas un audit réglementaire.

## 1. Rôle

La couche qualité transforme les lignes écartées, les flags et les référentiels en
**constats actionnables** :

- une observation chiffrée, reliée à un fichier ou à une source ;
- une famille de qualité des données ;
- une sévérité et une certitude ;
- un statut et un traitement ;
- une question métier compréhensible par un consultant RSE ;
- un impact en tCO₂e et/ou en euros quand il est calculable.

Elle ne corrige aucune donnée source et ne modifie pas le bilan. Les lignes écartées
restent dans `fct_exclusions` ; les règles provisoires restent flaguées dans
`fct_emissions`. La couche qualité les rend lisibles et les relie à une question.

**Constat ≠ test dbt.** Les tests dbt vérifient le code (unicité, anti-double comptage,
traçabilité). Les constats vérifient les données du client. Un constat peut être
« bloquant » sans faire échouer `dbt build` : c'est une information à traiter, pas une
erreur de code.

## 2. Taxonomie

### 2.1 Familles

Les 10 familles du cahier des charges sont utilisées :

| Famille | Question |
|---|---|
| `conformite_format` | Le fichier ou le libellé respecte-t-il la structure attendue ? |
| `unicite` | Une même information est-elle présente plusieurs fois ? |
| `completude` | Manque-t-il une valeur, une période ou une entité ? |
| `validite` | La valeur est-elle dans son domaine ? |
| `homogeneite_unites` | Toutes les lignes sont-elles dans la même unité ? |
| `valeurs_aberrantes` | La valeur est-elle anormalement haute ou basse ? |
| `integrite_referentielle` | Le code renvoie-t-il à un référentiel connu ? |
| `coherence_interne` | Les règles propres au format sont-elles respectées ? |
| `coherence_entre_sources` | Deux sources qui décrivent la même chose concordent-elles ? |
| `fraicheur` | Les données couvrent-elles toute la période ? |

### 2.2 Sévérité

| Sévérité | Sens |
|---|---|
| `bloquant` | Le bilan est faux ou incomplet tant que le point n'est pas levé. |
| `alerte` | Impact possible ; à vérifier avec le métier. |
| `info` | Traitement appliqué, pour transparence. |

### 2.3 Certitude

| Certitude | Sens |
|---|---|
| `certain` | Le fait est observé dans les données (doublon, site absent, écriture déséquilibrée). |
| `a_confirmer` | L'interprétation ou la règle métier reste à confirmer. |

### 2.4 Statut

Le statut suit le cycle de vie du retour métier, aligné sur `docs/anomalies/README.md` :

| Statut | Sens |
|---|---|
| `ouvert` | Constat posé, question pas encore envoyée. |
| `a_confirmer` | Question envoyée, réponse attendue. |
| `repondu` | Réponse reçue, décision à intégrer. |
| `integre` | Règle ou contrôle ajouté. |
| `ecarte` | Faux positif documenté. |

### 2.5 Traitement

Le traitement décrit ce que le pipeline a fait, indépendamment de la réponse métier :

| Traitement | Sens |
|---|---|
| `converti` | Une unité a été convertie (ex. MWh → kWh). |
| `mappe` | Une colonne ou un libellé a été rattaché à un champ canonique. |
| `exclu` | La ligne est écartée du calcul et conservée dans `fct_exclusions`. |
| `estime` | Une quantité manquante a été estimée avec un repère documenté. |
| `conserve` | La ligne est conservée dans le calcul et signalée. |
| `aucun` | Aucun traitement automatique ; le constat est signalé. |

### 2.6 Impact

| Type | Sens |
|---|---|
| `compte` | Impact déjà présent dans le bilan. |
| `non_compte` | Impact écarté du bilan ; il est listé pour transparence. |
| `exposition` | Impact qui changerait si la règle métier était différente. |
| `estimation` | Donnée manquante valorisée avec un repère documenté. |
| `non_calculable` | Impact non calculable avec les données disponibles. |

### 2.7 Impacts partagés

Deux constats peuvent décrire le même problème sous deux angles :

- `KAY-01` (site `LPT-ATL` absent) et `KAY-09` (écart électricité/FEC) partagent
  le groupe `KAY-ELEC-GAP` ;
- `VAC-01` (décembre manquant) et `VAC-02` (écart électricité/FEC) partagent
  le groupe `VAC-ELEC-GAP`.

Ces impacts ne sont **pas additifs**. `quality_summary` déduplique par
`impact_group` et retient l'estimation la plus élevée. Le détail des deux
estimations reste visible dans `quality_constats`.

## 3. Architecture

```text
fct_emissions / fct_exclusions / stg_* / ref_*
                 │
                 ▼
        int_quality_findings        détection des 42 constats
                 │
                 ▼
          quality_constats          registre + métriques calculées
                 │
                 ▼
          quality_summary           synthèse par entreprise
```

| Modèle | Grain | Rôle |
|---|---|---|
| `ref_quality_register` | Un constat | Registre lu depuis `config/quality/*.yml` |
| `int_quality_findings` | Un constat détecté | Contrôles génériques et métriques |
| `quality_constats` | Un constat | Registre enrichi, prêt pour le dashboard |
| `quality_summary` | Une entreprise | Compteurs et impacts dédupliqués |

Le registre est **un fichier par entreprise**, comme le dictionnaire et les
anomalies :

| Fichier | Constats |
|---|---:|
| `config/quality/KAY.yml` | 16 |
| `config/quality/FAN.yml` | 13 |
| `config/quality/VAC.yml` | 12 |
| `config/quality/_common.yml` | 1 (`GEN-01`, transverse) |

Ajouter un constat demande trois choses : une entrée YAML avec un `check_key`,
un contrôle SQL qui produit ce `check_key`, et un test de couverture. Aucun test
d'entreprise existant n'est réécrit.

### 3.1 Colonnes principales de `quality_constats`

| Colonne | Contenu |
|---|---|
| `constat_id` | Identifiant stable, ex. `KAY-09` |
| `registry_id` | Lien vers le registre étape 1, `NULL` pour un nouveau constat |
| `company_code`, `company_name` | Entreprise, ou `ALL` pour un constat transverse |
| `source_type`, `source_file`, `source_row` | Source et traçabilité |
| `family`, `severity`, `certitude`, `statut`, `traitement` | Taxonomie |
| `title`, `proof`, `business_question` | Libellé, preuve chiffrée, question métier |
| `evidence_lines`, `evidence_quantity`, `evidence_amount_eur` | Métriques sources |
| `impact_tco2e`, `impact_eur` | Impact calculé quand possible |
| `impact_type`, `impact_group`, `impact_basis` | Nature et limites de l'impact |
| `check_key` | Contrat entre le registre YAML et le SQL |
| `severity_rank`, `statut_rank` | Ordre de lecture |

## 4. Résultats vérifiés

```text
dbt build : PASS=303, 275 tests, 28 modèles, 0 erreur
constats  : 42
bloquants : 13
alertes   : 21
infos     : 8
certains              : 23
certitude à confirmer : 19
statut à confirmer    : 38
ouverts               : 4
```

### 4.1 Synthèse par entreprise

| Entreprise | Constats | Bloquants | Alertes | Infos | Impact tCO₂e | Impact € |
|---|---:|---:|---:|---:|---:|---:|
| ALL — Toutes les entreprises | 1 | 0 | 1 | 0 | 32,20 | 0,00 |
| FAN — Fanjan Agro SA | 13 | 4 | 6 | 3 | 5 439,38 | 14 513,91 |
| KAY — Kayamb Logistique SAS | 16 | 5 | 8 | 3 | 1 919,28 | 596 058,78 |
| VAC — Hôtels Vacoa Bleu SARL | 12 | 4 | 6 | 2 | 2 600,57 | 29 719,18 |

Les colonnes `Impact tCO₂e` et `Impact €` agrègent des impacts de natures
différentes (`compte`, `non_compte`, `exposition`, `estimation`) et dédupliquent
les groupes partagés. Elles ne représentent pas une perte financière ni un ajout
au bilan.

### 4.2 Constats par famille

| Famille | Constats | Bloquants |
|---|---:|---:|
| cohérence entre sources | 4 | 1 |
| cohérence interne | 2 | 1 |
| complétude | 5 | 2 |
| conformité format | 11 | 4 |
| fraîcheur | 1 | 1 |
| unités | 1 | 1 |
| intégrité référentielle | 8 | 1 |
| unicité | 2 | 2 |
| valeurs aberrantes | 1 | 0 |
| validité | 7 | 0 |

### 4.3 Registre complet

| ID | Société | Famille | Sévérité | Certitude | Statut | Traitement | Impact | Titre |
|---|---|---|---|---|---|---|---|---|
| GEN-01 | ALL | validité | alerte | à confirmer | ouvert | conservé | 32,20 tCO₂e exposé | Classe Affaires au facteur standard |
| FAN-01 | FAN | unités | bloquant | certain | à confirmer | converti | 568,09 tCO₂e compté | Feuille PIE-FRO exprimée en MWh |
| FAN-02 | FAN | complétude | bloquant | certain | à confirmer | estimé | 94,04 tCO₂e compté | Carburant sans volumes en litres |
| FAN-03 | FAN | intégrité référentielle | alerte | certain | à confirmer | aucun | n.c. | Cartes carburant sans référentiel véhicule |
| FAN-04 | FAN | validité | alerte | certain | à confirmer | exclu | n.c. | Intervention frigoriste sans code fluide |
| FAN-05 | FAN | validité | alerte | certain | à confirmer | exclu | n.c. | Code fluide R-? inconnu |
| FAN-06 | FAN | cohérence interne | bloquant | certain | à confirmer | aucun | 0,09 tCO₂e / 150,00 € exposé | Écriture AC000042 déséquilibrée |
| FAN-07 | FAN | intégrité référentielle | alerte | à confirmer | à confirmer | conservé | 4 756,84 tCO₂e exposé | Mappings 6011000 et 6021000 à confirmer |
| FAN-08 | FAN | conformité format | info | certain | à confirmer | exclu | 14 000,00 € non compté | CET en classe 6 mais hors périmètre |
| FAN-09 | FAN | cohérence entre sources | alerte | à confirmer | à confirmer | aucun | 1,67 tCO₂e / 363,91 € est. | Écart entre l'électricité et le FEC 6061100 |
| FAN-10 | FAN | complétude | info | à confirmer | à confirmer | aucun | n.c. | Aucune intervention frigoriste sur SPI-ADM |
| FAN-11 | FAN | conformité format | bloquant | à confirmer | à confirmer | aucun | n.c. | FEC supposé HT |
| FAN-12 | FAN | conformité format | alerte | à confirmer | à confirmer | conservé | 4,48 tCO₂e exposé | Aller simple / aller-retour à confirmer |
| FAN-13 | FAN | intégrité référentielle | info | à confirmer | à confirmer | conservé | 14,18 tCO₂e compté | Hôtels, taxis et repas en méthode monétaire |
| KAY-01 | KAY | complétude | bloquant | certain | à confirmer | aucun | 185,03 tCO₂e / 40 326,43 € est. | Site LPT-ATL sans relevé électrique |
| KAY-02 | KAY | unicité | bloquant | certain | à confirmer | exclu | 24,75 tCO₂e / 5 394,78 € non compté | Facture électricité de juillet dupliquée |
| KAY-03 | KAY | cohérence interne | alerte | certain | à confirmer | conservé | −9,17 tCO₂e compté | Régularisation négative en mai |
| KAY-04 | KAY | complétude | alerte | certain | à confirmer | conservé | 39,72 tCO₂e compté | Relevé d'avril estimé |
| KAY-05 | KAY | intégrité référentielle | alerte | à confirmer | à confirmer | conservé | 1 642,65 tCO₂e exposé | Libellés B7, GO et Diesel à confirmer |
| KAY-06 | KAY | conformité format | info | certain | à confirmer | exclu | 25,54 tCO₂e / 7 416,00 € non compté | ADBLUE exclu du calcul carburant |
| KAY-07 | KAY | validité | alerte | certain | à confirmer | exclu | 2 358,54 € | Produit 47 inconnu |
| KAY-08 | KAY | cohérence entre sources | alerte | à confirmer | à confirmer | aucun | 4,62 tCO₂e / 2 173,57 € est. | Écart entre le carburant et le FEC 6062200 |
| KAY-09 | KAY | cohérence entre sources | bloquant | à confirmer | à confirmer | aucun | 185,03 tCO₂e / 40 326,43 € est. | Écart entre l'électricité et le FEC 6061100 |
| KAY-10 | KAY | intégrité référentielle | bloquant | certain | à confirmer | exclu | 523 298,66 € exposé | Compte 6288000 non mappé |
| KAY-11 | KAY | validité | alerte | certain | à confirmer | exclu | 1 090,80 € | Destination de vol vide |
| KAY-12 | KAY | conformité format | alerte | à confirmer | à confirmer | conservé | 5,84 tCO₂e exposé | Aller simple / aller-retour à confirmer |
| KAY-13 | KAY | complétude | info | à confirmer | à confirmer | aucun | n.c. | Aucune intervention frigoriste sur LPT-SIE et LPT-ATL |
| KAY-14 | KAY | conformité format | bloquant | à confirmer | à confirmer | aucun | n.c. | FEC supposé HT |
| KAY-15 | KAY | conformité format | info | certain | ouvert | exclu | 14 000,00 € non compté | CET en classe 6 mais hors périmètre |
| KAY-16 | KAY | valeurs aberrantes | alerte | certain | ouvert | aucun | 0,31 tCO₂e exposé | Transaction carburant supérieure à la capacité du réservoir |
| VAC-01 | VAC | fraîcheur | bloquant | certain | à confirmer | aucun | 110,12 tCO₂e est. | Décembre manquant sur les 3 sites |
| VAC-02 | VAC | cohérence entre sources | alerte | à confirmer | à confirmer | aucun | 120,42 tCO₂e / 26 245,19 € est. | Écart entre l'électricité et le FEC 6061100 |
| VAC-03 | VAC | conformité format | bloquant | certain | à confirmer | mappé | 65,73 tCO₂e compté | Dérive de schéma carburant S1 / S2 |
| VAC-04 | VAC | unicité | bloquant | certain | à confirmer | exclu | 3,44 tCO₂e / 3 149,98 € non compté | Billets dupliqués |
| VAC-05 | VAC | validité | info | certain | à confirmer | exclu | 4,23 tCO₂e / 2 964,53 € non compté | Billets annulés |
| VAC-06 | VAC | intégrité référentielle | alerte | certain | à confirmer | aucun | n.c. | Cartes carburant sans véhicule |
| VAC-07 | VAC | conformité format | bloquant | à confirmer | à confirmer | aucun | n.c. | FEC supposé HT |
| VAC-08 | VAC | conformité format | alerte | à confirmer | à confirmer | conservé | 10,57 tCO₂e exposé | Aller simple / aller-retour à confirmer |
| VAC-09 | VAC | intégrité référentielle | alerte | à confirmer | à confirmer | conservé | 2 356,44 tCO₂e exposé | Mappings 6011000 et 6022000 à confirmer |
| VAC-10 | VAC | conformité format | info | certain | à confirmer | exclu | 14 000,00 € non compté | CET en classe 6 mais hors périmètre |
| VAC-11 | VAC | intégrité référentielle | alerte | à confirmer | à confirmer | conservé | 54,73 tCO₂e exposé | Publicité et commissions plateformes |
| VAC-12 | VAC | validité | alerte | à confirmer | ouvert | conservé | −14,98 tCO₂e / −16 640,52 € compté | Avoirs sur achats alimentaires |

### 4.4 Principaux impacts

| ID | Impact | Type | Titre |
|---|---:|---|---|
| FAN-07 | 4 756,84 | exposition | Mappings 6011000 et 6021000 à confirmer |
| VAC-09 | 2 356,44 | exposition | Mappings 6011000 et 6021000 à confirmer |
| KAY-05 | 1 642,65 | exposition | Libellés B7, GO et Diesel à confirmer |
| FAN-01 | 568,09 | compté | Feuille PIE-FRO exprimée en MWh |
| KAY-10 | 523 298,66 € | exposition | Compte 6288000 non mappé |
| KAY-09 | 185,03 | estimation | Écart entre l'électricité et le FEC 6061100 |
| KAY-01 | 185,03 | estimation | Site LPT-ATL sans relevé électrique |
| VAC-02 | 120,42 | estimation | Écart entre l'électricité et le FEC 6061100 |
| VAC-01 | 110,12 | estimation | Décembre manquant sur les 3 sites |
| FAN-02 | 94,04 | compté | Carburant sans volumes en litres |
| VAC-03 | 65,73 | compté | Dérive de schéma carburant S1 / S2 |
| VAC-11 | 54,73 | exposition | Publicité et commissions plateformes |

## 5. Deux constats racontés de bout en bout

### 5.1 KAY — l'électricité ne se recoupe pas

**Le parcours.**

1. `KAY/electricite/export_edf_2025.csv` contient 26 relevés pour deux points de
   livraison (`PDL-LPT-ENT`, `PDL-LPT-SIE`). Le site `LPT-ATL` est déclaré dans
   `config/companies/KAY.yml` mais n'a aucun relevé.
2. L'ingestion charge les lignes dans `raw.electricity`, puis `stg_electricity`
   détecte le doublon exact de juillet.
3. `int_electricity_physique` calcule `kWh × 0,780 / 1000`, exclut le doublon et
   conserve la régularisation négative de mai ainsi que le relevé estimé d'avril.
4. `fct_emissions` et `fct_exclusions` séparent les lignes incluses des lignes
   écartées.
5. `int_quality_findings` calcule les écarts entre l'export électrique et le
   compte `6061100` du FEC, puis `quality_constats` les relie aux questions du
   registre.

**Les chiffres.**

| Élément | Valeur |
|---|---:|
| Export électricité | 100 333,49 € HT |
| FEC `6061100` | 140 659,92 € |
| Écart | 40 326,43 € |
| Impact estimé | 185,03 tCO₂e |
| Doublon de juillet exclu | 24,75 tCO₂e |
| Régularisation de mai | −9,17 tCO₂e |
| Relevé d'avril estimé | 39,72 tCO₂e |

L'estimation de l'écart utilise le prix moyen de 0,17 €/kWh et le facteur
0,78 kgCO₂e/kWh. Ce n'est pas une correction : c'est un ordre de grandeur pour
prioriser la question.

**Les constats.**

- `KAY-01` — site `LPT-ATL` sans relevé, bloquant, certain ;
- `KAY-09` — écart électricité/FEC, bloquant, à confirmer ;
- `KAY-02` — doublon de juillet, bloquant, exclu ;
- `KAY-03` — régularisation de mai, alerte, conservée ;
- `KAY-04` — relevé d'avril estimé, alerte, conservé.

`KAY-01` et `KAY-09` partagent le groupe `KAY-ELEC-GAP` : l'écart est cohérent
avec le site manquant, mais il n'est pas prouvé que tout l'écart vienne de là.

**La question au métier.** « Le site `LPT-ATL` a-t-il consommé de l'électricité en
2025 ? Si oui, pouvez-vous fournir les relevés ou les factures ? » La réponse
permettra soit de compléter le scope 2, soit de documenter une consommation nulle
ou un site hors périmètre.

**Ce que le consultant retient.** Le scope 2 de KAY est incomplet, mais aucune
extrapolation silencieuse n'a été faite. Le doublon est exclu, la régularisation
et l'estimation sont conservées et signalées, et l'écart avec le FEC est chiffré.

### 5.2 FAN — MWh ou kWh ?

**Le parcours.**

1. `FAN/electricite/releves_electricite_2025.xlsx` contient trois feuilles :
   `SPI-USI`, `PIE-FRO` et `SPI-ADM`.
2. La configuration décrit `PIE-FRO` avec `unit: MWh`, les deux autres en `kWh`.
3. L'ingestion convertit `PIE-FRO` en kWh (×1000) et conserve `unit_raw = MWh`
   dans `raw.electricity`.
4. `stg_electricity` puis `int_electricity_physique` calculent les émissions sur
   la consommation convertie.
5. `int_quality_findings` détecte la présence de `unit_raw = MWh` et produit
   `FAN-01`.

**Les chiffres.**

| Élément | Valeur |
|---|---:|
| Lignes `PIE-FRO` | 12 |
| Consommation après conversion | 728 316 kWh |
| Montant HT | 123 813,72 € |
| Impact | 568,09 tCO₂e |

Sans conversion, `PIE-FRO` serait compté 728,316 kWh, soit un facteur 1000
d'erreur et environ 0,57 tCO₂e au lieu de 568,09 tCO₂e.

**Le constat.** `FAN-01`, famille `homogeneite_unites`, sévérité bloquante,
certitude certaine, statut à confirmer, traitement `converti`. La conversion est
tracée et l'unité d'origine est conservée : le consultant peut vérifier la règle.

**La question au métier.** « Confirmez-vous que `PIE-FRO` est bien en MWh et qu'il
faut multiplier par 1000 ? » Tant que la réponse n'est pas reçue, le constat reste
`à confirmer`, même si la conversion est appliquée.

**Ce que le consultant retient.** Une anomalie d'unité a été détectée, corrigée
de façon traçable et signalée. Le pipeline ne suppose pas que toutes les feuilles
d'un classeur partagent la même unité.

## 6. Contrôles positifs

| Contrôle | Résultat |
|---|---|
| FEC KAY, FAN, VAC équilibrés | OK, sauf `AC000042` FAN (constat `FAN-06`) |
| Parc KAY : 46 véhicules sur 46 | OK |
| Vols FAN vs FEC `6251100` | Écart 0,00 € |
| Vols KAY vs FEC `6251100` | Écart 0,01 € |
| Vols VAC vs FEC `6251100` après exclusions | Écart 0,04 € |
| Carburant FAN vs FEC `6062200` | Écart 0,00 € |
| Carburant VAC vs FEC `6062200` | Écart 0,03 € |
| Fluides : recharge ≤ charge nominale | OK, 0 dépassement |
| Dates FEC en 2025 | OK, 0 hors exercice |
| Électricité KAY `LPT-SIE` | 12 mois |
| Électricité FAN | 3 sites × 12 mois |
| Électricité VAC | 3 sites × 11 mois (décembre manquant, `VAC-01`) |
| Exclusions inattendues sans constat | 0 |
| Entrées du registre sans constat calculé | 0 |

## 7. Écarts avec les preuves de l'étape 1

Les preuves narratives de l'étape 1 ont été recalculées. Cinq écarts de
documentation apparaissent ; ils sont signalés ici, sans réécrire l'historique
des sections 1 à 4 des registres :

| Constat | Preuve étape 1 | Recalcul étape 5 |
|---|---|---|
| `KAY-06` | 8 240,00 € TTC | **7 416,00 € TTC** pour 8 240 L |
| `KAY-07` | 1 615,46 € TTC | **1 615,46 L** et **2 358,54 € TTC** |
| `KAY-08` | 2 248,15 € | **2 173,57 € HT** |
| `KAY-11` | montant non indiqué | **1 090,80 € TTC** |
| `FAN-09` | 363,91 € | **−363,91 €** (FEC inférieur à l'export) |

Ces écarts ne changent pas le bilan : les modèles dbt utilisaient déjà les
données brutes. Ils changent la preuve documentaire. La méthode de recalcul est
celle du modèle : `fct_exclusions`, `fct_emissions`, `stg_fec` et les référentiels.

## 8. Limites

- Les impacts `estimation` et `exposition` sont des ordres de grandeur, pas des
  corrections comptables.
- Les impacts ne sont pas additifs : `quality_summary` déduplique les groupes
  `KAY-ELEC-GAP` et `VAC-ELEC-GAP`, mais les autres impacts de natures différentes
  restent juxtaposés.
- Les 38 questions métier de l'étape 1 restent ouvertes : 38 constats ont le
  statut `à confirmer` et 4 le statut `ouvert` ; 19 constats ont en plus une
  certitude `à confirmer`.
- Aucune donnée source n'est corrigée. Les exclusions sont dans
  `fct_exclusions`, les flags dans `fct_emissions`.
- Le contrôle des valeurs aberrantes se limite au carburant vs capacité du
  réservoir. Il n'y a pas encore de détection IQR générique.
- La détection des doublons se limite aux doublons exacts. Les doublons
  fonctionnels (même trajet, même facture avec un libellé différent) ne sont pas
  couverts.
- L'hypothèse « FEC HT » reste à confirmer pour les trois entreprises.
- Le facteur de la classe Affaires reste celui de la classe Économique
  (`GEN-01`).
- Le carburant, les vols et le FEC ne sont pas rattachés à un site.
- DuckDB est mono-écrivain : ne pas lancer `make quality` et `make ingest` en
  parallèle.

## 9. Commandes

```bash
make quality          # dbt build + rapport des 42 constats
make quality-report   # rapport seul, sans reconstruire
make dashboard        # site statique avec le registre filtrable
make status           # synthèse console du pipeline
make dbt-build        # modèles et tests dbt
make dbt-test         # tests dbt seuls
uv run pytest         # tests Python
```

Filtres du rapport :

```bash
uv run python -m beges.quality --company KAY
uv run python -m beges.quality --severity bloquant
uv run python -m beges.quality --family coherence_entre_sources
uv run python -m beges.quality --company KAY --detail
uv run python -m beges.quality --top 10
uv run python -m beges.quality --markdown
```

Requêtes utiles :

```sql
select constat_id, severity, impact_tco2e, title
from analytics.quality_constats
order by severity_rank, company_code, constat_id;

select *
from analytics.quality_summary
order by company_code;
```

## 10. Références

- `config/quality/KAY.yml`, `FAN.yml`, `VAC.yml`, `_common.yml` : registre.
- `dbt/models/quality/` : détection, registre et synthèse.
- `dbt/tests/assert_quality_*.sql` : tests de cohérence du registre.
- `docs/anomalies/KAY.md`, `FAN.md`, `VAC.md` : questions métier d'origine.
- `docs/dashboard.md` : pages, génération et limites du dashboard.
- `docs/dbt.md` : couche dbt et lineage.
- `README.md` section 5 : familles et format d'un constat.
