import uuid
from pathlib import Path

from django.db import models


def original_upload_path(instance: "StylingRequest", filename: str) -> str:
    extension = Path(filename).suffix.lower() or ".jpg"
    return f"requests/{instance.id}/original/{uuid.uuid4().hex}{extension}"


def optimized_upload_path(instance: "StylingRequest", _: str) -> str:
    return f"requests/{instance.id}/optimized/{uuid.uuid4().hex}.jpg"


def generated_upload_path(instance: "StylingRequest", _: str) -> str:
    return f"requests/{instance.id}/generated/{uuid.uuid4().hex}.png"


class ReferenceModel(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class Season(ReferenceModel):
    class Meta(ReferenceModel.Meta):
        verbose_name = "Season"
        verbose_name_plural = "Seasons"


class Occasion(ReferenceModel):
    class Meta(ReferenceModel.Meta):
        verbose_name = "Occasion"
        verbose_name_plural = "Occasions"


class StyleTag(ReferenceModel):
    class Meta(ReferenceModel.Meta):
        verbose_name = "Style"
        verbose_name_plural = "Styles"


class StylingRequest(models.Model):
    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        RUNNING = "RUNNING", "Running"
        DONE = "DONE", "Done"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    season = models.ForeignKey(Season, on_delete=models.PROTECT, related_name="styling_requests")
    occasion = models.ForeignKey(Occasion, on_delete=models.PROTECT, related_name="styling_requests")
    style = models.ForeignKey(StyleTag, on_delete=models.PROTECT, related_name="styling_requests")
    additional_info = models.TextField(blank=True)
    image_original = models.ImageField(upload_to=original_upload_path, blank=True, null=True)
    image_optimized = models.ImageField(upload_to=optimized_upload_path, blank=True, null=True)
    generated_image = models.ImageField(upload_to=generated_upload_path, blank=True, null=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    result_json = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True)
    ai_model = models.CharField(max_length=128, blank=True)
    ai_latency_ms = models.IntegerField(blank=True, null=True)
    ai_usage = models.JSONField(blank=True, null=True)
    image_model = models.CharField(max_length=128, blank=True)
    image_latency_ms = models.IntegerField(blank=True, null=True)
    image_error_message = models.TextField(blank=True)
    files_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"StylingRequest<{self.id}> [{self.status}]"
