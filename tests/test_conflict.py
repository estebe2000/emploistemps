# Test — Logique de conflits & créneaux libres (TimetableCopilot)
# Utilise des fixtures isolées (object.__new__) pour ne pas dépendre des gros fichiers
# data/schedule_result.json et data/dataset_tc.json.

from assistant.copilot import TimetableCopilot


def _make_copilot():
    cp = object.__new__(TimetableCopilot)
    cp.dataset = {
        "calendar_config": {
            "days": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"],
            "daily_slots": [
                {"id": 0, "time": "08:00 - 09:30"},
                {"id": 1, "time": "09:45 - 11:15"},
            ],
        },
        "rooms": [
            {"id": "R1", "name": "Salle 1"},
            {"id": "R2", "name": "Salle 2"},
        ],
    }
    cp.schedule = {"events": [
        {"lesson_id": "A", "teacher_name": "Prof A", "group_id": "TD1",
         "room_id": "R1", "room_name": "Salle 1",
         "resource_code": "R1.01", "event_type": "CM",
         "day": "Lundi", "day_idx": 0, "slot_idx": 0},
        {"lesson_id": "B", "teacher_name": "Prof B", "group_id": "TD2",
         "room_id": "R2", "room_name": "Salle 2",
         "resource_code": "R1.02", "event_type": "TD",
         "day": "Lundi", "day_idx": 0, "slot_idx": 1},
        {"lesson_id": "C", "teacher_name": "Prof A", "group_id": "TD3",
         "room_id": "R2", "room_name": "Salle 2",
         "resource_code": "R1.03", "event_type": "TD",
         "day": "Lundi", "day_idx": 0, "slot_idx": 1},
    ]}
    return cp


def test_deplacement_sans_conflit():
    """Cas attendu : déplacement vers un créneau libre autorisé."""
    cp = _make_copilot()
    res = cp.verifier_conflit_deplacement("A", "Mardi", 0)
    assert res["conflit"] is False
    assert res.get("autorise", True) is True


def test_deplacement_conflit_enseignant():
    """Cas d'échec : prof déjà occupé sur le créneau cible (cours C)."""
    cp = _make_copilot()
    res = cp.verifier_conflit_deplacement("A", "Lundi", 1)
    assert res["conflit"] is True
    assert any("enseignant" in r.lower() for r in res["raisons"])


def test_deplacement_vers_salle_occupee():
    """Cas d'échec : conflit de salle sur le créneau cible."""
    cp = _make_copilot()
    # « A » déplacé Lundi créneau 1 dans la salle R2 (salle déjà occupée par B et C)
    res = cp.verifier_conflit_deplacement("A", "Lundi", 1, "R2")
    assert res["conflit"] is True
    assert any("salle" in r.lower() for r in res["raisons"])


def test_lesson_introuvable():
    """Cas limite : lesson_id inexistant -> conflit signalé."""
    cp = _make_copilot()
    res = cp.verifier_conflit_deplacement("ZZZ", "Mardi", 0)
    assert res["conflit"] is True
    assert "introuvable" in res["raisons"][0]


def test_creneaux_libres():
    """Cas attendu : les créneaux où le prof ET le groupe sont occupés sont exclus."""
    cp = _make_copilot()
    slots = cp.trouver_creneaux_libres("Prof B", "TD2")
    # Prof B & TD2 occupés uniquement Lundi créneau 1 => ce créneau ne doit pas apparaître.
    assert slots, "au moins un créneau libre attendu"
    assert all(s["slot_idx"] != 1 or s["jour"] != "Lundi" for s in slots)