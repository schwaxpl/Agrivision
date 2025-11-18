#!/usr/bin/env python3
"""
Script de test rapide pour vérifier que l'architecture fonctionne correctement.

Usage:
    python test_setup.py
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test que tous les modules peuvent être importés."""
    print("🔄 Test des imports...")
    
    try:
        from src.models import ScientificArticle
        from src.loaders import MarkdownLoader
        from src.processors import ScientificArticleProcessor
        from src.config import config
        print("✅ Tous les imports fonctionnent")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def test_pydantic_model():
    """Test du modèle Pydantic."""
    print("🔄 Test du modèle Pydantic...")
    
    try:
        from src.models import ScientificArticle
        
        # Création d'un article de test
        article = ScientificArticle(
            title="Article de test",
            authors=["Dr. Test", "Prof. Exemple"],
            abstract="Ceci est un résumé de test pour vérifier que le modèle fonctionne correctement.",
            keywords=["test", "pydantic", "validation"],
            research_field="Intelligence Artificielle",
            confidence_score=0.95
        )
        
        # Vérification des données
        assert article.title == "Article de test"
        assert len(article.authors) == 2
        assert article.confidence_score == 0.95
        
        # Test de conversion en dict
        article_dict = article.to_dict()
        assert "title" in article_dict
        assert "authors" in article_dict
        
        print("✅ Modèle Pydantic fonctionne correctement")
        return True
        
    except Exception as e:
        print(f"❌ Erreur avec le modèle Pydantic: {e}")
        return False

def test_markdown_loader():
    """Test du loader markdown."""
    print("🔄 Test du loader markdown...")
    
    try:
        from src.loaders import MarkdownLoader
        
        loader = MarkdownLoader()
        
        # Test avec le fichier d'exemple s'il existe
        example_file = Path("examples/article_exemple.md")
        if example_file.exists():
            document = loader.load_file(str(example_file))
            
            # Vérifications de base
            assert document.page_content is not None
            assert len(document.page_content) > 0
            assert "metadata" in str(type(document.metadata))
            
            # Test du prétraitement
            processed = loader.preprocess_content(document)
            assert processed.page_content is not None
            
            print("✅ Loader markdown fonctionne correctement")
            return True
        else:
            print("⚠️  Fichier d'exemple non trouvé, test partiel")
            return True
            
    except Exception as e:
        print(f"❌ Erreur avec le loader markdown: {e}")
        return False

def test_configuration():
    """Test de la configuration centralisée."""
    print("🔄 Test de la configuration centralisée...")
    
    try:
        from src.config import config
        
        # Vérification de la structure
        assert hasattr(config, 'DEFAULT_MODEL')
        assert hasattr(config, 'DEFAULT_TEMPERATURE')
        assert hasattr(config, 'MISTRAL_API_KEY')
        assert hasattr(config, 'OUTPUT_DIR')
        
        # Vérification des méthodes
        assert hasattr(config, 'validate')
        assert hasattr(config, 'get_model_config')
        assert hasattr(config, 'print_config')
        
        # Test de get_model_config
        model_config = config.get_model_config()
        assert 'model' in model_config
        assert 'temperature' in model_config
        
        print("✅ Configuration centralisée fonctionne")
        return True
        
    except Exception as e:
        print(f"❌ Erreur avec la configuration: {e}")
        return False

def test_environment():
    """Test de l'environnement."""
    print("🔄 Test de l'environnement...")
    
    # Vérification de Python
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 9:
        print(f"✅ Python {python_version.major}.{python_version.minor} détecté")
    else:
        print(f"⚠️  Python {python_version.major}.{python_version.minor} détecté (recommandé: 3.9+)")
    
    # Test de la configuration
    try:
        from src.config import config
        
        print(f"✅ Module de configuration chargé")
        
        if config.MISTRAL_API_KEY:
            print("✅ MISTRAL_API_KEY configurée")
        else:
            print("⚠️  MISTRAL_API_KEY non configurée (nécessaire pour l'exécution)")
        
        # Test de validation de la configuration
        if config.validate():
            print("✅ Configuration valide")
        else:
            print("⚠️  Configuration invalide")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur de configuration: {e}")
        return False

def test_file_structure():
    """Test de la structure des fichiers."""
    print("🔄 Test de la structure des fichiers...")
    
    expected_files = [
        "src/__init__.py",
        "src/config.py",
        "src/models/__init__.py",
        "src/models/scientific_article.py",
        "src/loaders/__init__.py",
        "src/loaders/markdown_loader.py",
        "src/processors/__init__.py",
        "src/processors/scientific_article_processor.py",
        "main.py",
        "requirements.txt",
        ".env.example"
    ]
    
    missing_files = []
    for file_path in expected_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Fichiers manquants: {', '.join(missing_files)}")
        return False
    else:
        print("✅ Structure de fichiers correcte")
        return True

def main():
    """Fonction principale de test."""
    print("🚀 Démarrage des tests de l'architecture Agrivision\n")
    
    tests = [
        ("Structure des fichiers", test_file_structure),
        ("Environnement", test_environment),
        ("Configuration", test_configuration),
        ("Imports", test_imports),
        ("Modèle Pydantic", test_pydantic_model),
        ("Loader Markdown", test_markdown_loader),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 50)
        success = test_func()
        results.append((test_name, success))
        
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSÉ" if success else "❌ ÉCHOUÉ"
        print(f"{test_name:<30} {status}")
        if success:
            passed += 1
    
    print(f"\n📈 Résumé: {passed}/{len(tests)} tests passés")
    
    if passed == len(tests):
        print("\n🎉 Tous les tests sont passés! L'architecture est prête.")
        print("\n💡 Prochaines étapes:")
        print("1. Configurer votre clé API Mistral dans .env")
        print("2. Tester avec: python main.py examples/article_exemple.md")
        return 0
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1

if __name__ == "__main__":
    exit(main())