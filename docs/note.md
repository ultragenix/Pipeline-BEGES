# Carnet de bord — Pipeline BEGES

> Projet de démonstration data engineering.
> Données fictives. Ce document n'est pas un audit réglementaire.

## 0. Pourquoi ce projet

Je voulais un cas qui relie la data et la transition environnementale.
Le BEGES est un bon prétexte : données hétérogènes, enjeux de périmètre,
double comptage, utilisateurs métier non techniques.

La démo est un bonus pour un entretien. Elle montre la curiosité, la méthode
et la capacité à apprendre Azure, pas une expertise réglementaire.

## 1. Ce que je savais / ce que je ne savais pas

**Je savais :** Python, SQL, dbt, culture data, GCP.

**Je ne savais pas :** BEGES, FEC, Azure, managed identity, Terraform azurerm.

**J'ai appris :** un pipeline fiable commence par le profiling des fichiers ;
les doublons apparents ne sont pas toujours des doublons ; les règles métier
non documentées doivent être signalées, pas devinées.

## 2. Méthode de travail

- Je pilote, l'assistant propose.
- Aucune écriture sans validation explicite.
- Une étape = un livrable = une preuve.
- Le carnet est rempli au fil de l'eau, pas après coup.
- La correction n'est pas ouverte avant la comparaison.

## 3. Journal

### 2026-10-21 — Cadrage et reset

**Objectif :** poser les règles et le plan avant de construire.

**Ce qu'on a fait :**
- retour au commit initial après une première tentative trop large ;
- création de `AGENTS.md` ;
- décision d'un dictionnaire avec un fichier par entreprise ;
- ajout d'un registre d'anomalies par entreprise, orienté questions métier ;
- décision de Terraform pour Azure ;
- définition des quality gates.

**Difficulté :** la première tentative a sauté l'étape de cadrage et produit
trop de structure d'un coup.

**Décision :** on réduit le périmètre, pas la rigueur. Chaque écriture est
proposée, validée, puis vérifiée.

**À retenir :** un projet réel commence par le cadre et les preuves, pas par le code.

## 4. Décisions

| Date | Décision | Pourquoi |
|---|---|---|
| 21/10 | `AGENTS.md` avec validation obligatoire | garder le contrôle, éviter les dérives |
| 21/10 | Un fichier de dictionnaire par entreprise | lisibilité, passage à l'échelle |
| 21/10 | Un registre d'anomalies par entreprise | séparer la structure des données des questions métier |
| 21/10 | Schémas communs séparés | éviter la duplication |
| 21/10 | Terraform pour Azure | rigueur, plan/apply, reproductibilité |
| 21/10 | uv + Docker | reproductibilité locale et cloud |
| 21/10 | Dashboard statique + observabilité | demo portable, pas de serveur |

## 5. Difficultés

| Difficulté | Leçon |
|---|---|
| Première tentative trop large | cadrer avant de coder |
| Docker Desktop non intégré à WSL | vérifier l'environnement avant de bâtir |
| Données hétérogènes | profiler avant d'écrire l'ingestion |

## 6. Questions ouvertes

- KAY : site LPT-ATL sans relevé électrique.
- KAY : doublon de juillet et régularisation de mai.
- VAC : décembre manquant.
- VAC : billets annulés et doublons.
- KAY : ADBLUE et PRODUIT 47.
- FAN : carburant sans litres.
- FAN : fluide `R-?`.
- KAY : compte `6288000` non mappé.
- FAN : écriture `AC000042` déséquilibrée.

Ces questions seront traitées à l'étape 1, dans le dictionnaire par entreprise.

## 7. À retenir pour l'entretien

- « Je réduis le périmètre, pas la rigueur. »
- « Un fichier par entreprise ; à 300, on génère depuis un catalogue. »
- « Le dictionnaire décrit, le registre d'anomalies questionne. »
- « Les règles métier manquées sont des règles métier, pas de l'ingénierie data. »
- « Terraform, plan avant apply, destroy après la démo. »

## 8. Prochaine étape

Étape 1 : dictionnaire et registre d'anomalies par entreprise, en commençant par FAN.
