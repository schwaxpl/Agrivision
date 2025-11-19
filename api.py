"""
API FastAPI pour l'enrichissement de scénarios pédagogiques
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import zipfile
import shutil
from pathlib import Path
import uuid
from datetime import datetime
import asyncio
import logging
import traceback

from src.config import Config
from src.models.pedagogical_scenario import PedagogicalScenario
from src.enrichment.scenario_enrichment import ScenarioEnrichment
from src.loaders.markdown_loader import MarkdownLoader
from src.loaders.airtable_loader import AirtableArticleManager
from src.processors.generate_md_for_marp import generate_marp_slides_from_md
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agrivision - Enrichissement de Scénarios",
    description="API pour enrichir des scénarios pédagogiques avec des articles scientifiques",
    version="1.0.0"
)

# Modèles Pydantic pour l'API
class EnrichmentRequest(BaseModel):
    scenario_json: str = "input/scenario.json"  # Utiliser le nouveau fichier JSON dans input
    data_directory: str = "data"
    output_format: str = "markdown"  # "json" ou "markdown"

class EnrichmentResponse(BaseModel):
    task_id: str
    status: str
    message: str

class AirtableSyncRequest(BaseModel):
    data_directory: str = "data"
    clean_before_sync: bool = False

class AirtableSyncResponse(BaseModel):
    task_id: str
    status: str
    message: str

class MarpSlidesRequest(BaseModel):
    task_id: str

class MarpSlidesResponse(BaseModel):
    task_id: str
    status: str
    message: str

class EnrichAndSlidesRequest(BaseModel):
    scenario_json: str = "input/scenario.json"
    data_directory: str = "data"
    output_format: str = "markdown"

class EnrichAndSlidesResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

# Stockage des tâches en mémoire (pour une version production, utiliser Redis/DB)
tasks_storage = {}

def load_scenario_from_json(json_path: str) -> PedagogicalScenario:
    """
    Charge un scénario depuis un fichier JSON généré précédemment.
    
    Args:
        json_path: Chemin vers le fichier JSON
        
    Returns:
        Objet PedagogicalScenario
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Le JSON contient metadata + scenarios, on prend le premier scénario
    scenarios_data = data.get("scenarios", [])
    if not scenarios_data:
        raise ValueError("Aucun scénario trouvé dans le fichier JSON")
    
    scenario_data = scenarios_data[0]
    return PedagogicalScenario(**scenario_data)

class EnrichmentTask:
    def __init__(self, task_id: str, request: EnrichmentRequest):
        self.task_id = task_id
        self.request = request
        self.status = "pending"
        self.progress = None
        self.result = None
        self.error = None
        self.created_at = datetime.now().isoformat()
        self.completed_at = None

def load_scenario_from_json(json_path: str) -> PedagogicalScenario:
    """
    Charge un scénario depuis un fichier JSON généré précédemment.
    
    Args:
        json_path: Chemin vers le fichier JSON
        
    Returns:
        Objet PedagogicalScenario
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Le JSON contient metadata + scenarios, on prend le premier scénario
    scenarios_data = data.get("scenarios", [])
    if not scenarios_data:
        raise ValueError("Aucun scénario trouvé dans le fichier JSON")
    
    scenario_data = scenarios_data[0]
    return PedagogicalScenario(**scenario_data)

async def process_enrichment_task(task: EnrichmentTask):
    """Traitement asynchrone de l'enrichissement"""
    try:
        logger.info(f"Démarrage de la tâche {task.task_id}")
        task.status = "running"
        task.progress = "Initialisation..."
        
        # Vérification des fichiers
        scenario_path = Path(task.request.scenario_json)
        data_path = Path(task.request.data_directory)
        
        logger.info(f"Vérification du fichier scénario JSON: {scenario_path}")
        if not scenario_path.exists():
            error_msg = f"Fichier scénario JSON non trouvé: {task.request.scenario_json}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info(f"Vérification du répertoire data: {data_path}")
        if not data_path.exists():
            error_msg = f"Répertoire data non trouvé: {task.request.data_directory}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        task.progress = "Chargement du scénario depuis JSON..."
        logger.info("Chargement du scénario depuis JSON")
        
        # Chargement du scénario depuis JSON
        try:
            scenario = load_scenario_from_json(str(scenario_path))
            logger.info(f"Scénario chargé: {scenario.scenario_title or 'Sans titre'}, {len(scenario.days)} jours")
        except Exception as e:
            error_msg = f"Erreur lors du chargement du scénario JSON: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Configuration pour l'enrichisseur
        try:
            config = Config()
            logger.info("Configuration chargée")
            
            # Vérifier que la clé API est configurée
            if not config.OPENAI_API_KEY:
                error_msg = "Clé API OpenAI non configurée. Vérifiez la variable d'environnement OPENAI_API_KEY"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            error_msg = f"Erreur lors du chargement de la configuration: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        task.progress = "Analyse des articles scientifiques..."
        logger.info("Démarrage de l'analyse des articles")
        
        # Initialisation de l'enrichisseur
        try:
            loader = MarkdownLoader()
            enricher = ScenarioEnrichment(            )
            logger.info("Enrichisseur initialisé")
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation de l'enrichisseur: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Analyse des articles
        try:
            articles = enricher.analyze_scientific_articles(str(data_path))
            logger.info(f"Articles analysés: {len(articles)}")
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse des articles: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        if not articles:
            error_msg = "Aucun article trouvé dans le répertoire data"
            logger.warning(error_msg)
            # Ne pas faire échouer la tâche, mais noter qu'il n'y a pas d'articles
        
        task.progress = "Enrichissement du scénario..."
        logger.info("Démarrage de l'enrichissement")
        
        # Enrichissement
        try:
            enriched_scenario = enricher.enrich_scenario(scenario, articles)
            logger.info("Enrichissement terminé")
        except Exception as e:
            error_msg = f"Erreur lors de l'enrichissement: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        task.progress = "Génération des résultats..."
        logger.info("Génération des fichiers de sortie")
        
        # Génération des fichiers de sortie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Créer le répertoire spécifique à cette tâche
        task_output_dir = Path(f"output/task_{task.task_id}")
        task_output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "scenario_original": enriched_scenario["scenario_original"],
            "enrichments": enriched_scenario["enrichments"],
            "articles_used": enriched_scenario["articles_used"],
            "statistics": {
                "total_sequences": len([seq for day in scenario.days for seq in day.sequences]),
                "enriched_sequences": sum(1 for day_enrich in enriched_scenario["enrichments"]["days"] 
                                        for seq_enrich in day_enrich["sequences"] 
                                        if seq_enrich["suggestions"]),
                "total_novelties": sum(len(seq_enrich["suggestions"]) for day_enrich in enriched_scenario["enrichments"]["days"] 
                                     for seq_enrich in day_enrich["sequences"] if seq_enrich["suggestions"]),
                "articles_count": len(articles)
            }
        }
        
        # Sauvegarde JSON
        json_output = task_output_dir / f"enriched_scenario_{timestamp}.json"
        try:
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(enriched_scenario, f, ensure_ascii=False, indent=2)
            logger.info(f"Fichier JSON sauvé: {json_output}")
        except Exception as e:
            error_msg = f"Erreur lors de la sauvegarde JSON: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        results["files"] = {"json": str(json_output)}
        
        # Génération markdown si demandé
        if task.request.output_format == "markdown":
            markdown_output = task_output_dir / f"enriched_scenario_{timestamp}.md"
            try:
                enricher.export_enriched_markdown(enriched_scenario, str(markdown_output))
                results["files"]["markdown"] = str(markdown_output)
                logger.info(f"Fichier Markdown sauvé: {markdown_output}")
            except Exception as e:
                error_msg = f"Erreur lors de la génération Markdown: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)
        
        # Ajouter un fichier de métadonnées pour la tâche
        metadata_output = task_output_dir / "task_metadata.json"
        task_metadata = {
            "task_id": task.task_id,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "request": task.request.model_dump(),
            "statistics": results["statistics"]
        }
        try:
            with open(metadata_output, 'w', encoding='utf-8') as f:
                json.dump(task_metadata, f, ensure_ascii=False, indent=2)
            results["files"]["metadata"] = str(metadata_output)
            logger.info(f"Métadonnées sauvées: {metadata_output}")
        except Exception as e:
            logger.warning(f"Erreur lors de la sauvegarde des métadonnées: {str(e)}")
        
        task.status = "completed"
        task.result = results
        task.completed_at = datetime.now().isoformat()
        task.progress = "Terminé avec succès"
        logger.info(f"Tâche {task.task_id} terminée avec succès")
        
    except Exception as e:
        error_details = {
            "error_message": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        
        logger.error(f"Erreur dans la tâche {task.task_id}: {error_details}")
        
        task.status = "failed"
        task.error = json.dumps(error_details, indent=2)
        task.completed_at = datetime.now().isoformat()
        task.progress = f"Erreur: {str(e)}"

@app.post("/generate-marp-slides", response_model=MarpSlidesResponse)
async def generate_marp_slides(
    request: MarpSlidesRequest,
    background_tasks: BackgroundTasks
):
    """
    Génère des slides Marp pour chaque document dans le dossier /data
    Les slides sont nommées avec task_id + document_id
    """
    # Vérifier que le dossier data existe
    data_dir = Path("data")
    if not data_dir.exists():
        raise HTTPException(status_code=404, detail="Dossier /data non trouvé")
    
    # Lister tous les fichiers .md dans le dossier data
    md_files = list(data_dir.glob("*.md"))
    if not md_files:
        raise HTTPException(status_code=404, detail="Aucun fichier .md trouvé dans /data")
    
    # Génération d'un nouvel ID pour la tâche de slides
    slides_task_id = str(uuid.uuid4())
    
    # Création d'une nouvelle tâche pour les slides
    slides_task = EnrichmentTask(slides_task_id, request)
    tasks_storage[slides_task_id] = slides_task
    
    # Lancement de la génération en arrière-plan
    background_tasks.add_task(process_marp_slides_from_data_task, slides_task, md_files)
    
    return MarpSlidesResponse(
        task_id=slides_task_id,
        status="pending",
        message=f"Génération de slides Marp lancée pour {len(md_files)} documents. Vérifiez l'avancement avec /tasks/{slides_task_id}"
    )

async def process_marp_slides_from_data_task(slides_task: EnrichmentTask, md_files: list):
    """Traitement asynchrone de la génération de slides Marp pour tous les documents du dossier data"""
    try:
        logger.info(f"Démarrage de la génération de slides Marp {slides_task.task_id} pour {len(md_files)} documents")
        slides_task.status = "running"
        slides_task.progress = f"Traitement de {len(md_files)} documents..."
        
        # Création du répertoire de sortie pour cette tâche
        task_output_dir = Path(f"output/task_{slides_task.task_id}")
        task_output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        generated_slides = []
        errors = []
        
        # Traitement de chaque fichier .md
        for i, md_file in enumerate(md_files, 1):
            try:
                slides_task.progress = f"Traitement document {i}/{len(md_files)}: {md_file.name}"
                logger.info(f"Traitement de {md_file.name}")
                
                # Extraction de l'ID du document depuis le nom du fichier
                # Format attendu: YYYYMMDD_recXXXXXXXXXXXXXX.md
                doc_name = md_file.stem
                doc_id = doc_name.split('_')[-1] if '_' in doc_name else doc_name
                
                # Lecture du contenu Markdown
                with open(md_file, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                logger.info(f"Fichier {md_file.name} lu: {len(md_content)} caractères")
                
                # Génération des slides avec le processeur existant
                marp_content = generate_marp_slides_from_md(md_content)
                
                # Traitement du contenu retourné par l'IA
                if hasattr(marp_content, 'content'):
                    markdown_content = marp_content.content
                else:
                    markdown_content = str(marp_content)
                
                # Nettoyage du contenu (même logique que dans le script original)
                if "```markdown" in markdown_content:
                    markdown_content = markdown_content.split("```markdown", 1)[1]
                if "```" in markdown_content:
                    markdown_content = markdown_content.split("```", 1)[0]
                
                markdown_content = markdown_content.strip()
                if markdown_content.startswith("---"):
                    markdown_content = markdown_content.split("---", 1)[1].lstrip()
                
                # Diviser en slides
                slides = markdown_content.split("---")
                non_empty_slides = [slide.strip() for slide in slides if slide.strip()]
                
                # Construction du contenu final
                final_content = "---\nmarp: true\n---\n\n" + "\n\n---\n\n".join(non_empty_slides)
                
                # Nom du fichier de sortie: task_id + doc_id
                slides_filename = f"marp_{slides_task.task_id}_{doc_id}.md"
                slides_path = task_output_dir / slides_filename
                
                # Sauvegarde des slides
                with open(slides_path, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                
                generated_slides.append({
                    "source_file": str(md_file),
                    "slides_file": str(slides_path),
                    "slides_count": len(non_empty_slides),
                    "document_id": doc_id
                })
                
                logger.info(f"Slides générées pour {md_file.name}: {slides_filename} ({len(non_empty_slides)} slides)")
                
            except Exception as e:
                error_info = {
                    "source_file": str(md_file),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                errors.append(error_info)
                logger.error(f"Erreur lors du traitement de {md_file.name}: {str(e)}")
        
        slides_task.progress = "Sauvegarde des métadonnées..."
        
        # Sauvegarde des métadonnées
        metadata_output = task_output_dir / "task_metadata.json"
        task_metadata = {
            "task_id": slides_task.task_id,
            "created_at": slides_task.created_at,
            "completed_at": slides_task.completed_at,
            "total_documents": len(md_files),
            "successful_generations": len(generated_slides),
            "errors_count": len(errors),
            "generated_slides": generated_slides,
            "errors": errors
        }
        
        try:
            with open(metadata_output, 'w', encoding='utf-8') as f:
                json.dump(task_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Erreur lors de la sauvegarde des métadonnées: {str(e)}")
        
        # Finalisation de la tâche
        slides_task.status = "completed"
        slides_task.result = {
            "total_documents": len(md_files),
            "successful_generations": len(generated_slides),
            "errors_count": len(errors),
            "generated_slides": generated_slides,
            "errors": errors,
            "files": {
                "metadata": str(metadata_output)
            }
        }
        slides_task.completed_at = datetime.now().isoformat()
        
        if errors:
            slides_task.progress = f"Terminé avec {len(generated_slides)}/{len(md_files)} réussites, {len(errors)} erreurs"
        else:
            slides_task.progress = f"Terminé: {len(generated_slides)} slides générées pour {len(md_files)} documents"
        
        logger.info(f"Tâche de génération de slides {slides_task.task_id} terminée: {len(generated_slides)} réussites, {len(errors)} erreurs")
        
    except Exception as e:
        error_details = {
            "error_message": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        
        logger.error(f"Erreur dans la génération de slides {slides_task.task_id}: {error_details}")
        
        slides_task.status = "failed"
        slides_task.error = json.dumps(error_details, indent=2)
        slides_task.completed_at = datetime.now().isoformat()
        slides_task.progress = f"Erreur: {str(e)}"

@app.post("/enrich-and-slides", response_model=EnrichAndSlidesResponse)
async def enrich_and_generate_slides(
    request: EnrichAndSlidesRequest,
    background_tasks: BackgroundTasks
):
    """
    Enrichit un scénario puis génère des slides pour chaque document du dossier data
    avec le même ID de tâche pour les deux opérations
    """
    # Génération d'un ID unique pour toute la pipeline
    task_id = str(uuid.uuid4())
    
    # Création de la tâche
    task = EnrichmentTask(task_id, request)
    tasks_storage[task_id] = task
    
    # Lancement de la pipeline complète en arrière-plan
    background_tasks.add_task(process_enrich_and_slides_task, task)
    
    return EnrichAndSlidesResponse(
        task_id=task_id,
        status="pending",
        message=f"Pipeline d'enrichissement et génération de slides lancée. Vérifiez l'avancement avec /tasks/{task_id}"
    )

async def process_enrich_and_slides_task(task: EnrichmentTask):
    """Pipeline complète : enrichissement + génération de slides"""
    try:
        logger.info(f"Démarrage de la pipeline complète {task.task_id}")
        task.status = "running"
        task.progress = "Étape 1/2 : Enrichissement du scénario..."
        
        # ÉTAPE 1 : ENRICHISSEMENT (code existant)
        # Vérification des fichiers
        scenario_path = Path(task.request.scenario_json)
        data_path = Path(task.request.data_directory)
        
        logger.info(f"Vérification du fichier scénario JSON: {scenario_path}")
        if not scenario_path.exists():
            error_msg = f"Fichier scénario JSON non trouvé: {task.request.scenario_json}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info(f"Vérification du répertoire data: {data_path}")
        if not data_path.exists():
            error_msg = f"Répertoire data non trouvé: {task.request.data_directory}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        task.progress = "Étape 1/2 : Chargement du scénario depuis JSON..."
        logger.info("Chargement du scénario depuis JSON")
        
        # Chargement du scénario depuis JSON
        try:
            scenario = load_scenario_from_json(str(scenario_path))
            logger.info(f"Scénario chargé: {scenario.scenario_title or 'Sans titre'}, {len(scenario.days)} jours")
        except Exception as e:
            error_msg = f"Erreur lors du chargement du scénario JSON: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Configuration pour l'enrichisseur
        try:
            config = Config()
            logger.info("Configuration chargée")
            
            if not config.OPENAI_API_KEY:
                error_msg = "Clé API OpenAI non configurée. Vérifiez la variable d'environnement OPENAI_API_KEY"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            error_msg = f"Erreur lors du chargement de la configuration: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        task.progress = "Étape 1/2 : Analyse des articles scientifiques..."
        logger.info("Démarrage de l'analyse des articles")
        
        # Initialisation de l'enrichisseur
        try:
            loader = MarkdownLoader()
            enricher = ScenarioEnrichment()
            logger.info("Enrichisseur initialisé")
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation de l'enrichisseur: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Analyse des articles
        try:
            articles = enricher.analyze_scientific_articles(str(data_path))
            logger.info(f"Articles analysés: {len(articles)}")
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse des articles: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        if not articles:
            logger.warning("Aucun article trouvé dans le répertoire data")
        
        task.progress = "Étape 1/2 : Enrichissement du scénario..."
        logger.info("Démarrage de l'enrichissement")
        
        # Enrichissement
        try:
            enriched_scenario = enricher.enrich_scenario(scenario, articles)
            logger.info("Enrichissement terminé")
        except Exception as e:
            error_msg = f"Erreur lors de l'enrichissement: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        task.progress = "Étape 1/2 : Génération des fichiers d'enrichissement..."
        logger.info("Génération des fichiers de sortie d'enrichissement")
        
        # Génération des fichiers de sortie d'enrichissement
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Créer le répertoire spécifique à cette tâche
        task_output_dir = Path(f"output/task_{task.task_id}")
        task_output_dir.mkdir(parents=True, exist_ok=True)
        
        enrichment_results = {
            "scenario_original": enriched_scenario["scenario_original"],
            "enrichments": enriched_scenario["enrichments"],
            "articles_used": enriched_scenario["articles_used"],
            "statistics": {
                "total_sequences": len([seq for day in scenario.days for seq in day.sequences]),
                "enriched_sequences": sum(1 for day_enrich in enriched_scenario["enrichments"]["days"] 
                                        for seq_enrich in day_enrich["sequences"] 
                                        if seq_enrich["suggestions"]),
                "total_novelties": sum(len(seq_enrich["suggestions"]) for day_enrich in enriched_scenario["enrichments"]["days"] 
                                     for seq_enrich in day_enrich["sequences"] if seq_enrich["suggestions"]),
                "articles_count": len(articles)
            }
        }
        
        # Sauvegarde JSON
        json_output = task_output_dir / f"enriched_scenario_{timestamp}.json"
        try:
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(enriched_scenario, f, ensure_ascii=False, indent=2)
            logger.info(f"Fichier JSON sauvé: {json_output}")
        except Exception as e:
            error_msg = f"Erreur lors de la sauvegarde JSON: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        enrichment_files = {"json": str(json_output)}
        
        # Génération markdown si demandé
        markdown_output = None
        if task.request.output_format == "markdown":
            markdown_output = task_output_dir / f"enriched_scenario_{timestamp}.md"
            try:
                enricher.export_enriched_markdown(enriched_scenario, str(markdown_output))
                enrichment_files["markdown"] = str(markdown_output)
                logger.info(f"Fichier Markdown sauvé: {markdown_output}")
            except Exception as e:
                error_msg = f"Erreur lors de la génération Markdown: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)
        
        # ÉTAPE 2 : GÉNÉRATION DES SLIDES
        task.progress = "Étape 2/2 : Génération des slides Marp..."
        logger.info("Démarrage de la génération des slides")
        
        # Vérifier les fichiers .md dans le dossier data
        md_files = list(data_path.glob("*.md"))
        if not md_files:
            logger.warning("Aucun fichier .md trouvé dans /data pour les slides")
            generated_slides = []
            slides_errors = []
        else:
            generated_slides = []
            slides_errors = []
            
            # Traitement de chaque fichier .md pour les slides
            for i, md_file in enumerate(md_files, 1):
                try:
                    task.progress = f"Étape 2/2 : Génération slides {i}/{len(md_files)}: {md_file.name}"
                    logger.info(f"Traitement de {md_file.name} pour les slides")
                    
                    # Extraction de l'ID du document depuis le nom du fichier
                    doc_name = md_file.stem
                    doc_id = doc_name.split('_')[-1] if '_' in doc_name else doc_name
                    
                    # Lecture du contenu Markdown
                    with open(md_file, 'r', encoding='utf-8') as f:
                        md_content = f.read()
                    logger.info(f"Fichier {md_file.name} lu: {len(md_content)} caractères")
                    
                    # Génération des slides avec le processeur existant
                    marp_content = generate_marp_slides_from_md(md_content)
                    
                    # Traitement du contenu retourné par l'IA
                    if hasattr(marp_content, 'content'):
                        markdown_content = marp_content.content
                    else:
                        markdown_content = str(marp_content)
                    
                    # Nettoyage du contenu
                    if "```markdown" in markdown_content:
                        markdown_content = markdown_content.split("```markdown", 1)[1]
                    if "```" in markdown_content:
                        markdown_content = markdown_content.split("```", 1)[0]
                    
                    markdown_content = markdown_content.strip()
                    if markdown_content.startswith("---"):
                        markdown_content = markdown_content.split("---", 1)[1].lstrip()
                    
                    # Diviser en slides
                    slides = markdown_content.split("---")
                    non_empty_slides = [slide.strip() for slide in slides if slide.strip()]
                    
                    # Construction du contenu final
                    final_content = "---\nmarp: true\n---\n\n" + "\n\n---\n\n".join(non_empty_slides)
                    
                    # Nom du fichier de sortie: task_id + doc_id
                    slides_filename = f"marp_{task.task_id}_{doc_id}.md"
                    slides_path = task_output_dir / slides_filename
                    
                    # Sauvegarde des slides
                    with open(slides_path, 'w', encoding='utf-8') as f:
                        f.write(final_content)
                    
                    generated_slides.append({
                        "source_file": str(md_file),
                        "slides_file": str(slides_path),
                        "slides_count": len(non_empty_slides),
                        "document_id": doc_id
                    })
                    
                    logger.info(f"Slides générées pour {md_file.name}: {slides_filename} ({len(non_empty_slides)} slides)")
                    
                except Exception as e:
                    error_info = {
                        "source_file": str(md_file),
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                    slides_errors.append(error_info)
                    logger.error(f"Erreur lors du traitement de {md_file.name}: {str(e)}")
        
        task.progress = "Finalisation : Sauvegarde des métadonnées..."
        
        # Ajouter un fichier de métadonnées globales
        metadata_output = task_output_dir / "task_metadata.json"
        task_metadata = {
            "task_id": task.task_id,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "request": task.request.model_dump(),
            "enrichment_statistics": enrichment_results["statistics"],
            "slides_statistics": {
                "total_documents": len(md_files),
                "successful_generations": len(generated_slides),
                "errors_count": len(slides_errors)
            },
            "generated_slides": generated_slides,
            "slides_errors": slides_errors
        }
        
        try:
            with open(metadata_output, 'w', encoding='utf-8') as f:
                json.dump(task_metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"Métadonnées globales sauvées: {metadata_output}")
        except Exception as e:
            logger.warning(f"Erreur lors de la sauvegarde des métadonnées: {str(e)}")
        
        # Finalisation de la tâche
        task.status = "completed"
        task.result = {
            "enrichment": enrichment_results,
            "slides": {
                "total_documents": len(md_files),
                "successful_generations": len(generated_slides),
                "errors_count": len(slides_errors),
                "generated_slides": generated_slides,
                "errors": slides_errors
            },
            "files": {
                "enrichment": enrichment_files,
                "metadata": str(metadata_output)
            }
        }
        task.completed_at = datetime.now().isoformat()
        
        # Message de statut final
        enrichment_stats = enrichment_results["statistics"]
        slides_count = len(generated_slides)
        slides_errors_count = len(slides_errors)
        
        if slides_errors_count > 0:
            task.progress = f"Terminé: Scénario enrichi ({enrichment_stats['total_novelties']} nouveautés), {slides_count}/{len(md_files)} slides générées"
        else:
            task.progress = f"Terminé: Scénario enrichi ({enrichment_stats['total_novelties']} nouveautés), {slides_count} slides générées"
        
        logger.info(f"Pipeline complète {task.task_id} terminée avec succès")
        
    except Exception as e:
        error_details = {
            "error_message": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        
        logger.error(f"Erreur dans la pipeline {task.task_id}: {error_details}")
        
        task.status = "failed"
        task.error = json.dumps(error_details, indent=2)
        task.completed_at = datetime.now().isoformat()
        task.progress = f"Erreur: {str(e)}"

@app.post("/sync-airtable", response_model=AirtableSyncResponse)
async def sync_airtable_articles(
    request: AirtableSyncRequest,
    background_tasks: BackgroundTasks
):
    """
    Synchronise les articles depuis Airtable vers le dossier data
    """
    # Génération d'un ID unique pour la tâche
    task_id = str(uuid.uuid4())
    
    # Création de la tâche
    task = EnrichmentTask(task_id, request)
    tasks_storage[task_id] = task
    
    # Lancement de la tâche en arrière-plan
    background_tasks.add_task(process_airtable_sync_task, task)
    
    return AirtableSyncResponse(
        task_id=task_id,
        status="pending",
        message=f"Synchronisation Airtable lancée. Vérifiez l'avancement avec /tasks/{task_id}"
    )

async def process_airtable_sync_task(task: EnrichmentTask):
    """Traitement asynchrone de la synchronisation Airtable"""
    try:
        logger.info(f"Démarrage de la synchronisation Airtable {task.task_id}")
        task.status = "running"
        task.progress = "Initialisation de la connexion Airtable..."
        
        # Configuration
        try:
            config = Config()
            airtable_api_key = config.AIRTABLE_API_KEY if hasattr(config, 'AIRTABLE_API_KEY') else os.environ.get('AIRTABLE_API_KEY')
            airtable_base_id = config.AIRTABLE_BASE_ID if hasattr(config, 'AIRTABLE_BASE_ID') else os.environ.get('AIRTABLE_BASE_ID')
            
            if not airtable_api_key:
                raise ValueError("AIRTABLE_API_KEY non configurée")
            if not airtable_base_id:
                raise ValueError("AIRTABLE_BASE_ID non configurée")
                
        except Exception as e:
            error_msg = f"Erreur de configuration Airtable: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        task.progress = "Connexion à Airtable..."
        
        # Initialisation du gestionnaire Airtable
        try:
            manager = AirtableArticleManager(
                api_key=airtable_api_key,
                base_id=airtable_base_id
            )
            logger.info("Gestionnaire Airtable initialisé")
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation Airtable: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Nettoyage si demandé
        if hasattr(task.request, 'clean_before_sync') and task.request.clean_before_sync:
            task.progress = "Nettoyage des anciens articles..."
            try:
                manager.clean_data_folder(task.request.data_directory)
                logger.info("Nettoyage terminé")
            except Exception as e:
                logger.warning(f"Erreur lors du nettoyage: {e}")
        
        task.progress = "Synchronisation des articles..."
        
        # Synchronisation
        try:
            sync_result = manager.sync_articles(task.request.data_directory)
            logger.info(f"Synchronisation terminée: {sync_result}")
        except Exception as e:
            error_msg = f"Erreur lors de la synchronisation: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Mise à jour du résultat
        task.status = "completed"
        task.result = sync_result
        task.completed_at = datetime.now().isoformat()
        task.progress = f"Terminé: {sync_result['articles_count']} articles synchronisés"
        logger.info(f"Tâche de synchronisation Airtable {task.task_id} terminée avec succès")
        
    except Exception as e:
        error_details = {
            "error_message": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        
        logger.error(f"Erreur dans la synchronisation Airtable {task.task_id}: {error_details}")
        
        task.status = "failed"
        task.error = json.dumps(error_details, indent=2)
        task.completed_at = datetime.now().isoformat()
        task.progress = f"Erreur: {str(e)}"

@app.post("/enrich", response_model=EnrichmentResponse)
async def enrich_scenario(
    request: EnrichmentRequest,
    background_tasks: BackgroundTasks
):
    """
    Lance l'enrichissement d'un scénario pédagogique avec les articles du répertoire data
    """
    # Génération d'un ID unique pour la tâche
    task_id = str(uuid.uuid4())
    
    # Création de la tâche
    task = EnrichmentTask(task_id, request)
    tasks_storage[task_id] = task
    
    # Lancement du traitement en arrière-plan
    background_tasks.add_task(process_enrichment_task, task)
    
    return EnrichmentResponse(
        task_id=task_id,
        status="pending",
        message="Enrichissement lancé en arrière-plan"
    )

@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Récupère le statut d'une tâche d'enrichissement
    """
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    task = tasks_storage[task_id]
    
    return TaskStatus(
        task_id=task.task_id,
        status=task.status,
        progress=task.progress,
        result=task.result,
        error=task.error,
        created_at=task.created_at,
        completed_at=task.completed_at
    )

@app.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: str):
    """
    Récupère les logs détaillés d'une tâche
    """
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    task = tasks_storage[task_id]
    
    detailed_info = {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
        "request_params": {
            "scenario_json": task.request.scenario_json,
            "data_directory": task.request.data_directory,
            "output_format": task.request.output_format
        }
    }
    
    if task.error:
        try:
            # Essayer de parser l'erreur comme JSON pour plus de détails
            detailed_info["error_details"] = json.loads(task.error)
        except:
            # Si ce n'est pas du JSON, garder comme string
            detailed_info["error"] = task.error
    
    if task.result:
        detailed_info["result"] = task.result
    
    return detailed_info

@app.get("/tasks")
async def list_tasks():
    """
    Liste toutes les tâches d'enrichissement
    """
    return [
        {
            "task_id": task.task_id,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at
        }
        for task in tasks_storage.values()
    ]

@app.get("/download/{task_id}")
async def download_task_results(task_id: str):
    """
    Télécharge tous les fichiers résultats d'une tâche dans un fichier ZIP
    """
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    task = tasks_storage[task_id]
    
    if task.status != "completed" or not task.result:
        raise HTTPException(status_code=400, detail="Tâche non terminée ou sans résultat")
    
    # Vérifier que le dossier de la tâche existe
    task_output_dir = Path(f"output/task_{task_id}")
    if not task_output_dir.exists():
        raise HTTPException(status_code=404, detail="Dossier de résultats non trouvé")
    
    # Créer un fichier ZIP temporaire
    zip_filename = f"task_{task_id}_results.zip"
    zip_path = Path(f"output/{zip_filename}")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Ajouter tous les fichiers du dossier de la tâche au ZIP
            for file_path in task_output_dir.iterdir():
                if file_path.is_file():
                    zipf.write(file_path, file_path.name)
                    logger.info(f"Ajouté au ZIP: {file_path.name}")
        
        logger.info(f"ZIP créé: {zip_path}")
        
        return FileResponse(
            str(zip_path),
            filename=zip_filename,
            media_type='application/zip',
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du ZIP: {str(e)}")
        if zip_path.exists():
            zip_path.unlink()  # Supprimer le fichier ZIP en cas d'erreur
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création du fichier ZIP: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Vérification de l'état de l'API
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """
    Page d'accueil de l'API
    """
    return {
        "message": "API Agrivision - Enrichissement de Scénarios",
        "documentation": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)