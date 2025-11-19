"""
Module pour récupérer des articles depuis Airtable
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from pyairtable import Api
import logging

logger = logging.getLogger(__name__)

class AirtableArticleManager:
    """
    Gestionnaire pour récupérer et sauvegarder des articles depuis Airtable
    """
    
    def __init__(self, api_key: str = None, base_id: str = None, table_name: str = "Article"):
        """
        Initialise le gestionnaire Airtable
        
        Args:
            api_key: Clé API Airtable
            base_id: ID de la base Airtable
            table_name: Nom de la table (par défaut "Article")
        """
        self.api_key = api_key or os.environ.get("AIRTABLE_API_KEY")
        self.base_id = base_id or os.environ.get("AIRTABLE_BASE_ID") 
        self.table_name = table_name
        
        if not self.api_key:
            raise ValueError("Clé API Airtable non trouvée. Définissez AIRTABLE_API_KEY dans l'environnement.")
        
        if not self.base_id:
            raise ValueError("ID de base Airtable non trouvé. Définissez AIRTABLE_BASE_ID dans l'environnement.")
        
        # Initialiser l'API Airtable
        self.api = Api(self.api_key)
        self.table = self.api.table(self.base_id, self.table_name)
        
        logger.info(f"AirtableArticleManager initialisé pour la table '{self.table_name}'")
    
    def fetch_articles(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les articles depuis Airtable
        
        Returns:
            Liste des articles avec leurs métadonnées
        """
        try:
            logger.info("Récupération des articles depuis Airtable...")
            
            # Récupérer tous les enregistrements
            records = self.table.all()
            
            articles = []
            for record in records:
                fields = record.get('fields', {})
                
                # Extraire les champs nécessaires
                article_data = {
                    'id': record.get('id'),
                    'date_article': fields.get('Date_article'),
                    'support_cours': fields.get('Support_cours'),
                    'created_time': record.get('createdTime'),
                    'raw_record': record
                }
                
                # Valider que les champs obligatoires sont présents
                if article_data['support_cours']:
                    articles.append(article_data)
                else:
                    logger.warning(f"Article {article_data['id']} ignoré: pas de contenu Support_cours")
            
            logger.info(f"✅ {len(articles)} articles récupérés depuis Airtable")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des articles Airtable: {e}")
            raise
    
    def save_articles_to_data_folder(self, articles: List[Dict[str, Any]], data_folder: str = "data") -> List[str]:
        """
        Sauvegarde les articles dans le dossier data
        
        Args:
            articles: Liste des articles à sauvegarder
            data_folder: Dossier de destination
            
        Returns:
            Liste des chemins des fichiers créés
        """
        data_path = Path(data_folder)
        data_path.mkdir(exist_ok=True)
        
        saved_files = []
        
        for article in articles:
            try:
                # Générer le nom de fichier : date_id.md
                article_id = article['id']
                date_article = article.get('date_article')
                
                # Format du nom de fichier
                if date_article:
                    # Parser la date si elle existe
                    try:
                        if isinstance(date_article, str):
                            # Essayer différents formats de date
                            date_formats = ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d %H:%M:%S']
                            parsed_date = None
                            for fmt in date_formats:
                                try:
                                    parsed_date = datetime.strptime(date_article.split('T')[0], '%Y-%m-%d')
                                    break
                                except:
                                    continue
                            
                            if parsed_date:
                                date_str = parsed_date.strftime('%Y%m%d')
                            else:
                                date_str = date_article.replace('-', '').replace(':', '').replace(' ', '')[:8]
                        else:
                            date_str = datetime.now().strftime('%Y%m%d')
                    except:
                        date_str = datetime.now().strftime('%Y%m%d')
                else:
                    date_str = datetime.now().strftime('%Y%m%d')
                
                # Créer le nom de fichier
                filename = f"{date_str}_{article_id}.md"
                file_path = data_path / filename
                
                # Sauvegarder le contenu
                content = article['support_cours']
                
                # Ajouter des métadonnées en en-tête
                metadata_header = f"""# Article Airtable - {filename}

**Date de l'article:** {date_article or 'Non spécifiée'}
**ID Airtable:** {article_id}
**Récupéré le:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
                
                full_content = metadata_header + content
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(full_content)
                
                saved_files.append(str(file_path))
                logger.info(f"📄 Article sauvé: {filename}")
                
            except Exception as e:
                logger.error(f"❌ Erreur sauvegarde article {article.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ {len(saved_files)} articles sauvés dans {data_folder}/")
        return saved_files
    
    def sync_articles(self, data_folder: str = "data") -> Dict[str, Any]:
        """
        Synchronise complètement les articles: récupère depuis Airtable et sauvegarde
        
        Args:
            data_folder: Dossier de destination
            
        Returns:
            Résultats de la synchronisation
        """
        try:
            start_time = datetime.now()
            
            # Récupérer les articles
            articles = self.fetch_articles()
            
            # Sauvegarder les articles
            saved_files = self.save_articles_to_data_folder(articles, data_folder)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            sync_result = {
                "success": True,
                "articles_count": len(articles),
                "files_created": len(saved_files),
                "saved_files": saved_files,
                "duration_seconds": duration,
                "sync_time": end_time.isoformat()
            }
            
            logger.info(f"🔄 Synchronisation terminée: {len(articles)} articles en {duration:.2f}s")
            return sync_result
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la synchronisation: {e}")
            return {
                "success": False,
                "error": str(e),
                "articles_count": 0,
                "files_created": 0,
                "saved_files": [],
                "sync_time": datetime.now().isoformat()
            }
    
    def clean_data_folder(self, data_folder: str = "data", keep_non_airtable: bool = True):
        """
        Nettoie le dossier data des anciens articles Airtable
        
        Args:
            data_folder: Dossier à nettoyer
            keep_non_airtable: Garder les fichiers qui ne viennent pas d'Airtable
        """
        data_path = Path(data_folder)
        if not data_path.exists():
            return
        
        removed_count = 0
        for file_path in data_path.glob("*.md"):
            if keep_non_airtable:
                # Ne supprimer que les fichiers au format date_id.md (articles Airtable)
                filename = file_path.name
                if "_" in filename and filename.replace(".md", "").split("_")[0].isdigit():
                    file_path.unlink()
                    removed_count += 1
            else:
                # Supprimer tous les fichiers .md
                file_path.unlink()
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"🧹 {removed_count} anciens articles supprimés du dossier {data_folder}/")


def create_airtable_manager(api_key: str = None, base_id: str = None) -> AirtableArticleManager:
    """Factory function pour créer un AirtableArticleManager"""
    return AirtableArticleManager(api_key=api_key, base_id=base_id)