"""
Synchronisation des emplois du temps depuis Hyperplanning (Université Le Havre).

Télécharge les flux iCal permanent des ressources configurées (voir data/hp_ical_sources.json),
les enregistre dans ical/ puis les ingère dans schedule_result.json via import_ical_schedule.

Les liens iCal HP sont des "liens permanents" de synchro agenda, accessibles sans session :
    https://hplanning.univ-lehavre.fr/Telechargements/ical/<file>.ics?idICal=<id>&param=<param>

Usage :
    python scripts/hp_sync.py [--sources BUT1,BUT2,BUT3] [--out ical] [--import]
Identifiants/serveur : lus depuis data.hyperplanning_client (HP_BASE_URL) via .env.
"""

import os
import sys
import json
import argparse
import datetime
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.hyperplanning_client import HP_BASE_URL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_PATH = os.path.join(ROOT, "data", "hp_ical_sources.json")
DEFAULT_ICAL_DIR = os.path.join(ROOT, "ical")

# Par défaut, l'URL de base est déduite de HP_BASE_URL (hplanning.univ-lehavre.fr)
def _base(url: str) -> str:
    return url.split('/mobile')[0].split('?')[0]


def load_sources() -> dict:
    with open(SOURCES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_url(cfg: dict, source: dict, base_url: str) -> str:
    version = cfg.get("version", "2022.0.5.0")
    param = cfg.get("param", "")
    file = source["file"]
    idical = source["idICal"]
    return (f"{base_url}/Telechargements/ical/{file}"
            f"?version={version}&idICal={idical}&param={param}")


def download_source(source: dict, cfg: dict, base_url: str, out_dir: str) -> str:
    url = build_url(cfg, source, base_url)
    resp = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    target = os.path.join(out_dir, source["file"])
    with open(target, "wb") as f:
        f.write(resp.content)
    return target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=None,
                    help="clés des sources à synchroniser (ex: BUT1,BUT2,BUT3). Défaut: toutes.")
    ap.add_argument("--out", default=DEFAULT_ICAL_DIR, help="dossier de sortie des .ics (défaut: ical/)")
    ap.add_argument("--import", dest="do_import", action="store_true",
                    help="ingère ensuite les .ics dans schedule_result.json")
    ap.add_argument("--base-url", default=None, help="URL du serveur HP (défaut: déduite du .env)")
    args = ap.parse_args()

    cfg = load_sources()
    base_url = (args.base_url or _base(HP_BASE_URL)).rstrip('/')
    keys = [k.strip() for k in args.sources.split(",")] if args.sources else None

    os.makedirs(args.out, exist_ok=True)
    downloaded = []
    for src in cfg["sources"]:
        if keys and src["key"] not in keys:
            continue
        try:
            target = download_source(src, cfg, base_url, args.out)
            size = os.path.getsize(target)
            downloaded.append((src["key"], target, size))
            print(f"✅ {src['key']} ({src['label']}) -> {os.path.basename(target)} ({size} octets)")
        except Exception as e:
            print(f"⚠️  {src['key']} ÉCHEC: {e}")

    if not downloaded:
        print("Aucun flux téléchargé.")
        return 1

    print(f"\n→ {len(downloaded)} iCal téléchargé(s) dans {args.out}")

    if args.do_import:
        print("\nIngestion dans schedule_result.json...")
        from data.import_ical_schedule import import_all_schedules
        result = import_all_schedules()
        print("Fin de l'ingestion.")

    # Note de dernière synchro
    meta = {"last_sync": datetime.datetime.now().isoformat(timespec="seconds"),
            "server": base_url, "sources": [k for k in keys] if keys else [s["key"] for s in cfg["sources"]]}
    meta_path = os.path.join(os.path.dirname(SOURCES_PATH), "hp_last_sync.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"→ dernière synchro enregistrée: {meta_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())