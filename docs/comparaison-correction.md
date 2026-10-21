# Rapport final — implémentation vs retour métier

> Données fictives. `docs/CORRECTION.md` joue le rôle d'un **retour métier simulé**.
> Il est versionné avec ce rapport ; il a été ouvert après l'écriture des
> contrôles, conformément à la démarche.
>
> Référence : commit `775744f`, `dbt build` PASS=303, 42 constats.
> Dernière vérification : 2026-10-21.

## 1. Objet et méthode

Le pipeline produit **42 constats**. Le retour métier décrit **16 anomalies
réellement présentes** dans les fichiers. Ce rapport répond à trois questions :

1. **Qu'est-ce que les outils data ont détecté seuls ?**
2. **Qu'est-ce qui relève de la qualification ou de la décision métier ?**
3. **Qu'est-ce que le pipeline a fait de la réponse métier ?**

La comparaison distingue trois niveaux :

| Niveau | Question | Exemple |
|---|---|---|
| **Détection outillée** | Un contrôle data peut-il voir le signal ? | doublon, unité, schéma, code inconnu |
| **Qualification métier** | Est-ce une anomalie ou un cas normal ? | avoir légitime, B7 = gazole |
| **Décision métier** | Que fait-on ? | exclure, convertir, estimer, conserver |

Un outil peut détecter un **symptôme** sans pouvoir décider de son **sens**. C'est
la différence centrale entre « trouvé » et « intégré ».

### 1.1 Types d'impact

Les impacts du registre ne sont pas additifs et ne veulent pas tous dire la même
chose :

| Type | Sens |
|---|---|
| `compte` | Déjà inclus dans le bilan ; le chiffre est le montant concerné, pas une erreur supplémentaire. |
| `non_compte` | Exclu du bilan ; le chiffre est ce qui aurait été compté. |
| `estimation` | Manque chiffré avec un repère documenté ; non ajouté au bilan. |
| `exposition` | Montant en jeu si la règle métier change ; pas une émission supplémentaire. |
| `non_calculable` | Impossible à chiffrer sans information complémentaire. |

## 2. Scorecard

| Critère | Résultat |
|---|---:|
| Anomalies du retour métier | **16** |
| Anomalies détectées | **16/16** |
| Anomalies non détectées | **0** |
| Constats produits | **42** |
| Constats couvrant le retour métier | **21** |
| Constats hors retour métier | **21** |
| Anomalies éclatées en plusieurs constats | **4** (A04, A06, A12, A16) |
| Constats bloquants | **13** |
| Constats en alerte | **21** |
| Constats en info | **8** |
| Constats `à confirmer` | **38** |
| Constats `ouverts` | **4** |
| Constats `repondu` / `integre` / `ecarte` | **0** |

Le pipeline a donc trouvé **tous les signaux**, mais n'a pas encore fermé la
boucle métier : aucune réponse du retour métier n'est enregistrée comme
`repondu` ou `integre`.

## 3. Détection data vs qualification métier

### 3.1 La chaîne de détection

| Couche | Ce qu'elle voit | Exemples |
|---|---|---|
| Ingestion / configuration | format, encodage, délimiteur, schéma, types, unités | A01, A08 |
| Staging | doublons exacts, statuts, montants négatifs, jointures référentielles | A02, A11, A13, A14, A15 |
| Intermediate | règles de calcul : estimation carburant, mapping FEC, distance avion | A06, A07, A10 |
| Qualité / croisement | complétude, cohérence interne, écarts entre sources, valeurs aberrantes | A03, A04, A05, A09, A12, A16 |

### 3.2 Ce que les outils data peuvent voir seuls

- conformité du format, encodage, délimiteur, en-têtes ;
- dérive de schéma entre deux fichiers ;
- hétérogénéité des unités ;
- doublons exacts ou fonctionnels ;
- complétude : mois, sites, quantités, destinations ;
- valeurs négatives ou aberrantes ;
- codes absents d'un référentiel ;
- écriture comptable déséquilibrée ;
- écarts entre une source physique et le FEC ;
- volumes et ordres de grandeur.

### 3.3 Ce qui reste métier

- décider si un doublon est une erreur d'export ou deux factures réelles ;
- confirmer qu'une feuille est bien en MWh et non en kWh ;
- savoir qu'AdBlue n'est pas un carburant ;
- savoir que B7, GO et Diesel sont des synonymes de gazole ;
- comprendre qu'un montant négatif sur un compte d'achats est un avoir légitime ;
- interpréter un plein de 400 L dans un réservoir de 300 L ;
- expliquer qu'un site manque à l'export mais existe en comptabilité ;
- accepter ou refuser une estimation par les prix ;
- choisir un poste et un ratio pour un compte non mappé ;
- choisir le PRG d'un fluide inconnu ;
- décider du périmètre de la CET, de la classe Affaires ou des hôtels/taxis.

### 3.4 Matrice A01 → A16

| Id | Anomalie | Détection data engineering | Qualification / décision métier |
|---|---|---|---|
| A01 | Unités MWh/kWh | **Oui** — unité par feuille, ordre de grandeur | Confirmer l'unité, valider la conversion |
| A02 | Facture en double | **Oui** — doublon exact : n° facture, site, mois, montant | Confirmer que c'est un doublon d'export |
| A03 | Décembre manquant | **Oui** — complétude 11/12 mois × 3 sites | Confirmer l'absence, demander les factures, bilan provisoire |
| A04 | Estimé + régularisation | **Partiel** — flag « Estimé », valeur négative | Comprendre le couple estimation/régularisation, décider de conserver |
| A05 | 400 L > réservoir 300 L | **Partiel** — outlier ; exact avec le parc véhicule | Confirmer erreur de saisie ou fraude, demander au client |
| A06 | Produit inconnu | **Oui** — libellé hors référentiel | Dire ce qu'est « PRODUIT 47 », qu'AdBlue est hors carburant, que B7/GO/Diesel sont du gazole |
| A07 | Carburant sans litres | **Oui** — colonne quantité absente | Choisir et valider l'estimation par les prix |
| A08 | Schéma S1/S2 | **Oui** — comparaison des en-têtes | Confirmer l'alias, valider le mapping |
| A09 | Écriture déséquilibrée | **Oui** — débit ≠ crédit | Demander un nouvel export, décider du traitement |
| A10 | Compte 6288000 non mappé | **Oui** — compte hors table de correspondance | Choisir le poste et le ratio |
| A11 | Avoirs fournisseurs | **Oui pour le négatif, non pour le sens** | Comprendre que c'est un avoir, décider de calculer net et de garder |
| A12 | Fluide inconnu | **Oui** — code vide ou hors référentiel | Obtenir le rapport frigoriste, choisir un PRG |
| A13 | Billets annulés | **Oui** — statut « Annulé » | Confirmer la fiabilité du statut, décider l'exclusion |
| A14 | Billets en double | **Oui** — doublon exact : n° billet | Confirmer le doublon, garder une occurrence |
| A15 | Destination vide | **Oui** — destination vide / IATA inconnu | Obtenir le détail de l'agence |
| A16 | Site absent | **Oui pour la liste des sites ; partiel pour le FEC** | Comprendre que le FEC couvre le site manquant, demander l'export |

### 3.5 Synthèse « trouvable sans le métier ? »

| Réponse du retour métier | Anomalies | Nombre |
|---|---|---:|
| Oui | A01, A02, A03, A06, A07, A08, A09, A10, A12, A13, A14, A15 | 12 |
| En partie | A04, A05, A16 | 3 |
| Non | A11 | 1 |

Nuance importante : « trouvable » ne veut pas dire « décidable ». A06, A07, A10,
A12 et A15 sont détectables par un outil, mais leur traitement reste une décision
métier.

## 4. Correspondance A01 → A16

| Id | Constat(s) actuel(s) | Traitement | Sévérité / statut | Impact | Écart avec le retour métier |
|---|---|---|---|---|---|
| A01 | `FAN-01` | converti | bloquant / à confirmer | 568,086 tCO₂e `compte` | Conversion correcte ; confirmation de l'unité encore ouverte. |
| A02 | `KAY-02` | exclu | bloquant / à confirmer | 24,753 tCO₂e `non_compte` | Conforme (≈ 25 attendu). |
| A03 | `VAC-01` (+ `VAC-02`) | aucun | bloquant / à confirmer | 110,117 `estimation` ; 120,419 pour `VAC-02` | Décembre manquant bien vu ; le bilan n'est pas affiché comme provisoire. |
| A04 | `KAY-03` + `KAY-04` | conserve | alerte / à confirmer | -9,166 et 39,718 `compte` | Les deux lignes sont conservées ; le lien « régularisation corrige avril » n'est pas explicite. |
| A05 | `KAY-16` | aucun | alerte / ouvert | 0,31 tCO₂e `exposition` | Ligne conservée ; conforme. |
| A06 | `KAY-05` + `KAY-06` + `KAY-07` | conserve / exclu / exclu | alerte, info, alerte / à confirmer | 1 642,647 `exposition` ; 25,544 `non_compte` ; `non_calculable` | PRODUIT 47 : 1 615,46 L non valorisés. AdBlue exclu. B7/GO/Diesel encore à confirmer alors que le retour métier dit que ce sont des synonymes de gazole. |
| A07 | `FAN-02` | estimé | bloquant / à confirmer | 94,042 tCO₂e `compte` | Estimation correcte, mais sévérité trop forte : le retour métier parle d'une info à signaler. |
| A08 | `VAC-03` | mappé | bloquant / à confirmer | 65,726 tCO₂e `compte` | Alias S1/S2 correctement mappé ; conforme. |
| A09 | `FAN-06` | aucun | bloquant / à confirmer | 0,09 tCO₂e `exposition` | 150 € détectés ; conforme. |
| A10 | `KAY-10` | exclu | bloquant / à confirmer | exposition 62,8–261,6 tCO₂e | 523 298,66 € exclus ; conforme. |
| A11 | `VAC-12` | conserve | alerte / ouvert | -14,976 tCO₂e `compte` | Les avoirs sont bien inclus nets, mais le statut devrait être info/intégré, pas alerte/ouvert. |
| A12 | `FAN-04` + `FAN-05` | exclu | alerte / à confirmer | `non_calculable` | 10,5 kg exclus ; le retour métier donne plus de 40 tCO₂e, le pipeline ne chiffre pas. |
| A13 | `VAC-05` | exclu | info / à confirmer | 4,229 tCO₂e `non_compte` | Exclusion correcte ; statut à intégrer. |
| A14 | `VAC-04` | exclu | bloquant / à confirmer | 3,437 tCO₂e `non_compte` | Conforme. |
| A15 | `KAY-11` | exclu | alerte / à confirmer | `non_calculable` | 1 billet, 1 090,80 € ; le retour métier donne ≈ 2 tCO₂e, non chiffré. |
| A16 | `KAY-01` + `KAY-09` | aucun | bloquant / à confirmer | 185,027 tCO₂e `estimation` | 185,027 contre ≈ 210 dans le retour métier ; écart FEC de 40 326,43 € ; même `impact_group`. |

## 5. Les 21 constats hors retour métier

### 5.1 Répartition

| Famille | Constats | Nombre |
|---|---|---:|
| Hypothèses / questions méthodologiques | `FAN-07`, `FAN-08`, `FAN-11`, `FAN-12`, `FAN-13`, `KAY-12`, `KAY-14`, `KAY-15`, `VAC-07`, `VAC-08`, `VAC-09`, `VAC-10`, `VAC-11`, `GEN-01` | 14 |
| Complétude référentielle | `FAN-03`, `FAN-10`, `KAY-13`, `VAC-06` | 4 |
| Écarts entre sources | `FAN-09`, `KAY-08`, `VAC-02` | 3 |

### 5.2 Détail et proposition

| Constat | Titre | Nature | Proposition |
|---|---|---|---|
| `GEN-01` | Classe Affaires au facteur standard | Méthode / facteur | `à confirmer` ; chiffrer si un facteur Affaires est validé. |
| `FAN-03` | Cartes carburant sans référentiel véhicule | Complétude | `à confirmer` ; demander le parc, sinon `ecarte` si FAN ne le fournit pas. |
| `FAN-07` | Mappings 6011000 et 6021000 à confirmer | Méthode / mapping | `à confirmer` ; exposition majeure (4 756,837 tCO₂e). |
| `FAN-08` | CET en classe 6 mais hors périmètre | Méthode / périmètre | `ecarte` ou info si le hors-périmètre est confirmé. |
| `FAN-09` | Écart électricité / FEC 6061100 | Croisement | `à confirmer` ; 1,67 tCO₂e, probable arrondi ou périmètre. |
| `FAN-10` | Aucune intervention frigoriste sur SPI-ADM | Complétude | `à confirmer` ; une absence de recharge peut être normale. |
| `FAN-11` | FEC supposé HT | Méthode | `à confirmer` ; ne pas laisser bloquant si le HT est confirmé. |
| `FAN-12` | Aller simple / aller-retour à confirmer | Méthode | `à confirmer` ; 4,481 tCO₂e exposés. |
| `FAN-13` | Hôtels, taxis et repas en méthode monétaire | Méthode / mapping | `à confirmer` ; 14,179 tCO₂e déjà comptés. |
| `KAY-08` | Écart carburant / FEC 6062200 | Croisement | `à confirmer` ; 4,615 tCO₂e. |
| `KAY-12` | Aller simple / aller-retour à confirmer | Méthode | `à confirmer` ; 5,835 tCO₂e exposés. |
| `KAY-13` | Aucune intervention frigoriste sur LPT-SIE et LPT-ATL | Complétude | `à confirmer` ; peut être normal. |
| `KAY-14` | FEC supposé HT | Méthode | `à confirmer` ; ne pas laisser bloquant si le HT est confirmé. |
| `KAY-15` | CET en classe 6 mais hors périmètre | Méthode / périmètre | `ecarte` ou info si confirmé. |
| `VAC-02` | Écart électricité / FEC 6061100 | Croisement | `à confirmer` ; 120,419 tCO₂e, cohérent avec décembre manquant. |
| `VAC-06` | Cartes carburant sans véhicule | Complétude | `à confirmer` ; demander le parc, sinon `ecarte`. |
| `VAC-07` | FEC supposé HT | Méthode | `à confirmer` ; ne pas laisser bloquant si le HT est confirmé. |
| `VAC-08` | Aller simple / aller-retour à confirmer | Méthode | `à confirmer` ; 10,568 tCO₂e exposés. |
| `VAC-09` | Mappings 6011000 et 6022000 à confirmer | Méthode / mapping | `à confirmer` ; exposition majeure (2 356,439 tCO₂e). |
| `VAC-10` | CET en classe 6 mais hors périmètre | Méthode / périmètre | `ecarte` ou info si confirmé. |
| `VAC-11` | Publicité et commissions plateformes | Méthode / mapping | `à confirmer` ; 54,726 tCO₂e exposés. |

Ces constats ne sont pas forcément faux. Ils sont hors du périmètre des 16
anomalies du retour métier. Certains sont de vraies questions, d'autres des
hypothèses méthodologiques. Le rapport ne les corrige pas : il propose de les
qualifier.

## 6. Écarts de sévérité, de statut et de chiffrage

### 6.1 Sévérité

Le pipeline compte **13 bloquants** :

- **10** couvrent le retour métier ;
- **3** sont la même hypothèse « FEC supposé HT » (`FAN-11`, `KAY-14`, `VAC-07`),
  absente du retour métier.

Deux écarts notables :

- **`FAN-02` (A07)** : bloquant alors que le retour métier présente l'estimation
  par les prix comme une méthode à documenter et une info à signaler.
- **`VAC-12` (A11)** : alerte/ouvert alors que le retour métier demande un calcul
  net et une info.

### 6.2 Statut

```text
38 constats : à confirmer
 4 constats : ouverts
 0 constat  : répondu
 0 constat  : intégré
 0 constat  : écarté
```

Le retour métier donne pourtant des décisions exploitables :

| Constat | Décision métier | Statut actuel | Statut cible proposé |
|---|---|---|---|
| `KAY-05` (A06) | B7/GO/Diesel = gazole | à confirmer | `integre` |
| `FAN-02` (A07) | estimation documentée | à confirmer | `repondu` |
| `VAC-12` (A11) | avoirs nets, info | ouvert | `integre` |
| `VAC-05` (A13) | billets annulés exclus | à confirmer | `integre` |
| `KAY-02` (A02) | garder une occurrence | à confirmer | `integre` |
| `VAC-04` (A14) | garder une occurrence | à confirmer | `integre` |
| `KAY-01`/`KAY-09` (A16) | demander l'export | à confirmer | `a_confirmer` (bloquant) |
| `VAC-01` (A03) | demander décembre | à confirmer | `a_confirmer` (bloquant) |

### 6.3 Chiffrage

| Anomalie | Retour métier | Pipeline actuel | Calcul possible |
|---|---|---|---|
| A12 FAN fluides | ≈ 10 kg, plus de 40 tCO₂e | `non_calculable` | Avec R404A (PRG 3 922) : 10,5 kg → **41,2 tCO₂e** |
| A15 KAY vol sans destination | ≈ 2 tCO₂e | `non_calculable` | Distance métropole + facteur avion |
| A06 KAY PRODUIT 47 | ≈ 1 600 L | 1 615,46 L, `non_calculable` | Au facteur gazole : **≈ 5,0 tCO₂e** |
| A16 KAY site absent | ≈ 210 tCO₂e | **185,027 tCO₂e** | Écart FEC 40 326,43 € ; ordre de grandeur cohérent (≈ 30 % de l'électricité) |

Pour A16, l'écart 185 vs 210 (≈ 12 %) s'explique probablement par l'arrondi du
retour métier et par la méthode d'estimation (écart FEC / prix moyen / facteur).

## 7. Lecture du dashboard

- **42 constats ne veulent pas dire 42 anomalies.** Le retour métier en retient 16.
- Les totaux d'impact de `quality_summary` sont dominés par des constats hors
  retour métier ou sur-interprétés :

| Entreprise | Impact total | Constat dominant | Part |
|---|---:|---|---:|
| FAN | 5 439,4 tCO₂e | `FAN-07` : 4 756,8 | **87,5 %** |
| KAY | 1 919,3 tCO₂e | `KAY-05` : 1 642,6 | **85,6 %** |
| VAC | 2 600,6 tCO₂e | `VAC-09` : 2 356,4 | **90,6 %** |

Ces montants sont des **expositions**, pas des émissions non comptées. Ils ne
doivent pas être lus comme « les anomalies du retour métier pèsent 5 439 tCO₂e ».

- Le retour métier dit que **le bilan VAC est provisoire** à cause de décembre
  manquant. Le dashboard affiche un total VAC de 4 242,278 tCO₂e sans bandeau
  « provisoire ».
- Les **13 bloquants** incluent 3 hypothèses « FEC HT » qui ne sont pas des
  anomalies du retour métier. Le chiffre de 13 est donc plus large que le nombre
  de bloquants réellement confirmés.

## 8. Décisions proposées

Le rapport ne modifie pas le registre. Il propose un plan en quatre lots.

### 8.1 Intégrer les décisions métier

- `KAY-05` : B7/GO/Diesel = gazole → `integre`, info.
- `FAN-02` : estimation par les prix validée → `repondu`, info/alerte.
- `VAC-12` : avoirs nets → `integre`, info.
- `VAC-05` : billets annulés → `integre`, info.
- `KAY-02`, `VAC-04` : doublons → `integre`.
- `FAN-01`, `VAC-03` : conversion/mapping → `integre`.

### 8.2 Requalifier les constats sur-interprétés

- `KAY-05` : ne plus exposer 1 642,647 tCO₂e si les libellés sont confirmés.
- `FAN-02` : passer de bloquant à info/alerte.
- `VAC-12` : passer de alerte/ouvert à info/intégré.
- Les trois « FEC supposé HT » : ne pas les laisser bloquants sans confirmation.

### 8.3 Chiffrer les impacts manquants

- A12 : 10,5 kg × PRG de référence → ≈ 41,2 tCO₂e.
- A15 : distance typique + facteur avion → ≈ 2 tCO₂e.
- A06 PRODUIT 47 : 1 615,46 L × facteur gazole → ≈ 5,0 tCO₂e.

### 8.4 Qualifier les 21 constats hors retour métier

Décider, pour chacun, entre :

- **conserver** comme question métier ;
- **requalifier** en info ;
- **écarter** comme faux positif documenté ;
- **fusionner** avec un constat existant.

## 9. Preuves et reproductibilité

```bash
make all          # PASS=303, 28 modèles, 275 tests, 42 constats
uv run pytest     # 72 passed
```

Les chiffres de ce rapport viennent de :

- `analytics.quality_constats` : 42 constats, sévérité, statut, impact ;
- `analytics.quality_summary` : compteurs et impacts par entreprise ;
- `analytics.fct_exclusions` : lignes écartées et motifs ;
- `analytics.mart_beges` : bilan par entreprise, scope, poste et méthode ;
- `docs/CORRECTION.md` : retour métier simulé, versionné.

Le commit de référence est `775744f`. `docs/CORRECTION.md` est versionné dans le
dépôt public : il ne contient que des données fictives, aucun secret.

## 10. Limites

- Données fictives ; le retour métier est simulé, pas un audit réel.
- Le rapprochement anomalie ↔ constat est manuel ; certains constats couvrent
  plusieurs anomalies et inversement.
- Les impacts ne sont pas additifs : `compte`, `non_compte`, `estimation` et
  `exposition` ne mesurent pas la même chose.
- Les 21 constats hors retour métier ne sont pas nécessairement des faux
  positifs : certains sont de vraies questions, d'autres des hypothèses.
- Les décisions proposées n'ont pas été appliquées aux YAML ; elles doivent être
  validées avant de modifier le registre.

## Annexe A — « Trouvé seul ? »

| Id | Trouvé seul ? | Commentaire |
|---|---|---|
| A01 | Oui | Unités détectées et converties. |
| A02 | Oui | Doublon exact exclu. |
| A03 | Oui | 11/12 mois détectés. |
| A04 | Oui | Deux flags séparés ; lien non explicite. |
| A05 | Oui | Capacité du réservoir croisée avec le parc. |
| A06 | Oui | Trois constats : PRODUIT 47, AdBlue, B7/GO/Diesel. |
| A07 | Oui | Estimation par les prix. |
| A08 | Oui | Dérive de schéma mappée. |
| A09 | Oui | Débit ≠ crédit, 150 €. |
| A10 | Oui | Compte 6288000 exclu et listé. |
| A11 | Oui, via contrôle générique | Montants négatifs détectés ; qualification métier encore nécessaire. |
| A12 | Oui | Deux recharges sans fluide exploitable. |
| A13 | Oui | Statut « Annulé » exclu. |
| A14 | Oui | Doublons de billets exclus. |
| A15 | Oui | Destination vide détectée. |
| A16 | Oui | Site absent + écart FEC. |

## Annexe B — Constats mappés et constats hors retour métier

**Mappés (21)** : `FAN-01`, `FAN-02`, `FAN-04`, `FAN-05`, `FAN-06`, `KAY-01`,
`KAY-02`, `KAY-03`, `KAY-04`, `KAY-05`, `KAY-06`, `KAY-07`, `KAY-09`, `KAY-10`,
`KAY-11`, `KAY-16`, `VAC-01`, `VAC-03`, `VAC-04`, `VAC-05`, `VAC-12`.

**Hors retour métier (21)** : `GEN-01`, `FAN-03`, `FAN-07`, `FAN-08`, `FAN-09`,
`FAN-10`, `FAN-11`, `FAN-12`, `FAN-13`, `KAY-08`, `KAY-12`, `KAY-13`, `KAY-14`,
`KAY-15`, `VAC-02`, `VAC-06`, `VAC-07`, `VAC-08`, `VAC-09`, `VAC-10`, `VAC-11`.

## Conclusion

Le pipeline est solide sur la **détection outillée** : 16/16 anomalies trouvées,
y compris A11 que le retour métier classait « non trouvable sans le métier ».
Ses faiblesses sont ailleurs :

- il produit **21 constats de plus** que le retour métier ;
- il **sur-interprète** certains signaux (`KAY-05`, `FAN-02`, `VAC-12`) ;
- il **ne chiffre pas** certains impacts (A12, A15, A06 PRODUIT 47) ;
- il **n'intègre pas** les décisions métier : 0 constat `repondu`/`integre`.

La prochaine étape n'est donc pas d'ajouter des contrôles, mais de **fermer la
boucle** : qualifier les 21 constats hors retour métier, requalifier les constats
sur-interprétés, chiffrer les impacts manquants et enregistrer les décisions
métier dans le registre.
