"""
Stockage & accès aux données (fichiers JSON) pour l'API Emplois du Temps TC.

Centralise les chemins de fichiers et les helpers de lecture/écriture utilisés
par les routers, afin d'éviter la duplication dans api/main.py.
"""
import os
import json
import sys

from fastapi import HTTPException

# Rend la racine du projet importable (solver, assistant, scripts) quel que soit le CWD.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

BASE_DIR = _ROOT
DATASET_PATH = os.path.join(BASE_DIR, "data", "dataset_tc.json")
SCHEDULE_PATH = os.path.join(BASE_DIR, "data", "schedule_result.json")
HP_SOURCES_PATH = os.path.join(BASE_DIR, "data", "hp_ical_sources.json")
CONSTRAINTS_PATH = os.path.join(BASE_DIR, "data", "constraints.json")


def get_dataset():
    """Charge le dataset départemental TC depuis data/dataset_tc.json."""
    if not os.path.exists(DATASET_PATH):
        raise HTTPException(status_code=404, detail="Dataset TC non trouvé. Exécutez extract_dataset.py.")
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_schedule():
    """Charge le planning courant depuis data/schedule_result.json."""
    if not os.path.exists(SCHEDULE_PATH):
        return {"semester": "S1", "week": 1, "status": "EMPTY", "total_events": 0, "events": []}
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_constraints_data():
    """Charge les contraintes (indispos, fermetures, évaluations, alternance)."""
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


def get_constraints_path():
    return CONSTRAINTS_PATH


def save_constraints_data(data: dict):
    with open(CONSTRAINTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_schedule(sched: dict):
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(sched, f, indent=2, ensure_ascii=False)


def save_dataset_data(data: dict):
    with open(DATASET_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)