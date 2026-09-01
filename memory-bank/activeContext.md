# Active Context

## Focus de travail actuel
Reprise du **déploiement** du microservice Emplois du Temps TC. Une **revue de code** vient d'être réalisée (voir « Revue de code » ci-dessous et le résumé de session).

## Derniers changements (repo)
- Derniers commits : bilan HETD (barres de progression), correction fuseau horaire (Europe/Paris) + 6 créneaux sur l'import iCal, actions clic-droit (changer salle, déplacer, différer…).
- Modification locale non commitée : `api/main.py` — ajout `import re` (+ ligne vide), probablement préparation du matching d'enseignants.

## État de fonctionnement (validé 09/2026 en local)
- Serveur se lance (`uvicorn api.main:app`), tous les endpoints principaux répondent :
  - `/health` OK ; `/api/v1/dataset` (33 enseignants, 15 salles) ; `/api/v1/schedule` (2840 événements, issus du pipeline iCal à 6 créneaux) ; `/api/v1/teachers/workload` (33 profs) ; `/` (interface web) OK.

## Problèmes critiques identifiés (revue de code)
1. 🔴 **Token Albert API en clair** dans `assistant/copilot.py` (variable par défaut) → secret à retirer + rotation du jeton.
2. 🟠 **3 endpoints documentés/absents** : `/api/v1/schedule/move`, `/api/v1/schedule/verify-conflict`, `/api/v1/schedule/free-slots` — annoncés dans le README et appelés par le SDK Go (`client.go`), **non implémentés** dans `api/main.py` → 404 pour le SDK.
3. 🟠 **Aucun jeu de tests** (pas de `tests/`, pas de pytest).
4. 🟡 **Incohérence 4 vs 6 créneaux/jour** entre le solveur CP-SAT et le pipeline iCal + descriptions dans le copilote.
5. 🟡 `max_hours_per_day_teacher/student` définis mais **jamais appliqués** en contraintes CP-SAT.
6. 🟡 CORS `allow_origins=["*"]` + `allow_credentials=True` incohérent/sans restriction.
7. 🟡 Accès concurrents non sécurisés sur les fichiers JSON (pas de verrou).

## Problèmes traités cette session (09/2026)
- ✅ **Déploiement Docker** : création `Dockerfile` (python:3.12-slim + libgomp1 pour OR-Tools), `.dockerignore`, `docker-compose.yml` (bind `./data:/app/data`, port 8000, env optionnel). Image `emploistemps-tc:latest` construite ; conteneur **up** ; **tous les endpoints validés dans le conteneur** (health, dataset, schedule 2840, workload, index, free-slots, verify-conflict, ai/chat protégé) ; solveur CP-SAT exécuté dans le conteneur (FEASIBLE).
- ⚠️ Effet de bord noté : le bind mount `./data` est partagé ; une génération CP-SAT via l'API écrase `schedule_result.json` (2840 → 36 events) aussi sur l'hôte. Restauré depuis git ; comportement volontaire (persistance), à garder en tête.
- ✅ **Token Albert API retiré de `assistant/copilot.py`** (lecture via `ALBERT_API_TOKEN`, garde-fou si absent). ⚠️ Jeton encore présent dans **git** (commit `10b99a4`) → **rotation obligatoire** sur Etalab.
- ✅ Contrat API réparé : `move`, `verify-conflict`, `free-slots` implémentés.
- ✅ CORS restreint (défaut localhost), contraintes `max_hours_per_day_*` appliquées au CP-SAT, suite pytest (10 OK).

## Décisions actives / à trancher
- Durcissement : arrêter le conteneur ? Vérifier si l'utilisateur souhaite que le service reste actif.
- Alignement des modèles **4 vs 6 créneaux** (solveur CP-SAT / iCal / copilote) → à arbitrer.
- Verrouillage des fichiers JSON + gestion globale des erreurs → à durcir.

## Sécurité / dépôt (session 09/2026)
- ✅ **Purge de l'historique (option B) de la clé Albert** : réécriture via `git filter-repo --replace-text` (installé via `pip install git-filter-repo`), substitution `→ sk-RETIRE_SECRET_ALBERT`, force-push vers `origin/main` (`a9629cf...c436906`). Vérifié sur **clone frais du remote** : secret absent. GC + reflog expiré localement.
- ⚠️ La clé était déjà exposée publiquement (historique mais aussi éventuels forks/caches). **Rotation obligatoire sur Etalab** recommandée malgré la purge.
- ✅ Périmètre committé et poussé : `.dockerignore`/`.env.example`/Docker/docker-compose/scan_secrets/hook pre-commit/memory-bank.
- ✅ **Hook pre-commit anti-fuite** : `.githooks/pre-commit` + `scripts/scan_secrets.py` (scanner fichiers staged, encodage cp1252 corrigé).
- ✅ `ical/` : exemples SOAP officiels Index Education committés (hors binaires `.jar/.exe/.wsdl` et `nbproject/private/`).
- Sécurité applicative : jeton Albert retiré du code (`ALBERT_API_TOKEN` via `.env`), CORS restreint, contraintes `max_hours_per_day_*` au CP-SAT, endpoints move/verify-conflict/free-slots implémentés.

## Prochaines étapes (voir TASK.md)
1. Renseigner `CAS_USERNAME` / `CAS_PASSWORD` dans `.env` (jamais ailleurs) → tester auth CAS + cartographier le portail mobile Hyperplanning.
2. Rotation du jeton Albert sur Etalab (recommandé malgré la purge).
3. Aligner/déclarer les modèles 4 vs 6 créneaux.
4. Durcir (verrou JSON, handler d'erreurs).