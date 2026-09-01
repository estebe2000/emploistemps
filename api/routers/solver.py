"""
Routes du solveur CP-SAT (génération d'emplois du temps optimisés).
"""
from fastapi import APIRouter, HTTPException

from ..schemas import GenerateScheduleRequest
from ..storage import DATASET_PATH

router = APIRouter(prefix="/api/v1/solver", tags=["Solveur CP-SAT"])


@router.post("/generate")
def generate_schedule(req: GenerateScheduleRequest):
    """
    Lance le solveur d'optimisation CP-SAT (Google OR-Tools) pour générer un emploi du temps à 0 conflit.
    """
    try:
        from solver.timetable_cp_sat import TimetableSolver
        solver = TimetableSolver(DATASET_PATH)
        result = solver.solve_weekly_pattern(
            target_week=req.week,
            semester=req.semester,
            time_limit_seconds=req.time_limit_seconds
        )
        if not result:
            raise HTTPException(status_code=422, detail="Aucun emploi du temps valide trouvé sous les contraintes données.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))