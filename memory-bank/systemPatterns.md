# System Patterns

## Architecture globale
```
Projet parent / Application Go (ERP, Scodoc, Orchestrateur)
              │  HTTP REST / SDK Go (client)
              ▼
   API REST FastAPI (api/main.py)  ── serve interface web (web/index.html)
              │                        │
              ▼                        ▼
   ASSISTANT IA (assistant/copilot.py)   SOLVEUR (solver/timetable_cp_sat.py)
   - Albert API / Onllama                - OR-Tools CP-SAT, 0 conflit
   - Tool calling                        - Respect PN, FI vs FA, HETD
```

## Modules
- `api/main.py` : FastAPI, middlewares CORS, schémas Pydantic, routes OpenAPI, serveur de `web/index.html`.
- `solver/timetable_cp_sat.py` : modélisation CP-SAT (variables binaires x[lesson, slot, room], hard constraints).
- `assistant/copilot.py` : client Albert API + fonctions `verifier_conflit_deplacement`, `deplacer_cours`, `trouver_creneaux_libres`.
- `data/` : `extract_dataset.py` (PN → dataset), `import_ical_schedule.py` (iCal → schedule), `referentiel_pn.json`, `dataset_tc.json`, `schedule_result.json`, `constraints.json`.
- `sdk/go/` : module Go `github.com/estebe2000/emploistemps/sdk/go` (client REST).
- `web/index.html` : interface web monofichier (grille, modales, actions).

## Contraintes CP-SAT (solveur)
1. Chaque séance posée exactement 1× (`sum == 1`).
2. Pas de collision salle / créneau.
3. Pas de collision enseignant / créneau.
4. Hiérarchie groupes BUT1 : PROMO→TDk→TPkA/TPkB (pas de chevauchement).
5. Fermetures permanentes (Jeudi PM, Samedi PM) — slots bloqués `== 0`.
6. Indisponibilités / absences enseignants — slots bloqués pour ce prof.
7. Fermetures / réservations de salles.

Optimisation (soft) : minimiser un indice de créneau (favoriser le matin).

## Persistance
Tout est stocké en **fichiers JSON** sur disque :
- `data/dataset_tc.json` (lecture seule, source de référence)
- `data/schedule_result.json` (planning courant, modifiable par les endpoints)
- `data/constraints.json` (contraintes admin : évaluations, indispos, absences, réservations)

## Règles HETD appliquées
- CM : × 1.5 ; TD : × 1.0 ; TP : × 0.75. (4h TP = 3h TD)
- `api/main.py` `/api/v1/teachers/workload` calcule le bilan par enseignant.

## Décision d'architecture clés
- Microservices API-first + SDK Go pour intégration dans `sibutv3`.
- IA souveraine (Albert/Etalab) avec fallback Ollama ; création de la règle **toute intégration IA passe par ollama sauf indication contraire**.
- Écarts connus : le solveur CP-SAT est en **4 créneaux/jour**, alors que le pipeline iCal d'import produit **6 créneaux/jour** (voir `activeContext`).