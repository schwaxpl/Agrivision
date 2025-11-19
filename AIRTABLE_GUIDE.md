# Guide Intégration Airtable

## 🎯 Vue d'ensemble

Le système Agrivision peut maintenant synchroniser automatiquement des articles depuis votre base Airtable pour enrichir les scénarios pédagogiques.

## 📋 Prérequis

### 1. Base Airtable configurée
Votre base Airtable doit contenir une table avec la structure suivante :

| Champ | Type | Description |
|-------|------|-------------|
| `Date_article` | Date | Date de récupération/publication de l'article |
| `Support_cours` | Long text | Contenu de l'article au format Markdown |

### 2. Clé API Airtable
1. Aller sur https://airtable.com/developers/web/api/introduction
2. Créer un token personnel avec les permissions `data.records:read`
3. Noter votre clé API (commence par `pat...`)

### 3. ID de la base
1. Dans votre base Airtable, aller dans `Help` > `API Documentation`
2. L'ID de la base se trouve dans l'URL (commence par `app...`)

## ⚙️ Configuration

### Variables d'environnement
Ajoutez dans votre fichier `.env` :

```env
# Airtable Configuration
AIRTABLE_API_KEY=pat_votre_cle_api_ici
AIRTABLE_BASE_ID=app_votre_base_id_ici
AIRTABLE_TABLE_NAME=Article
```

## 🚀 Utilisation

### 1. Via l'API

**Synchronisation simple :**
```bash
POST /sync-airtable
{
  "data_directory": "data"
}
```

**Synchronisation avec nettoyage :**
```bash
POST /sync-airtable
{
  "data_directory": "data",
  "clean_before_sync": true
}
```

### 2. Via le script en ligne de commande

```bash
# Synchronisation simple
python sync_airtable.py

# Avec nettoyage
python sync_airtable.py --clean

# Vers un autre dossier
python sync_airtable.py --data-folder articles

# Avec clés spécifiques
python sync_airtable.py --api-key pat_xxx --base-id app_xxx
```

## 📁 Organisation des fichiers

Les articles sont sauvegardés dans le format :
```
data/
├── 20241119_recXXXXXXXX.md
├── 20241118_recYYYYYYYY.md
└── ...
```

**Format du nom :** `{date}_{airtable_id}.md`

**Contenu du fichier :**
```markdown
# Article Airtable - 20241119_recXXXXXXXX.md

**Date de l'article:** 2024-11-19
**ID Airtable:** recXXXXXXXX
**Récupéré le:** 2024-11-19 15:30:00

---

[Contenu de Support_cours]
```

## 🔄 Workflow complet

1. **Synchroniser les articles :**
   ```bash
   POST /sync-airtable
   ```

2. **Vérifier la tâche :**
   ```bash
   GET /tasks/{task_id}
   ```

3. **Enrichir le scénario :**
   ```bash
   POST /enrich
   {
     "scenario_json": "input/scenario.json",
     "data_directory": "data",
     "output_format": "markdown"
   }
   ```

4. **Télécharger les résultats :**
   ```bash
   GET /download/{task_id}
   ```

## 🛠️ Dépannage

### Erreurs communes

**"Clé API non trouvée"**
- Vérifiez que `AIRTABLE_API_KEY` est définie
- La clé doit commencer par `pat`

**"Base non trouvée"**
- Vérifiez `AIRTABLE_BASE_ID`
- L'ID doit commencer par `app`
- Vérifiez les permissions de la clé API

**"Table non trouvée"**
- Vérifiez `AIRTABLE_TABLE_NAME`
- Le nom doit correspondre exactement à votre table

**"Champs manquants"**
- Vérifiez que votre table a bien les champs :
  - `Date_article` (Type: Date)
  - `Support_cours` (Type: Long text)

### Debug

Activez le debug dans `.env` :
```env
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

## 📊 API Endpoints

### POST /sync-airtable
Synchronise les articles depuis Airtable

**Request:**
```json
{
  "data_directory": "data",
  "clean_before_sync": false
}
```

**Response:**
```json
{
  "task_id": "uuid-de-la-tache",
  "status": "pending",
  "message": "Synchronisation Airtable lancée..."
}
```

### GET /tasks/{task_id}
Vérifie le statut de la synchronisation

**Response lors du succès:**
```json
{
  "task_id": "uuid-de-la-tache",
  "status": "completed",
  "result": {
    "success": true,
    "articles_count": 15,
    "files_created": 15,
    "saved_files": ["data/20241119_rec1.md", ...],
    "duration_seconds": 3.5,
    "sync_time": "2024-11-19T15:30:00"
  }
}
```

## 🔒 Sécurité

- Ne jamais commiter les clés API dans le code
- Utiliser les variables d'environnement
- Limiter les permissions de la clé API Airtable
- Surveiller l'usage de l'API

## 📈 Limites

- **Rate limiting Airtable :** 5 requêtes/seconde
- **Taille des articles :** Pas de limite technique
- **Nombre d'articles :** Pas de limite (paginé automatiquement)

---

💡 **Astuce :** Utilisez `clean_before_sync: true` pour éviter les doublons lors des synchronisations régulières.