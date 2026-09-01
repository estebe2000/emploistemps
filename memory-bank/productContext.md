# Product Context

## Pourquoi ce projet existe
L'IUT TC doit produire chaque semaine un emploi du temps valide (0 conflit salle/prof/étudiant), respectant le Programme National (PN) et les services HETD officiels. Ce travail est devenu complexe avec 3 promos (BUT 1/2/3), des sous-groupes TD/TP, des parcours (BDMRC, MDEE, MMPV), l'alternance FI/FA et des fermetures (Jeudi PM, Samedi PM).

## Problèmes résolus
1. **Blocage manuel** : la modélisation CP-SAT automatise la pose des séances.
2. **Conflits** : garantie métier de non-superposition (salle, enseignant, groupe).
3. **Replanification pédagogique** : copilote IA (Albert/Etalab) + outils de vérification/déplacement.
4. **Services HETD** : bilan des équivalents TD pour piloter les charges enseignants.

## Objectifs UX
- **Responsable pédagogique** : grille interactive, actions clic-droit (déplacer, annuler, changer salle/prof, différer, convertir en éval), outil IA.
- **Intégrateur** : API REST OpenAPI `/docs` + SDK Go.
- **Intervenant / secrétariat** : export iCal pour Google Agenda / Outlook, filtres par groupe/prof/salle.

## Workflow nominal
1. `data/extract_dataset.py` → construit `dataset_tc.json` depuis le PN + Excel pilotage.
2. `data/import_ical_schedule.py` → importe le planning réel (`.ics`) dans `schedule_result.json` (6 créneaux/jour).
3. `/api/v1/solver/generate` (CP-SAT) → génère un planning à 0 conflit (4 créneaux/jour).
4. `/api/v1/schedule/*` et `/api/v1/ai/chat` → consultation et ajustement.