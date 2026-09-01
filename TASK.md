# TASK.md — Suivi des tâches

> Mettre à jour immédiatement chaque tâche terminée (✓). Ajouter toute tâche découverte sous « Discovered During Work ».

## Terminé (reprise du déploiement, session 09/2026)
- [x] **Revue de code initiale** — Memory Bank créé (`memory-bank/`).
- [x] **1. Faille de sécurité** : retrait du jeton Albert en clair de `assistant/copilot.py` (lecture depuis `ALBERT_API_TOKEN`, garde-fou si absent) ; `.env.example` ; README ; recommandation de **rotation du jeton** (fuite dans git `10b99a4`).
- [x] **2. Contrat API cassé** : implémentation de `POST /api/v1/schedule/move`, `POST /api/v1/schedule/verify-conflict`, `GET /api/v1/schedule/free-slots` (alignés SDK Go + README).
- [x] **3. Suite pytest** : `tests/` (`test_conflict.py`, `test_hetd.py`), `conftest.py`, `requirements-dev.txt` ; 10 tests OK ; correction d'une incohérence `raison` → `raisons`.
- [x] **4. Contraintes HETD** : `max_hours_per_day_teacher` / `max_hours_per_day_student` appliquées au CP-SAT (faisabilité validée).
- [x] **5. CORS** : restreint à `CORS_ALLOW_ORIGINS` (défaut localhost), `allow_credentials=False`.
- [x] **8. Procédure de déploiement** : `Dockerfile`, `.dockerignore`, `docker-compose.yml` ; image construite et **conteneur déployé** (`emploistemps-tc`, port 8000) ; **validé de bout en bout dans le conteneur** (health, dataset, schedule, workload, interface, free-slots, verify-conflict, ai/chat protégé, génération CP-SAT).

## En cours
- [ ] (aucune tâche bloquée — service Docker actif)

## Terminé
- [x] **Push de la version actuelle sur `origin/main`** — 76 fichiers, aucun secret.
- [x] **Option B : purge de la clé Albert de l'historique git** : `git filter-repo --replace-text`, force-push (`a9629cf...c436906`), vérifié sur clone frais du remote (secret absent). GC + reflog purgés.
- [x] **Garde-fou anti-fuite** : `scripts/scan_secrets.py` + hook `.githooks/pre-commit`.
- [x] **`.gitignore` renforcé** : `.env.*` (sauf `.env.example`), `rqcode-*.png`, `*.jar/*.exe/*.dll/*.wsdl`, `**/nbproject/private/`.
- [x] ✅ **IMPORTANT utilisateur** : `.env` et QR restent locaux (jamais commités).

## Hyperplanning (en cours)
- [x] **Authentification CAS** fonctionnelle (`cas_authenticate`, login en `.env`).
- [x] **Accès iCal permanent** découvert + **synchro implémentée** :
  - `scripts/hp_sync.py` (télécharge les iCal, `--import` pour ingérer).
  - `data/hp_ical_sources.json` (3 promos BUT TC).
  - Résultat : **2573 cours** synchronisés depuis Hyperplanning, servis par l'API Docker.
  - Tests `tests/test_hp_sync.py` (3).
- [ ] Étendre les sources (enseignants, salles, groupes TD/TP) via `scripts/hp_explore.py`.
- [ ] Planifier la synchro périodique (cron/APScheduler) et/ou au démarrage Docker.

## Terminé
- [x] **Option B : purge de la clé Albert** de l'historique git (force-push, vérifié clone frais).
- [x] **Garde-fou anti-fuite** : `scripts/scan_secrets.py` + hook `.githooks/pre-commit`.
- [x] **`.gitignore` renforcé** : `.env.*` (sauf `.env.example`), `rqcode-*.png`, `*.jar/*.exe/*.dll/*.wsdl`, `**/nbproject/private/`, `data/hp_last_sync.json`.
- [x] ✅ `.env` et QR restent locaux (jamais commités).

## Discovered During Work
- [ ] Révocation + rotation du jeton Albert sur Etalab (obligatoire).
- [ ] Driver le build du SDK Go : Go non installé localement.
- [ ] `ai/chat` sans jeton : retourne un message d'avertissement (comportement attendu).