"""
Génération de textes type "mail" pour le responsable EDT (demandes).

Permet de produire les messages de demande (déplacement, changement de salle,
changement d'enseignant, reprogrammation) utilisés côté API/frontend, de façon
centralisée.
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEDULE_PATH = os.path.join(BASE_DIR, "data", "schedule_result.json")

# Libellés des créneaux (6 créneaux / jour).
SLOT_TIMES = {
    0: "08:00 - 09:30", 1: "09:30 - 11:00", 2: "11:00 - 12:30",
    3: "13:30 - 15:00", 4: "15:00 - 16:30", 5: "16:30 - 18:00",
}


def _load_schedule():
    if not os.path.exists(SCHEDULE_PATH):
        return {}
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _week_label(week):
    # Approximation côté backend : on reflète la semaine pédagogique 1..15.
    # (Le calcul ISO précis est fait en frontend ; ici on fournit une mention lisible.)
    return f"Semaine {week}"


def generate_text(lesson_id: str, kind: str, options: dict) -> str:
    """
    Génère un texte de demande (mail) pour le responsable EDT.

    Args:
        lesson_id (str): identifiant du cours concerné.
        kind (str): 'move', 'room', 'teacher' ou 'defer'.
        options (dict): paramètres selon le type
            - move:   target_day, target_slot_idx, target_room_id/name
            - room:   new_room_id, new_room_name
            - teacher:new_teacher
            - defer:  note

    Returns:
        str: le texte du mail.
    """
    sched = _load_schedule()
    ev = next((e for e in sched.get("events", []) if e.get("lesson_id") == lesson_id), None)
    if not ev:
        raise ValueError(f"Cours {lesson_id} introuvable.")

    cur_week = _week_label(ev.get("week", 1))
    cur_day = ev.get("day", "?")
    cur_slot = SLOT_TIMES.get(ev.get("slot_idx", 0), "")
    lines = ["Bonjour,", ""]

    if kind == "move":
        lines.append("Je souhaite modifier le créneau du cours suivant :")
        lines.extend([
            "",
            f"• Cours : {ev.get('resource_name', '')} ({ev.get('resource_code', '')})",
            f"• Groupe : {ev.get('group_id', '')}",
            f"• Enseignant : {ev.get('teacher_name', '')}",
            f"• Actuellement : {cur_week} - {cur_day} {cur_slot} - Salle {ev.get('room_name', '')}",
            "",
            "Proposition de nouveau créneau :",
            "",
            f"• Nouveau créneau : {options.get('target_day')} {SLOT_TIMES.get(int(options.get('target_slot_idx', 0)), '')} - Salle {options.get('target_room_name') or options.get('target_room_id')}",
        ])
    elif kind == "room":
        lines.append("Je souhaite modifier la salle du cours suivant :")
        lines.extend([
            "",
            f"• Cours : {ev.get('resource_name', '')} ({ev.get('resource_code', '')})",
            f"• Groupe : {ev.get('group_id', '')}",
            f"• Enseignant : {ev.get('teacher_name', '')}",
            f"• Créneau : {cur_week} - {cur_day} {cur_slot}",
            f"• Salle actuelle : {ev.get('room_name', '')}",
            "",
            "Proposition de changement :",
            "",
            f"• Nouvelle salle : {options.get('new_room_name') or options.get('new_room_id')}",
        ])
    elif kind == "teacher":
        lines.append("Je souhaite modifier l'enseignant du cours suivant :")
        lines.extend([
            "",
            f"• Cours : {ev.get('resource_name', '')} ({ev.get('resource_code', '')})",
            f"• Groupe : {ev.get('group_id', '')}",
            f"• Enseignant actuel : {ev.get('teacher_name', '')}",
            f"• Créneau : {cur_week} - {cur_day} {cur_slot}",
            f"• Salle : {ev.get('room_name', '')}",
            "",
            "Proposition de changement :",
            "",
            f"• Nouvel enseignant : {options.get('new_teacher')}",
        ])
    elif kind == "defer":
        lines.append("Je souhaite reporter la reprogrammation du cours suivant :")
        note = options.get("note") or "—"
        lines.extend([
            "",
            f"• Cours : {ev.get('resource_name', '')} ({ev.get('resource_code', '')})",
            f"• Groupe : {ev.get('group_id', '')}",
            f"• Enseignant : {ev.get('teacher_name', '')}",
            f"• Créneau actuel : {cur_week} - {cur_day} {cur_slot}",
            f"• Salle actuelle : {ev.get('room_name', '')}",
            "",
            "Merci de bien vouloir reprogrammer ce cours sur un prochain créneau disponible.",
            "",
            "Précisions : " + note,
        ])
    else:
        raise ValueError(f"Type de demande inconnu : {kind}")

    lines.extend(["", "Merci de confirmer la disponibilité et de mettre à jour l'emploi du temps.", "Cordialement."])
    return "\n".join(lines)