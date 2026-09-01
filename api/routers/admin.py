"""
Routes d'administration & contraintes : constraints, sources iCal, synchronisation,
indisponibilités enseignants, fermetures de salles, calendrier d'alternance.
"""
import os
import json

from fastapi import APIRouter

from ..storage import (get_constraints_data, save_constraints_data,
                       HP_SOURCES_PATH, BASE_DIR, get_constraints_path)

router = APIRouter(prefix="/api/v1/admin", tags=["Administration"])


@router.get("/constraints")
def get_admin_constraints():
    """Récupère l'ensemble des contraintes configurées."""
    return get_constraints_data()


@router.post("/constraints")
def save_admin_constraints(constraints: dict):
    """Enregistre l'ensemble des contraintes départementales."""
    save_constraints_data(constraints)
    return {"status": "success", "message": "Contraintes enregistrées avec succès."}


@router.get("/ical-sources")
def get_ical_sources():
    """Récupère la configuration des sources iCal Hyperplanning (URLs de synchro)."""
    if not os.path.exists(HP_SOURCES_PATH):
        return {"version": "2022.0.5.0", "param": "", "sources": []}
    with open(HP_SOURCES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/ical-sources")
def save_ical_sources(payload: dict):
    """Enregistre la configuration des sources iCal Hyperplanning."""
    version = payload.get("version", "2022.0.5.0")
    param = payload.get("param", "")
    base = payload.get("base_url", "https://hplanning.univ-lehavre.fr")
    sources = []
    for s in payload.get("sources", []):
        sources.append({
            "key": s.get("key", "").strip() or f"SRC_{len(sources)+1}",
            "label": s.get("label", "").strip(),
            "file": s.get("file", "").strip(),
            "idICal": s.get("idICal", "").strip(),
            "url": s.get("url", "").strip(),
        })
    out = {"version": version, "param": param, "base_url": base, "sources": sources}
    with open(HP_SOURCES_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return {"status": "success", "message": f"{len(sources)} source(s) iCal enregistrée(s).", "sources": out}


@router.post("/ical-sync")
def run_ical_sync():
    """Lance la synchronisation des iCal Hyperplanning et l'ingestion dans le planning."""
    from scripts.hp_sync import run_sync
    try:
        result = run_sync(do_import=True)
        status = "success" if result.get("success") else "error"
        return {
            "status": status,
            "message": (f"✅ Synchronisation terminée : {len(result.get('downloaded', []))} iCal téléchargés"
                        f" et {result.get('total_events') or 0} cours ingérés.") if result.get("success")
                       else result.get("message", "Échec de la synchronisation."),
            "last_sync": result.get("last_sync"),
            "downloaded": result.get("downloaded"),
            "total_events": result.get("total_events"),
            "errors": result.get("errors", []),
        }
    except Exception as e:
        return {"status": "error", "message": f"Erreur synchronisation : {e}", "errors": [str(e)]}


@router.get("/ical-sync/status")
def get_ical_sync_status():
    """Retourne l'état de la dernière synchronisation iCal (en cours / succès / échec + stats)."""
    status_path = os.path.join(BASE_DIR, "data", "hp_last_sync.json")
    if not os.path.exists(status_path):
        return {"status": "idle", "running": False,
                "message": "Aucune synchronisation effectuée pour l'instant.",
                "last_sync": None, "downloaded": 0, "total_events": None}
    with open(status_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/teacher/unavailability")
def update_teacher_unavailability(payload: dict):
    """Ajoute ou met à jour l'indisponibilité d'un enseignant."""
    c = get_constraints_data()
    t_name = payload.get("teacher_name")
    unavails = c.get("teacher_unavailabilities", [])
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


@router.post("/room/closure")
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


@router.post("/cohort/alternance")
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


@router.get("/teacher-services")
def get_teacher_services():
    """Récupère les services déclarés des enseignants (mode + heures HETD)."""
    data = get_constraints_data()
    return data.get("teacher_services", {})


@router.post("/teacher-services")
def save_teacher_services(payload: dict):
    """
    Enregistre les services déclarés des enseignants.
    Format attendu : { "services": { "<Nom enseignant>": {"mode": "PLAIN|DEMI|CUSTOM", "hetd": 384} } }
    """
    services = payload.get("services", {})
    data = get_constraints_data()
    data["teacher_services"] = services
    save_constraints_data(data)
    return {"status": "success", "message": f"{len(services)} service(s) enseignant mis à jour."}


@router.get("/rooms")
def get_admin_rooms():
    """Récupère les salles avec leurs infos éditables (nb_places, informatique, labo_lang)."""
    data = get_constraints_data()
    return data.get("rooms_config", {})


@router.post("/rooms")
def save_admin_rooms(payload: dict):
    """Enregistre les infos éditables des salles (nb_places, informatique, labo_lang)."""
    rooms = payload.get("rooms", {})
    data = get_constraints_data()
    data["rooms_config"] = rooms
    save_constraints_data(data)
    return {"status": "success", "message": f"{len(rooms)} salle(s) mise(s) à jour."}


# Évaluations & absences : ces routes sont sous /api/v1 (pas /api/v1/admin) pour
# préserver le contrat existant, mais relèvent de l'administration.
router_root = APIRouter(prefix="/api/v1", tags=["Administration"])


@router_root.post("/evaluations")
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


@router_root.post("/teachers/absence")
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