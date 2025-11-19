"""
Script de validation pour détecter les incohérences dans le code Agrivision
"""

import ast
import inspect
from pathlib import Path
from typing import Dict, List, Set
from src.models.pedagogical_scenario import PedagogicalScenario, PedagogicalSequence, PedagogicalDay
from src.config import Config

def get_class_attributes(cls):
    """Récupère tous les attributs d'une classe Pydantic"""
    if hasattr(cls, '__fields__'):
        # Pydantic v1
        return set(cls.__fields__.keys())
    elif hasattr(cls, 'model_fields'):
        # Pydantic v2
        return set(cls.model_fields.keys())
    else:
        # Fallback: inspection manuelle
        return set([attr for attr in dir(cls) if not attr.startswith('_')])

def analyze_attribute_usage():
    """Analyse l'usage des attributs dans le code"""
    print("🔍 Analyse des attributs utilisés dans le code")
    print("=" * 60)
    
    # Attributs des modèles Pydantic
    scenario_attrs = get_class_attributes(PedagogicalScenario)
    sequence_attrs = get_class_attributes(PedagogicalSequence)
    day_attrs = get_class_attributes(PedagogicalDay)
    config_attrs = set([attr for attr in dir(Config) if not attr.startswith('_')])
    
    print(f"📋 Attributs PedagogicalScenario: {sorted(scenario_attrs)}")
    print(f"📋 Attributs PedagogicalSequence: {sorted(sequence_attrs)}")
    print(f"📋 Attributs PedagogicalDay: {sorted(day_attrs)}")
    print(f"📋 Attributs Config: {sorted(list(config_attrs))}")
    print()
    
    # Chercher les fichiers Python
    python_files = list(Path('.').rglob('*.py'))
    
    issues = []
    
    for file_path in python_files:
        if 'venv' in str(file_path) or '__pycache__' in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Patterns à détecter
            patterns = [
                # Attributs de séquence potentiellement incorrects
                ('sequence.activities', 'Utiliser sequence.resources_needed'),
                ('sequence.materials', 'Utiliser sequence.resources_needed'),
                ('scenario.title', 'Utiliser scenario.scenario_title'),
                ('config.openai_api_key', 'Utiliser config.OPENAI_API_KEY'),
                ('config.mistral_api_key', 'Utiliser config.MISTRAL_API_KEY (si défini)'),
                ('config.api_key', 'Spécifier quel type de clé API'),
            ]
            
            for pattern, suggestion in patterns:
                if pattern in content:
                    line_num = None
                    for i, line in enumerate(content.split('\n'), 1):
                        if pattern in line:
                            line_num = i
                            break
                    
                    issues.append({
                        'file': str(file_path),
                        'line': line_num,
                        'pattern': pattern,
                        'suggestion': suggestion,
                        'severity': 'error' if 'title' in pattern else 'warning'
                    })
                    
        except Exception as e:
            print(f"⚠️  Erreur lors de la lecture de {file_path}: {e}")
    
    return issues

def check_imports():
    """Vérifie les imports potentiellement problématiques"""
    print("📦 Vérification des imports")
    print("=" * 30)
    
    python_files = list(Path('.').rglob('*.py'))
    import_issues = []
    
    for file_path in python_files:
        if 'venv' in str(file_path) or '__pycache__' in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier les imports problématiques
            problematic_imports = [
                'from config import',  # Devrait être 'from src.config import'
                'import config',       # Devrait être 'from src.config import Config'
            ]
            
            for bad_import in problematic_imports:
                if bad_import in content:
                    import_issues.append({
                        'file': str(file_path),
                        'issue': f"Import potentiellement incorrect: {bad_import}",
                        'suggestion': "Utiliser 'from src.config import Config'"
                    })
                    
        except Exception as e:
            continue
    
    return import_issues

def validate_json_compatibility():
    """Vérifie la compatibilité avec les fichiers JSON existants"""
    print("📄 Vérification de la compatibilité JSON")
    print("=" * 40)
    
    json_files = list(Path('.').rglob('*.json'))
    json_issues = []
    
    for json_file in json_files:
        if 'node_modules' in str(json_file) or 'venv' in str(json_file):
            continue
            
        try:
            import json
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Vérifier la structure des scénarios
            if 'scenarios' in data:
                for scenario in data['scenarios']:
                    # Vérifier les attributs attendus vs réels
                    scenario_keys = set(scenario.keys())
                    expected_scenario_keys = get_class_attributes(PedagogicalScenario)
                    
                    missing_keys = expected_scenario_keys - scenario_keys
                    extra_keys = scenario_keys - expected_scenario_keys
                    
                    if missing_keys:
                        json_issues.append({
                            'file': str(json_file),
                            'issue': f"Clés manquantes dans le scénario: {missing_keys}",
                            'severity': 'warning'
                        })
                    
                    if extra_keys:
                        json_issues.append({
                            'file': str(json_file),
                            'issue': f"Clés inattendues dans le scénario: {extra_keys}",
                            'severity': 'info'
                        })
                        
        except Exception as e:
            json_issues.append({
                'file': str(json_file),
                'issue': f"Erreur lors de la lecture: {e}",
                'severity': 'error'
            })
    
    return json_issues

def main():
    """Fonction principale de validation"""
    print("🔧 VALIDATION COMPLÈTE DU CODE AGRIVISION")
    print("=" * 70)
    print()
    
    # 1. Analyse des attributs
    attribute_issues = analyze_attribute_usage()
    
    # 2. Vérification des imports
    import_issues = check_imports()
    
    # 3. Compatibilité JSON
    json_issues = validate_json_compatibility()
    
    # Rapport des problèmes
    print("📊 RÉSUMÉ DES PROBLÈMES DÉTECTÉS")
    print("=" * 50)
    
    total_issues = len(attribute_issues) + len(import_issues) + len(json_issues)
    
    if total_issues == 0:
        print("✅ Aucun problème détecté! Le code semble cohérent.")
        return
    
    # Problèmes d'attributs
    if attribute_issues:
        print(f"⚠️  {len(attribute_issues)} problèmes d'attributs détectés:")
        for issue in attribute_issues:
            severity_icon = "🔴" if issue['severity'] == 'error' else "🟡"
            print(f"   {severity_icon} {issue['file']}:{issue['line']} - {issue['pattern']}")
            print(f"      💡 {issue['suggestion']}")
        print()
    
    # Problèmes d'imports
    if import_issues:
        print(f"📦 {len(import_issues)} problèmes d'imports détectés:")
        for issue in import_issues:
            print(f"   🔴 {issue['file']} - {issue['issue']}")
            print(f"      💡 {issue['suggestion']}")
        print()
    
    # Problèmes JSON
    if json_issues:
        print(f"📄 {len(json_issues)} problèmes JSON détectés:")
        for issue in json_issues:
            severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}[issue['severity']]
            print(f"   {severity_icon} {issue['file']} - {issue['issue']}")
        print()
    
    print(f"🏁 Total: {total_issues} problèmes trouvés")
    print("\n💡 Corrigez ces problèmes pour éviter les erreurs d'exécution.")

if __name__ == "__main__":
    main()