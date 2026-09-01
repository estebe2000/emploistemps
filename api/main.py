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


# --- ADMIN & CONSTRAINTS ENDPOINTS ---

CONSTRAINTS_PATH = os.path.join(BASE_DIR, "data", "constraints.json")

def get_constraints_data():
    if not os.path.exists(CONSTRAINTS_PATH):
        return {
            "department": "TC",
            "max_hours_per_day_teacher": 6,
            "max_hours_per_day_student": 8,
            "catchup_weeks": [8, 15],
            "teacher_unavailabilities": [],
            "room_closures_or_reservations": [],
            "cohort_alternance_calendar": {}
        }
    with open(CONSTRAINTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_constraints_data(data: dict):
    with open(CONSTRAINTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_dataset_data(data: dict):
    with open(DATASET_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.get("/api/v1/admin/constraints", tags=["Administration"])
def get_admin_constraints():
    """Récupère l'ensemble des contraintes configurées."""
    return get_constraints_data()


@app.post("/api/v1/admin/constraints", tags=["Administration"])
def save_admin_constraints(constraints: dict):
    """Enregistre l'ensemble des contraintes départementales."""
    save_constraints_data(constraints)
    return {"status": "success", "message": "Contraintes enregistrées avec succès."}


@app.post("/api/v1/admin/teacher/unavailability", tags=["Administration"])
def update_teacher_unavailability(payload: dict):
    """Ajoute ou met à jour l'indisponibilité d'un enseignant."""
    c = get_constraints_data()
    t_name = payload.get("teacher_name")
    unavails = c.get("teacher_unavailabilities", [])
    # Filter out existing unavailabilities for this teacher if full replacement is passed
    if payload.get("replace"):
        unavails = [u for u in unavails if u.get("teacher_name", "").lower() != t_name.lower()]
    
    new_unavail = {
        "teacher_name": t_name,
        "day": payload.get("day"),
        "slots": payload.get("slots", []),
        "reason": payload.get("reason", "Indisponibilité")
    }
    unavails.append(new_unavail)
    c["teacher_unavailabilities"] = unavails
    save_constraints_data(c)
    return {"status": "success", "message": f"Indisponibilité enregistrée pour {t_name}."}


@app.post("/api/v1/admin/room/closure", tags=["Administration"])
def update_room_closure(payload: dict):
    """Ajoute une fermeture ou réservation de salle."""
    c = get_constraints_data()
    closures = c.get("room_closures_or_reservations", [])
    closures.append({
        "room_id": payload.get("room_id"),
        "week": payload.get("week"),
        "day": payload.get("day"),
        "slots": payload.get("slots", []),
        "reason": payload.get("reason", "Réservation")
    })
    c["room_closures_or_reservations"] = closures
    save_constraints_data(c)
    return {"status": "success", "message": "Fermeture/Réservation de salle enregistrée."}


@app.post("/api/v1/admin/cohort/alternance", tags=["Administration"])
def update_cohort_alternance(payload: dict):
    """Met à jour le calendrier d'alternance pour une cohorte (semaines entreprise)."""
    c = get_constraints_data()
    cohort_id = payload.get("cohort_id")
    weeks = payload.get("company_weeks", [])
    if "cohort_alternance_calendar" not in c:
        c["cohort_alternance_calendar"] = {}
    c["cohort_alternance_calendar"][cohort_id] = {
        "company_weeks": weeks,
        "comment": payload.get("comment", "Semaines en entreprise")
    }
    save_constraints_data(c)
    return {"status": "success", "message": f"Calendrier d'alternance mis à jour pour {cohort_id}."}


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


# --- WORKLOAD & SERVICES HETD ENDPOINT ---

@app.get("/api/v1/teachers/workload", tags=["Gestion des Services"])
def get_teachers_workload():
    """
    Calcule le bilan des services d'enseignement en Heures Équivalent TD (HETD)
    selon la réglementation officielle (1h CM = 1.5h TD, 1h TD = 1.0h TD, 4h TP = 3.0h TD / ratio 0.75).
    """
    dataset = get_dataset()
    sched = get_schedule()
    events = sched.get("events", [])
    
    workload_summary = []
    
    for t in dataset.get("teachers", []):
        t_name = t["name"]
        t_events = [e for e in events if e.get("teacher_name", "").lower() == t_name.lower()]
        
        cm_hours = sum(e.get("duration_hours", 1.5) for e in t_events if e.get("event_type") == "CM")
        td_hours = sum(e.get("duration_hours", 1.5) for e in t_events if e.get("event_type") == "TD")
        tp_hours = sum(e.get("duration_hours", 1.5) for e in t_events if e.get("event_type") == "TP")
        eval_hours = sum(e.get("duration_hours", 1.5) for e in t_events if e.get("event_type") == "EVAL" or e.get("is_evaluation"))
        
        # Total HETD on planned week * 15 weeks semester estimate
        week_hetd = (cm_hours * 1.5) + (td_hours * 1.0) + (tp_hours * 0.75) + (eval_hours * 1.0)
        est_semester_hetd = round(week_hetd * 15, 1)
        statutaire = t.get("service_statutaire_hetd", 192)
        
        delta = round(est_semester_hetd - statutaire, 1)
        status = "ÉQUILIBRÉ"
        if delta > 10:
            status = "HEURES_SUP"
        elif delta < -10:
            status = "SOUS_SERVICE"
            
        workload_summary.append({
            "teacher_id": t["id"],
            "teacher_name": t_name,
            "statut": t.get("statut", "MCF"),
            "service_statutaire_hetd": statutaire,
            "semaine_heures_cm": cm_hours,
            "semaine_heures_td": td_hours,
            "semaine_heures_tp": tp_hours,
            "semaine_total_hetd": round(week_hetd, 2),
            "semestre_estime_hetd": est_semester_hetd,
            "delta_hetd": delta,
            "status": status,
            "nb_cours_planifies": len(t_events)
        })
        
    # Sort by name
    workload_summary.sort(key=lambda x: x["teacher_name"])
    return {
        "hetd_rule": "1h CM = 1.5h TD | 1h TD = 1.0h TD | 4h TP = 3h TD (ratio 0.75)",
        "teachers": workload_summary
    }


# --- EVALUATIONS & ABSENCES MANAGEMENT ---

@app.post("/api/v1/evaluations", tags=["Administration"])
def create_evaluation(payload: dict):
    """Planifie une évaluation / partiel / DS."""
    c = get_constraints_data()
    evals = c.get("evaluations", [])
    new_eval = {
        "id": f"EVAL_{len(evals)+1:02d}",
        "title": payload.get("title", "Évaluation"),
        "resource_code": payload.get("resource_code", "R1.01"),
        "target_group": payload.get("target_group", "BUT1_PROMO"),
        "week": payload.get("week", 1),
        "day": payload.get("day", "Lundi"),
        "slot_idx": payload.get("slot_idx", 0),
        "room_id": payload.get("room_id", "IUTC-amphi 3"),
        "duration_hours": payload.get("duration_hours", 1.5),
        "invigilators": payload.get("invigilators", [])
    }
    evals.append(new_eval)
    c["evaluations"] = evals
    save_constraints_data(c)
    return {"status": "success", "message": f"Évaluation '{new_eval['title']}' planifiée.", "eval": new_eval}


@app.post("/api/v1/teachers/absence", tags=["Administration"])
def record_teacher_absence(payload: dict):
    """Enregistre une absence d'enseignant."""
    c = get_constraints_data()
    absences = c.get("teacher_absences", [])
    new_abs = {
        "id": f"ABS_{len(absences)+1:02d}",
        "teacher_name": payload.get("teacher_name"),
        "week": payload.get("week"),
        "day": payload.get("day"),
        "slots": payload.get("slots", [0, 1, 2, 3]),
        "reason": payload.get("reason", "Absence"),
        "needs_replacement": payload.get("needs_replacement", True)
    }
    absences.append(new_abs)
    c["teacher_absences"] = absences
    save_constraints_data(c)
    return {"status": "success", "message": f"Absence enregistrée pour {new_abs['teacher_name']}."}


@app.post("/api/v1/schedule/quick-action", tags=["Planning"])
def execute_quick_action(payload: dict):
    """
    Exécute une action contextuelle (menu clic droit sur un cours) :
    - 'MOVE' : Déplacer vers créneau cible
    - 'CHANGE_ROOM' : Changer de salle
    - 'CHANGE_TEACHER' : Changer d'enseignant
    - 'CANCEL' : Annuler la séance
    - 'CONVERT_EVAL' : Transformer en DS/Évaluation
    """
    action = payload.get("action")
    lesson_id = payload.get("lesson_id")
    sched = get_schedule()
    events = sched.get("events", [])
    
    target_event = next((e for e in events if e["lesson_id"] == lesson_id), None)
    if not target_event and action != "CREATE":
        raise HTTPException(status_code=404, detail="Cours introuvable.")
        
    if action == "CANCEL":
        sched["events"] = [e for e in events if e["lesson_id"] != lesson_id]
        sched["total_events"] = len(sched["events"])
        with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
            json.dump(sched, f, indent=2, ensure_ascii=False)
        return {"status": "success", "message": f"Séance {lesson_id} annulée."}
        
    elif action == "CHANGE_ROOM":
        new_room_id = payload.get("new_room_id")
        dataset = get_dataset()
        room_obj = next((r for r in dataset["rooms"] if r["id"] == new_room_id), None)
        if room_obj:
            target_event["room_id"] = room_obj["id"]
            target_event["room_name"] = room_obj["name"]
            with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
                json.dump(sched, f, indent=2, ensure_ascii=False)
            return {"status": "success", "message": f"Salle modifiée vers {room_obj['name']}."}
            
    elif action == "CHANGE_TEACHER":
        new_teacher = payload.get("new_teacher")
        target_event["teacher_name"] = new_teacher
        with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
            json.dump(sched, f, indent=2, ensure_ascii=False)
        return {"status": "success", "message": f"Enseignant modifié vers {new_teacher}."}

    elif action == "CONVERT_EVAL":
        target_event["is_evaluation"] = True
        target_event["event_type"] = "EVAL"
        with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
            json.dump(sched, f, indent=2, ensure_ascii=False)
        return {"status": "success", "message": "Séance convertie en Évaluation."}
        
    raise HTTPException(status_code=400, detail=f"Action inconnue : {action}")



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
