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

## Restant
- [ ] **6. Aligner les modèles 4 vs 6 créneaux** (solveur / iCal / copilote) — unifier ou documenter.
- [ ] **7. Durcir** : verrouillage des fichiers JSON (race), gestion globale des erreurs.
- [ ] **9. Valider le déploiement de bout en bout** : ✅ fait en conteneur (revoir si arrêt/rebuild désiré).
- [ ] Rotation du jeton Albert sur Etalab.

## Discovered During Work
- [ ] Révocation + rotation du jeton Albert sur Etalab (obligatoire).
- [ ] Driver le build du SDK Go : Go non installé localement.
- [ ] `ai/chat` sans jeton : retourne un message d'avertissement (comportement attendu).