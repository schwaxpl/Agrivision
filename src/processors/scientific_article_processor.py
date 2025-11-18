"""
Processeur pour extraire des informations structurées d'articles scientifiques
à partir de documents markdown en utilisant LangChain.
"""

import os
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models.base import BaseLanguageModel
from langchain_mistralai import ChatMistralAI
import logging

from ..models.scientific_article import ScientificArticle
from ..config import config
from ..config import config


class ScientificArticleProcessor:
    """
    Processeur pour extraire des informations structurées d'articles scientifiques
    à partir de résumés en markdown.
    """
    
    def __init__(self, 
                 llm: Optional[BaseLanguageModel] = None,
                 temperature: Optional[float] = None,
                 model_name: Optional[str] = None):
        """
        Initialise le processeur.
        
        Args:
            llm: Modèle de langage à utiliser (si None, utilise ChatMistralAI par défaut)
            temperature: Température pour le modèle (utilise config par défaut si None)
            model_name: Nom du modèle à utiliser (utilise config par défaut si None)
        """
        if llm is None:
            # Configuration avec Mistral en utilisant les variables d'environnement
            model_config = config.get_model_config()
            
            self.llm = ChatMistralAI(
                model=model_name or model_config["model"],
                temperature=temperature or model_config["temperature"],
                max_tokens=model_config["max_tokens"],
                timeout=model_config["timeout"],
                mistral_api_key=config.MISTRAL_API_KEY
            )
        else:
            self.llm = llm
            
        # Parser pour convertir la sortie en objet Pydantic
        self.output_parser = PydanticOutputParser(pydantic_object=ScientificArticle)
        
        # Template de prompt pour l'extraction
        self.prompt_template = self._create_prompt_template()
        
        # Chaîne de traitement LangChain
        self.chain = self.prompt_template | self.llm | self.output_parser
    
    def _create_prompt_template(self) -> PromptTemplate:
        """
        Crée le template de prompt pour l'extraction d'informations.
        
        Returns:
            Template de prompt LangChain
        """
        template = """
Vous êtes un expert en analyse d'articles scientifiques. 
Votre tâche est d'extraire des informations structurées à partir du résumé d'un article scientifique fourni en format markdown.

Analysez attentivement le texte suivant et extrayez les informations demandées. 
Si une information n'est pas disponible ou ne peut pas être déterminée avec certitude, laissez le champ vide ou utilisez une valeur par défaut appropriée.

TEXTE À ANALYSER:
{text}

INSTRUCTIONS:
- Identifiez le titre de l'article
- Extrayez la liste des auteurs (s'ils sont mentionnés)
- Récupérez le résumé/abstract complet
- Identifiez les mots-clés pertinents
- Déterminez la date de publication si mentionnée
- Identifiez le journal/revue de publication si mentionné
- Trouvez le DOI si présent
- Déterminez le domaine de recherche principal
- Identifiez la méthodologie utilisée
- Extrayez les principales découvertes/résultats
- Évaluez votre confiance dans l'extraction (0.0 à 1.0)

{format_instructions}

RÉPONSE:
"""
        
        return PromptTemplate(
            template=template,
            input_variables=["text"],
            partial_variables={
                "format_instructions": self.output_parser.get_format_instructions()
            }
        )
    
    def process_document(self, document: Document) -> ScientificArticle:
        """
        Traite un document et extrait les informations structurées.
        
        Args:
            document: Document LangChain contenant le texte markdown
            
        Returns:
            Objet ScientificArticle avec les informations extraites
            
        Raises:
            Exception: Si le traitement échoue
        """
        try:
            # Debug: afficher le prompt si demandé
            if config.SHOW_PROMPTS:
                prompt_text = self.prompt_template.format(text=document.page_content[:500] + "...")
                print(f"🔍 PROMPT ENVOYÉ AU MODÈLE:\n{prompt_text}\n{'='*60}")
            
            # Exécution de la chaîne LangChain
            result = self.chain.invoke({"text": document.page_content})
            
            # Debug: sauvegarder la réponse brute si demandé
            if config.SAVE_RAW_RESPONSES:
                import json
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                response_file = f"{config.LOG_DIR}/raw_response_{timestamp}.json"
                with open(response_file, 'w', encoding='utf-8') as f:
                    json.dump(result.model_dump() if hasattr(result, 'model_dump') else result.dict(), f, indent=2, default=str)
            
            # Ajout des métadonnées du document source
            if hasattr(result, 'model_fields_set'):
                # Pour les versions récentes de Pydantic
                result_dict = result.model_dump()
            else:
                result_dict = result.dict()
                
            # Ajouter des métadonnées sur la source
            if document.metadata:
                result_dict["source_metadata"] = document.metadata
            
            return result
            
        except Exception as e:
            if config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
            raise Exception(f"Erreur lors du traitement du document: {str(e)}")
    
    def process_documents(self, documents: List[Document]) -> List[ScientificArticle]:
        """
        Traite une liste de documents.
        
        Args:
            documents: Liste de documents LangChain
            
        Returns:
            Liste d'objets ScientificArticle
        """
        results = []
        failed_documents = []
        
        for i, document in enumerate(documents):
            try:
                result = self.process_document(document)
                results.append(result)
                print(f"Document {i+1}/{len(documents)} traité avec succès")
            except Exception as e:
                failed_documents.append((i, str(e)))
                print(f"Erreur lors du traitement du document {i+1}: {e}")
        
        if failed_documents:
            print(f"\nAttention: {len(failed_documents)} documents ont échoué:")
            for idx, error in failed_documents:
                print(f"  - Document {idx+1}: {error}")
        
        print(f"\nTraitement terminé: {len(results)}/{len(documents)} documents traités avec succès")
        return results
    
    def batch_process_with_retry(self, documents: List[Document], 
                                max_retries: Optional[int] = None) -> List[ScientificArticle]:
        """
        Traite les documents par batch avec mécanisme de retry.
        
        Args:
            documents: Liste de documents à traiter
            max_retries: Nombre maximum de tentatives par document (utilise config si None)
            
        Returns:
            Liste d'objets ScientificArticle
        """
        max_retries = max_retries or config.MAX_RETRIES
        results = []
        
        for i, document in enumerate(documents):
            success = False
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    result = self.process_document(document)
                    results.append(result)
                    success = True
                    print(f"Document {i+1}/{len(documents)} traité avec succès (tentative {attempt+1})")
                    break
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        print(f"Échec tentative {attempt+1} pour document {i+1}, retry...")
                    
            if not success:
                print(f"Document {i+1} échoué après {max_retries} tentatives: {last_error}")
        
        return results
    
    def update_prompt_template(self, new_template: str) -> None:
        """
        Met à jour le template de prompt.
        
        Args:
            new_template: Nouveau template de prompt
        """
        self.prompt_template = PromptTemplate(
            template=new_template,
            input_variables=["text"],
            partial_variables={
                "format_instructions": self.output_parser.get_format_instructions()
            }
        )
        
        # Recréer la chaîne
        self.chain = self.prompt_template | self.llm | self.output_parser
    
    def get_processing_stats(self, articles: List[ScientificArticle]) -> Dict[str, Any]:
        """
        Génère des statistiques sur les articles traités.
        
        Args:
            articles: Liste d'articles traités
            
        Returns:
            Dictionnaire avec les statistiques
        """
        if not articles:
            return {"total_articles": 0}
        
        # Calculs des statistiques
        total_articles = len(articles)
        articles_with_authors = len([a for a in articles if a.authors])
        articles_with_doi = len([a for a in articles if a.doi])
        articles_with_date = len([a for a in articles if a.publication_date])
        
        confidence_scores = [a.confidence_score for a in articles if a.confidence_score is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        research_fields = [a.research_field for a in articles if a.research_field]
        unique_fields = len(set(research_fields))
        
        stats = {
            "total_articles": total_articles,
            "articles_with_authors": articles_with_authors,
            "articles_with_doi": articles_with_doi,
            "articles_with_publication_date": articles_with_date,
            "average_confidence_score": round(avg_confidence, 3),
            "unique_research_fields": unique_fields,
            "completion_rates": {
                "authors": round(articles_with_authors / total_articles * 100, 1),
                "doi": round(articles_with_doi / total_articles * 100, 1),
                "publication_date": round(articles_with_date / total_articles * 100, 1)
            }
        }
        
        return stats