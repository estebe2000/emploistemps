# Project Brief — Emplois du Temps TC

## Objectif fondamental
Application et microservice d'optimisation d'emplois du temps pour le département **Techniques de Commercialisation (TC)** de l'IUT. Il combine :
- un **moteur déterministe** (Google OR-Tools CP-SAT) garantissant des plannings à 0 conflit ;
- un **Copilote IA Souverain** (API Albert / Etalab) outillé (function/tool calling) pour consulter, déplacer et réparer des cours en langage naturel.

Conçu comme un **sous-projet / microservice API-First**, intégrable dans une architecture plus large via REST OpenAPI et un **SDK Go** dédié.

## Périmètre
- Département TC — BUT 1/2/3, Formation Initiale (FI) et Alternance (FA).
- Respect du PN (Programme National) et des règles HETD (1h CM = 1.5h TD, 4h TP = 3h TD / ratio 0.75).

## Critères de succès
- Générer un planning sans conflit (salle / professeur / étudiant).
- Fournir une API REST documentée + interface web grille + export iCal.
- Intégrable par une application parente via le SDK Go.

## Indices de décision
- `projetsibut.txt` → dépôt parent Go : `https://github.com/estebe2000/sibutv3.git`