# Pipeline BEGES : cahier des charges

> Des fichiers clients en vrac → un bilan carbone fiable, avec une observabilité qui dit ce qui cloche.
>
> Ce document décrit **la mission**, **ce que le client a transmis**, **la méthodologie fournie par l'équipe RSE**
> (Responsabilité Sociétale des Entreprises) et **ce que le pipeline doit produire**.
> Il ne dit pas ce qui ne va pas dans les données : c'est au pipeline de le trouver.

[![CI](https://github.com/ultragenix/Pipeline-BEGES/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ultragenix/Pipeline-BEGES/actions/workflows/ci.yml)

**Démo en ligne :** <https://ultragenix.github.io/Pipeline-BEGES/>

## Démarrage rapide

Prérequis : Docker et Docker Compose.

```bash
docker compose up --build
# Site : http://localhost:8080
```

En local, avec [uv](https://docs.astral.sh/uv/) :

```bash
uv sync
make all
make status
```

L'image, la CI et la publication sont détaillées dans
[`docs/docker-ci.md`](docs/docker-ci.md). `make help` liste les commandes.

---

## 1. La mission

Trois entreprises réunionnaises doivent réaliser leur BEGES (Bilan d'Émissions de Gaz à Effet de Serre) sur l'exercice 2025.
En outre-mer, il est obligatoire au-delà de **250 salariés**, tous les 4 ans.

Les consultants RSE s'occupent de la méthodologie et de la restitution au client.
**Le rôle du data engineer :** transformer les fichiers transmis par les clients en un bilan fiable et traçable, et
**signaler tout ce qui pourrait fausser ce bilan**, même sans être sûr que ce soit une erreur.

Les données arrivent telles quelles. Personne ne dit ce qui cloche dedans.

---

## 2. Ce que les clients ont transmis

### 2.1 Informations recueillies en réunion de lancement

| Code | Raison sociale | Ville | Secteur | Salariés |
|---|---|---|---|---|
| KAY | Kayamb Logistique SAS | Le Port | Transport et logistique portuaire | 310 |
| FAN | Fanjan Agro SA | Saint-Pierre | Agroalimentaire | 420 |
| VAC | Hôtels Vacoa Bleu SARL | Saint-Gilles-les-Bains | Hôtellerie | 280 |

**Sites déclarés par chaque client** (chaque site a son propre compteur électrique, identifié par un point de livraison) :

| Entreprise | Code site | Site | Point de livraison |
|---|---|---|---|
| KAY | LPT-ENT | Entrepôt Le Port | PDL-LPT-ENT |
| KAY | LPT-SIE | Siège Le Port | PDL-LPT-SIE |
| KAY | LPT-ATL | Atelier mécanique | PDL-LPT-ATL |
| FAN | SPI-USI | Usine Saint-Pierre | PDL-SPI-USI |
| FAN | PIE-FRO | Chambres froides Pierrefonds | PDL-PIE-FRO |
| FAN | SPI-ADM | Bureaux Saint-Pierre | PDL-SPI-ADM |
| VAC | SGI-HT1 | Hôtel Vacoa Lagon | PDL-SGI-HT1 |
| VAC | SGI-HT2 | Hôtel Vacoa des Hauts | PDL-SGI-HT2 |
| VAC | SGI-BLA | Blanchisserie | PDL-SGI-BLA |

### 2.2 Fichiers reçus

```
data/raw/
├── KAY/
│   ├── fec/          900000001FEC20251231.txt
│   ├── electricite/  export_edf_2025.csv
│   ├── carburant/    transactions_cartes_2025.csv, parc_vehicules.csv
│   ├── fluides/      interventions_frigoristes_2025.csv
│   └── vols/         export_agence_voyages_2025.csv
├── FAN/
│   ├── fec/          900000002FEC20251231.txt
│   ├── electricite/  releves_electricite_2025.xlsx
│   ├── carburant/    cartes_carburant_2025.csv
│   ├── fluides/      interventions_frigoristes_2025.csv
│   └── vols/         export_agence_voyages_2025.csv
└── VAC/
    ├── fec/          900000003FEC20251231.txt
    ├── electricite/  energy_invoices_2025.csv
    ├── carburant/    carburant_2025_S1.csv, carburant_2025_S2.csv
    ├── fluides/      interventions_frigoristes_2025.csv
    └── vols/         export_agence_voyages_2025.csv
```

| Source | Contenu | Pourquoi on en a besoin |
|---|---|---|
| FEC (Fichier des Écritures Comptables) | Toutes les écritures comptables de l'exercice, au format légal | Estimer toutes les dépenses (scope 3) et recouper les autres sources |
| Électricité | Factures ou relevés mensuels par site | Scope 2 |
| Carburant | Transactions des cartes carburant (+ parc de véhicules chez KAY) | Scope 1, combustion des véhicules |
| Fluides frigorigènes | Recharges réalisées par les frigoristes | Scope 1, fuites de climatisation et de froid |
| Vols | Export de l'agence de voyages | Scope 3, déplacements professionnels |

Chaque client exporte depuis ses propres outils. **Les formats ne sont pas homogènes** : à découvrir en ouvrant les fichiers.

---

## 3. Méthodologie fournie par l'équipe RSE

### 3.1 Deux méthodes de calcul

- **Méthode physique** : quantité mesurée × facteur d'émission (kWh, litres, kg de fluide, passager.km). Précise.
- **Méthode monétaire** : montant HT de dépense × ratio (kgCO₂e par k€). Couvre tout, mais approximative.

**Règle :** quand une donnée physique existe pour un poste, elle remplace la méthode monétaire sur ce poste.
**Un même poste ne doit jamais être compté deux fois.**

### 3.2 Facteurs d'émission physiques (indicatifs)

| Code | Activité | Valeur | Unité | Source |
|---|---|---|---|---|
| ELEC_REUNION | Électricité, mix La Réunion | 0,780 | kgCO₂e / kWh | ADEME Base Carbone |
| GAZOLE | Gazole routier (combustion + amont) | 3,10 | kgCO₂e / L | ADEME Base Empreinte |
| SP95 | Essence SP95 | 2,80 | kgCO₂e / L | Démonstration |
| AVION_COURT | Vol < 1 000 km | 0,258 | kgCO₂e / passager.km | Démonstration |
| AVION_MOYEN | Vol de 1 000 à 3 500 km | 0,187 | kgCO₂e / passager.km | Démonstration |
| AVION_LONG | Vol > 3 500 km | 0,152 | kgCO₂e / passager.km | Démonstration |

- **Fluides frigorigènes :** émissions = kg rechargés × PRG (Pouvoir de Réchauffement Global).
  PRG (règlement F-gas) : R404A 3922 · R410A 2088 · R407C 1774 · R134a 1430 · R449A 1397 · R32 675.
- **Avion :** distance orthodromique entre les deux aéroports **+ 95 km** (correction ADEME). Un aller-retour compte 2 trajets.
  La tranche de facteur se choisit sur la distance d'un aller.

### 3.3 Correspondance comptes comptables → postes (méthode monétaire)

On rattache chaque compte au **préfixe le plus long** qui lui correspond.
« Remplacé par » = poste couvert par une source physique quand elle existe.

| Préfixe | Libellé | Poste | Scope | Ratio (kgCO₂e / k€ HT) | Remplacé par |
|---|---|---|---|---|---|
| 60611 | Électricité | Électricité | 2 | — | électricité |
| 60622 | Carburants | Combustion mobile | 1 | — | carburant |
| 62511 | Billets d'avion | Déplacements professionnels | 3 | — | vols |
| 62512 | Hôtels, taxis, repas | Déplacements professionnels | 3 | 300 | |
| 601 | Matières premières | Achats de biens | 3 | 900 | |
| 6021 | Emballages | Achats de biens | 3 | 600 | |
| 6022 | Boissons | Achats de biens | 3 | 800 | |
| 6063 | Fournitures et petit équipement | Achats de biens | 3 | 450 | |
| 6064 | Fournitures administratives | Achats de biens | 3 | 400 | |
| 611 | Sous-traitance | Achats de services | 3 | 300 | |
| 613 | Locations | Achats de services | 3 | 120 | |
| 615 | Entretien et maintenance | Achats de services | 3 | 250 | |
| 616 | Assurances | Achats de services | 3 | 50 | |
| 6226 | Honoraires | Achats de services | 3 | 110 | |
| 6231 | Publicité | Achats de services | 3 | 150 | |
| 6241 | Transports sur achats | Fret amont | 3 | 500 | |
| 626 | Télécommunications | Achats de services | 3 | 150 | |
| 627 | Services bancaires | Achats de services | 3 | 40 | |
| 2154 | Matériel industriel | Immobilisations | 3 | 600 | |
| 2182 | Matériel de transport | Immobilisations | 3 | 500 | |
| 2184 | Mobilier | Immobilisations | 3 | 400 | |
| 63 à 69 | Impôts, personnel, charges financières, exceptionnelles, dotations | Hors périmètre | — | — | |

Seuls les comptes de charges (classe 6) et d'immobilisations (21) entrent dans le calcul. Les autres classes (bilan, produits) sont ignorées.

### 3.4 Repères de prix (indicatifs, 2025)

| Repère | Valeur |
|---|---|
| Tarif moyen électricité professionnelle | 0,17 € HT / kWh |
| Gazole à la pompe | 1,46 € TTC / L |
| SP95 à la pompe | 1,72 € TTC / L |
| TVA, taux normal La Réunion | 8,5 % |

---

## 4. Ce que le pipeline doit produire

1. **Ingestion** de tous les fichiers reçus, quels que soient leur format et leur encodage, sans perte et avec traçabilité.
2. **Bilan carbone** par entreprise, par scope et par poste, en tCO₂e, avec la part calculée en méthode physique.
3. **Traçabilité** : chaque émission doit pouvoir être reliée à son fichier et à sa ligne d'origine.
4. **Observabilité** : une liste de constats sur la qualité des données reçues, compréhensible par un consultant RSE.
5. **Un tableau de bord** consultable en ligne, régénéré automatiquement.

---

## 5. Observabilité : la démarche attendue

### 5.1 Le principe

Tu ne connais pas tout le métier de chaque client. Ce n'est pas grave : c'est même la situation normale.

- **Détecter au maximum** avec les contrôles génériques de qualité des données.
- **Ne jamais trancher seul quand on doute.** Une ligne suspecte n'est pas forcément fausse. On la signale.
- **Rien n'est corrigé en silence.** Une ligne écartée ou convertie est toujours listée.
- **Remonter l'information au métier**, puis intégrer ses retours dans de nouveaux contrôles.

### 5.2 Les familles d'anomalies génériques (point de départ)

Ce sont les dimensions classiques de la qualité des données. Pour chacune : la question à se poser, et des pistes de détection.

| Famille | Question à se poser | Pistes de détection |
|---|---|---|
| **Conformité du format** | Le fichier a-t-il la structure attendue ? | Colonnes attendues présentes, types convertibles, encodage, séparateur ; comparer la structure entre fichiers d'une même source |
| **Unicité** | Une même information est-elle présente plusieurs fois ? | Clé naturelle (n° de facture, n° de billet…) ; doublons exacts et doublons fonctionnels |
| **Complétude** | Manque-t-il des valeurs, des périodes ou des entités ? | Valeurs vides ; comparer ce qui est reçu à ce qui est attendu (12 mois × chaque site déclaré) |
| **Validité** | Les valeurs sont-elles dans leur domaine ? | Valeurs négatives, codes ou libellés inconnus, dates hors exercice, statuts inattendus |
| **Homogénéité des unités** | Tout est-il exprimé dans la même unité ? | Colonnes d'unité, ordres de grandeur très différents entre lignes comparables |
| **Valeurs aberrantes** | Une valeur est-elle anormalement haute ou basse ? | Écart à la médiane, intervalle interquartile, comparaison entre mois ou entre pairs |
| **Intégrité référentielle** | Chaque code renvoie-t-il à un référentiel connu ? | Site, compte comptable, produit, aéroport absents des référentiels |
| **Cohérence interne** | Les règles propres au format sont-elles respectées ? | Exemple : une écriture comptable doit être équilibrée (débit = crédit) |
| **Cohérence entre sources** | Deux sources qui décrivent la même chose concordent-elles ? | Recouper une donnée physique avec la dépense comptable correspondante |
| **Fraîcheur** | Les données couvrent-elles toute la période ? | Dernière date reçue comparée à la fin de l'exercice |

### 5.3 Format d'un constat

Chaque contrôle produit des constats avec :

| Champ | Contenu |
|---|---|
| Contrôle | Identifiant et libellé |
| Entreprise, source | Où se trouve le problème |
| Sévérité | **bloquant** (le bilan est faux tant que ce n'est pas levé), **alerte** (à vérifier), **info** (traitement appliqué, pour transparence) |
| Statut | **certain** (anomalie avérée) ou **à confirmer par le métier** (suspect, on demande) |
| Question au métier | La question à poser au client ou au consultant, en langage clair |
| Détail | Les lignes concernées, lisibles par un non-technicien |
| Impact estimé | En tCO₂e quand c'est calculable |

### 5.4 La boucle de retour métier

1. Le pipeline produit ses constats.
2. Les constats « à confirmer » partent au consultant RSE ou au client, sous forme de questions.
3. Chaque réponse est consignée dans un **journal des retours métier** (`docs/retours-metier.md`) : date, question, réponse, décision.
4. La décision devient une règle : nouveau contrôle, nouvelle entrée de référentiel, ou exclusion documentée.

Dans cette démonstration, le fichier [`CORRECTION.md`](CORRECTION.md) joue le rôle du retour métier.
**À n'ouvrir qu'après avoir écrit ses contrôles.**

---

## 6. Tests du code vs contrôles des données

À ne pas confondre :
- **Les tests dbt** vérifient que le **code** est juste : unicité des clés, intégrité référentielle, pas de double comptage,
  le bilan agrégé retombe sur la somme des faits. Un échec bloque le pipeline.
- **Les contrôles qualité** vérifient les **données du client**. Ils produisent des constats, sans bloquer le pipeline.

---

## 7. Critères de réussite

| # | Critère | Vérification |
|---|---|---|
| 1 | Tous les fichiers sont ingérés, quel que soit leur format | Journal d'ingestion : fichier, nombre de lignes, statut, empreinte |
| 2 | Ajouter un client ne demande pas de code | Formats décrits dans un fichier de configuration |
| 3 | Un fichier non conforme est isolé, pas chargé à moitié | Statut « quarantaine » + raison |
| 4 | Le bilan est calculé sans double comptage | Test dbt dédié |
| 5 | Chaque émission est traçable jusqu'à sa ligne source | Colonnes fichier + ligne dans la table de faits |
| 6 | Les constats sont compréhensibles par un consultant | Une question métier par contrôle |
| 7 | Tout se reconstruit en une commande | `make all` |
| 8 | Le résultat est consultable en ligne | GitHub Pages, publié par la CI (intégration continue) |

---

## 8. Architecture et stack

```
Fichiers clients ──(configuration)──▶ Ingestion Python ──▶ raw (DuckDB)
                                                             │
                                  dbt staging ◀──────────────┘
                                       │
                         dbt intermediate (physique / monétaire)
                                       │
                              dbt marts (bilan)
                                       │
            contrôles qualité (dbt) ───┴──▶ tableau de bord ──▶ GitHub Pages
```

Python avec **uv**, DuckDB, dbt, pandas + openpyxl, GitHub Actions. Azure et Power BI en étape suivante.

---

## 9. Plan de construction

| Phase | Livrable | À savoir expliquer | Durée estimée |
|---|---|---|---|
| 0 | Squelette du dépôt, `pyproject.toml`, Makefile | Pourquoi uv, structure du projet | 15 min |
| 1 | **Exploration** : ouvrir chaque fichier, noter formats, encodages, colonnes, premières bizarreries | Ce qu'on regarde en premier face à un fichier inconnu | 30 min |
| 2 | Ingestion pilotée par configuration, journal, quarantaine | Fidélité, idempotence, traçabilité | 1 h |
| 3 | dbt : staging, intermediate, marts, tests | Physique vs monétaire, anti-double comptage, préfixe le plus long | 1 h 30 |
| 4 | Contrôles qualité (familles génériques) + constats | Constat ≠ test, certain vs à confirmer | 1 h 30 |
| 5 | Tableau de bord HTML | Rendre un constat lisible par un non-technicien | 45 min |
| 6 | **Retour métier** : ouvrir `CORRECTION.md`, mesurer trouvé / raté, compléter le journal | Ce que le métier apporte que la technique seule ne voit pas | 30 min |
| 7 | CI + GitHub Pages | Ce que fait chaque job | 30 min |

**Pour mercredi :** phases 0 à 7, environ 6 h.

**Feuille de route après l'entretien :** Azure (ADLS Gen2 + Azure SQL via Terraform), rapport Power BI, contrôles issus des retours métier.

---

## 10. Limites à assumer

- Facteurs et ratios indicatifs : un vrai bilan utilise la Base Empreinte de l'ADEME à jour.
- Rechargement complet à chaque exécution : suffisant à ce volume.
- Pas d'orchestrateur : la suite logique serait Azure Data Factory, déclenché à l'arrivée d'un fichier.

---

*Toutes les entreprises, personnes et données de ce projet sont fictives.*
