from pathlib import Path

from django import forms
from django.conf import settings

from .image_utils import ImageValidationError, verify_uploaded_image
from .models import Occasion, Season, StyleTag, StylingRequest


class StylingRequestForm(forms.ModelForm):
    class Meta:
        model = StylingRequest
        fields = ["image_original", "season", "occasion", "style", "additional_info"]
        widgets = {
            "additional_info": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "E.g. I prefer minimal looks, neutral colors, and comfort.",
                }
            )
        }
        labels = {
            "image_original": "Clothing photo",
            "season": "Season",
            "occasion": "Occasion",
            "style": "Style",
            "additional_info": "Additional information",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["season"].queryset = Season.objects.filter(is_active=True).order_by("sort_order", "name")
        self.fields["occasion"].queryset = Occasion.objects.filter(is_active=True).order_by("sort_order", "name")
        self.fields["style"].queryset = StyleTag.objects.filter(is_active=True).order_by("sort_order", "name")

    def clean_image_original(self):
        uploaded = self.cleaned_data["image_original"]
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        if uploaded.size > max_bytes:
            raise forms.ValidationError(f"Image is too large. Max size is {settings.MAX_UPLOAD_SIZE_MB} MB.")

        extension = Path(uploaded.name).suffix.lower().lstrip(".")
        if extension not in settings.ALLOWED_IMAGE_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_IMAGE_EXTENSIONS)
            raise forms.ValidationError(f"Unsupported image type. Allowed: {allowed}.")

        try:
            verify_uploaded_image(uploaded)
        except ImageValidationError as exc:
            raise forms.ValidationError(str(exc)) from exc

        return uploaded
