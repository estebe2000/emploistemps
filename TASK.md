# TASK.md — Suivi des tâches

> Mettre à jour immédiatement chaque tâche terminée (✓). Ajouter toute tâche découverte sous « Discovered During Work ».

## Terminé (sécurité & fondations)
- [x] **Revue de code initiale** — Memory Bank créé (`memory-bank/`).
- [x] **Faille de sécurité** : retrait du jeton Albert en clair (lecture via `ALBERT_API_TOKEN`), garde-fou si absent, `.env.example`.
- [x] **Purge de l'historique git (option B)** : `git filter-repo`, force-push, vérifié clone frais (secret absent).
- [x] **Garde-fou anti-fuite** : `scripts/scan_secrets.py` + hook `.githooks/pre-commit`.
- [x] **`.gitignore` renforcé** + `.env` et QR restent locaux (jamais commités).
- [x] **Contrat API** : `move`, `verify-conflict`, `free-slots` implémentés (alignés SDK Go + README).
- [x] **Suite pytest** : `tests/` (conflits, HETD, HP sync), 13 tests OK.
- [x] **CORS restreint** (`CORS_ALLOW_ORIGINS`), **contraintes HETD** appliquées au CP-SAT.

## Terminé (refactor & déploiement)
- [x] **Refactor backend** : `api/` découpé en routers + storage + schemas + services (aucun > 283 lignes).
- [x] **Refactor frontend** : CSS/JS extraits (`web/css/style.css`, `web/js/*.js`), `index.html` 578 lignes.
- [x] **Docker** : image `emploistemps-tc`, conteneur déployé, pilotable **100% par API**.
- [x] **Assistant IA Albert masqué** dans l'interface ; planning en pleine largeur.

## Terminé (Hyperplanning & interface)
- [x] **Synchro Hyperplanning** : `hp_sync.py` + sources iCal (BUT1/2/3) + statut temps réel.
- [x] **Numéros de semaine ISO réels** partout (36..50 ; fin des S1..S15 trompeurs).
- [x] **Admin enrichi** : service enseignant (plein/demi/custom + bilan HETD), salles éditables (places/info/labo), fermetures par plage de dates, évaluations.
- [x] **Actions clic-droit → demandes par mail** (déplacer, changer salle, changer enseignant, reprogrammer) sans modification directe.
- [x] **Politique de déplacement** (gestionnaire EDT : avant jeudi 18h pour la semaine suivante) respectée.

## Terminé (API / intégration)
- [x] **Génération de textes EDT** : `POST /api/v1/admin/generate-text` (kind: move/room/teacher/defer).
- [x] **Suggestions exposées en API** : `GET /schedule/suggest-move` et `/schedule/suggest-room` (pour clients externes).
- [x] **Document d'intégration SkilLHub** : `docs/integration_sibutv3.md` (architecture Docker interne, rôles, workflows, checklist).

## En cours
- [ ] Pont côté SkilLHub (sibutv3) : client `http://edt:8000`, endpoints `me/edt`, vérification des rôles, reproduction de l'interface.

## Discovered During Work
- [ ] Révocation + rotation du jeton Albert sur Etalab (obligatoire).
- [ ] Driver le build du SDK Go (Go non installé localement).
- [ ] Étendre les sources iCal (enseignants, salles, groupes TD/TP).