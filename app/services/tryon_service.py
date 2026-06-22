import asyncio
import io
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

import httpx
from gradio_client import Client, handle_file
from huggingface_hub import InferenceClient

from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.infrastructure.storage.cloudinary_client import upload_image
from app.models.user import UserMeasurements
from app.services.fit_service import classify_torso, detect_body_shape

_HF_TRYON_SPACE = "Kwai-Kolors/Kolors-Virtual-Try-On"

_executor = ThreadPoolExecutor(max_workers=2)


# ── Avatar generation via FLUX.1-dev (InferenceClient) ──────────────────────

def _build_avatar_prompt(m: UserMeasurements) -> str:
    skin = f"Skin tone: {m.skin_tone}." if m.skin_tone else ""
    hair = f"Hair color: {m.hair_color}." if m.hair_color else ""

    shape_note = ""
    if m.bust_cm and m.waist_cm and m.hips_cm:
        profile = detect_body_shape(m.bust_cm, m.waist_cm, m.hips_cm)
        shape_note = f"Body shape: {profile.description}."

    torso_note = ""
    if m.torso_length_cm and m.height_cm:
        _, torso_desc = classify_torso(m.torso_length_cm, m.height_cm)
        torso_note = f"Torso proportion: {torso_desc}."

    lines = [f"Height: {m.height_cm} cm", f"Weight: {m.weight_kg} kg"]
    for label, val in [
        ("Bust", m.bust_cm), ("Waist", m.waist_cm), ("Hips", m.hips_cm),
        ("Shoulder width", m.shoulder_cm), ("Thigh", m.thigh_cm),
    ]:
        if val:
            lines.append(f"{label}: {val} cm")

    prompt = (
        "A highly realistic full-body female avatar. "
        + ", ".join(lines) + ". "
        + shape_note + " " + torso_note + " " + skin + " " + hair
        + " Natural facial features resembling Syrian/Levant women. "
        "Uncovered hair. Modest casual clothing: long-sleeve shirt and jeans. "
        "No hijab or headscarf. Full-body view, neutral standing pose, "
        "studio lighting, plain background, photorealistic, highly detailed."
    )
    return " ".join(prompt.split())


def _sync_generate_avatar(prompt: str, hf_token: str) -> bytes:
    client = InferenceClient(provider="auto", api_key=hf_token)
    image = client.text_to_image(prompt, model="black-forest-labs/FLUX.1-dev")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


async def generate_avatar(measurements: UserMeasurements, user_id: str) -> str:
    if not settings.HF_TOKEN:
        raise BadRequestError("HF_TOKEN not configured")

    prompt = _build_avatar_prompt(measurements)

    loop = asyncio.get_event_loop()
    try:
        image_data = await loop.run_in_executor(
            _executor, _sync_generate_avatar, prompt, settings.HF_TOKEN
        )
    except Exception as e:
        raise BadRequestError(f"Avatar generation failed: {e}")

    return await upload_image(image_data, "tryon", public_id=f"avatar_{user_id}")


# ── Virtual Try-On via Kolors Space ─────────────────────────────────────────

def _sync_tryon(person_path: str, garment_path: str) -> bytes:
    client = Client(_HF_TRYON_SPACE, hf_token=settings.HF_TOKEN or None)
    result = client.predict(
        handle_file(person_path),
        handle_file(garment_path),
        api_name="/tryon",
    )
    result_path = result[0] if isinstance(result, (list, tuple)) else result
    with open(result_path, "rb") as f:
        return f.read()


async def _run_tryon(person_bytes: bytes, product_bytes: bytes) -> bytes:
    p_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    g_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    try:
        p_file.write(person_bytes)
        p_file.close()
        g_file.write(product_bytes)
        g_file.close()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, _sync_tryon, p_file.name, g_file.name
        )
    finally:
        os.unlink(p_file.name)
        os.unlink(g_file.name)


async def tryon_with_photo(user_photo: bytes, product_image_url: str, user_id: str) -> str:
    async with httpx.AsyncClient(timeout=30) as http:
        product_bytes = (await http.get(product_image_url)).content
    image_data = await _run_tryon(user_photo, product_bytes)
    return await upload_image(image_data, "tryon", public_id=f"tryon_{user_id}")


async def tryon_on_avatar(avatar_url: str, product_image_url: str, user_id: str) -> str:
    async with httpx.AsyncClient(timeout=30) as http:
        avatar_bytes = (await http.get(avatar_url)).content
        product_bytes = (await http.get(product_image_url)).content
    image_data = await _run_tryon(avatar_bytes, product_bytes)
    return await upload_image(image_data, "tryon", public_id=f"tryon_avatar_{user_id}")
