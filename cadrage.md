# Fiche de Cadrage — Projet AURORAS
## Prédiction des Tempêtes Géomagnétiques

**Auteurs** : [Vos noms]  
**Domaine métier** : Environnement / Météo spatiale  
**Source de données** : NASA APIs (DONKI & SPDF/OMNI)

---

## 1. Objectifs métiers quantifiés

**Problématique** : Les tempêtes géomagnétiques peuvent induire des courants électriques destructeurs dans les satellites et les réseaux terrestres.
**Objectif principal** : Prédire **6 heures à l'avance** le déclenchement d'une tempête (statut binaire : Calme ou Tempête) pour permettre le passage en mode "safe" des équipements sensibles.

**Objectifs quantifiés** :
- **Détection** : Capturer au moins **80% des événements réels** pour minimiser les risques de casse matérielle.
- **Fiabilité** : Ne pas avoir plus de **50% de fausses alertes** pour maintenir la confiance des opérateurs et éviter des coûts de maintenance inutiles.

## 2. Traduction Métier → ML

| Objectif métier | Objectif ML | Métrique principale |
| :--- | :--- | :--- |
| **Sécurité maximale** : Ne rater aucune tempête majeure | Maximiser le rappel (Recall) sur la classe 1 | **Recall ≥ 0.80** |
| **Efficacité opérationnelle** : Limiter les arrêts de service inutiles | Maintenir une précision (Precision) décente | **Precision ≥ 0.50** |
| **Stabilité sur classe rare** : Performance équilibrée | Optimiser l'aire sous la courbe Precision-Recall | **PR-AUC** |

## 3. Analyse du coût asymétrique

L'asymétrie des coûts entre une erreur de type I (Faux Positif) et de type II (Faux Négatif) est ici extrême :

- **Faux Négatif (FN)** : Une tempête arrive mais n'est pas prédite.
    - *Impact* : Perte d'un satellite de communication ou panne majeure du réseau électrique (ex: Québec 1989).
    - *Coût estimé* : **~200 000 000 $** (valeur moyenne d'un satellite de télécommunications).
- **Faux Positif (FP)** : Une alerte est lancée mais il ne se passe rien.
    - *Impact* : Suspension temporaire d'un service, mobilisation d'une équipe technique de veille.
    - *Coût estimé* : **~2 000 $** (coût opérationnel de mise en sécurité et perte d'exploitation mineure).

**Rapport d'asymétrie** : Un Faux Négatif coûte environ **100 000 fois plus cher** qu'un Faux Positif.

> [!IMPORTANT]
> Cette analyse justifie le choix du **Recall** comme priorité absolue. Dans ce domaine métier, il est préférable de déclencher des alertes préventives (quitte à se tromper) plutôt que de subir un impact matériel catastrophique non anticipé.

## 4. Caractéristiques du Dataset et Métriques

- **Taille** : ~43 300 lignes (Granularité horaire 2019-2023).
- **Déséquilibre** : ~8% de classe minoritaire (après élargissement des fenêtres temporelles pour respecter le seuil minimal de 5% exigé).
- **Métrique principale** : **PR-AUC** (Precision-Recall Area Under Curve).
- **Métriques secondaires** : Recall, Precision, F1-Score.
- **Métriques refusées** : Accuracy et ROC-AUC seule (car elles sont trop optimistes sur des données déséquilibrées et ne reflètent pas la capacité réelle à détecter la classe rare).