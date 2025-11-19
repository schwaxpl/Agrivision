#!/usr/bin/env python3
"""
Script de test rapide pour vérifier la connexion OpenAI.
"""

import os
import sys
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

def test_openai_connection():
    """Test de la connexion à l'API OpenAI."""
    
    print("🧪 TEST DE CONNEXION OPENAI")
    print("=" * 50)
    
    # Vérification de la clé API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY non configurée!")
        print("💡 Ajoutez votre clé API dans le fichier .env")
        return False
    
    print(f"✅ OPENAI_API_KEY configurée (se termine par ...{api_key[-4:]})")
    
    try:
        # Test d'import
        from langchain_openai import ChatOpenAI
        print("✅ Import langchain_openai réussi")
        
        # Test de création du modèle
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=100,
            openai_api_key=api_key
        )
        print("✅ Modèle ChatOpenAI créé")
        
        # Test d'appel simple
        print("🔄 Test d'appel API...")
        response = llm.invoke("Dis simplement 'Bonjour, l'API fonctionne!'")
        print(f"✅ Réponse reçue: {response.content}")
        
        print("\n🎉 Connexion OpenAI fonctionnelle!")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Installez les dépendances: pip install langchain-openai")
        return False
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("💡 Vérifiez votre clé API et votre connexion internet")
        return False

if __name__ == "__main__":
    success = test_openai_connection()
    sys.exit(0 if success else 1)