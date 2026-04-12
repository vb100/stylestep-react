from django.test import SimpleTestCase

from stylist.prompts import render_json_repair_prompt, render_outfit_image_prompt


class PromptRenderingTests(SimpleTestCase):
    def test_outfit_image_prompt_substitution(self):
        rendered = render_outfit_image_prompt(
            season="Summer",
            occasion="Office",
            style="Minimal",
            selected_outfit_json='{"title":"Test"}',
            detected_items_json='[{"id":"item_1","label":"White blazer"}]',
            to_buy_json='[{"name":"Shoes"}]',
        )
        self.assertIn("Summer", rendered)
        self.assertIn("Office", rendered)
        self.assertIn("Minimal", rendered)
        self.assertIn('{"title":"Test"}', rendered)
        self.assertIn('"label":"White blazer"', rendered)

    def test_json_repair_prompt_truncates_large_invalid_json(self):
        invalid_json = "x" * 9000
        rendered = render_json_repair_prompt(
            invalid_json=invalid_json,
            validation_error="schema error",
        )
        self.assertIn("schema error", rendered)
        self.assertIn("[TRUNCATED", rendered)
