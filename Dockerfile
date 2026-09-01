# Syntaxe de build : python 3.12 minimal, optimisé pour OR-Tools CP-SAT.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# libgomp1 : dépendance runtime requise par OR-Tools (OpenMP) sur les images slim.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# D'abord les dépendances (layer cache optimisé lors des reconstructions).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Puis le code source et les données.
COPY . .

# Port de l'API FastAPI.
EXPOSE 8000

# Lance le serveur. Le jeton Albert est fourni via ALBERT_API_TOKEN (env) au besoin.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]