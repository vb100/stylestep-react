from __future__ import annotations

import base64
import json
import logging
import uuid
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote_plus

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from .image_utils import ImageOptimizationError, optimize_image_to_jpeg
from .models import StylingRequest
from .openai_client import (
    OpenAIIntegrationError,
    request_json_repair,
    request_outfit_image,
    request_primary_json_output,
)
from .prompts import load_prompt_file, render_json_repair_prompt, render_outfit_image_prompt, render_user_prompt
from .schemas import has_schema_payload, try_validate_ai_json

logger = logging.getLogger("stylist")

GENERATED_OUTFIT_KEY = "safe"
OUTFIT_DISPLAY_ORDER = ("safe", "bold", "creative")
OUTFIT_OPTION_LABELS = {
    "safe": "1 variantas",
    "bold": "2 variantas",
    "creative": "3 variantas",
}
OUTFIT_VARIANT_LABELS = {
    "safe": "Ramus",
    "bold": "Ryškesnis",
    "creative": "Kūrybiškas",
}


class AIOutputValidationError(Exception):
    pass


def _preview_text(value: str, limit: int = 800) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit]}..."


def create_optimized_image(styling_request: StylingRequest) -> None:
    if not styling_request.image_original:
        raise ImageOptimizationError("No source image provided.")

    optimized_content = optimize_image_to_jpeg(styling_request.image_original)
    filename = f"{uuid.uuid4().hex}.jpg"
    styling_request.image_optimized.save(filename, optimized_content, save=False)


def _read_file_as_base64(field_file) -> str:
    payload = _read_field_file_bytes(field_file)
    return base64.b64encode(payload).decode("ascii")


def _read_field_file_bytes(field_file) -> bytes:
    field_file.open("rb")
    try:
        return field_file.read()
    finally:
        field_file.close()


def run_openai_styling_analysis(
    styling_request: StylingRequest,
) -> tuple[dict, str, dict | list | str | int | float | None]:
    if not styling_request.image_optimized:
        raise OpenAIIntegrationError("Optimized image is missing for AI analysis.")

    system_prompt = load_prompt_file("system_prompt.txt")
    user_prompt = render_user_prompt(
        season=styling_request.season.name,
        occasion=styling_request.occasion.name,
        style=styling_request.style.name,
        additional_info=styling_request.additional_info,
    )
    image_base64 = _read_file_as_base64(styling_request.image_optimized)
    requested_model = settings.OPENAI_MODEL

    raw_output, model_name, usage = request_primary_json_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        image_base64_jpeg=image_base64,
        model=requested_model,
    )
    raw_output = raw_output.strip() or "{}"
    validated, validation_error = try_validate_ai_json(raw_output)
    if validated:
        return validated.model_dump(), model_name, usage

    logger.warning(
        "request_id=%s invalid primary output preview=%s",
        styling_request.id,
        _preview_text(raw_output),
    )

    if not has_schema_payload(raw_output):
        logger.warning(
            "request_id=%s AI output did not contain schema payload; retrying primary request once",
            styling_request.id,
        )
        retry_output, retry_model_name, retry_usage = request_primary_json_output(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            image_base64_jpeg=image_base64,
            model=requested_model,
        )
        retry_output = retry_output.strip() or "{}"
        retry_validated, retry_error = try_validate_ai_json(retry_output)
        if retry_validated:
            merged_usage = {"primary": usage, "primary_retry": retry_usage}
            return retry_validated.model_dump(), retry_model_name, merged_usage
        logger.warning(
            "request_id=%s invalid primary retry output preview=%s",
            styling_request.id,
            _preview_text(retry_output),
        )
        logger.warning(
            "request_id=%s primary retry still invalid: %s",
            styling_request.id,
            retry_error,
        )
        raw_output = retry_output
        model_name = retry_model_name
        usage = {"primary": usage, "primary_retry": retry_usage}
        validation_error = retry_error

    logger.warning(
        "request_id=%s AI output invalid on first attempt, running repair flow: %s",
        styling_request.id,
        validation_error,
    )

    repair_prompt = render_json_repair_prompt(
        invalid_json=raw_output,
        validation_error=str(validation_error),
    )
    repaired_output, repaired_model, repair_usage = request_json_repair(
        system_prompt=system_prompt,
        repair_prompt=repair_prompt,
        model=requested_model,
    )
    repaired_output = repaired_output.strip() or "{}"
    repaired_validated, repair_error = try_validate_ai_json(repaired_output)
    if repaired_validated:
        merged_usage = {"primary": usage, "repair": repair_usage}
        return repaired_validated.model_dump(), repaired_model, merged_usage

    logger.warning(
        "request_id=%s invalid repair output contains_schema=%s preview=%s",
        styling_request.id,
        has_schema_payload(repaired_output),
        _preview_text(repaired_output),
    )

    raise AIOutputValidationError(
        f"AI output failed schema validation after one retry. Last error: {repair_error}"
    )


def _detect_image_extension(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "jpg"
    return "png"


def generate_outfit_image(
    styling_request: StylingRequest,
    result_json: dict,
) -> tuple[ContentFile, str, str, dict | list | str | int | float | None]:
    selected_outfit = (result_json.get("outfits") or {}).get(GENERATED_OUTFIT_KEY) or {}
    detected_items = result_json.get("detected_items") or []
    to_buy = result_json.get("to_buy") or []

    image_prompt = render_outfit_image_prompt(
        season=styling_request.season.name,
        occasion=styling_request.occasion.name,
        style=styling_request.style.name,
        selected_outfit_json=json.dumps(selected_outfit, ensure_ascii=True),
        detected_items_json=json.dumps(detected_items, ensure_ascii=True),
        to_buy_json=json.dumps(to_buy, ensure_ascii=True),
    )

    reference_image_field = styling_request.image_optimized or styling_request.image_original
    reference_image_bytes = None
    reference_image_filename = "reference.jpg"
    if reference_image_field:
        reference_image_bytes = _read_field_file_bytes(reference_image_field)
        reference_image_filename = Path(reference_image_field.name or reference_image_filename).name

    b64_image, image_model, image_usage = request_outfit_image(
        prompt=image_prompt,
        model=settings.OPENAI_IMAGE_MODEL,
        size=settings.OPENAI_IMAGE_SIZE,
        quality=settings.OPENAI_IMAGE_QUALITY,
        reference_image_bytes=reference_image_bytes,
        reference_image_filename=reference_image_filename,
    )
    try:
        image_bytes = base64.b64decode(b64_image, validate=True)
    except Exception as exc:
        raise OpenAIIntegrationError(f"Generated image payload decode failed: {exc}") from exc
    extension = _detect_image_extension(image_bytes)
    content = ContentFile(image_bytes)
    return content, extension, image_model, image_usage


def build_generated_outfit_metadata(result_json: dict | None) -> dict | None:
    outfits = (result_json or {}).get("outfits") or {}
    selected_outfit = outfits.get(GENERATED_OUTFIT_KEY)
    if not isinstance(selected_outfit, dict):
        return None

    return {
        "key": GENERATED_OUTFIT_KEY,
        "option_label": OUTFIT_OPTION_LABELS[GENERATED_OUTFIT_KEY],
        "variant_label": OUTFIT_VARIANT_LABELS[GENERATED_OUTFIT_KEY],
        "title": selected_outfit.get("title", ""),
    }


def build_outfit_cards(result_json: dict) -> list[dict]:
    outfits = result_json.get("outfits") or {}
    cards: list[dict] = []

    for outfit_key in OUTFIT_DISPLAY_ORDER:
        outfit_data = outfits.get(outfit_key) or {}
        if not isinstance(outfit_data, dict):
            continue

        cards.append(
            {
                "key": outfit_key,
                "option_label": OUTFIT_OPTION_LABELS[outfit_key],
                "variant_label": OUTFIT_VARIANT_LABELS[outfit_key],
                "is_generated_source": outfit_key == GENERATED_OUTFIT_KEY,
                "title": outfit_data.get("title", ""),
                "why_it_works": outfit_data.get("why_it_works", ""),
                "fit_notes": outfit_data.get("fit_notes", ""),
                "color_notes": outfit_data.get("color_notes", ""),
                "items": outfit_data.get("items", []),
            }
        )

    return cards


def build_google_search_url(query: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(query)}"


def cleanup_old_requests_media(days: int) -> int:
    cutoff = timezone.now() - timedelta(days=days)
    queryset = StylingRequest.objects.filter(created_at__lt=cutoff, files_deleted=False)
    cleaned_records = 0

    for styling_request in queryset.iterator():
        update_fields: list[str] = []
        for field_name in ("image_original", "image_optimized", "generated_image"):
            file_field = getattr(styling_request, field_name)
            if file_field and file_field.name:
                try:
                    file_field.storage.delete(file_field.name)
                except Exception:
                    logger.exception(
                        "request_id=%s failed to delete %s=%s",
                        styling_request.id,
                        field_name,
                        file_field.name,
                    )
                setattr(styling_request, field_name, None)
                update_fields.append(field_name)

        styling_request.files_deleted = True
        update_fields.append("files_deleted")
        update_fields.append("updated_at")
        styling_request.save(update_fields=sorted(set(update_fields)))
        cleaned_records += 1

    return cleaned_records
