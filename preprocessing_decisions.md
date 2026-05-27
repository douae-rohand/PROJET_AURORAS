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
| `bz_dst_interaction` | Feature d'interaction | `bz_component × dst_index` | Une tempête se produit quand Bz est négatif ET que le Dst chute simultanément. Le produit capture cette co-occurrence que les features seules ne voient pas. | **0.056** > \|r\| = 0.017 de bz_component seul |
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

| Variable | Action effectuée | Pourquoi ? |
|---|---|---|
| `timestamp` | **Suppression** | Index temporel brut inutilisable par un modèle ML. L'information temporelle est déjà capturée par `sin_month`, `cos_month` et `season`. |
| `solar_wind_speed` | **RobustScaler** | 51.2% des outliers sont des tempêtes (6× le taux global) - valeurs extrêmes conservées car porteuses du signal le plus fort. |
| `solar_wind_density` | **RobustScaler** | Outliers valides conservés (pics = éjections de masse coronale). RobustScaler choisi pour ne pas écraser ces valeurs extrêmes. |
| `bz_component` | **RobustScaler** | 25.5% des outliers sont des tempêtes. Les valeurs très négatives représentent la reconnexion magnétique - signal physique critique. |
| `solar_wind_pressure` | **RobustScaler** | 25.5% des outliers sont des tempêtes. Les pics de pression correspondent aux chocs magnétosphériques lors des tempêtes majeures. |
| `bz_min_3h` | **RobustScaler** | 26.7% des outliers sont des tempêtes. Minimum glissant de `bz_component` sur 3h - même justification physique. |
| `dst_index` | **RobustScaler** | 49.5% des outliers sont des tempêtes (6× le taux global). Dst < -50 nT = définition officielle d'une tempête géomagnétique. |
| `month` | **Suppression** | Redondant avec `sin_month` et `cos_month` qui encodent le même mois de manière cyclique et continue - suppression pour redondance, pas pour manque de signal. |
| `sin_month` | **Conservation** | Encodage cyclique du mois - permet au modèle de comprendre que décembre et janvier sont consécutifs. |
| `cos_month` | **Conservation** | Complément de `sin_month` pour un encodage cyclique complet du mois. |
| `season` | **One-Hot Encoding** | Variable nominale transformée en 4 colonnes binaires. L'EDA confirme son pouvoir discriminant : automne 12.57% vs été 4.22% de tempêtes. |
| `hour_interval` | **One-Hot Encoding** | Variable nominale transformée en 8 colonnes binaires. Conservée malgré un signal faible dans l'EDA pour laisser le modèle évaluer son utilité. |
| `bz_negative` | **Conservation** | Déjà binaire {0,1}. Indique si la reconnexion magnétique est active — information directement exploitable. |
| `is_solar_maximum` | **Conservation** | Déjà binaire {0,1}. Capture le cycle solaire de 11 ans - contexte d'activité solaire globale. |
| `bz_dst_interaction` | **Nouvelle feature** | Produit `bz_component × dst_index` - capture la co-occurrence des deux signaux forts qu'aucune feature seule ne voit. |
| `dst_rate_change` | **Nouvelle feature** | Variation de `dst_index` sur 3h — un Dst qui chute rapidement est un indicateur d'alarme plus fort qu'un Dst stable à valeur basse. |
| `is_storm` | **Conservation** | Variable cible - 1 si tempête à T+6h, 0 sinon. Ratio 8.5% / 91.5%. |
---

