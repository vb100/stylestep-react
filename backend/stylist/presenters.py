from __future__ import annotations

from typing import Any

from django.conf import settings

from .models import Occasion, Season, StyleTag, StylingRequest
from .schemas import StylingResult
from .services import build_generated_outfit_metadata, build_google_search_url, build_outfit_cards


def serialize_reference_queryset(queryset) -> list[dict[str, Any]]:
    return [
        {
            "id": item.id,
            "name": item.name,
            "code": item.code,
        }
        for item in queryset
    ]


def serialize_reference_data() -> dict[str, Any]:
    return {
        "seasons": serialize_reference_queryset(Season.objects.filter(is_active=True).order_by("sort_order", "name")),
        "occasions": serialize_reference_queryset(
            Occasion.objects.filter(is_active=True).order_by("sort_order", "name")
        ),
        "styles": serialize_reference_queryset(StyleTag.objects.filter(is_active=True).order_by("sort_order", "name")),
    }


def _build_result_payload(styling_request: StylingRequest) -> dict[str, Any] | None:
    if not styling_request.result_json:
        return None

    validated = StylingResult.model_validate(styling_request.result_json)
    result_data = validated.model_dump()

    to_buy_with_links = [
        {
            **item,
            "google_search_url": build_google_search_url(item["google_query"]),
        }
        for item in result_data["to_buy"]
    ]

    return {
        **result_data,
        "generated_outfit": build_generated_outfit_metadata(result_data),
        "outfit_cards": build_outfit_cards(result_data),
        "to_buy_with_links": to_buy_with_links,
    }


def serialize_request_status(styling_request: StylingRequest) -> dict[str, Any]:
    result_ready = bool(styling_request.result_json) and styling_request.status != StylingRequest.Status.FAILED
    image_ready = bool(styling_request.generated_image)
    image_pending = (
        result_ready
        and settings.OPENAI_ENABLE_OUTFIT_IMAGE
        and styling_request.status == StylingRequest.Status.RUNNING
        and not image_ready
        and not styling_request.image_error_message
    )
    return {
        "id": str(styling_request.id),
        "status": styling_request.status,
        "result_ready": result_ready,
        "image_ready": image_ready,
        "image_pending": image_pending,
        "error_message": styling_request.error_message,
        "image_error_message": styling_request.image_error_message,
        "ai_latency_ms": styling_request.ai_latency_ms,
        "image_latency_ms": styling_request.image_latency_ms,
        "created_at": styling_request.created_at.isoformat(),
        "updated_at": styling_request.updated_at.isoformat(),
        "detail_url": f"/api/requests/{styling_request.id}/",
    }


def serialize_request_detail(styling_request: StylingRequest) -> dict[str, Any]:
    payload = serialize_request_status(styling_request)
    payload.update(
        {
            "season": {
                "id": styling_request.season_id,
                "name": styling_request.season.name,
                "code": styling_request.season.code,
            },
            "occasion": {
                "id": styling_request.occasion_id,
                "name": styling_request.occasion.name,
                "code": styling_request.occasion.code,
            },
            "style": {
                "id": styling_request.style_id,
                "name": styling_request.style.name,
                "code": styling_request.style.code,
            },
            "additional_info": styling_request.additional_info,
            "ai_model": styling_request.ai_model,
            "image_model": styling_request.image_model,
            "generated_image_url": styling_request.generated_image.url if styling_request.generated_image else None,
            "image_original_url": styling_request.image_original.url if styling_request.image_original else None,
            "result": _build_result_payload(styling_request),
        }
    )
    return payload
