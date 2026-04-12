from django.test import SimpleTestCase

from stylist.services import build_generated_outfit_metadata, build_outfit_cards


def _build_result_payload() -> dict:
    return {
        "outfits": {
            "safe": {
                "title": "Klasikinis derinys",
                "items": [{"detected_item_id": "item_1", "role": "top"}],
                "why_it_works": "Aisku ir tvarkinga.",
                "fit_notes": "Tiesus siluetas.",
                "color_notes": "Ramus kontrastas.",
            },
            "bold": {
                "title": "Ryskus derinys",
                "items": [{"detected_item_id": "item_2", "role": "bottom"}],
                "why_it_works": "Daugiau kontrasto.",
                "fit_notes": "Ryskesnis siluetas.",
                "color_notes": "Akcentines spalvos.",
            },
            "creative": {
                "title": "Kurybinis derinys",
                "items": [{"detected_item_id": "item_3", "role": "layer"}],
                "why_it_works": "Idomus sluoksniavimas.",
                "fit_notes": "Laisvesnis kirpimas.",
                "color_notes": "Daugiau teksturu.",
            },
        }
    }


class ResultDisplayMetadataTests(SimpleTestCase):
    def test_generated_outfit_metadata_uses_option_one_safe(self):
        metadata = build_generated_outfit_metadata(_build_result_payload())
        self.assertEqual(metadata["key"], "safe")
        self.assertEqual(metadata["option_label"], "1 variantas")
        self.assertEqual(metadata["variant_label"], "Ramus")
        self.assertEqual(metadata["title"], "Klasikinis derinys")

    def test_outfit_cards_marks_generated_source(self):
        cards = build_outfit_cards(_build_result_payload())
        self.assertEqual(len(cards), 3)
        self.assertTrue(cards[0]["is_generated_source"])
        self.assertEqual(cards[0]["option_label"], "1 variantas")
        self.assertFalse(cards[1]["is_generated_source"])
        self.assertEqual(cards[1]["option_label"], "2 variantas")
        self.assertEqual(cards[2]["option_label"], "3 variantas")
