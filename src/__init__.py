"""
Package principal pour le traitement d'articles scientifiques avec LangChain.
"""

# N'importons que la configuration pour éviter les problèmes de dépendances
from .config import config, init_config

__all__ = ["config", "init_config"]

# Les autres modules peuvent être importés explicitement quand nécessaire
# from .models import ScientificArticle
# from .loaders import MarkdownLoader  
# from .processors import ScientificArticleProcessor