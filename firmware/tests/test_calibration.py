from deck.calibration import CalibrationWizard, apply, default_curve


def test_default_curve_is_identity():
    for level in (0.0, 0.1, 0.25, 0.6, 1.0):
        assert apply(level, default_curve()) == level


def test_interpolates_between_points():
    curve = [0.0, 0.2, 0.5, 0.8, 1.0]
    assert apply(0.25, curve) == 0.2
    assert abs(apply(0.125, curve) - 0.1) < 1e-9
    assert abs(apply(0.875, curve) - 0.9) < 1e-9


def test_clamps_level_and_passes_through_bad_curves():
    assert apply(1.5, default_curve()) == 1.0
    assert apply(-1.0, default_curve()) == 0.0
    assert apply(0.4, None) == 0.4
    assert apply(0.4, [0.0, 1.0]) == 0.4
    assert apply(0.4, ["a", 0, 0, 0, 0]) == 0.4


def _to_points(wizard):
    wizard.push()  # pick -> trimpot
    wizard.push()  # trimpot -> point 0


def test_wizard_nudge_never_crosses_neighbours():
    wizard = CalibrationWizard()
    wizard.start({})
    _to_points(wizard)
    wizard.push()  # point 1, starts at 0.25
    for _ in range(200):
        wizard.rotate(1)
    assert wizard.curves["CONTEXT"][1] == 0.5  # stopped at point 2
    for _ in range(200):
        wizard.rotate(-1)
    assert wizard.curves["CONTEXT"][1] == 0.0


def test_wizard_drives_trimpot_at_full_scale_then_points():
    wizard = CalibrationWizard()
    wizard.start({})
    assert wizard.drive() == 0.0
    wizard.push()
    assert wizard.drive() == 1.0
    wizard.push()
    assert wizard.drive() == 0.0
    wizard.push()
    assert wizard.drive() == 0.25


def test_wizard_finishes_after_last_point_and_keeps_other_meter():
    saved = {"FIVE_HOUR": [0.0, 0.3, 0.5, 0.7, 1.0]}
    wizard = CalibrationWizard()
    wizard.start(saved)
    _to_points(wizard)
    for _ in range(5):
        wizard.push()
    assert wizard.step == "done" and not wizard.finished
    wizard.push()
    assert wizard.finished
    assert wizard.curves["FIVE_HOUR"] == saved["FIVE_HOUR"]
    assert wizard.curves["FIVE_HOUR"] is not saved["FIVE_HOUR"]


def test_wizard_rejects_malformed_saved_curve():
    wizard = CalibrationWizard()
    wizard.start({"CONTEXT": [1, 2]})
    assert wizard.curves["CONTEXT"] == default_curve()
