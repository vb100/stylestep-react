from __future__ import annotations

import io
import json
import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger("stylist")


class OpenAIIntegrationError(Exception):
    pass


def _build_client():
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - dependency issue
        raise OpenAIIntegrationError("OpenAI SDK is not installed.") from exc

    return OpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.OPENAI_TIMEOUT_SECONDS)


def _resolve_maybe_callable(value: Any) -> Any:
    if not callable(value):
        return value
    try:
        return value()
    except TypeError:
        return value
    except Exception:
        return value


def _get_attr(value: Any, key: str, default: Any = None, resolve_callables: bool = True) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    attr_value = getattr(value, key, default)
    if resolve_callables:
        return _resolve_maybe_callable(attr_value)
    return attr_value


def _serialize_model(value: Any) -> dict | list | str | int | float | None:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, (dict, list, str, int, float, bool)):
        return value
    return str(value)


def _as_non_empty_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _extract_text_candidate(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, dict):
        direct_text = _as_non_empty_text(value.get("text"))
        if direct_text:
            return direct_text
        nested_value = _as_non_empty_text(value.get("value"))
        if nested_value:
            return nested_value
        return None

    text_attr = _get_attr(value, "text")
    if isinstance(text_attr, dict):
        nested_text = _as_non_empty_text(text_attr.get("text"))
        if nested_text:
            return nested_text
        nested_value = _as_non_empty_text(text_attr.get("value"))
        if nested_value:
            return nested_value
    text_attr_text = _as_non_empty_text(text_attr)
    if text_attr_text:
        return text_attr_text

    value_attr = _get_attr(value, "value")
    value_attr_text = _as_non_empty_text(value_attr)
    if value_attr_text:
        return value_attr_text

    return _as_non_empty_text(value)


def _extract_message_structured_candidate(message: Any) -> str | None:
    parsed = _get_attr(message, "parsed")
    if parsed is not None:
        payload = json.dumps(_serialize_model(parsed), ensure_ascii=False)
        payload_text = _as_non_empty_text(payload)
        if payload_text:
            return payload_text

    function_call = _get_attr(message, "function_call")
    if function_call is not None:
        arguments = _as_non_empty_text(_get_attr(function_call, "arguments"))
        if arguments:
            return arguments

    tool_calls = _get_attr(message, "tool_calls", [])
    if tool_calls is None:
        tool_calls = []
    if not isinstance(tool_calls, list):
        tool_calls = [tool_calls]
    for tool_call in tool_calls:
        function_obj = _get_attr(tool_call, "function")
        if function_obj is None:
            continue
        arguments = _as_non_empty_text(_get_attr(function_obj, "arguments"))
        if arguments:
            return arguments

    return None


def _extract_output_text(response: Any) -> str:
    if response is None:
        raise OpenAIIntegrationError("OpenAI response is empty.")

    choices = _get_attr(response, "choices")
    if choices:
        first_choice = choices[0]
        message = _get_attr(first_choice, "message", {})
        structured_candidate = _extract_message_structured_candidate(message)
        if structured_candidate:
            return structured_candidate

        content = _get_attr(message, "content", "")
        if isinstance(content, list):
            parts = []
            for entry in content:
                entry_type = _get_attr(entry, "type")
                if entry_type and entry_type not in {"text", "output_text"}:
                    continue
                maybe_text = _extract_text_candidate(entry)
                if maybe_text:
                    parts.append(maybe_text)
            content = "\n".join(parts).strip()
        elif content is not None:
            content_candidate = _extract_text_candidate(content)
            if content_candidate:
                content = content_candidate
        content_text = _as_non_empty_text(content)
        if content_text:
            return content_text
        refusal = _get_attr(message, "refusal")
        refusal_text = _as_non_empty_text(refusal)
        if refusal_text:
            return refusal_text

        choice_text = _as_non_empty_text(_get_attr(first_choice, "text"))
        if choice_text:
            return choice_text

    output_text = _get_attr(response, "output_text")
    if output_text:
        if isinstance(output_text, (dict, list)):
            payload = json.dumps(_serialize_model(output_text), ensure_ascii=False)
            payload_text = _as_non_empty_text(payload)
            if payload_text:
                return payload_text
        output_text_value = _as_non_empty_text(output_text)
        if output_text_value:
            return output_text_value

    output_items = _get_attr(response, "output", [])
    if isinstance(output_items, dict):
        output_items = [output_items]
    chunks: list[str] = []
    for output in output_items:
        # Handle output objects that directly contain JSON payload.
        output_json = _get_attr(output, "json", resolve_callables=False)
        if output_json is not None:
            payload = json.dumps(_serialize_model(output_json), ensure_ascii=False)
            payload_text = _as_non_empty_text(payload)
            if payload_text:
                return payload_text

        content_items = _get_attr(output, "content", [])
        if isinstance(content_items, dict):
            content_items = [content_items]
        for content in content_items:
            content_type = _get_attr(content, "type")
            if content_type in {"output_json", "json"}:
                content_json = _get_attr(content, "json", resolve_callables=False)
                if content_json is not None:
                    payload = json.dumps(_serialize_model(content_json), ensure_ascii=False)
                    payload_text = _as_non_empty_text(payload)
                    if payload_text:
                        return payload_text
            if content_type not in {"output_text", "text"}:
                continue
            text_value = _get_attr(content, "text")
            if isinstance(text_value, dict):
                text_value = text_value.get("value")
            elif hasattr(text_value, "value"):
                text_value = _get_attr(text_value, "value")
            text_part = _as_non_empty_text(text_value)
            if text_part:
                chunks.append(text_part)

    parsed = _get_attr(response, "parsed")
    if parsed is not None:
        payload = json.dumps(_serialize_model(parsed), ensure_ascii=False)
        payload_text = _as_non_empty_text(payload)
        if payload_text:
            return payload_text

    combined = "\n".join(part.strip() for part in chunks if part).strip()
    if combined:
        return combined

    # Last-resort fallback: return serialized response envelope so downstream
    # normalization/repair can still extract a valid JSON payload.
    serialized = _serialize_model(response)
    if isinstance(serialized, (dict, list)):
        if isinstance(serialized, dict):
            first_choice = None
            choices_value = serialized.get("choices")
            if isinstance(choices_value, list) and choices_value:
                first_choice = choices_value[0]
            finish_reason = None
            if isinstance(first_choice, dict):
                finish_reason = first_choice.get("finish_reason")
            logger.warning(
                "Falling back to serialized response envelope; top-level keys=%s finish_reason=%s",
                sorted(serialized.keys()),
                finish_reason,
            )
        return json.dumps(serialized, ensure_ascii=False)
    if isinstance(serialized, str) and serialized.strip():
        return serialized.strip()
    raise OpenAIIntegrationError("OpenAI response did not include textual output.")


def _collect_metadata(response: Any, fallback_model: str) -> tuple[str, dict | list | str | int | float | None]:
    model_name = _get_attr(response, "model", fallback_model) or fallback_model
    usage = _serialize_model(_get_attr(response, "usage"))
    return str(model_name), usage


def _supports_responses(client: Any) -> bool:
    return hasattr(client, "responses")


def _supports_images(client: Any) -> bool:
    return hasattr(client, "images") and hasattr(client.images, "generate")


def _supports_image_edits(client: Any) -> bool:
    return hasattr(client, "images") and hasattr(client.images, "edit")


def _is_parameter_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "unsupported parameter" in msg
        or "not supported" in msg
        or "unknown parameter" in msg
        or "invalid value" in msg
        or "invalid_value" in msg
        or "invalid size" in msg
        or "invalid quality" in msg
    )


def _supports_max_completion_tokens(exc: Exception) -> bool:
    message = str(exc).lower()
    return "max_tokens" in message and "max_completion_tokens" in message


def _supports_max_tokens(exc: Exception) -> bool:
    message = str(exc).lower()
    return "max_completion_tokens" in message and "max_tokens" in message


def _error_mentions_parameter(exc: Exception, parameter: str) -> bool:
    return parameter.lower() in str(exc).lower()


SUPPORTED_IMAGE_SIZES = ("1024x1024", "1024x1536", "1536x1024", "auto")


def _chat_completion_create_once(*, client: Any, payload: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    try:
        response = client.chat.completions.create(**payload)
        return response, payload
    except Exception as exc:
        # Some models require max_completion_tokens instead of max_tokens.
        if _supports_max_completion_tokens(exc) and "max_tokens" in payload:
            retry_payload = dict(payload)
            retry_payload["max_completion_tokens"] = retry_payload.pop("max_tokens")
            response = client.chat.completions.create(**retry_payload)
            return response, retry_payload

        # Keep compatibility if a model expects max_tokens only.
        if _supports_max_tokens(exc) and "max_completion_tokens" in payload:
            retry_payload = dict(payload)
            retry_payload["max_tokens"] = retry_payload.pop("max_completion_tokens")
            response = client.chat.completions.create(**retry_payload)
            return response, retry_payload

        if _is_parameter_error(exc) and "temperature" in payload and _error_mentions_parameter(exc, "temperature"):
            retry_payload = dict(payload)
            retry_payload.pop("temperature", None)
            response = client.chat.completions.create(**retry_payload)
            return response, retry_payload

        if (
            _is_parameter_error(exc)
            and "response_format" in payload
            and _error_mentions_parameter(exc, "response_format")
        ):
            retry_payload = dict(payload)
            retry_payload.pop("response_format", None)
            response = client.chat.completions.create(**retry_payload)
            return response, retry_payload

        raise


def _chat_finish_reason(response: Any) -> str | None:
    choices = _get_attr(response, "choices", [])
    if isinstance(choices, list) and choices:
        finish_reason = _get_attr(choices[0], "finish_reason")
        if finish_reason is not None:
            return str(finish_reason)
    return None


def _get_chat_token_limit(payload: dict[str, Any]) -> int | None:
    if "max_completion_tokens" in payload:
        value = payload.get("max_completion_tokens")
    else:
        value = payload.get("max_tokens")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _set_chat_token_limit(payload: dict[str, Any], value: int) -> dict[str, Any]:
    updated = dict(payload)
    if "max_completion_tokens" in updated:
        updated["max_completion_tokens"] = value
    else:
        updated["max_tokens"] = value
    return updated


def _create_chat_completion_with_token_fallback(*, client: Any, payload: dict[str, Any]) -> Any:
    max_attempts = 4
    max_limit = 12000
    response, used_payload = _chat_completion_create_once(client=client, payload=payload)

    attempt = 1
    while True:
        finish_reason = (_chat_finish_reason(response) or "").lower()
        if finish_reason != "length":
            return response

        current_limit = _get_chat_token_limit(used_payload) or 2500
        if attempt >= max_attempts or current_limit >= max_limit:
            logger.warning(
                "Chat completion remained truncated after %s attempt(s); last token limit=%s",
                attempt,
                current_limit,
            )
            return response

        retry_limit = min(max(current_limit * 2, current_limit + 1500), max_limit)
        retry_payload = _set_chat_token_limit(used_payload, retry_limit)
        logger.warning(
            "Chat completion truncated (finish_reason=length). Retrying with larger token limit: %s -> %s",
            current_limit,
            retry_limit,
        )
        response, used_payload = _chat_completion_create_once(client=client, payload=retry_payload)
        attempt += 1


def _create_responses_with_fallback(*, client: Any, payload: dict[str, Any]) -> Any:
    attempts: list[dict[str, Any]] = []
    seen_payload_signatures: set[str] = set()

    def _add_attempt(candidate: dict[str, Any]) -> None:
        signature = json.dumps(candidate, sort_keys=True, default=str)
        if signature in seen_payload_signatures:
            return
        seen_payload_signatures.add(signature)
        attempts.append(candidate)

    base_attempt = dict(payload)
    _add_attempt(base_attempt)

    if "text" in base_attempt:
        without_text = dict(base_attempt)
        without_text.pop("text", None)
        _add_attempt(without_text)

    if "max_output_tokens" in base_attempt:
        with_max_completion_tokens = dict(base_attempt)
        with_max_completion_tokens["max_completion_tokens"] = with_max_completion_tokens.pop("max_output_tokens")
        _add_attempt(with_max_completion_tokens)

    if "text" in base_attempt and "max_output_tokens" in base_attempt:
        fallback_payload = dict(base_attempt)
        fallback_payload.pop("text", None)
        fallback_payload["max_completion_tokens"] = fallback_payload.pop("max_output_tokens")
        _add_attempt(fallback_payload)

    if "temperature" in base_attempt:
        current_attempts = list(attempts)
        for attempt in current_attempts:
            without_temperature = dict(attempt)
            without_temperature.pop("temperature", None)
            _add_attempt(without_temperature)

    last_exc: Exception | None = None
    for attempt in attempts:
        try:
            return client.responses.create(**attempt)
        except Exception as exc:
            last_exc = exc
            if not _is_parameter_error(exc):
                raise
            continue

    if last_exc is None:  # pragma: no cover - defensive
        raise OpenAIIntegrationError("Responses API call failed unexpectedly.")
    raise last_exc


def _extract_image_base64(response: Any) -> str:
    data = _get_attr(response, "data", [])
    if isinstance(data, dict):
        data = [data]
    if not data:
        raise OpenAIIntegrationError("Image generation returned empty data.")

    first_item = data[0]
    b64_payload = _get_attr(first_item, "b64_json")
    if b64_payload:
        return str(b64_payload)

    raise OpenAIIntegrationError("Image generation response did not contain b64_json.")


def _build_image_payload_attempts(
    *,
    model: str,
    prompt: str,
    size: str | None,
    quality: str | None,
) -> list[dict[str, Any]]:
    base_payload: dict[str, Any] = {"model": model, "prompt": prompt, "n": 1}
    if size:
        base_payload["size"] = size
    if quality:
        base_payload["quality"] = quality

    attempts: list[dict[str, Any]] = []
    seen_payload_signatures: set[str] = set()

    def _add_attempt(candidate: dict[str, Any]) -> None:
        signature = json.dumps(candidate, sort_keys=True, default=str)
        if signature in seen_payload_signatures:
            return
        seen_payload_signatures.add(signature)
        attempts.append(candidate)

    _add_attempt({**base_payload, "response_format": "b64_json"})

    if size and size not in SUPPORTED_IMAGE_SIZES:
        for fallback_size in ("1024x1024", "auto"):
            fallback_payload = dict(base_payload)
            fallback_payload["size"] = fallback_size
            _add_attempt({**fallback_payload, "response_format": "b64_json"})
            _add_attempt(dict(fallback_payload))

            if "quality" in fallback_payload:
                fallback_without_quality = {k: v for k, v in fallback_payload.items() if k != "quality"}
                _add_attempt({**fallback_without_quality, "response_format": "b64_json"})
                _add_attempt(fallback_without_quality)

    if "quality" in base_payload:
        without_quality = {k: v for k, v in base_payload.items() if k != "quality"}
        _add_attempt({**without_quality, "response_format": "b64_json"})
        _add_attempt(without_quality)

    _add_attempt(dict(base_payload))
    _add_attempt({"model": model, "prompt": prompt, "n": 1, "response_format": "b64_json"})
    _add_attempt({"model": model, "prompt": prompt, "n": 1})

    return attempts


def _build_image_edit_attempts(
    *,
    model: str,
    prompt: str,
    size: str | None,
) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    seen_payload_signatures: set[str] = set()

    def _add_attempt(candidate: dict[str, Any]) -> None:
        signature = json.dumps(candidate, sort_keys=True, default=str)
        if signature in seen_payload_signatures:
            return
        seen_payload_signatures.add(signature)
        attempts.append(candidate)

    base_payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "response_format": "b64_json",
    }
    if size:
        base_payload["size"] = size

    _add_attempt({**base_payload, "extra_body": {"input_fidelity": "high"}})
    _add_attempt(dict(base_payload))

    if size != "1024x1024":
        fallback_payload = dict(base_payload)
        fallback_payload["size"] = "1024x1024"
        _add_attempt({**fallback_payload, "extra_body": {"input_fidelity": "high"}})
        _add_attempt(fallback_payload)

    minimal_payload = {
        "model": model,
        "prompt": prompt,
        "response_format": "b64_json",
    }
    _add_attempt({**minimal_payload, "extra_body": {"input_fidelity": "high"}})
    _add_attempt(minimal_payload)

    return attempts


def _create_reference_image_file(reference_image_bytes: bytes, filename: str) -> io.BytesIO:
    image_file = io.BytesIO(reference_image_bytes)
    image_file.name = filename
    return image_file


def _chat_completion_with_image(
    *,
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
    image_base64_jpeg: str,
) -> Any:
    payload = {
        "model": model,
        "max_tokens": 4000,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64_jpeg}"}},
                ],
            },
        ],
        "response_format": {"type": "json_object"},
    }
    if settings.OPENAI_TEMPERATURE is not None:
        payload["temperature"] = settings.OPENAI_TEMPERATURE

    return _create_chat_completion_with_token_fallback(client=client, payload=payload)


def _chat_completion_text_only(
    *,
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> Any:
    payload = {
        "model": model,
        "max_tokens": 4000,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    if settings.OPENAI_TEMPERATURE is not None:
        payload["temperature"] = settings.OPENAI_TEMPERATURE

    return _create_chat_completion_with_token_fallback(client=client, payload=payload)


def request_primary_json_output(
    *,
    system_prompt: str,
    user_prompt: str,
    image_base64_jpeg: str,
    model: str,
) -> tuple[str, str, dict | list | str | int | float | None]:
    if not settings.OPENAI_API_KEY:
        raise OpenAIIntegrationError("OPENAI_API_KEY is not configured.")

    client = _build_client()
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user_prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_base64_jpeg}",
                    },
                ],
            },
        ],
        "max_output_tokens": 4000,
        "text": {"format": {"type": "json_object"}},
    }
    if settings.OPENAI_TEMPERATURE is not None:
        payload["temperature"] = settings.OPENAI_TEMPERATURE

    try:
        if _supports_responses(client):
            response = _create_responses_with_fallback(client=client, payload=payload)
        else:
            response = _chat_completion_with_image(
                client=client,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                image_base64_jpeg=image_base64_jpeg,
            )
    except Exception as exc:
        raise OpenAIIntegrationError(f"Primary OpenAI request failed: {exc}") from exc

    try:
        return _extract_output_text(response), *_collect_metadata(response, fallback_model=model)
    except OpenAIIntegrationError as exc:
        if not _supports_responses(client):
            raise
        try:
            fallback_response = _chat_completion_with_image(
                client=client,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                image_base64_jpeg=image_base64_jpeg,
            )
            return _extract_output_text(fallback_response), *_collect_metadata(fallback_response, fallback_model=model)
        except Exception:
            raise exc


def request_json_repair(
    *,
    system_prompt: str,
    repair_prompt: str,
    model: str,
) -> tuple[str, str, dict | list | str | int | float | None]:
    if not settings.OPENAI_API_KEY:
        raise OpenAIIntegrationError("OPENAI_API_KEY is not configured.")

    client = _build_client()
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": repair_prompt}],
            },
        ],
        "max_output_tokens": 4000,
        "text": {"format": {"type": "json_object"}},
    }
    if settings.OPENAI_TEMPERATURE is not None:
        payload["temperature"] = settings.OPENAI_TEMPERATURE

    try:
        if _supports_responses(client):
            response = _create_responses_with_fallback(client=client, payload=payload)
        else:
            response = _chat_completion_text_only(
                client=client,
                model=model,
                system_prompt=system_prompt,
                user_prompt=repair_prompt,
            )
    except Exception as exc:
        raise OpenAIIntegrationError(f"JSON repair OpenAI request failed: {exc}") from exc

    try:
        return _extract_output_text(response), *_collect_metadata(response, fallback_model=model)
    except OpenAIIntegrationError as exc:
        if not _supports_responses(client):
            raise
        try:
            fallback_response = _chat_completion_text_only(
                client=client,
                model=model,
                system_prompt=system_prompt,
                user_prompt=repair_prompt,
            )
            return _extract_output_text(fallback_response), *_collect_metadata(fallback_response, fallback_model=model)
        except Exception:
            raise exc


def request_outfit_image(
    *,
    prompt: str,
    model: str,
    size: str | None,
    quality: str | None,
    reference_image_bytes: bytes | None = None,
    reference_image_filename: str = "reference.jpg",
) -> tuple[str, str, dict | list | str | int | float | None]:
    if not settings.OPENAI_API_KEY:
        raise OpenAIIntegrationError("OPENAI_API_KEY is not configured.")

    client = _build_client()
    if not _supports_images(client):
        raise OpenAIIntegrationError("OpenAI SDK client does not support image generation.")

    if reference_image_bytes and _supports_image_edits(client):
        edit_attempts = _build_image_edit_attempts(
            model=model,
            prompt=prompt,
            size=size,
        )
        last_edit_exc: Exception | None = None

        for payload in edit_attempts:
            edit_payload = dict(payload)
            edit_payload["image"] = _create_reference_image_file(reference_image_bytes, reference_image_filename)
            try:
                response = client.images.edit(**edit_payload)
                return _extract_image_base64(response), *_collect_metadata(response, fallback_model=model)
            except Exception as exc:
                last_edit_exc = exc
                logger.warning(
                    "Reference image edit attempt failed model=%s size=%s response_format=%s error=%s",
                    payload.get("model"),
                    payload.get("size"),
                    payload.get("response_format"),
                    exc,
                )
                if not _is_parameter_error(exc):
                    break

        if last_edit_exc is not None:
            logger.warning(
                "Falling back to text-only image generation after reference edit failure: %s",
                last_edit_exc,
            )

    payload_attempts = _build_image_payload_attempts(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
    )

    last_exc: Exception | None = None
    response: Any = None
    for payload in payload_attempts:
        try:
            response = client.images.generate(**payload)
            break
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Image generation attempt failed model=%s size=%s quality=%s response_format=%s error=%s",
                payload.get("model"),
                payload.get("size"),
                payload.get("quality"),
                payload.get("response_format"),
                exc,
            )
            if not _is_parameter_error(exc):
                raise OpenAIIntegrationError(f"Outfit image generation failed: {exc}") from exc
            continue

    if response is None:
        raise OpenAIIntegrationError(f"Outfit image generation failed: {last_exc}")

    return _extract_image_base64(response), *_collect_metadata(response, fallback_model=model)
