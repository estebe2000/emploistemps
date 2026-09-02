"""
Routes de génération de textes (demandes par mail pour le responsable EDT).
Permet de produire les messages sans passer par l'interface web.
"""
from typing import Optional, List

from fastapi import APIRouter, HTTPException

from ..services.texts import generate_text, _week_label

router = APIRouter(prefix="/api/v1/admin", tags=["Textes EDT"])


@router.post("/generate-text")
def api_generate_text(payload: dict):
    """
    Génère un texte type mail pour une demande EDT.

    Corps : { "lesson_id": "...", "kind": "move|room|teacher|defer", "options": {...} }
    - move: options = { target_day, target_slot_idx, target_room_id, target_room_name }
    - room: options = { new_room_id, new_room_name }
    - teacher: options = { new_teacher }
    - defer: options = { note }
    """
    lesson_id = payload.get("lesson_id")
    kind = payload.get("kind")
    options = payload.get("options") or {}
    if not lesson_id or not kind:
        raise HTTPException(status_code=400, detail="lesson_id et kind sont requis.")
    try:
        text = generate_text(lesson_id, kind, options)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"lesson_id": lesson_id, "kind": kind, "text": text}