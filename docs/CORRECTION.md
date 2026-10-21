# Retour métier : les anomalies présentes dans les fichiers

> ⚠️ **À ouvrir seulement après avoir écrit ses contrôles qualité.**
>
> Ce document joue le rôle du retour des consultants RSE et des clients. Il liste les 16 anomalies réellement
> présentes dans les fichiers reçus, explique pourquoi chacune compte pour le bilan, et indique si un contrôle
> générique pouvait la trouver ou s'il fallait une connaissance du métier.
>
> Rater certaines anomalies n'est pas un échec : c'est la réalité du terrain. L'important, c'est la boucle
> « je détecte → je remonte → le métier répond → j'intègre ».

---

## Comment l'utiliser

1. Lancer le pipeline et lister ses propres constats.
2. Remplir la colonne « Trouvé seul ? » du tableau de synthèse ci-dessous.
3. Pour chaque anomalie ratée : noter pourquoi dans `docs/retours-metier.md`, puis ajouter le contrôle ou la règle.
4. Pour chaque constat de son pipeline absent de cette liste : vérifier si c'est un faux positif, ou une vraie anomalie non listée ici.

---

## Synthèse

| Id | Entreprise | Source | Anomalie | Famille | Trouvable sans le métier ? | Trouvé seul ? |
|---|---|---|---|---|---|---|
| A01 | FAN | Électricité | Un site exporté en MWh, les autres en kWh | Homogénéité des unités | Oui | |
| A02 | KAY | Électricité | Une facture en double | Unicité | Oui | |
| A03 | VAC | Électricité | Décembre jamais transmis | Complétude, fraîcheur | Oui | |
| A04 | KAY | Électricité | Relevé estimé puis régularisation négative | Validité | En partie | |
| A05 | KAY | Carburant | Plein de 400 L dans un réservoir de 300 L | Valeurs aberrantes | En partie | |
| A06 | KAY | Carburant | Libellé produit inconnu | Intégrité référentielle | Oui | |
| A07 | FAN | Carburant | Montants en € sans litres | Complétude | Oui (la conversion est un choix métier) | |
| A08 | VAC | Carburant | Une colonne renommée en cours d'année | Conformité du format | Oui | |
| A09 | FAN | FEC | Une écriture déséquilibrée | Cohérence interne | Oui, avec la règle comptable de base | |
| A10 | KAY | FEC | Un compte de charges absent de la correspondance | Intégrité référentielle | Oui | |
| A11 | VAC | FEC | Avoirs fournisseurs | Validité | Non | |
| A12 | FAN | Fluides | Recharges sans type de fluide exploitable | Complétude, intégrité référentielle | Oui | |
| A13 | VAC | Vols | Billets annulés encore présents | Validité | Oui | |
| A14 | VAC | Vols | Billets en double | Unicité | Oui | |
| A15 | KAY | Vols | Un billet sans destination | Complétude | Oui | |
| A16 | KAY | Électricité | Un site entier absent, mais facturé en comptabilité | Complétude, cohérence entre sources | Oui avec la liste des sites ; le recoupement comptable est un réflexe métier | |

---

## Détail des anomalies

### A01 · Fanjan Agro · Unités mélangées dans l'électricité
- **Ce qui se passe :** dans le fichier Excel, la feuille du site « Chambres froides Pierrefonds » est en **MWh**. Les autres feuilles sont en kWh.
- **Pourquoi c'est grave :** sans conversion, la consommation du site est divisée par 1 000. C'est le site le plus énergivore après l'usine.
- **Comment le voir :** la colonne « Unité » varie d'une feuille à l'autre ; les valeurs de ce site sont 1 000 fois plus petites.
- **Décision métier :** convertir en kWh, et le signaler pour que le client confirme l'unité.

### A02 · Kayamb Logistique · Facture d'électricité en double
- **Ce qui se passe :** la facture de juillet de l'entrepôt apparaît deux fois, à l'identique.
- **Pourquoi c'est grave :** un mois de consommation compté deux fois (environ 25 tCO₂e).
- **Comment le voir :** même numéro de facture, même site, même mois, même montant.
- **Décision métier :** ne garder qu'une occurrence, et signaler.

### A03 · Hôtels Vacoa Bleu · Décembre manquant
- **Ce qui se passe :** aucune facture de décembre, pour aucun des trois sites.
- **Pourquoi c'est grave :** un mois manque, et c'est un mois d'été austral, donc de forte climatisation (environ 8 % du poste électricité).
- **Comment le voir :** 11 mois reçus au lieu de 12 par site ; dernier mois reçu = novembre.
- **Décision métier :** demander les factures au client. En attendant, le bilan est provisoire.

### A04 · Kayamb Logistique · Relevé estimé puis régularisation
- **Ce qui se passe :** en avril, le relevé de l'entrepôt est « Estimé », avec 30 % de trop. En mai, une ligne « Régularisation » **négative** corrige l'écart.
- **Pourquoi c'est grave :** sur l'année, le total est juste. Mais une analyse mois par mois serait faussée, et une ligne négative peut casser des calculs ou des tests mal conçus.
- **Comment le voir :** une consommation négative est le signal générique. Comprendre le couple « estimé → régularisation » demande de connaître la facturation de l'énergie.
- **Décision métier :** conserver les deux lignes (le total annuel est correct) et le signaler comme alerte.

### A05 · Kayamb Logistique · Plein impossible
- **Ce qui se passe :** un plein de 400 L sur un porteur dont le réservoir fait 300 L.
- **Pourquoi c'est grave :** erreur de saisie, ou carte utilisée pour un autre véhicule. C'est une question de fiabilité, et parfois un sujet de fraude.
- **Comment le voir :** une détection statistique des valeurs aberrantes peut le repérer. La règle exacte (litres > capacité du réservoir) suppose de penser à croiser avec le fichier du parc, ce qui relève du métier.
- **Décision métier :** demander au client ; conserver la ligne en attendant, avec une alerte.

### A06 · Kayamb Logistique · Produit carburant inconnu
- **Ce qui se passe :** 9 transactions portent le libellé « PRODUIT 47 », un code interne de station. Le fichier contient aussi plusieurs libellés pour le même gazole (GAZOLE, GO, B7, Diesel) et de l'AdBlue.
- **Pourquoi c'est grave :** environ 1 600 L sans facteur d'émission, donc absents du bilan.
- **Comment le voir :** tout libellé absent du référentiel des produits.
- **Point métier :** l'AdBlue est un additif, pas un carburant. Il est hors périmètre.
- **Décision métier :** demander au client ce que recouvre « PRODUIT 47 ».

### A07 · Fanjan Agro · Carburant sans litres
- **Ce qui se passe :** le fournisseur de cartes n'exporte que des montants TTC, sans les litres.
- **Pourquoi c'est grave :** il faut reconstituer les litres à partir d'un prix moyen. La précision baisse.
- **Comment le voir :** colonne de quantité absente ou vide pour toute une source.
- **Décision métier :** litres = montant TTC / prix moyen du litre. C'est une méthode à documenter, et une info à signaler (demander l'export détaillé l'année suivante).

### A08 · Hôtels Vacoa Bleu · Changement de format en juillet
- **Ce qui se passe :** le fichier du premier semestre a une colonne « Quantite (L) ». Celui du second semestre l'appelle « Volume ».
- **Pourquoi c'est grave :** une ingestion rigide échoue, ou perd silencieusement six mois de carburant.
- **Comment le voir :** comparer les en-têtes des fichiers d'une même source.
- **Décision métier :** ajouter l'alias dans la configuration, et garder la trace du changement.

### A09 · Fanjan Agro · Écriture comptable déséquilibrée
- **Ce qui se passe :** une écriture d'achat d'emballages a un débit supérieur au crédit de 150 €.
- **Pourquoi c'est grave :** un FEC est toujours équilibré, écriture par écriture. Un écart signale un export incomplet ou corrompu, et met en doute la fiabilité de tout le fichier.
- **Comment le voir :** pour chaque numéro d'écriture, la somme des débits doit égaler la somme des crédits.
- **Décision métier :** demander un nouvel export à l'expert-comptable.

### A10 · Kayamb Logistique · Compte comptable non rattaché
- **Ce qui se passe :** le compte 6288000 « Prestations diverses portuaires » (environ 520 k€) n'a pas de préfixe dans la table de correspondance.
- **Pourquoi c'est grave :** une dépense importante disparaît du bilan, sans aucune erreur visible.
- **Comment le voir :** tout compte de classe 6 sans correspondance.
- **Décision métier :** le consultant RSE choisit le poste et le ratio, puis complète le référentiel.

### A11 · Hôtels Vacoa Bleu · Avoirs fournisseurs
- **Ce qui se passe :** trois avoirs (remboursements fournisseurs) sont passés au crédit du compte d'achats alimentaires.
- **Pourquoi c'est grave :** si l'on ne prend que les débits, les achats sont surestimés.
- **Comment le voir :** des montants au crédit sur des comptes de charges. Encore faut-il savoir qu'en comptabilité, c'est la marque d'un avoir.
- **Décision métier :** calculer sur le montant net (débit − crédit), et le signaler en info.

### A12 · Fanjan Agro · Fluide frigorigène non identifié
- **Ce qui se passe :** deux recharges sur des chambres froides : l'une sans type de fluide, l'autre avec « R-? ».
- **Pourquoi c'est grave :** environ 10 kg de fluide non valorisés. Avec un PRG de plusieurs milliers, cela peut représenter plus de 40 tCO₂e.
- **Comment le voir :** fluide vide ou absent du référentiel des PRG.
- **Décision métier :** demander le rapport d'intervention au frigoriste.

### A13 · Hôtels Vacoa Bleu · Billets annulés
- **Ce qui se passe :** trois billets ont le statut « Annulé » dans l'export de l'agence.
- **Pourquoi c'est grave :** des vols jamais effectués seraient comptés.
- **Comment le voir :** la colonne Statut.
- **Décision métier :** les exclure, et le signaler en info.

### A14 · Hôtels Vacoa Bleu · Billets en double
- **Ce qui se passe :** deux billets apparaissent deux fois.
- **Pourquoi c'est grave :** double comptage de deux allers-retours.
- **Comment le voir :** numéro de billet en double.
- **Décision métier :** ne garder qu'une occurrence.

### A15 · Kayamb Logistique · Billet sans destination
- **Ce qui se passe :** un billet n'a pas d'aéroport de destination.
- **Pourquoi c'est grave :** impossible de calculer la distance ; le vol disparaît du bilan (environ 2 tCO₂e pour un aller-retour vers la métropole).
- **Comment le voir :** destination vide ou inconnue du référentiel des aéroports.
- **Décision métier :** demander le détail à l'agence de voyages.

### A16 · Kayamb Logistique · Un site oublié dans l'export d'électricité
- **Ce qui se passe :** l'export d'électricité ne contient pas l'« Atelier mécanique ». Ses factures sont pourtant bien en comptabilité.
- **Pourquoi c'est grave :** environ un tiers de l'électricité de l'entreprise manque (environ 210 tCO₂e). Comme la méthode physique remplace la méthode monétaire, ce site disparaît complètement du bilan.
- **Comment le voir :** deux voies.
  - *Générique :* comparer les sites reçus à la liste des sites déclarés en réunion de lancement.
  - *Métier :* recouper les kWh mesurés avec la dépense d'électricité comptabilisée, divisée par le tarif moyen. L'écart est d'environ −33 %.
- **Décision métier :** demander l'export du site manquant. C'est l'exemple type de ce que seul le recoupement entre sources permet de voir.

---

## Ce qu'il faut en retenir

- **Les contrôles génériques** (format, unicité, complétude, validité, intégrité) attrapent la majorité des anomalies.
- **Les anomalies les plus coûteuses** (A16 : 210 tCO₂e, A12 : plus de 40 tCO₂e) se trouvent en croisant les sources, ou en connaissant le terrain.
- **Le recoupement avec la comptabilité** est le meilleur filet de sécurité d'un bilan carbone. Toutes les dépenses passent par le FEC.
- **La conversation avec le métier** ne vient pas en fin de projet : c'est une partie du pipeline.
