# Progress

## ✅ Ce qui fonctionne
- **API FastAPI** opérationnelle et déployée en Docker (`emploistemps-tc`, port 8000, **pilotable 100% par API**).
  - Données : `/health`, `/api/v1/dataset`, `/teachers`, `/resources`, `/rooms`, `/cohorts`.
  - Solveur : `/api/v1/solver/generate` (CP-SAT).
  - Planning : `/schedule` (filtres teacher/group/room), `verify-conflict`, `move`, `free-slots`, `deferred`, `reprogram`, `quick-action`, `export/ical`.
  - Admin : `admin/constraints`, `teacher-services`, `rooms`, `teacher/unavailability`, `room/closure`, `cohort/alternance`, `evaluations`, `teachers/absence`, `ical-sources`, `ical-sync` (+ status).
  - **Textes** : `POST /api/v1/admin/generate-text` (kind: move/room/teacher/defer).
  - **Suggestions** : `GET /schedule/suggest-move` et `/schedule/suggest-room`.
- **Interface web** servie à `/` ; grille (largeur complète), clic-droit → demandes par mail (salle/enseignant/déplacement/reprogrammation), admin enrichi (service HETD, salles éditables, fermetures par dates, évaluations, sources iCal, politique de déplacement), **numéros de semaine ISO réels**.
- **Synchro Hyperplanning** : `hp_sync.py` (iCal BUT1/2/3), statut temps réel.
- **Assistant IA Albert masqué** dans l'interface.
- **Refactor** : `api/` en routers + services (aucun > 283 lignes) ; frontend en fichiers (`css/style.css`, `js/*.js`).
- **Sécurité** : jeton Albert retiré + historiqe purgé ; hook pre-commit anti-fuite ; `.gitignore` renforcé.
- **Tests** : `tests/` (conflits, HETD, HP sync) — 13 tests OK.
- **SDK Go** : client REST complet.
- **Document d'intégration** : `docs/integration_sibutv3.md` (pont SkilLHub).

## ⏳ Ce qui reste à faire
- [ ] **Pont côté SkilLHub (sibutv3)** : client `http://edt:8000`, endpoints `me/edt` (semaine/jour), vérification des rôles (EDT_MANAGER/PROFESSOR/STUDENT), reproduction de l'interface.
- [ ] Verrouillage d'accès aux fichiers JSON (course) + gestion globale des erreurs.
- [ ] Unifier/documenter les modèles 4 vs 6 créneaux (solveur vs iCal).
- [ ] Rotation du jeton Albert sur Etalab (recommandée malgré la purge).
- [ ] Étendre les sources iCal (enseignants, salles, groupes TD/TP).

## Problèmes connus
- Jeton Albert poussé historiquement (purged, rotation conseillée).
- Incohérence 4 vs 6 créneaux entre moteur CP-SAT et données iCal.
- Pas de verrouillage des fichiers JSON.

## Évolution des décisions
- 09/2026 : refactor backend/frontend, Docker, interface enrichie, numéros ISO, demandes par mail, suggestions API, textes API, doc d'intégration SkilLHub.