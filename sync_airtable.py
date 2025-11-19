#!/usr/bin/env python3
"""
Script pour synchroniser les articles depuis Airtable
"""

import os
import sys
from pathlib import Path
import argparse
import logging

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from loaders.airtable_loader import AirtableArticleManager

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description="Synchroniser les articles depuis Airtable")
    parser.add_argument("--data-folder", default="data", help="Dossier de destination des articles")
    parser.add_argument("--clean", action="store_true", help="Nettoyer les anciens articles avant sync")
    parser.add_argument("--api-key", help="Clé API Airtable (ou utiliser AIRTABLE_API_KEY)")
    parser.add_argument("--base-id", help="ID de la base Airtable (ou utiliser AIRTABLE_BASE_ID)")
    
    args = parser.parse_args()
    
    try:
        # Initialiser le gestionnaire Airtable
        print("🔌 Initialisation de la connexion Airtable...")
        manager = AirtableArticleManager(
            api_key=args.api_key,
            base_id=args.base_id
        )
        
        # Nettoyer si demandé
        if args.clean:
            print(f"🧹 Nettoyage du dossier {args.data_folder}...")
            manager.clean_data_folder(args.data_folder)
        
        # Synchroniser les articles
        print("🔄 Synchronisation des articles...")
        result = manager.sync_articles(args.data_folder)
        
        if result["success"]:
            print(f"✅ Synchronisation réussie!")
            print(f"   Articles récupérés: {result['articles_count']}")
            print(f"   Fichiers créés: {result['files_created']}")
            print(f"   Durée: {result['duration_seconds']:.2f}s")
            print(f"   Dossier: {args.data_folder}/")
            
            if result["saved_files"]:
                print("\n📄 Fichiers créés:")
                for file_path in result["saved_files"]:
                    print(f"   - {Path(file_path).name}")
        else:
            print(f"❌ Erreur lors de la synchronisation: {result.get('error', 'Erreur inconnue')}")
            return 1
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\n💡 Assurez-vous que les variables d'environnement sont configurées:")
        print("   - AIRTABLE_API_KEY: votre clé API Airtable")
        print("   - AIRTABLE_BASE_ID: l'ID de votre base Airtable")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())