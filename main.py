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
from src.loaders.word_loader import WordLoader
from src.processors.scientific_article_processor import PedagogicalScenarioProcessor
from src.models.pedagogical_scenario import PedagogicalScenario


class PedagogicalProcessor:
    """
    Classe principale pour orchestrer le traitement des scénarios pédagogiques.
    """
    
    def __init__(self, 
                 model_name: Optional[str] = None,
                 temperature: Optional[float] = None,
                 output_dir: Optional[str] = None):
        """
        Initialise le processeur de scénarios pédagogiques.
        
        Args:
            model_name: Nom du modèle LLM à utiliser (utilise config par défaut si None)
            temperature: Température du modèle (utilise config par défaut si None) 
            output_dir: Répertoire de sortie pour les résultats (utilise config par défaut si None)
        """
        # Configuration du logger
        self.logger = logging.getLogger(__name__)
        
        self.markdown_loader = MarkdownLoader()
        self.word_loader = WordLoader(extract_tables=True, preserve_formatting=True)
        self.processor = PedagogicalScenarioProcessor(
            model_name=model_name,
            temperature=temperature
        )
        self.output_dir = Path(output_dir or config.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
        
    def process_file(self, file_path: str) -> PedagogicalScenario:
        """
        Traite un seul fichier (markdown ou Word).
        
        Args:
            file_path: Chemin vers le fichier (.md ou .docx)
            
        Returns:
            Scénario pédagogique structuré
        """
        print(f"Traitement du fichier: {file_path}")
        
        # Détection du type de fichier et chargement approprié
        file_path_lower = file_path.lower()
        
        if file_path_lower.endswith('.md') or file_path_lower.endswith('.markdown'):
            # Fichier Markdown
            document = self.markdown_loader.load_file(file_path)
            document = self.markdown_loader.preprocess_content(document)
        elif file_path_lower.endswith('.docx'):
            # Fichier Word
            documents = self.word_loader.load(file_path)
            if not documents:
                raise ValueError(f"Aucun contenu extrait du fichier Word: {file_path}")
            document = documents[0]  # Prendre le premier document
        else:
            raise ValueError(f"Type de fichier non supporté: {file_path}. Formats supportés: .md, .markdown, .docx")
        
        # Extraction d'informations structurées
        scenario = self.processor.process_document(document)
        
        print(f"Scénario traité: {scenario.scenario_title or 'Sans titre'}...")
        return scenario
    
    def process_directory(self, 
                         directory_path: str,
                         pattern: Optional[str] = None,
                         recursive: bool = True) -> List[PedagogicalScenario]:
        """
        Traite tous les fichiers supportés d'un répertoire.
        
        Args:
            directory_path: Chemin vers le répertoire
            pattern: Pattern de fichiers à traiter (défaut: markdown et Word)
            recursive: Traitement récursif des sous-répertoires
            
        Returns:
            Liste des scénarios pédagogiques structurés
        """
        print(f"Traitement du répertoire: {directory_path}")
        print(f"Récursif: {recursive}")
        
        # Si aucun pattern spécifié, traiter markdown et Word
        if pattern is None:
            # Chargement des documents markdown
            md_documents = self.markdown_loader.load_directory(
                directory_path, 
                pattern=config.MARKDOWN_PATTERN,
                recursive=recursive
            )
            
            # Chargement des documents Word
            word_documents = self.word_loader.load_directory(
                directory_path,
                pattern="*.docx", 
                recursive=recursive
            )
            
            documents = md_documents + word_documents
        else:
            # Pattern spécifique fourni - déterminer le type
            if pattern.endswith('.docx') or 'docx' in pattern:
                documents = self.word_loader.load_directory(
                    directory_path,
                    pattern=pattern,
                    recursive=recursive
                )
            else:
                documents = self.markdown_loader.load_directory(
                    directory_path,
                    pattern=pattern,
                    recursive=recursive
                )
        
        print(f"{len(documents)} documents trouvés")
        
        if not documents:
            print("Aucun document trouvé à traiter.")
            return []
        
        # Traitement des documents
        print("Extraction des informations structurées...")
        scenarios = self.processor.batch_process_with_retry(
            documents, 
            max_retries=config.MAX_RETRIES
        )
        
        return scenarios
    
    def save_results(self, 
                    scenarios: List[PedagogicalScenario], 
                    format: str = "json",
                    filename: Optional[str] = None) -> str:
        """
        Sauvegarde les résultats dans le format spécifié.
        
        Args:
            scenarios: Liste des scénarios pédagogiques à sauvegarder
            format: Format de sortie ("json", "csv", "txt")
            filename: Nom du fichier (généré automatiquement si None)
            
        Returns:
            Chemin vers le fichier de sortie
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scenarios_{timestamp}.{format}"
        
        output_path = self.output_dir / filename
        
        if format == "json":
            self._save_as_json(scenarios, output_path)
        elif format == "csv":
            self._save_as_csv(scenarios, output_path)
        elif format == "txt":
            self._save_as_txt(scenarios, output_path)
        else:
            raise ValueError(f"Format non supporté: {format}")
        
        print(f"Résultats sauvegardés dans: {output_path}")
        return str(output_path)
    
    def _save_as_json(self, scenarios: List[PedagogicalScenario], path: Path):
        """Sauvegarde en format JSON."""
        data = {
            "metadata": {
                "total_scenarios": len(scenarios),
                "processing_date": datetime.now().isoformat(),
                "version": "1.0"
            },
            "scenarios": [scenario.to_dict() for scenario in scenarios]
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def _save_as_csv(self, scenarios: List[PedagogicalScenario], path: Path):
        """Sauvegarde en format CSV."""
        import csv
        
        if not scenarios:
            return
        
        # Déterminer les colonnes à partir du premier scénario
        fieldnames = list(scenarios[0].to_dict().keys())
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for scenario in scenarios:
                row = scenario.to_dict()
                # Convertir les listes en chaînes de caractères
                for key, value in row.items():
                    if isinstance(value, list):
                        row[key] = "; ".join(str(v) for v in value)
                writer.writerow(row)
    
    def _save_as_txt(self, scenarios: List[PedagogicalScenario], path: Path):
        """Sauvegarde en format texte lisible."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT D'EXTRACTION DE SCÉNARIOS PÉDAGOGIQUES\n")
            f.write(f"Date de traitement: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nombre de scénarios: {len(scenarios)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, scenario in enumerate(scenarios, 1):
                f.write(f"SCÉNARIO {i}\n")
                f.write("-" * 40 + "\n")
                f.write(f"Séquence N°: {scenario.sequence_number}\n")
                f.write(f"Horaires: {scenario.start_time} - {scenario.end_time}\n")
                duration = scenario.calculate_duration()
                if duration:
                    f.write(f"Durée: {duration} minutes\n")
                f.write(f"Public cible: {scenario.target_audience or 'Non spécifié'}\n")
                f.write(f"Confiance: {scenario.confidence_score or 'N/A'}\n\n")
                f.write(f"Contenu:\n{scenario.content}\n\n")
                
                if scenario.pedagogical_methods:
                    f.write(f"Méthodes pédagogiques:\n")
                    for method in scenario.pedagogical_methods:
                        f.write(f"- {method}\n")
                    f.write("\n")
                
                if scenario.evaluation_modalities:
                    f.write(f"Modalités d'évaluation:\n")
                    for modality in scenario.evaluation_modalities:
                        f.write(f"- {modality}\n")
                    f.write("\n")
                
                f.write("=" * 80 + "\n\n")
    
    def generate_report(self, scenarios: List[PedagogicalScenario]) -> dict:
        """
        Génère un rapport détaillé des résultats.
        
        Args:
            scenarios: Liste des scénarios pédagogiques traités
            
        Returns:
            Dictionnaire contenant le rapport
        """
        stats = self.processor.get_processing_stats(scenarios)
        
        report = {
            "processing_summary": stats,
            "timestamp": datetime.now().isoformat(),
            "sample_scenarios": [
                {
                    "title": scenario.scenario_title or "Sans titre",
                    "days_count": scenario.get_total_days(),
                    "sequences_count": scenario.get_total_sequences(),
                    "confidence": scenario.confidence_score,
                    "duration_hours": round(scenario.get_total_duration() / 60, 1)
                }
                for scenario in scenarios[:5]  # Premiers 5 scénarios comme échantillon
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
        processor = PedagogicalProcessor(
            model_name=args.model,
            temperature=args.temperature,
            output_dir=args.output_dir
        )
        
        # Traitement
        input_path = Path(args.input_path)
        
        if input_path.is_file():
            print("Traitement d'un fichier unique...")
            scenario = processor.process_file(str(input_path))
            scenarios = [scenario]
        elif input_path.is_dir():
            print("Traitement d'un répertoire...")
            scenarios = processor.process_directory(
                str(input_path),
                pattern=args.pattern,
                recursive=not args.no_recursive
            )
        else:
            print(f"Erreur: Le chemin {input_path} n'existe pas.")
            return 1
        
        if not scenarios:
            print("Aucun article n'a pu être traité.")
            return 1
        
        # Sauvegarde des résultats
        output_file = processor.save_results(scenarios, format=args.format)
        
        # Génération et affichage du rapport
        report = processor.generate_report(scenarios)
        print("\nRAPPORT DE TRAITEMENT:")
        print(f"Scénarios traités: {report['processing_summary']['total_scenarios']}")
        print(f"Total jours: {report['processing_summary']['total_days']}")
        print(f"Total séquences: {report['processing_summary']['total_sequences']}")
        print(f"Durée totale: {report['processing_summary']['total_duration_hours']}h")
        print(f"Score de confiance moyen: {report['processing_summary']['average_confidence_score']}")
        print(f"Séquences avec méthodes: {report['processing_summary']['content_completion_rates']['sequences_with_methods']}%")
        
        print(f"\nTraitement terminé avec succès!")
        print(f"Résultats disponibles dans: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"Erreur lors du traitement: {e}")
        return 1


if __name__ == "__main__":
    exit(main())