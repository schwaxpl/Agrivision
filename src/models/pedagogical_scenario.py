"""
Modèles Pydantic pour représenter un scénario pédagogique multi-jours.
"""

from datetime import time, date
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class PedagogicalSequence(BaseModel):
    """
    Modèle représentant une séquence pédagogique individuelle.
    """
    
    sequence_number: int = Field(
        description="Numéro de séquence pédagogique",
        ge=1
    )
    
    start_time: str = Field(
        description="Heure de début de la séquence (format HH:MM)"
    )
    
    end_time: str = Field(
        description="Heure de fin de la séquence (format HH:MM)"
    )
    
    content: str = Field(
        description="Contenu détaillé de la séquence pédagogique"
    )
    
    pedagogical_methods: List[str] = Field(
        default_factory=list,
        description="Liste des méthodes pédagogiques utilisées"
    )
    
    evaluation_modalities: List[str] = Field(
        default_factory=list,
        description="Modalités d'évaluation prévues pour cette séquence"
    )
    
    # Champs optionnels pour enrichir la séquence
    title: Optional[str] = Field(
        default=None,
        description="Titre de la séquence"
    )
    
    objectives: List[str] = Field(
        default_factory=list,
        description="Objectifs pédagogiques spécifiques de la séquence"
    )
    
    resources_needed: List[str] = Field(
        default_factory=list,
        description="Ressources matérielles ou numériques nécessaires"
    )
    
    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, v):
        """Valide le format des heures."""
        if not v:
            return v
        
        # Vérifie le format HH:MM
        try:
            time_parts = v.split(':')
            if len(time_parts) == 2:
                hours = int(time_parts[0])
                minutes = int(time_parts[1])
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    return f"{hours:02d}:{minutes:02d}"
        except (ValueError, IndexError):
            pass
        
        # Si le format n'est pas valide, on garde la valeur originale
        return v
    
    def calculate_duration(self) -> Optional[int]:
        """Calcule la durée en minutes entre start_time et end_time."""
        try:
            start_parts = self.start_time.split(':')
            end_parts = self.end_time.split(':')
            
            start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
            end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
            
            duration = end_minutes - start_minutes
            if duration < 0:  # Si on passe minuit
                duration += 24 * 60
                
            return duration
        except (ValueError, IndexError, AttributeError):
            return None
    
    def __str__(self) -> str:
        return f"Séquence {self.sequence_number}: {self.start_time}-{self.end_time}"


class PedagogicalDay(BaseModel):
    """
    Modèle représentant une journée de formation avec ses séquences.
    """
    
    day_number: int = Field(
        description="Numéro du jour de formation",
        ge=1
    )
    
    day_date: Optional[str] = Field(
        default=None,
        description="Date du jour (format YYYY-MM-DD ou texte libre)"
    )
    
    day_title: Optional[str] = Field(
        default=None,
        description="Titre ou thème du jour"
    )
    
    sequences: List[PedagogicalSequence] = Field(
        default_factory=list,
        description="Liste des séquences pédagogiques de la journée"
    )
    
    daily_objectives: List[str] = Field(
        default_factory=list,
        description="Objectifs pédagogiques globaux de la journée"
    )
    
    def get_total_duration(self) -> int:
        """Calcule la durée totale de la journée en minutes."""
        total = 0
        for sequence in self.sequences:
            duration = sequence.calculate_duration()
            if duration:
                total += duration
        return total
    
    def get_sequences_count(self) -> int:
        """Retourne le nombre de séquences de la journée."""
        return len(self.sequences)
    
    def __str__(self) -> str:
        duration = self.get_total_duration()
        return f"Jour {self.day_number}: {len(self.sequences)} séquences ({duration}min)"


class PedagogicalScenario(BaseModel):
    """
    Modèle représentant un scénario pédagogique complet multi-jours.
    
    Ce modèle structure une formation complète organisée par jours,
    chaque jour contenant plusieurs séquences pédagogiques.
    """
    
    scenario_title: Optional[str] = Field(
        default=None,
        description="Titre du scénario pédagogique complet"
    )
    
    days: List[PedagogicalDay] = Field(
        default_factory=list,
        description="Liste des jours de formation"
    )
    
    target_audience: Optional[str] = Field(
        default=None,
        description="Public cible (niveau, profil des apprenants)"
    )
    
    global_objectives: List[str] = Field(
        default_factory=list,
        description="Objectifs pédagogiques globaux du scénario"
    )
    
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Prérequis nécessaires pour le scénario complet"
    )
    
    global_resources: List[str] = Field(
        default_factory=list,
        description="Ressources générales nécessaires pour tout le scénario"
    )
    
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Score de confiance de l'extraction (0.0 à 1.0)"
    )
    
    def get_total_days(self) -> int:
        """Retourne le nombre total de jours."""
        return len(self.days)
    
    def get_total_sequences(self) -> int:
        """Retourne le nombre total de séquences sur tous les jours."""
        return sum(day.get_sequences_count() for day in self.days)
    
    def get_total_duration(self) -> int:
        """Calcule la durée totale du scénario en minutes."""
        return sum(day.get_total_duration() for day in self.days)
    
    def get_day_by_number(self, day_number: int) -> Optional[PedagogicalDay]:
        """Retourne un jour spécifique par son numéro."""
        for day in self.days:
            if day.day_number == day_number:
                return day
        return None
    
    class Config:
        """Configuration du modèle Pydantic."""
        json_encoders = {
            # Pas d'encodage spécial nécessaire pour les strings
        }
        
    def to_dict(self) -> dict:
        """Convertit le modèle en dictionnaire."""
        data = self.model_dump()
        # Ajoute des statistiques calculées
        data['statistics'] = {
            'total_days': self.get_total_days(),
            'total_sequences': self.get_total_sequences(),
            'total_duration_minutes': self.get_total_duration(),
            'total_duration_hours': round(self.get_total_duration() / 60, 2)
        }
        return data
    
    def __str__(self) -> str:
        """Représentation string du scénario."""
        return f"ScénarioPédagogique: {self.get_total_days()} jours, {self.get_total_sequences()} séquences"
    
    def get_summary(self) -> str:
        """Retourne un résumé détaillé du scénario."""
        total_hours = round(self.get_total_duration() / 60, 1)
        
        summary = []
        if self.scenario_title:
            summary.append(f"Titre: {self.scenario_title}")
        
        summary.append(f"Durée totale: {self.get_total_days()} jour(s) - {total_hours}h")
        summary.append(f"Nombre de séquences: {self.get_total_sequences()}")
        
        if self.target_audience:
            summary.append(f"Public: {self.target_audience}")
        
        # Résumé par jour
        for day in self.days:
            day_duration = round(day.get_total_duration() / 60, 1)
            summary.append(f"  Jour {day.day_number}: {day.get_sequences_count()} séquences ({day_duration}h)")
        
        return "\n".join(summary)