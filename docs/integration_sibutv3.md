# Intégration du microservice "Emplois du Temps" dans SkilLHub (sibutv3)

## 1. Contexte

SkilLHub (`sibutv3`) est la plateforme pédagogique du département TC (FastAPI + SQLModel,
auth Keycloak OIDC, docker-compose avec les services `ingress`, `keycloak`, `app`, `db`, …).
Elle héberge l'authentification et le référentiel des utilisateurs/groupes (rôles
`ADMIN`, `PROFESSOR`, `STUDENT`, `DEPT_HEAD`, …).

Le **microservice "Emplois du Temps TC"** (`emploistemps`) est un moteur d'emploi du temps
(OR-Tools CP-SAT) + assistant, exposé en **API REST** (FastAPI, port 8000), déjà fonctionnel.
On souhaite que SkilLHub pilote ce moteur : afficher l'EDT de chaque utilisateur, poser des
contraintes, et générer des **demandes par mail** pour le gestionnaire d'emplois du temps.

Ce document décrit l'intégration à réaliser. Il s'adresse à un LLM (ou un développeur)
chargé d'implémenter le pont côté SkilLHub.

---

## 2. Architecture cible

```
Utilisateurs (étudiants, enseignants, gestionnaire EDT)
        │  (auth Keycloak)
        ▼
SkilLHub backend  (service "app", port 8000, réseau Docker)
        │  appel HTTP interne (réseau Docker)
        ▼
Emplois du Temps microservice  (service "edt", port 8000, réseau Docker)
   - GET  /api/v1/schedule                 (EDT par enseignant ou groupe)
   - GET  /api/v1/schedule/suggest-move / suggest-room
   - POST /api/v1/admin/generate-text      (texte de demande)
   - POST /api/v1/admin/teacher/unavailability
   - (admin) sources iCal, synchro, contraintes, solveur
```

### 2.1 "Même Docker" = service séparé dans le même compose
Le microservice doit être ajouté comme **service dédié** dans le `docker-compose.yml` de
SkilLHub (ex. nom de service `edt`, `container_name: butv3_edt`). Il partage le même réseau
Docker que `app`, donc le backend SkilLHub l'appelle via le **nom de service** : `http://edt:8000`.

> ⚠️ Ne pas "mettre dans le conteneur app" : on garde deux conteneurs distincts
> (un process/moteur par conteneur), reliés par le réseau Docker.

---

## 3. Rôles & périmètre d'accès

On ajoute un rôle **`EDT_MANAGER`** (gestionnaire d'emplois du temps, accès complet).
Sinon, rôles existants :

| Rôle cible | Droits sur le microservice | Endpoints autorisés (côté SkilLHub) |
|---|---|---|
| `ADMIN` / `EDT_MANAGER` | Tout (admin, contraintes, synchro, solveur) | Tous les endpoints, y compris admin |
| `PROFESSOR` | Son EDT + poser **ses** indisponibilités + générer un mail | `GET /schedule?teacher=...`, `POST /generate-text`, `POST /teacher/unavailability` |
| `STUDENT` | Son EDT (via son groupe) | `GET /schedule?group_id=<son groupe>` (lecture) + `generate-text` (reprogrammation) |
| `DEPT_HEAD` / `STUDY_DIRECTOR` | Consulter tous les EDT | `GET /schedule` (tous) |

---

## 4. Correspondance utilisateur → entité de l'EDT

La clé : traduire l'utilisateur authentifié en paramètre de l'API EDT.

### 4.1 Enseignant
- `GET /auth/me` (SkilLHub) → `full_name` de l'utilisateur (ex: `Pytel Steeve`).
- Appel EDT : `GET http://edt:8000/api/v1/schedule?teacher=<full_name>`

> ⚠️ Le planning utilise parfois `"Nom Prénom"` (iCal) vs `"Prénom Nom"` (référentiel).
> Utiliser une normalisation ou l'inclusion de tokens des deux côtés.

### 4.2 Étudiant
- `GET /auth/me` → `User.group_id` **ou** le mapping ScoDoc (promotion/groupes).
- Appel EDT : `GET http://edt:8000/api/v1/schedule?group_id=<TD4|TP4A|BUT1_PROMO>`

> Pour l'étudiant, la liste de ses groupes vient du référentiel ScoDoc (présent dans
> SkilLHub : `User.group_id`, `promotion`, `ActivityGroup`). On renvoie l'EDT des groupes
> auxquels il appartient.

---

## 5. Workflows côté SkilLHub

### 5.1 Afficher l'EDT d'un utilisateur (semaine ou jour)
1. Résoudre l'identité (enseignant → `teacher`, étudiant → `group_id`).
2. Appeler `GET /schedule?teacher=...` (ou `?group_id=...`).
3. Filtrer côté SkilLHub par semaine (paramètre `week`) ou par jour pour l'affichage.
   *(l'API renvoie la semaine ; le filtrage jour se fait côté app)*

### 5.2 Poser une contrainte (enseignant)
- L'enseignant déclare ses indisponibilités.
- Appel : `POST http://edt:8000/api/v1/admin/teacher/unavailability`
  avec `{ "teacher_name": "<SON nom>", "day": "...", "slots": [...], "replace": true }`.
- ⚠️ **Sécurité** : vérifier côté SkilLHub que `teacher_name == full_name` de l'utilisateur
  (ou utiliser un endpoint qui dérive le nom depuis le token).

### 5.3 Préparer une demande (mail au gestionnaire EDT)
L'utilisateur choisit une action et obtient des **suggestions**, puis le texte du mail.

- **Suggestions de déplacement** : `GET /schedule/suggest-move?lesson_id=<id>`
- **Suggestions de salle** : `GET /schedule/suggest-room?lesson_id=<id>`
- **Génération du mail** : `POST /admin/generate-text` avec le `kind` adapté :
  ```json
  { "lesson_id": "...", "kind": "move|room|teacher|defer", "options": { ... } }
  ```
  Selon le `kind` :
  - `move`    : `{ "target_day": "Mardi", "target_slot_idx": 3, "target_room_id": "IUTC-514", "target_room_name": "..." }`
  - `room`    : `{ "new_room_id": "...", "new_room_name": "..." }`
  - `teacher` : `{ "new_teacher": "..." }`
  - `defer`   : `{ "note": "..." }`

- Affichage du texte dans l'UI + bouton **copier** → l'utilisateur l'envoie au gestionnaire EDT.

> Différenciation des demandes : le champ `kind` détermine le message. Le microservice
> retourne un texte de mail prêt à copier/coller pour chaque situation.

---

## 6. Endpoints API du microservice (résumé)

| Méthode | Route | Usage |
|---|---|---|
| `GET` | `/health` | santé |
| `GET` | `/api/v1/schedule?teacher=&group_id=&room=` | EDT filtré |
| `GET` | `/api/v1/schedule/suggest-move?lesson_id=` | suggestions de déplacement |
| `GET` | `/api/v1/schedule/suggest-room?lesson_id=` | suggestions de salle |
| `POST` | `/api/v1/admin/generate-text` | texte de demande (kind) |
| `POST` | `/api/v1/admin/teacher/unavailability` | indispo enseignant |
| `POST` | `/api/v1/admin/constraints` | contraintes (admin) |
| `POST` | `/api/v1/admin/ical-sources`, `/ical-sync` | sources iCal + synchro (admin) |
| `POST` | `/api/v1/solver/generate` | génération CP-SAT |
| `GET` | `/api/v1/export/ical` | export iCal |

---

## 7. Recommandations d'implémentation (SkilLHub)

1. **Client HTTP interne** : un module client dans le backend SkilLHub pointant vers
   `http://edt:8000` (variable d'env `EDT_API_URL`).
2. **Secret** : si le microservice exige un token/clé, le transmettre en `Authorization`
   (variable d'env `EDT_API_KEY`). Ne jamais l'exposer au client.
3. **Filtrage par rôle** : chaque endpoint SkilLHub du module EDT vérifie le rôle via le
   token Keycloak et limite les appels (enseignant → son nom, étudiant → son groupe).
4. **Interface** : reproduire dans SkilLHub les vues (grille, suggestions, textarea de mail)
   en **appelant les endpoints** du microservice, **sans** dupliquer la logique métier
   (contraintes, suggestions) — elle vit dans le microservice.
5. **CORS** : appel serveur-à-serveur (réseau Docker) → pas de problème. Sinon, autoriser
   l'origine de SkilLHub.

---

## 8. Checklist de mise en service

- [ ] Ajouter le service `edt` (image `emploistemps-tc:latest`) au docker-compose de SkilLHub
      sur le même réseau.
- [ ] Variable `EDT_API_URL=http://edt:8000` (+ clé si besoin).
- [ ] Module client + endpoints SkilLHub : `me/edt`, `me/edt/day`, `me/absence`, `edt/demande`.
- [ ] Vérification des rôles (EDT_MANAGER / PROFESSOR / STUDENT).
- [ ] Reproduire l'interface grille + suggestions + mail dans SkilLHub.
- [ ] Tests d'intégration (enseignant, étudiant, gestionnaire).

---
*Document prêt pour l'implémentation du pont côté SkilLHub.*