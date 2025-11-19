"""
Script pour enrichir un scénario pédagogique avec des articles scientifiques
et exporter en format markdown.
"""

import json
import argparse
from pathlib import Path
from typing import Optional

from src.config import config, init_config
from src.models.pedagogical_scenario import PedagogicalScenario
from src.enrichment.scenario_enrichment import ScenarioEnrichment


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


def main():
    """Fonction principale d'enrichissement."""
    parser = argparse.ArgumentParser(
        description="Enrichissement de scénario pédagogique avec articles scientifiques"
    )
    
    parser.add_argument(
        "scenario_json",
        help="Chemin vers le fichier JSON du scénario à enrichir"
    )
    
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Répertoire contenant les articles scientifiques (défaut: data)"
    )
    
    parser.add_argument(
        "--output",
        default=None,
        help="Chemin de sortie du fichier markdown enrichi (défaut: auto-généré)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Mode debug avec informations détaillées"
    )
    
    args = parser.parse_args()
    
    # Initialisation
    init_config()
    
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        print("🚀 Démarrage de l'enrichissement du scénario pédagogique")
        print("=" * 60)
        
        # 1. Chargement du scénario
        print(f"📖 Chargement du scénario: {args.scenario_json}")
        scenario = load_scenario_from_json(args.scenario_json)
        print(f"   ✅ Scénario '{scenario.scenario_title}' chargé")
        print(f"   📊 {scenario.get_total_days()} jours, {scenario.get_total_sequences()} séquences")
        
        # 2. Initialisation de l'enrichisseur
        print(f"\n🔬 Initialisation de l'enrichisseur...")
        enricher = ScenarioEnrichment()
        
        # 3. Analyse des articles scientifiques
        print(f"\n📚 Analyse des articles dans: {args.data_dir}")
        articles = enricher.analyze_scientific_articles(args.data_dir)
        
        if not articles:
            print("⚠️  Aucun article trouvé. Enrichissement non possible.")
            return 1
        
        print(f"   ✅ {len(articles)} articles analysés:")
        for article in articles:
            print(f"   - {article['title']}")
            print(f"     Mots-clés: {', '.join(article['keywords'][:5])}")
        
        # 4. Enrichissement du scénario
        print(f"\n🎯 Enrichissement du scénario avec les articles...")
        enriched_scenario = enricher.enrich_scenario(scenario, articles)
        
        # Statistiques d'enrichissement
        total_suggestions = 0
        relevant_sequences = 0
        
        for day_enrich in enriched_scenario["enrichments"]["days"]:
            for seq_enrich in day_enrich["sequences"]:
                if seq_enrich["suggestions"]:
                    relevant_sequences += 1
                    for suggestion_group in seq_enrich["suggestions"]:
                        total_suggestions += len(suggestion_group["nouveautes"])
        
        print(f"   ✅ Enrichissement terminé:")
        print(f"   🆕 {total_suggestions} nouveautés scientifiques identifiées")
        print(f"   🎯 {relevant_sequences} séquences enrichies (sur {scenario.get_total_sequences()})")
        print(f"   🌟 {len(enriched_scenario['enrichments']['global_suggestions'])} suggestions globales")
        
        # 5. Export en markdown
        if args.output is None:
            scenario_name = scenario.scenario_title or "scenario"
            safe_name = "".join(c for c in scenario_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()
            args.output = f"output/{safe_name}_enrichi.md"
        
        print(f"\n📝 Export du scénario enrichi...")
        output_path = enricher.export_enriched_markdown(enriched_scenario, args.output)
        
        # 6. Sauvegarde du JSON enrichi pour debug
        if args.debug:
            json_debug_path = args.output.replace('.md', '_debug.json')
            with open(json_debug_path, 'w', encoding='utf-8') as f:
                json.dump(enriched_scenario, f, indent=2, ensure_ascii=False, default=str)
            print(f"🔍 Données de debug sauvées: {json_debug_path}")
        
        print("\n" + "=" * 60)
        print("✅ ENRICHISSEMENT TERMINÉ AVEC SUCCÈS!")
        print(f"📄 Scénario enrichi disponible: {output_path}")
        
        # Résumé final
        print(f"\n📋 RÉSUMÉ:")
        print(f"   • Scénario original: {scenario.get_total_sequences()} séquences")
        print(f"   • Articles consultés: {len(articles)}")
        print(f"   • Nouveautés scientifiques: {total_suggestions}")
        print(f"   • Séquences avec nouveautés: {relevant_sequences}/{scenario.get_total_sequences()}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Fichier non trouvé: {e}")
        return 1
    except Exception as e:
        print(f"❌ Erreur lors de l'enrichissement: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())