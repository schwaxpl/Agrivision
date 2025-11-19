---
title: Agrivision API
emoji: 🌱
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Agrivision - API d'Enrichissement de Scénarios Pédagogiques

## 🌱 Description

Agrivision est une API intelligente qui enrichit automatiquement les scénarios pédagogiques agricoles en utilisant des articles scientifiques récents et l'intelligence artificielle.

## 🚀 Fonctionnalités

- **Enrichissement automatique** : Analyse des articles scientifiques et intégration de nouvelles découvertes
- **API REST complète** : Interface simple et documentée
- **Traitement asynchrone** : Gestion des tâches longues en arrière-plan
- **Export multiple** : JSON et Markdown
- **Téléchargement ZIP** : Tous les résultats d'une tâche dans un seul fichier

## 📖 Utilisation

### Accès à l'API

- **Interface de documentation** : `/docs`
- **Vérification de santé** : `/health`
- **Liste des tâches** : `/tasks`

### Endpoints principaux

1. **POST /enrich** - Lancer un enrichissement
2. **GET /tasks/{task_id}** - Vérifier le statut d'une tâche  
3. **GET /download/{task_id}** - Télécharger les résultats en ZIP

### Exemple d'utilisation

```python
import requests

# Lancer un enrichissement
response = requests.post("/enrich", json={
    "scenario_json": "input/scenario.json",
    "data_directory": "data",
    "output_format": "markdown"
})

task_id = response.json()["task_id"]

# Vérifier le statut
status = requests.get(f"/tasks/{task_id}")

# Télécharger les résultats
if status.json()["status"] == "completed":
    results = requests.get(f"/download/{task_id}")
```

## 🔧 Configuration

### Variables d'environnement requises

- `OPENAI_API_KEY` : Clé API OpenAI pour l'enrichissement intelligent

### Structure des fichiers

- `input/scenario.json` : Scénario pédagogique à enrichir
- `data/` : Articles scientifiques au format Markdown
- `output/task_{id}/` : Résultats organisés par tâche

## 📊 Format des données

### Scénario d'entrée (JSON)
```json
{
  "scenarios": [
    {
      "scenario_title": "Formation en Agriculture",
      "target_audience": "Agriculteurs",
      "global_objectives": ["Objectif 1", "Objectif 2"],
      "days": [...]
    }
  ]
}
```

### Articles scientifiques (Markdown)
- Fichiers `.md` dans le dossier `data/`
- Structurés avec des titres et sections
- Contenu scientifique récent et pertinent

## 🏗️ Architecture

- **FastAPI** : Framework web moderne et rapide
- **Pydantic** : Validation des données
- **OpenAI** : Modèles de langage pour l'enrichissement
- **Uvicorn** : Serveur ASGI haute performance

## 📝 Licence

MIT License - Voir le fichier LICENSE pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir des issues ou des pull requests.

---

*Développé avec ❤️ pour l'amélioration de la formation agricole*