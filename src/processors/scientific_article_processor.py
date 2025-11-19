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
from langchain_openai import ChatOpenAI
import logging

from ..models.pedagogical_scenario import PedagogicalScenario, PedagogicalDay, PedagogicalSequence
from ..config import config
from ..config import config


class PedagogicalScenarioProcessor:
    """
    Processeur pour extraire des informations structurées de scénarios pédagogiques
    à partir de documents de formation en markdown.
    """
    
    def __init__(self, 
                 llm: Optional[BaseLanguageModel] = None,
                 temperature: Optional[float] = None,
                 model_name: Optional[str] = None):
        """
        Initialise le processeur de scénarios pédagogiques.
        
        Args:
            llm: Modèle de langage à utiliser (si None, utilise ChatOpenAI par défaut)
            temperature: Température pour le modèle (utilise config par défaut si None)
            model_name: Nom du modèle à utiliser (utilise config par défaut si None)
        """
        if llm is None:
            # Configuration avec OpenAI en utilisant les variables d'environnement
            model_config = config.get_model_config()
            
            self.llm = ChatOpenAI(
                model=model_name or model_config["model"],
                temperature=temperature or model_config["temperature"],
                max_tokens=model_config["max_tokens"],
                timeout=model_config["timeout"],
                openai_api_key=config.OPENAI_API_KEY,
                openai_api_base=config.OPENAI_API_BASE
            )
        else:
            self.llm = llm
            
        # Parser pour convertir la sortie en objet Pydantic
        self.output_parser = PydanticOutputParser(pydantic_object=PedagogicalScenario)
        
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
Vous êtes un expert en ingénierie pédagogique et en analyse de documents de formation. 
Votre tâche est d'extraire des informations structurées pour créer un scénario pédagogique multi-jours à partir du document fourni en format markdown.

Analysez attentivement le texte suivant et structurez-le selon une organisation hiérarchique : SCÉNARIO > JOURS > SÉQUENCES.
Si une information n'est pas disponible, utilisez des valeurs cohérentes par défaut.

TEXTE À ANALYSER:
{text}

INSTRUCTIONS DÉTAILLÉES :

**NIVEAU SCÉNARIO (global)** :
- **scenario_title** : Titre général du scénario de formation
- **target_audience** : Public cible (niveau, profil des apprenants)
- **global_objectives** : Objectifs pédagogiques globaux du scénario complet
- **prerequisites** : Prérequis nécessaires
- **global_resources** : Ressources générales nécessaires
- **confidence_score** : Votre niveau de confiance (0.0 à 1.0)

**NIVEAU JOURS** :
Pour chaque jour identifié dans le document :
- **day_number** : Numéro du jour (1, 2, 3, etc.)
- **day_date** : Date si mentionnée (format libre)
- **day_title** : Titre/thème du jour
- **daily_objectives** : Objectifs spécifiques de la journée
- **sequences** : Liste des séquences de ce jour

**NIVEAU SÉQUENCES** :
Pour chaque séquence pédagogique :
- **sequence_number** : N° de séquence dans la journée (1, 2, 3, etc.)
- **start_time** : Heure de début (format "HH:MM")
- **end_time** : Heure de fin (format "HH:MM")
- **content** : Contenu détaillé de la séquence
- **pedagogical_methods** : Méthodes pédagogiques ["Cours magistral", "TP", "Travail de groupe"...]
- **evaluation_modalities** : Modalités d'évaluation ["QCM", "Présentation orale", "Rapport"...]
- **title** : Titre de la séquence (optionnel)
- **objectives** : Objectifs spécifiques de la séquence
- **resources_needed** : Ressources nécessaires pour cette séquence

**LOGIQUE D'ORGANISATION** :
- Si le document ne mentionne qu'une journée, créez 1 jour avec toutes les séquences
- Si plusieurs jours sont mentionnés, organisez les séquences par jour
- Si aucun horaire n'est mentionné, estimez des créneaux cohérents (ex: 09:00-12:00, 14:00-17:00)
- Numérotez les séquences par jour (recommencer à 1 pour chaque jour)

{format_instructions}

RÉPONSE STRUCTURÉE :
"""
        
        return PromptTemplate(
            template=template,
            input_variables=["text"],
            partial_variables={
                "format_instructions": self.output_parser.get_format_instructions()
            }
        )
    
    def process_document(self, document: Document) -> PedagogicalScenario:
        """
        Traite un document et extrait les informations structurées.
        
        Args:
            document: Document LangChain contenant le texte markdown
            
        Returns:
            Objet PedagogicalScenario avec les informations extraites
            
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
    
    def process_documents(self, documents: List[Document]) -> List[PedagogicalScenario]:
        """
        Traite une liste de documents.
        
        Args:
            documents: Liste de documents LangChain
            
        Returns:
            Liste d'objets PedagogicalScenario
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
                                max_retries: Optional[int] = None) -> List[PedagogicalScenario]:
        """
        Traite les documents par batch avec mécanisme de retry.
        
        Args:
            documents: Liste de documents à traiter
            max_retries: Nombre maximum de tentatives par document
            
        Returns:
            Liste d'objets PedagogicalScenario
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
    
    def get_processing_stats(self, scenarios: List[PedagogicalScenario]) -> Dict[str, Any]:
        """
        Génère des statistiques sur les scénarios traités.
        
        Args:
            scenarios: Liste de scénarios traités
            
        Returns:
            Dictionnaire avec les statistiques
        """
        if not scenarios:
            return {"total_scenarios": 0}
        
        # Calculs des statistiques de base
        total_scenarios = len(scenarios)
        total_days = sum(scenario.get_total_days() for scenario in scenarios)
        total_sequences = sum(scenario.get_total_sequences() for scenario in scenarios)
        total_duration_minutes = sum(scenario.get_total_duration() for scenario in scenarios)
        
        # Statistiques sur les contenus
        scenarios_with_global_objectives = len([s for s in scenarios if s.global_objectives])
        scenarios_with_target_audience = len([s for s in scenarios if s.target_audience])
        scenarios_with_title = len([s for s in scenarios if s.scenario_title])
        
        # Scores de confiance
        confidence_scores = [s.confidence_score for s in scenarios if s.confidence_score is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Statistiques au niveau des jours
        total_day_objectives = 0
        days_with_objectives = 0
        for scenario in scenarios:
            for day in scenario.days:
                if day.daily_objectives:
                    days_with_objectives += 1
                    total_day_objectives += len(day.daily_objectives)
        
        # Statistiques au niveau des séquences
        sequences_with_methods = 0
        sequences_with_evaluation = 0
        sequences_with_objectives = 0
        total_methods = 0
        total_evaluations = 0
        
        for scenario in scenarios:
            for day in scenario.days:
                for sequence in day.sequences:
                    if sequence.pedagogical_methods:
                        sequences_with_methods += 1
                        total_methods += len(sequence.pedagogical_methods)
                    if sequence.evaluation_modalities:
                        sequences_with_evaluation += 1
                        total_evaluations += len(sequence.evaluation_modalities)
                    if sequence.objectives:
                        sequences_with_objectives += 1
        
        stats = {
            "total_scenarios": total_scenarios,
            "total_days": total_days,
            "total_sequences": total_sequences,
            "total_duration_minutes": total_duration_minutes,
            "total_duration_hours": round(total_duration_minutes / 60, 2),
            "average_days_per_scenario": round(total_days / total_scenarios, 1),
            "average_sequences_per_scenario": round(total_sequences / total_scenarios, 1),
            "average_duration_per_scenario": round(total_duration_minutes / total_scenarios, 1),
            "average_confidence_score": round(avg_confidence, 3),
            "content_completion_rates": {
                "scenarios_with_title": round(scenarios_with_title / total_scenarios * 100, 1),
                "scenarios_with_target_audience": round(scenarios_with_target_audience / total_scenarios * 100, 1),
                "scenarios_with_global_objectives": round(scenarios_with_global_objectives / total_scenarios * 100, 1),
                "days_with_objectives": round(days_with_objectives / total_days * 100, 1) if total_days > 0 else 0,
                "sequences_with_methods": round(sequences_with_methods / total_sequences * 100, 1) if total_sequences > 0 else 0,
                "sequences_with_evaluation": round(sequences_with_evaluation / total_sequences * 100, 1) if total_sequences > 0 else 0,
                "sequences_with_objectives": round(sequences_with_objectives / total_sequences * 100, 1) if total_sequences > 0 else 0
            },
            "averages": {
                "methods_per_sequence": round(total_methods / sequences_with_methods, 1) if sequences_with_methods > 0 else 0,
                "evaluations_per_sequence": round(total_evaluations / sequences_with_evaluation, 1) if sequences_with_evaluation > 0 else 0,
                "objectives_per_day": round(total_day_objectives / days_with_objectives, 1) if days_with_objectives > 0 else 0
            }
        }
        
        return stats