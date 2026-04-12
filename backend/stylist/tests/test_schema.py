import json

from django.test import SimpleTestCase
from pydantic import ValidationError

from stylist.schemas import has_schema_payload, validate_ai_json


def build_valid_payload() -> dict:
    return {
        "detected_items": [
            {
                "id": "item_1",
                "label": "blue denim jeans",
                "category": "bottom",
                "colors": ["blue"],
                "pattern": None,
                "material": "denim",
                "confidence": 0.95,
                "notes": None,
            },
            {
                "id": "item_2",
                "label": "white t-shirt",
                "category": "top",
                "colors": ["white"],
                "pattern": None,
                "material": "cotton",
                "confidence": 0.92,
                "notes": None,
            },
        ],
        "outfits": {
            "safe": {
                "title": "Classic everyday",
                "items": [
                    {"detected_item_id": "item_1", "role": "bottom"},
                    {"detected_item_id": "item_2", "role": "top"},
                ],
                "why_it_works": "Balanced and simple.",
                "fit_notes": "Regular fit.",
                "color_notes": "Neutral contrast.",
            },
            "bold": {
                "title": "High contrast",
                "items": [{"detected_item_id": "item_2", "role": "top"}],
                "why_it_works": "Crisp focus on top layer.",
                "fit_notes": "Tuck for structure.",
                "color_notes": "Strong monochrome base.",
            },
            "creative": {
                "title": "Layered experiment",
                "items": [{"detected_item_id": "item_1", "role": "base"}],
                "why_it_works": "Adds dimension with accessories.",
                "fit_notes": "Use relaxed silhouette.",
                "color_notes": "Add textures around blue tones.",
            },
        },
        "to_buy": [
            {
                "name": "navy overshirt",
                "why_needed": "Adds a top layer for cooler evenings.",
                "google_query": "men navy overshirt cotton",
                "priority": "nice_to_have",
            }
        ],
        "advice": {
            "style": ["Use clean sneakers for cohesion."],
            "care": ["Wash denim inside out in cold water."],
            "impression": ["Looks approachable and polished."],
        },
    }


class StylingSchemaTests(SimpleTestCase):
    def test_valid_schema_passes(self):
        payload = build_valid_payload()
        validated = validate_ai_json(json.dumps(payload))
        self.assertEqual(validated.outfits.safe.items[0].detected_item_id, "item_1")

    def test_invalid_detected_item_reference_fails(self):
        payload = build_valid_payload()
        payload["outfits"]["bold"]["items"][0]["detected_item_id"] = "item_999"

        with self.assertRaises((ValidationError, ValueError)):
            validate_ai_json(json.dumps(payload))

    def test_double_encoded_json_string_passes(self):
        payload = build_valid_payload()
        wrapped = json.dumps(json.dumps(payload))
        validated = validate_ai_json(wrapped)
        self.assertEqual(validated.detected_items[0].id, "item_1")

    def test_chat_envelope_content_json_string_passes(self):
        payload = build_valid_payload()
        envelope = {
            "id": "chatcmpl-example",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(payload),
                    }
                }
            ],
        }
        validated = validate_ai_json(json.dumps(envelope))
        self.assertEqual(validated.outfits.safe.title, "Classic everyday")

    def test_chat_envelope_content_text_value_passes(self):
        payload = build_valid_payload()
        envelope = {
            "id": "chatcmpl-example-2",
            "choices": [
                {
                    "message": {
                        "content": [
                            {
                                "type": "text",
                                "text": {"value": json.dumps(payload)},
                            }
                        ]
                    }
                }
            ],
        }
        validated = validate_ai_json(json.dumps(envelope))
        self.assertEqual(validated.outfits.bold.title, "High contrast")

    def test_chat_envelope_legacy_choice_text_passes(self):
        payload = build_valid_payload()
        envelope = {
            "id": "chatcmpl-example-3",
            "choices": [
                {
                    "text": json.dumps(payload),
                }
            ],
        }
        validated = validate_ai_json(json.dumps(envelope))
        self.assertEqual(validated.outfits.creative.title, "Layered experiment")

    def test_chat_envelope_message_parsed_passes(self):
        payload = build_valid_payload()
        envelope = {
            "id": "chatcmpl-example-4",
            "choices": [
                {
                    "message": {
                        "parsed": payload,
                    }
                }
            ],
        }
        validated = validate_ai_json(json.dumps(envelope))
        self.assertEqual(validated.detected_items[0].id, "item_1")

    def test_chat_envelope_tool_calls_arguments_passes(self):
        payload = build_valid_payload()
        envelope = {
            "id": "chatcmpl-example-5",
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "type": "function",
                                "function": {
                                    "name": "styling_result",
                                    "arguments": json.dumps(payload),
                                },
                            }
                        ]
                    }
                }
            ],
        }
        validated = validate_ai_json(json.dumps(envelope))
        self.assertEqual(validated.outfits.safe.title, "Classic everyday")

    def test_responses_envelope_text_value_passes(self):
        payload = build_valid_payload()
        envelope = {
            "id": "resp_example",
            "output": [
                {
                    "content": [
                        {
                            "type": "output_text",
                            "text": {"value": json.dumps(payload)},
                        }
                    ]
                }
            ],
        }
        validated = validate_ai_json(json.dumps(envelope))
        self.assertEqual(validated.outfits.bold.title, "High contrast")

    def test_responses_envelope_ignores_empty_output_text(self):
        payload = build_valid_payload()
        envelope = {
            "id": "resp_example_2",
            "output_text": "",
            "output": [
                {
                    "content": [
                        {
                            "type": "output_text",
                            "text": {"value": json.dumps(payload)},
                        }
                    ]
                }
            ],
        }
        validated = validate_ai_json(json.dumps(envelope))
        self.assertEqual(validated.outfits.creative.title, "Layered experiment")

    def test_chat_completion_envelope_with_metadata_passes(self):
        payload = build_valid_payload()
        envelope = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1771795143,
            "model": "gpt-5-mini-2025-08-07",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "length",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "output_text",
                                "text": {"value": json.dumps(payload)},
                                "annotations": [],
                            }
                        ],
                    },
                }
            ],
            "usage": {
                "prompt_tokens": 123,
                "completion_tokens": 456,
                "total_tokens": 579,
            },
        }
        validated = validate_ai_json(json.dumps(envelope))
        self.assertEqual(validated.detected_items[0].id, "item_1")
        self.assertTrue(has_schema_payload(json.dumps(envelope)))
