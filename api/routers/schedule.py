"""
Routes de gestion du planning : consultation, vérification/déplacement, créneaux libres,
file de reprogrammation, actions rapides et export iCal.
"""
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, Response

from ..storage import get_schedule, save_schedule, get_dataset

router = APIRouter(prefix="/api/v1", tags=["Planning"])


@router.get("/schedule")
def get_current_schedule(
    group_id: Optional[str] = Query(None, description="Filtrer par groupe (ex: 'BUT1_PROMO', 'BUT1_TD1')"),
    teacher: Optional[str] = Query(None, description="Filtrer par enseignant"),
    room: Optional[str] = Query(None, description="Filtrer par salle")
):
    """Récupère l'EDT filtré par groupe, enseignant ou salle."""
    sched = get_schedule()
    events = sched.get("events", [])

    if group_id:
        events = [e for e in events if e["group_id"] == group_id or "PROMO" in e["group_id"]]
    if teacher:
        t = teacher.lower()
        events = [e for e in events if t in e.get("teacher_name", "").lower()]
    if room:
        r = room.lower()
        events = [e for e in events if r in e.get("room_name", "").lower() or r in e.get("room_id", "").lower()]

    return {
        "semester": sched.get("semester", "S1"),
        "week": sched.get("week", 1),
        "semester_start": sched.get("semester_start"),
        "status": sched.get("status", "OK"),
        "total_events": len(events),
        "events": events
    }


def _get_copilot():
    from assistant.copilot import TimetableCopilot
    return TimetableCopilot()


@router.post("/schedule/verify-conflict")
def verify_schedule_conflict(payload: dict):
    """Vérifie si déplacer une séance provoque un conflit (salle / enseignant / groupe)."""
    copilot = _get_copilot()
    check = copilot.verifier_conflit_deplacement(
        lesson_id=payload.get("lesson_id"),
        cible_jour=payload.get("target_day", payload.get("cible_jour")),
        cible_creneau_idx=int(payload.get("target_slot_idx", payload.get("cible_creneau_idx", 0))),
        cible_salle=payload.get("target_room_id", payload.get("cible_salle"))
    )
    return {
        "conflit": check.get("conflit", True),
        "raisons": check.get("raisons", []),
        "autorise": check.get("autorise", not check.get("conflit", True)),
        "message": check.get("message", "Vérification effectuée.")
    }


@router.post("/schedule/move")
def move_schedule_lesson(payload: dict):
    """Déplace une séance vers un jour/créneau cible (et éventuellement une autre salle)."""
    lesson_id = payload.get("lesson_id")
    target_day = payload.get("target_day", payload.get("cible_jour"))
    target_slot_idx = int(payload.get("target_slot_idx", payload.get("cible_creneau_idx", 0)))
    target_room_id = payload.get("target_room_id", payload.get("cible_salle"))

    if not lesson_id or not target_day:
        raise HTTPException(status_code=400, detail="lesson_id et target_day sont requis.")

    copilot = _get_copilot()
    check = copilot.verifier_conflit_deplacement(
        lesson_id=lesson_id, cible_jour=target_day, cible_creneau_idx=target_slot_idx, cible_salle=target_room_id
    )
    if check.get("conflit"):
        raise HTTPException(status_code=400, detail=check)

    result = copilot.deplacer_cours(
        lesson_id=lesson_id, cible_jour=target_day, cible_creneau_idx=target_slot_idx, cible_salle=target_room_id
    )
    return {
        "conflit": False,
        "raisons": [],
        "message": result.get("message", f"Cours {lesson_id} déplacé avec succès.")
    }


@router.get("/schedule/free-slots")
def get_free_slots(
    teacher: str = Query(..., description="Enseignant pour lequel chercher des créneaux libres"),
    group_id: str = Query(..., description="Groupe d'étudiants visé (ex: 'BUT1_TD1')")
):
    """Retourne les créneaux où un enseignant ET un groupe sont simultanément libres."""
    copilot = _get_copilot()
    return copilot.trouver_creneaux_libres(enseignant=teacher, groupe_id=group_id)


@router.get("/schedule/suggest-move")
def suggest_move(
    lesson_id: str = Query(..., description="ID de la séance à déplacer"),
    target_week: Optional[int] = Query(None, description="Semaine cible (défaut: semaine du cours)")
):
    """Propose des créneaux compatibles pour déplacer un cours (contraintes + EDT groupe + salle)."""
    from ..services.suggest import suggest_move as _sm
    return _sm(lesson_id, target_week)


@router.get("/schedule/suggest-room")
def suggest_room(
    lesson_id: str = Query(..., description="ID de la séance")
):
    """Propose les salles libres/recommandées pour le créneau courant d'une séance."""
    from ..services.suggest import suggest_room as _sr
    return _sr(lesson_id)


@router.get("/schedule/deferred")
def get_deferred_lessons():
    """Récupère la liste des cours mis en attente à reprogrammer ultérieurement."""
    sched = get_schedule()
    return {"deferred_events": sched.get("deferred_events", [])}


@router.post("/schedule/reprogram")
def reprogram_lesson(payload: dict):
    """Reprogramme un cours depuis la file d'attente vers un créneau et une salle cibles."""
    lesson_id = payload.get("lesson_id")
    target_day = payload.get("target_day")
    target_slot_idx = int(payload.get("target_slot_idx", 0))
    target_room_id = payload.get("target_room_id")

    sched = get_schedule()
    deferred = sched.get("deferred_events", [])
    target_evt = next((e for e in deferred if e["lesson_id"] == lesson_id), None)
    if not target_evt:
        raise HTTPException(status_code=404, detail="Cours introuvable dans la file de reprogrammation.")

    copilot = _get_copilot()
    check = copilot.verifier_conflit_deplacement(
        lesson_id=lesson_id, cible_jour=target_day, cible_creneau_idx=target_slot_idx, cible_salle=target_room_id
    )
    if check.get("conflit"):
        raise HTTPException(status_code=400, detail=check)

    dataset = get_dataset()
    days = dataset["calendar_config"]["days"]
    daily_slots = dataset["calendar_config"]["daily_slots"]
    room_obj = next((r for r in dataset["rooms"] if r["id"] == target_room_id), None)

    day_idx = days.index(target_day) if target_day in days else 0
    target_evt["day"] = target_day
    target_evt["day_idx"] = day_idx
    target_evt["slot_idx"] = target_slot_idx
    target_evt["slot_time"] = daily_slots[target_slot_idx]["time"]
    target_evt["global_slot"] = day_idx * len(daily_slots) + target_slot_idx
    if room_obj:
        target_evt["room_id"] = room_obj["id"]
        target_evt["room_name"] = room_obj["name"]

    sched["deferred_events"] = [e for e in deferred if e["lesson_id"] != lesson_id]
    sched["events"].append(target_evt)
    sched["total_events"] = len(sched["events"])
    save_schedule(sched)

    return {"status": "success", "message": f"Cours {target_evt['resource_name']} reprogrammé le {target_day} à {target_evt['slot_time']}."}


@router.post("/schedule/quick-action")
def execute_quick_action(payload: dict):
    """
    Exécute une action contextuelle (menu clic droit sur un cours) :
    MOVE | CHANGE_ROOM | CHANGE_TEACHER | DEFER | CANCEL | CONVERT_EVAL.
    """
    action = payload.get("action")
    lesson_id = payload.get("lesson_id")
    sched = get_schedule()
    events = sched.get("events", [])
    target_event = next((e for e in events if e["lesson_id"] == lesson_id), None)
    if not target_event:
        raise HTTPException(status_code=404, detail=f"Cours {lesson_id} introuvable.")

    if action == "CANCEL":
        sched["events"] = [e for e in events if e["lesson_id"] != lesson_id]
        sched["total_events"] = len(sched["events"])
        save_schedule(sched)
        return {"status": "success", "message": f"Cours '{target_event['resource_name']}' annulé."}

    elif action == "DEFER":
        if "deferred_events" not in sched:
            sched["deferred_events"] = []
        sched["events"] = [e for e in events if e["lesson_id"] != lesson_id]
        sched["deferred_events"].append(target_event)
        sched["total_events"] = len(sched["events"])
        save_schedule(sched)
        return {"status": "success", "message": f"Cours '{target_event['resource_name']}' déplacé vers la liste des cours à reprogrammer."}

    elif action == "MOVE":
        target_day = payload.get("target_day")
        target_slot_idx = int(payload.get("target_slot_idx", 0))
        target_room_id = payload.get("target_room_id")

        copilot = _get_copilot()
        check = copilot.verifier_conflit_deplacement(
            lesson_id=lesson_id, cible_jour=target_day, cible_creneau_idx=target_slot_idx, cible_salle=target_room_id
        )
        if check.get("conflit"):
            raise HTTPException(status_code=400, detail=check)

        dataset = get_dataset()
        days = dataset["calendar_config"]["days"]
        daily_slots = dataset["calendar_config"]["daily_slots"]
        room_obj = next((r for r in dataset["rooms"] if r["id"] == target_room_id), None)

        day_idx = days.index(target_day) if target_day in days else 0
        target_event["day"] = target_day
        target_event["day_idx"] = day_idx
        target_event["slot_idx"] = target_slot_idx
        target_event["slot_time"] = daily_slots[target_slot_idx]["time"]
        target_event["global_slot"] = day_idx * len(daily_slots) + target_slot_idx
        if room_obj:
            target_event["room_id"] = room_obj["id"]
            target_event["room_name"] = room_obj["name"]

        save_schedule(sched)
        return {"status": "success", "message": f"Cours déplacé au {target_day} à {target_event['slot_time']}."}

    elif action == "CHANGE_ROOM":
        new_room_id = payload.get("new_room_id")
        dataset = get_dataset()
        room_obj = next((r for r in dataset["rooms"] if r["id"] == new_room_id), None)
        if room_obj:
            target_event["room_id"] = room_obj["id"]
            target_event["room_name"] = room_obj["name"]
            save_schedule(sched)
            return {"status": "success", "message": f"Salle modifiée vers {room_obj['name']}."}

    elif action == "CHANGE_TEACHER":
        new_teacher = payload.get("new_teacher")
        target_event["teacher_name"] = new_teacher
        save_schedule(sched)
        return {"status": "success", "message": f"Enseignant modifié vers {new_teacher}."}

    elif action == "CONVERT_EVAL":
        target_event["is_evaluation"] = True
        target_event["event_type"] = "EVAL"
        save_schedule(sched)
        return {"status": "success", "message": "Séance convertie en Évaluation."}

    raise HTTPException(status_code=400, detail=f"Action inconnue : {action}")


@router.get("/export/ical", tags=["Exports"])
def export_ical():
    """Exporte l'emploi du temps au format standard iCalendar (.ics)."""
    sched = get_schedule()
    events = sched.get("events", [])
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//IUT TC//EmploisDuTemps v1.0//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
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
        date_str = f"2026090{6 + d_offset}"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{ev['lesson_id']}@iut-tc.univ.fr",
            "DTSTAMP:20260901T000000Z",
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