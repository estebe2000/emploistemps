"""
Exploration headless de l'espace Hyperplanning enseignant (via Playwright + Edge).
Login CAS Université Le Havre puis capture des liens d'export iCal / navigation.

Usage :
    python scripts/hp_explore.py                # connexion, affiche les liens iCal visibles
    python scripts/hp_explore.py --dump html    # sauvegarde le HTML page par page
Identifiants : lues depuis data/hyperplanning_client (HP_* / CAS_* via .env).
"""

import os
import sys
import re
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.hyperplanning_client import CAS_BASE_URL, CAS_USERNAME, CAS_PASSWORD

HP_HOME = "https://hplanning.univ-lehavre.fr/"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", default=None, help="dossier où écrire les HTML dumpés")
    ap.add_argument("--headless", action="store_true", default=True)
    args = ap.parse_args()

    if not (CAS_USERNAME and CAS_PASSWORD):
        print("Identifiants CAS manquants (.env).")
        return 1

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()

        # 1) Page CAS
        login_url = f"{CAS_BASE_URL}/login"
        # Paramètre service = racine HP
        page.goto(login_url, wait_until="domcontentloaded")
        # le CAS peut pré-remplir ; remplissons champs username/password
        try:
            page.fill("input[name=username]", CAS_USERNAME)
            page.fill("input[name=password]", CAS_PASSWORD)
            page.click("input[name=submit], button[type=submit]")
        except Exception as e:
            print("form CAS:", e)
            page.screenshot(path="_cas_form.png")
        # attente redirection
        page.wait_for_load_state("networkidle", timeout=45000)
        print("URL après login:", page.url)

        # 2) Racine espace enseignant
        page.goto(HP_HOME, wait_until="networkidle", timeout=45000)
        time.sleep(1)
        title = page.title()
        print("TITRE:", title)
        print("URL:", page.url)

        if args.dump:
            os.makedirs(args.dump, exist_ok=True)
            open(os.path.join(args.dump, "hp_root.html"), "w", encoding="utf-8").write(page.content())

        # 3) Capturer tous les liens <a href> uniques
        links = page.eval_on_selector_all("a", "els => els.map(e => e.href)")
        uniq = sorted(set(l for l in links if l and "javascript" not in l and l.startswith("http")))
        print(f"\n=== {len(uniq)} liens externes uniques ===")
        for l in uniq[:60]:
            print(" ", l)

        # 4) Chercher les liens iCal (contiennent 'ical' ou 'param=')
        ical = [l for l in uniq if "ical" in l.lower() or ("param=" in l and l.startswith(HP_HOME))]
        print(f"\n=== {len(ical)} liens iCal/param ===")
        for l in ical[:30]:
            print(" ", l)

        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())