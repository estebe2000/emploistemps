"""
FastAPI Backend Server for IUT TC Timetable Management, Solver & AI Assistant.
Full REST API with OpenAPI documentation, CP-SAT solver triggering, and Albert AI Copilot.
"""

import os
import sys
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

# Local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from solver.timetable_cp_sat import TimetableSolver
from assistant.copilot import TimetableCopilot

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "data", "dataset_tc.json")
SCHEDULE_PATH = os.path.join(BASE_DIR, "data", "schedule_result.json")

app = FastAPI(
    title="API Gestion Emplois du Temps & Assistant IA (Département TC)",
    description="Microservice d'optimisation d'emplois du temps (Google OR-Tools CP-SAT) et Assistant IA Souverain (Albert API)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend / external services
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- REQUEST & RESPONSE SCHEMAS ---

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


# --- DATA UTILITIES ---

def get_dataset():
    if not os.path.exists(DATASET_PATH):
        raise HTTPException(status_code=404, detail="Dataset TC non trouvé. Exécutez extract_dataset.py.")
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_schedule():
    if not os.path.exists(SCHEDULE_PATH):
        # Auto-generate or return empty
        return {"semester": "S1", "week": 1, "status": "EMPTY", "total_events": 0, "events": []}
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# --- API ENDPOINTS ---

@app.get("/health", tags=["Système"])
def health_check():
    return {
        "status": "healthy",
        "service": "emploistemps-api",
        "solver": "ortools-cp-sat",
        "ai_engine": "albert-etalab"
    }


@app.get("/api/v1/dataset", tags=["Données"])
def read_full_dataset():
    """Renvoie l'ensemble du dataset départemental TC (enseignants, ressources, salles, cohortes)."""
    return get_dataset()


@app.get("/api/v1/teachers", tags=["Données"])
def list_teachers():
    """Liste tous les enseignants et intervenants avec leurs affectations."""
    return get_dataset().get("teachers", [])


@app.get("/api/v1/resources", tags=["Données"])
def list_resources(semester: Optional[str] = Query(None, description="Filtrer par semestre, ex: 'S1'")):
    """Liste les ressources pédagogiques du PN avec volumes CM/TD/TP."""
    res = get_dataset().get("resources", [])
    if semester:
        res = [r for r in res if r["semester"].upper() == semester.upper()]
    return res


@app.get("/api/v1/rooms", tags=["Données"])
def list_rooms():
    """Liste les salles, amphis et laboratoires avec capacités et équipements."""
    return get_dataset().get("rooms", [])


@app.get("/api/v1/cohorts", tags=["Données"])
def list_cohorts():
    """Liste les cohortes (Formation Initiale et Alternance) avec leurs groupes TD/TP."""
    return get_dataset().get("cohorts", [])


@app.post("/api/v1/solver/generate", tags=["Solveur CP-SAT"])
def generate_schedule(req: GenerateScheduleRequest):
    """
    Lance le solveur d'optimisation CP-SAT (Google OR-Tools) pour générer un emploi du temps à 0 conflit.
    """
    try:
        solver = TimetableSolver(DATASET_PATH)
        result = solver.solve_weekly_pattern(
            target_week=req.week,
            semester=req.semester,
            time_limit_seconds=req.time_limit_seconds
        )
        if not result:
            raise HTTPException(status_code=422, detail="Aucun emploi du temps valide trouvé sous les contraintes données.")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/schedule", tags=["Planning"])
def get_current_schedule(
    group_id: Optional[str] = Query(None, description="Filtrer par groupe (ex: 'BUT1_PROMO', 'BUT1_TD1')"),
    teacher: Optional[str] = Query(None, description="Filtrer par enseignant"),
    room: Optional[str] = Query(None, description="Filtrer par salle")
):
    """Récupère l'emploi du temps actuel avec filtres dynamiques."""
    sched = get_schedule()
    events = sched.get("events", [])

    if group_id:
        events = [e for e in events if e["group_id"] == group_id or "PROMO" in e["group_id"]]
    if teacher:
        events = [e for e in events if teacher.lower() in e["teacher_name"].lower()]
    if room:
        events = [e for e in events if room.lower() in e["room_name"].lower() or room.lower() in e["room_id"].lower()]

    return {
        "semester": sched.get("semester", "S1"),
        "week": sched.get("week", 1),
        "status": sched.get("status", "OK"),
        "total_events": len(events),
        "events": events
    }


@app.post("/api/v1/schedule/verify-conflict", tags=["Planning"])
def verify_conflict(req: MoveLessonRequest):
    """Vérifie si le déplacement d'un cours causerait un conflit sans modifier le planning."""
    copilot = TimetableCopilot()
    return copilot.verifier_conflit_deplacement(
        lesson_id=req.lesson_id,
        cible_jour=req.target_day,
        cible_creneau_idx=req.target_slot_idx,
        cible_salle=req.target_room_id
    )


@app.post("/api/v1/schedule/move", tags=["Planning"])
def move_lesson(req: MoveLessonRequest):
    """Déplace un cours vers un nouveau créneau et/ou salle après vérification des conflits."""
    copilot = TimetableCopilot()
    res = copilot.deplacer_cours(
        lesson_id=req.lesson_id,
        cible_jour=req.target_day,
        cible_creneau_idx=req.target_slot_idx,
        cible_salle=req.target_room_id
    )
    if res.get("conflit"):
        raise HTTPException(status_code=400, detail=res)
    return res


@app.get("/api/v1/schedule/free-slots", tags=["Planning"])
def find_free_slots(
    teacher: str = Query(..., description="Nom de l'enseignant"),
    group_id: str = Query(..., description="ID du groupe d'étudiants (ex: 'BUT1_TD1')")
):
    """Recherche tous les créneaux communs libres pour un enseignant et un groupe d'étudiants."""
    copilot = TimetableCopilot()
    return copilot.trouver_creneaux_libres(teacher, group_id)


@app.post("/api/v1/ai/chat", tags=["Assistant IA"])
def ai_chat(req: AIChatRequest):
    """
    Envoie une requête en langage naturel à l'Assistant IA (Albert API) avec exécution automatique d'outils.
    """
    copilot = TimetableCopilot()
    response_text = copilot.chat(req.prompt)
    return {"response": response_text}


@app.get("/api/v1/export/ical", tags=["Exports"])
def export_ical():
    """Exporte l'emploi du temps au format standard iCalendar (.ics) pour Google Agenda / Outlook."""
    sched = get_schedule()
    events = sched.get("events", [])
    
    # Simple iCal generator
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//IUT TC//EmploisDuTemps v1.0//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    # Mapping day names to offset in dummy week
    day_offsets = {"Lundi": 1, "Mardi": 2, "Mercredi": 3, "Jeudi": 4, "Vendredi": 5}
    slot_hours = {
        0: ("080000", "100000"),
        1: ("101500", "121500"),
        2: ("133000", "153000"),
        3: ("154500", "174500")
    }

    for ev in events:
        d_offset = day_offsets.get(ev.get("day", "Lundi"), 1)
        sh, eh = slot_hours.get(ev.get("slot_idx", 0), ("080000", "100000"))
        # Example date for S1 week 1: 20260907 (Monday)
        date_str = f"2026090{6 + d_offset}"
        
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{ev['lesson_id']}@iut-tc.univ.fr",
            f"DTSTAMP:20260901T000000Z",
            f"DTSTART:{date_str}T{sh}",
            f"DTEND:{date_str}T{eh}",
            f"SUMMARY:{ev['event_type']} {ev['resource_code']} - {ev['teacher_name']}",
            f"DESCRIPTION:Ressource: {ev['resource_name']} ({ev['group_id']})",
            f"LOCATION:{ev['room_name']}",
            "STATUS:CONFIRMED",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    ical_content = "\r\n".join(lines)
    
    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=planning_tc.ics"}
    )


# --- SERVE WEB INTERFACE ---

@app.get("/", response_class=HTMLResponse, tags=["Interface Web"])
def serve_dashboard():
    index_file = os.path.join(BASE_DIR, "web", "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Application Emplois du Temps TC</h1><p>Visitez <a href='/docs'>/docs</a> pour l'API OpenAPI.</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
