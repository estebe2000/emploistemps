# Test — Règles HETD (extract_dataset.calculate_hetd)
# Règlement : 1h CM = 1.5h TD ; 1h TD = 1.0h TD ; 4h TP = 3h TD (ratio 0.75).

from data.extract_dataset import calculate_hetd


def test_hetd_nominal():
    """Cas attendu : mix CM/TD/TP standard."""
    # 2h CM (3) + 2h TD (2) + 2h TP (1.5) = 6.5
    assert calculate_hetd(2, 2, 2) == 6.5


def test_hetd_quatre_heures_tp_equivalent_trois_td():
    """Cas attendu : 4h TP doivent équivaloir à 3h TD."""
    assert calculate_hetd(0, 0, 4) == 3.0


def test_hetd_zero():
    """Cas limite : aucun volume -> 0."""
    assert calculate_hetd(0, 0, 0) == 0.0


def test_hetd_cm_seul():
    """Cas limite : CM seul, ratio 1.5 appliqué."""
    assert calculate_hetd(10, 0, 0) == 15.0


def test_hetd_tp_converti_en_float():
    """Cas d'arrondi : volumes fractionnaires conservés en float arrondi 2."""
    assert calculate_hetd(1, 1, 1) == 3.25