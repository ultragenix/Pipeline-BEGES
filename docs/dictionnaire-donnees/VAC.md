# VAC — Hôtels Vacoa Bleu SARL

> Fiche entreprise. Les schémas communs sont dans `schemas-communs.md`.
> Les anomalies et questions métier sont dans [`../anomalies/VAC.md`](../anomalies/VAC.md).

## 1. Métadonnées

| Champ | Valeur |
|---|---|
| Code | `VAC` |
| Raison sociale | Hôtels Vacoa Bleu SARL |
| Ville | Saint-Gilles-les-Bains |
| Secteur | Hôtellerie |
| Salariés | 280 |
| Exercice | 2025 |
| Contact métier | fictif |

## 2. Sites

| Code site | Nom | Point de livraison |
|---|---|---|
| `SGI-HT1` | Hôtel Vacoa Lagon | `PDL-SGI-HT1` |
| `SGI-HT2` | Hôtel Vacoa des Hauts | `PDL-SGI-HT2` |
| `SGI-BLA` | Blanchisserie | `PDL-SGI-BLA` |

## 3. Fichiers reçus

| Source | Fichier | Format | Encodage | Délimiteur | Lignes | Colonnes | Période |
|---|---|---|---:|---|---:|---:|---|
| FEC | `VAC/fec/900000003FEC20251231.txt` | Texte délimité | UTF-8 | pipe | 662 | 18 | 2025 |
| Électricité | `VAC/electricite/energy_invoices_2025.csv` | CSV | UTF-8 | virgule | 33 | 5 | 2025 |
| Carburant S1 | `VAC/carburant/carburant_2025_S1.csv` | CSV | UTF-8 | point-virgule | 182 | 5 | S1 2025 |
| Carburant S2 | `VAC/carburant/carburant_2025_S2.csv` | CSV | UTF-8 | point-virgule | 185 | 5 | S2 2025 |
| Fluides | `VAC/fluides/interventions_frigoristes_2025.csv` | CSV | UTF-8 | point-virgule | 32 | 6 | 2025 |
| Vols | `VAC/vols/export_agence_voyages_2025.csv` | CSV | UTF-8 | point-virgule | 122 | 10 | 2025 |

**Total** : 6 fichiers, 1 216 lignes de données.

## 4. Spécificités

### FEC

- UTF-8, pipe, virgule décimale.
- 662 lignes, 233 écritures, 27 comptes.
- Toutes les écritures sont équilibrées.
- Exercice 2025 uniquement.
- Comptes hors périmètre : `6351100`, `6411000`, `6451000` (préfixes 63/64).

### Électricité

- 33 lignes, 3 sites × 11 mois (janvier à novembre).
- **Décembre manquant sur les 3 sites.**
- Colonnes anglaises : `invoice_id`, `site_code`, `month`, `kwh`, `amount_eur`.
- Totaux :

| Site | Mois | Consommation | Montant HT |
|---|---:|---:|---:|
| `SGI-BLA` | 11 | 197 422 kWh | 33 561,74 € |
| `SGI-HT1` | 11 | 913 138 kWh | 155 233,46 € |
| `SGI-HT2` | 11 | 442 366 kWh | 75 202,22 € |
| **Total** | **33** | **1 552 926 kWh** | **263 997,42 €** |

### Carburant

- S1 : 182 lignes, colonne `Quantite (L)`.
- S2 : 185 lignes, colonne `Volume`.
- **Dérive de schéma** entre les deux semestres.
- 5 cartes : `VAC-NAV-0` à `VAC-NAV-4`.
- Produit unique : `Gazole`.
- Total : **21 201,93 L** et **30 954,76 € TTC**.
- Après TVA 8,5 % : **28 529,73 € HT**.

### Fluides

- 32 interventions : 18 sur `SGI-HT1`, 10 sur `SGI-HT2`, 4 sur `SGI-BLA`.
- Fluides : `R410A` (22), `R32` (10).
- Charges nominales : 2,40 kg, 1,80 kg, 12,00 kg.
- Recharge toujours ≤ charge nominale.

### Vols

- 122 lignes, **120 numéros de billets distincts**.
- 2 billets dupliqués à l'identique : `VAC-TKT-0009` et `VAC-TKT-0061`.
- 3 billets annulés : `VAC-TKT-0004`, `VAC-TKT-0018`, `VAC-TKT-0042`.
- Origine `RUN` pour tous.
- Destinations : `ORY` (44), `CDG` (39), `MRU` (15), `MRS` (8), `LYS` (5), `DZA` (5), `TNR` (5), `JNB` (1).
- 107 `AR`, 15 `AS` ; 112 économiques, 10 affaires.
- Total TTC : **141 069,17 €**.
- Après exclusion des annulés et doublons : **134 954,66 €**, contre **134 954,62 €** au FEC `6251100`.

## 5. Schémas et écarts

| Source | Schéma brut | Écart avec le commun | Traitement |
|---|---|---|---|
| FEC | 18 colonnes FEC | Aucun écart de colonnes | UTF-8, pipe, virgule |
| Électricité | 5 colonnes anglaises | Nommage anglais, mois `aaaa-mm` | Mapping vers le canonique |
| Carburant S1 | 5 colonnes | `Quantite (L)` | Mapper vers `quantity_l` |
| Carburant S2 | 5 colonnes | `Volume` | Mapper vers `quantity_l` |
| Fluides | 6 colonnes communes | Aucun écart | Trois sites |
| Vols | 10 colonnes communes | Doublons et annulés | Dédupliquer et exclure |

## 6. Comptes FEC utilisés

| Compte | Libellé | Montant (supposé HT) | Préfixe | Poste | Traitement |
|---|---|---:|---|---|---|
| `2184000` | Mobilier | 95 000,00 € | `2184` | Immobilisations | monétaire 400 |
| `6011000` | Achats denrées alimentaires | 2 091 151,75 € | `601` | Achats de biens | monétaire 900 |
| `6022000` | Achats boissons | 593 002,61 € | `6022` | Achats de biens | monétaire 800 |
| `6061100` | Électricité | 290 242,61 € | `60611` | Électricité | physique |
| `6062200` | Carburants | 28 529,76 € | `60622` | Combustion mobile | physique |
| `6063000` | Fournitures et petit équipement | 264 507,56 € | `6063` | Achats de biens | monétaire 450 |
| `6064000` | Fournitures administratives | 28 089,30 € | `6064` | Achats de biens | monétaire 400 |
| `6156000` | Maintenance climatisation | 134 865,57 € | `615` | Achats de services | monétaire 250 |
| `6160000` | Primes d'assurance | 144 166,12 € | `616` | Achats de services | monétaire 50 |
| `6226000` | Honoraires | 71 013,12 € | `6226` | Achats de services | monétaire 110 |
| `6231000` | Publicité et commission plateformes | 364 841,57 € | `6231` | Achats de services | monétaire 150, à confirmer |
| `6251100` | Billets d'avion | 134 954,62 € | `62511` | Déplacements professionnels | physique |
| `62512000` | Hôtels, taxis et repas | 21 794,02 € | `62512` | Déplacements professionnels | monétaire 300 |
| `6260000` | Frais postaux et télécommunications | 32 770,98 € | `626` | Achats de services | monétaire 150 |
| `6270000` | Services bancaires | 26 139,41 € | `627` | Achats de services | monétaire 40 |
| `6351100` | Contribution économique territoriale | 14 000,00 € | `63` | Hors périmètre | exclu |
| `6411000` | Salaires | 8 736 000,00 € | `64` | Hors périmètre | exclu |
| `6451000` | Cotisations URSSAF | 3 669 120,00 € | `64` | Hors périmètre | exclu |

## 7. Clés

| Entité | Clé | Remarque |
|---|---|---|
| Société | `VAC` | — |
| Site | `site_code` | `SGI-HT1`, `SGI-HT2`, `SGI-BLA` |
| Écriture comptable | `EcritureNum` | non unique, plusieurs lignes |
| Pièce comptable | `PieceRef` | facture fournisseur |
| Électricité | `invoice_id` | 33/33 unique |
| Carburant | date + carte + produit + montant | pas de clé transactionnelle fournie |
| Fluides | date + site + équipement | une date peut avoir plusieurs interventions |
| Vols | `Numero billet` | 120 distincts / 122 lignes |

## 8. Anomalies et questions

Les 11 anomalies et questions métier sont détaillées dans
[`../anomalies/VAC.md`](../anomalies/VAC.md).

| ID | Sujet | Sévérité | Statut |
|---|---|---|---|
| VAC-01 | Décembre manquant | Bloquant | À confirmer |
| VAC-02 | Écart électricité / FEC | Alerte | À confirmer |
| VAC-03 | Dérive de schéma S1/S2 | Bloquant | À confirmer |
| VAC-04 | Billets dupliqués | Bloquant | À confirmer |
| VAC-05 | Billets annulés | Info | À confirmer |
| VAC-06 | Cartes sans référentiel véhicule | Alerte | À confirmer |
| VAC-07 | FEC supposé HT | Bloquant | À confirmer |
| VAC-08 | `AR` / `AS` | Alerte | À confirmer |
| VAC-09 | Mapping `6011000` / `6022000` | Alerte | À confirmer |
| VAC-10 | CET hors périmètre | Info | À confirmer |
| VAC-11 | Publicité et commissions plateformes | Alerte | À confirmer |

## 9. Contrôles positifs

| Contrôle | Résultat |
|---|---|
| FEC : 233 écritures équilibrées | OK |
| Électricité : 33 factures uniques | OK |
| Électricité : 3 sites couverts | OK, 11 mois chacun |
| Carburant : S1 + S2 couvrent janvier à décembre | OK |
| Carburant : total HT = FEC `6062200` | OK, écart 0,03 € |
| Vols : total après exclusions = FEC `6251100` | OK, écart 0,04 € |
| Fluides : R410A et R32 connus, recharge ≤ nominal | OK |
| FEC : toutes les dates en 2025 | OK |

## 10. Validation

- [ ] Fiche relue
- [ ] Sources complètes
- [ ] Questions métier transmises
