# Tech Context

## Stack technique
- **Python 3.12** (environnement local confirmé : `Python 3.12.10`).
- **FastAPI** (0.141.1) + **Uvicorn** (0.52.4) — serveur HTTP.
- **Pydantic** (2.13.5) — validation des schémas.
- **OR-Tools** (9.15.6755) — CP-SAT (`ortools.sat.python.cp_model`).
- **openpyxl** (3.1.5) — lecture du fichier Excel de pilotage.
- **pandas** (3.0.5), **requests** (2.34.2).
- **Go** : SDK Go (`sdk/go`) — **Go n'est PAS installé localement** (vérifié `go` introuvable). Non requis pour lancer l'API.
- **Front** : `web/index.html` monofichier HTML/JS (vanilla), servi par FastAPI.

## Dépendances (requirements.txt)
```
ortools>=9.15.0
openpyxl>=3.1.5
pydantic>=2.13.0
requests>=2.34.0
fastapi>=0.141.0
uvicorn>=0.52.0
pandas>=3.0.0
```

## Exécution
- Démarrage : `uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload`
- Docs : `/docs` (Swagger), `/redoc`.
- Interface : `/`.
- Scripts data : `python data/extract_dataset.py`, `python data/import_ical_schedule.py`.
- Test de regénération : `python solver/timetable_cp_sat.py`.

## Configuration / variables d'environnement
- `ALBERT_API_URL` (def `https://albert.api.etalab.gouv.fr/v1`)
- `ALBERT_API_TOKEN` — **⚠️ une valeur en clair est codée en dur dans `assistant/copilot.py` (faille sécurité)**
- `ALBERT_MODEL` (def `mistral-small-3-2-24b-instruct-2506`)

## Outils & contraintes plateforme
- OS : **Windows** — toutes les commandes en **PowerShell**.
- Générz des données volumineuses : `data/schedule_result.json` (~2 Mo, 2840 événements), `data/referentiel_pn.json` (~529 Ko).

## Environnement cible de déploiement
- Non défini explicitement. Le lancement local (uvicorn) fonctionne. Possibilités à trancher : NSSM (service Windows), Docker, systemd (Linux). Voir TASK.md.