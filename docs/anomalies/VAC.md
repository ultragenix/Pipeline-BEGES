# Anomalies et questions métier — VAC

> Hôtels Vacoa Bleu SARL. Les schémas sont dans `../dictionnaire-donnees/VAC.md`.

## 1. Résumé

| ID | Source | Constat | Sévérité | Certitude | Question métier | Impact | Statut |
|---|---|---|---|---|---|---|---|
| VAC-01 | Électricité | Décembre manquant sur les 3 sites | Bloquant | Certain | La facture de décembre est-elle disponible ? | Bilan sous-estimé | À confirmer |
| VAC-02 | Électricité / FEC | Écart de 26 245,19 € avec `6061100` | Alerte | À confirmer | L'écart correspond-il à décembre manquant ? | Bilan sous-estimé | À confirmer |
| VAC-03 | Carburant | S1 `Quantite (L)` vs S2 `Volume` | Bloquant | Certain | Les deux colonnes représentent-elles bien des litres ? | S2 perdue si non mappée | À confirmer |
| VAC-04 | Vols | 2 billets dupliqués à l'identique | Bloquant | Certain | Les billets `VAC-TKT-0009` et `VAC-TKT-0061` sont-ils des doublons ? | Double comptage | À confirmer |
| VAC-05 | Vols | 3 billets annulés | Info | Certain | Les billets annulés doivent-ils être exclus ? | Surévaluation si comptés | À confirmer |
| VAC-06 | Carburant | 5 cartes, aucun référentiel véhicule | Alerte | Certain | Pouvez-vous fournir l'affectation carte/véhicule ? | Intégrité non vérifiable | À confirmer |
| VAC-07 | FEC | Montants supposés HT | Bloquant | À confirmer | Les montants du FEC sont-ils bien HT ? | Confusion HT/TTC | À confirmer |
| VAC-08 | Vols | `AR` / `AS` | Alerte | À confirmer | `AS` signifie-t-il bien aller simple ? | Doublement ou omission | À confirmer |
| VAC-09 | FEC | Mapping `6011000` / `6022000` | Alerte | À confirmer | Confirmez-vous matières premières (900) et boissons (800) ? | Poste ou ratio erroné | À confirmer |
| VAC-10 | FEC | `6351100` CET en classe 6 mais hors périmètre | Info | Certain | Confirmez-vous l'exclusion de la CET ? | Double comptage possible | À confirmer |
| VAC-11 | FEC | `6231000` publicité et commissions plateformes | Alerte | À confirmer | Les commissions plateformes relèvent-elles de la publicité (150) ? | Ratio possiblement erroné | À confirmer |

## 2. Détail

### VAC-01 — Décembre manquant

**Constat** : l'export électricité contient 11 mois par site (janvier à novembre 2025).
Décembre est absent sur les 3 sites.

**Preuve** : 33 lignes, 3 sites × 11 mois. Mois observés : `2025-01` à `2025-11`.

**Pourquoi c'est important** : le scope 2 est incomplet. Une année complète doit couvrir
12 mois par site.

**Question au métier** : la facture de décembre est-elle disponible ? A-t-elle été reçue
après l'export, ou manque-t-elle réellement ?

**Réponse attendue** : facture de décembre ou confirmation d'une absence.

**Impact estimé** : consommation mensuelle moyenne ≈ 141 175 kWh pour les 3 sites,
soit environ 110 tCO₂e pour décembre. L'écart avec le FEC `6061100` est de 26 245,19 €,
soit environ 120 tCO₂e. À recalculer avec la vraie facture.

**Traitement proposé** : constat bloquant, pas d'extrapolation silencieuse.

**Statut** : À confirmer.

### VAC-02 — Écart électricité / FEC

**Constat** : l'export électricité totalise 263 997,42 € HT, le compte `6061100` totalise
290 242,61 €, soit un écart de 26 245,19 €.

**Preuve** : somme des 33 lignes vs somme des débits `6061100` du FEC.
Détail par site :
- `SGI-BLA` : 197 422 kWh, 33 561,74 €, 11 mois.
- `SGI-HT1` : 913 138 kWh, 155 233,46 €, 11 mois.
- `SGI-HT2` : 442 366 kWh, 75 202,22 €, 11 mois.

**Pourquoi c'est important** : l'écart est cohérent avec décembre manquant, mais il faut
le confirmer pour ne pas compenser une autre erreur.

**Question au métier** : l'écart de 26 245,19 € correspond-il à la facture de décembre
manquante, ou à un autre périmètre ?

**Réponse attendue** : facture de décembre ou explication.

**Impact estimé** : environ 120 tCO₂e si tout l'écart est de l'électricité.

**Traitement proposé** : constat d'alerte, à rapprocher de VAC-01.

**Statut** : À confirmer.

### VAC-03 — Dérive de schéma carburant S1/S2

**Constat** : le fichier S1 utilise la colonne `Quantite (L)`, le fichier S2 utilise
`Volume`. Les deux représentent des litres, mais le nom change au milieu de l'année.

**Preuve** : S1, 182 lignes, colonne `Quantite (L)` ; S2, 185 lignes, colonne `Volume`.

**Pourquoi c'est important** : une concaténation naïve perd la quantité de S2 ou la
décale. Sans mapping, le second semestre n'est pas compté.

**Question au métier** : confirmez-vous que `Volume` et `Quantite (L)` sont bien des litres ?

**Réponse attendue** : oui/non, avec unité confirmée.

**Impact estimé** : S2 représente 10 576,32 L, soit environ 32,8 tCO₂e si perdu.

**Traitement proposé** : mapping des deux colonnes vers `quantity_l`, contrôle de schéma.

**Statut** : À confirmer.

### VAC-04 — Billets dupliqués

**Constat** : deux numéros de billet apparaissent deux fois à l'identique :
`VAC-TKT-0009` et `VAC-TKT-0061`.

**Preuve** :
- `VAC-TKT-0009` : RUN → DZA, 476,63 € TTC, 2 lignes identiques.
- `VAC-TKT-0061` : RUN → ORY, 2 673,35 € TTC, 2 lignes identiques.

**Pourquoi c'est important** : les doublons doublent le nombre de trajets et les
émissions associées.

**Question au métier** : ces deux billets sont-ils réellement présents deux fois dans
l'export, ou s'agit-il d'une erreur d'extraction ?

**Réponse attendue** : confirmation des doublons.

**Impact estimé** : 3 149,98 € TTC ; impact carbone à recalculer après distance.

**Traitement proposé** : déduplication exacte, constat `Info` si confirmé.

**Statut** : À confirmer.

### VAC-05 — Billets annulés

**Constat** : trois billets sont marqués `Annulé`.

**Preuve** :
- `VAC-TKT-0004` : RUN → CDG, 586,61 € TTC.
- `VAC-TKT-0018` : RUN → CDG, 1 678,33 € TTC.
- `VAC-TKT-0042` : RUN → MRS, 699,59 € TTC.

**Pourquoi c'est important** : un billet annulé ne correspond pas à un déplacement réalisé.

**Question au métier** : ces billets ont-ils été remboursés, remplacés ou finalement
utilisés ?

**Réponse attendue** : exclusion confirmée ou justification.

**Impact estimé** : 2 964,53 € TTC ; impact carbone à exclure.

**Traitement proposé** : exclure du calcul, conserver le constat.

**Statut** : À confirmer.

### VAC-06 — Cartes carburant sans référentiel véhicule

**Constat** : 5 cartes carburant (`VAC-NAV-0` à `VAC-NAV-4`), mais aucun identifiant
véhicule dans le fichier et aucun référentiel parc fourni.

**Preuve** : colonnes `Date`, `Carte`, `Produit`, `Quantite (L)`/`Volume`, `Montant (EUR)`.

**Pourquoi c'est important** : on ne peut pas vérifier l'affectation des cartes ni
détecter une carte inconnue.

**Question au métier** : pouvez-vous fournir le parc véhicules et l'affectation
carte/véhicule ?

**Réponse attendue** : référentiel ou confirmation que les 5 cartes sont valides.

**Impact estimé** : intégrité, pas d'impact carbone direct.

**Traitement proposé** : constat d'alerte, pas de blocage du calcul.

**Statut** : À confirmer.

### VAC-09 — Mapping 6011000 / 6022000

**Constat** : les comptes `6011000` (2 091 151,75 €) et `6022000` (593 002,61 €)
correspondent aux matières premières et aux boissons.

**Preuve** : libellés FEC « Achats denrées alimentaires » et « Achats boissons ».

**Pourquoi c'est important** : le préfixe le plus long détermine le poste et le ratio
(900 pour `601`, 800 pour `6022`).

**Question au métier** : confirmez-vous ces deux mappings et ces ratios ?

**Réponse attendue** : oui/non, avec ratio corrigé si besoin.

**Impact estimé** : 2 684,15 k€ au total ; un ratio erroné change fortement le bilan.

**Traitement proposé** : mapping documenté, test de non-régression.

**Statut** : À confirmer.

### VAC-11 — Publicité et commissions plateformes

**Constat** : le compte `6231000` « Publicité et commission plateformes » totalise
364 841,57 €.

**Preuve** : FEC VAC, `CompteNum = 6231000`, 12 lignes.

**Pourquoi c'est important** : le ratio `6231` (150 kgCO₂e/k€) est prévu pour la publicité ;
les commissions de plateformes peuvent relever d'un autre poste.

**Question au métier** : les commissions plateformes doivent-elles être traitées comme
de la publicité, ou comme un achat de services ?

**Réponse attendue** : poste et ratio confirmés.

**Impact estimé** : 364,84 k€ × 150 ≈ 54,7 tCO₂e ; ×300 ≈ 109,5 tCO₂e.

**Traitement proposé** : constat d'alerte, mapping à valider.

**Statut** : À confirmer.

## 3. Contrôles positifs

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
| VAC-01 | fraîcheur | bloquant | certain | à confirmer | aucun | 110,12 tCO₂e est. | Décembre manquant sur les 3 sites |
| VAC-02 | cohérence entre sources | alerte | à confirmer | à confirmer | aucun | 120,42 tCO₂e / 26 245,19 € est. | Écart entre l'électricité et le FEC 6061100 |
| VAC-03 | conformité format | bloquant | certain | à confirmer | mappé | 65,73 tCO₂e compté | Dérive de schéma carburant S1 / S2 |
| VAC-04 | unicité | bloquant | certain | à confirmer | exclu | 3,44 tCO₂e / 3 149,98 € non compté | Billets dupliqués |
| VAC-05 | validité | info | certain | à confirmer | exclu | 4,23 tCO₂e / 2 964,53 € non compté | Billets annulés |
| VAC-06 | intégrité référentielle | alerte | certain | à confirmer | aucun | n.c. | Cartes carburant sans véhicule |
| VAC-07 | conformité format | bloquant | à confirmer | à confirmer | aucun | n.c. | FEC supposé HT |
| VAC-08 | conformité format | alerte | à confirmer | à confirmer | conservé | 10,57 tCO₂e exposé | Aller simple / aller-retour à confirmer |
| VAC-09 | intégrité référentielle | alerte | à confirmer | à confirmer | conservé | 2 356,44 tCO₂e exposé | Mappings 6011000 et 6022000 à confirmer |
| VAC-10 | conformité format | info | certain | à confirmer | exclu | 14 000,00 € non compté | CET en classe 6 mais hors périmètre |
| VAC-11 | intégrité référentielle | alerte | à confirmer | à confirmer | conservé | 54,73 tCO₂e exposé | Publicité et commissions plateformes |
| VAC-12 | validité | alerte | à confirmer | ouvert | conservé | −14,98 tCO₂e / −16 640,52 € compté | Avoirs sur achats alimentaires |

### Chiffres recomputés

- **VAC-01** : 3 sites × 11 mois, décembre manquant. La moyenne mensuelle de
  141 175 kWh représente 110,12 tCO₂e estimés.
- **VAC-02** : l'écart avec le FEC `6061100` est de 26 245,19 €, soit
  120,42 tCO₂e estimés. L'écart est cohérent avec décembre manquant, sans être
  prouvé.
- **VAC-03** : S1 = 182 lignes / 10 625,61 L ; S2 = 185 lignes / 10 576,32 L.
  Total : 367 lignes, 21 201,93 L et 65,73 tCO₂e comptés.
- **VAC-04** : 2 billets dupliqués, 3 149,98 € TTC et 3,44 tCO₂e non comptés.
- **VAC-05** : 3 billets annulés, 2 964,53 € TTC et 4,23 tCO₂e non comptés.
- **VAC-06** : 5 cartes sans identifiant véhicule.
- **VAC-09** : 27 lignes, 2 684 154,36 € HT et 2 356,44 tCO₂e exposés.
- **VAC-11** : 12 lignes, 364 841,57 € HT et 54,73 tCO₂e exposés. À
  300 kgCO₂e/k€, l'impact serait d'environ 109,5 tCO₂e.
- **VAC-12** : 3 lignes négatives sur `6011000`, −16 640,52 € HT et
  −14,98 tCO₂e comptés.

### Nouveau constat issu des contrôles

**VAC-12** — trois avoirs sur achats alimentaires sont conservés dans le calcul
monétaire. Ils réduisent le scope 3 de 14,98 tCO₂e. La question métier est de
savoir s'il s'agit de notes de crédit légitimes ou d'une erreur d'export.

### Impacts partagés

`VAC-01` et `VAC-02` partagent le groupe `VAC-ELEC-GAP` : les deux estimations
décembre manquant et écart FEC décrivent le même problème. Elles ne sont pas
additives ; la synthèse retient 120,42 tCO₂e.
