# Anomalies et questions métier — FAN

> Fanjan Agro SA. Les schémas sont dans `../dictionnaire-donnees/FAN.md`.

## 1. Résumé

| ID | Source | Constat | Sévérité | Certitude | Question métier | Impact | Statut |
|---|---|---|---|---|---|---|---|
| FAN-01 | Électricité | `PIE-FRO` en MWh, les autres feuilles en kWh | Bloquant | Certain | La feuille `PIE-FRO` est-elle bien en MWh, à convertir en kWh (×1000) ? | Sous-estimation ×1000 si non converti | À confirmer |
| FAN-02 | Carburant | Aucune quantité en litres | Bloquant | Certain | Pouvez-vous fournir les litres, ou confirmez-vous l'estimation via les prix repères ? | Méthode physique impossible sans estimation | À confirmer |
| FAN-03 | Carburant | 12 cartes / 12 véhicules, aucun référentiel parc | Alerte | Certain | Pouvez-vous fournir le parc et l'affectation carte/véhicule ? | Intégrité des véhicules non vérifiable | À confirmer |
| FAN-04 | Fluides | Une ligne sans code fluide | Alerte | Certain | Quel fluide a été rechargé sur cette intervention ? | PRG non calculable | À confirmer |
| FAN-05 | Fluides | Un code `R-?` | Alerte | Certain | Que signifie `R-?` et quel fluide est concerné ? | PRG non calculable | À confirmer |
| FAN-06 | FEC | `AC000042` déséquilibrée de 150,00 € | Bloquant | Certain | L'écriture est-elle déséquilibrée dans l'export, ou manque-t-il une ligne de 150,00 € ? | Bilan potentiellement faux | À confirmer |
| FAN-07 | FEC | `6011000` et `6021000` à mapper | Alerte | Certain | Confirmez-vous `6011000` → matières premières (900) et `6021000` → emballages (600) ? | Poste ou ratio erroné | À confirmer |
| FAN-08 | FEC | `6351100` CET en classe 6 mais hors périmètre | Info | Certain | Confirmez-vous l'exclusion de la CET du bilan carbone ? | Double comptage possible | À confirmer |
| FAN-09 | Électricité / FEC | Écart de 363,91 € avec `6061100` | Alerte | À confirmer | Une facture manque-t-elle, ou est-ce un arrondi ? | Bilan sous-estimé | À confirmer |
| FAN-10 | Fluides | Aucune intervention sur `SPI-ADM` | Info | À confirmer | Est-ce normal (pas d'équipement frigorifique) ? | Complétude scope 1 | À confirmer |
| FAN-11 | FEC | Montants supposés HT | Bloquant | À confirmer | Les montants du FEC sont-ils bien HT ? | Confusion HT/TTC | À confirmer |
| FAN-12 | Vols | `AR` / `AS` | Alerte | À confirmer | `AS` signifie-t-il bien aller simple ? | Doublement ou omission | À confirmer |
| FAN-13 | FEC | `62512000` sans source physique | Info | Certain | Confirmez-vous la méthode monétaire pour hôtels/taxis/repas ? | Périmètre scope 3 | À confirmer |

## 2. Détail

### FAN-01 — Unité MWh sur PIE-FRO

**Constat** : la feuille `PIE-FRO` du classeur Excel est exprimée en MWh, alors que
`SPI-USI` et `SPI-ADM` sont en kWh.

**Preuve** : feuille `PIE-FRO`, lignes 5 à 16, colonne `Unité` = `MWh` ;
exemple ligne 5 : `01/2025`, `71.589`, `MWh`, `12170.13`.

**Pourquoi c'est important** : sans conversion, la consommation de `PIE-FRO` est
sous-estimée d'un facteur 1000, donc le scope 2 est faux.

**Question au métier** : confirmez-vous que `PIE-FRO` est bien en MWh et qu'il faut
multiplier par 1000 pour obtenir des kWh ?

**Réponse attendue** : oui/non, avec confirmation de l'unité.

**Impact estimé** : 728 316 kWh après conversion, soit environ 568 tCO₂e avec le facteur
0,780 kgCO₂e/kWh. À recalculer après validation.

**Traitement proposé** : convertir en kWh, tracer `source_file` et `source_row`,
et ajouter un contrôle d'unité.

**Statut** : À confirmer.

### FAN-06 — Écriture AC000042 déséquilibrée

**Constat** : l'écriture `AC000042` présente un débit total de 20 018,25 € et un crédit
de 19 868,25 €, soit un écart de 150,00 €.

**Preuve** : FEC FAN, `EcritureNum = AC000042` :
- `6021000` achats emballages : débit 18 450,00 €
- `4456600` TVA déductible : débit 1 568,25 €
- `4010000` fournisseurs : crédit 19 868,25 €

**Pourquoi c'est important** : une écriture déséquilibrée peut signifier une ligne
manquante ou un montant faux ; le ratio monétaire et le bilan peuvent être impactés.

**Question au métier** : l'écriture est-elle déséquilibrée dans l'export, ou manque-t-il
une ligne de 150,00 € (par exemple une remise, un port ou une TVA) ?

**Réponse attendue** : montant manquant ou confirmation que l'écriture est à corriger.

**Impact estimé** : 150,00 € × ratio `6021` (600 kgCO₂e/k€) ≈ 0,09 tCO₂e.
À confirmer.

**Traitement proposé** : signaler en bloquant, ne pas corriger automatiquement.

**Statut** : À confirmer.

### FAN-02 — Carburant sans litres

**Constat** : le fichier carburant ne contient que `montant_ttc`, sans quantité.

**Preuve** : colonnes `date`, `carte`, `vehicule`, `produit`, `montant_ttc` ;
623 lignes, aucun champ litre.

**Pourquoi c'est important** : la méthode physique a besoin de litres ; sans litres,
on doit estimer ou basculer en méthode monétaire.

**Question au métier** : pouvez-vous fournir les volumes en litres, ou confirmez-vous
l'estimation à partir des montants TTC et des prix repères (gazole 1,46 €/L,
SP95 1,72 €/L) ?

**Réponse attendue** : litres fournis, ou validation de l'estimation, ou choix du monétaire.

**Impact estimé** : 47 357,52 € TTC, soit 43 647,48 € HT ; l'impact dépend de la méthode.

**Traitement proposé** : si pas de litres, estimer et marquer `physique_estimée`.

**Statut** : À confirmer.

### FAN-04 et FAN-05 — Fluides inconnus

**Constat** : une intervention n'a pas de code fluide, une autre utilise `R-?`.

**Preuve** : fichier fluides, colonne `Fluide` ; 17 lignes, 1 vide, 1 `R-?`.

**Pourquoi c'est important** : sans code fluide, le PRG n'est pas calculable.

**Question au métier** : quel fluide a été rechargé sur ces deux interventions ?

**Réponse attendue** : code F-gas (R404A, R449A, etc.) ou confirmation d'exclusion.

**Impact estimé** : non calculable sans le PRG.

**Traitement proposé** : signaler, ne pas deviner.

**Statut** : À confirmer.

### FAN-09 — Écart électricité / FEC

**Constat** : l'export électricité totalise 424 311,33 € HT, le compte `6061100`
totalise 423 947,42 €, soit un écart de 363,91 €.

**Preuve** : somme des 36 lignes Excel vs somme des débits `6061100` du FEC.

**Pourquoi c'est important** : un écart peut signifier une facture manquante ou un arrondi.

**Question au métier** : l'écart de 363,91 € correspond-il à une facture manquante,
à un arrondi ou à un autre périmètre ?

**Réponse attendue** : explication ou facture complémentaire.

**Impact estimé** : 363,91 € × ratio `60611` ou facteur physique, à recalculer.

**Traitement proposé** : constat d'alerte, pas de correction silencieuse.

**Statut** : À confirmer.

## 3. Contrôles positifs

| Contrôle | Résultat |
|---|---|
| Électricité : 12 mois sur les 3 sites | OK |
| Vols : total TTC = FEC `6251100` | OK, écart 0,00 € |
| Carburant : total HT = FEC `6062200` | OK, écart 0,00 € |
| Vols : aucun annulé, aucun doublon | OK |
| Fluides : recharge ≤ charge nominale | OK |
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
| FAN-01 | unités | bloquant | certain | à confirmer | converti | 568,09 tCO₂e compté | Feuille PIE-FRO exprimée en MWh |
| FAN-02 | complétude | bloquant | certain | à confirmer | estimé | 94,04 tCO₂e compté | Carburant sans volumes en litres |
| FAN-03 | intégrité référentielle | alerte | certain | à confirmer | aucun | n.c. | Cartes carburant sans référentiel véhicule |
| FAN-04 | validité | alerte | certain | à confirmer | exclu | n.c. | Intervention frigoriste sans code fluide |
| FAN-05 | validité | alerte | certain | à confirmer | exclu | n.c. | Code fluide R-? inconnu |
| FAN-06 | cohérence interne | bloquant | certain | à confirmer | aucun | 0,09 tCO₂e / 150,00 € exposé | Écriture AC000042 déséquilibrée |
| FAN-07 | intégrité référentielle | alerte | à confirmer | à confirmer | conservé | 4 756,84 tCO₂e exposé | Mappings 6011000 et 6021000 à confirmer |
| FAN-08 | conformité format | info | certain | à confirmer | exclu | 14 000,00 € non compté | CET en classe 6 mais hors périmètre |
| FAN-09 | cohérence entre sources | alerte | à confirmer | à confirmer | aucun | 1,67 tCO₂e / 363,91 € est. | Écart entre l'électricité et le FEC 6061100 |
| FAN-10 | complétude | info | à confirmer | à confirmer | aucun | n.c. | Aucune intervention frigoriste sur SPI-ADM |
| FAN-11 | conformité format | bloquant | à confirmer | à confirmer | aucun | n.c. | FEC supposé HT |
| FAN-12 | conformité format | alerte | à confirmer | à confirmer | conservé | 4,48 tCO₂e exposé | Aller simple / aller-retour à confirmer |
| FAN-13 | intégrité référentielle | info | à confirmer | à confirmer | conservé | 14,18 tCO₂e compté | Hôtels, taxis et repas en méthode monétaire |

### Chiffres recomputés

- **FAN-01** : 12 lignes, 728 316 kWh après conversion, 123 813,72 € HT et
  568,09 tCO₂e comptés. La conversion MWh → kWh est appliquée et tracée.
- **FAN-02** : 623 lignes, 31 075,64 L estimés, 43 647,48 € HT et 94,04 tCO₂e.
- **FAN-03** : 12 cartes et 12 véhicules sans référentiel de parc.
- **FAN-06** : 3 lignes d'écriture, 150,00 € d'écart et 0,09 tCO₂e exposé.
- **FAN-07** : 25 lignes, 5 538 974,57 € HT et 4 756,84 tCO₂e exposés.
- **FAN-09** : le FEC est inférieur de **363,91 €** à l'export électricité ;
  l'écart absolu représente 1,67 tCO₂e estimé.
- **FAN-13** : 12 lignes, 47 263,53 € HT et 14,18 tCO₂e comptés.

### Point d'attention

`FAN-07` est le premier impact exposé du registre : 4 756,84 tCO₂e dépendent
des ratios `6011000 → 900` et `6021000 → 600`. Une erreur de mapping changerait
fortement le bilan. La question métier reste prioritaire.
