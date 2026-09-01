# Test de la synchronisation Hyperplanning (construction d'URL + config des sources).

import json
import os
from scripts.hp_sync import load_sources, build_url

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_sources_config_exist():
    """La config des sources iCal est lisible et contient les 3 promos TC."""
    cfg = load_sources()
    assert cfg["param"]
    keys = [s["key"] for s in cfg["sources"]]
    assert "BUT1" in keys and "BUT2" in keys and "BUT3" in keys


def test_url_construction():
    """L'URL iCal est construite selon le schéma officiel (chemin + idICal + param)."""
    cfg = load_sources()
    src = next(s for s in cfg["sources"] if s["key"] == "BUT1")
    url = build_url(cfg, src, "https://hplanning.univ-lehavre.fr")
    assert url.startswith("https://hplanning.univ-lehavre.fr/Telechargements/ical/")
    assert src["file"] in url
    assert "idICal=" in url and src["idICal"] in url
    assert "param=" in url and cfg["param"] in url


def test_url_param_is_stable_hex():
    """Le param est un hexadécimal (encodage des préférences d'export)."""
    cfg = load_sources()
    param = cfg["param"]
    # Vérifier que c'est bien de l'hexadécimal, et décoder 'd=[1..62]&fh=1&f=...'
    assert all(c in "0123456789abcdefABCDEF" for c in param)
    import binascii
    dec = binascii.unhexlify(param).decode("ascii")
    assert "d=[" in dec and "&fh=" in dec and "&f=" in dec