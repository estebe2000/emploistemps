# 📅 Emplois du Temps TC — Moteur CP-SAT & Assistant IA Souverain

Application et microservice d'optimisation d'emplois du temps pour le département **Techniques de Commercialisation (TC)**, combinant un **moteur déterministe (Google OR-Tools CP-SAT)** et un **Copilote IA Souverain outillé (API Albert / Etalab)**.

Ce projet est conçu comme un **sous-projet / microservice API-First**, intégrable facilement dans une architecture globale via **REST OpenAPI** et via son **SDK Go (Golang)** dédié.

---

## 🌟 Architecture Globale

```
┌────────────────────────────────────────────────────────┐
│            PROJET PARENT / APPLICATION GO              │
│    (Orchestrateur, ERP Universitaire, Scodoc, etc.)   │
└───────────────────────────┬────────────────────────────┘
                            │
              Appels HTTP / SDK Go (Client)
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               API REST FASTAPI (Python)                │
│    - Endpoints OpenAPI (/docs & /redoc)                │
│    - Exports standards (iCal .ics, JSON, ADE)          │
│    - Dashboard Web interactif (Vue grille & Chat)      │
└──────────────┬───────────────────────────▲─────────────┘
               │                           │
               ▼                           ▼
┌───────────────────────────┐  ┌─────────────────────────┐
│  ASSISTANT IA ALBERT      │  │  SOLVEUR GOOGLE OR-TOOLS│
│  (Etalab Sovereign LLM)   │  │  (CP-SAT Constraint)    │
│  - Function / Tool Calling│  │  - 0 conflit garanti    │
│  - Diagnostic des blocages│  │  - Respect strict du PN │
│  - Recommandation créneaux│  │  - FI vs FA (Alternance)│
└───────────────────────────┘  └─────────────────────────┘
```

---

## 🚀 Démarrage Rapide

### 1. Installation des dépendances Python
```bash
pip install -r requirements.txt
# ou directement :
pip install ortools openpyxl pydantic requests fastapi uvicorn pandas
```

### 2. Lancement du Serveur API & Interface Web
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
* **Tableau de bord Web interactif :** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Documentation OpenAPI / Swagger :** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Documentation Redoc :** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 🔐 Configuration & Sécurité
Le copilote IA requiert le jeton d'API Albert (Etalab). **Ne jamais le coder en dur.**
1. Copier `.env.example` vers `.env` et renseigner `ALBERT_API_TOKEN`.
2. Exposer la variable dans l'environnement du processus (le serveur lit `os.environ`).
   ```powershell
   $env:ALBERT_API_TOKEN = "votre_jeton"
   uvicorn api.main:app --host 127.0.0.1 --port 8000
   ```
3. ⚠️ **Recommandation forte** : un ancien jeton a été poussé par erreur dans l'historique git — révoquez-le et régénérez-en un sur la plateforme Etalab.

Autres variables : `ALBERT_API_URL`, `ALBERT_MODEL`, `CORS_ALLOW_ORIGINS` (défaut = localhost uniquement).

### 🐳 Déploiement Docker
L'image `emploistemps-tc` est construite via le `Dockerfile` et orchestrée par `docker-compose.yml`.

```powershell
# 1. (Optionnel) Fournir le jeton Albert via un .env : copier .env.example vers .env
#    puis renseigner ALBERT_API_TOKEN. Sans jeton, le copilote répond en mode protégé.

# 2. Construire l'image et démarrer le service
docker compose up -d --build

# 3. Vérifier
docker compose ps
docker logs -f emploistemps-tc
```

* **Interface Web :** http://127.0.0.1:8000
* **OpenAPI :** http://127.0.0.1:8000/docs

Le dossier local `./data` est **monté** dans le conteneur (`/app/data`) : les modifications apportées par l'API (`schedule_result.json`, `constraints.json`) sont persistées sur l'hôte. Le port exposé se règle dans `docker-compose.yml` (`"8000:8000"`).

### 🔄 Synchronisation Hyperplanning (Université Le Havre)
Le planning peut être synchronisé **en direct** depuis Hyperplanning (PRONOTE Campus) via les liens iCal permanents des ressources.

Configurer les sources dans `data/hp_ical_sources.json` (nom + `idICal` de chaque ressource). Le `param` (encodé en hex) décrit les préférences d'export (`d=[1..62]&fh=1&f=11000`) et est commun à toutes les ressources.

```powershell
# Télécharger les iCal (ici les 3 promos BUT TC) puis les ingérer dans le planning
python scripts/hp_sync.py --sources BUT1,BUT2,BUT3 --import

# Ou tout synchroniser/ingérer
python scripts/hp_sync.py --import
```

Le flux : `Hyperplanning /Telechargements/ical/<res>.ics?idICal=...` → `ical/*.ics` → `data/import_ical_schedule.py` → `data/schedule_result.json` (6 créneaux/jour, fuseau Europe/Paris).

Pour trouver les `idICal` d'autres ressources (enseignants, salles, groupes), utiliser `scripts/hp_explore.py` qui explore le portail connecté (identifiants CAS depuis `.env`) afin de capturer les liens iCal.

### ✅ Tests
```powershell
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

### ⚙️ Pilotage par API
Le conteneur est **entièrement pilotable par l'API** (déclaration iCal, synchro, contraintes, solveur, textes) :
- `POST /api/v1/admin/ical-sources` (déclarer les sources)
- `POST /api/v1/admin/ical-sync` (+ `GET /status`)
- `POST /api/v1/admin/constraints`, `teacher-services`, `rooms`, `teacher/unavailability`, …
- `GET /api/v1/schedule?teacher=&group_id=&room=` (EDT filtré)
- `GET /api/v1/schedule/suggest-move` / `suggest-room` (propositions)
- `POST /api/v1/admin/generate-text` (`kind`: move | room | teacher | defer → texte de demande)
- `POST /api/v1/solver/generate` (CP-SAT), `GET /api/v1/export/ical`

### 🔌 Intégration SkilLHub (sibutv3)
Voir [docs/integration_sibutv3.md](docs/integration_sibutv3.md) : ajouter `emploistemps` comme
service `edt` dans le docker-compose de SkilLHub (accès interne `http://edt:8000`), mapper
l'utilisateur authentifié (enseignant `full_name` / étudiant `group_id`) puis appeler l'API
ci-dessus ; rôles (ADMIN/EDT_MANAGER, PROFESSOR, STUDENT) pour limiter les accès.

---

## 🐹 Intégration Go (Golang SDK)

Le module Go est situé dans [`sdk/go`](file:///c:/Users/estebe/Documents/emloistemps/sdk/go) (`github.com/estebe2000/emploistemps/sdk/go`).

### Exemple d'utilisation dans une application Go :
```go
package main

import (
	"context"
	"fmt"
	"log"
	"time"

	emploistemps "github.com/estebe2000/emploistemps/sdk/go"
)

func main() {
	// 1. Initialiser le client Go
	client := emploistemps.NewClient("http://localhost:8000")
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	// 2. Déclencher la résolution CP-SAT
	schedule, err := client.GenerateSchedule(ctx, emploistemps.GenerateRequest{
		Semester:         "S1",
		Week:             1,
		TimeLimitSeconds: 15,
	})
	if err != nil {
		log.Fatalf("Erreur génération : %v", err)
	}
	fmt.Printf("Planning résolu avec statut : %s en %.2fs\n", schedule.Status, schedule.SolveTimeSec)

	// 3. Rechercher des créneaux libres pour un groupe et un prof
	freeSlots, _ := client.FindFreeSlots(ctx, "Thierry Tabellion", "BUT1_TD1")
	fmt.Printf("%d créneaux libres trouvés\n", len(freeSlots))

	// 4. Interagir en langage naturel avec l'Assistant IA
	answer, _ := client.AskAI(ctx, "Trouve un créneau de rattrapage de 2h pour M. Cardinale avec le TD2")
	fmt.Println("Réponse IA :", answer)
}
```

---

## 📡 Spécification des Principaux Endpoints REST

| Méthode | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Statut du microservice et des moteurs (OR-Tools, Albert). |
| `GET` | `/api/v1/dataset` | Données consolidées (Enseignants, Salles, PN, Cohortes). |
| `POST` | `/api/v1/solver/generate` | Génère un planning optimisé à 0 conflit via CP-SAT. |
| `GET` | `/api/v1/schedule` | Récupère l'EDT filtré par groupe, enseignant ou salle. |
| `POST` | `/api/v1/schedule/move` | Déplace un cours vers un autre créneau avec vérification. |
| `POST` | `/api/v1/schedule/verify-conflict` | Teste si un déplacement provoque un conflit (salle/prof/étudiant). |
| `GET` | `/api/v1/schedule/free-slots` | Recherche les créneaux libres communs prof / groupe. |
| `POST` | `/api/v1/ai/chat` | Envoie une instruction en langage naturel à l'IA avec outillage automatique. |
| `GET` | `/api/v1/export/ical` | Exporte le planning au format standard `.ics` (Outlook / Google Agenda). |

---

## 📂 Structure du Répertoire

* `api/` : Serveur REST FastAPI, middlewares et routes OpenAPI.
* `solver/` : Modélisation mathématique et solveur CP-SAT (`timetable_cp_sat.py`).
* `assistant/` : Copilote IA avec Tool Calling Albert API / Ollama (`copilot.py`).
* `data/` : Référentiel national PN, données Excel enseignants et scripts d'extraction.
* `sdk/go/` : Module Go officiel pour intégrer le moteur dans un projet parent.
* `web/` : Interface tableau de bord dynamique et responsive.