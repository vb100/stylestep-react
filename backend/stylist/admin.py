from django.contrib import admin

from .models import Occasion, Season, StyleTag, StylingRequest


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("sort_order", "name")


@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("sort_order", "name")


@admin.register(StyleTag)
class StyleTagAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("sort_order", "name")


@admin.register(StylingRequest)
class StylingRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "status",
        "season",
        "occasion",
        "style",
        "ai_model",
        "ai_latency_ms",
        "image_model",
        "image_latency_ms",
        "files_deleted",
    )
    list_filter = ("status", "season", "occasion", "style", "files_deleted", "image_model")
    search_fields = ("id",)
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "status",
        "season",
        "occasion",
        "style",
        "additional_info",
        "image_original",
        "image_optimized",
        "generated_image",
        "result_json",
        "error_message",
        "ai_model",
        "ai_latency_ms",
        "ai_usage",
        "image_model",
        "image_latency_ms",
        "image_error_message",
        "files_deleted",
    )

    def has_add_permission(self, request) -> bool:
        return False
