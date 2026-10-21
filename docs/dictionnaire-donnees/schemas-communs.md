# Schémas communs

> Colonnes partagées par les entreprises.
> Les spécificités et les écarts sont décrits dans `<CODE>.md`.

## 1. Conventions

| Sujet | Convention | Piège |
|---|---|---|
| Encodage | UTF-8 majoritaire ; CP1252 pour KAY FEC et KAY carburant | ne jamais supposer UTF-8 |
| Délimiteur | virgule, point-virgule, pipe, tabulation | un fichier par format |
| Décimales | virgule ou point selon la source | convertir avant calcul |
| Dates | `jj/mm/aaaa`, `aaaa-mm-jj`, `aaaammjj`, `mm/aaaa`, `aaaa-mm` | parser par source |
| Montants | FEC supposé HT ; exports carburant et vols TTC | ne pas comparer sans TVA |
| Devise | EUR | — |
| Unités | kWh, MWh, L, kg, passager.km | convertir MWh × 1000 |
| Identifiants | codes société, site, PDL, facture, billet | conserver les zéros de tête |

## 2. FEC — colonnes communes

| Colonne | Type | Nullable | Description | Exemple |
|---|---|---|---|---|
| `JournalCode` | Texte | Non | Code journal | `AC`, `PA`, `VE`, `BQ`, `OD` |
| `JournalLib` | Texte | Non | Libellé journal | `Achats` |
| `EcritureNum` | Texte | Non | Numéro d'écriture | `AC000001` |
| `EcritureDate` | Date `aaaammjj` | Non | Date de l'écriture | `20250102` |
| `CompteNum` | Texte | Non | Numéro de compte | `6061100` |
| `CompteLib` | Texte | Non | Libellé du compte | `Électricité` |
| `CompAuxNum` | Texte | Oui | Compte auxiliaire | `F0054` |
| `CompAuxLib` | Texte | Oui | Libellé auxiliaire | `Fournisseur 0054` |
| `PieceRef` | Texte | Non | Référence de pièce | `FAKAY000144` |
| `PieceDate` | Date `aaaammjj` | Non | Date de la pièce | `20250102` |
| `EcritureLib` | Texte | Non | Libellé de l'écriture | `Facture électricité` |
| `Debit` | Décimal | Non | Montant au débit | `64500,76` |
| `Credit` | Décimal | Non | Montant au crédit | `0,00` |
| `EcritureLet` | Texte | Oui | Lettrage | vide |
| `DateLet` | Date | Oui | Date de lettrage | vide |
| `ValidDate` | Date `aaaammjj` | Non | Date de validation | `20250102` |
| `Montantdevise` | Décimal | Oui | Montant en devise | vide |
| `Idevise` | Texte | Oui | Code devise | vide |

Règles :

- `EcritureNum` n'est pas unique : plusieurs lignes par écriture.
- Pour chaque `EcritureNum`, `somme(Debit) = somme(Credit)`.
- Seules les classes 6 (charges) et 21 (immobilisations) entrent dans le calcul.
- Les classes 4, 5 et 7 sont hors périmètre.
- `CompteNum` doit rester du texte pour préserver les zéros de tête.

## 3. Électricité — champs canoniques

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `company_code` | Texte | Oui | KAY, FAN, VAC |
| `site_code` | Texte | Oui | Code site |
| `pdl` | Texte | Non | Point de livraison |
| `month` | Date `aaaa-mm` | Oui | Mois de consommation |
| `period_start` | Date | Non | Début de période |
| `period_end` | Date | Non | Fin de période |
| `consumption_kwh` | Décimal | Oui | Consommation en kWh |
| `amount_ht_eur` | Décimal | Oui | Montant HT |
| `reading_type` | Texte | Non | Réel, Estimé, Régularisation |
| `source_file` | Texte | Oui | Fichier d'origine |
| `source_row` | Entier | Oui | Ligne d'origine |

Règles :

- 12 mois attendus par site et par exercice.
- Convertir les MWh en kWh.
- Ne jamais additionner un relevé réel et sa régularisation sans comprendre le signe.
- Un doublon exact se déduplique ; une régularisation ne se déduplique pas.

## 4. Carburant — champs canoniques

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `company_code` | Texte | Oui | KAY, FAN, VAC |
| `transaction_date` | Date | Oui | Date de transaction |
| `card_id` | Texte | Oui | Carte carburant |
| `vehicle_id` | Texte | Non | Véhicule |
| `product_raw` | Texte | Oui | Libellé brut |
| `product_code` | Texte | Oui | GAZOLE, SP95, INCONNU, NON_CARBURANT |
| `quantity_l` | Décimal | Non | Litres |
| `amount_ttc_eur` | Décimal | Oui | Montant TTC |
| `station` | Texte | Non | Station |
| `source_file` | Texte | Oui | Fichier d'origine |
| `source_row` | Entier | Oui | Ligne d'origine |

Correspondance produit :

| Libellé brut | Code cible | Traitement |
|---|---|---|
| `GAZOLE`, `Gazole`, `B7`, `GO`, `Diesel` | `GAZOLE` | à confirmer pour B7/GO/Diesel |
| `SP95` | `SP95` | — |
| `ADBLUE` | `NON_CARBURANT` | exclure du calcul carburant |
| `PRODUIT 47` | `INCONNU` | signaler, ne pas deviner |

Règles :

- Les montants sont TTC ; le FEC est supposé HT.
- Si les litres manquent, estimer via le prix repère ou passer en méthode monétaire.
- Ne jamais compter ADBLUE comme un carburant.

## 5. Fluides frigorigènes — colonnes communes

| Colonne | Type | Nullable | Description |
|---|---|---|---:|
| `Date intervention` | Date `jj/mm/aaaa` | Non | Date |
| `Site` | Texte | Non | Code site |
| `Equipement` | Texte | Non | Équipement |
| `Fluide` | Texte | Oui | Code fluide |
| `Charge nominale (kg)` | Décimal | Non | Charge du circuit |
| `Quantité rechargée (kg)` | Décimal | Non | Recharge |

Règles :

- Le PRG dépend du fluide ; un code inconnu ne doit pas être deviné.
- La recharge ne doit pas dépasser la charge nominale.
- Un fluide vide est un constat, pas une correction.

## 6. Vols — colonnes communes

| Colonne | Type | Nullable | Description |
|---|---|---|---:|
| `Numero billet` | Texte | Non | Identifiant billet |
| `Date emission` | Date `jj/mm/aaaa` | Non | Émission |
| `Date depart` | Date `jj/mm/aaaa` | Non | Départ |
| `Voyageur` | Texte | Non | Code employé |
| `Origine` | Texte | Non | Aéroport IATA |
| `Destination` | Texte | Oui | Aéroport IATA |
| `Type trajet` | Texte | Non | `AR` ou `AS` |
| `Classe` | Texte | Non | Économique ou Affaires |
| `Statut` | Texte | Non | Émis ou Annulé |
| `Montant TTC (€)` | Décimal | Non | Montant TTC |

Règles :

- `AR` = aller-retour, `AS` = aller simple (à confirmer).
- Un aller-retour compte deux trajets.
- Un billet annulé est exclu du calcul, mais signalé.
- Distance = orthodromie + 95 km ; facteur choisi sur la distance d'un aller.
- Un code aéroport inconnu est un constat.

## 7. Clés et relations

| Entité | Clé naturelle | Remarque |
|---|---|---|
| Société | `company_code` | KAY, FAN, VAC |
| Site | `company_code` + `site_code` | 9 sites |
| Point de livraison | `pdl` | 1 par site |
| Facture électricité | `invoice_id` / `N° facture` | doublons possibles |
| Écriture comptable | `EcritureNum` | plusieurs lignes |
| Pièce comptable | `PieceRef` | facture fournisseur |
| Véhicule | `Immatriculation` / `vehicule` | parc KAY |
| Carte carburant | `N° carte` / `carte` | — |
| Billet d'avion | `Numero billet` | doublons possibles |
| Aéroport | `iata` | 9 codes |

## 8. Recoupements génériques

- Électricité ↔ FEC `60611`.
- Carburant ↔ FEC `60622`.
- Vols ↔ FEC `62511`.
- Hôtels/taxis/repas ↔ FEC `62512`.
- Les montants FEC sont supposés HT ; les exports sont TTC.
- TVA normale La Réunion : 8,5 %.
- Un écart n'est pas forcément une erreur : il peut venir du périmètre, d'un site manquant,
  d'une régularisation ou d'une règle de comptabilisation.
