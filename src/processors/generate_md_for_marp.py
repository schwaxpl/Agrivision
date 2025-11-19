import os
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from ..config import config

# Initialiser le modèle OpenAI avec la configuration centralisée
llm = ChatOpenAI(
    api_key=config.OPENAI_API_KEY,
    model=config.DEFAULT_MODEL,
    temperature=config.DEFAULT_TEMPERATURE,
    max_tokens=config.MAX_TOKENS
)

# Prompt pour générer des slides Marp
MARPPROMPT = """
Tu es un expert en rédaction de présentations scientifiques.
À partir du contenu Markdown ci-dessous, génère un résumé sous forme de slides au format Markdown compatible Marp.
Structure chaque slide avec '---' et commence par un titre.

Contenu Markdown :
{input_md}
"""

def generate_marp_slides_from_md(md_content: str) -> str:
    """
    Utilise OpenAI pour générer des slides Marp à partir d'un contenu Markdown.
    Utilise la configuration centralisée pour l'API et les paramètres du modèle.
    """
    prompt = PromptTemplate.from_template(MARPPROMPT)
    chain = prompt | llm
    marp_md = chain.invoke({"input_md": md_content})
    return marp_md

def process_examples_folder(examples_folder: str, output_folder: str):
    """
    Parcourt tous les fichiers .md du dossier examples, génère des slides Marp et les sauvegarde dans output_folder.
    """
    examples_path = Path(examples_folder)
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)

    for md_file in examples_path.glob("*.md"):
        with md_file.open("r", encoding="utf-8") as f:
            md_content = f.read()
            marp_md = generate_marp_slides_from_md(md_content)
            out_file = output_path / f"marp_{md_file.stem}.md"
            with out_file.open("w", encoding="utf-8") as f:
                markdown_content = marp_md.content if hasattr(marp_md, 'content') else str(marp_md)
                
                # Suppression des blocs de code markdown
                if "```markdown" in markdown_content:
                    markdown_content = markdown_content.split("```markdown", 1)[1]
                if "```" in markdown_content:
                    markdown_content = markdown_content.split("```", 1)[0]
                
                # Nettoyage du contenu
                markdown = markdown_content.strip()
                if markdown.startswith("---"):
                    markdown = markdown.split("---", 1)[1].lstrip()
                
                # Diviser en slides basé sur les séparateurs '---'
                slides = markdown.split("---")
                
                # Filtrer les slides vides (ne contenant que des espaces/lignes vides)
                non_empty_slides = [slide.strip() for slide in slides if slide.strip()]
                
                # Ajout du header Marp
                f.write("---\nmarp: true\n---\n\n")
                
                # Écrire les slides non vides avec séparateurs
                f.write("\n\n---\n\n".join(non_empty_slides))
                
        print(f"Slides Marp générées : {out_file}")

if __name__ == "__main__":
    # Utiliser les répertoires de configuration centralisée
    examples_folder = os.path.join(os.path.dirname(__file__), "../../examples")
    output_folder = config.OUTPUT_DIR
    process_examples_folder(examples_folder, output_folder)