"""
Module pour enrichir des scénarios pédagogiques avec des suggestions 
basées sur des articles scientifiques.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from ..models.pedagogical_scenario import PedagogicalScenario, PedagogicalDay, PedagogicalSequence
from ..loaders.markdown_loader import MarkdownLoader
from ..config import config


class ScenarioEnrichment:
    """
    Classe pour enrichir des scénarios pédagogiques avec des suggestions
    basées sur des articles scientifiques.
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialise l'enrichisseur de scénarios.
        
        Args:
            llm: Modèle de langage à utiliser
        """
        if llm is None:
            model_config = config.get_model_config()
            self.llm = ChatOpenAI(
                model=model_config["model"],
                temperature=0.3,  # Température plus basse pour plus de précision
                max_tokens=model_config["max_tokens"],
                openai_api_key=config.OPENAI_API_KEY,
                openai_api_base=config.OPENAI_API_BASE
            )
        else:
            self.llm = llm
        
        self.loader = MarkdownLoader()
        
        # Template pour analyser les articles scientifiques
        self.analysis_template = PromptTemplate(
            input_variables=["article_content", "sequence_info"],
            template="""
Vous êtes un expert en ingénierie pédagogique et en agronomie.

Analysez l'article scientifique et identifiez UNIQUEMENT les NOUVEAUTÉS SCIENTIFIQUES RÉCENTES 
qui pourraient enrichir cette séquence pédagogique de manière significative.

ARTICLE SCIENTIFIQUE:
{article_content}

SÉQUENCE PÉDAGOGIQUE:
Titre: {sequence_title}
Objectifs: {sequence_objectives}  
Contenu: {sequence_content}

CRITÈRES STRICTS:
1. Ne suggérer QUE des découvertes récentes, méthodes innovantes, ou résultats d'études récentes
2. La nouveauté doit être DIRECTEMENT pertinente pour cette séquence spécifique
3. Ignorer les concepts de base déjà connus
4. Maximum 2-3 suggestions de haute qualité, sinon RIEN
5. Soyez exigeant sur la pertinence

Format de réponse:
PERTINENCE: [score 1-5, 5=très pertinent avec vraies nouveautés]
NOUVEAUTÉS SCIENTIFIQUES:
- [Nouveauté 1: Description détaillée et comment l'intégrer]
- [Nouveauté 2: Description détaillée et comment l'intégrer]

Si aucune nouveauté pertinente: répondre simplement "PERTINENCE: 1"
"""
        )
    
    def analyze_scientific_articles(self, data_directory: str) -> List[Dict[str, Any]]:
        """
        Analyse tous les articles scientifiques du répertoire data.
        
        Args:
            data_directory: Chemin vers le répertoire contenant les articles
            
        Returns:
            Liste des articles analysés avec leur contenu et métadonnées
        """
        data_path = Path(data_directory)
        if not data_path.exists():
            raise FileNotFoundError(f"Répertoire non trouvé: {data_directory}")
        
        articles = []
        
        # Chargement des documents
        documents = self.loader.load_directory(
            str(data_path),
            pattern="*.md",
            recursive=True
        )
        
        for doc in documents:
            article_info = {
                "source": doc.metadata.get("source", "unknown"),
                "title": self._extract_title_from_content(doc.page_content),
                "content": doc.page_content,
                "keywords": self._extract_keywords(doc.page_content),
                "summary": self._create_summary(doc.page_content)
            }
            articles.append(article_info)
        
        print(f"📚 {len(articles)} articles scientifiques analysés")
        return articles
    
    def enrich_scenario(self, scenario: PedagogicalScenario, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enrichit un scénario pédagogique avec des suggestions basées sur les articles.
        
        Args:
            scenario: Scénario pédagogique à enrichir
            articles: Liste des articles scientifiques analysés
            
        Returns:
            Scénario enrichi avec suggestions
        """
        enriched_scenario = {
            "scenario_original": scenario.model_dump(),
            "enrichments": {
                "global_suggestions": [],
                "days": []
            },
            "articles_used": [{"title": art["title"], "source": art["source"]} for art in articles]
        }
        
        # Suggestions globales pour le scénario complet
        global_suggestions = self._get_global_suggestions(scenario, articles)
        enriched_scenario["enrichments"]["global_suggestions"] = global_suggestions
        
        # Extraire toutes les nouveautés scientifiques des articles
        print("🔬 Extraction des nouveautés scientifiques...")
        all_novelties = self._extract_all_novelties(articles)
        print(f"📋 {len(all_novelties)} nouveautés extraites")
        
        # Distribuer chaque nouveauté à la séquence la plus pertinente
        novelty_assignments = self._assign_novelties_to_sequences(scenario, all_novelties)
        
        # Enrichissement par jour
        for day in scenario.days:
            enriched_day = {
                "day_number": day.day_number,
                "day_title": day.day_title,
                "sequences": []
            }
            
            # Enrichissement par séquence avec les nouveautés assignées
            for sequence in day.sequences:
                sequence_key = f"{day.day_number}-{sequence.sequence_number}"
                assigned_novelties = novelty_assignments.get(sequence_key, [])
                enriched_sequence = self._create_enriched_sequence(sequence, assigned_novelties)
                enriched_day["sequences"].append(enriched_sequence)
            
            enriched_scenario["enrichments"]["days"].append(enriched_day)
        
        return enriched_scenario
    
    def _extract_all_novelties(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extrait toutes les nouveautés scientifiques de tous les articles."""
        all_novelties = []
        
        for article in articles:
            try:
                prompt = f"""
Analysez cet article scientifique et identifiez LA CONCLUSION PRINCIPALE.

ARTICLE SCIENTIFIQUE:
Titre: {article['title']}
Contenu: {article['content'][:4000]}

OBJECTIF:
Extraire la conclusion principale de cet article - la découverte, innovation ou résultat le plus significatif.

Cherchez dans l'article les sections comme:
- Conclusions
- Conclusion
- Conclusions Opérationnelles 
- Résultats principaux
- Principales découvertes

CRITÈRES:
- Un seul résultat ou conclusion majeure
- Innovation méthodologique principale
- Découverte scientifique clé
- Recommandation pratique principale

RÉPONSE ATTENDUE:
Rédigez en une phrase claire et concise la conclusion principale de l'étude.

Exemple de format: "L'étude démontre que [découverte principale] grâce à [méthode/innovation] ce qui permet [impact pratique]."

Si aucune conclusion claire, répondez: "AUCUNE CONCLUSION"
"""

                response = self.llm.invoke([{"role": "user", "content": prompt}])
                conclusion = response.content.strip()
                
                if "AUCUNE CONCLUSION" not in conclusion and conclusion:
                    all_novelties.append({
                        "nouveaute": conclusion,
                        "article_title": article['title'],
                        "article_source": article['source'],
                        "article": article
                    })
                    print(f"📋 Conclusion extraite de {article['title']}: {conclusion[:80]}...")
                                
            except Exception as e:
                print(f"Erreur lors de l'extraction des nouveautés de {article['title']}: {e}")
                continue
                
        return all_novelties
    
    def _analyze_sequence_relevance(self, sequence: PedagogicalSequence, nouveaute: str) -> float:
        """Analyse la pertinence d'une nouveauté pour une séquence spécifique."""
        try:
            sequence_info = {
                "title": sequence.title or f"Séquence {sequence.sequence_number}",
                "objectives": ", ".join(sequence.objectives) if sequence.objectives else "Non spécifiés",
                "content": sequence.content,
                "methods": ", ".join(sequence.pedagogical_methods),
                "activities": ", ".join(getattr(sequence, 'activities', [])),
                "materials": ", ".join(getattr(sequence, 'materials', []))
            }
            
            prompt = f"""
Évaluez la pertinence de cette nouveauté scientifique pour cette séquence pédagogique précise.

SÉQUENCE PÉDAGOGIQUE:
Titre: {sequence_info['title']}
Objectifs: {sequence_info['objectives']}
Contenu: {sequence_info['content']}
Méthodes: {sequence_info['methods']}

NOUVEAUTÉ SCIENTIFIQUE:
{nouveaute}

Donnez un score de pertinence de 0 à 5:
- 5: Parfaitement aligné avec les objectifs et activités de cette séquence
- 4: Très pertinent, peut enrichir significativement cette séquence
- 3: Pertinent mais pas spécifiquement pour cette séquence
- 2: Peu pertinent pour cette séquence précise
- 1: Marginalement lié
- 0: Non pertinent

Répondez UNIQUEMENT par un chiffre de 0 à 5.
"""

            response = self.llm.invoke([{"role": "user", "content": prompt}])
            score_text = response.content.strip()
            
            try:
                return float(score_text)
            except:
                # Si le parsing échoue, essayer d'extraire le premier chiffre
                import re
                match = re.search(r'[0-5]', score_text)
                return float(match.group()) if match else 0.0
                
        except Exception as e:
            print(f"Erreur lors de l'évaluation de pertinence: {e}")
            return 0.0
    
    def _assign_novelties_to_sequences(self, scenario: PedagogicalScenario, all_novelties: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Assigne chaque nouveauté à la séquence la plus pertinente."""
        assignments = {}
        
        for novelty in all_novelties:
            best_sequence = None
            best_score = 0
            best_key = None
            
            # Trouver la séquence avec le meilleur score de pertinence
            for day in scenario.days:
                for sequence in day.sequences:
                    score = self._analyze_sequence_relevance(sequence, novelty["nouveaute"])
                    sequence_key = f"{day.day_number}-{sequence.sequence_number}"
                    
                    if score >= 4.0 and score > best_score:
                        best_score = score
                        best_sequence = sequence
                        best_key = sequence_key
            
            # Assigner la nouveauté à la meilleure séquence
            if best_key:
                if best_key not in assignments:
                    assignments[best_key] = []
                assignments[best_key].append({
                    "nouveaute": novelty["nouveaute"],
                    "article_title": novelty["article_title"],
                    "article_source": novelty["article_source"],
                    "pertinence": best_score
                })
                print(f"📍 Nouveauté assignée à la séquence {best_key} (score: {best_score:.1f})")
        
        return assignments
    
    def _create_enriched_sequence(self, sequence: PedagogicalSequence, assigned_novelties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crée une séquence enrichie avec les nouveautés assignées."""
        enriched_sequence = {
            "sequence_number": sequence.sequence_number,
            "sequence_title": sequence.title or f"Séquence {sequence.sequence_number}",
            "original_content": sequence.model_dump(),
            "suggestions": []
        }
        
        if assigned_novelties:
            # Grouper par article
            suggestions_by_article = {}
            for novelty in assigned_novelties:
                article_title = novelty["article_title"]
                if article_title not in suggestions_by_article:
                    suggestions_by_article[article_title] = {
                        "article_source": article_title,
                        "pertinence_moyenne": 0,
                        "nouveautes": []
                    }
                suggestions_by_article[article_title]["nouveautes"].append(novelty["nouveaute"])
            
            # Calculer pertinence moyenne par article
            for article_title, suggestion in suggestions_by_article.items():
                relevant_scores = [n["pertinence"] for n in assigned_novelties if n["article_title"] == article_title]
                suggestion["pertinence_moyenne"] = sum(relevant_scores) / len(relevant_scores) if relevant_scores else 0
            
            enriched_sequence["suggestions"] = list(suggestions_by_article.values())
            print(f"✅ Séquence {sequence.sequence_number}: {len(assigned_novelties)} nouveautés assignées")
        
        return enriched_sequence
    
    def _enrich_sequence_with_relevance(self, sequence: PedagogicalSequence, all_novelties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enrichit une séquence en analysant la pertinence de chaque nouveauté.
        """
        enriched_sequence = {
            "sequence_number": sequence.sequence_number,
            "sequence_title": sequence.title or f"Séquence {sequence.sequence_number}",
            "original_content": sequence.model_dump(),
            "suggestions": []
        }
        
        # Analyser chaque nouveauté pour cette séquence
        sequence_novelties = []
        for novelty in all_novelties:
            relevance_score = self._analyze_sequence_relevance(sequence, novelty["nouveaute"])
            
            # Seuil de pertinence élevé: 4/5 minimum
            if relevance_score >= 4.0:
                sequence_novelties.append({
                    "nouveaute": novelty["nouveaute"],
                    "article_title": novelty["article_title"],
                    "article_source": novelty["article_source"],
                    "pertinence": relevance_score
                })
        
        # Grouper par article source
        suggestions_by_article = {}
        for novelty in sequence_novelties:
            article_title = novelty["article_title"]
            if article_title not in suggestions_by_article:
                suggestions_by_article[article_title] = {
                    "article_source": article_title,
                    "pertinence_moyenne": 0,
                    "nouveautes": []
                }
            suggestions_by_article[article_title]["nouveautes"].append(novelty["nouveaute"])
        
        # Calculer pertinence moyenne par article
        for article_title, suggestion in suggestions_by_article.items():
            relevant_scores = [n["pertinence"] for n in sequence_novelties if n["article_title"] == article_title]
            suggestion["pertinence_moyenne"] = sum(relevant_scores) / len(relevant_scores) if relevant_scores else 0
        
        enriched_sequence["suggestions"] = list(suggestions_by_article.values())
        
        if sequence_novelties:
            print(f"📍 Séquence {sequence.sequence_number}: {len(sequence_novelties)} nouveautés pertinentes trouvées")
        
        return enriched_sequence
    
    def _enrich_sequence(self, sequence: PedagogicalSequence, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Méthode legacy - maintenue pour compatibilité.
        """
        return self._enrich_sequence_with_relevance(sequence, self._extract_all_novelties(articles))
    
    def _parse_text_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse une réponse texte structurée pour les nouveautés scientifiques.
        """
        result = {
            "pertinence_score": 0,
            "nouveautes": []
        }
        
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("PERTINENCE:"):
                # Extraire le score
                try:
                    score_text = line.replace("PERTINENCE:", "").strip()
                    result["pertinence_score"] = int(score_text.split()[0])
                except:
                    result["pertinence_score"] = 1
            
            elif line == "NOUVEAUTÉS SCIENTIFIQUES:":
                current_section = "nouveautes"
            
            elif line.startswith("-") and current_section == "nouveautes":
                nouveaute_text = line[1:].strip()
                if nouveaute_text:  # Ne pas inclure les lignes vides
                    result["nouveautes"].append(nouveaute_text)
        
        return result
    
    def _get_global_suggestions(self, scenario: PedagogicalScenario, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Génère des suggestions globales pour tout le scénario.
        """
        global_prompt = f"""
Analysez le scénario pédagogique et les articles scientifiques pour proposer 
des améliorations générales du programme de formation.

SCÉNARIO: {scenario.scenario_title}
OBJECTIFS GLOBAUX: {', '.join(scenario.global_objectives)}
DURÉE: {scenario.get_total_days()} jours, {scenario.get_total_sequences()} séquences

ARTICLES SCIENTIFIQUES DISPONIBLES:
{chr(10).join([f"- {art['title']}: {art['summary'][:200]}..." for art in articles])}

Proposez 3-4 suggestions d'amélioration du programme:

SUGGESTIONS GLOBALES:
- [Suggestion 1 avec justification]
- [Suggestion 2 avec justification]
- [Suggestion 3 avec justification]
"""
        
        try:
            response = self.llm.invoke([{"role": "user", "content": global_prompt}])
            response_text = response.content.strip()
            
            suggestions = []
            lines = response_text.split('\n')
            in_suggestions = False
            
            for line in lines:
                line = line.strip()
                if line == "SUGGESTIONS GLOBALES:":
                    in_suggestions = True
                elif line.startswith("-") and in_suggestions:
                    suggestion_text = line[1:].strip()
                    suggestions.append({
                        "titre": suggestion_text.split(":")[0] if ":" in suggestion_text else "Amélioration",
                        "description": suggestion_text,
                        "justification": "Basé sur l'analyse des articles scientifiques",
                        "articles_sources": [art['title'] for art in articles]
                    })
            
            return suggestions
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la génération des suggestions globales: {e}")
            return []
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extrait le titre d'un document markdown."""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## ') and 'synthèse' in line.lower():
                # Pour les articles qui commencent par une synthèse
                return line[3:].strip()
        return "Article scientifique"
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extrait des mots-clés pertinents du contenu."""
        # Version simple - peut être améliorée avec NLP
        keywords = []
        important_terms = [
            "prairie", "fertilisation", "sol", "agriculture biologique", 
            "rotation", "pâturage", "phosphore", "potassium", "azote",
            "fertilité", "amendement", "carbone"
        ]
        
        content_lower = content.lower()
        for term in important_terms:
            if term in content_lower:
                keywords.append(term)
        
        return keywords
    
    def _create_summary(self, content: str) -> str:
        """Crée un résumé du contenu."""
        lines = content.split('\n')
        # Prendre les premières phrases de chaque section importante
        summary_parts = []
        
        current_section = ""
        for line in lines:
            line = line.strip()
            if line.startswith('##') and len(line) > 3:
                current_section = line[2:].strip()
                summary_parts.append(current_section)
            elif len(summary_parts) < 5 and line and not line.startswith('#'):
                summary_parts.append(line[:100] + "..." if len(line) > 100 else line)
                break
        
        return " | ".join(summary_parts[:3])
    
    def export_enriched_markdown(self, enriched_scenario: Dict[str, Any], output_path: str) -> str:
        """
        Exporte le scénario enrichi en format markdown.
        
        Args:
            enriched_scenario: Scénario enrichi avec suggestions
            output_path: Chemin de sortie du fichier
            
        Returns:
            Chemin du fichier généré
        """
        output_file = Path(output_path)
        scenario_data = enriched_scenario["scenario_original"]
        enrichments = enriched_scenario["enrichments"]
        
        markdown_content = []
        
        # En-tête
        markdown_content.append(f"# {scenario_data.get('scenario_title', 'Scénario Pédagogique Enrichi')}")
        markdown_content.append("")
        markdown_content.append("*Scénario enrichi avec des suggestions basées sur des articles scientifiques récents*")
        markdown_content.append("")
        
        # Informations générales
        if scenario_data.get("target_audience"):
            markdown_content.append(f"**Public cible :** {scenario_data['target_audience']}")
        if scenario_data.get("global_objectives"):
            markdown_content.append("**Objectifs globaux :**")
            for obj in scenario_data["global_objectives"]:
                markdown_content.append(f"- {obj}")
        markdown_content.append("")
        
        # Suggestions globales
        if enrichments["global_suggestions"]:
            markdown_content.append("## 💡 Suggestions d'Amélioration Globales")
            markdown_content.append("")
            for i, suggestion in enumerate(enrichments["global_suggestions"], 1):
                markdown_content.append(f"### {i}. {suggestion['titre']}")
                markdown_content.append(f"{suggestion['description']}")
                markdown_content.append(f"*Justification :* {suggestion['justification']}")
                markdown_content.append("")
        
        # Détail par jour
        for day_data, day_enrichment in zip(scenario_data["days"], enrichments["days"]):
            markdown_content.append(f"## Jour {day_data['day_number']}: {day_data.get('day_title', '')}")
            markdown_content.append("")
            
            if day_data.get("daily_objectives"):
                markdown_content.append("**Objectifs de la journée :**")
                for obj in day_data["daily_objectives"]:
                    markdown_content.append(f"- {obj}")
                markdown_content.append("")
            
            # Tableau des séquences avec suggestions
            markdown_content.append("| Séq. | Horaire | Contenu | Méthodes | Évaluation | 💡 Suggestions et Nouveautés |")
            markdown_content.append("|------|---------|---------|----------|------------|------------------------------|")
            
            for seq_data, seq_enrichment in zip(day_data["sequences"], day_enrichment["sequences"]):
                seq_num = seq_data["sequence_number"]
                horaire = f"{seq_data['start_time']} - {seq_data['end_time']}"
                contenu = seq_data["content"][:80] + "..." if len(seq_data["content"]) > 80 else seq_data["content"]
                methodes = ", ".join(seq_data["pedagogical_methods"])
                evaluation = ", ".join(seq_data["evaluation_modalities"])
                
                # Formatage des suggestions - version courte pour le tableau
                suggestions_text = ""
                if seq_enrichment["suggestions"]:
                    count = len([nouveaute for suggestion_group in seq_enrichment["suggestions"] 
                               for nouveaute in suggestion_group["nouveautes"]])
                    suggestions_text = f"🆕 {count} nouveauté{'s' if count > 1 else ''} scientifique{'s' if count > 1 else ''}"
                else:
                    suggestions_text = "-"
                
                markdown_content.append(f"| {seq_num} | {horaire} | {contenu} | {methodes} | {evaluation} | {suggestions_text} |")
            
            markdown_content.append("")
            
            # Section détaillée des nouveautés pour ce jour
            nouveautes_jour = []
            for seq_enrichment in day_enrichment["sequences"]:
                if seq_enrichment["suggestions"]:
                    for suggestion_group in seq_enrichment["suggestions"]:
                        for nouveaute in suggestion_group["nouveautes"]:
                            nouveautes_jour.append((seq_enrichment["sequence_number"], nouveaute))
            
            if nouveautes_jour:
                markdown_content.append(f"### 🆕 Nouveautés Scientifiques - Jour {day_data['day_number']}")
                markdown_content.append("")
                for seq_num, nouveaute in nouveautes_jour:
                    markdown_content.append(f"**Séquence {seq_num}:** {nouveaute}")
                    markdown_content.append("")
        
        # Articles sources
        markdown_content.append("## 📚 Articles Scientifiques Consultés")
        markdown_content.append("")
        for article in enriched_scenario["articles_used"]:
            markdown_content.append(f"- **{article['title']}** _{article['source']}_")
        
        markdown_content.append("")
        markdown_content.append("---")
        markdown_content.append("*Document généré automatiquement par l'IA*")
        
        # Sauvegarde
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))
        
        print(f"📄 Scénario enrichi exporté vers: {output_file}")
        return str(output_file)


def create_scenario_enrichment(llm: Optional[ChatOpenAI] = None) -> ScenarioEnrichment:
    """Factory function pour créer un ScenarioEnrichment."""
    return ScenarioEnrichment(llm=llm)