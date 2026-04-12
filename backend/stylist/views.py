from __future__ import annotations

import logging
from uuid import UUID

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from .forms import StylingRequestForm
from .image_utils import ImageOptimizationError
from .models import StylingRequest
from .schemas import StylingResult
from .services import (
    build_generated_outfit_metadata,
    build_google_search_url,
    build_outfit_cards,
    create_optimized_image,
)
from .tasks import run_ai_styling_request

logger = logging.getLogger("stylist")


@require_http_methods(["GET", "POST"])
def home(request):
    if request.method == "POST":
        form = StylingRequestForm(request.POST, request.FILES)
        if form.is_valid():
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
                return redirect("stylist:submitted", request_id=styling_request.id)

            run_ai_styling_request.delay(str(styling_request.id))
            logger.info("request_id=%s status=QUEUED", styling_request.id)
            return redirect("stylist:submitted", request_id=styling_request.id)
    else:
        form = StylingRequestForm()

    return render(request, "stylist/home.html", {"form": form})


@require_GET
def submitted(request, request_id: UUID):
    styling_request = get_object_or_404(StylingRequest, id=request_id)
    return render(
        request,
        "stylist/submitted.html",
        {
            "styling_request": styling_request,
            "status_url": reverse("stylist:status", kwargs={"request_id": styling_request.id}),
            "result_url": reverse("stylist:result", kwargs={"request_id": styling_request.id}),
        },
    )


@require_GET
def request_status(request, request_id: UUID):
    styling_request = get_object_or_404(StylingRequest, id=request_id)
    payload = {"status": styling_request.status}

    if styling_request.status == StylingRequest.Status.FAILED and styling_request.error_message:
        payload["error"] = styling_request.error_message
    if styling_request.status == StylingRequest.Status.DONE:
        payload["result_url"] = reverse("stylist:result", kwargs={"request_id": styling_request.id})

    return JsonResponse(payload)


@require_GET
def result(request, request_id: UUID):
    styling_request = get_object_or_404(StylingRequest, id=request_id)

    if styling_request.status == StylingRequest.Status.FAILED:
        return render(
            request,
            "stylist/result.html",
            {"styling_request": styling_request, "result": None, "to_buy_with_links": []},
        )

    if styling_request.status != StylingRequest.Status.DONE or not styling_request.result_json:
        return redirect("stylist:submitted", request_id=styling_request.id)

    try:
        validated = StylingResult.model_validate(styling_request.result_json)
        result_data = validated.model_dump()
    except Exception:
        logger.exception("request_id=%s failed to parse stored result_json", styling_request.id)
        styling_request.status = StylingRequest.Status.FAILED
        styling_request.error_message = "Stored AI result is invalid."
        styling_request.save(update_fields=["status", "error_message", "updated_at"])
        return redirect("stylist:submitted", request_id=styling_request.id)

    to_buy_with_links = []
    for item in result_data["to_buy"]:
        to_buy_with_links.append(
            {
                **item,
                "google_search_url": build_google_search_url(item["google_query"]),
            }
        )

    generated_outfit = build_generated_outfit_metadata(result_data)
    outfit_cards = build_outfit_cards(result_data)

    return render(
        request,
        "stylist/result.html",
        {
            "styling_request": styling_request,
            "result": result_data,
            "to_buy_with_links": to_buy_with_links,
            "generated_outfit": generated_outfit,
            "outfit_cards": outfit_cards,
        },
    )
