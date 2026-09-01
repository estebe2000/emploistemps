"""
Client de synchronisation Hyperplanning (PRONOTE Campus) — Université Le Havre Normandie.

Principe : le QR mobile (`mobile.enseignant`) fournit un jeton pré-authentifié + un login
qui permettent d'accéder au portail mobile SANS passer par le CAS (single sign-on).
Ce module explore et collecte les emplois du temps exposés par le portail mobile.

Les identifiants sont fournis via variables d'environnement (jamais codés en dur) :
    HP_BASE_URL  (défaut : https://hplanning.univ-lehavre.fr/mobile.enseignant)
    HP_TOKEN     (jeton mobile, ex. fourni par le QR rqcode-5545.png)
    HP_LOGIN     (login/identifiant de la ressource liée au jeton)
"""

import os
import re
import sys
from typing import Dict, List, Optional

import requests

# Chargement optionnel de .env (si python-dotenv est présent) pour les tests locaux.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

HP_BASE_URL = os.environ.get("HP_BASE_URL", "https://hplanning.univ-lehavre.fr/mobile.enseignant")
HP_TOKEN = os.environ.get("HP_TOKEN", "")
HP_LOGIN = os.environ.get("HP_LOGIN", "")
# Identifiants SSO CAN (Université Le Havre) — fournis via .env, jamais codés en dur.
CAS_BASE_URL = os.environ.get("CAS_BASE_URL", "https://cas.univ-lehavre.fr/cas")
CAS_USERNAME = os.environ.get("CAS_USERNAME", "")
CAS_PASSWORD = os.environ.get("CAS_PASSWORD", "")

# Session réutilisable, headers proches d'un navigateur mobile.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9",
}


class HyperplanningClient:
    """Client du portail mobile Hyperplanning utilisant le jeton pré-authentifié."""

    def __init__(self, base_url: str = HP_BASE_URL, token: str = HP_TOKEN, login: str = HP_LOGIN):
        self.base_url = base_url or HP_BASE_URL
        self.token = token or HP_TOKEN
        self.login = login or HP_LOGIN
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._root_url = base_url
        self.authenticated = False

    # --- Authentification ---

    def cas_authenticate(self, username: str = CAS_USERNAME, password: str = CAS_PASSWORD,
                         base_url: str = CAS_BASE_URL) -> bool:
        """
        Authentifie la session auprès du CAS (Apereo) de l'Université Le Havre,
        puis valide le ticket de service sur l'application Hyperplanning mobile.

        Returns:
            bool: True si la session est authentifiée.
        """
        if not (username and password):
            return False

        # Simule le parcours navigateur (iOS Safari) requis par le CAS.
        self.session.get(base_url, timeout=30)

        # Étape 1 : récupérer le formulaire de login + token d'éxécution (execution + lt)
        service = f"{self.base_url}"
        login_url = f"{base_url}/login"
        probe = self.session.get(login_url, params={"service": service}, timeout=30)
        html = probe.text

        # Extraction des champs cachés CAS (execution, lt, _eventId...)
        execution = re.search(r'name=["\']execution["\'][^>]*value=["\']([^"\']+)["\']', html)
        lt = re.search(r'name=["\']lt["\'][^>]*value=["\']([^"\']+)["\']', html)
        if not execution:
            return False

        data = {
            "username": username,
            "password": password,
            "execution": execution.group(1),
            "_eventId": "submit",
        }
        if lt:
            data["lt"] = lt.group(1)

        # Étape 2 : POST identifiants → redirige vers service avec ?ticket=ST-...
        resp = self.session.post(login_url, params={"service": service},
                                 data=data, allow_redirects=False,
                                 timeout=30)
        location = resp.headers.get("Location", "")
        # Si l'authentification a échoué, le CAS renvoie la page de login.
        if "ticket=" not in location and resp.status_code == 302 and "login" in location.lower():
            return False

        # Étape 3 : suivre la redirection s'il y a lieu, puis consommer le ticket
        if resp.status_code in (301, 302, 303):
            final = self.session.get(location, timeout=30)
        else:
            final = resp

        # La session a désormais le cookie de session HP.
        self.authenticated = "ticket=" in location or final.status_code == 200
        return self.authenticated

    # --- Accès de base ---

    def _auth_params(self) -> Dict[str, str]:
        """Retourne les paramètres d'authentification du portail mobile."""
        if self.token and self.login:
            return {"jeton": self.token, "login": self.login}
        if self.token:
            return {"jeton": self.token}
        return {}

    def get(self, url: str, params: Optional[Dict] = None, timeout: int = 30):
        """GET avec les paramètres d'authentification par défaut."""
        p = dict(params) if params else {}
        p.update(self._auth_params())
        return self.session.get(url, params=p, timeout=timeout)

    def fetch_root(self, timeout: int = 30) -> str:
        """Ouvre la racine du portail mobile et renvoie le HTML brut."""
        resp = self.get(self.base_url, timeout=timeout)
        resp.raise_for_status()
        return resp.text

    # --- Utilitaire ---

    def extract_links(self, html: str) -> List[str]:
        """Extrait les liens <a href> uniques du HTML."""
        m = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        out = []
        for href in m:
            href = href.strip()
            if href and href not in out and not href.startswith(('javascript:', 'mailto:', "#")):
                out.append(href)
        return out


if __name__ == "__main__":
    cli = HyperplanningClient()

    # 1) Tenter l'authentification CAS complète si des identifiants sont fournis.
    if cli.token:
        print(f"🌐 Portail mobile : {cli.base_url}")
        try:
            html = cli.fetch_root()
            if "hyperplanning" in html.lower() or "emploi" in html.lower() or 'cours' in html.lower():
                print(f"✅ Accès direct avec le jeton (HTML {len(html)} octets).")
                print("\n--- Liens du portail ---")
                for link in cli.extract_links(html):
                    print(" ", link)
            else:
                print(f"ℹ️  Le jeton seul renvoie une page de session (HTML {len(html)} octets). Si c'est le CAS, CAS_USERNAME/PASSWORD sont requis.")
        except Exception as e:
            print(f"⚠️  Jeton seul : {e}")

    if CAS_USERNAME and CAS_PASSWORD and not cli.authenticated:
        print("\n🔑 Authentification CAS...")
        ok = cli.cas_authenticate()
        print(f"✅ Authentifié CAS : {ok}")
        if ok:
            html = cli.fetch_root()
            print(f"\n--- Portail mobile après CAS ({len(html)} octets) ---")
            for link in cli.extract_links(html):
                print(" ", link)

    if not cli.token and not (CAS_USERNAME and CAS_PASSWORD):
        print("⚠️  Ni HP_TOKEN ni identifiants CAS fournis. Renseignez .env (HP_TOKEN/HP_LOGIN ou CAS_USERNAME/CAS_PASSWORD).")