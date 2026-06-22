from dataclasses import dataclass

from app.models.product import SizeGuide
from app.models.user import BodyShape, UserMeasurements
from app.schemas.tryon import FitResult


SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

BLEND_THRESHOLD = 0.25  # secondary shape shows if its score >= primary * this ratio


@dataclass
class ShapeProfile:
    primary: BodyShape
    secondary: BodyShape | None
    description: str  # for avatar prompt


def _score_shapes(bust: float, waist: float, hips: float) -> dict[BodyShape, float]:
    b_w = max(0.0, bust - waist)
    h_w = max(0.0, hips - waist)
    b_h = abs(bust - hips)

    scores: dict[BodyShape, float] = {}

    # Hourglass: waist defined on both sides, bust ≈ hips
    scores[BodyShape.hourglass] = (
        min(b_w, h_w) * max(0.0, 1 - b_h / 12)
    )

    # Pear: hips significantly larger than bust
    scores[BodyShape.pear] = max(0.0, hips - bust) * min(1.0, h_w / 9)

    # Inverted triangle: bust significantly larger than hips
    scores[BodyShape.inverted_triangle] = max(0.0, bust - hips) * min(1.0, b_w / 9)

    # Apple: wide waist, little definition
    waist_ratio = waist / min(bust, hips)
    scores[BodyShape.apple] = max(0.0, (waist_ratio - 0.70) * 20)

    # Rectangle: balanced measurements, waist not very defined
    balance = max(0.0, 1 - b_h / 8)
    no_waist = max(0.0, 1 - min(b_w, h_w) / 9)
    scores[BodyShape.rectangle] = balance * no_waist * 8

    return scores


_SHAPE_NAMES_AR = {
    BodyShape.hourglass: "ساعة الرمل",
    BodyShape.pear: "الكمثرى",
    BodyShape.inverted_triangle: "المثلث المعكوس",
    BodyShape.apple: "التفاحة",
    BodyShape.rectangle: "المستطيل",
}


def classify_torso(torso_length_cm: float, height_cm: float) -> tuple[str, str]:
    """
    Returns (torso_type, prompt_description)
    torso_type: "short" | "average" | "long"
    """
    ratio = torso_length_cm / height_cm

    if ratio < 0.24:
        return (
            "short",
            "Has a short upper torso — the natural waistline sits noticeably high relative to overall height. "
            "The legs appear longer in proportion. This affects how waistbands, crop tops, and empire-waist "
            "dresses appear: they sit higher on the body than average.",
        )
    elif ratio > 0.28:
        return (
            "long",
            "Has a long upper torso — the natural waistline sits lower relative to overall height. "
            "The legs appear shorter in proportion. High-waisted styles may not hit at the natural waist.",
        )
    else:
        return (
            "average",
            "Has an average torso length with balanced upper-to-lower body proportions.",
        )


def detect_body_shape(bust: float, waist: float, hips: float) -> ShapeProfile:
    scores = _score_shapes(bust, waist, hips)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    primary, primary_score = ranked[0]
    secondary_shape, secondary_score = ranked[1]

    is_blend = primary_score > 0 and (secondary_score / primary_score) >= BLEND_THRESHOLD

    secondary = secondary_shape if is_blend else None

    if secondary:
        description = (
            f"Body shape is a blend of {primary.value} and {secondary.value}. "
            f"Primarily {_SHAPE_NAMES_AR[primary]} with tendencies toward {_SHAPE_NAMES_AR[secondary]}."
        )
    else:
        description = f"Body shape is {primary.value} ({_SHAPE_NAMES_AR[primary]})."

    return ShapeProfile(primary=primary, secondary=secondary, description=description)


def calculate_fit(measurements: UserMeasurements, size_guides: list[SizeGuide], selected_size: str) -> FitResult:
    if not size_guides or not measurements:
        return FitResult(score=0.0, assessment="لا تتوفر بيانات كافية للمقارنة")

    guides_map = {g.size_label.upper(): g for g in size_guides}
    selected = guides_map.get(selected_size.upper())

    if not selected:
        return FitResult(score=0.0, assessment="المقاس المحدد غير موجود في جدول المقاسات")

    scores = []
    if selected.bust_cm and measurements.bust_cm:
        diff = abs(selected.bust_cm - measurements.bust_cm)
        scores.append(max(0, 1 - diff / 10))
    if selected.waist_cm and measurements.waist_cm:
        diff = abs(selected.waist_cm - measurements.waist_cm)
        scores.append(max(0, 1 - diff / 10))
    if selected.hips_cm and measurements.hips_cm:
        diff = abs(selected.hips_cm - measurements.hips_cm)
        scores.append(max(0, 1 - diff / 10))

    if not scores:
        return FitResult(score=0.75, assessment="لا توجد قياسات تفصيلية للمقارنة الدقيقة")

    score = round(sum(scores) / len(scores), 2)

    recommended = _find_best_size(measurements, guides_map)
    warning = None

    if score < 0.5:
        warning = f"قد يكون هذا المقاس غير مناسب لقياساتك — المقاس المقترح هو {recommended}"
    elif score < 0.75:
        warning = f"المقاس المقترح لقياساتك هو {recommended}"

    if score >= 0.9:
        assessment = "مطابق تماماً لقياساتك ✓"
    elif score >= 0.75:
        assessment = "مناسب لقياساتك"
    elif score >= 0.5:
        assessment = "مقاس قريب — قد يحتاج تعديلاً بسيطاً"
    else:
        assessment = "المقاس غير مناسب لقياساتك"

    return FitResult(
        score=round(score * 100),
        assessment=assessment,
        recommended_size=recommended,
        warning=warning,
    )


def _find_best_size(measurements: UserMeasurements, guides_map: dict[str, SizeGuide]) -> str | None:
    best_size = None
    best_score = -1

    for size_label, guide in guides_map.items():
        scores = []
        if guide.bust_cm and measurements.bust_cm:
            scores.append(max(0, 1 - abs(guide.bust_cm - measurements.bust_cm) / 10))
        if guide.waist_cm and measurements.waist_cm:
            scores.append(max(0, 1 - abs(guide.waist_cm - measurements.waist_cm) / 10))
        if guide.hips_cm and measurements.hips_cm:
            scores.append(max(0, 1 - abs(guide.hips_cm - measurements.hips_cm) / 10))
        if scores:
            avg = sum(scores) / len(scores)
            if avg > best_score:
                best_score = avg
                best_size = size_label

    return best_size
