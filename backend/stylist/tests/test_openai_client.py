from unittest.mock import patch

from django.test import SimpleTestCase
from django.test import override_settings

from stylist.openai_client import _extract_output_text, _is_parameter_error, request_outfit_image


class _ResponseWithCallableOutputText:
    def output_text(self):
        return '{"ok": true}'


class _ResponseWithCallableParsed:
    @property
    def output_text(self):
        return None

    def parsed(self):
        return {"foo": "bar"}


class _TruthyEmptyText:
    def __bool__(self):
        return True

    def __str__(self):
        return ""


class _ResponseWithTruthyEmptyOutputText:
    @property
    def output_text(self):
        return _TruthyEmptyText()

    @property
    def parsed(self):
        return {"wrapped": "payload"}


class _ContentPartObject:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _MessageObject:
    def __init__(self, content):
        self.content = content


class _ChoiceObject:
    def __init__(self, message):
        self.message = message


class _ResponseWithObjectContent:
    def __init__(self, content):
        self.choices = [_ChoiceObject(_MessageObject(content))]


class _ResponseWithMessage:
    def __init__(self, message):
        self.choices = [_ChoiceObject(message)]


class _FunctionObject:
    def __init__(self, arguments):
        self.arguments = arguments


class _ToolCallObject:
    def __init__(self, arguments):
        self.function = _FunctionObject(arguments)


class _MessageWithToolCalls:
    def __init__(self, arguments):
        self.content = None
        self.tool_calls = [_ToolCallObject(arguments)]


class _MessageWithParsed:
    def __init__(self, parsed):
        self.content = None
        self.parsed = parsed


class _FakeImagesAPI:
    def __init__(self):
        self.calls = []
        self.edit_calls = []

    def generate(self, **payload):
        self.calls.append(payload)
        if payload.get("size") == "512x512":
            raise Exception(
                "Error code: 400 - {'error': {'message': \"Invalid size '512x512'. "
                "Supported sizes are 1024x1024, 1024x1536, 1536x1024, and auto.\", "
                "'type': 'image_generation_user_error', 'param': 'size', 'code': 'invalid_value'}}"
            )
        return {
            "data": [{"b64_json": "aGVsbG8="}],
            "model": "gpt-image-1",
            "usage": {"total_tokens": 1},
        }

    def edit(self, **payload):
        self.edit_calls.append(payload)
        return {
            "data": [{"b64_json": "cmVmZXJlbmNl"}],
            "model": "gpt-image-1",
            "usage": {"total_tokens": 2},
        }


class _FakeFailingEditImagesAPI(_FakeImagesAPI):
    def edit(self, **payload):
        self.edit_calls.append(payload)
        raise Exception("Temporary edit failure")


class _FakeClient:
    def __init__(self):
        self.images = _FakeImagesAPI()


class OpenAIClientParsingTests(SimpleTestCase):
    def test_extract_output_text_handles_callable_output_text(self):
        response = _ResponseWithCallableOutputText()
        extracted = _extract_output_text(response)
        self.assertEqual(extracted, '{"ok": true}')

    def test_extract_output_text_handles_callable_parsed(self):
        response = _ResponseWithCallableParsed()
        extracted = _extract_output_text(response)
        self.assertEqual(extracted, '{"foo": "bar"}')

    def test_extract_output_text_does_not_return_empty_string(self):
        response = _ResponseWithTruthyEmptyOutputText()
        extracted = _extract_output_text(response)
        self.assertEqual(extracted, '{"wrapped": "payload"}')

    def test_extract_output_text_handles_object_content_parts(self):
        content = [_ContentPartObject({"value": '{"ok": true}'})]
        response = _ResponseWithObjectContent(content)
        extracted = _extract_output_text(response)
        self.assertEqual(extracted, '{"ok": true}')

    def test_extract_output_text_handles_message_parsed(self):
        message = _MessageWithParsed({"detected_items": []})
        response = _ResponseWithMessage(message)
        extracted = _extract_output_text(response)
        self.assertEqual(extracted, '{"detected_items": []}')

    def test_extract_output_text_handles_tool_call_arguments(self):
        message = _MessageWithToolCalls('{"ok": true}')
        response = _ResponseWithMessage(message)
        extracted = _extract_output_text(response)
        self.assertEqual(extracted, '{"ok": true}')

    def test_parameter_error_detection_handles_invalid_value_code(self):
        exc = Exception(
            "Error code: 400 - {'error': {'message': \"Invalid size '512x512'.\", "
            "'param': 'size', 'code': 'invalid_value'}}"
        )
        self.assertTrue(_is_parameter_error(exc))

    @override_settings(OPENAI_API_KEY="test-key")
    def test_request_outfit_image_retries_with_supported_size(self):
        fake_client = _FakeClient()
        with patch("stylist.openai_client._build_client", return_value=fake_client):
            b64_image, model_name, usage = request_outfit_image(
                prompt="test prompt",
                model="gpt-image-1",
                size="512x512",
                quality="low",
            )

        self.assertEqual(b64_image, "aGVsbG8=")
        self.assertEqual(model_name, "gpt-image-1")
        self.assertEqual(usage, {"total_tokens": 1})
        self.assertEqual(fake_client.images.calls[0]["size"], "512x512")
        self.assertEqual(fake_client.images.calls[1]["size"], "1024x1024")

    @override_settings(OPENAI_API_KEY="test-key")
    def test_request_outfit_image_prefers_reference_edit(self):
        fake_client = _FakeClient()
        with patch("stylist.openai_client._build_client", return_value=fake_client):
            b64_image, model_name, usage = request_outfit_image(
                prompt="test prompt",
                model="gpt-image-1",
                size="1024x1024",
                quality="low",
                reference_image_bytes=b"fake-image-bytes",
                reference_image_filename="closet.jpg",
            )

        self.assertEqual(b64_image, "cmVmZXJlbmNl")
        self.assertEqual(model_name, "gpt-image-1")
        self.assertEqual(usage, {"total_tokens": 2})
        self.assertEqual(len(fake_client.images.edit_calls), 1)
        self.assertEqual(fake_client.images.edit_calls[0]["image"].name, "closet.jpg")
        self.assertEqual(fake_client.images.calls, [])

    @override_settings(OPENAI_API_KEY="test-key")
    def test_request_outfit_image_falls_back_to_generate_after_edit_failure(self):
        fake_client = _FakeClient()
        fake_client.images = _FakeFailingEditImagesAPI()
        with patch("stylist.openai_client._build_client", return_value=fake_client):
            b64_image, model_name, usage = request_outfit_image(
                prompt="test prompt",
                model="gpt-image-1",
                size="1024x1024",
                quality="low",
                reference_image_bytes=b"fake-image-bytes",
                reference_image_filename="closet.jpg",
            )

        self.assertEqual(b64_image, "aGVsbG8=")
        self.assertEqual(model_name, "gpt-image-1")
        self.assertEqual(usage, {"total_tokens": 1})
        self.assertGreaterEqual(len(fake_client.images.edit_calls), 1)
        self.assertEqual(len(fake_client.images.calls), 1)
