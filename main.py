"""
Script principal pour le traitement d'articles scientifiques avec LangChain.

Ce script orchestre le processus complet :
1. Chargement des fichiers markdown
2. Prétraitement des documents
3. Extraction d'informations structurées avec LangChain
4. Export des résultats
"""

import os
import json
import argparse
import logging
import warnings
import ssl
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# ======== CONFIGURATION SSL POUR ZSCALER ========
# Configuration SSL pour ZScaler et autres proxies d'entreprise
# Désactivation de la vérification SSL si nécessaire
os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""

# Configuration SSL globale pour Python
ssl._create_default_https_context = ssl._create_unverified_context

# Suppression des warnings SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Suppression des warnings de compatibilité Pydantic V1
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality")
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core._api.deprecation")
# ================================================

from src.config import config, init_config
from src.loaders.markdown_loader import MarkdownLoader
from src.processors.scientific_article_processor import ScientificArticleProcessor
from src.models.scientific_article import ScientificArticle


class ArticleProcessor:
    """
    Classe principale pour orchestrer le traitement des articles scientifiques.
    """
    
    def __init__(self, 
                 model_name: Optional[str] = None,
                 temperature: Optional[float] = None,
                 output_dir: Optional[str] = None):
        """
        Initialise le processeur d'articles.
        
        Args:
            model_name: Nom du modèle LLM à utiliser (utilise config par défaut si None)
            temperature: Température du modèle (utilise config par défaut si None) 
            output_dir: Répertoire de sortie pour les résultats (utilise config par défaut si None)
        """
        # Configuration du logger
        self.logger = logging.getLogger(__name__)
        
        self.loader = MarkdownLoader()
        self.processor = ScientificArticleProcessor(
            model_name=model_name,
            temperature=temperature
        )
        self.output_dir = Path(output_dir or config.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
        
    def process_file(self, file_path: str) -> ScientificArticle:
        """
        Traite un seul fichier markdown.
        
        Args:
            file_path: Chemin vers le fichier markdown
            
        Returns:
            Article scientifique structuré
        """
        print(f"Traitement du fichier: {file_path}")
        
        # Chargement du document
        document = self.loader.load_file(file_path)
        
        # Prétraitement
        document = self.loader.preprocess_content(document)
        
        # Extraction d'informations structurées
        article = self.processor.process_document(document)
        
        print(f"Article traité: {article.title[:50]}...")
        return article
    
    def process_directory(self, 
                         directory_path: str,
                         pattern: Optional[str] = None,
                         recursive: bool = True) -> List[ScientificArticle]:
        """
        Traite tous les fichiers markdown d'un répertoire.
        
        Args:
            directory_path: Chemin vers le répertoire
            pattern: Pattern de fichiers à traiter (utilise config si None)
            recursive: Traitement récursif des sous-répertoires
            
        Returns:
            Liste des articles scientifiques structurés
        """
        pattern = pattern or config.MARKDOWN_PATTERN
        print(f"Traitement du répertoire: {directory_path}")
        print(f"Pattern: {pattern}, Récursif: {recursive}")
        
        # Chargement des documents
        documents = self.loader.load_directory(
            directory_path, 
            pattern=pattern, 
            recursive=recursive
        )
        
        if not documents:
            print("Aucun document trouvé à traiter.")
            return []
        
        # Prétraitement des documents
        print("Prétraitement des documents...")
        preprocessed_docs = [
            self.loader.preprocess_content(doc) for doc in documents
        ]
        
        # Extraction d'informations structurées
        print("Extraction des informations structurées...")
        articles = self.processor.batch_process_with_retry(
            preprocessed_docs, 
            max_retries=config.MAX_RETRIES
        )
        
        return articles
    
    def save_results(self, 
                    articles: List[ScientificArticle], 
                    format: str = "json",
                    filename: Optional[str] = None) -> str:
        """
        Sauvegarde les résultats dans le format spécifié.
        
        Args:
            articles: Liste des articles à sauvegarder
            format: Format de sortie ("json", "csv", "txt")
            filename: Nom du fichier (généré automatiquement si None)
            
        Returns:
            Chemin vers le fichier de sortie
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"articles_{timestamp}.{format}"
        
        output_path = self.output_dir / filename
        
        if format == "json":
            self._save_as_json(articles, output_path)
        elif format == "csv":
            self._save_as_csv(articles, output_path)
        elif format == "txt":
            self._save_as_txt(articles, output_path)
        else:
            raise ValueError(f"Format non supporté: {format}")
        
        print(f"Résultats sauvegardés dans: {output_path}")
        return str(output_path)
    
    def _save_as_json(self, articles: List[ScientificArticle], path: Path):
        """Sauvegarde en format JSON."""
        data = {
            "metadata": {
                "total_articles": len(articles),
                "processing_date": datetime.now().isoformat(),
                "version": "1.0"
            },
            "articles": [article.to_dict() for article in articles]
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def _save_as_csv(self, articles: List[ScientificArticle], path: Path):
        """Sauvegarde en format CSV."""
        import csv
        
        if not articles:
            return
        
        # Déterminer les colonnes à partir du premier article
        fieldnames = list(articles[0].to_dict().keys())
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for article in articles:
                row = article.to_dict()
                # Convertir les listes en chaînes de caractères
                for key, value in row.items():
                    if isinstance(value, list):
                        row[key] = "; ".join(str(v) for v in value)
                writer.writerow(row)
    
    def _save_as_txt(self, articles: List[ScientificArticle], path: Path):
        """Sauvegarde en format texte lisible."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT D'EXTRACTION D'ARTICLES SCIENTIFIQUES\n")
            f.write(f"Date de traitement: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nombre d'articles: {len(articles)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, article in enumerate(articles, 1):
                f.write(f"ARTICLE {i}\n")
                f.write("-" * 40 + "\n")
                f.write(f"Titre: {article.title}\n")
                f.write(f"Auteurs: {', '.join(article.authors) if article.authors else 'Non spécifié'}\n")
                f.write(f"Journal: {article.journal or 'Non spécifié'}\n")
                f.write(f"Date: {article.publication_date or 'Non spécifiée'}\n")
                f.write(f"DOI: {article.doi or 'Non spécifié'}\n")
                f.write(f"Domaine: {article.research_field or 'Non spécifié'}\n")
                f.write(f"Confiance: {article.confidence_score or 'N/A'}\n\n")
                f.write(f"Résumé:\n{article.abstract}\n\n")
                
                if article.keywords:
                    f.write(f"Mots-clés: {', '.join(article.keywords)}\n\n")
                
                if article.main_findings:
                    f.write(f"Principales découvertes:\n")
                    for finding in article.main_findings:
                        f.write(f"- {finding}\n")
                    f.write("\n")
                
                f.write("=" * 80 + "\n\n")
    
    def generate_report(self, articles: List[ScientificArticle]) -> dict:
        """
        Génère un rapport détaillé des résultats.
        
        Args:
            articles: Liste des articles traités
            
        Returns:
            Dictionnaire contenant le rapport
        """
        stats = self.processor.get_processing_stats(articles)
        
        report = {
            "processing_summary": stats,
            "timestamp": datetime.now().isoformat(),
            "sample_articles": [
                {
                    "title": article.title,
                    "authors_count": len(article.authors),
                    "confidence": article.confidence_score,
                    "research_field": article.research_field
                }
                for article in articles[:5]  # Premiers 5 articles comme échantillon
            ]
        }
        
        return report


def main():
    """Fonction principale avec interface en ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Traitement d'articles scientifiques avec LangChain"
    )
    
    parser.add_argument(
        "input_path",
        help="Chemin vers le fichier ou répertoire à traiter"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default=config.OUTPUT_DIR,
        help=f"Répertoire de sortie (défaut: {config.OUTPUT_DIR})"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["json", "csv", "txt"],
        default="json",
        help="Format de sortie (défaut: json)"
    )
    
    parser.add_argument(
        "--model",
        default=config.DEFAULT_MODEL,
        help=f"Modèle LLM à utiliser (défaut: {config.DEFAULT_MODEL})"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=config.DEFAULT_TEMPERATURE,
        help=f"Température du modèle (défaut: {config.DEFAULT_TEMPERATURE})"
    )
    
    parser.add_argument(
        "--pattern",
        default=config.MARKDOWN_PATTERN,
        help=f"Pattern de fichiers pour les répertoires (défaut: {config.MARKDOWN_PATTERN})"
    )
    
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Ne pas traiter récursivement les sous-répertoires"
    )
    
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Afficher la configuration et quitter"
    )
    
    args = parser.parse_args()
    
    # Affichage de la configuration si demandé
    if args.show_config:
        config.print_config()
        return 0
    
    # Validation de la configuration
    if not config.validate():
        print("\n💡 Conseil: Copiez .env.example vers .env et remplissez les valeurs")
        return 1
    
    try:
        # Initialisation du processeur
        processor = ArticleProcessor(
            model_name=args.model,
            temperature=args.temperature,
            output_dir=args.output_dir
        )
        
        # Traitement
        input_path = Path(args.input_path)
        
        if input_path.is_file():
            print("Traitement d'un fichier unique...")
            article = processor.process_file(str(input_path))
            articles = [article]
        elif input_path.is_dir():
            print("Traitement d'un répertoire...")
            articles = processor.process_directory(
                str(input_path),
                pattern=args.pattern,
                recursive=not args.no_recursive
            )
        else:
            print(f"Erreur: Le chemin {input_path} n'existe pas.")
            return 1
        
        if not articles:
            print("Aucun article n'a pu être traité.")
            return 1
        
        # Sauvegarde des résultats
        output_file = processor.save_results(articles, format=args.format)
        
        # Génération et affichage du rapport
        report = processor.generate_report(articles)
        print("\nRAPPORT DE TRAITEMENT:")
        print(f"Articles traités: {report['processing_summary']['total_articles']}")
        print(f"Taux de complétude auteurs: {report['processing_summary']['completion_rates']['authors']}%")
        print(f"Score de confiance moyen: {report['processing_summary']['average_confidence_score']}")
        print(f"Domaines de recherche uniques: {report['processing_summary']['unique_research_fields']}")
        
        print(f"\nTraitement terminé avec succès!")
        print(f"Résultats disponibles dans: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"Erreur lors du traitement: {e}")
        return 1


if __name__ == "__main__":
    exit(main())