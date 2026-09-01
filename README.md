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