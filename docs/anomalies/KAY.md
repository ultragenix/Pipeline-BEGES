# Anomalies et questions métier — KAY

> Kayamb Logistique SAS. Les schémas sont dans `../dictionnaire-donnees/KAY.md`.

## 1. Résumé

| ID | Source | Constat | Sévérité | Certitude | Question métier | Impact | Statut |
|---|---|---|---|---|---|---|---|
| KAY-01 | Électricité | Site `LPT-ATL` déclaré mais aucun relevé reçu | Bloquant | Certain | Le site a-t-il consommé de l'électricité en 2025 ? | Bilan sous-estimé | À confirmer |
| KAY-02 | Électricité | Facture de juillet présente deux fois à l'identique | Bloquant | Certain | La facture est-elle réellement dupliquée dans l'export ? | Double comptage | À confirmer |
| KAY-03 | Électricité | Mai : relevé réel + régularisation négative | Alerte | Certain | La régularisation corrige-t-elle avril (estimé) ou mai ? | Net à recalculer | À confirmer |
| KAY-04 | Électricité | Avril estimé à `LPT-ENT` | Alerte | Certain | L'estimation d'avril a-t-elle été corrigée plus tard ? | Incertitude sur le scope 2 | À confirmer |
| KAY-05 | Carburant | `B7`, `GO`, `Diesel` : synonymes de gazole ? | Alerte | À confirmer | Ces libellés sont-ils tous du gazole ? | Facteur d'émission erroné | À confirmer |
| KAY-06 | Carburant | `ADBLUE` présent (412 lignes) | Info | Certain | Confirmez-vous l'exclusion d'`ADBLUE` du calcul carburant ? | Surévaluation si compté | À confirmer |
| KAY-07 | Carburant | `PRODUIT 47` inconnu (9 lignes) | Alerte | Certain | Qu'est-ce que `PRODUIT 47` ? | Non calculable | À confirmer |
| KAY-08 | Carburant / FEC | Écart de 2 248,15 € avec `6062200` | Alerte | À confirmer | L'écart vient-il d'un arrondi ou d'une ligne manquante ? | Bilan légèrement faux | À confirmer |
| KAY-09 | Électricité / FEC | Écart de 40 326,43 € avec `6061100` | Bloquant | À confirmer | L'écart correspond-il au site `LPT-ATL` manquant ? | Bilan sous-estimé | À confirmer |
| KAY-10 | FEC | `6288000` « Prestations diverses portuaires » non mappé | Bloquant | Certain | Quel poste et quel ratio appliquer à ces prestations ? | 523 298,66 € non valorisés | À confirmer |
| KAY-11 | Vols | Une destination vide | Alerte | Certain | Quelle est la destination de ce billet ? | Distance non calculable | À confirmer |
| KAY-12 | Vols | `AR` / `AS` | Alerte | À confirmer | `AS` signifie-t-il bien aller simple ? | Doublement ou omission | À confirmer |
| KAY-13 | Fluides | Aucune intervention sur `LPT-SIE` et `LPT-ATL` | Info | À confirmer | Est-ce normal (pas d'équipement frigorifique) ? | Complétude scope 1 | À confirmer |
| KAY-14 | FEC | Montants supposés HT | Bloquant | À confirmer | Les montants du FEC sont-ils bien HT ? | Confusion HT/TTC | À confirmer |

## 2. Détail

### KAY-01 — Site LPT-ATL sans relevé électrique

**Constat** : trois sites sont déclarés (`LPT-ENT`, `LPT-SIE`, `LPT-ATL`), mais seuls
deux points de livraison sont présents dans l'export EDF.

**Preuve** : `Point de livraison` contient `PDL-LPT-ENT` (14 lignes) et `PDL-LPT-SIE`
(12 lignes). Aucune ligne pour `PDL-LPT-ATL`. Le site `LPT-ATL` est déclaré dans
le référentiel client.

**Pourquoi c'est important** : sans relevé, la consommation du site est absente du
scope 2. Le bilan est faux tant que le site n'est pas couvert ou justifié.

**Question au métier** : le site `LPT-ATL` a-t-il consommé de l'électricité en 2025 ?
Si oui, pouvez-vous fournir les relevés ou les factures ?

**Réponse attendue** : relevés manquants, confirmation d'une consommation nulle, ou
justification d'un site hors périmètre.

**Impact estimé** : l'écart avec le FEC `6061100` est de 40 326,43 €. À 0,17 €/kWh,
cela représente environ 237 000 kWh, soit environ 185 tCO₂e. À recalculer avec les
vraies données du site.

**Traitement proposé** : constat bloquant, pas de fallback silencieux.

**Statut** : À confirmer.

### KAY-02 — Doublon de juillet

**Constat** : la facture `EDF-KAY-LPT-ENT-202507` apparaît deux fois à l'identique.

**Preuve** : deux lignes identiques pour `PDL-LPT-ENT`, juillet 2025 :
31 734,00 kWh, 5 394,78 € HT, type `Réel`.

**Pourquoi c'est important** : si les deux lignes sont conservées, la consommation
de juillet est comptée deux fois.

**Question au métier** : la facture de juillet est-elle réellement présente deux fois
dans l'export, ou s'agit-il d'une erreur d'extraction ?

**Réponse attendue** : confirmation du doublon ou justification d'une seconde facture.

**Impact estimé** : 31 734 kWh × 0,780 / 1000 ≈ 24,75 tCO₂e.

**Traitement proposé** : déduplication exacte, constat `Info` si confirmé.

**Statut** : À confirmer.

### KAY-03 — Régularisation de mai et estimation d'avril

**Constat** : mai contient un relevé réel de 36 544 kWh et une régularisation négative
de −11 751 kWh. Avril est marqué `Estimé` à 50 920 kWh.

**Preuve** :
- avril : `EDF-KAY-LPT-ENT-202504`, 50 920 kWh, `Estimé`.
- mai : `EDF-KAY-LPT-ENT-202505`, 36 544 kWh, `Réel`.
- mai : `EDF-KAY-LPT-ENT-202505R`, −11 751 kWh, `Régularisation`.

**Pourquoi c'est important** : une régularisation négative peut corriger une estimation
précédente. Si on déduplique par mois, on perd la régularisation ; si on additionne tout,
on peut compter deux fois le réel.

**Question au métier** : la régularisation de mai corrige-t-elle l'estimation d'avril,
ou une consommation de mai ? Faut-il la rattacher à avril ou à mai ?

**Réponse attendue** : mois de rattachement et traitement attendu.

**Impact estimé** : 11 751 kWh × 0,780 / 1000 ≈ 9,17 tCO₂e.

**Traitement proposé** : conserver réel + régularisation, tracer le mois de rattachement,
et ne jamais dédupliquer une régularisation.

**Statut** : À confirmer.

### KAY-06 — ADBLUE

**Constat** : 412 lignes `ADBLUE` représentent 8 240,00 € TTC et 20,00 L par transaction.

**Preuve** : colonne `Produit` = `ADBLUE` ; 412 lignes ; quantité totale 8 240 L.

**Pourquoi c'est important** : l'ADBLUE n'est pas un carburant. Le compter comme du gazole
surévalue le scope 1.

**Question au métier** : confirmez-vous que l'ADBLUE doit être exclu du calcul carburant ?

**Réponse attendue** : oui/non, avec traitement attendu.

**Impact estimé** : si compté comme du gazole, 8 240 L × 3,10 / 1000 ≈ 25,5 tCO₂e.
À exclure.

**Traitement proposé** : exclure, constat `Info` pour transparence.

**Statut** : À confirmer.

### KAY-10 — Compte 6288000 non mappé

**Constat** : le compte `6288000` « Prestations diverses portuaires » totalise
523 298,66 € et n'apparaît pas dans la table de correspondance fournie.

**Preuve** : FEC KAY, `CompteNum = 6288000`, 12 lignes, débit total 523 298,66 €.

**Pourquoi c'est important** : sans poste ni ratio, cette dépense est absente du bilan
monétaire. Elle peut représenter un impact important.

**Question au métier** : à quel poste et quel ratio rattacher les prestations portuaires ?
S'agit-il d'achats de services, de fret amont, ou d'un autre poste ?

**Réponse attendue** : poste, scope et ratio.

**Impact estimé** : 523,30 k€ × ratio. Fourchette indicative :
- 120 kgCO₂e/k€ → 62,8 tCO₂e
- 250 → 130,8 tCO₂e
- 300 → 157,0 tCO₂e
- 500 → 261,6 tCO₂e

**Traitement proposé** : constat bloquant, aucune valeur par défaut inventée.

**Statut** : À confirmer.

### KAY-09 — Écart électricité / FEC

**Constat** : l'export électricité totalise 100 333,49 € HT, le compte `6061100` totalise
140 659,92 €, soit un écart de 40 326,43 €.

**Preuve** : somme des 26 lignes EDF vs somme des débits `6061100` du FEC.

**Pourquoi c'est important** : l'écart peut correspondre au site `LPT-ATL` manquant,
à une facture absente ou à un autre périmètre.

**Question au métier** : l'écart de 40 326,43 € correspond-il au site `LPT-ATL`,
à une facture manquante ou à un autre périmètre ?

**Réponse attendue** : explication ou factures complémentaires.

**Impact estimé** : lié à KAY-01 ; à recalculer après récupération du site.

**Traitement proposé** : constat bloquant, pas de correction silencieuse.

**Statut** : À confirmer.

### KAY-11 — Destination vide

**Constat** : un billet KAY n'a pas de destination.

**Preuve** : `export_agence_voyages_2025.csv`, colonne `Destination` vide sur une ligne.

**Pourquoi c'est important** : sans destination, la distance et le facteur de vol ne sont
pas calculables.

**Question au métier** : quelle est la destination de ce billet ?

**Réponse attendue** : code IATA.

**Impact estimé** : non calculable.

**Traitement proposé** : signaler, exclure du calcul physique tant que la destination
n'est pas connue.

**Statut** : À confirmer.

### KAY-05, KAY-07, KAY-08, KAY-12, KAY-13, KAY-14

Ces points sont détaillés dans le résumé et suivent le même format :

- **KAY-05** : confirmer que `B7`, `GO` et `Diesel` sont du gazole.
- **KAY-07** : identifier `PRODUIT 47` (9 lignes, 1 615,46 € TTC).
- **KAY-08** : expliquer l'écart de 2 248,15 € entre le carburant et `6062200`.
- **KAY-12** : confirmer `AS` = aller simple.
- **KAY-13** : confirmer l'absence de fluides sur `LPT-SIE` et `LPT-ATL`.
- **KAY-14** : confirmer que le FEC est HT.

## 3. Contrôles positifs

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

## 4. Journal des réponses

| Date | ID | Réponse | Décision | Impact |
|---|---|---|---|---|
| | | | | |

## 5. Constats calculés — étape 5

> Recalculés par `analytics.quality_constats` à partir des données brutes.
> Le détail narratif des sections 1 à 4 reste la question d'origine.
> Registre central : [`../quality.md`](../quality.md).

| ID | Famille | Sévérité | Certitude | Statut | Traitement | Impact | Titre |
|---|---|---|---|---|---|---|---|
| KAY-01 | complétude | bloquant | certain | à confirmer | aucun | 185,03 tCO₂e / 40 326,43 € est. | Site LPT-ATL sans relevé électrique |
| KAY-02 | unicité | bloquant | certain | à confirmer | exclu | 24,75 tCO₂e / 5 394,78 € non compté | Facture électricité de juillet dupliquée |
| KAY-03 | cohérence interne | alerte | certain | à confirmer | conservé | −9,17 tCO₂e compté | Régularisation négative en mai |
| KAY-04 | complétude | alerte | certain | à confirmer | conservé | 39,72 tCO₂e compté | Relevé d'avril estimé |
| KAY-05 | intégrité référentielle | alerte | à confirmer | à confirmer | conservé | 1 642,65 tCO₂e exposé | Libellés B7, GO et Diesel à confirmer |
| KAY-06 | conformité format | info | certain | à confirmer | exclu | 25,54 tCO₂e / 7 416,00 € non compté | ADBLUE exclu du calcul carburant |
| KAY-07 | validité | alerte | certain | à confirmer | exclu | 2 358,54 € | Produit 47 inconnu |
| KAY-08 | cohérence entre sources | alerte | à confirmer | à confirmer | aucun | 4,62 tCO₂e / 2 173,57 € est. | Écart entre le carburant et le FEC 6062200 |
| KAY-09 | cohérence entre sources | bloquant | à confirmer | à confirmer | aucun | 185,03 tCO₂e / 40 326,43 € est. | Écart entre l'électricité et le FEC 6061100 |
| KAY-10 | intégrité référentielle | bloquant | certain | à confirmer | exclu | 523 298,66 € exposé | Compte 6288000 non mappé |
| KAY-11 | validité | alerte | certain | à confirmer | exclu | 1 090,80 € | Destination de vol vide |
| KAY-12 | conformité format | alerte | à confirmer | à confirmer | conservé | 5,84 tCO₂e exposé | Aller simple / aller-retour à confirmer |
| KAY-13 | complétude | info | à confirmer | à confirmer | aucun | n.c. | Aucune intervention frigoriste sur LPT-SIE et LPT-ATL |
| KAY-14 | conformité format | bloquant | à confirmer | à confirmer | aucun | n.c. | FEC supposé HT |
| KAY-15 | conformité format | info | certain | ouvert | exclu | 14 000,00 € non compté | CET en classe 6 mais hors périmètre |
| KAY-16 | valeurs aberrantes | alerte | certain | ouvert | aucun | 0,31 tCO₂e exposé | Transaction carburant supérieure à la capacité du réservoir |

### Écarts avec les preuves de l'étape 1

- **KAY-06** : 412 lignes ADBLUE pour **8 240 L et 7 416,00 € TTC**, et non
  8 240,00 €. L'impact de 25,54 tCO₂e non compté est inchangé.
- **KAY-07** : 9 lignes pour **1 615,46 L et 2 358,54 € TTC**. Le registre
  initial confondait litres et euros.
- **KAY-08** : l'écart recalculé est de **2 173,57 € HT** (FEC 1 173 861,36 €
  moins carburant HT 1 171 687,79 €), et non 2 248,15 €. L'ordre de grandeur
  reste 0,19 %.
- **KAY-11** : le billet sans destination représente **1 090,80 € TTC**.
- **KAY-05** : 2 721 lignes, 529 886,02 L et 1 642,65 tCO₂e exposés.
- **KAY-12** : 5 billets AS, 2 796,82 € TTC et 5,84 tCO₂e.

### Nouveaux constats issus des contrôles

- **KAY-15** : la CET `6351100` (14 000,00 €) est en classe 6 mais exclue
  comme les autres comptes 63. Constat `info`, question métier ouverte.
- **KAY-16** : le 14/08/2025, le véhicule `FK-107-RE` a une transaction de
  400 L pour un réservoir de 300 L. L'excédent de 100 L représente 0,31 tCO₂e
  exposé. Constat `alerte`, à confirmer.

### Impacts partagés

`KAY-01` et `KAY-09` partagent le groupe `KAY-ELEC-GAP` : l'écart de
40 326,43 € est cohérent avec le site manquant, mais il n'est pas prouvé que
tout l'écart vienne de là. Les deux impacts ne sont pas additifs.
