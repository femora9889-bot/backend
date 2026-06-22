import pytest

from app.models.product import SizeGuide
from app.models.user import BodyShape, UserMeasurements
from app.services.fit_service import calculate_fit, classify_torso, detect_body_shape


def make_measurements(**kwargs) -> UserMeasurements:
    defaults = dict(
        id="m1", user_id="u1",
        height_cm=165, weight_kg=60,
        bust_cm=88, waist_cm=70, hips_cm=94,
    )
    defaults.update(kwargs)
    m = UserMeasurements()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


def make_guides(sizes: dict) -> list[SizeGuide]:
    guides = []
    for label, dims in sizes.items():
        g = SizeGuide()
        g.size_label = label
        g.bust_cm = dims.get("bust")
        g.waist_cm = dims.get("waist")
        g.hips_cm = dims.get("hips")
        g.length_cm = dims.get("length")
        guides.append(g)
    return guides


SIZE_CHART = {
    "S":  {"bust": 84, "waist": 66, "hips": 90},
    "M":  {"bust": 88, "waist": 70, "hips": 94},
    "L":  {"bust": 92, "waist": 74, "hips": 98},
    "XL": {"bust": 96, "waist": 78, "hips": 102},
}


def test_perfect_fit():
    m = make_measurements(bust_cm=88, waist_cm=70, hips_cm=94)
    guides = make_guides(SIZE_CHART)
    result = calculate_fit(m, guides, "M")
    assert result.score == 100
    assert result.warning is None


def test_wrong_size_triggers_warning():
    m = make_measurements(bust_cm=88, waist_cm=70, hips_cm=94)
    guides = make_guides(SIZE_CHART)
    result = calculate_fit(m, guides, "XL")
    assert result.score < 75
    assert result.warning is not None
    assert result.recommended_size == "M"


def test_recommends_correct_size():
    m = make_measurements(bust_cm=92, waist_cm=74, hips_cm=98)
    guides = make_guides(SIZE_CHART)
    result = calculate_fit(m, guides, "S")
    assert result.recommended_size == "L"


def test_no_size_guides_returns_zero():
    m = make_measurements()
    result = calculate_fit(m, [], "M")
    assert result.score == 0.0


def test_size_not_in_chart():
    m = make_measurements()
    guides = make_guides(SIZE_CHART)
    result = calculate_fit(m, guides, "XXS")
    assert result.score == 0.0


def test_no_measurements_details_returns_default():
    m = make_measurements(bust_cm=None, waist_cm=None, hips_cm=None)
    guides = make_guides(SIZE_CHART)
    result = calculate_fit(m, guides, "M")
    assert result.score == 0.75 * 100 or "لا توجد" in result.assessment


def test_borderline_fit():
    m = make_measurements(bust_cm=90, waist_cm=70, hips_cm=94)
    guides = make_guides(SIZE_CHART)
    result = calculate_fit(m, guides, "M")
    assert 50 <= result.score <= 100


# --- detect_body_shape tests ---

def test_detect_hourglass():
    profile = detect_body_shape(bust=88, waist=68, hips=90)
    assert profile.primary == BodyShape.hourglass


def test_detect_pear():
    profile = detect_body_shape(bust=84, waist=68, hips=96)
    assert profile.primary == BodyShape.pear


def test_detect_inverted_triangle():
    profile = detect_body_shape(bust=96, waist=72, hips=88)
    assert profile.primary == BodyShape.inverted_triangle


def test_detect_apple():
    profile = detect_body_shape(bust=90, waist=86, hips=92)
    assert profile.primary == BodyShape.apple


def test_detect_rectangle():
    profile = detect_body_shape(bust=88, waist=82, hips=90)
    assert profile.primary == BodyShape.rectangle


def test_blend_has_secondary():
    # Borderline hourglass-pear: hips slightly bigger than bust, waist defined
    profile = detect_body_shape(bust=86, waist=68, hips=92)
    assert profile.secondary is not None
    assert profile.primary in (BodyShape.hourglass, BodyShape.pear)
    assert profile.secondary in (BodyShape.hourglass, BodyShape.pear)


def test_pure_shape_has_no_secondary():
    # Classic hourglass — clear separation
    profile = detect_body_shape(bust=92, waist=68, hips=92)
    assert profile.secondary is None


def test_blend_description_mentions_both():
    profile = detect_body_shape(bust=86, waist=68, hips=92)
    if profile.secondary:
        assert profile.primary.value in profile.description
        assert profile.secondary.value in profile.description


# --- classify_torso tests ---

def test_short_torso():
    torso_type, desc = classify_torso(torso_length_cm=38, height_cm=170)
    assert torso_type == "short"
    assert "high" in desc.lower()


def test_long_torso():
    torso_type, desc = classify_torso(torso_length_cm=50, height_cm=168)
    assert torso_type == "long"
    assert "lower" in desc.lower()


def test_average_torso():
    torso_type, _ = classify_torso(torso_length_cm=43, height_cm=165)
    assert torso_type == "average"


def test_torso_ratio_boundary():
    # ratio = 40.8/170 = 0.24 → exactly average
    torso_type, _ = classify_torso(torso_length_cm=40.8, height_cm=170)
    assert torso_type == "average"
