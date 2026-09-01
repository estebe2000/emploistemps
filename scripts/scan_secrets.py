#!/usr/bin/env python3
"""Script de détection de secrets (garde-fou anti-fuite).

Balayage des fichiers sensibles et des patterns de "vrais" secrets :
  - tokens JWT / clés (sk-eyJ..., Bearer, jetons hexalongs Alice/Hyperplanning)
  - mots de passe en dur non-placeholder (hors fichiers d'exemples officiels)
  - fichiers .env qui auraient pu être ajoutés par erreur

Usage :
    python scripts/scan_secrets.py [chemin...]   # scanne les chemins donnés (par défaut .)
Retourne 0 si aucun secret détecté, 1 sinon.
"""

import os
import re
import sys

# Compatibilité console (cp1252 sur Windows) : ne jamais planter sur un émoji/unicode.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Chemins / extensions systématiquement hors-scope (données, binaires, historiques externes)
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "node_modules", "memory-bank"}
SKIP_EXT = {".jar", ".class", ".exe", ".dll", ".lnk", ".png", ".jpg", ".jpeg", ".gif", ".pyc", ".ics"}

# Fichiers « modèles » autorisés (placeholders vides, jamais de valeur réelle).
KNOWN_SAFE = {"SoapClientPHP.php", ".env.example", ".env.dist", ".env.sample", "docker-compose.yml"}

# Placeholder explicite de substitution utilisé lors de la purge d'historique (option B).
# Ce n'est PAS un vrai secret ; on l'autorise uniquement sous cette forme exacte.
PLACEHOLDER_SUBSTITUTION = "sk-RETIRE_SECRET_ALBERT"

# Fragments présents dans une ligne suspectée qui indiquent un *accès* à une variable
# (et non une valeur en dur) → on ignore le hit.
CODE_ACCESS = (
    "os.environ", "environ.get", "os.getenv", "getenv(", "environ[",
    "Console.", "ReadLine", "readline(", "args[", "input(", "read(",
    "$env:", "${", "votre", "your_", "<enter>", ".service(", "@class",
)

# Patterns de "vrais" secrets (à haut signal) :
SECRET_PATTERNS = [
    # Jeton API / JWT (sk- + base64url jwt, ou eyJ...)
    re.compile(r"\bsk-[A-Za-z0-9._-]{20,}", re.I),
    re.compile(r"\beyJ[A-Za-z0-9_-]{30,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    # Jeton Hyperplanning mobile (hex très long) — ex. rqcode-5545
    re.compile(r"\b[0-9A-Fa-f]{64,}\b"),
    # Bearer avec valeur
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{16,}", re.I),
    # Mot de passe / clé en dur comme littéral (valeur non-vide)
    re.compile(r"(password|passwd|pwd|motdepasse|mot_de_passe|mdp|secret|apikey|api_key|token)\s*[=:]\s*(?:\"[^\"]{3,}\"|'[^']{3,}'|[A-Za-z0-9_./+=-]{8,})", re.I),
    # Fichier .env glissé (contient ligne var=valeur sensible non-vide)
    re.compile(r"^(hp_token|cas_password|albert_api_token|hp_password|sw_login|sw_pass)\s*=\s*\S+", re.I | re.M),
]


def _is_code_access(line: str) -> bool:
    return any(tok in line for tok in CODE_ACCESS)


def scan_file(path: str) -> list:
    """Renvoie la liste des (ligne, motif) suspects pour un fichier texte."""
    hits = []
    base = os.path.basename(path)
    if base in KNOWN_SAFE:
        return hits
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except OSError:
        return hits
    for lineno, raw in enumerate(lines, 1):
        line = raw.rstrip("\r\n")
        if _is_code_access(line):
            continue
        # Autoriser le placeholder de substitution exact (ex. mémoire/trace de purge).
        if PLACEHOLDER_SUBSTITUTION in line:
            continue
        for pat in SECRET_PATTERNS:
            if pat.search(line):
                hits.append((path, lineno, pat.pattern))
    return hits


def main(argv):
    roots = argv[1:] or ["."]
    found = []
    for root in roots:
        if os.path.isfile(root):
            found.extend(scan_file(root))
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in SKIP_EXT:
                    continue
                fp = os.path.join(dirpath, fn)
                found.extend(scan_file(fp))
    if found:
        print("[WARN] SECRETS / VALEURS SENSIBLES DETECTES (commit refuse) :")
        for path, line, pat in found:
            print(f"   - {path}:{line}  motif={pat}")
        print("\n-> Verifiez ces fichiers. Si c'est un vrai secret, deplacez-le dans .env (gitignore) et neutralisez la valeur en dur.")
        return 1
    print("[OK] Aucun secret detecte dans le perimetre valide.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))