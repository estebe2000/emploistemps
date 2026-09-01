"""
AI Copilot Assistant for Timetable Management (Department TC).
Uses Etalab sovereign Albert API (or Ollama fallback) with Function Calling.
"""

import os
import sys
import json
import requests
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Albert API Configuration
ALBERT_API_URL = os.environ.get("ALBERT_API_URL", "https://albert.api.etalab.gouv.fr/v1")
ALBERT_API_TOKEN = os.environ.get(
    "ALBERT_API_TOKEN",
    "sk-RETIRE_SECRET_ALBERT"
)
ALBERT_MODEL = os.environ.get("ALBERT_MODEL", "mistral-small-3-2-24b-instruct-2506")

SCHEDULE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "schedule_result.json")
DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dataset_tc.json")


class TimetableCopilot:
    def __init__(self):
        self.load_data()

    def load_data(self):
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)
        
        if os.path.exists(SCHEDULE_PATH):
            with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
                self.schedule = json.load(f)
        else:
            self.schedule = {"events": []}

    def save_schedule(self):
        with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.schedule, f, indent=2, ensure_ascii=False)

    # --- TOOLS AVAILABLE TO THE AI ---

    def verifier_conflit_deplacement(self, lesson_id: str, cible_jour: str, cible_creneau_idx: int, cible_salle: Optional[str] = None) -> Dict[str, Any]:
        """
        Vérifie si le déplacement d'un cours vers un jour et un créneau (0=08h-10h, 1=10h15-12h15, 2=13h30-15h30, 3=15h45-17h45)
        provoque un conflit de salle, d'enseignant ou de groupe d'étudiants.
        """
        events = self.schedule.get("events", [])
        target_event = next((e for e in events if e["lesson_id"] == lesson_id), None)
        if not target_event:
            return {"conflit": True, "raison": f"Cours avec l'identifiant {lesson_id} introuvable."}

        teacher = target_event["teacher_name"]
        group = target_event["group_id"]
        room = cible_salle or target_event["room_id"]

        conflits = []

        # Parcourir les autres cours sur ce créneau cible
        for e in events:
            if e["lesson_id"] == lesson_id:
                continue
            if e["day"].lower() == cible_jour.lower() and e["slot_idx"] == cible_creneau_idx:
                # 1. Conflit Enseignant
                if e["teacher_name"].lower() == teacher.lower():
                    conflits.append(f"L'enseignant {teacher} a déjà le cours {e['resource_code']} ({e['event_type']}) sur ce créneau.")
                # 2. Conflit Salle
                if (e.get("room_id") == room or e.get("room_name") == room):
                    conflits.append(f"La salle {e['room_name']} est déjà occupée par {e['resource_code']} ({e['group_id']}).")
                # 3. Conflit Groupe / Sous-groupe
                if e["group_id"] == group or "PROMO" in e["group_id"] or "PROMO" in group:
                    conflits.append(f"Le groupe {group} a déjà un cours programmé ({e['resource_code']}).")

        if conflits:
            return {
                "conflit": True,
                "autorise": False,
                "raisons": conflits,
                "message": f"❌ Impossible de déplacer le cours : {'; '.join(conflits)}"
            }
        else:
            return {
                "conflit": False,
                "autorise": True,
                "message": f"✅ Déplacement autorisé : aucun conflit détecté pour {teacher} en {room} le {cible_jour} créneau {cible_creneau_idx}."
            }

    def deplacer_cours(self, lesson_id: str, cible_jour: str, cible_creneau_idx: int, cible_salle: Optional[str] = None) -> Dict[str, Any]:
        """
        Déplace effectivement un cours après validation des conflits.
        """
        verif = self.verifier_conflit_deplacement(lesson_id, cible_jour, cible_creneau_idx, cible_salle)
        if verif["conflit"]:
            return verif

        events = self.schedule.get("events", [])
        slots_cfg = self.dataset["calendar_config"]["daily_slots"]
        day_names = self.dataset["calendar_config"]["days"]
        day_idx = next((i for i, d in enumerate(day_names) if d.lower() == cible_jour.lower()), 0)

        for e in events:
            if e["lesson_id"] == lesson_id:
                e["day"] = cible_jour.capitalize()
                e["day_idx"] = day_idx
                e["slot_idx"] = cible_creneau_idx
                e["slot_time"] = slots_cfg[cible_creneau_idx]["time"]
                e["global_slot"] = day_idx * len(slots_cfg) + cible_creneau_idx
                if cible_salle:
                    room_obj = next((r for r in self.dataset["rooms"] if r["id"] == cible_salle or r["name"] == cible_salle), None)
                    if room_obj:
                        e["room_id"] = room_obj["id"]
                        e["room_name"] = room_obj["name"]

        self.save_schedule()
        return {
            "success": True,
            "message": f"✅ Cours {lesson_id} déplacé avec succès au {cible_jour.capitalize()} à {slots_cfg[cible_creneau_idx]['time']}."
        }

    def trouver_creneaux_libres(self, enseignant: str, groupe_id: str) -> List[Dict[str, Any]]:
        """
        Trouve tous les créneaux de la semaine où un enseignant ET un groupe sont simultanément libres.
        """
        events = self.schedule.get("events", [])
        days = self.dataset["calendar_config"]["days"]
        slots = self.dataset["calendar_config"]["daily_slots"]

        creneaux_libres = []

        for d_idx, day in enumerate(days):
            for s_idx, slot in enumerate(slots):
                # Vérifier occupation
                occupes = [
                    e for e in events
                    if e["day_idx"] == d_idx and e["slot_idx"] == s_idx and
                    (e["teacher_name"].lower() == enseignant.lower() or e["group_id"] == groupe_id or "PROMO" in e["group_id"])
                ]
                if not occupes:
                    creneaux_libres.append({
                        "jour": day,
                        "slot_idx": s_idx,
                        "heure": slot["time"]
                    })

        return creneaux_libres

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Executes a tool called by the LLM."""
        if tool_name == "verifier_conflit_deplacement":
            return json.dumps(self.verifier_conflit_deplacement(
                lesson_id=args.get("lesson_id"),
                cible_jour=args.get("cible_jour"),
                cible_creneau_idx=int(args.get("cible_creneau_idx", 0)),
                cible_salle=args.get("cible_salle")
            ), ensure_ascii=False)
        elif tool_name == "deplacer_cours":
            return json.dumps(self.deplacer_cours(
                lesson_id=args.get("lesson_id"),
                cible_jour=args.get("cible_jour"),
                cible_creneau_idx=int(args.get("cible_creneau_idx", 0)),
                cible_salle=args.get("cible_salle")
            ), ensure_ascii=False)
        elif tool_name == "trouver_creneaux_libres":
            return json.dumps(self.trouver_creneaux_libres(
                enseignant=args.get("enseignant"),
                groupe_id=args.get("groupe_id")
            ), ensure_ascii=False)
        return json.dumps({"error": f"Outil inconnu : {tool_name}"})

    def chat(self, user_prompt: str) -> str:
        """
        Sends a query to Albert API with defined tool definitions and returns the AI response.
        """
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "verifier_conflit_deplacement",
                    "description": "Vérifie si déplacer un cours vers un jour et un créneau spécifique cause un conflit. La salle est facultative (si omise, conserve la salle actuelle du cours).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lesson_id": {"type": "string", "description": "L'ID du cours (ex: 'R1.01_CM', '47_CM', etc.)"},
                            "cible_jour": {"type": "string", "description": "Le jour visé ('Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi')"},
                            "cible_creneau_idx": {"type": "integer", "description": "L'indice du créneau : 0 pour 8h-10h, 1 pour 10h15-12h15, 2 pour 13h30-15h30, 3 pour 15h45-17h45"}
                        },
                        "required": ["lesson_id", "cible_jour", "cible_creneau_idx"]
                    }
                }
            },

            {
                "type": "function",
                "function": {
                    "name": "deplacer_cours",
                    "description": "Déplace un cours sur un créneau libre sans conflit.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lesson_id": {"type": "string", "description": "L'ID unique du cours à déplacer"},
                            "cible_jour": {"type": "string", "description": "Le jour visé"},
                            "cible_creneau_idx": {"type": "integer", "description": "L'indice du créneau (0 à 3)"},
                            "cible_salle": {"type": "string", "description": "Optionnel: nouvelle salle"}
                        },
                        "required": ["lesson_id", "cible_jour", "cible_creneau_idx"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "trouver_creneaux_libres",
                    "description": "Trouve les créneaux disponibles où un enseignant et un groupe d'étudiants sont tous les deux libres.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "enseignant": {"type": "string", "description": "Nom de l'enseignant"},
                            "groupe_id": {"type": "string", "description": "Identifiant du groupe (ex: 'BUT1_TD1', 'BUT1_PROMO')"}
                        },
                        "required": ["enseignant", "groupe_id"]
                    }
                }
            }
        ]

        system_msg = {
            "role": "system",
            "content": (
                "Tu es l'Assistant IA expert en gestion d'emplois du temps pour le département TC (IUT Techniques de Commercialisation). "
                "Tu aides le responsable pédagogique à consulter, ajuster et déplacer des cours. "
                "Tu as accès à des outils pour vérifier les conflits et trouver des créneaux libres. "
                "Sois toujours précis, concis, bienveillant et professionnel en français."
            )
        }

        messages = [system_msg, {"role": "user", "content": user_prompt}]

        headers = {
            "Authorization": f"Bearer {ALBERT_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": ALBERT_MODEL,
            "messages": messages,
            "tools": tools,
            "temperature": 0.2
        }

        try:
            resp = requests.post(f"{ALBERT_API_URL}/chat/completions", headers=headers, json=payload, timeout=25)
            if resp.status_code != 200:
                return f"Erreur API Albert ({resp.status_code}): {resp.text}"

            resp_data = resp.json()
            message = resp_data["choices"][0]["message"]
            raw_content = message.get("content", "") or ""

            # Check if LLM requested tool calling via native tool_calls OR text format [TOOL_CALLS]
            tool_calls = message.get("tool_calls", [])
            
            # Text format parsing fallback for Mistral: [TOOL_CALLS]func_name{args}
            if not tool_calls and "[TOOL_CALLS]" in raw_content:
                import re
                match = re.search(r'\[TOOL_CALLS\]\s*([a-zA-Z0-9_]+)\s*(\{.*?\})', raw_content, re.DOTALL)
                if match:
                    tool_calls = [{
                        "id": "call12345",
                        "type": "function",
                        "function": {
                            "name": match.group(1),
                            "arguments": match.group(2)
                        }
                    }]

            if tool_calls:
                # Update message format if needed
                message["tool_calls"] = tool_calls
                messages.append(message)
                for tool in tool_calls:
                    fn_name = tool["function"]["name"]
                    fn_args = json.loads(tool["function"]["arguments"]) if isinstance(tool["function"]["arguments"], str) else tool["function"]["arguments"]
                    print(f"🤖 [IA Tool Call] Exécution de '{fn_name}' avec arguments:", fn_args)
                    tool_res = self.execute_tool(fn_name, fn_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool.get("id") or "call12345",
                        "name": fn_name,
                        "content": tool_res
                    })


                # Second call to get final synthesized response
                payload["messages"] = messages
                payload.pop("tools", None)
                resp2 = requests.post(f"{ALBERT_API_URL}/chat/completions", headers=headers, json=payload, timeout=25)
                if resp2.status_code == 200:
                    final_msg = resp2.json()["choices"][0]["message"]["content"]
                    return final_msg
                else:
                    return f"Erreur retour second appel : {resp2.text}"

            return raw_content

        except Exception as e:
            return f"Exception lors de l'appel à l'IA : {str(e)}"



if __name__ == "__main__":
    copilot = TimetableCopilot()
    print("Test 1: Demande à l'IA de trouver des créneaux libres pour Thierry Tabellion...")
    reply = copilot.chat("Quels sont les créneaux disponibles pour planifier un rattrapage avec M. Thierry Tabellion pour le groupe BUT1_TD1 ?")
    print("\nRéponse de l'Assistant IA :")
    print(reply)
