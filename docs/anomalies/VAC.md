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
