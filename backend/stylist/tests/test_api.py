from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from stylist.models import Occasion, Season, StyleTag, StylingRequest


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
                "label": "šviesus švarkas",
                "category": "outerwear",
                "colors": ["smėlio"],
                "pattern": None,
                "material": "vilna",
                "confidence": 0.94,
                "notes": None,
            }
        ],
        "outfits": {
            "safe": {
                "title": "Klasikinis šviesus derinys",
                "items": [{"detected_item_id": "item_1", "role": "viršus"}],
                "why_it_works": "Subalansuotas ir švarus variantas.",
                "fit_notes": "Tiesesnė linija išlaiko tvarkingą siluetą.",
                "color_notes": "Šviesi neutrali gama suteikia lengvumo.",
            },
            "bold": {
                "title": "Ryškesnis kontrasto akcentas",
                "items": [{"detected_item_id": "item_1", "role": "viršus"}],
                "why_it_works": "Kontrastas suteikia daugiau dinamikos.",
                "fit_notes": "Aiškesnė struktūra išlaiko tvarką.",
                "color_notes": "Tamsesni akcentai sustiprina pagrindinį drabužį.",
            },
            "creative": {
                "title": "Kūrybiškas lengvas sluoksniavimas",
                "items": [{"detected_item_id": "item_1", "role": "viršus"}],
                "why_it_works": "Pagrindinis drabužis išlieka dėmesio centre.",
                "fit_notes": "Laisvesnė proporcija palieka judesio.",
                "color_notes": "Tekstūriniai neutralūs atspalviai išlaiko vientisumą.",
            },
        },
        "to_buy": [],
        "advice": {
            "style": ["Švarką palik kaip pagrindinį akcentą."],
            "care": ["Prieš dėvint lengvai išgarink."],
            "impression": ["Įvaizdis atrodo tvarkingas ir ramus."],
        },
    }


class ApiFlowTests(TestCase):
    def setUp(self):
        self.season = Season.objects.get(code="summer")
        self.occasion = Occasion.objects.get(code="office")
        self.style = StyleTag.objects.get(code="classic")

    def test_bootstrap_returns_reference_data(self):
        response = self.client.get("/api/bootstrap/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["app_name"], "StyleStep | Tavo asmeninis stilistas")
        season_codes = [season["code"] for season in payload["reference_data"]["seasons"]]
        self.assertIn("summer", season_codes)
        season_by_code = {season["code"]: season["name"] for season in payload["reference_data"]["seasons"]}
        occasion_by_code = {item["code"]: item["name"] for item in payload["reference_data"]["occasions"]}
        style_by_code = {item["code"]: item["name"] for item in payload["reference_data"]["styles"]}
        self.assertEqual(season_by_code["summer"], "Vasara")
        self.assertEqual(occasion_by_code["office"], "Biuras")
        self.assertEqual(style_by_code["classic"], "Klasikinis")

    def test_create_request_queues_and_optimizes_image(self):
        response = self.client.post(
            "/api/requests/",
            data={
                "season": self.season.id,
                "occasion": self.occasion.id,
                "style": self.style.id,
                "additional_info": "Keep it practical.",
                "image_original": build_uploaded_image(),
            },
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        styling_request = StylingRequest.objects.get(id=payload["id"])
        self.assertEqual(styling_request.status, StylingRequest.Status.QUEUED)
        self.assertTrue(bool(styling_request.image_optimized))

    def test_request_detail_returns_queued_payload_before_worker_runs(self):
        styling_request = StylingRequest.objects.create(
            season=self.season,
            occasion=self.occasion,
            style=self.style,
            additional_info="Queued request.",
            status=StylingRequest.Status.QUEUED,
        )
        response = self.client.get(f"/api/requests/{styling_request.id}/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "QUEUED")
        self.assertFalse(payload["result_ready"])
        self.assertFalse(payload["image_ready"])
        self.assertFalse(payload["image_pending"])
        self.assertIsNone(payload["result"])

    def test_request_detail_returns_partial_result_while_image_is_still_generating(self):
        styling_request = StylingRequest.objects.create(
            season=self.season,
            occasion=self.occasion,
            style=self.style,
            additional_info="Text result is ready.",
            status=StylingRequest.Status.RUNNING,
            result_json=build_valid_result_payload(),
            ai_model="gpt-5-mini",
            ai_latency_ms=78000,
        )
        response = self.client.get(f"/api/requests/{styling_request.id}/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "RUNNING")
        self.assertTrue(payload["result_ready"])
        self.assertFalse(payload["image_ready"])
        self.assertTrue(payload["image_pending"])
        self.assertIsNotNone(payload["result"])
        self.assertEqual(payload["result"]["generated_outfit"]["key"], "safe")
        self.assertEqual(len(payload["result"]["outfit_cards"]), 3)
