# Data – Indice Pollution + Météo

## Démarrage rapide

### En local (Python)

```bash
# Depuis la racine du repo
pip install -r data/requirements.txt
python3 -m uvicorn data.api:app --reload --port 8000
```

### Avec Docker

```bash
# Depuis le dossier data/
docker build -t data-service .
docker run -p 8000:8000 data-service
```

### Déploiement Azure (App Service)

| Champ | Valeur |
|-------|--------|
| Nom de l'image | `data-service` |
| Tag | `latest` |
| Port | `8000` |
| Variable d'environnement | `WEBSITES_PORT=8000` |
| Health check path | `/health` |

---

## Architecture globale

```
LCSQA (pollution)  ──┐
                      ├──► data-service (FastAPI) ──► backend (CRON) ──► BDD ──► front
Météo-France (SYNOP) ─┘
```

- **Data** : produit et expose les indices via cette API
- **Backend** : appelle l'API via CRON, stocke en BDD, expose au front
- **Front** : interagit uniquement avec le backend, jamais avec cette API directement
- **Infra** : héberge l'ensemble

---

## Intégration backend

### Schéma minimal de la BDD

Le backend doit stocker au minimum les champs suivants :

| Colonne        | Type      | Description                            |
|----------------|-----------|----------------------------------------|
| `station_id`   | varchar   | Identifiant unique de la station       |
| `station_name` | varchar   | Nom de la station                      |
| `lat`          | float     | Latitude WGS84                         |
| `lon`          | float     | Longitude WGS84                        |
| `date`         | timestamp | Horodatage ISO 8601 de la mesure       |
| `indice`       | float     | Indice final combiné, 0 à 100          |

Champs optionnels utiles : `indice_pollution`, `modificateur_meteo`, `synop_station_id`.

Contrainte d'unicité recommandée : `(station_id, date)` pour éviter les doublons lors des mises à jour.

### 1. Initialisation (à faire une seule fois)

Appeler `/init` au démarrage pour peupler la BDD avec les 10 derniers jours :

```
GET http://data-service:8000/init?days=10
```

Retourne la même structure que `/index`, tous jours confondus (~96 000 enregistrements).

### 2. Mise à jour en continu (CRON)

Les données pollution sont publiées **toutes les heures** par le LCSQA.
Configurer un CRON **toutes les heures** pour appeler :

```
GET http://data-service:8000/index?date=<YYYY-MM-DD>
```

Exemple de crontab (mise à jour toutes les heures) :

```cron
0 * * * * curl -s "http://data-service:8000/index?date=$(date +\%Y-\%m-\%d)" | <insérer dans BDD>
```

La réponse contient l'ensemble des stations pour la date demandée.
Insérer avec `ON CONFLICT (station_id, date) DO UPDATE` pour gérer les données partielles en cours de journée.

---

## Endpoints

### `GET /index`

Retourne l'indice combiné pour toutes les stations pour une date donnée.

**Paramètre**

| Nom    | Type   | Obligatoire | Description                        | Exemple      |
|--------|--------|-------------|------------------------------------|--------------|
| `date` | string | Non         | Date au format `YYYY-MM-DD`. Défaut : hier. | `2026-03-29` |

**Requête**

```
GET http://localhost:8000/index?date=2026-03-29
```

**Réponse `200 OK`**

```json
[
  {
    "station_id": "FR01011",
    "station_name": "Metz-Centre",
    "lat": 49.119442,
    "lon": 6.180833,
    "date": "2026-03-29T00:00:00",
    "indice": 42.3,
    "indice_pollution": 45.0,
    "modificateur_meteo": 0.94,
    "synop_station_id": "07083"
  },
  ...
]
```

**Champs de la réponse**

| Champ                | Type    | Description                                                  |
|----------------------|---------|--------------------------------------------------------------|
| `station_id`         | string  | Code de la station pollution (ex: `FR01011`)                 |
| `station_name`       | string  | Nom lisible de la station                                    |
| `lat`                | float   | Latitude WGS84                                               |
| `lon`                | float   | Longitude WGS84                                              |
| `date`               | string  | Timestamp ISO 8601 de la mesure                              |
| `indice`             | float   | **Indice final combiné, de 0 à 100**                         |
| `indice_pollution`   | float   | Sous-indice pollution seul (avant modificateur météo)        |
| `modificateur_meteo` | float   | Multiplicateur météo appliqué (0.5 → 1.5)                   |
| `synop_station_id`   | string  | ID de la station météo SYNOP associée (null si indisponible) |

**Interprétation de l'indice**

| Valeur      | Niveau          |
|-------------|-----------------|
| 0 – 25      | Bon             |
| 26 – 50     | Moyen           |
| 51 – 75     | Dégradé         |
| 76 – 100    | Mauvais         |

---

### `GET /init`

Retourne l'historique des N derniers jours. **À appeler une seule fois** pour initialiser la BDD.

**Paramètre**

| Nom    | Type | Obligatoire | Description                          | Défaut |
|--------|------|-------------|--------------------------------------|--------|
| `days` | int  | Non         | Nombre de jours à récupérer (1–30)   | `10`   |

**Requête**

```
GET http://localhost:8000/init?days=10
```

**Réponse `200 OK`** : même structure que `/index`, tous jours confondus.

> Attention : cet endpoint déclenche N appels pipeline. Prévoir ~2–5 min pour 10 jours.

---

### `GET /forecast`

Prévisions de l'indice par régression linéaire simple.

**Paramètres**

| Nom        | Type | Obligatoire | Description                                   | Défaut |
|------------|------|-------------|-----------------------------------------------|--------|
| `date`     | string | Non       | Date de référence `YYYY-MM-DD`. Défaut : hier | —      |
| `lookback` | int  | Non         | Jours d'historique utilisés (2–30)            | `7`    |
| `horizon`  | int  | Non         | Jours à prévoir (1–7)                         | `3`    |

**Requête**

```
GET http://localhost:8000/forecast?date=2026-03-29&lookback=7&horizon=3
```

**Réponse `200 OK`**

```json
[
  {
    "station_id": "FR01011",
    "station_name": "Metz-Centre",
    "lat": 49.119442,
    "lon": 6.180833,
    "date": "2026-04-01",
    "indice_prevu": 38.5,
    "tendance": -1.2
  }
]
```

`tendance` : variation de l'indice par jour (négatif = amélioration, positif = dégradation).

---

### `GET /health`

Health check — vérifie que l'API est opérationnelle.

```
GET http://localhost:8000/health
```

```json
{ "status": "ok" }
```

---

## Documentation interactive

FastAPI génère automatiquement un Swagger UI accessible à :

```
http://localhost:8000/docs
```

---

## Architecture des fichiers

```
data/
├── api.py                  # Endpoints FastAPI (point d'entrée)
├── extract_pollution.py    # Fetch + nettoyage données pollution LCSQA
├── extract_synop.py        # Fetch + nettoyage données météo SYNOP
├── spatial_join.py         # Jointure géospatiale Haversine pollution ↔ SYNOP
├── index_calculator.py     # Calcul de l'indice combiné 0-100
├── forecast.py             # Prévisions par régression linéaire
├── requirements.txt        # Dépendances Python
├── Dockerfile              # Image Docker
└── README.md               # Cette documentation
```

---

## Fréquence des données

Les données pollution sont mises à jour **toutes les heures** par le LCSQA.
Le pipeline traite ~514 stations de pollution et ~187 stations SYNOP sur la France entière.
