# Agrivision - Traitement d'Articles Scientifiques

Une architecture complète basée sur LangChain et Pydantic pour traiter des résumés d'articles scientifiques en markdown et les convertir en objets structurés.

*Projet développé dans le cadre du Hackathon Agreen Defi Tech élevage 2025*

## 🚀 Caractéristiques

- **Traitement intelligent** : Utilise LangChain et des modèles de langage pour extraire des informations structurées
- **Modèle Pydantic** : Structure de données robuste et validée pour les articles scientifiques
- **Formats multiples** : Support des sorties JSON, CSV et texte
- **Architecture modulaire** : Code organisé en composants réutilisables
- **Interface CLI** : Traitement en ligne de commande simple et efficace
- **Gestion d'erreurs** : Mécanisme de retry et rapports détaillés

## 📁 Structure du Projet

```
Agrivision/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── scientific_article.py     # Modèle Pydantic pour articles
│   ├── loaders/
│   │   ├── __init__.py
│   │   └── markdown_loader.py        # Chargement des fichiers markdown
│   ├── processors/
│   │   ├── __init__.py
│   │   └── scientific_article_processor.py  # Traitement LangChain
│   └── __init__.py
├── main.py                           # Script principal
├── requirements.txt                  # Dépendances Python
├── pyproject.toml                    # Configuration Poetry
├── .env.example                      # Variables d'environnement
├── .gitignore
└── README.md
```

## 🛠 Installation

### 1. Cloner le projet et installer les dépendances

```bash
# Avec pip
pip install -r requirements.txt

# Ou avec Poetry (recommandé)
poetry install
```

### 2. Configuration

```bash
# Copier le fichier d'exemple d'environnement
cp .env.example .env

# Éditer le fichier .env et ajouter votre clé API OpenAI
OPENAI_API_KEY=your_openai_api_key_here
```

## 📖 Utilisation

### Interface en ligne de commande

```bash
# Traiter un fichier unique
python main.py path/to/article.md

# Traiter tous les fichiers markdown d'un répertoire
python main.py path/to/articles/ --format json

# Options avancées
python main.py input/ \
  --output-dir output \
  --format csv \
  --model mistral-large-latest \
  --temperature 0.2 \
  --pattern "*.md"
```

### Utilisation programmatique

```python
from src.loaders import MarkdownLoader
from src.processors import ScientificArticleProcessor
from src.models import ScientificArticle

# Initialisation
loader = MarkdownLoader()
processor = ScientificArticleProcessor(model_name="mistral-large-latest")

# Traitement d'un fichier
document = loader.load_file("article.md")
preprocessed = loader.preprocess_content(document)
article = processor.process_document(preprocessed)

print(f"Titre: {article.title}")
print(f"Auteurs: {', '.join(article.authors)}")
```

## 📊 Modèle de Données

L'objet `ScientificArticle` inclut les champs suivants :

- **title** : Titre de l'article
- **authors** : Liste des auteurs
- **abstract** : Résumé/abstract complet
- **keywords** : Mots-clés associés
- **publication_date** : Date de publication
- **journal** : Nom du journal/revue
- **doi** : Digital Object Identifier
- **research_field** : Domaine de recherche principal
- **methodology** : Méthodologie utilisée
- **main_findings** : Principales découvertes
- **confidence_score** : Score de confiance de l'extraction (0.0-1.0)

## 🔧 Options de Configuration

### Variables d'environnement

- `MISTRAL_API_KEY` : Clé API Mistral (requis)
- `DEFAULT_MODEL` : Modèle par défaut
- `DEFAULT_TEMPERATURE` : Température par défaut
- `OUTPUT_DIR` : Répertoire de sortie
- `MAX_RETRIES` : Nombre maximum de tentatives

### Options CLI

```
positional arguments:
  input_path           Chemin vers le fichier ou répertoire à traiter

optional arguments:
  --output-dir, -o     Répertoire de sortie (défaut: output)
  --format, -f         Format de sortie: json, csv, txt (défaut: json)
  --model             Modèle LLM à utiliser (défaut: mistral-large-latest)
  --temperature       Température du modèle (défaut: 0.1)
  --pattern           Pattern de fichiers pour les répertoires (défaut: *.md)
  --no-recursive      Ne pas traiter récursivement les sous-répertoires
```

## 📄 Formats de Sortie

### JSON
Structure complète avec métadonnées de traitement

### CSV
Format tabulaire pour analyse de données

### TXT
Rapport lisible pour révision humaine

## 🎯 Exemple d'Utilisation Complète

```bash
# 1. Préparer les fichiers markdown d'articles
mkdir input
echo "# Mon Article\n\n**Auteurs**: Jean Dupont, Marie Martin\n\n**Résumé**: Cette étude examine..." > input/article1.md

# 2. Traiter les articles
python main.py input/ --format json --model mistral-large-latest

# 3. Consulter les résultats
ls output/
cat output/articles_*.json
```

## 🔄 Développement et Extension

### Modifier le modèle Pydantic

Éditez `src/models/scientific_article.py` pour ajouter de nouveaux champs :

```python
class ScientificArticle(BaseModel):
    # Champs existants...
    
    # Nouveaux champs
    funding_sources: List[str] = Field(default_factory=list)
    ethical_approval: Optional[str] = None
    study_duration: Optional[str] = None
```

### Personnaliser le prompt

Modifiez `src/processors/scientific_article_processor.py` :

```python
def _create_prompt_template(self) -> PromptTemplate:
    template = """
    Votre nouveau prompt personnalisé...
    {text}
    {format_instructions}
    """
    # ...
```

## 🧪 Tests et Qualité

```bash
# Tests
pytest

# Formatage du code
black .

# Vérification de style
flake8 .

# Type checking
mypy src/
```

## 📋 Prérequis

- Python 3.9+
- Clé API Mistral
- Connexion Internet pour les appels API

## 🤝 Contribution

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📝 Licence

MIT License

## 🆘 Support

Pour toute question ou problème, ouvrez une issue sur le repository GitHub.

---

**Note** : Ce projet est une architecture de base qui peut être étendue selon vos besoins spécifiques. N'hésitez pas à adapter les modèles, prompts et fonctionnalités selon vos cas d'usage.
