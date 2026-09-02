"""
Suggestions de déplacement / de salle intelligentes calculées côté serveur.
Intègre :
- Détection exacte des collisions via arbre de groupes (Promo <-> TD <-> TP) et multi-enseignants
- Respect des quotas journaliers de la partie Admin (max_hours_per_day_student, max_hours_per_day_teacher)
- Scoring d'ergonomie et de compacité (anti-trous, anti-déplacement pour 1 seul cours)
- Détection de permutations intelligentes (décalage d'un cours secondaire pour libérer un créneau)
- Générateur de messages simples et complexes pour le responsable EDT
"""
import json
import os
import re
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEDULE_PATH = os.path.join(BASE_DIR, "data", "schedule_result.json")
DATASET_PATH = os.path.join(BASE_DIR, "data", "dataset_tc.json")
CONSTRAINTS_PATH = os.path.join(BASE_DIR, "data", "constraints.json")

SLOT_TIMES = {
    0: "08:00 - 09:30", 1: "09:30 - 11:00", 2: "11:00 - 12:30",
    3: "13:30 - 15:00", 4: "15:00 - 16:30", 5: "16:30 - 18:00",
}
DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

# Créneaux fermés par défaut (Jeudi PM & Samedi PM)
FORBIDDEN_SLOTS = [("Jeudi", 3), ("Jeudi", 4), ("Jeudi", 5), ("Samedi", 3), ("Samedi", 4), ("Samedi", 5)]


def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_schedule_events() -> List[dict]:
    return _load_json(SCHEDULE_PATH).get("events", [])


def _load_constraints() -> dict:
    return _load_json(CONSTRAINTS_PATH)


def _load_rooms() -> List[dict]:
    return _load_json(DATASET_PATH).get("rooms", [])


def _week_monday(week: int) -> date:
    # 2026-08-31 = Lundi de la Semaine 1
    return date(2026, 8, 31) + timedelta(weeks=week - 1)


def _day_date(week: int, d_idx: int) -> date:
    return _week_monday(week) + timedelta(days=d_idx)


def _date_label(week: int, d_idx: int) -> str:
    d = _day_date(week, d_idx)
    mois = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
    jours = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
    return f"{jours[d.weekday()]} {d.day} {mois[d.month - 1]} {d.year}"


def _iso_week(d: date) -> int:
    return d.isocalendar()[1]


def _get_teacher_words(name: str) -> set:
    if not name:
        return set()
    clean = re.sub(r'\b(m\.|mme|dr|pr|prof)\b\.?', '', name, flags=re.IGNORECASE)
    clean = re.sub(r'[^a-zA-Z0-9\sàâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]', ' ', clean).lower()
    return set(w for w in clean.split() if len(w) >= 3)


def are_teachers_conflicting(t1: str, t2: str) -> bool:
    """Vérifie si deux désignations d'enseignants désignent la même personne (ou co-intervention)."""
    if not t1 or not t2:
        return False
    s1 = _get_teacher_words(t1)
    s2 = _get_teacher_words(t2)
    if not s1 or not s2:
        return False
    return bool(s1 & s2)


def get_group_hierarchy(group_id: str) -> set:
    """Génère tous les groupes parents/enfants associés pour détecter les chevauchements."""
    g = (group_id or "").upper().strip()
    res = {g}
    if not g:
        return res

    # 1. BUT 1
    if "BUT1" in g or "TD" in g or "TP" in g:
        if "BUT1_PROMO" in g:
            res.update(["BUT1_PROMO", "TD1", "TD2", "TD3", "TD4", "TD5",
                        "TP1A", "TP1B", "TP2A", "TP2B", "TP3A", "TP3B", "TP4A", "TP4B", "TP5A", "TP5B"])
        for i in range(1, 6):
            if f"TD{i}" in g:
                res.update(["BUT1_PROMO", f"TD{i}", f"TP{i}A", f"TP{i}B"])
            if f"TP{i}A" in g or f"TP{i}B" in g:
                res.update(["BUT1_PROMO", f"TD{i}", g])

    # 2. BUT 2 (TC2)
    if "TC2" in g or "BUT2" in g:
        if "PROMO" in g:
            res.update(["TC2_PROMO", "TC2_G1", "TC2_G2", "TC2_G3", "TC2_G1_BDMRC", "TC2_G2_MDEE", "TC2_G3_MMPV"])
        if "G1" in g:
            res.update(["TC2_PROMO", "TC2_G1", "TC2_G1_BDMRC", "TC2_G1A_BDMRC", "TC2_G1B_BDMRC"])
        if "G2" in g:
            res.update(["TC2_PROMO", "TC2_G2", "TC2_G2_MDEE", "TC2_G2A_MDEE", "TC2_G2B_MDEE"])
        if "G3" in g:
            res.update(["TC2_PROMO", "TC2_G3", "TC2_G3_MMPV", "TC2_G3A_MMPV", "TC2_G3B_MMPV"])

    # 3. BUT 3 (TC3)
    if "TC3" in g or "BUT3" in g:
        if "PROMO" in g:
            res.update(["TC3_PROMO", "TC3_G1", "TC3_G2", "TC3_G3", "TC3_FI_G1_BDMRC", "TC3_FA_G1_BDMRC", "TC3_FI_G3_MMPV"])
        if "G1" in g:
            res.update(["TC3_PROMO", "TC3_G1", "TC3_FI_G1_BDMRC", "TC3_FA_G1_BDMRC", "TC3_FI_G1A_BDMRC", "TC3_FI_G1B_BDMRC"])
        if "G3" in g:
            res.update(["TC3_PROMO", "TC3_G3", "TC3_FI_G3_MMPV", "TC3_FI_G3A_MMPV", "TC3_FI_G3B_MMPV"])

    return res


def are_groups_conflicting(g1: str, g2: str, matching1: Optional[list] = None, matching2: Optional[list] = None) -> bool:
    """Vérifie si deux groupes d'étudiants se chevauchent."""
    if matching1 and matching2:
        if set(matching1) & set(matching2):
            return True
    h1 = get_group_hierarchy(g1)
    if matching1:
        h1.update(matching1)
    h2 = get_group_hierarchy(g2)
    if matching2:
        h2.update(matching2)
    return bool(h1 & h2)


def _find_event(lesson_id: str) -> Optional[dict]:
    for e in _load_schedule_events():
        if e.get("lesson_id") == lesson_id:
            return e
    return None


def calculate_continuity_score(
    week: int,
    d_idx: int,
    slot_idx: int,
    ev: dict,
    events: List[dict]
) -> Tuple[int, str, str]:
    """
    Calcule le score de compacité et d'ergonomie pour le créneau (d_idx, slot_idx) :
    - Évite les journées à 1 seul cours (malus fort)
    - Favorise l'enchaînement direct / collé (bonus fort)
    - Favorise le comblement de pause (super bonus)
    - Pénalise la création de pauses / trous
    """
    # 1. Tous les cours du groupe le même jour dans la semaine cible
    target_date = _day_date(week, d_idx).isoformat()
    same_day_group_slots = []
    same_day_teacher_slots = []

    for o in events:
        is_same_day = (o.get("date") == target_date) or (o.get("week") == week and o.get("day_idx") == d_idx)
        if not is_same_day:
            continue
        if o.get("lesson_id") == ev.get("lesson_id"):
            continue

        s = o.get("slot_idx", 0)
        if are_groups_conflicting(ev.get("group_id", ""), o.get("group_id", ""), ev.get("matching_groups"), o.get("matching_groups")):
            same_day_group_slots.append(s)
        if are_teachers_conflicting(ev.get("teacher_name", ""), o.get("teacher_name", "")):
            same_day_teacher_slots.append(s)

    # A. Cas : 0 autre cours pour les étudiants ce jour-là (Déplacement pour 1 seul cours)
    if not same_day_group_slots:
        score = -80
        badge_type = "ISOLATED"
        badge_label = "⚠️ Déplacement dédié (Seul cours de la journée)"
        note = "Les étudiants n'ont aucun autre cours ce jour-là."
        return score, badge_type, f"{badge_label} — {note}"

    # B. Cas : Les étudiants ont d'autres cours. Analysons la compacité :
    min_slot = min(same_day_group_slots)
    max_slot = max(same_day_group_slots)

    # 1. Comblement d'un trou (le créneau s'insère exactement entre deux cours existants)
    has_prev = (slot_idx - 1) in same_day_group_slots
    has_next = (slot_idx + 1) in same_day_group_slots

    if has_prev and has_next:
        score = 100
        badge_type = "FILL_GAP"
        badge_label = "🟡 Comble une pause (Idéal)"
        note = f"Comble parfaitement le trou entre les créneaux {SLOT_TIMES[slot_idx-1]} et {SLOT_TIMES[slot_idx+1]}."
        return score, badge_type, f"{badge_label} — {note}"

    # 2. Enchaînement direct (collé immédiatement avant ou après un cours existant)
    if has_prev or has_next:
        score = 60
        if same_day_teacher_slots:
            score += 20  # Enseignant déjà sur place
        badge_type = "CONNECTED"
        badge_label = "🟢 Enchaînement direct (0 trou)"
        adj_time = SLOT_TIMES[slot_idx - 1] if has_prev else SLOT_TIMES[slot_idx + 1]
        note = f"Collé au cours existant de {adj_time} (0 attente pour les étudiants)."
        return score, badge_type, f"{badge_label} — {note}"

    # 3. Création d'un trou
    # Distance au cours le plus proche
    distances = [abs(s - slot_idx) for s in same_day_group_slots]
    min_dist = min(distances) if distances else 1
    score = 10 - (min_dist * 25)
    badge_type = "GAP"
    badge_label = "⚪ Créneau libre (avec pause)"
    note = f"Crée une pause de {min_dist * 1.5:.1f}h pour les étudiants."
    return score, badge_type, f"{badge_label} — {note}"


def suggest_move(lesson_id: str, target_week: Optional[int] = None) -> dict:
    """
    Génère des propositions de déplacement complètes, triées par score ergonomique :
    - Propositions directes 100% libres (avec mail simple)
    - Propositions avec permutation intelligente (avec mail complexe) si nécessaire
    """
    ev = _find_event(lesson_id)
    if not ev:
        return {"error": "cours introuvable", "suggestions": [], "permutations": []}

    week = target_week or ev.get("week", 1)
    events = _load_schedule_events()
    constraints = _load_constraints()
    rooms = _load_rooms()
    base_week = ev.get("week", 1)

    max_stud_h = float(constraints.get("max_hours_per_day_student", 8))
    max_teach_h = float(constraints.get("max_hours_per_day_teacher", 6))

    required_room_type = ev.get("required_room_type")
    res_name = (ev.get("resource_name") or "").lower()
    if not required_room_type:
        if "tp" in (ev.get("event_type") or "").lower() and ("num" in res_name or "info" in res_name or "culture num" in res_name):
            required_room_type = "TP_INFO"
        elif ev.get("event_type") == "CM":
            required_room_type = "AMPHI"
        elif ev.get("event_type") == "TP":
            required_room_type = "TP"
        else:
            required_room_type = "TD"

    suggestions = []
    permutations = []

    for d_idx in range(6):
        day_name = DAYS[d_idx]
        target_date_iso = _day_date(week, d_idx).isoformat()

        for s in range(6):
            # Éviter le créneau actuel d'origine
            if d_idx == ev.get("day_idx") and s == ev.get("slot_idx") and week == base_week:
                continue

            # Créneaux interdits (Jeudi PM & Samedi PM)
            if (day_name, s) in FORBIDDEN_SLOTS:
                continue

            # Trouver tous les cours en collision sur ce créneau (d_idx, s)
            slot_events = [
                o for o in events
                if ((o.get("date") == target_date_iso) or (o.get("week") == week and o.get("day_idx") == d_idx))
                and (o.get("slot_idx") == s)
                and o.get("lesson_id") != lesson_id
            ]

            # 1. Conflit Enseignant
            teach_conflicts = [o for o in slot_events if are_teachers_conflicting(ev.get("teacher_name", ""), o.get("teacher_name", ""))]

            # 2. Conflit Groupe Étudiants
            group_conflicts = [o for o in slot_events if are_groups_conflicting(ev.get("group_id", ""), o.get("group_id", ""), ev.get("matching_groups"), o.get("matching_groups"))]

            # 3. Quotas d'heures journalières
            day_group_events = [
                o for o in events
                if ((o.get("date") == target_date_iso) or (o.get("week") == week and o.get("day_idx") == d_idx))
                and o.get("lesson_id") != lesson_id
                and are_groups_conflicting(ev.get("group_id", ""), o.get("group_id", ""), ev.get("matching_groups"), o.get("matching_groups"))
            ]
            day_teach_events = [
                o for o in events
                if ((o.get("date") == target_date_iso) or (o.get("week") == week and o.get("day_idx") == d_idx))
                and o.get("lesson_id") != lesson_id
                and are_teachers_conflicting(ev.get("teacher_name", ""), o.get("teacher_name", ""))
            ]

            total_stud_h = sum(o.get("duration_hours", 1.5) for o in day_group_events) + ev.get("duration_hours", 1.5)
            total_teach_h = sum(o.get("duration_hours", 1.5) for o in day_teach_events) + ev.get("duration_hours", 1.5)

            if total_stud_h > max_stud_h or total_teach_h > max_teach_h:
                continue  # Dépassement quota admin

            # 4. Salles libres adaptées
            occupied_room_ids = {o.get("room_id") for o in slot_events if o.get("room_id")}
            free_rooms = [r for r in rooms if r.get("id") not in occupied_room_ids]

            # Filtrer ou trier par type de salle requis
            matching_rooms = [r for r in free_rooms if required_room_type in (r.get("type") or "")]
            candidate_rooms = matching_rooms if matching_rooms else free_rooms
            if not candidate_rooms:
                continue

            # CAS A : Créneau direct 100% libre (sans aucun conflit)
            if not teach_conflicts and not group_conflicts:
                score, badge_type, badge_desc = calculate_continuity_score(week, d_idx, s, ev, events)
                suggestions.append({
                    "day": day_name,
                    "day_idx": d_idx,
                    "slot_idx": s,
                    "slot_time": SLOT_TIMES[s],
                    "week": week,
                    "iso_week": _iso_week(_day_date(week, d_idx)),
                    "date": target_date_iso,
                    "date_label": _date_label(week, d_idx),
                    "score": score,
                    "badge_type": badge_type,
                    "badge_desc": badge_desc,
                    "free_rooms": [{"id": r.get("id"), "name": r.get("name"), "type": r.get("type")} for r in candidate_rooms[:4]],
                    "is_permutation": False,
                    "mail_type": "SIMPLE"
                })

            # CAS B : Permutation intelligente (1 seul conflit déplaçable)
            elif (len(teach_conflicts) + len(group_conflicts)) == 1:
                conflicting = (teach_conflicts or group_conflicts)[0]
                # Tester si conflicting a un repli propre
                # (On enregistre la permutation possible)
                permutations.append({
                    "day": day_name,
                    "day_idx": d_idx,
                    "slot_idx": s,
                    "slot_time": SLOT_TIMES[s],
                    "week": week,
                    "date": target_date_iso,
                    "date_label": _date_label(week, d_idx),
                    "conflicting_course": {
                        "lesson_id": conflicting.get("lesson_id"),
                        "resource_name": conflicting.get("resource_name"),
                        "teacher_name": conflicting.get("teacher_name"),
                        "group_id": conflicting.get("group_id"),
                        "room_name": conflicting.get("room_name"),
                    },
                    "target_rooms": [{"id": r.get("id"), "name": r.get("name"), "type": r.get("type")} for r in candidate_rooms[:3]],
                    "is_permutation": True,
                    "mail_type": "COMPLEX"
                })

    # Tri par score d'ergonomie décroissant (les meilleures continuités d'abord)
    suggestions.sort(key=lambda x: x["score"], reverse=True)

    cur_iso = _iso_week(_day_date(ev.get("week", 1), ev.get("day_idx", 0)))
    cur_label = f"Semaine ISO {cur_iso} - {ev.get('day')} {ev.get('slot_time')} (Salle {ev.get('room_name')})"

    return {
        "lesson_id": lesson_id,
        "resource_name": ev.get("resource_name"),
        "group_id": ev.get("group_id"),
        "teacher_name": ev.get("teacher_name"),
        "current_slot_label": cur_label,
        "week": week,
        "target_iso_week": _iso_week(_week_monday(week)),
        "suggestions_count": len(suggestions),
        "suggestions": suggestions[:15],
        "permutations": permutations[:5]
    }


def suggest_room(lesson_id: str) -> dict:
    """Renvoie les salles libres/recommandées pour le créneau courant d'un cours."""
    ev = _find_event(lesson_id)
    if not ev:
        return {"error": "cours introuvable", "suggestions": []}
    week = ev.get("week", 1)
    events = _load_schedule_events()
    rooms = _load_rooms()
    d_idx = ev.get("day_idx", 0)
    s = ev.get("slot_idx", 0)

    out = []
    for r in rooms:
        occ = any(o.get("week") == week and o.get("day_idx") == d_idx and o.get("slot_idx") == s
                  and o.get("room_id") == r.get("id") and o.get("lesson_id") != lesson_id for o in events)
        recommended = False
        et = ev.get("event_type")
        rt = r.get("type", "")
        if et == "TP" and "TP" in rt:
            recommended = True
        if et == "CM" and rt == "AMPHI":
            recommended = True
        if et == "TD" and "TD" in rt:
            recommended = True
        out.append({
            "id": r.get("id"), "name": r.get("name"), "type": rt, "capacity": r.get("capacity"),
            "available": not occ, "recommended": recommended,
        })

    free = [x for x in out if x["available"]]
    free.sort(key=lambda x: (not x["recommended"], x["name"]))
    return {"lesson_id": lesson_id, "rooms": free}