"""
Module de configuration pour Agrivision.
Gère toutes les variables d'environnement de manière centralisée.
"""

import os
import warnings
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Suppression des warnings de compatibilité Pydantic V1
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality")
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core._api.deprecation")

# Chargement du fichier .env
load_dotenv()

class Config:
    """
    Classe de configuration centralisée pour Agrivision.
    Toutes les variables d'environnement sont définies ici.
    """
    
    # ==========================================================================
    # API CONFIGURATION
    # ==========================================================================
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_API_BASE: str = os.getenv("MISTRAL_API_BASE", "https://api.mistral.ai/v1")
    
    # ==========================================================================
    # MODÈLE CONFIGURATION
    # ==========================================================================
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "mistral-large-latest")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.1"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4000"))
    
    # ==========================================================================
    # RÉPERTOIRES
    # ==========================================================================
    INPUT_DIR: str = os.getenv("INPUT_DIR", "input")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    
    # ==========================================================================
    # TRAITEMENT
    # ==========================================================================
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT_SECONDS: int = int(os.getenv("TIMEOUT_SECONDS", "120"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))
    MARKDOWN_PATTERN: str = os.getenv("MARKDOWN_PATTERN", "*.md")
    
    # ==========================================================================
    # LOGGING
    # ==========================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT", 
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # ==========================================================================
    # DÉVELOPPEMENT
    # ==========================================================================
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    SHOW_PROMPTS: bool = os.getenv("SHOW_PROMPTS", "false").lower() == "true"
    SAVE_RAW_RESPONSES: bool = os.getenv("SAVE_RAW_RESPONSES", "false").lower() == "true"
    
    # ==========================================================================
    # RÉSEAU ET SSL
    # ==========================================================================
    VERIFY_SSL: bool = os.getenv("VERIFY_SSL", "true").lower() == "true"
    SSL_CERT_PATH: Optional[str] = os.getenv("SSL_CERT_PATH")
    DISABLE_SSL_WARNINGS: bool = os.getenv("DISABLE_SSL_WARNINGS", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> bool:
        """
        Valide que toutes les variables d'environnement requises sont définies.
        
        Returns:
            bool: True si la configuration est valide, False sinon
        """
        errors = []
        
        if not cls.MISTRAL_API_KEY:
            errors.append("MISTRAL_API_KEY est requis")
        
        if cls.DEFAULT_TEMPERATURE < 0 or cls.DEFAULT_TEMPERATURE > 1:
            errors.append("DEFAULT_TEMPERATURE doit être entre 0 et 1")
        
        if cls.MAX_RETRIES <= 0:
            errors.append("MAX_RETRIES doit être supérieur à 0")
        
        if cls.BATCH_SIZE <= 0:
            errors.append("BATCH_SIZE doit être supérieur à 0")
        
        if errors:
            print("❌ Erreurs de configuration:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """
        Affiche la configuration actuelle (sans les clés sensibles).
        """
        print("🔧 CONFIGURATION AGRIVISION")
        print("=" * 50)
        print(f"Modèle par défaut: {cls.DEFAULT_MODEL}")
        print(f"Température: {cls.DEFAULT_TEMPERATURE}")
        print(f"Max tokens: {cls.MAX_TOKENS}")
        print(f"Répertoire d'entrée: {cls.INPUT_DIR}")
        print(f"Répertoire de sortie: {cls.OUTPUT_DIR}")
        print(f"Max tentatives: {cls.MAX_RETRIES}")
        print(f"Timeout: {cls.TIMEOUT_SECONDS}s")
        print(f"Taille de batch: {cls.BATCH_SIZE}")
        print(f"Niveau de log: {cls.LOG_LEVEL}")
        print(f"Mode debug: {cls.DEBUG_MODE}")
        print(f"API Mistral configurée: {'✅' if cls.MISTRAL_API_KEY else '❌'}")
        print("=" * 50)
    
    @classmethod
    def get_model_config(cls) -> dict:
        """
        Retourne la configuration spécifique au modèle.
        
        Returns:
            dict: Configuration du modèle
        """
        config = {
            "model": cls.DEFAULT_MODEL,
            "temperature": cls.DEFAULT_TEMPERATURE,
            "max_tokens": cls.MAX_TOKENS,
            "timeout": cls.TIMEOUT_SECONDS
        }
        
        # Configuration SSL pour les environnements d'entreprise
        if not cls.VERIFY_SSL:
            config["verify"] = False
        elif cls.SSL_CERT_PATH:
            config["verify"] = cls.SSL_CERT_PATH
            
        return config
    
    @classmethod
    def ensure_directories(cls) -> None:
        """
        Crée les répertoires nécessaires s'ils n'existent pas.
        """
        directories = [cls.INPUT_DIR, cls.OUTPUT_DIR, cls.LOG_DIR]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            
# Instance de configuration globale
config = Config()

def init_config() -> bool:
    """
    Initialise la configuration complète de l'application.
    
    Returns:
        bool: True si l'initialisation réussit, False sinon
    """
    # Désactivation des warnings SSL si demandé
    if config.DISABLE_SSL_WARNINGS:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Suppression également des warnings SSL de requests
        import requests.packages.urllib3
        requests.packages.urllib3.disable_warnings()
    
    # Validation de la configuration
    if not config.validate():
        return False
    
    # Création des répertoires
    config.ensure_directories()
    
    return True