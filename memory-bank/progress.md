# Progress

## ✅ Ce qui fonctionne
- **API FastAPI** complète et opérationnelle : démarrage `uvicorn api.main:app`.
  - `/health`, `/api/v1/dataset`, `/api/v1/teachers`, `/api/v1/resources`, `/api/v1/rooms`, `/api/v1/cohorts`.
  - `/api/v1/solver/generate` (CP-SAT), `/api/v1/schedule` (filtres), `/api/v1/teachers/workload`.
  - Administration : `admin/constraints`, `teacher/unavailability`, `room/closure`, `cohort/alternance`, `evaluations`, `teachers/absence`.
  - Planning : `schedule/deferred`, `schedule/reprogram`, `schedule/quick-action`.
  - `ai/chat` (copilote Albert), `export/ical`.
- **Interface web** (`web/index.html`) servie à `/` ; grille, clic-droit, modales, bilan HETD.
- **Import iCal** → `schedule_result.json` (2840 événements, 6 créneaux/jour, fuseau Europe/Paris).
- **Extraction dataset** → `dataset_tc.json` (33 enseignants, 15 salles, ressources, cohortes BUT1/2/3).
- **SDK Go** (`sdk/go`) : client REST complet (health, generate, schedule, workload, quick-action, ai).

## ⏳ Ce qui reste à faire
3. **Tests** : suite créée (`tests/`, 10 tests OK). Étendre au besoin.
4. **Contraintes** : `max_hours_per_day_teacher/student` désormais appliquées au CP-SAT (fait).
5. **Créneaux** : unifier les modèles 4 vs 6 créneaux/jour (solveur vs iCal vs copilote) ou documenter explicitement. *(en attente d'arbitrage)*
6. **Robustesse** : verrouillage d'accès aux fichiers JSON, gestion globale des erreurs. *(à faire)*
7. **Déploiement** : choisir et documenter le mode (NSSM / Docker / reverse-proxy), fournir script de démarrage. *(à faire)*

## Problèmes connus
- ⚠️ **Jeton Albert présent dans l'historique git** (commit `10b99a4`) → rotation/révocation obligatoire sur Etalab.
- Incohérence 4 vs 6 créneaux entre moteur CP-SAT et données importées d'iCal (à documenter/unifier).
- Pas de verrouillage des fichiers JSON (risque de course).

## Évolution des décisions
- 09/2026 : reprise du déploiement ; revue de code ; création du Memory Bank ; **sécurité (token) + contrat API + CORS + contraintes HETD + tests** traités.