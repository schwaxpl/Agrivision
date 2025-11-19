#!/usr/bin/env python3
"""
Script de démarrage pour Hugging Face Spaces
Configure et lance l'API Agrivision sur le port 7860
"""

import os
import uvicorn
import logging
from pathlib import Path

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Fonction principale de démarrage"""
    
    # Configuration du port (Hugging Face Spaces utilise 7860)
    port = int(os.environ.get("PORT", 7860))
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Créer les répertoires nécessaires s'ils n'existent pas
    directories = ["output", "data", "logs", "input"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Répertoire {directory} vérifié/créé")
    
    # Configuration des variables d'environnement par défaut
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY non configurée - l'API ne fonctionnera pas correctement")
    
    # Démarrer l'application
    logger.info(f"Démarrage de l'API Agrivision sur {host}:{port}")
    logger.info("Interface disponible sur /docs pour la documentation")
    
    try:
        uvicorn.run(
            "api:app",
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=False  # Pas de reload en production
        )
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'API: {e}")
        raise

if __name__ == "__main__":
    main()