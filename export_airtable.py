"""
Script pour exporter une base Airtable complète avec structure et données.
Génère un fichier JSON complet de la base et ses métadonnées.
"""

import os
import json
import requests
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

class AirtableExporter:
    """
    Exporteur complet pour base Airtable incluant structure et données.
    """
    
    def __init__(self, api_key: str, base_id: str):
        """
        Initialise l'exporteur Airtable.
        
        Args:
            api_key: Clé API Airtable
            base_id: ID de la base Airtable
        """
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = "https://api.airtable.com/v0"
        self.meta_base_url = "https://api.airtable.com/v0/meta"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_base_schema(self) -> Dict[str, Any]:
        """
        Récupère le schéma complet de la base (tables, champs, etc.).
        
        Returns:
            Dict contenant le schéma de la base
        """
        url = f"{self.meta_base_url}/bases/{self.base_id}/tables"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            schema_data = response.json()
            print(f"✅ Schéma récupéré: {len(schema_data.get('tables', []))} tables trouvées")
            
            return schema_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération du schéma: {e}")
            return {}
    
    def get_table_data(self, table_id: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Récupère toutes les données d'une table.
        
        Args:
            table_id: ID de la table
            table_name: Nom de la table
            
        Returns:
            Liste des enregistrements de la table
        """
        url = f"{self.base_url}/{self.base_id}/{table_id}"
        all_records = []
        offset = None
        
        try:
            while True:
                params = {"pageSize": 100}
                if offset:
                    params["offset"] = offset
                
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                records = data.get("records", [])
                all_records.extend(records)
                
                print(f"📄 {table_name}: {len(records)} enregistrements récupérés (total: {len(all_records)})")
                
                offset = data.get("offset")
                if not offset:
                    break
            
            print(f"✅ Table '{table_name}' complètement exportée: {len(all_records)} enregistrements")
            return all_records
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération des données de '{table_name}': {e}")
            return []
    
    def export_complete_base(self, output_dir: str = "export") -> str:
        """
        Exporte la base complète avec structure et données.
        
        Args:
            output_dir: Répertoire de sortie
            
        Returns:
            Chemin du fichier d'export généré
        """
        print("🚀 Démarrage de l'export complet de la base Airtable...")
        
        # Création du répertoire de sortie
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Récupération du schéma
        print("\n📋 Récupération du schéma de la base...")
        schema = self.get_base_schema()
        
        if not schema:
            print("❌ Impossible de récupérer le schéma, arrêt de l'export")
            return ""
        
        # Structure de l'export complet
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "base_id": self.base_id,
                "export_type": "complete_base"
            },
            "schema": schema,
            "tables_data": {}
        }
        
        # Export des données pour chaque table
        print("\n📊 Export des données des tables...")
        tables = schema.get("tables", [])
        
        for table in tables:
            table_id = table.get("id")
            table_name = table.get("name", f"Table_{table_id}")
            
            print(f"\n📋 Export de la table: {table_name}")
            
            # Récupération des données
            table_records = self.get_table_data(table_id, table_name)
            
            # Ajout à l'export avec métadonnées
            export_data["tables_data"][table_id] = {
                "table_info": {
                    "id": table_id,
                    "name": table_name,
                    "description": table.get("description", ""),
                    "fields_count": len(table.get("fields", [])),
                    "records_count": len(table_records)
                },
                "records": table_records
            }
        
        # Génération du fichier d'export
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"airtable_export_{self.base_id}_{timestamp}.json"
        export_path = output_path / export_filename
        
        print(f"\n💾 Sauvegarde de l'export...")
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            # Statistiques finales
            total_records = sum(
                table_data["table_info"]["records_count"] 
                for table_data in export_data["tables_data"].values()
            )
            total_tables = len(export_data["tables_data"])
            file_size = export_path.stat().st_size / 1024 / 1024  # MB
            
            print("\n🎉 Export terminé avec succès!")
            print("=" * 50)
            print(f"📁 Fichier: {export_path}")
            print(f"📊 Tables exportées: {total_tables}")
            print(f"📄 Total enregistrements: {total_records}")
            print(f"💾 Taille du fichier: {file_size:.2f} MB")
            print("=" * 50)
            
            return str(export_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return ""
    
    def export_schema_only(self, output_dir: str = "export") -> str:
        """
        Exporte uniquement le schéma de la base (structure sans données).
        
        Args:
            output_dir: Répertoire de sortie
            
        Returns:
            Chemin du fichier de schéma généré
        """
        print("📋 Export du schéma uniquement...")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        schema = self.get_base_schema()
        
        if not schema:
            return ""
        
        # Ajout de métadonnées
        schema_export = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "base_id": self.base_id,
                "export_type": "schema_only"
            },
            "schema": schema
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        schema_filename = f"airtable_schema_{self.base_id}_{timestamp}.json"
        schema_path = output_path / schema_filename
        
        try:
            with open(schema_path, 'w', encoding='utf-8') as f:
                json.dump(schema_export, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Schéma exporté: {schema_path}")
            return str(schema_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de l'export du schéma: {e}")
            return ""
    
    def export_table_structure_readable(self, output_dir: str = "export") -> str:
        """
        Génère un rapport lisible de la structure des tables.
        
        Args:
            output_dir: Répertoire de sortie
            
        Returns:
            Chemin du fichier rapport généré
        """
        print("📖 Génération du rapport de structure lisible...")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        schema = self.get_base_schema()
        
        if not schema:
            return ""
        
        # Génération du rapport markdown
        report_lines = []
        report_lines.append(f"# Structure Base Airtable - {self.base_id}")
        report_lines.append("")
        report_lines.append(f"**Export généré le:** {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
        report_lines.append("")
        
        tables = schema.get("tables", [])
        report_lines.append(f"**Nombre de tables:** {len(tables)}")
        report_lines.append("")
        
        for table in tables:
            table_name = table.get("name", "Table sans nom")
            table_id = table.get("id", "")
            description = table.get("description", "")
            
            report_lines.append(f"## Table: {table_name}")
            report_lines.append("")
            report_lines.append(f"- **ID:** `{table_id}`")
            if description:
                report_lines.append(f"- **Description:** {description}")
            report_lines.append("")
            
            # Champs de la table
            fields = table.get("fields", [])
            report_lines.append(f"### Champs ({len(fields)} champs)")
            report_lines.append("")
            report_lines.append("| Nom | Type | Description | Options |")
            report_lines.append("|-----|------|-------------|---------|")
            
            for field in fields:
                field_name = field.get("name", "")
                field_type = field.get("type", "")
                field_desc = field.get("description", "")
                field_options = field.get("options", {})
                
                options_str = ""
                if field_options:
                    if "choices" in field_options:
                        choices = [choice.get("name", "") for choice in field_options["choices"]]
                        options_str = f"Choix: {', '.join(choices)}"
                    elif "linkedTableId" in field_options:
                        options_str = f"Lien vers: {field_options['linkedTableId']}"
                    else:
                        options_str = str(field_options)[:50]
                
                report_lines.append(f"| {field_name} | {field_type} | {field_desc} | {options_str} |")
            
            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")
        
        # Sauvegarde du rapport
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"airtable_structure_{self.base_id}_{timestamp}.md"
        report_path = output_path / report_filename
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            print(f"✅ Rapport de structure généré: {report_path}")
            return str(report_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération du rapport: {e}")
            return ""


def main():
    """
    Fonction principale pour l'export Airtable.
    """
    print("🔧 Export Base Airtable - Agrivision")
    print("=" * 40)
    
    # Configuration depuis les variables d'environnement
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    
    if not api_key:
        print("❌ AIRTABLE_API_KEY non configurée dans .env")
        return
    
    if not base_id:
        print("❌ AIRTABLE_BASE_ID non configurée dans .env")
        return
    
    # Initialisation de l'exporteur
    exporter = AirtableExporter(api_key, base_id)
    
    # Menu de choix
    print("\nChoisissez le type d'export:")
    print("1. Export complet (structure + données)")
    print("2. Structure uniquement")
    print("3. Rapport de structure lisible")
    print("4. Tout exporter")
    
    choice = input("\nVotre choix (1-4): ").strip()
    
    if choice == "1":
        exporter.export_complete_base()
    elif choice == "2":
        exporter.export_schema_only()
    elif choice == "3":
        exporter.export_table_structure_readable()
    elif choice == "4":
        print("\n🚀 Export complet de tous les formats...")
        exporter.export_complete_base()
        exporter.export_schema_only()
        exporter.export_table_structure_readable()
    else:
        print("❌ Choix invalide")


if __name__ == "__main__":
    main()