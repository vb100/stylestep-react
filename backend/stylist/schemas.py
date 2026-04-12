import json
from typing import Any
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class OutfitItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detected_item_id: str
    role: str


class OutfitOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    items: list[OutfitItem]
    why_it_works: str
    fit_notes: str
    color_notes: str


class OutfitCollection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    safe: OutfitOption
    bold: OutfitOption
    creative: OutfitOption


class DetectedItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    category: Literal["top", "bottom", "outerwear", "dress", "shoes", "accessory", "other"]
    colors: list[str]
    pattern: str | None = None
    material: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str | None = None


class ToBuyItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    why_needed: str
    google_query: str
    priority: Literal["must", "nice_to_have"]


class AdviceBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    style: list[str]
    care: list[str]
    impression: list[str]


class StylingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detected_items: list[DetectedItem]
    outfits: OutfitCollection
    to_buy: list[ToBuyItem]
    advice: AdviceBlock

    @model_validator(mode="after")
    def validate_detected_item_references(self):
        valid_ids = {item.id for item in self.detected_items}
        for option in (self.outfits.safe, self.outfits.bold, self.outfits.creative):
            for item in option.items:
                if item.detected_item_id not in valid_ids:
                    raise ValueError(
                        f"outfits item references unknown detected_item_id={item.detected_item_id}"
                    )
        return self


REQUIRED_TOP_LEVEL_KEYS = {"detected_items", "outfits", "to_buy", "advice"}


def _looks_like_schema_payload(value: Any) -> bool:
    return isinstance(value, dict) and REQUIRED_TOP_LEVEL_KEYS.issubset(set(value.keys()))


def _normalize_potentially_wrapped_json(value: Any) -> Any:
    current = value
    for _ in range(6):
        if not isinstance(current, str):
            break
        stripped = current.strip()
        if not stripped:
            return {}
        try:
            current = json.loads(stripped)
        except json.JSONDecodeError:
            break
    return current


def _as_non_empty_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _extract_content_from_chat_envelope(data: dict) -> Any:
    choices = data.get("choices")
    if not isinstance(choices, list):
        return data

    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message", {})
        if isinstance(message, dict):
            parsed = message.get("parsed")
            if parsed is not None:
                return parsed

            function_call = message.get("function_call")
            if isinstance(function_call, dict):
                arguments = _as_non_empty_string(function_call.get("arguments"))
                if arguments:
                    return arguments

            tool_calls = message.get("tool_calls")
            if isinstance(tool_calls, list):
                for tool_call in tool_calls:
                    if not isinstance(tool_call, dict):
                        continue
                    function_obj = tool_call.get("function")
                    if not isinstance(function_obj, dict):
                        continue
                    arguments = _as_non_empty_string(function_obj.get("arguments"))
                    if arguments:
                        return arguments

            content = message.get("content")
            if isinstance(content, str):
                content_value = _as_non_empty_string(content)
                if content_value:
                    return content_value
            if isinstance(content, dict):
                for key in ("json", "content", "text", "value"):
                    if key in content:
                        return content[key]
            if isinstance(content, list):
                text_parts: list[str] = []
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    item_type = item.get("type")
                    if item_type and item_type not in {"text", "output_text"}:
                        continue

                    maybe_text = item.get("text")
                    maybe_text_value = _as_non_empty_string(maybe_text)
                    if maybe_text_value:
                        text_parts.append(maybe_text_value)
                        continue

                    if isinstance(maybe_text, dict):
                        nested_value = _as_non_empty_string(maybe_text.get("value"))
                        if nested_value:
                            text_parts.append(nested_value)
                if text_parts:
                    return "\n".join(text_parts)

            refusal = _as_non_empty_string(message.get("refusal"))
            if refusal:
                return refusal

        legacy_choice_text = _as_non_empty_string(choice.get("text"))
        if legacy_choice_text:
            return legacy_choice_text

    return data


def _extract_content_from_responses_envelope(data: dict) -> Any:
    output_text = data.get("output_text")
    if isinstance(output_text, str):
        output_text_value = _as_non_empty_string(output_text)
        if output_text_value:
            return output_text_value
    if isinstance(output_text, dict):
        output_text_value = _as_non_empty_string(output_text.get("value"))
        if output_text_value:
            return output_text_value

    output = data.get("output")
    if isinstance(output, list):
        text_parts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content_items = item.get("content")
            if not isinstance(content_items, list):
                continue
            for content in content_items:
                if not isinstance(content, dict):
                    continue
                content_type = content.get("type")
                if content_type in {"output_text", "text"}:
                    text_value = content.get("text")
                    text_candidate = _as_non_empty_string(text_value)
                    if text_candidate:
                        text_parts.append(text_candidate)
                    elif isinstance(text_value, dict):
                        nested_candidate = _as_non_empty_string(text_value.get("value"))
                        if nested_candidate:
                            text_parts.append(nested_candidate)
                if content_type in {"output_json", "json"} and content.get("json") is not None:
                    return content.get("json")
        if text_parts:
            return "\n".join(text_parts)
    return data


def _normalize_ai_output_payload(raw_json: str) -> Any:
    data: Any = _normalize_potentially_wrapped_json(raw_json)
    for _ in range(6):
        previous = data
        if isinstance(data, dict):
            if {"detected_items", "outfits", "to_buy", "advice"}.issubset(set(data.keys())):
                return data
            data = _extract_content_from_chat_envelope(data)
            if data is previous:
                data = _extract_content_from_responses_envelope(data)
        data = _normalize_potentially_wrapped_json(data)
        if data is previous:
            break
    if isinstance(data, str) and not data.strip():
        return {}
    return data


def _deep_find_schema_payload(value: Any, depth: int = 0) -> dict | None:
    if depth > 20:
        return None

    current = _normalize_potentially_wrapped_json(value)
    if _looks_like_schema_payload(current):
        return current

    if isinstance(current, dict):
        priority_keys = ("parsed", "json", "output_text", "content", "text", "value", "choices", "message", "output")
        for key in priority_keys:
            if key in current:
                found = _deep_find_schema_payload(current[key], depth + 1)
                if found is not None:
                    return found

        for nested_value in current.values():
            found = _deep_find_schema_payload(nested_value, depth + 1)
            if found is not None:
                return found
        return None

    if isinstance(current, list):
        for nested_value in current:
            found = _deep_find_schema_payload(nested_value, depth + 1)
            if found is not None:
                return found
        return None

    return None


def has_schema_payload(raw_json: str) -> bool:
    data = _normalize_ai_output_payload(raw_json)
    if _looks_like_schema_payload(data):
        return True
    return _deep_find_schema_payload(data) is not None


def validate_ai_json(raw_json: str) -> StylingResult:
    data = _normalize_ai_output_payload(raw_json)
    if _looks_like_schema_payload(data):
        return StylingResult.model_validate(data)

    extracted = _deep_find_schema_payload(data)
    if extracted is not None:
        return StylingResult.model_validate(extracted)

    return StylingResult.model_validate(data)


def try_validate_ai_json(raw_json: str) -> tuple[StylingResult | None, ValidationError | ValueError | None]:
    try:
        validated = validate_ai_json(raw_json)
        return validated, None
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        return None, exc
