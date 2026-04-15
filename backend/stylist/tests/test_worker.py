from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from stylist.models import Occasion, Season, StyleTag, StylingRequest
from stylist.tasks import process_next_styling_request


def build_uploaded_image(name: str = "closet.jpg") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (1200, 900), color=(240, 240, 240)).save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name=name, content=buffer.read(), content_type="image/jpeg")


def build_valid_result_payload() -> dict:
    return {
        "detected_items": [
            {
                "id": "item_1",
                "label": "white blazer",
                "category": "outerwear",
                "colors": ["white"],
                "pattern": None,
                "material": "cotton",
                "confidence": 0.95,
                "notes": None,
            }
        ],
        "outfits": {
            "safe": {
                "title": "Classic blazer look",
                "items": [{"detected_item_id": "item_1", "role": "outerwear"}],
                "why_it_works": "Balanced and simple.",
                "fit_notes": "Straight silhouette.",
                "color_notes": "Light neutral palette.",
            },
            "bold": {
                "title": "Bold blazer look",
                "items": [{"detected_item_id": "item_1", "role": "outerwear"}],
                "why_it_works": "Adds contrast with accessories.",
                "fit_notes": "Sharper structure.",
                "color_notes": "Use darker accents around the blazer.",
            },
            "creative": {
                "title": "Creative blazer look",
                "items": [{"detected_item_id": "item_1", "role": "outerwear"}],
                "why_it_works": "Keeps the blazer central.",
                "fit_notes": "Relaxed proportions.",
                "color_notes": "Textural neutrals work best.",
            },
        },
        "to_buy": [],
        "advice": {
            "style": ["Keep the blazer as the main focal point."],
            "care": ["Steam lightly before wearing."],
            "impression": ["Polished and calm."],
        },
    }


class WorkerFlowTests(TestCase):
    def setUp(self):
        self.season = Season.objects.get(code="summer")
        self.occasion = Occasion.objects.get(code="office")
        self.style = StyleTag.objects.get(code="classic")

    def test_process_next_styling_request_marks_request_done(self):
        with TemporaryDirectory() as temp_media_root:
            with override_settings(MEDIA_ROOT=temp_media_root):
                styling_request = StylingRequest.objects.create(
                    season=self.season,
                    occasion=self.occasion,
                    style=self.style,
                    additional_info="Please keep it polished.",
                    image_original=build_uploaded_image(),
                    status=StylingRequest.Status.QUEUED,
                )

                styling_request.image_optimized.save("optimized.jpg", ContentFile(b"fake-image"), save=True)

                with patch(
                    "stylist.tasks.run_openai_styling_analysis",
                    return_value=(build_valid_result_payload(), "gpt-5-mini", {"total_tokens": 123}),
                ), patch(
                    "stylist.tasks.generate_outfit_image",
                    return_value=(ContentFile(b"fake-png"), "png", "gpt-image-1", {"images": 1}),
                ):
                    processed = process_next_styling_request()

                self.assertIsNotNone(processed)
                styling_request.refresh_from_db()
                self.assertEqual(styling_request.status, StylingRequest.Status.DONE)
                self.assertEqual(styling_request.ai_model, "gpt-5-mini")
                self.assertEqual(styling_request.image_model, "gpt-image-1")
                self.assertTrue(bool(styling_request.result_json))

    def test_process_next_styling_request_saves_text_result_before_image_stage(self):
        with TemporaryDirectory() as temp_media_root:
            with override_settings(MEDIA_ROOT=temp_media_root):
                styling_request = StylingRequest.objects.create(
                    season=self.season,
                    occasion=self.occasion,
                    style=self.style,
                    additional_info="Please keep it polished.",
                    image_original=build_uploaded_image(),
                    status=StylingRequest.Status.QUEUED,
                )

                styling_request.image_optimized.save("optimized.jpg", ContentFile(b"fake-image"), save=True)

                def fake_generate_outfit_image(*args, **kwargs):
                    styling_request.refresh_from_db()
                    self.assertEqual(styling_request.status, StylingRequest.Status.RUNNING)
                    self.assertTrue(bool(styling_request.result_json))
                    self.assertEqual(styling_request.ai_model, "gpt-5-mini")
                    return ContentFile(b"fake-png"), "png", "gpt-image-1", {"images": 1}

                with patch(
                    "stylist.tasks.run_openai_styling_analysis",
                    return_value=(build_valid_result_payload(), "gpt-5-mini", {"total_tokens": 123}),
                ), patch(
                    "stylist.tasks.generate_outfit_image",
                    side_effect=fake_generate_outfit_image,
                ):
                    process_next_styling_request()
