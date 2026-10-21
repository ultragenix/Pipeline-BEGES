# Dictionnaire des données

> Un fichier par entreprise. Les schémas communs sont décrits une seule fois.

## Index

| Entreprise | Fiche | Statut |
|---|---|---|
| KAY — Kayamb Logistique SAS | [KAY.md](KAY.md) | disponible |
| FAN — Fanjan Agro SA | [FAN.md](FAN.md) | disponible |
| VAC — Hôtels Vacoa Bleu SARL | [VAC.md](VAC.md) | disponible |

## Comment lire

- `schemas-communs.md` : conventions et colonnes partagées.
- `_modele-entreprise.md` : modèle pour ajouter un client.
- `<CODE>.md` : spécificités de l'entreprise (fichiers, encodages, volumes,
  écarts de schéma, clés, anomalies, questions).

## Règles

- Un fait observé est marqué **Certain**.
- Une hypothèse est marquée **À confirmer**.
- On ne corrige jamais une donnée dans la documentation.
- Toute question métier est reliée à un contrôle ou à une fiche.
- Les données du dépôt sont fictives.

## Ajouter une entreprise

1. Copier `_modele-entreprise.md` en `<CODE>.md`.
2. Remplir les métadonnées, les fichiers, les spécificités et les clés.
3. Vérifier que chaque source est décrite.
4. Faire relire par un data steward ou un consultant.
5. Mettre à jour l'index.

## Passage à l'échelle

À 3 entreprises, un fichier Markdown par entreprise est lisible.
À 300, on ne maintient pas 300 fichiers à la main :

1. catalogue machine-readable par entreprise (`config/companies/*.yml`) ;
2. schéma canonique commun + overrides ;
3. profiling automatisé ;
4. génération des fiches Markdown depuis le catalogue ;
5. data catalog (Purview, DataHub, OpenMetadata) pour recherche, lineage, ownership ;
6. data contracts et détection de dérive ;
7. revue par un data steward ;
8. cloisonnement des données clients dans un repo privé ou un namespace protégé.

## Statut

- [x] Cadrage
- [x] FAN
- [x] KAY
- [x] VAC
