# Projet ML — Prédiction des Aurores Boréales

## Informations générales

- **Module** : Machine Learning — 2ème année Cycle Ingénieurs GI
- **Phase** : Phase 1 — Cadrage et constitution du dataset
- **Année** : 2025-2026

---

## Sujet du projet

**Prédire si une aurore boréale sera visible**, en se basant sur les données de l'activité géomagnétique et du vent solaire.

---

## Type de problème ML

Classification supervisée **binaire** :

- Classe 0 → aurore non visible (activité géomagnétique faible, Kp < 5)
- Classe 1 → aurore visible (activité géomagnétique forte, Kp ≥ 5)

---

## Sources de données

### Source 1 — NOAA Space Weather Prediction Center
- **URL** : https://www.swpc.noaa.gov
- **Données** : Indice Kp historique (toutes les 3 heures, depuis 1994)
- **Quota** : Accès libre par fichiers, aucune clé requise
- **Format** : Fichiers JSON/texte par année

### Source 2 — NASA DONKI API
- **URL** : https://api.nasa.gov / https://kauai.ccmc.gsfc.nasa.gov/DONKI
- **Données** : Événements du vent solaire (vitesse, densité, composante Bz)
- **Quota** : 1000 requêtes/heure avec clé gratuite (api.nasa.gov)
- **Format** : JSON

---

## Variable cible

```
aurora_visible = 1  si  Kp ≥ 5  (aurore probable)
aurora_visible = 0  si  Kp < 5  (aurore improbable)
```

Cette variable est construite à partir d'une définition **scientifique réelle** — non inventée artificiellement.

---

## Features du dataset (11 features)

### Features brutes

| Feature | Source | Type | Description |
|---|---|---|---|
| kp_index | NOAA | Numérique | Indice géomagnétique principal (0 à 9) |
| ap_index | NOAA | Numérique | Indice dérivé du Kp (version linéaire) |
| month | NOAA | Catégoriel | Mois de l'année (1 à 12) |
| season | NOAA | Catégoriel | Saison (hiver/printemps/été/automne) |
| hour_interval | NOAA | Catégoriel | Tranche horaire (0h-3h, 3h-6h, etc.) |
| solar_wind_speed | NASA DONKI | Numérique | Vitesse du vent solaire (km/s) |
| solar_wind_density | NASA DONKI | Numérique | Densité du vent solaire |
| bz_component | NASA DONKI | Numérique | Composante Bz du champ magnétique |

### Features créées par feature engineering

| Feature | Type | Description |
|---|---|---|
| is_solar_maximum | Catégoriel | Phase du cycle solaire de 11 ans (0 ou 1) |
| kp_previous_interval | Numérique | Valeur Kp de la période précédente |
| bz_negative | Catégoriel | 1 si Bz est négatif (condition favorable aux aurores) |

---

## Caractéristiques du dataset

| Critère | Objectif | Notre dataset |
|---|---|---|
| Type de tâche | Classification supervisée | ✅ Binaire |
| Taille totale | ≥ 10 000 lignes | ✅ ~14 600 lignes (5 ans × 365 jours × 8 mesures) |
| Nombre de features | ≥ 8 | ✅ 11 features |
| Classe minoritaire | Entre 5% et 25% | ✅ ~10-15% (jours Kp ≥ 5 naturellement rares) |
| Types de variables | Numériques + catégorielles | ✅ 6 numériques + 5 catégorielles |

---

## Objectifs métiers

**Objectif principal** : Alerter les observatoires, agences spatiales et opérateurs de satellites **3 heures à l'avance** lorsqu'une aurore boréale (et donc une tempête géomagnétique) est probable, afin de :
- Déclencher les protocoles de protection des satellites
- Optimiser les sessions d'observation scientifique
- Anticiper les perturbations des réseaux électriques

---

## Tableau de traduction Métier → ML

| Objectif métier | Objectif ML | Métrique principale |
|---|---|---|
| Détecter 80% des aurores probables | Maximiser le recall sur la classe 1 | Recall ≥ 0.80 |
| Éviter trop de fausses alertes inutiles | Maintenir une précision acceptable | Precision ≥ 0.50 |
| Performance globale sur classe rare | Mesurer la qualité sur la classe minoritaire | F1-score ou PR-AUC |

---

## Analyse du coût asymétrique

### Faux négatif (aurore prédite absente, mais elle arrive)
- Satellite non protégé exposé à une tempête géomagnétique
- Coût estimé : **des centaines de millions de dollars** en dommages matériels
- Opportunités d'observation scientifique ratées

### Faux positif (aurore prédite présente, mais elle n'arrive pas)
- Un observatoire mobilisé inutilement
- Coût estimé : **quelques heures de travail perdues** (faible)

### Conclusion
Le faux négatif coûte infiniment plus cher → on **privilégie le Recall** comme métrique principale.
L'Accuracy et le ROC-AUC seuls sont refusés comme métriques principales (trop optimistes sur données déséquilibrées).

---

## Structure du projet

```
projet-aurores/
│
├── src/
│   └── data_collection.py       # Script de collecte reproductible
│
├── data/
│   ├── dataset.csv              # Dataset final (≥ 10 000 lignes)
│   └── sample.csv               # Extrait de 100 lignes
│
├── notebooks/
│   └── 01_discovery.ipynb       # Notebook exploratoire initial
│
├── cadrage.md                   # Fiche de cadrage officielle
├── DATASET.md                   # Documentation du dataset
└── PROJET_AURORES.md            # Ce fichier
```

---

## Vérification des pièges à éviter (checklist prof)

| Piège | Notre situation |
|---|---|
| API avec quota insuffisant (100 req/jour) | ✅ NOAA accès libre par fichiers, NASA 1000 req/heure |
| Variable cible inventée artificiellement | ✅ Kp ≥ 5 est une définition scientifique réelle |
| Déséquilibre forcé artificiellement | ✅ Les jours Kp ≥ 5 sont naturellement rares (~10-15%) |
| Sujet naturellement équilibré | ✅ Déséquilibre naturel confirmé |
| Moins de 10 000 lignes | ✅ 5 ans de données = ~14 600 lignes |
| Moins de 8 features | ✅ 11 features disponibles |
| Métrique principale inadaptée | ✅ Recall comme métrique principale, justifié par l'asymétrie des coûts |
