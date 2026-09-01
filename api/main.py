"""
FastAPI Backend Server for IUT TC Timetable Management, Solver & AI Assistant.
Assemble l'application, le CORS, les routers par domaine et sert l'interface web.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .storage import BASE_DIR
from .routers import admin, data, solver, schedule, ai

app = FastAPI(
    title="API Gestion Emplois du Temps & Assistant IA (Département TC)",
    description="Microservice d'optimisation d'emplois du temps (Google OR-Tools CP-SAT) et Assistant IA Souverain (Albert API)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS : origines restreintes, configurables via CORS_ALLOW_ORIGINS.
_CORS_ALLOW_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ALLOW_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Système"])
def health_check():
    return {
        "status": "healthy",
        "service": "emploistemps-api",
        "solver": "ortools-cp-sat",
        "ai_engine": "albert-etalab"
    }


# Routers métier
app.include_router(admin.router)
app.include_router(admin.router_root)
app.include_router(data.router)
app.include_router(solver.router)
app.include_router(schedule.router)
app.include_router(ai.router)

# Fichiers statiques de l'interface (CSS / JS extraits de web/index.html)
_web_dir = os.path.join(BASE_DIR, "web")
if os.path.isdir(_web_dir):
    app.mount("/css", StaticFiles(directory=os.path.join(_web_dir, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(_web_dir, "js")), name="js")


@app.get("/", response_class=HTMLResponse, tags=["Interface Web"])
def serve_dashboard():
    index_file = os.path.join(BASE_DIR, "web", "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Application Emplois du Temps TC</h1><p>Visitez <a href='/docs'>/docs</a> pour l'API OpenAPI.</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)