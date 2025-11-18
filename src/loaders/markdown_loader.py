"""
Loader pour les fichiers markdown contenant des résumés d'articles scientifiques.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_core.documents import Document


class MarkdownLoader:
    """
    Classe pour charger et prétraiter les fichiers markdown
    contenant des résumés d'articles scientifiques.
    """
    
    def __init__(self, encoding: str = "utf-8"):
        """
        Initialise le loader markdown.
        
        Args:
            encoding: Encodage des fichiers (par défaut utf-8)
        """
        self.encoding = encoding
        
    def load_file(self, file_path: str) -> Document:
        """
        Charge un seul fichier markdown.
        
        Args:
            file_path: Chemin vers le fichier markdown
            
        Returns:
            Document LangChain contenant le contenu du fichier
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si le fichier n'est pas un fichier markdown
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
            
        if path.suffix.lower() not in ['.md', '.markdown']:
            raise ValueError(f"Le fichier {file_path} n'est pas un fichier markdown")
        
        # Utilisation du loader LangChain pour markdown
        loader = UnstructuredMarkdownLoader(
            file_path=str(path),
            encoding=self.encoding
        )
        
        documents = loader.load()
        
        if not documents:
            raise ValueError(f"Impossible de charger le contenu de {file_path}")
            
        # Ajouter des métadonnées au document
        document = documents[0]
        document.metadata.update({
            "source_file": str(path.absolute()),
            "file_name": path.name,
            "file_size": path.stat().st_size,
            "loader_type": "MarkdownLoader"
        })
        
        return document
    
    def load_directory(self, directory_path: str, 
                      pattern: str = "*.md",
                      recursive: bool = True) -> List[Document]:
        """
        Charge tous les fichiers markdown d'un répertoire.
        
        Args:
            directory_path: Chemin vers le répertoire
            pattern: Pattern pour filtrer les fichiers (par défaut *.md)
            recursive: Si True, parcourt les sous-répertoires
            
        Returns:
            Liste des documents LangChain
            
        Raises:
            FileNotFoundError: Si le répertoire n'existe pas
        """
        path = Path(directory_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Le répertoire {directory_path} n'existe pas")
            
        if not path.is_dir():
            raise ValueError(f"{directory_path} n'est pas un répertoire")
        
        # Recherche des fichiers markdown
        if recursive:
            markdown_files = list(path.rglob(pattern))
        else:
            markdown_files = list(path.glob(pattern))
        
        documents = []
        failed_files = []
        
        for file_path in markdown_files:
            try:
                document = self.load_file(str(file_path))
                documents.append(document)
            except Exception as e:
                failed_files.append((str(file_path), str(e)))
        
        if failed_files:
            print(f"Attention: {len(failed_files)} fichiers n'ont pas pu être chargés:")
            for file_path, error in failed_files:
                print(f"  - {file_path}: {error}")
        
        print(f"Chargement terminé: {len(documents)} fichiers traités avec succès")
        return documents
    
    def preprocess_content(self, document: Document) -> Document:
        """
        Prétraite le contenu d'un document markdown.
        
        Args:
            document: Document LangChain à prétraiter
            
        Returns:
            Document prétraité
        """
        content = document.page_content
        
        # Nettoyage basique du contenu markdown
        # Suppression des liens markdown mais conservation du texte
        import re
        
        # Enlever les liens [texte](url) et garder juste le texte
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        
        # Enlever les images ![alt](url)
        content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', content)
        
        # Normaliser les espaces multiples
        content = re.sub(r'\s+', ' ', content)
        
        # Nettoyer les sauts de ligne multiples
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        # Mettre à jour le document
        document.page_content = content.strip()
        
        return document
    
    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """
        Obtient les statistiques d'un fichier markdown.
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Dictionnaire contenant les statistiques du fichier
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
        
        with open(path, 'r', encoding=self.encoding) as f:
            content = f.read()
        
        stats = {
            "file_path": str(path.absolute()),
            "file_name": path.name,
            "file_size": path.stat().st_size,
            "character_count": len(content),
            "word_count": len(content.split()),
            "line_count": len(content.splitlines()),
        }
        
        return stats