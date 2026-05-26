![Aurora Borealis Data Banner](assets/banner.png)
# Tableau de Décisions - Preprocessing
## Projet ML : Prédiction des Tempêtes Géomagnétiques (Aurora)

**Auteurs :** AMEZIANE Oumaima, ROHAND Douae, MOHITO Raihana  
**Phase 2 :** Nettoyage, Transformation & Feature Engineering

---

## 1. Valeurs Manquantes

| Variable | Taux NaN | Stratégie | Justification |
|---|---|---|---|
| Toutes (15 colonnes) | 0.0% | Aucune action | Dataset OMNI2 de la NASA : données harmonisées et nettoyées en amont. Confirmé par l'EDA. |

---

## 2. Doublons et Incohérences

| Vérification | Résultat | Action |
|---|---|---|
| Doublons exacts (toutes colonnes) | 0 | Aucune |
| Timestamps dupliqués | 0 | Aucune |
| `solar_wind_speed` hors [200, 2000] km/s | 0 | Aucune |
| `solar_wind_density` négative | 0 | Aucune |
| `solar_wind_pressure` négative | 0 | Aucune |
| Timestamps hors 2019-2023 | 0 | Aucune |
| Valeurs hors {0,1} dans binaires | 0 | Aucune |
| Incohérence `bz_negative` vs `bz_component` | 0 | Aucune |

---

## 3. Outliers

> **Principe :** Dans le domaine de la météorologie spatiale, les valeurs extrêmes sont les plus informatives. Les supprimer équivaudrait à effacer les exemples les plus représentatifs des tempêtes majeures.

| Variable | Méthode | Outliers détectés (IQR) | Décision | Justification |
|---|---|---|---|---|
| `solar_wind_speed` | IQR + Z-score | Oui (691 lignes, 1.60%) | **Conservation** | **51.2%** de tempêtes parmi ses outliers (6× le taux global), éruptions solaires majeures |
| `solar_wind_density` | IQR + Z-score | Oui (2218 lignes, 5.13%) | **Conservation** | **11.5%** de tempêtes parmi ses outliers, pics de densité associés aux éjections de masse coronale |
| `bz_component` | IQR + Z-score | Oui (2064 lignes, 4.78%) | **Conservation** | **25.5%** de tempêtes parmi ses outliers (3× le taux global), reconnexion magnétique intense |
| `solar_wind_pressure` | IQR + Z-score | Oui (2507 lignes, 5.80%) | **Conservation** | **25.5%** de tempêtes parmi ses outliers (3× le taux global), choc magnétosphérique |
| `bz_min_3h` | IQR + Z-score | Oui (2090 lignes, 4.84%) | **Conservation** | **26.7%** de tempêtes parmi ses outliers (3× le taux global), minimum glissant de `bz_component` |
| `dst_index` | IQR + Z-score | Oui (1751 lignes, 4.05%) | **Conservation** | **49.5%** de tempêtes parmi ses outliers (6× le taux global), Dst < -50 nT = définition officielle d'une tempête |

**Conséquence sur le scaling :** L'ensemble des outliers étant conservés, le `RobustScaler` (basé sur médiane et IQR, insensible aux valeurs extrêmes) est choisi plutôt que le `StandardScaler` (basé sur moyenne et écart-type, fortement perturbé par les outliers).

---

## 4. Encodage des Variables Catégorielles

| Variable | Cardinalité | Type | Technique | Colonnes créées | Justification |
|---|---|---|---|---|---|
| `season` | 4 (hiver, printemps, été, automne) | Nominale | **One-Hot Encoding** | 4 | Variable nominale sans ordre naturel. Cardinalité < 15. L'EDA montre que la saison est discriminante (automne : 12.57% vs été : 4.22%). |
| `hour_interval` | 8 créneaux de 3h | Nominale | **One-Hot Encoding** | 8 | Variable nominale sans ordre naturel. L'EDA montre un taux de tempête uniforme (~8.5% sur tous les créneaux), mais on conserve la feature pour ne pas biaiser le modèle. |
| `bz_negative` | 2 ({0, 1}) | Binaire | **Aucune transformation** | — | Déjà encodée en binaire. |
| `is_solar_maximum` | 2 ({0, 1}) | Binaire | **Aucune transformation** | — | Déjà encodée en binaire. |
---

## 5. Normalisation des Variables Numériques

**Scaler choisi : `RobustScaler`** pour toutes les variables numériques continues.

| Variable | Scaler | Justification |
|---|---|---|
| `solar_wind_speed` | RobustScaler | Outliers valides conservés (51.2% de tempêtes parmi ses outliers) |
| `solar_wind_density` | RobustScaler | Outliers valides conservés (11.5% de tempêtes parmi ses outliers) |
| `bz_component` | RobustScaler | Outliers valides conservés (25.5% de tempêtes parmi ses outliers) |
| `solar_wind_pressure` | RobustScaler | Outliers valides conservés (25.5% de tempêtes parmi ses outliers) |
| `bz_min_3h` | RobustScaler | Outliers valides conservés (26.7% de tempêtes parmi ses outliers) |
| `dst_index` | RobustScaler | Outliers valides conservés (49.5% de tempêtes parmi ses outliers) |
| `sin_month`, `cos_month` | Aucun | Déjà dans [-1.0, 1.0] |
| `bz_negative`, `is_solar_maximum` | Aucun | Binaire {0, 1} |
| `month` | Supprimée | Redondante avec `sin_month` et `cos_month` |

> **Note Data Leakage :** Dans le pipeline officiel, le `RobustScaler` sera **fitté uniquement sur `X_train`** puis appliqué à `X_val` et `X_test`, conformément aux bonnes pratiques anti-leakage.
---

## 6. Multicolinéarité

| Paire | Corrélation | Action |
|---|---|---|
| `solar_wind_pressure` & `solar_wind_density` | r = 0.815 |**Conservation des deux** - Supprimer une feature maintenant serait prématuré : les arbres (Random Forest, XGBoost) sont insensibles à la multicolinéarité et choisiront naturellement la plus utile, et la régression logistique la gère via la régularisation L2. L'importance des features en Phase 3 décidera si l'une est redondante. |
| `bz_component` & `bz_min_3h` | r < 0.8 (non confirmé) | **Conservation** - L'EDA n'a pas détecté de corrélation > 0.8 entre ces deux features. |

---

## 7. Feature Engineering
| Nouvelle Feature | Type | Formule | Justification Métier | Corrélation avec is_storm |
|---|---|---|---|---|
| `bz_dst_interaction` | Feature d'interaction | `bz_component × dst_index` | Une tempête se produit quand Bz est négatif ET que le Dst chute simultanément. Le produit capture cette co-occurrence que les features seules ne voient pas. | 0.056 > \|r\| = 0.017 de bz_component seul |
| `dst_rate_change` | Feature temporelle (diff) | `dst_index.diff(periods=3)` | La vitesse de chute du Dst est un indicateur d'alarme : un Dst qui chute rapidement est plus significatif qu'un Dst stable à valeur basse. Capture la dynamique temporelle du système. | **-0.016 (Vitesse)** : Montre si la situation change vite, ce qui aide à prévenir tôt. |

---

## 8. Colonnes Supprimées

| Colonne | Raison de suppression |
|---|---|
| `timestamp` | Index temporel, non utilisable comme feature numérique brute. L'information temporelle est capturée par `sin_month`, `cos_month` et `season`. |
| `month` | Redondant avec `sin_month` et `cos_month` qui encodent la même information de manière cyclique et continue, plus adaptée aux modèles ML. |

---

## 10. Récapitulatif par Variable (Synthèse Spécification)

Ce tableau récapitule l'action effectuée pour chaque variable du dataset initial, conformément aux exigences du cahier des charges.

| Variable | Action effectuée | Pourquoi ? (Mots simples) |
|---|---|---|---|
| `timestamp` | **Suppression** | Pas utile pour les calculs. On utilise déjà le mois et l'heure à la place. |
| `solar_wind_speed` | **Changement d'échelle** | On garde les valeurs fortes car ce sont elles qui montrent les grosses tempêtes. |
| `solar_wind_density` | **Changement d'échelle** | On garde les pics de densité car c'est là que le soleil "souffle" le plus fort. |
| `bz_component` | **Changement d'échelle** | On garde les valeurs extrêmes car elles montrent quand le champ magnétique change. |
| `solar_wind_pressure` | **Changement d'échelle** | On garde les chocs forts sur la Terre. |
| `bz_min_3h` | **Changement d'échelle** | On garde les moments où le champ magnétique est le plus bas. |
| `dst_index` | **Changement d'échelle** | C'est la mesure principale pour dire s'il y a une tempête ou non. |
| `month` | **Suppression** | Déjà remplacé par des versions mathématiques plus faciles à lire pour l'ordinateur. |
| `sin_month` | **Conservation** | Aide l'ordinateur à comprendre les saisons (été, hiver, etc.). |
| `cos_month` | **Conservation** | Aide l'ordinateur à comprendre les saisons. |
| `season` | **Transformation** | Transformé en 4 colonnes (printemps, été, automne, hiver) pour plus de clarté. |
| `hour_interval` | **Transformation** | Découpé en tranches d'heures pour voir si le moment de la journée compte. |
| `bz_negative` | **Conservation** | Dit simplement si le champ magnétique est du bon côté pour une tempête (Oui/Non). |
| `is_solar_maximum` | **Conservation** | Dit si le Soleil est dans sa période de grande activité (tous les 11 ans). |
| `bz_dst_interaction` | **Nouveau calcul** | Mélange de deux mesures pour voir quand les conditions de tempête sont réunies. |
| `dst_rate_change` | **Nouveau calcul** | Regarde si la tempête arrive vite ou doucement. |
| `is_storm` | **Conservation** | C'est ce que l'on veut deviner (Tempête : Oui ou Non). |

---

