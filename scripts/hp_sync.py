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


def run_sync(sources_keys=None, out_dir=None, do_import=True, base_url=None) -> dict:
    """
    Exécute la synchronisation iCal Hyperplanning (téléchargement + import optionnel).

    Args:
        sources_keys (list, optional): clés des sources à synchroniser (toutes si None).
        out_dir (str, optional): dossier de sortie des .ics.
        do_import (bool): ingère ensuite dans schedule_result.json.
        base_url (str, optional): URL du serveur HP.

    Returns:
        dict: résultat (succès, message, sources, total_events).
    """
    cfg = load_sources()
    b = (base_url or _base(HP_BASE_URL)).rstrip('/')
    out = out_dir or DEFAULT_ICAL_DIR
    os.makedirs(out, exist_ok=True)
    keys = sources_keys if sources_keys is not None else None
    bset = set(keys) if keys else None

    # chemin vers le fichier de statut
    meta_path = os.path.join(os.path.dirname(SOURCES_PATH), "hp_last_sync.json")
    started_at = datetime.datetime.now().isoformat(timespec="seconds")

    def _write_status(payload):
        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # Marquage "en cours"
    _write_status({"status": "running", "running": True, "started_at": started_at, "server": b})

    downloaded = []
    errors = []
    for src in cfg["sources"]:
        if bset and src["key"] not in bset:
            continue
        try:
            target = download_source(src, cfg, b, out)
            size = os.path.getsize(target)
            downloaded.append({"key": src["key"], "file": src["file"], "size": size})
        except Exception as e:
            errors.append({"key": src.get("key"), "error": str(e)})

    if not downloaded:
        _write_status({"status": "error", "running": False, "started_at": started_at,
                       "finished_at": datetime.datetime.now().isoformat(timespec="seconds"),
                       "server": b, "message": "Aucun iCal téléchargé.", "errors": errors})
        return {"success": False, "message": "Aucun iCal téléchargé. Vérifiez les sources et l'accès réseau.", "errors": errors}

    total_events = None
    if do_import:
        from data.import_ical_schedule import import_all_schedules
        sched = import_all_schedules()
        total_events = sched.get("total_events") if isinstance(sched, dict) else None

    finished_at = datetime.datetime.now().isoformat(timespec="seconds")
    meta = {"status": "success", "running": False,
            "last_sync": finished_at,
            "started_at": started_at,
            "finished_at": finished_at,
            "server": b,
            "downloaded": len(downloaded),
            "total_events": total_events,
            "sources": [s["key"] for s in downloaded],
            "errors": errors}
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    return {
        "success": True,
        "last_sync": meta["last_sync"],
        "downloaded": downloaded,
        "imported": bool(do_import),
        "total_events": total_events,
        "errors": errors,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=None,
                    help="clés des sources à synchroniser (ex: BUT1,BUT2,BUT3). Défaut: toutes.")
    ap.add_argument("--out", default=DEFAULT_ICAL_DIR, help="dossier de sortie des .ics (défaut: ical/)")
    ap.add_argument("--import", dest="do_import", action="store_true",
                    help="ingère ensuite les .ics dans schedule_result.json")
    ap.add_argument("--base-url", default=None, help="URL du serveur HP (défaut: déduite du .env)")
    args = ap.parse_args()

    keys = [k.strip() for k in args.sources.split(",")] if args.sources else None
    result = run_sync(sources_keys=keys, out_dir=args.out, do_import=bool(args.do_import), base_url=args.base_url)

    if result.get("success"):
        for d in result["downloaded"]:
            print(f"✅ {d['key']} → {d['file']} ({d['size']} octets)")
        print(f"\n→ {len(result['downloaded'])} iCal téléchargé(s) dans {args.out}")
        if result.get("imported"):
            print(f"\n✅ Ingestion terminée : {result.get('total_events')} cours ingérés.")
        print(f"→ dernière synchro enregistrée : {result.get('last_sync')}")
        return 0
    else:
        print(f"⚠️  {result.get('message')}")
        for e in result.get("errors", []):
            print(f"  - {e.get('key')}: {e.get('error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())