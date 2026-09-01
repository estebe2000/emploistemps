"""
Extraction and harmonization of BUT TC pedagogical repository and teacher assignments.
Combines:
1. National Educational Program (PN) from referentiel_pn.json
2. Departmental Teacher Assignments & Workloads from Export_Pilotage_Departemental_Stages_20260901_1907.xlsx
"""

import os
import sys
import json
import re
import openpyxl

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


DATA_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(os.path.dirname(DATA_DIR), "Export_Pilotage_Departemental_Stages_20260901_1907.xlsx")
PN_JSON_PATH = os.path.join(DATA_DIR, "referentiel_pn.json")
OUTPUT_PATH = os.path.join(DATA_DIR, "dataset_tc.json")


def extract_semester_from_code(code: str) -> str:
    """Extract semester (e.g. 'R1.01' -> 'S1', 'SAE 2.03' -> 'S2')."""
    match = re.search(r'[RS](\d)', code, re.IGNORECASE)
    if match:
        return f"S{match.group(1)}"
    return "S1"


def parse_hours_distribution(total_hours: int, details_text: str = "") -> dict:
    """
    Decomposes total hours into CM, TD, TP.
    Example: '24 heures dont 20 heures de TP' -> {'CM': 0, 'TD': 4, 'TP': 20}
    Standard default IUT ratio if unspecified: ~20% CM, 40% TD, 40% TP.
    """
    tp = 0
    td = 0
    cm = 0
    
    if details_text:
        tp_match = re.search(r'(\d+)\s*h(?:eures?)?\s*de\s*TP', details_text, re.IGNORECASE)
        if tp_match:
            tp = int(tp_match.group(1))
        
        td_match = re.search(r'(\d+)\s*h(?:eures?)?\s*de\s*TD', details_text, re.IGNORECASE)
        if td_match:
            td = int(td_match.group(1))

        cm_match = re.search(r'(\d+)\s*h(?:eures?)?\s*de\s*CM', details_text, re.IGNORECASE)
        if cm_match:
            cm = int(cm_match.group(1))
            
    remaining = max(0, total_hours - (tp + td + cm))
    if remaining > 0:
        if total_hours <= 12:
            td += remaining
        elif tp > 0 and cm == 0 and td == 0:
            td += remaining
        else:
            # Default split: ~1/3 CM, 2/3 TD
            calc_cm = (remaining // 3)
            calc_td = remaining - calc_cm
            cm += calc_cm
            td += calc_td

    return {
        "CM": cm,
        "TD": td,
        "TP": tp,
        "total": total_hours
    }


def build_dataset():
    print(f"Loading National PN Referentiel from {PN_JSON_PATH}...")
    with open(PN_JSON_PATH, "r", encoding="utf-8") as f:
        pn_data = json.load(f)

    print(f"Loading Excel file from {EXCEL_PATH}...")
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

    # 1. Teachers extraction
    teachers = {}
    if "👥 Charge Enseignants" in wb.sheetnames:
        ws_teach = wb["👥 Charge Enseignants"]
        for row in ws_teach.iter_rows(min_row=5, values_only=True):
            if row and row[0]:
                name = str(row[0]).strip()
                teachers[name] = {
                    "id": f"T_{len(teachers)+1:02d}",
                    "name": name,
                    "max_hours_per_day": 6,
                    "unavailabilities": [], # list of [day, slot]
                    "assigned_resources": []
                }

    # 2. Resources extraction with Teacher assignments
    resources = {}
    pn_resources = {r.get("code"): r for r in pn_data.get("resources", [])}
    
    if "📚 Ressources Pedagogiques" in wb.sheetnames:
        ws_res = wb["📚 Ressources Pedagogiques"]
        for row in ws_res.iter_rows(min_row=5, values_only=True):
            if not row or not row[1]:
                continue
            code = str(row[1]).strip()
            libelle = str(row[2]).strip() if row[2] else ""
            volume = int(row[4]) if row[4] and str(row[4]).isdigit() else 20
            parcours = str(row[5]).strip() if row[5] else "Tronc Commun"
            responsable = str(row[6]).strip() if row[6] else ""
            equipe_str = str(row[7]).strip() if row[7] else ""
            
            # Parse team members
            team = []
            if equipe_str:
                for member in equipe_str.split(","):
                    clean_name = re.sub(r'\(.*?\)', '', member).strip()
                    if clean_name:
                        team.append(clean_name)
                        if clean_name not in teachers:
                            teachers[clean_name] = {
                                "id": f"T_{len(teachers)+1:02d}",
                                "name": clean_name,
                                "max_hours_per_day": 6,
                                "unavailabilities": [],
                                "assigned_resources": []
                            }
                        teachers[clean_name]["assigned_resources"].append(code)

            pn_info = pn_resources.get(code, {})
            hours_details = pn_info.get("hours_details", "")
            semester = extract_semester_from_code(code)
            
            hours_split = parse_hours_distribution(volume, hours_details)

            resources[code] = {
                "code": code,
                "label": libelle or pn_info.get("label", code),
                "semester": semester,
                "parcours": parcours,
                "volume_total": volume,
                "hours_split": hours_split,
                "responsable": responsable,
                "team": team,
                "requires_computer_lab": hours_split["TP"] > 0
            }

    # 3. Default Rooms setup for IUT TC
    rooms = [
        {"id": "AMPHI_1", "name": "Amphithéâtre TC 1", "capacity": 120, "type": "AMPHI", "equipments": ["VIDEO", "MIC"]},
        {"id": "AMPHI_2", "name": "Amphithéâtre TC 2", "capacity": 80, "type": "AMPHI", "equipments": ["VIDEO", "MIC"]},
        {"id": "SALLE_101", "name": "Salle TD 101", "capacity": 35, "type": "TD", "equipments": ["VIDEO", "BOARD"]},
        {"id": "SALLE_102", "name": "Salle TD 102", "capacity": 35, "type": "TD", "equipments": ["VIDEO", "BOARD"]},
        {"id": "SALLE_103", "name": "Salle TD 103", "capacity": 35, "type": "TD", "equipments": ["VIDEO", "BOARD"]},
        {"id": "SALLE_104", "name": "Salle TD 104", "capacity": 35, "type": "TD", "equipments": ["VIDEO", "BOARD"]},
        {"id": "LAB_INFO_1", "name": "Lab Informatique 201", "capacity": 20, "type": "TP_INFO", "equipments": ["COMPUTERS", "VIDEO"]},
        {"id": "LAB_INFO_2", "name": "Lab Informatique 202", "capacity": 20, "type": "TP_INFO", "equipments": ["COMPUTERS", "VIDEO"]},
        {"id": "LAB_NEGO_1", "name": "Salle Négociation & Vente 301", "capacity": 18, "type": "TP_NEGO", "equipments": ["CAMERAS", "AUDIO"]},
        {"id": "LAB_LANG_1", "name": "Labo de Langues 302", "capacity": 20, "type": "TP_LANG", "equipments": ["HEADSETS", "AUDIO"]}
    ]

    # 4. Cohorts setup (Initial training vs Work-study / Alternance)
    # BUT1 (S1 & S2): 1 Promo CM (80 ét.) -> 2 TD (TD1, TD2 ~40 ét.) -> 4 TP (TP11, TP12, TP21, TP22 ~20 ét.)
    # BUT2 FI & BUT2 FA (Alternance)
    # BUT3 FI & BUT3 FA (Alternance)
    cohorts = [
        {
            "id": "BUT1_FI",
            "name": "BUT 1 TC (Formation Initiale)",
            "level": "BUT1",
            "mode": "FI",
            "size": 80,
            "groups_td": ["BUT1_TD1", "BUT1_TD2"],
            "groups_tp": ["BUT1_TP11", "BUT1_TP12", "BUT1_TP21", "BUT1_TP22"],
            "alternance_weeks": [] # No company weeks
        },
        {
            "id": "BUT2_FA",
            "name": "BUT 2 TC (Alternance)",
            "level": "BUT2",
            "mode": "FA",
            "size": 30,
            "groups_td": ["BUT2_FA_TD1"],
            "groups_tp": ["BUT2_FA_TP1", "BUT2_FA_TP2"],
            "alternance_weeks": [2, 4, 6, 8, 10, 12, 14] # Alternating company weeks
        }
    ]

    # 5. Calendar constraints (15 teaching weeks per semester, 6 days Lun..Sam, 4 slots/day)
    calendar_config = {
        "weeks_per_semester": 15,
        "catchup_weeks": [8, 15], # Semaines de rattrapage / partiels
        "days": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"],
        "daily_slots": [
            {"id": 0, "name": "M1", "time": "08:00 - 10:00", "period": "MATIN", "duration_hours": 2},
            {"id": 1, "name": "M2", "time": "10:15 - 12:15", "period": "MATIN", "duration_hours": 2},
            {"id": 2, "name": "S1", "time": "13:30 - 15:30", "period": "APRES_MIDI", "duration_hours": 2},
            {"id": 3, "name": "S2", "time": "15:45 - 17:45", "period": "APRES_MIDI", "duration_hours": 2}
        ],
        "permanent_closures": [
            {"day": "Jeudi", "period": "APRES_MIDI", "slots": [2, 3], "reason": "Fermeture Jeudi Après-midi (Sport / Vie étudiante)"},
            {"day": "Samedi", "period": "APRES_MIDI", "slots": [2, 3], "reason": "Fermeture Samedi Après-midi"}
        ]
    }


    dataset = {
        "department": "Techniques de Commercialisation (TC)",
        "teachers": list(teachers.values()),
        "resources": list(resources.values()),
        "rooms": rooms,
        "cohorts": cohorts,
        "calendar_config": calendar_config
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"✅ Successfully exported TC dataset to {OUTPUT_PATH}")
    print(f"  - Teachers extracted: {len(teachers)}")
    print(f"  - Pedagogical resources: {len(resources)}")
    print(f"  - Rooms defined: {len(rooms)}")
    print(f"  - Cohorts defined: {len(cohorts)}")


if __name__ == "__main__":
    build_dataset()
