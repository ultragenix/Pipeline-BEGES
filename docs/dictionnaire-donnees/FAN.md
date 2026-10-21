# FAN — Fanjan Agro SA

> Fiche entreprise. Les schémas communs sont dans `schemas-communs.md`.
> Les anomalies et questions métier sont dans [`../anomalies/FAN.md`](../anomalies/FAN.md).

## 1. Métadonnées

| Champ | Valeur |
|---|---|
| Code | `FAN` |
| Raison sociale | Fanjan Agro SA |
| Ville | Saint-Pierre |
| Secteur | Agroalimentaire |
| Salariés | 420 |
| Exercice | 2025 |
| Contact métier | fictif |

## 2. Sites

| Code site | Nom | Point de livraison |
|---|---|---|
| `SPI-USI` | Usine Saint-Pierre | `PDL-SPI-USI` |
| `PIE-FRO` | Chambres froides Pierrefonds | `PDL-PIE-FRO` |
| `SPI-ADM` | Bureaux Saint-Pierre | `PDL-SPI-ADM` |

## 3. Fichiers reçus

| Source | Fichier | Format | Encodage | Délimiteur | Lignes | Colonnes | Période |
|---|---|---|---:|---|---:|---:|---|
| FEC | `FAN/fec/900000002FEC20251231.txt` | Texte délimité | UTF-8 | tabulation | 690 | 18 | 2025 |
| Électricité | `FAN/electricite/releves_electricite_2025.xlsx` | Excel, 3 feuilles | — | — | 36 | 4 | 2025 |
| Carburant | `FAN/carburant/cartes_carburant_2025.csv` | CSV | UTF-8 | virgule | 623 | 5 | 2025 |
| Fluides | `FAN/fluides/interventions_frigoristes_2025.csv` | CSV | UTF-8 | point-virgule | 17 | 6 | 2025 |
| Vols | `FAN/vols/export_agence_voyages_2025.csv` | CSV | UTF-8 | point-virgule | 40 | 10 | 2025 |

**Total** : 5 fichiers, 1 406 lignes de données.

## 4. Spécificités

### FEC

- UTF-8, tabulation, point décimal.
- 690 lignes, 242 écritures, 28 comptes.
- Exercice 2025 uniquement.
- Une écriture déséquilibrée : `AC000042`, écart de 150,00 €.
- Les comptes `6351100`, `6411000` et `6451000` sont hors périmètre (préfixes 63/64).

### Électricité

- Classeur Excel de 3 feuilles : `SPI-USI`, `PIE-FRO`, `SPI-ADM`.
- Lignes 1-2 : titre ; ligne 3 : vide ; ligne 4 : en-tête ; lignes 5-16 : 12 mois.
- `PIE-FRO` est en **MWh**, les deux autres feuilles en **kWh**.
- Conversion obligatoire : `MWh × 1000`.
- Totaux après conversion :

| Site | Consommation | Montant HT |
|---|---:|---:|
| `SPI-USI` | 1 698 589 kWh | 288 760,13 € |
| `PIE-FRO` | 728 316 kWh | 123 813,72 € |
| `SPI-ADM` | 69 044 kWh | 11 737,48 € |
| **Total** | **2 495 949 kWh** | **424 311,33 €** |

### Carburant

- 623 lignes, 12 cartes, 12 véhicules.
- Produits : `GAZOLE` (467 lignes), `SP95` (156 lignes).
- Aucune quantité en litres : seulement `montant_ttc`.
- Aucun référentiel parc fourni.
- Total TTC : 47 357,52 € ; après TVA 8,5 % : 43 647,48 € HT.

### Fluides

- 17 interventions : 12 sur `PIE-FRO`, 5 sur `SPI-USI`.
- Fluides : `R404A` (10), `R449A` (5), 1 ligne vide, 1 code `R-?`.
- Aucune intervention sur `SPI-ADM`.

### Vols

- 40 billets, 40 numéros uniques.
- Origine `RUN` pour tous.
- Destinations : `ORY` (14), `CDG` (14), `MRU` (6), `MRS` (2), `TNR` (2), `LYS` (2).
- 35 `AR`, 5 `AS` ; 35 économiques, 5 affaires.
- Aucun annulé, aucun doublon.
- Total TTC : 51 934,24 €.

## 5. Schémas et écarts

| Source | Schéma brut | Écart avec le commun | Traitement |
|---|---|---|---|
| FEC | 18 colonnes FEC | Aucun écart de colonnes | UTF-8, tabulation, point décimal |
| Électricité | 3 feuilles, 4 colonnes | Excel, lignes de titre, unité par ligne | Lire la feuille, ligne 4, convertir MWh |
| Carburant | 5 colonnes | Pas de quantité, date ISO, virgule | Estimer les litres ou méthode monétaire |
| Fluides | 6 colonnes communes | Aucun écart | Signaler fluide vide et `R-?` |
| Vols | 10 colonnes communes | Aucun écart | Aucun annulé, aucun doublon |

## 6. Comptes FEC utilisés

| Compte | Libellé | Montant (supposé HT) | Préfixe | Poste | Traitement |
|---|---|---:|---|---|---|
| `6011000` | Achats matières premières agricoles | 4 778 173,54 € | `601` | Achats de biens | monétaire 900 |
| `6021000` | Achats emballages | 760 801,03 € | `6021` | Achats de biens | monétaire 600 |
| `6061100` | Électricité | 423 947,42 € | `60611` | Électricité | physique |
| `6062200` | Carburants | 43 647,48 € | `60622` | Combustion mobile | physique |
| `6063000` | Fournitures et petit équipement | 201 494,70 € | `6063` | Achats de biens | monétaire 450 |
| `6064000` | Fournitures administratives | 35 012,98 € | `6064` | Achats de biens | monétaire 400 |
| `6156000` | Maintenance installations frigorifiques | 263 750,06 € | `615` | Achats de services | monétaire 250 |
| `6160000` | Primes d'assurance | 186 034,94 € | `616` | Achats de services | monétaire 50 |
| `6226000` | Honoraires | 121 182,23 € | `6226` | Achats de services | monétaire 110 |
| `6231000` | Publicité | 207 575,75 € | `6231` | Achats de services | monétaire 150 |
| `6241000` | Transports sur achats | 420 922,53 € | `6241` | Fret amont | monétaire 500 |
| `6251100` | Billets d'avion | 51 934,24 € | `62511` | Déplacements professionnels | physique |
| `62512000` | Hôtels, taxis et repas | 47 263,53 € | `62512` | Déplacements professionnels | monétaire 300 |
| `6260000` | Frais postaux et télécommunications | 39 686,21 € | `626` | Achats de services | monétaire 150 |
| `6270000` | Services bancaires | 17 860,69 € | `627` | Achats de services | monétaire 40 |
| `6351100` | Contribution économique territoriale | 14 000,00 € | `63` | Hors périmètre | exclu |
| `6411000` | Salaires | 13 104 000,00 € | `64` | Hors périmètre | exclu |
| `6451000` | Cotisations URSSAF | 5 503 680,00 € | `64` | Hors périmètre | exclu |
| `2154000` | Matériel industriel | 380 000,00 € | `2154` | Immobilisations | monétaire 600 |

## 7. Clés

| Entité | Clé | Remarque |
|---|---|---|
| Société | `FAN` | — |
| Site | `site_code` | `SPI-USI`, `PIE-FRO`, `SPI-ADM` |
| Écriture comptable | `EcritureNum` | non unique, plusieurs lignes |
| Pièce comptable | `PieceRef` | facture fournisseur |
| Électricité | feuille + `Mois` | 12 mois par feuille |
| Carburant | date + carte + véhicule + montant | pas de clé transactionnelle fournie |
| Fluides | date + site + équipement | une date peut avoir plusieurs interventions |
| Vols | `Numero billet` | 40/40 unique |

## 8. Anomalies et questions

Les 13 anomalies et questions métier sont détaillées dans
[`../anomalies/FAN.md`](../anomalies/FAN.md).

| ID | Sujet | Sévérité | Statut |
|---|---|---|---|
| FAN-01 | Unité MWh sur `PIE-FRO` | Bloquant | À confirmer |
| FAN-02 | Carburant sans litres | Bloquant | À confirmer |
| FAN-03 | Référentiel véhicules absent | Alerte | À confirmer |
| FAN-04 | Fluide vide | Alerte | À confirmer |
| FAN-05 | Code `R-?` | Alerte | À confirmer |
| FAN-06 | Écriture `AC000042` déséquilibrée | Bloquant | À confirmer |
| FAN-07 | Mapping `6011000` / `6021000` | Alerte | À confirmer |
| FAN-08 | CET hors périmètre | Info | À confirmer |
| FAN-09 | Écart électricité / FEC | Alerte | À confirmer |
| FAN-10 | Absence de fluides sur `SPI-ADM` | Info | À confirmer |
| FAN-11 | Montants FEC supposés HT | Bloquant | À confirmer |
| FAN-12 | `AR` / `AS` | Alerte | À confirmer |
| FAN-13 | `62512000` en monétaire | Info | À confirmer |

## 9. Contrôles positifs

| Contrôle | Résultat |
|---|---|
| Électricité : 12 mois sur les 3 sites | OK |
| Vols : total TTC = FEC `6251100` | OK, écart 0,00 € |
| Carburant : total HT = FEC `6062200` | OK, écart 0,00 € |
| Vols : aucun annulé, aucun doublon | OK |
| Fluides : recharge ≤ charge nominale | OK |
| FEC : toutes les dates en 2025 | OK |

## 10. Validation

- [ ] Fiche relue
- [ ] Sources complètes
- [ ] Questions métier transmises
