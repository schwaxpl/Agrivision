"""
Modèle Pydantic pour représenter un article scientifique.
"""

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class ScientificArticle(BaseModel):
    """
    Modèle représentant un article scientifique structuré.
    
    Ce modèle servira de structure de base pour extraire et organiser
    les informations des résumés d'articles scientifiques en markdown.
    """
    
    title: str = Field(
        description="Titre de l'article scientifique"
    )
    
    authors: List[str] = Field(
        default_factory=list,
        description="Liste des auteurs de l'article"
    )
    
    abstract: str = Field(
        description="Résumé/abstract de l'article"
    )
    
    keywords: List[str] = Field(
        default_factory=list,
        description="Mots-clés associés à l'article"
    )
    
    publication_date: Optional[date] = Field(
        default=None,
        description="Date de publication de l'article"
    )
    
    journal: Optional[str] = Field(
        default=None,
        description="Nom du journal/revue de publication"
    )
    
    doi: Optional[str] = Field(
        default=None,
        description="Digital Object Identifier (DOI) de l'article"
    )
    
    research_field: Optional[str] = Field(
        default=None,
        description="Domaine de recherche principal"
    )
    
    methodology: Optional[str] = Field(
        default=None,
        description="Méthodologie utilisée dans l'étude"
    )
    
    main_findings: List[str] = Field(
        default_factory=list,
        description="Principales découvertes/résultats de l'étude"
    )
    
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Score de confiance de l'extraction (0.0 à 1.0)"
    )
    
    class Config:
        """Configuration du modèle Pydantic."""
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }
        
    def to_dict(self) -> dict:
        """Convertit le modèle en dictionnaire."""
        return self.model_dump()
    
    def __str__(self) -> str:
        """Représentation string de l'article."""
        return f"ScientificArticle(title='{self.title}', authors={len(self.authors)} auteurs)"