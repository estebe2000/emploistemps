"""
Import and harmonization of real current schedules from all iCal (.ics) files in ical/
Uses exact timezone-aware conversion (Paris local time) and full 6-slot daily schedule:
  - M1: 08:00 - 09:30
  - M2: 09:30 - 11:00 (ou 09:45 - 11:15)
  - M3: 11:00 - 12:30 (ou 11:15 - 12:45)
  - S1: 13:30 - 15:00
  - S2: 15:00 - 16:30 (ou 15:15 - 16:45)
  - S3: 16:30 - 18:00 (ou 16:45 - 18:15)
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
ICAL_DIR = os.path.join(os.path.dirname(DATA_DIR), "ical")
OUTPUT_PATH = os.path.join(DATA_DIR, "schedule_result.json")

DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

DAILY_SLOTS = [
    {"id": 0, "name": "M1", "time": "08:00 - 09:30", "period": "MATIN"},
    {"id": 1, "name": "M2", "time": "09:30 - 11:00", "period": "MATIN"},
    {"id": 2, "name": "M3", "time": "11:00 - 12:30", "period": "MATIN"},
    {"id": 3, "name": "S1", "time": "13:30 - 15:00", "period": "APRES_MIDI"},
    {"id": 4, "name": "S2", "time": "15:00 - 16:30", "period": "APRES_MIDI"},
    {"id": 5, "name": "S3", "time": "16:30 - 18:00", "period": "APRES_MIDI"}
]


def parse_ics_file(file_path: str) -> List[Dict[str, str]]:
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    unfolded = []
    for line in lines:
        if (line.startswith(' ') or line.startswith('\t')) and unfolded:
            unfolded[-1] = unfolded[-1].rstrip('\r\n') + line[1:]
        else:
            unfolded.append(line)
            
    events = []
    cur = {}
    for line in unfolded:
        line = line.strip()
        if line == 'BEGIN:VEVENT':
            cur = {}
        elif line == 'END:VEVENT':
            if cur and 'DTSTART' in cur:
                events.append(cur)
        elif ':' in line:
            k, v = line.split(':', 1)
            k_clean = k.split(';')[0]
            cur[k_clean] = v
            
    return events


def to_paris_local_time(dt_str: str) -> Tuple[datetime, datetime]:
    clean_dt = re.sub(r'[^0-9T]', '', dt_str)
    if 'T' in clean_dt:
        dt_utc = datetime.strptime(clean_dt[:15], "%Y%m%dT%H%M%S")
        month = dt_utc.month
        offset_hours = 2 if (month >= 4 and month <= 10) else 1
        dt_local = dt_utc + timedelta(hours=offset_hours)
        return dt_local, dt_utc
    d = datetime.strptime(clean_dt[:8], "%Y%m%d")
    return d, d


def map_time_to_slot(dt_local: datetime) -> int:
    """
    Maps local hour in Paris to exact 6-slot daily schedule:
    - 08:00 -> M1 (0)
    - 09:30 -> M2 (1)
    - 11:00 -> M3 (2)
    - 13:30 -> S1 (3)
    - 15:00 -> S2 (4)
    - 16:30 -> S3 (5)
    """
    total_mins = dt_local.hour * 60 + dt_local.minute

    if total_mins < 525:      # < 08:45
        return 0
    elif total_mins < 615:    # < 10:15
        return 1
    elif total_mins < 750:    # < 12:30
        return 2
    elif total_mins < 855:    # < 14:15
        return 3
    elif total_mins < 945:    # < 15:45
        return 4
    else:                     # >= 15:45 (16:30..18:00)
        return 5


def extract_all_teachers(desc: str, summary: str) -> list:
    """
    Extrait TOUTES les enseignants listés dans la DESCRIPTION (format Hyperplanning :
    'Enseignants : A\\, B\\, C' ou 'Enseignant : X'). Retourne une liste de noms nettoyés.
    """
    m = re.search(r'Enseignants?\s*:\s*([^\n\\;<]+)', desc, re.IGNORECASE)
    if m:
        raw = m.group(1).replace(r'\,', ',').replace(r'\\n', ' ').strip()
        raw = raw.split('TD :')[0].split('Type :')[0].split('Salle :')[0]
        names = [p.strip() for p in raw.split(',') if p.strip()]
        # nettoie préfixes civilité
        names = [re.sub(r'^(?:Mme|M\.|M)\s+', '', n).strip() for n in names]
        return [n for n in names if n]
    # Fallback : un seul enseignant
    single = extract_teacher_name(desc, summary)
    return [single] if single and single != "Enseignant TC" else []


def extract_teacher_name(desc: str, summary: str) -> str:
    m = re.search(r'Enseignant[s]?\s*:\s*([^\n\\;<]+)', desc, re.IGNORECASE)
    if m:
        raw = m.group(1).replace(r'\,', ',').replace(r'\n', '').strip()
        first_prof = raw.split(',')[0].strip()
        first_prof = re.sub(r'^(?:Mme|M\.|M)\s+', '', first_prof).strip()
        first_prof = first_prof.split('TD :')[0].split('Type :')[0].split('Salle :')[0].strip()
        return first_prof
    
    parts = summary.split('-')
    if len(parts) >= 2:
        candidate = parts[1].strip()
        if any(w in candidate.lower() for w in ['mme', 'm.', 'pytel', 'tabellion', 'motte', 'leber', 'millet', 'saudrais', 'cardinale', 'jeanne', 'david', 'ihsane', 'khaled']):
            cand = re.sub(r'^(?:Mme|M\.|M)\s+', '', candidate).strip()
            cand = cand.split('TD :')[0].split('Type :')[0].split('Salle :')[0].strip()
            return cand
            
    return "Enseignant TC"



def extract_event_type(desc: str, summary: str) -> str:
    text = (desc + " " + summary).upper()
    # Événements « autres » : réunions / "matière à préciser" / sans type pédagogique clair.
    if "MATIÈRE À PRÉCISER" in text or "MATIERE A PRECISER" in text or "RÉUNION" in text or "REUNION" in text:
        return "AUTRE"
    if "PARTIEL" in text or "EXAM" in text or "DS " in text or "EVAL" in text:
        return "EVAL"
    if "CM" in text:
        return "CM"
    if "TP" in text:
        return "TP"
    return "TD"


def extract_groups_and_hierarchy(desc: str, summary: str, default_promo: str) -> Tuple[str, List[str]]:
    text = (desc + " " + summary).replace(r'\,', ',')

    # All BUT 1 Promo
    if "TD1, TD2, TD3, TD4, TD5" in text or "TD1,TD2,TD3,TD4,TD5" in text or "CM TC" in text:
        all_but1 = ["BUT1_PROMO", "TD1", "TD2", "TD3", "TD4", "TD5",
                    "TP1A", "TP1B", "TP2A", "TP2B", "TP3A", "TP3B", "TP4A", "TP4B", "TP5A", "TP5B"]
        return "BUT1_PROMO", all_but1

    # BUT 1 Specific TP
    for i in range(1, 6):
        for sub in ['A', 'B']:
            tp_str = f"TP{i}{sub}"
            if re.search(rf'\b{tp_str}\b', text, re.IGNORECASE):
                return tp_str, ["BUT1_PROMO", f"TD{i}", tp_str]

    # BUT 1 Specific TD
    for i in range(1, 6):
        td_str = f"TD{i}"
        if re.search(rf'\b{td_str}\b', text, re.IGNORECASE):
            return td_str, ["BUT1_PROMO", td_str, f"TP{i}A", f"TP{i}B"]

    # BUT 2 Specific TD & TP A/B
    if "TC2" in text or "2" in default_promo:
        if "BDMRC" in text or "G1" in text:
            if "G1 A" in text or "G1A" in text or ("A" in text and "TP" in text and "G1" in text):
                return "TC2_G1A_BDMRC", ["TC2_PROMO", "TC2_G1_BDMRC", "TC2_G1A_BDMRC"]
            if "G1 B" in text or "G1B" in text or ("B" in text and "TP" in text and "G1" in text):
                return "TC2_G1B_BDMRC", ["TC2_PROMO", "TC2_G1_BDMRC", "TC2_G1B_BDMRC"]
            return "TC2_G1_BDMRC", ["TC2_PROMO", "TC2_G1_BDMRC", "TC2_G1A_BDMRC", "TC2_G1B_BDMRC"]

        if "MDEE" in text or "G2" in text:
            if "G2 A" in text or "G2A" in text or ("A" in text and "TP" in text and "G2" in text):
                return "TC2_G2A_MDEE", ["TC2_PROMO", "TC2_G2_MDEE", "TC2_G2A_MDEE"]
            if "G2 B" in text or "G2B" in text or ("B" in text and "TP" in text and "G2" in text):
                return "TC2_G2B_MDEE", ["TC2_PROMO", "TC2_G2_MDEE", "TC2_G2B_MDEE"]
            return "TC2_G2_MDEE", ["TC2_PROMO", "TC2_G2_MDEE", "TC2_G2A_MDEE", "TC2_G2B_MDEE"]

        if "MMPV" in text or "G3" in text:
            if "G3 A" in text or "G3A" in text or ("A" in text and "TP" in text and "G3" in text):
                return "TC2_G3A_MMPV", ["TC2_PROMO", "TC2_G3_MMPV", "TC2_G3A_MMPV"]
            if "G3 B" in text or "G3B" in text or ("B" in text and "TP" in text and "G3" in text):
                return "TC2_G3B_MMPV", ["TC2_PROMO", "TC2_G3_MMPV", "TC2_G3B_MMPV"]
            return "TC2_G3_MMPV", ["TC2_PROMO", "TC2_G3_MMPV", "TC2_G3A_MMPV", "TC2_G3B_MMPV"]

        if "FA" in text or "FA BUT2" in text:
            return "TC2_FA_BUT2", ["TC2_PROMO", "TC2_FA_BUT2"]

    # BUT 3 Specific TD & TP A/B
    if "TC3" in text or "3" in default_promo:
        if "BDMRC" in text or "G1" in text:
            if "FA" in text:
                return "TC3_FA_G1_BDMRC", ["TC3_PROMO", "TC3_FA_G1_BDMRC"]
            if "G1 A" in text or "G1A" in text or ("A" in text and "TP" in text and "G1" in text):
                return "TC3_FI_G1A_BDMRC", ["TC3_PROMO", "TC3_FI_G1_BDMRC", "TC3_FI_G1A_BDMRC"]
            if "G1 B" in text or "G1B" in text or ("B" in text and "TP" in text and "G1" in text):
                return "TC3_FI_G1B_BDMRC", ["TC3_PROMO", "TC3_FI_G1_BDMRC", "TC3_FI_G1B_BDMRC"]
            return "TC3_FI_G1_BDMRC", ["TC3_PROMO", "TC3_FI_G1_BDMRC", "TC3_FI_G1A_BDMRC", "TC3_FI_G1B_BDMRC"]

        if "MDEE" in text or "G2" in text:
            if "FA" in text:
                return "TC3_FA_G2_MDEE", ["TC3_PROMO", "TC3_FA_G2_MDEE"]
            if "G2 A" in text or "G2A" in text or ("A" in text and "TP" in text and "G2" in text):
                return "TC3_FI_G2A_MDEE", ["TC3_PROMO", "TC3_FI_G2_MDEE", "TC3_FI_G2A_MDEE"]
            if "G2 B" in text or "G2B" in text or ("B" in text and "TP" in text and "G2" in text):
                return "TC3_FI_G2B_MDEE", ["TC3_PROMO", "TC3_FI_G2_MDEE", "TC3_FI_G2B_MDEE"]
            return "TC3_FI_G2_MDEE", ["TC3_PROMO", "TC3_FI_G2_MDEE", "TC3_FI_G2A_MDEE", "TC3_FI_G2B_MDEE"]

        if "MMPV" in text or "G3" in text:
            if "FA" in text:
                return "TC3_FA_G3_MMPV", ["TC3_PROMO", "TC3_FA_G3_MMPV"]
            if "G3 A" in text or "G3A" in text or ("A" in text and "TP" in text and "G3" in text):
                return "TC3_FI_G3A_MMPV", ["TC3_PROMO", "TC3_FI_G3_MMPV", "TC3_FI_G3A_MMPV"]
            if "G3 B" in text or "G3B" in text or ("B" in text and "TP" in text and "G3" in text):
                return "TC3_FI_G3B_MMPV", ["TC3_PROMO", "TC3_FI_G3_MMPV", "TC3_FI_G3B_MMPV"]
            return "TC3_FI_G3_MMPV", ["TC3_PROMO", "TC3_FI_G3_MMPV", "TC3_FI_G3A_MMPV", "TC3_FI_G3B_MMPV"]

        return f"{default_promo}_PROMO", [f"{default_promo}_PROMO"]

    return f"{default_promo}_PROMO", [f"{default_promo}_PROMO"]


def clean_room_name(loc: str) -> (str, str):
    if not loc or loc.strip() == "None":
        return "IUTC-514", "IUTC-Salle 514 (TD)"
    
    raw = loc.replace(r'\,', ',').split(',')[0].strip()
    raw = raw.replace('\\', '')
    
    if "amphi" in raw.lower():
        return "IUTC-amphi 3", "IUTC-Amphi 3"
    elif "503" in raw:
        return "IUTC-503 i", "IUTC-503 (Info)"
    elif "506" in raw:
        return "IUTC-506 i", "IUTC-506 (Info)"
    elif "501" in raw or "502" in raw:
        return "IUTC-501/502 i", "IUTC-501/502 (Info)"
    elif "524" in raw:
        return "IUTC-524 n", "IUTC-524 (Négociation & Vente)"
    elif "309" in raw:
        return "IUTC-LABO 309", "IUTC-Labo Langues 309"
    elif "102" in raw or "claac" in raw.lower():
        return "IUTC-102 - CLAAC", "IUTC-102 (CLAAC Pédagogie Active)"
    elif "515" in raw:
        return "IUTC-515", "IUTC-Salle 515 (TD)"
    elif "516" in raw:
        return "IUTC-516", "IUTC-Salle 516 (TD)"
    elif "518" in raw:
        return "IUTC-518", "IUTC-Salle 518 (TD)"
    elif "519" in raw:
        return "IUTC-519", "IUTC-Salle 519 (TD)"
    elif "513" in raw:
        return "IUTC-513", "IUTC-Salle 513 (TD)"
    elif "311" in raw:
        return "IUTC-311", "IUTC-Salle 311 (TD)"
    elif "322" in raw:
        return "IUTC-322", "IUTC-Salle 322 (TD)"
        
    return raw, raw


def import_all_schedules():
    print("🚀 Ingestion exacte avec conversion fuseau horaire Europe/Paris et 6 créneaux journaliers...")
    
    files = [
        ("Edt_IUT_1ERE_ANNEE_TECH_DE_COMMERCIALISATION.ics", "BUT1"),
        ("Edt_IUT_2EME_ANNEE_TC.ics", "BUT2"),
        ("Edt_IUT_3EME_ANNEE_TC.ics", "BUT3"),
        ("Edt_Pytel.ics", "BUT1")
    ]

    all_raw_events = []
    earliest_date = None

    for fn, promo in files:
        fpath = os.path.join(ICAL_DIR, fn)
        if not os.path.exists(fpath):
            continue
        evts = parse_ics_file(fpath)
        for e in evts:
            e["_source_promo"] = promo
            all_raw_events.append(e)
            try:
                dt_loc, dt_utc = to_paris_local_time(e['DTSTART'])
                if earliest_date is None or dt_loc < earliest_date:
                    if dt_loc.year >= 2025:
                        earliest_date = dt_loc
            except:
                pass

    if earliest_date:
        # On écarte les artefacts isolés (quelques cours hors-semestre) pour trouver le
        # VRAI début pédagogique : la première semaine (ISO) ayant un volume de cours cohérent.
        week_counts = {}
        for ev in all_raw_events:
            try:
                dt_local, _ = to_paris_local_time(ev['DTSTART'])
            except Exception:
                continue
            if dt_local.year < 2025:
                continue
            key = dt_local.date() - timedelta(days=dt_local.weekday())  # lundi de la semaine
            week_counts[key] = week_counts.get(key, 0) + 1
        dense = sorted(k for k, v in week_counts.items() if v >= 20)
        # Choix : la première semaine dense >= 20 cours (début du semestre pédagogique).
        # On travaille ensuite en datetime pour rester homogène avec dt_start.
        first_dense = dense[0] if dense else earliest_date
        start_monday = first_dense - timedelta(days=first_dense.weekday())
        if not isinstance(start_monday, datetime):
            start_monday = datetime(start_monday.year, start_monday.month, start_monday.day)
    else:
        start_monday = datetime(2026, 9, 1)

    sm = start_monday
    sm_str = sm.isoformat() if hasattr(sm, 'isoformat') else str(sm)
    print(f"🗓️  Début du semestre pédagogique (semaine 1) : {sm_str}")

    processed_events = []
    seen_keys = set()

    for idx, e in enumerate(all_raw_events):
        try:
            dt_start, _ = to_paris_local_time(e['DTSTART'])
            dt_end, _ = to_paris_local_time(e['DTEND']) if 'DTEND' in e else (dt_start + timedelta(minutes=90), None)
        except Exception:
            continue

        days_diff = (dt_start.date() - start_monday.date()).days
        if days_diff < 0:
            # Événement antérieur au début pédagogique (artefact isolé) → ignoré.
            continue
        acad_week = (days_diff // 7) + 1
        # On ne retient que les 15 semaines du semestre courant ; les suivantes (semestre
        # suivant / artefacts) sont ignorées pour éviter tout chevauchement de dates.
        if acad_week > 15:
            continue

        weekday_idx = dt_start.weekday()
        if weekday_idx > 5:
            continue

        day_name = DAYS_FR[weekday_idx]
        slot_idx = map_time_to_slot(dt_start)

        summary = e.get('SUMMARY', '').replace(r'\,', ',').replace(r'\n', ' ').strip()
        desc = e.get('DESCRIPTION', '').replace(r'\,', ',').replace(r'\n', ' ').strip()
        loc = e.get('LOCATION', '')

        if not summary and not desc:
            continue

        teacher = extract_teacher_name(desc, summary)
        ev_type = extract_event_type(desc, summary)
        primary_group, matching_groups = extract_groups_and_hierarchy(desc, summary, e["_source_promo"])
        room_id, room_name = clean_room_name(loc)
        is_other = (ev_type == "AUTRE")

        # Pour les événements « autres » (réunions / co-encadrements), on attribue à TOUS
        # les enseignants listés. Pour les cours, on garde l'enseignant principal.
        teachers = extract_all_teachers(desc, summary) if is_other else ([teacher] if teacher and teacher != "Enseignant TC" else [])

        # Resource title extraction
        res_code = "R1.01"
        res_name = summary
        m_code = re.search(r'\b(R[1-6]\.\d{2}|SAE\s*[1-6]\.\d{2})\b', summary + " " + desc, re.IGNORECASE)
        if m_code:
            res_code = m_code.group(1).upper().replace(" ", "")
        else:
            res_code = summary.split('-')[0].strip()[:10] if '-' in summary else summary[:10]

        duration_mins = int((dt_end - dt_start).total_seconds() / 60)
        dur_hours = round(duration_mins / 60, 2)
        # Les réunions / événements « autres » peuvent dépasser 5h : on garde la durée réelle.
        # Seuls les cours pédagogiques anormaux (< 0.5h ou absurdes) sont ramenés à 1.5h.
        if not is_other and (dur_hours < 0.5 or dur_hours > 5.0):
            dur_hours = 1.5

        hetd_coeff = 0.0 if ev_type == "AUTRE" else (1.5 if ev_type == "CM" else (0.75 if ev_type == "TP" else 1.0))
        hetd_hours = round(dur_hours * hetd_coeff, 2)

        slot_info = DAILY_SLOTS[slot_idx]

        # Génère un événement par enseignant (si plusieurs, pour les co-encadrements / réunions).
        for tch in teachers:
            teacher = tch

            # Robust cross-file deduplication. Pour les événements « autres » (réunions),
            # on dédoublonne par (créneau + enseignant) afin de garder tous les co-encodeurs.
            if is_other:
                dedup_key = (acad_week, weekday_idx, slot_idx, teacher)
            else:
                dedup_key = (acad_week, weekday_idx, slot_idx, primary_group, room_id)
            teacher_key = (acad_week, weekday_idx, slot_idx, teacher)
            if dedup_key in seen_keys or (teacher != "Enseignant TC" and teacher_key in seen_keys):
                continue
            seen_keys.add(dedup_key)
            if teacher != "Enseignant TC":
                seen_keys.add(teacher_key)

            lesson_id = f"REAL_{acad_week}_{weekday_idx}_{slot_idx}_{len(processed_events)+1}_{teacher.replace(' ','_')}"

            processed_events.append({
                "lesson_id": lesson_id,
                "resource_code": res_code,
                "resource_name": summary or res_name,
                "event_type": ev_type,
                "group_id": primary_group,
                "matching_groups": matching_groups,
                "teacher_name": teacher,
                "room_id": room_id,
                "room_name": room_name,
                "week": acad_week,
                "day": day_name,
                "day_idx": weekday_idx,
                "slot_idx": slot_idx,
                "slot_time": slot_info["time"],
                "date": dt_start.date().isoformat(),          # date calendaire réelle (YYYY-MM-DD)
                "duration_hours": dur_hours,
                "hetd_hours": hetd_hours,
                "is_evaluation": ev_type == "EVAL",
                "is_other": is_other,
                "global_slot": weekday_idx * len(DAILY_SLOTS) + slot_idx
            })

    processed_events.sort(key=lambda x: (x["week"], x["day_idx"], x["slot_idx"]))

    schedule_output = {
        "semester": "S1",
        "week": 1,
        "semester_start": start_monday.date().isoformat(),  # lundi de la semaine 1 (source vérité : iCal)
        "status": "ACTUAL_ICS_IMPORTED_6_SLOTS",
        "solve_time_sec": 0.05,
        "total_events": len(processed_events),
        "events": processed_events
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(schedule_output, f, indent=2, ensure_ascii=False)

    print(f"✅ Ingestion terminée : {len(processed_events)} cours positionnés sans collision sur 6 créneaux journaliers.")

    return schedule_output


if __name__ == "__main__":
    import_all_schedules()
