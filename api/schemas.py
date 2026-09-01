"""
Schémas Pydantic (modèles de requête) pour l'API Emplois du Temps TC.
"""
from typing import Optional

from pydantic import BaseModel, Field


class GenerateScheduleRequest(BaseModel):
    semester: str = Field(default="S1", description="Semestre visé (S1..S6)")
    week: int = Field(default=1, description="Numéro de la semaine à planifier (1 à 15)")
    time_limit_seconds: int = Field(default=15, description="Temps max alloué au solveur CP-SAT en secondes")


class MoveLessonRequest(BaseModel):
    lesson_id: str = Field(..., description="ID unique de la séance")
    target_day: str = Field(..., description="Jour cible ('Lundi'..'Vendredi')")
    target_slot_idx: int = Field(..., ge=0, le=3, description="Indice du créneau (0: 8h-10h, 1: 10h15-12h15, 2: 13h30-15h30, 3: 15h45-17h45)")
    target_room_id: Optional[str] = Field(None, description="Optionnel: ID de la nouvelle salle")


class AIChatRequest(BaseModel):
    prompt: str = Field(..., description="Instruction ou question en langage naturel pour l'Assistant IA")