package main

import (
	"context"
	"fmt"
	"log"
	"time"

	emploistemps "github.com/estebe2000/emploistemps/sdk/go"
)

func main() {
	fmt.Println("🚀 Initialisation du client Go Emplois du Temps...")

	// 1. Instancier le client Go
	client := emploistemps.NewClient("http://localhost:8000")
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	// 2. Health check
	health, err := client.Health(ctx)
	if err != nil {
		log.Fatalf("Erreur health check : %v", err)
	}
	fmt.Printf("✅ Statut de l'API : %v\n", health)

	// 3. Génération d'un emploi du temps optimisé via le solveur CP-SAT
	fmt.Println("\n🧩 Appel du solveur CP-SAT (Semestre 1, Semaine 1)...")
	sched, err := client.GenerateSchedule(ctx, emploistemps.GenerateRequest{
		Semester:         "S1",
		Week:             1,
		TimeLimitSeconds: 15,
	})
	if err != nil {
		log.Fatalf("Erreur génération CP-SAT : %v", err)
	}
	fmt.Printf("🎉 Planning généré avec statut : %s en %.2fs (%d événements planifiés)\n",
		sched.Status, sched.SolveTimeSec, sched.TotalEvents)

	// 4. Recherche de créneaux libres
	fmt.Println("\n🔍 Recherche de créneaux de rattrapage disponibles...")
	freeSlots, err := client.FindFreeSlots(ctx, "Thierry Tabellion", "BUT1_TD1")
	if err != nil {
		log.Printf("Erreur recherche créneaux : %v", err)
	} else {
		fmt.Printf("📅 %d créneaux libres trouvés pour Thierry Tabellion & BUT1_TD1 :\n", len(freeSlots))
		for _, s := range freeSlots {
			fmt.Printf("   • %s à %s\n", s.Jour, s.Heure)
		}
	}

	// 5. Interaction avec l'Assistant IA (Albert API)
	fmt.Println("\n🤖 Envoi d'une instruction en langage naturel à l'IA...")
	aiResponse, err := client.AskAI(ctx, "Peux-tu me résumer les cours prévus le lundi pour la promo BUT 1 ?")
	if err != nil {
		log.Printf("Erreur appel IA : %v", err)
	} else {
		fmt.Printf("💬 Réponse IA :\n%s\n", aiResponse)
	}
}
