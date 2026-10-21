# KAY — Kayamb Logistique SAS

> Fiche entreprise. Les schémas communs sont dans `schemas-communs.md`.
> Les anomalies et questions métier sont dans [`../anomalies/KAY.md`](../anomalies/KAY.md).

## 1. Métadonnées

| Champ | Valeur |
|---|---|
| Code | `KAY` |
| Raison sociale | Kayamb Logistique SAS |
| Ville | Le Port |
| Secteur | Transport et logistique portuaire |
| Salariés | 310 |
| Exercice | 2025 |
| Contact métier | fictif |

## 2. Sites

| Code site | Nom | Point de livraison |
|---|---|---|
| `LPT-ENT` | Entrepôt Le Port | `PDL-LPT-ENT` |
| `LPT-SIE` | Siège Le Port | `PDL-LPT-SIE` |
| `LPT-ATL` | Atelier mécanique | `PDL-LPT-ATL` |

## 3. Fichiers reçus

| Source | Fichier | Format | Encodage | Délimiteur | Lignes | Colonnes | Période |
|---|---|---|---:|---|---:|---:|---|
| FEC | `KAY/fec/900000001FEC20251231.txt` | Texte délimité | CP1252 | pipe | 647 | 18 | 2025 |
| Électricité | `KAY/electricite/export_edf_2025.csv` | CSV | UTF-8 | point-virgule | 26 | 8 | 2025 |
| Carburant | `KAY/carburant/transactions_cartes_2025.csv` | CSV | CP1252 | point-virgule | 4 889 | 7 | 2025 |
| Carburant | `KAY/carburant/parc_vehicules.csv` | CSV | CP1252 | point-virgule | 46 | 3 | référence |
| Fluides | `KAY/fluides/interventions_frigoristes_2025.csv` | CSV | UTF-8 | point-virgule | 8 | 6 | 2025 |
| Vols | `KAY/vols/export_agence_voyages_2025.csv` | CSV | UTF-8 | point-virgule | 25 | 10 | 2025 |

**Total** : 6 fichiers, 5 641 lignes de données.

## 4. Spécificités

### FEC

- CP1252, pipe, virgule décimale.
- 647 lignes, 227 écritures, 27 comptes.
- Toutes les écritures sont équilibrées.
- Exercice 2025 uniquement.
- Compte non mappé : `6288000` « Prestations diverses portuaires » (523 298,66 €).
- Comptes hors périmètre : `6351100`, `6411000`, `6451000` (préfixes 63/64).

### Électricité

- 26 lignes, 2 points de livraison sur 3 sites déclarés.
- `PDL-LPT-ENT` : 14 lignes ; `PDL-LPT-SIE` : 12 lignes.
- `PDL-LPT-ATL` absent.
- Mai contient un relevé réel et une régularisation négative.
- Avril est marqué `Estimé`.
- Juillet est présent deux fois à l'identique.
- Total : **590 197 kWh** et **100 333,49 € HT**.

### Carburant

- 4 889 transactions, 46 cartes, 46 véhicules, 3 stations.
- Aucun doublon exact.
- Les 46 immatriculations existent dans le parc.
- Parc : 40 porteurs 19 t (300 L), 6 utilitaires (80 L).
- Produits :

| Produit | Lignes | Interprétation |
|---|---:|---|
| `GAZOLE` | 1 747 | Gazole |
| `B7` | 920 | Gazole (à confirmer) |
| `GO` | 911 | Gazole (à confirmer) |
| `Diesel` | 890 | Gazole (à confirmer) |
| `ADBLUE` | 412 | Non combustible, à exclure |
| `PRODUIT 47` | 9 | Inconnu, à signaler |

- Total : **880 510,01 L** et **1 281 055,79 € TTC**.

### Fluides

- 8 interventions, toutes sur `LPT-ENT`.
- Fluide `R134a`, charge nominale 4,50 kg.
- Recharge comprise entre 0,79 et 1,71 kg : toujours ≤ charge nominale.
- Aucune intervention sur `LPT-SIE` et `LPT-ATL`.

### Vols

- 25 billets, 25 numéros uniques.
- Origine `RUN` pour tous.
- Destinations : `CDG` (9), `ORY` (9), `MRS` (2), `TNR` (2), `JNB` (1), `MRU` (1), 1 vide.
- 20 `AR`, 5 `AS` ; 24 économiques, 1 affaires.
- Aucun annulé, aucun doublon.
- Total TTC : **28 293,32 €**.

## 5. Schémas et écarts

| Source | Schéma brut | Écart avec le commun | Traitement |
|---|---|---|---|
| FEC | 18 colonnes FEC | Aucun écart de colonnes | CP1252, pipe, virgule |
| Électricité | 8 colonnes | Aucun écart majeur | 2 PDL sur 3, doublon et régularisation |
| Carburant | 7 colonnes | Produits multiples | Normaliser les libellés |
| Parc | 3 colonnes | Référentiel véhicules | Valider les immatriculations |
| Fluides | 6 colonnes communes | Aucun écart | Un seul site |
| Vols | 10 colonnes communes | Aucun écart | Une destination vide |

## 6. Comptes FEC utilisés

| Compte | Libellé | Montant (supposé HT) | Préfixe | Poste | Traitement |
|---|---|---:|---|---|---|
| `2182000` | Matériel de transport | 290 000,00 € | `2182` | Immobilisations | monétaire 500 |
| `6061100` | Électricité | 140 659,92 € | `60611` | Électricité | physique |
| `6062200` | Carburants | 1 173 861,36 € | `60622` | Combustion mobile | physique |
| `6063000` | Fournitures et petit équipement | 294 816,60 € | `6063` | Achats de biens | monétaire 450 |
| `6064000` | Fournitures administratives | 41 345,04 € | `6064` | Achats de biens | monétaire 400 |
| `6110000` | Sous-traitance transport | 1 101 862,39 € | `611` | Achats de services | monétaire 300 |
| `6132000` | Locations immobilières | 400 438,98 € | `613` | Achats de services | monétaire 120 |
| `6155000` | Entretien et réparations véhicules | 713 698,17 € | `615` | Achats de services | monétaire 250 |
| `6160000` | Primes d'assurance | 217 332,83 € | `616` | Achats de services | monétaire 50 |
| `6226000` | Honoraires | 93 977,68 € | `6226` | Achats de services | monétaire 110 |
| `6251100` | Billets d'avion | 28 293,31 € | `62511` | Déplacements professionnels | physique |
| `62512000` | Hôtels, taxis et repas | 36 268,15 € | `62512` | Déplacements professionnels | monétaire 300 |
| `6260000` | Frais postaux et télécommunications | 57 471,13 € | `626` | Achats de services | monétaire 150 |
| `6270000` | Services bancaires | 20 409,86 € | `627` | Achats de services | monétaire 40 |
| `6288000` | Prestations diverses portuaires | 523 298,66 € | non mappé | à définir | à définir |
| `6351100` | Contribution économique territoriale | 14 000,00 € | `63` | Hors périmètre | exclu |
| `6411000` | Salaires | 9 672 000,00 € | `64` | Hors périmètre | exclu |
| `6451000` | Cotisations URSSAF | 4 062 240,00 € | `64` | Hors périmètre | exclu |

## 7. Clés

| Entité | Clé | Remarque |
|---|---|---|
| Société | `KAY` | — |
| Site | `site_code` | `LPT-ENT`, `LPT-SIE`, `LPT-ATL` |
| Écriture comptable | `EcritureNum` | non unique, plusieurs lignes |
| Pièce comptable | `PieceRef` | facture fournisseur |
| Facture électricité | `N° facture` | doublon juillet |
| Carburant | date + carte + véhicule + montant | pas de clé transactionnelle fournie |
| Véhicule | `Immatriculation` | 46/46 dans le parc |
| Fluides | date + site + équipement | un seul site |
| Vols | `Numero billet` | 25/25 unique |

## 8. Anomalies et questions

Les 14 anomalies et questions métier sont détaillées dans
[`../anomalies/KAY.md`](../anomalies/KAY.md).

| ID | Sujet | Sévérité | Statut |
|---|---|---|---|
| KAY-01 | Site `LPT-ATL` sans relevé | Bloquant | À confirmer |
| KAY-02 | Doublon de juillet | Bloquant | À confirmer |
| KAY-03 | Régularisation de mai | Alerte | À confirmer |
| KAY-04 | Avril estimé | Alerte | À confirmer |
| KAY-05 | Synonymes de gazole | Alerte | À confirmer |
| KAY-06 | `ADBLUE` | Info | À confirmer |
| KAY-07 | `PRODUIT 47` | Alerte | À confirmer |
| KAY-08 | Écart carburant / FEC | Alerte | À confirmer |
| KAY-09 | Écart électricité / FEC | Bloquant | À confirmer |
| KAY-10 | Compte `6288000` non mappé | Bloquant | À confirmer |
| KAY-11 | Destination vide | Alerte | À confirmer |
| KAY-12 | `AR` / `AS` | Alerte | À confirmer |
| KAY-13 | Fluides absents sur 2 sites | Info | À confirmer |
| KAY-14 | FEC supposé HT | Bloquant | À confirmer |

## 9. Contrôles positifs

| Contrôle | Résultat |
|---|---|
| FEC : 227 écritures équilibrées | OK |
| Carburant : 46 véhicules sur 46 dans le parc | OK |
| Vols : total TTC = FEC `6251100` | OK, écart 0,01 € |
| Carburant : total HT proche de `6062200` après exclusions | OK, écart 2 248,15 € (0,19 %) |
| Fluides : recharge ≤ charge nominale | OK |
| FEC : toutes les dates en 2025 | OK |
| Électricité : `LPT-SIE` 12 mois | OK |
| Carburant : aucun doublon exact | OK |

## 10. Validation

- [ ] Fiche relue
- [ ] Sources complètes
- [ ] Questions métier transmises
