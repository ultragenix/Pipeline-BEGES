# Anomalies et questions métier

> Un fichier par entreprise. Chaque anomalie doit avoir une preuve et une question
> compréhensible par un consultant RSE ou le client.

## Index

| Entreprise | Fichier | Statut |
|---|---|---|
| KAY — Kayamb Logistique SAS | [KAY.md](KAY.md) | disponible |
| FAN — Fanjan Agro SA | [FAN.md](FAN.md) | disponible |
| VAC — Hôtels Vacoa Bleu SARL | [VAC.md](VAC.md) | disponible |

> Depuis l'étape 5, les constats sont recalculés dans
> [`../quality.md`](../quality.md) et dans la table `analytics.quality_constats`.
> Chaque registre d'entreprise garde la question métier d'origine et ajoute une
> section 5 avec les preuves recalculées.

## Comment utiliser

1. Lire le résumé.
2. Pour chaque ligne, vérifier la preuve (fichier, ligne, valeur).
3. Poser la question au métier.
4. Consigner la réponse dans le journal des réponses.
5. Transformer la réponse en règle, contrôle ou exclusion documentée.

## Statuts

- **Ouvert** : constat posé, question pas encore envoyée.
- **À confirmer** : question envoyée, réponse attendue.
- **Répondu** : réponse reçue, décision à intégrer.
- **Intégré** : règle ou contrôle ajouté.
- **Écarté** : faux positif documenté.

## Sévérités

- **Bloquant** : le bilan est faux tant que ce n'est pas levé.
- **Alerte** : à vérifier, impact possible.
- **Info** : traitement appliqué, pour transparence.

## Règles

- Une anomalie = une preuve + une question + un impact.
- Pas de correction silencieuse.
- Une question sans réponse reste ouverte.
- Le fichier est mis à jour à chaque retour métier.
