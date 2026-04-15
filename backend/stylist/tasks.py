from __future__ import annotations

import logging
import uuid
from time import monotonic

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import StylingRequest
from .services import cleanup_old_requests_media, generate_outfit_image, run_openai_styling_analysis

logger = logging.getLogger("stylist")


def claim_next_styling_request() -> StylingRequest | None:
    next_request_id = (
        StylingRequest.objects.filter(status=StylingRequest.Status.QUEUED)
        .order_by("created_at")
        .values_list("id", flat=True)
        .first()
    )
    if not next_request_id:
        return None

    updated = StylingRequest.objects.filter(id=next_request_id, status=StylingRequest.Status.QUEUED).update(
        status=StylingRequest.Status.RUNNING,
        error_message="",
        ai_model=settings.OPENAI_MODEL,
        image_error_message="",
        updated_at=timezone.now(),
    )
    if not updated:
        return None

    styling_request = StylingRequest.objects.get(id=next_request_id)
    logger.info("request_id=%s status=RUNNING", next_request_id)
    return styling_request


def process_styling_request(request_id: str) -> None:
    try:
        styling_request = StylingRequest.objects.get(id=request_id)
    except StylingRequest.DoesNotExist:
        logger.error("request_id=%s not found", request_id)
        return

    start_ts = monotonic()
    if styling_request.generated_image and styling_request.generated_image.name:
        try:
            styling_request.generated_image.storage.delete(styling_request.generated_image.name)
        except Exception:
            logger.exception("request_id=%s failed to delete previous generated image", request_id)
    styling_request.generated_image = None
    styling_request.image_error_message = ""
    styling_request.save(update_fields=["generated_image", "image_error_message", "updated_at"])

    try:
        analysis_start_ts = monotonic()
        logger.info("request_id=%s stage=analysis status=RUNNING", request_id)
        result_json, model_name, usage = run_openai_styling_analysis(styling_request)
        analysis_latency_ms = int((monotonic() - analysis_start_ts) * 1000)
        logger.info("request_id=%s stage=analysis status=DONE latency_ms=%s", request_id, analysis_latency_ms)
        image_model = ""
        image_latency_ms = None
        image_error_message = ""

        with transaction.atomic():
            styling_request.result_json = result_json
            styling_request.error_message = ""
            styling_request.ai_model = model_name
            styling_request.ai_usage = usage
            styling_request.ai_latency_ms = analysis_latency_ms
            styling_request.image_model = ""
            styling_request.image_latency_ms = None
            styling_request.image_error_message = ""
            styling_request.save(
                update_fields=[
                    "result_json",
                    "error_message",
                    "ai_model",
                    "ai_usage",
                    "ai_latency_ms",
                    "image_model",
                    "image_latency_ms",
                    "image_error_message",
                    "updated_at",
                ]
            )

        if settings.OPENAI_ENABLE_OUTFIT_IMAGE:
            image_start_ts = monotonic()
            logger.info("request_id=%s stage=image status=RUNNING", request_id)
            try:
                image_content, image_extension, image_model_name, image_usage = generate_outfit_image(
                    styling_request=styling_request,
                    result_json=result_json,
                )
                image_filename = f"{uuid.uuid4().hex}.{image_extension}"
                styling_request.generated_image.save(image_filename, image_content, save=False)
                image_model = image_model_name
                usage = {"text": usage, "image": image_usage}
            except Exception as image_exc:
                image_model = settings.OPENAI_IMAGE_MODEL
                image_error_message = str(image_exc)[:2000]
                logger.warning("request_id=%s outfit image generation skipped: %s", request_id, image_error_message)
            image_latency_ms = int((monotonic() - image_start_ts) * 1000)
            logger.info("request_id=%s stage=image status=DONE latency_ms=%s", request_id, image_latency_ms)

        latency_ms = int((monotonic() - start_ts) * 1000)
        with transaction.atomic():
            styling_request.status = StylingRequest.Status.DONE
            styling_request.result_json = result_json
            styling_request.error_message = ""
            styling_request.ai_model = model_name
            styling_request.ai_usage = usage
            styling_request.ai_latency_ms = latency_ms
            styling_request.image_model = image_model
            styling_request.image_latency_ms = image_latency_ms
            styling_request.image_error_message = image_error_message
            styling_request.save(
                update_fields=[
                    "status",
                    "result_json",
                    "error_message",
                    "ai_model",
                    "ai_usage",
                    "ai_latency_ms",
                    "generated_image",
                    "image_model",
                    "image_latency_ms",
                    "image_error_message",
                    "updated_at",
                ]
            )
        logger.info("request_id=%s status=DONE latency_ms=%s", request_id, latency_ms)
    except Exception as exc:
        latency_ms = int((monotonic() - start_ts) * 1000)
        styling_request.status = StylingRequest.Status.FAILED
        styling_request.error_message = str(exc)[:2000]
        styling_request.ai_latency_ms = latency_ms
        styling_request.save(update_fields=["status", "error_message", "ai_latency_ms", "updated_at"])
        logger.exception("request_id=%s status=FAILED latency_ms=%s", request_id, latency_ms)


def process_next_styling_request() -> StylingRequest | None:
    styling_request = claim_next_styling_request()
    if styling_request is None:
        return None
    process_styling_request(str(styling_request.id))
    return styling_request


def cleanup_old_media_files(days: int | None = None) -> int:
    days = int(days or settings.MEDIA_CLEANUP_DAYS)
    deleted_count = cleanup_old_requests_media(days=days)
    logger.info("cleanup_old_media_files days=%s cleaned_records=%s", days, deleted_count)
    return deleted_count
