# Fiche de Cadrage — Projet AURORAS
## Prédiction des Tempêtes Géomagnétiques

**Auteurs** : [Vos noms]
**Module** : Machine Learning — 2ème année Cycle Ingénieurs GI
**Année** : 2025-2026
**Domaine métier** : Environnement / Météorologie Spatiale
**Sources de données** : NASA DONKI API & NASA/NOAA OMNI (SPDF)

---

## 1. Problématique scientifique

### 1.1 Les tempêtes géomagnétiques : un phénomène naturel aux conséquences industrielles majeures

Le Soleil éjecte en permanence un flux de particules chargées (protons, électrons) connu sous le nom de **vent solaire**, qui voyage à des vitesses de 300 à 800 km/s dans des conditions normales. Lors d'éruptions solaires intenses — les **éjections de masse coronale (CME)** — ce flux peut atteindre 1 000 à 3 000 km/s et transporter un champ magnétique orienté vers le sud (composante **Bz négative**). Lorsque ce champ interagit avec la magnétosphère terrestre, il déclenche une **tempête géomagnétique** : une perturbation globale et soudaine du champ magnétique de la Terre.

Ces perturbations induisent des **courants géomagnétiquement induits (GIC)** dans tous les conducteurs longs à la surface de la Terre — lignes à haute tension, pipelines, câbles sous-marins — et augmentent la densité atmosphérique dans l'orbite basse, amplifiant le freinage atmosphérique (drag) des satellites.

### 1.2 Cas réels documentés et chiffrés

**Tempête de Québec — 13 mars 1989 (tempête de classe G5, Kp = 9)**

Le 13 mars 1989 à 01h27 UTC, une CME issue d'une éruption solaire de classe X15 du 6 mars atteint la Terre. Le vent solaire mesuré à son apogée atteignait **v ≈ 980 km/s** avec une composante Bz descendant à **-40 à -60 nT** [1]. La perturbation magnétique mesurée par l'indice Dst atteignit un minimum historique de **-589 nT** [1].

En moins de **90 secondes**, l'ensemble du réseau électrique d'Hydro-Québec s'effondre : les courants GIC saturent les transformateurs, les compensateurs de puissance réactive (Static VAR Compensators) disjonctent, et le système perd toute stabilité [2]. Le bilan est le suivant :

- **6 millions de Québécois** privés d'électricité pendant **9 heures** [3]
- **13,2 millions de dollars** de dommages matériels directs chez Hydro-Québec, dont **6,5 millions** pour les dommages d'équipements seuls [4]
- Des perturbations simultanées aux États-Unis, en Suède et au Royaume-Uni, avec des transformateurs endommagés [1]
- Le rapport de la National Academy of Sciences estime qu'une tempête équivalente aujourd'hui provoquerait des dommages supérieurs à **1 trillion de dollars** aux États-Unis seuls [5]
- La tempête de 1989 était un événement statistique de **1 fois tous les 50 ans** [3]

**Incident Starlink — 4 février 2022 (tempête mineure, Kp = 5)**

Le 3 février 2022, SpaceX lance 49 satellites Starlink depuis le Kennedy Space Center. Le lendemain, une tempête géomagnétique de niveau G1 — **la plus basse catégorie de tempête** — augmente la densité atmosphérique de **20 à 30%** à 210 km d'altitude [6], amplifiant le freinage sur les satellites en phase d'ascension orbitale.

- **38 des 49 satellites** (77,6%) sont rendus inopérables et se désintègrent dans l'atmosphère [6][7]
- Coût financier estimé entre **50 et 100 millions de dollars** selon le Dr. Hugh Lewis, expert en débris spatiaux à l'Université de Southampton [8]
- Cet événement démontre que même les tempêtes **mineures** peuvent avoir des conséquences économiques majeures sur les infrastructures spatiales

**Fréquence statistique des tempêtes**

Selon les données NOAA sur 22 ans d'historique Kp, les périodes de tempête (Kp ≥ 5) représentent environ **1/20ème du temps total** (~5%), avec une chute rapide pour les événements plus extrêmes [9]. Les tempêtes G1 (Kp = 5) surviennent environ **1 700 fois par cycle solaire de 11 ans** [10], soit en moyenne tous les 2,4 jours en période de maximum solaire.

### 1.3 Contexte actuel : le maximum solaire du Cycle 25

En 2025-2026, nous sommes en plein **maximum solaire du Cycle 25**, officiellement déclaré par la NASA et la NOAA. La tempête du 10-11 mai 2024 a atteint le niveau G5 (Kp = 9), le plus élevé depuis 2003 [11], confirmant l'intensité exceptionnelle de cette période. Notre dataset (2019-2023) capture la montée progressive vers ce maximum, avec une croissance naturelle du taux de tempêtes en fin de période.

---

## 2. Objectifs métiers quantifiés

**Objectif principal** : Prédire **6 heures à l'avance** si une tempête géomagnétique officielle (référencée dans le catalogue NASA DONKI) va se déclencher, afin de :

- Passer les satellites en mode "safe mode" (réorientation pour minimiser la surface exposée au vent solaire)
- Déclencher les protocoles de protection des réseaux électriques à haute tension
- Alerter les opérateurs de réseaux GPS/GNSS d'une dégradation imminente de la précision

### Justification scientifique de l'horizon de prédiction de 6 heures

Le choix de **6 heures** comme horizon de prédiction n'est pas arbitraire. Il repose sur deux réalités physiques et opérationnelles documentées :

**Réalité physique n°1 — La limitation fondamentale du point L1**

Les satellites de surveillance du vent solaire (ACE, DSCOVR) sont positionnés au **point de Lagrange L1**, situé à environ 1,5 million de kilomètres de la Terre en direction du Soleil. À cette distance, le vent solaire est mesuré **en avance** sur son arrivée à la Terre — mais cette avance est très courte.

Le modèle opérationnel Geospace du **NOAA Space Weather Prediction Center (SWPC)** ne peut fournir qu'une prévision de **30 à 60 minutes** à partir des données L1 en temps réel, selon la vitesse du vent solaire [12]. C'est insuffisant pour déclencher des protocoles industriels complexes.

**Réalité physique n°2 — Le temps nécessaire pour les procédures de protection**

Pour qu'une alerte soit **actionnable** par les opérateurs industriels, il faut :
- Valider l'alerte et déclencher le protocole interne : ~30 minutes
- Réorienter un satellite en mode safe : 1 à 4 heures selon le type de satellite
- Ajuster la charge des réseaux électriques haute tension : 2 à 6 heures

Un horizon de **6 heures** est le minimum opérationnel identifié dans la littérature scientifique pour permettre des actions correctives réelles [13]. La recherche académique en Machine Learning appliquée à la météorologie spatiale cible explicitement des prévisions **jusqu'à 6 heures en avance** sur les données de vent solaire [13].

**Objectifs quantifiés** :
- **Détection** : Capturer au moins **80%** des tempêtes officielles NASA avant leur déclenchement
- **Fiabilité** : Ne pas dépasser **50% de fausses alertes** pour maintenir la confiance opérationnelle

---

## 3. Traduction Métier → ML

| Objectif métier | Objectif ML | Métrique principale |
| :--- | :--- | :--- |
| **Sécurité maximale** : Ne rater aucune tempête majeure (éviter la perte de satellites ou pannes réseau) | Maximiser le rappel (Recall) sur la classe 1 | **Recall ≥ 0.80** |
| **Efficacité opérationnelle** : Limiter les arrêts de service inutiles (fausses alertes coûteuses) | Maintenir une précision (Precision) décente | **Precision ≥ 0.50** |
| **Performance globale sur classe rare** : Robustesse malgré le déséquilibre ~5% / 95% | Optimiser l'équilibre Précision-Rappel | **F1-score & PR-AUC** |

---

## 4. Analyse du coût asymétrique

L'asymétrie des coûts entre une erreur de Type I (Faux Positif) et de Type II (Faux Négatif) est ici extrême et documentée :

### 4.1 Faux Négatif (FN) — Tempête non prédite qui arrive quand même

| Scénario | Impact | Coût estimé | Source |
|---|---|---|---|
| Satellite de télécommunication perdu | Destruction ou dégradation irréparable en orbite | 200 M$ à 500 M$ par satellite | Valeur de marché standard |
| Réseau électrique non protégé | Pannes en cascade, transformateurs brûlés | 13,2 M$ (Québec 1989, réseau régional seul) | Bolduc, 2002 [4] |
| Superstorm scénario (Carrington-level) | Panne continentale, des mois de rétablissement | > 1 trillion $ aux USA | National Academy of Sciences [5] |
| 38 satellites Starlink (tempête G1, 2022) | Déorbitation et destruction complète | 50 à 100 M$ | Dr. Hugh Lewis, Univ. Southampton [8] |

### 4.2 Faux Positif (FP) — Alerte lancée inutilement

| Scénario | Impact | Coût estimé |
|---|---|---|
| Mise en mode safe d'un satellite | Interruption temporaire du service, heures de travail d'ingénieurs | ~2 000 à 10 000 $ |
| Alerte réseau électrique non justifiée | Mobilisation d'une équipe de veille, ajustements préventifs | ~5 000 à 20 000 $ |

### 4.3 Rapport d'asymétrie

Le rapport entre le coût d'un Faux Négatif et d'un Faux Positif est de l'ordre de **10 000 à 100 000 fois**. Cette asymétrie extrême oriente sans ambiguïté le choix de la métrique principale.

> **Conclusion** : Dans ce domaine métier, manquer une tempête réelle est catastrophique et irréversible (satellite perdu, infrastructure détruite). Déclencher une fausse alerte est coûteux mais gérable et réversible. On **maximise donc le Recall** comme priorité absolue, quitte à accepter un taux de Faux Positifs plus élevé.

---

## 5. Métriques retenues — Justification détaillée

### 5.1 Pourquoi l'Accuracy est refusée comme métrique principale

Notre dataset présente un déséquilibre naturel de ~8.41% de tempêtes (classe 1) contre ~91.59% de calme (classe 0). Un modèle naïf qui prédit systématiquement "pas de tempête" obtient une **Accuracy de 91.59%** — score excellent en apparence, mais le modèle ne détecte **aucune tempête**. L'Accuracy ne distingue pas les erreurs sur la classe rare de celles sur la classe dominante.

### 5.2 Pourquoi le ROC-AUC seul est refusé comme métrique principale

Le ROC-AUC mesure la capacité du modèle à séparer les classes **sur l'ensemble des seuils**. Sur des données très déséquilibrées, la courbe ROC est optimiste car le grand nombre de Vrais Négatifs (91.59% de non-tempêtes) fait artificiellement monter le Taux de Vrais Positifs sans pénaliser suffisamment les Faux Positifs. Un modèle peut avoir un ROC-AUC de 0,85 tout en ayant un Recall de seulement 0,40 sur la classe tempête — ce qui est inacceptable dans notre contexte opérationnel.

### 5.3 Métriques retenues et leur rôle

**Recall (métrique principale, objectif ≥ 0.80)**
$$\text{Recall} = \frac{TP}{TP + FN}$$
Mesure la proportion de tempêtes réelles correctement détectées. C'est la métrique directement alignée avec l'objectif de sécurité maximal. Maximiser le Recall revient à minimiser les Faux Négatifs — soit les tempêtes manquées aux conséquences catastrophiques.

**Precision (métrique secondaire, objectif ≥ 0.50)**
$$\text{Precision} = \frac{TP}{TP + FP}$$
Mesure la proportion d'alertes émises qui correspondent à de vraies tempêtes. Une Precision trop faible dégrade la confiance des opérateurs et génère des coûts opérationnels inutiles. L'objectif de 50% signifie qu'on accepte jusqu'à une fausse alerte pour chaque vraie alarme — un compromis raisonnable compte tenu de l'asymétrie des coûts.

**F1-Score (métrique d'équilibre)**
$$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$
Moyenne harmonique de la Precision et du Recall. Particulièrement utile pour comparer des modèles sur la classe minoritaire. Pénalise fortement les modèles qui sacrifient entièrement l'une ou l'autre métrique.

**PR-AUC — Aire sous la courbe Précision-Rappel (métrique globale)**
Contrairement au ROC-AUC, la courbe PR se concentre exclusivement sur la classe positive (tempêtes) et n'est pas affectée par l'abondance de la classe négative. Un PR-AUC élevé garantit qu'un modèle est performant sur la classe rare à tous les seuils de décision — c'est la métrique recommandée pour les problèmes de classification déséquilibrée en météorologie spatiale [9].

### 5.4 Résumé des métriques

| Métrique | Statut | Objectif | Justification |
|---|---|---|---|
| **Recall** | Principale | ≥ 0.80 | Minimiser les FN catastrophiques |
| **Precision** | Secondaire | ≥ 0.50 | Limiter les fausses alertes |
| **F1-Score** | Secondaire | Maximiser | Équilibre Precision/Recall |
| **PR-AUC** | Secondaire | Maximiser | Performance globale sur classe rare |
| Accuracy seule | Refusée | — | Optimiste sur données déséquilibrées |
| ROC-AUC seul | Refusée | — | Insuffisant pour classe rare |

---

## 6. Références

[1] Boteler, D. H. (2019). *A 21st Century View of the March 1989 Magnetic Storm*. Space Weather, 17(10), 1427–1441. https://doi.org/10.1029/2019SW002278

[2] Spaceweather.com (2021). *The Great Québec Blackout*. https://spaceweatherarchive.com/2021/03/12/the-great-quebec-blackout/

[3] Canadian History Ehx (2022). *The 1989 Quebec Blackout*. https://canadaehx.com/2022/03/26/the-1989-quebec-blackout/

[4] Bolduc, L. (2002). *GIC observations and studies in the Hydro-Québec power system*. Journal of Atmospheric and Solar-Terrestrial Physics, 64(16), 1793–1802. https://doi.org/10.1016/S1364-6826(02)00128-1

[5] U.S. Geological Survey (USGS). *Preparing the Nation for Intense Space Weather*. National Academy of Sciences report cited. https://www.usgs.gov/news/preparing-nation-intense-space-weather

[6] Fang, T.-W., et al. (2022). *Starlink Satellite Losses During the February 2022 Geomagnetic Storm Event*. Space Weather, AGU Publications. https://agupubs.onlinelibrary.wiley.com/doi/toc/10.1002/(ISSN)1542-7390.STRLNK2022

[7] NASA Scientific Visualization Studio (2024). *Geomagnetic Storm Causes Satellite Loss*. https://svs.gsfc.nasa.gov/5193/

[8] MIT Technology Review (2022). *SpaceX just lost 40 satellites to a geomagnetic storm*. https://www.technologyreview.com/2022/02/10/1045202/spacex-just-lost-40-satellites-to-a-geomagnetic-storm-there-could-be-worse-to-come/

[9] Chakraborty, S., & Morley, S. K. (2020). *Probabilistic Prediction of Geomagnetic Storms and the Kp Index*. Journal of Space Weather and Space Climate. https://www.swsc-journal.org/articles/swsc/full_html/2020/01/swsc190086/swsc190086.html

[10] The World Data (2025). *Geomagnetic Storm in Statistics US 2025*. Based on NOAA Space Weather Scales Historical Data. https://theworlddata.com/geomagnetic-storm-in-us/

[11] Elvidge, S., et al. (2025). *The Probability of the May 2024 Geomagnetic Superstorm*. Space Weather, Wiley. https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024SW004113

[12] NOAA Space Weather Prediction Center (2021). *Geospace Geomagnetic Activity Plot — Model Description*. https://www.swpc.noaa.gov/products/geospace-geomagnetic-activity-plot

[13] Upendran, V., et al. (2020). *Simultaneously forecasting global geomagnetic activity using Recurrent Networks*. arXiv:2010.06487. https://arxiv.org/pdf/2010.06487

[14] Weiler, et al. (2025). *First observations of a geomagnetic superstorm with a sub-L1 monitor*. arXiv:2411.12490. https://arxiv.org/html/2411.12490v2