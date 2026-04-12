from functools import lru_cache
from string import Template

from django.conf import settings

MAX_REPAIR_INVALID_JSON_CHARS = 8000


@lru_cache(maxsize=8)
def load_prompt_file(filename: str) -> str:
    prompt_path = settings.BASE_DIR / "prompts" / filename
    return prompt_path.read_text(encoding="utf-8")


def render_user_prompt(*, season: str, occasion: str, style: str, additional_info: str) -> str:
    template = Template(load_prompt_file("user_prompt_template.txt"))
    return template.safe_substitute(
        season=season,
        occasion=occasion,
        style=style,
        additional_info=additional_info or "N/A",
    )


def render_json_repair_prompt(*, invalid_json: str, validation_error: str) -> str:
    template = Template(load_prompt_file("json_repair_prompt.txt"))
    if len(invalid_json) > MAX_REPAIR_INVALID_JSON_CHARS:
        truncated_chars = len(invalid_json) - MAX_REPAIR_INVALID_JSON_CHARS
        invalid_json = (
            f"{invalid_json[:MAX_REPAIR_INVALID_JSON_CHARS]}\n"
            f"...[TRUNCATED {truncated_chars} chars]"
        )
    return template.safe_substitute(
        invalid_json=invalid_json,
        validation_error=validation_error,
    )


def render_outfit_image_prompt(
    *,
    season: str,
    occasion: str,
    style: str,
    selected_outfit_json: str,
    detected_items_json: str,
    to_buy_json: str,
) -> str:
    template = Template(load_prompt_file("outfit_image_prompt_template.txt"))
    return template.safe_substitute(
        season=season,
        occasion=occasion,
        style=style,
        selected_outfit_json=selected_outfit_json,
        detected_items_json=detected_items_json,
        to_buy_json=to_buy_json,
    )
