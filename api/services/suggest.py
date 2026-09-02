"""
Suggestions de déplacement / de salle, calculées côté serveur (miroir de la logique
frontend afin que des clients comme sibutv3 puissent faire les mêmes propositions).
"""
import json
import os
from datetime import date, datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEDULE_PATH = os.path.join(BASE_DIR, "data", "schedule_result.json")
DATASET_PATH = os.path.join(BASE_DIR, "data", "dataset_tc.json")

SLOT_TIMES = {
    0: "08:00 - 09:30", 1: "09:30 - 11:00", 2: "11:00 - 12:30",
    3: "13:30 - 15:00", 4: "15:00 - 16:30", 5: "16:30 - 18:00",
}
DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
# Créneaux interdits (IUT fermé l'après-midi)
FORBIDDEN = [("Jeudi", 3), ("Jeudi", 4), ("Jeudi", 5), ("Samedi", 3), ("Samedi", 4), ("Samedi", 5)]


def _load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_schedule_events():
    return _load_json(SCHEDULE_PATH).get("events", [])


def _week_monday(week):
    # Défaut du semestre : lundi 2026-08-31 (semaine 1). À ajuster si semester_start change.
    return date(2026, 8, 31) + timedelta(weeks=week - 1)


def _day_date(week, d_idx):
    monday = _week_monday(week)
    return monday + timedelta(days=d_idx)


def _date_label(week, d_idx):
    d = _day_date(week, d_idx)
    mois = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."]
    return f"{d.day} {mois[d.month - 1]} {d.year}"


def _iso_week(d):
    return d.isocalendar()[1]


def _find_event(lesson_id):
    for e in _load_schedule_events():
        if e.get("lesson_id") == lesson_id:
            return e
    return None


def suggest_move(lesson_id: str, target_week: int | None = None) -> dict:
    """Renvoie les créneaux compatibles pour déplacer un cours (miroir frontend)."""
    ev = _find_event(lesson_id)
    if not ev:
        return {"error": "cours introuvable", "suggestions": []}
    week = target_week or ev.get("week", 1)
    events = _load_schedule_events()
    rooms = _load_json(DATASET_PATH).get("rooms", [])
    suggestions = []
    base_week = ev.get("week", 1)

    for d_idx in range(6):
        day_name = DAYS[d_idx]
        for s in range(6):
            if d_idx == ev.get("day_idx") and s == ev.get("slot_idx") and week == base_week:
                continue
            if (day_name, s) in FORBIDDEN:
                continue
            # group libre
            if any(o.get("week") == week and o.get("day_idx") == d_idx and o.get("slot_idx") == s
                   and o.get("group_id") == ev.get("group_id") for o in events):
                continue
            # enseignant libre
            if any(o.get("week") == week and o.get("day_idx") == d_idx and o.get("slot_idx") == s
                   and o.get("teacher_name") == ev.get("teacher_name") for o in events):
                continue
            # salles libres
            free_rooms = [r for r in rooms if not any(
                o.get("week") == week and o.get("day_idx") == d_idx and o.get("slot_idx") == s
                and o.get("room_id") == r.get("id") for o in events)]
            if not free_rooms:
                continue
            suggestions.append({
                "day": day_name,
                "day_idx": d_idx,
                "slot_idx": s,
                "slot_time": SLOT_TIMES[s],
                "week": week,
                "iso_week": _iso_week(_week_monday(week)),
                "date": _day_date(week, d_idx).isoformat(),
                "date_label": _date_label(week, d_idx),
                "free_rooms": [{"id": r.get("id"), "name": r.get("name"), "type": r.get("type")} for r in free_rooms[:3]],
            })

    suggestions.sort(key=lambda x: (x["day_idx"], x["slot_idx"]))
    return {"lesson_id": lesson_id, "week": week, "iso_week": _iso_week(_week_monday(week)), "suggestions": suggestions[:15]}


def suggest_room(lesson_id: str) -> dict:
    """Renvoie les salles libres/recommandées pour le créneau courant d'un cours."""
    ev = _find_event(lesson_id)
    if not ev:
        return {"error": "cours introuvable", "suggestions": []}
    week = ev.get("week", 1)
    events = _load_schedule_events()
    rooms = _load_json(DATASET_PATH).get("rooms", [])
    d_idx = ev.get("day_idx", 0)
    s = ev.get("slot_idx", 0)

    out = []
    for r in rooms:
        occ = any(o.get("week") == week and o.get("day_idx") == d_idx and o.get("slot_idx") == s
                  and o.get("room_id") == r.get("id") and o.get("lesson_id") != lesson_id for o in events)
        recommended = False
        et = ev.get("event_type")
        rt = r.get("type", "")
        if et == "TP" and "TP" in rt: recommended = True
        if et == "CM" and rt == "AMPHI": recommended = True
        if et == "TD" and "TD" in rt: recommended = True
        out.append({
            "id": r.get("id"), "name": r.get("name"), "type": rt, "capacity": r.get("capacity"),
            "available": not occ, "recommended": recommended,
        })

    free = [x for x in out if x["available"]]
    free.sort(key=lambda x: (not x["recommended"], x["name"]))
    return {"lesson_id": lesson_id, "rooms": free}