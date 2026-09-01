"""
Routes de données : dataset, enseignants, ressources, salles, cohortes et workload HETD.
"""
import re
from typing import Optional

from fastapi import APIRouter, Query

from ..storage import get_dataset, get_schedule

router = APIRouter(prefix="/api/v1", tags=["Données"])


@router.get("/dataset")
def read_full_dataset():
    """Renvoie l'ensemble du dataset départemental TC (enseignants, ressources, salles, cohortes)."""
    return get_dataset()


@router.get("/teachers")
def list_teachers():
    """Liste tous les enseignants et intervenants avec leurs affectations."""
    return get_dataset().get("teachers", [])


@router.get("/resources")
def list_resources(semester: Optional[str] = Query(None, description="Filtrer par semestre, ex: 'S1'")):
    """Liste les ressources pédagogiques du PN avec volumes CM/TD/TP."""
    res = get_dataset().get("resources", [])
    if semester:
        res = [r for r in res if r["semester"].upper() == semester.upper()]
    return res


@router.get("/rooms")
def list_rooms():
    """Liste les salles, amphis et laboratoires avec capacités et équipements."""
    return get_dataset().get("rooms", [])


@router.get("/cohorts")
def list_cohorts():
    """Liste les cohortes (Formation Initiale et Alternance) avec leurs groupes TD/TP."""
    return get_dataset().get("cohorts", [])


def _match_teacher_name(name1: str, name2: str) -> bool:
    """Compare deux noms d'enseignant en extrayant les tokens (>=3 lettres), insensible casse."""
    if not name1 or not name2:
        return False
    toks1 = set(re.findall(r'[a-zA-ZÀ-ÿ]{3,}', name1.lower()))
    toks2 = set(re.findall(r'[a-zA-ZÀ-ÿ]{3,}', name2.lower()))
    toks1.discard("enseignant")
    toks2.discard("enseignant")
    toks1.discard("prof")
    toks2.discard("prof")
    return len(toks1.intersection(toks2)) >= 1


@router.get("/teachers/workload", tags=["Gestion des Services"])
def get_teachers_workload():
    """
    Calcule le bilan réel des services d'enseignement en Heures Équivalent TD (HETD)
    selon la réglementation officielle (1h CM = 1.5h TD, 1h TD = 1.0h TD, 4h TP = 3.0h TD / ratio 0.75).
    """
    dataset = get_dataset()
    sched = get_schedule()
    events = sched.get("events", [])

    workload_summary = []

    for t in dataset.get("teachers", []):
        t_name = t["name"]
        t_events = [e for e in events if _match_teacher_name(t_name, e.get("teacher_name", ""))]

        cm_hours = round(sum(e.get("duration_hours", 1.5) for e in t_events if e.get("event_type") == "CM"), 1)
        td_hours = round(sum(e.get("duration_hours", 1.5) for e in t_events if e.get("event_type") == "TD"), 1)
        tp_hours = round(sum(e.get("duration_hours", 1.5) for e in t_events if e.get("event_type") == "TP"), 1)
        eval_hours = round(sum(e.get("duration_hours", 1.5) for e in t_events if e.get("event_type") == "EVAL" or e.get("is_evaluation")), 1)

        total_hetd = round((cm_hours * 1.5) + (td_hours * 1.0) + (tp_hours * 0.75) + (eval_hours * 1.0), 1)

        statutaire = t.get("service_statutaire_hetd", 192)
        delta = round(total_hetd - statutaire, 1)

        status = "ÉQUILIBRÉ"
        if delta > 15:
            status = "HEURES_SUP"
        elif delta < -15:
            status = "SOUS_SERVICE"

        workload_summary.append({
            "teacher_id": t["id"],
            "teacher_name": t_name,
            "statut": t.get("statut", "PRAG" if statutaire >= 384 else ("MCF" if statutaire >= 192 else "VACATAIRE")),
            "service_statutaire_hetd": statutaire,
            "total_heures_cm": cm_hours,
            "total_heures_td": td_hours,
            "total_heures_tp": tp_hours,
            "total_hetd": total_hetd,
            "delta_hetd": delta,
            "status": status,
            "nb_cours_planifies": len(t_events)
        })

    workload_summary.sort(key=lambda x: x["teacher_name"])
    return {
        "hetd_rule": "1h CM = 1.5h TD | 1h TD = 1.0h TD | 4h TP = 3h TD (ratio 0.75)",
        "total_teachers": len(workload_summary),
        "teachers": workload_summary
    }