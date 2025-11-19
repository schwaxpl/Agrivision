# Guide de Déploiement - Hugging Face Spaces

## 📋 Prérequis

1. **Compte Hugging Face** : Créer un compte sur [huggingface.co](https://huggingface.co)
2. **Repository Git** : Code source prêt dans un repository Git
3. **Clé API OpenAI** : Pour l'enrichissement intelligent

## 🚀 Étapes de Déploiement

### 1. Créer un nouveau Space

1. Aller sur [huggingface.co/spaces](https://huggingface.co/spaces)
2. Cliquer sur "Create new Space"
3. Configurer :
   - **Name** : `agrivision-api`
   - **License** : `MIT`
   - **SDK** : `Docker`
   - **Hardware** : `CPU basic` (ou plus selon les besoins)

### 2. Configuration du Repository

Fichiers essentiels à inclure :

```
├── Dockerfile                 # Configuration Docker
├── requirements.txt           # Dépendances Python
├── README.md                  # Documentation (utiliser README_HF.md)
├── api.py                     # Application FastAPI principale
├── start_hf_spaces.py         # Script de démarrage
├── src/                       # Code source de l'application
├── data/                      # Exemples d'articles scientifiques
├── input/                     # Exemples de scénarios
└── .env.hf_spaces            # Configuration d'environnement
```

### 3. Configuration des Variables d'Environnement

Dans l'interface Hugging Face Spaces, ajouter les secrets :

- **`OPENAI_API_KEY`** : Votre clé API OpenAI
- **`OPENAI_API_BASE`** : `https://api.openai.com/v1` (optionnel)

### 4. Dockerfile pour Hugging Face

Le Dockerfile doit :
- Exposer le port 7860
- Installer toutes les dépendances
- Configurer l'utilisateur non-root
- Démarrer l'application correctement

### 5. Test du Déploiement

Une fois déployé, l'API sera accessible à :
- **Interface principale** : `https://username-agrivision-api.hf.space`
- **Documentation** : `https://username-agrivision-api.hf.space/docs`
- **Health Check** : `https://username-agrivision-api.hf.space/health`

## 🔧 Configuration Recommandée

### Hardware
- **CPU basic** : Pour tests et usage léger
- **CPU upgrade** : Pour usage intensif
- **GPU** : Optionnel (l'API utilise l'API OpenAI, pas de modèles locaux)

### Secrets (Variables d'Environnement)
```
OPENAI_API_KEY=sk-...
LOG_LEVEL=info
ENVIRONMENT=production
```

### Limites Recommandées
- **Timeout** : 30 minutes par tâche
- **Taille des fichiers** : 50 MB max
- **Tâches simultanées** : 5 max

## 📝 Fichiers de Test

Pour tester l'API une fois déployée, utiliser :

### Scénario de Test (`input/scenario.json`)
```json
{
  "scenarios": [
    {
      "scenario_title": "Formation Agriculture Durable",
      "target_audience": "Agriculteurs",
      "global_objectives": ["Apprendre l'agriculture durable"],
      "days": [...]
    }
  ]
}
```

### Article de Test (`data/test_article.md`)
```markdown
# Nouvelles Techniques Agricoles

## Techniques Innovantes

Des études récentes montrent que...

## Conclusion

Ces innovations permettent...
```

## 🧪 Tests de Validation

Utiliser le script `test_deployment.py` pour valider :

```bash
python test_deployment.py https://username-agrivision-api.hf.space
```

## ⚠️ Points d'Attention

1. **Sécurité** : Ne jamais exposer les clés API dans le code
2. **Performance** : Surveiller l'usage CPU et mémoire
3. **Logs** : Vérifier les logs en cas d'erreur
4. **Timeout** : Configurer des timeouts appropriés
5. **Stockage** : Les fichiers sont temporaires, pas de persistance

## 🔄 Mise à Jour

Pour mettre à jour l'application :
1. Pousser les modifications vers le repository Git
2. Hugging Face redéploiera automatiquement
3. Vérifier le bon fonctionnement avec les tests

## 📞 Support

En cas de problème :
- Consulter les logs dans l'interface Hugging Face
- Vérifier la configuration des variables d'environnement
- Tester localement avec Docker avant déploiement