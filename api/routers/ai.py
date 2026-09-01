"""
Routes de l'Assistant IA (copilote Albert / Ollama).
"""
from fastapi import APIRouter

from ..schemas import AIChatRequest

router = APIRouter(prefix="/api/v1", tags=["Assistant IA"])


@router.post("/ai/chat")
def ai_chat(req: AIChatRequest):
    """
    Envoie une requête en langage naturel à l'Assistant IA (Albert API) avec exécution automatique d'outils.
    """
    from assistant.copilot import TimetableCopilot
    copilot = TimetableCopilot()
    response_text = copilot.chat(req.prompt)
    return {"response": response_text}