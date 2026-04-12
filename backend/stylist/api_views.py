from __future__ import annotations

import logging
from uuid import UUID

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from .forms import StylingRequestForm
from .image_utils import ImageOptimizationError
from .models import StylingRequest
from .presenters import serialize_reference_data, serialize_request_detail, serialize_request_status
from .services import create_optimized_image

logger = logging.getLogger("stylist")


def _json_error(message: str, status: int = 400, *, details: dict | None = None) -> JsonResponse:
    payload: dict[str, object] = {"error": message}
    if details:
        payload["details"] = details
    return JsonResponse(payload, status=status)


def _serialize_form_errors(form: StylingRequestForm) -> dict[str, list[str]]:
    return {field: [str(error) for error in errors] for field, errors in form.errors.items()}


@require_GET
def health(request):
    return JsonResponse({"status": "ok", "app_name": "StyleStep"})


@ensure_csrf_cookie
@require_GET
def bootstrap(request):
    return JsonResponse(
        {
            "app_name": "StyleStep | Tavo asmeninis stilistas",
            "default_model": settings.OPENAI_MODEL,
            "reference_data": serialize_reference_data(),
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def create_request(request):
    form = StylingRequestForm(request.POST, request.FILES)
    if not form.is_valid():
        return _json_error("Nepavyko patikrinti formos duomenų.", status=400, details={"fields": _serialize_form_errors(form)})

    styling_request = form.save(commit=False)
    styling_request.status = StylingRequest.Status.QUEUED
    styling_request.ai_model = settings.OPENAI_MODEL
    styling_request.save()

    try:
        create_optimized_image(styling_request)
        styling_request.save(update_fields=["image_optimized", "updated_at"])
    except ImageOptimizationError as exc:
        styling_request.status = StylingRequest.Status.FAILED
        styling_request.error_message = str(exc)
        styling_request.save(update_fields=["status", "error_message", "updated_at"])
        logger.exception("request_id=%s image optimization failed", styling_request.id)
        return JsonResponse(serialize_request_status(styling_request), status=201)

    logger.info("request_id=%s status=QUEUED", styling_request.id)
    return JsonResponse(serialize_request_status(styling_request), status=201)


@require_GET
def request_status(request, request_id: UUID):
    try:
        styling_request = StylingRequest.objects.get(id=request_id)
    except StylingRequest.DoesNotExist:
        return _json_error("Užklausa nerasta.", status=404)

    return JsonResponse(serialize_request_status(styling_request))


@require_GET
def request_detail(request, request_id: UUID):
    try:
        styling_request = StylingRequest.objects.select_related("season", "occasion", "style").get(id=request_id)
    except StylingRequest.DoesNotExist:
        return _json_error("Užklausa nerasta.", status=404)

    try:
        payload = serialize_request_detail(styling_request)
    except Exception:
        logger.exception("request_id=%s failed to serialize result_json", request_id)
        styling_request.status = StylingRequest.Status.FAILED
        styling_request.error_message = "Nepavyko paruošti išsaugoto rezultato."
        styling_request.save(update_fields=["status", "error_message", "updated_at"])
        payload = serialize_request_detail(styling_request)

    return JsonResponse(payload)
