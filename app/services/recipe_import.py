from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.models import RecipeIngredient, RecipeItem, RecipeStep


class RecipeImportError(Exception):
    pass


async def import_recipe_from_url(url: str) -> RecipeItem:
    html = await _fetch_html(url)
    recipe_data = _extract_recipe_jsonld(html)

    if not recipe_data:
        raise RecipeImportError("No recipe metadata found at this URL")

    title = _as_text(recipe_data.get("name")) or _fallback_title_from_url(url)
    if not title:
        raise RecipeImportError("Recipe title could not be determined")

    description = _as_text(recipe_data.get("description")) or None
    servings = _normalize_servings(recipe_data.get("recipeYield"))
    prep_time = _normalize_duration(recipe_data.get("prepTime"))
    cook_time = _normalize_duration(recipe_data.get("cookTime"))
    total_time = _normalize_duration(recipe_data.get("totalTime"))

    ingredients = _normalize_ingredients(recipe_data.get("recipeIngredient"))
    steps = _normalize_instructions(recipe_data.get("recipeInstructions"))

    if not ingredients and not steps:
        raise RecipeImportError("Recipe metadata was found, but no ingredients or steps were available")

    recipe_id = _build_recipe_id(url, title)

    return RecipeItem(
        id=recipe_id,
        title=title,
        description=description,
        servings=servings,
        prep_time=prep_time,
        cook_time=cook_time,
        total_time=total_time,
        source_url=url,
        ingredients=ingredients,
        steps=steps,
        labels=[],
    )


async def _fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://www.google.com/",
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as exc:
        raise RecipeImportError(f"Failed to fetch recipe URL: {exc}") from exc


def _extract_recipe_jsonld(html: str) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})

    for script in scripts:
        raw = script.string or script.get_text(strip=True) or ""
        if not raw:
            continue

        for parsed in _parse_json_candidates(raw):
            recipe = _find_recipe_object(parsed)
            if recipe:
                return recipe

    return None


def _parse_json_candidates(raw: str) -> list[Any]:
    candidates: list[Any] = []

    try:
        candidates.append(json.loads(raw))
        return candidates
    except json.JSONDecodeError:
        pass

    cleaned = raw.strip()
    cleaned = re.sub(r"<!--|-->", "", cleaned).strip()

    try:
        candidates.append(json.loads(cleaned))
    except json.JSONDecodeError:
        return []

    return candidates


def _find_recipe_object(node: Any) -> dict[str, Any] | None:
    if isinstance(node, dict):
        node_type = node.get("@type")
        if _is_recipe_type(node_type):
            return node

        graph = node.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                found = _find_recipe_object(item)
                if found:
                    return found

        main_entity = node.get("mainEntity")
        if main_entity:
            found = _find_recipe_object(main_entity)
            if found:
                return found

        item_list = node.get("itemListElement")
        if isinstance(item_list, list):
            for item in item_list:
                found = _find_recipe_object(item)
                if found:
                    return found

    elif isinstance(node, list):
        for item in node:
            found = _find_recipe_object(item)
            if found:
                return found

    return None


def _is_recipe_type(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "recipe"
    if isinstance(value, list):
        return any(isinstance(v, str) and v.lower() == "recipe" for v in value)
    return False


def _normalize_ingredients(value: Any) -> list[RecipeIngredient]:
    if not value:
        return []

    items = value if isinstance(value, list) else [value]
    ingredients: list[RecipeIngredient] = []

    for item in items:
        if isinstance(item, str):
            text = item.strip()
            if text:
                ingredients.append(
                    RecipeIngredient(
                        text=text,
                        quantity=None,
                        unit=None,
                        item=None,
                        note=None,
                        original_text=text,
                        metadata={},
                    )
                )
        elif isinstance(item, dict):
            text = _ingredient_text_from_dict(item)
            if text:
                ingredients.append(
                    RecipeIngredient(
                        text=text,
                        quantity=_as_text(item.get("value")) or _as_text(item.get("amount")),
                        unit=_as_text(item.get("unitText")) or _as_text(item.get("unitCode")),
                        item=_as_text(item.get("name")),
                        note=_as_text(item.get("description")) or _as_text(item.get("note")),
                        original_text=_as_text(item.get("text")) or text,
                        metadata={"source": item},
                    )
                )

    return ingredients


def _ingredient_text_from_dict(item: dict[str, Any]) -> str:
    if _as_text(item.get("text")):
        return _as_text(item.get("text"))

    value = _as_text(item.get("value"))
    unit = _as_text(item.get("unitText")) or _as_text(item.get("unitCode"))
    name = _as_text(item.get("name"))

    parts = [p for p in [value, unit, name] if p]
    return " ".join(parts).strip()


def _normalize_instructions(value: Any) -> list[RecipeStep]:
    if not value:
        return []

    lines = _flatten_instruction_nodes(value)
    steps: list[RecipeStep] = []

    for idx, node in enumerate(lines, start=1):
        text = node["text"].strip()
        if text:
            steps.append(
                RecipeStep(
                    number=idx,
                    text=text,
                    metadata=node.get("metadata", {}),
                )
            )

    return steps


def _flatten_instruction_nodes(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, str):
        parts = [part.strip() for part in value.splitlines()]
        return [{"text": part, "metadata": {}} for part in parts if part]

    if isinstance(value, list):
        output: list[dict[str, Any]] = []
        for item in value:
            output.extend(_flatten_instruction_nodes(item))
        return output

    if isinstance(value, dict):
        node_type = value.get("@type")

        if node_type == "HowToStep":
            text = _as_text(value.get("text")) or _as_text(value.get("name"))
            return [{"text": text, "metadata": {"source": value}}] if text else []

        if node_type == "HowToSection":
            output: list[dict[str, Any]] = []
            section_name = _as_text(value.get("name"))
            if section_name:
                output.append(
                    {"text": section_name, "metadata": {"section_heading": True, "source": value}}
                )

            steps = value.get("itemListElement") or value.get("steps")
            output.extend(_flatten_instruction_nodes(steps))
            return output

        if "text" in value or "name" in value:
            text = _as_text(value.get("text")) or _as_text(value.get("name"))
            return [{"text": text, "metadata": {"source": value}}] if text else []

        if "itemListElement" in value:
            return _flatten_instruction_nodes(value.get("itemListElement"))

        if "steps" in value:
            return _flatten_instruction_nodes(value.get("steps"))

    return []


def _normalize_servings(value: Any) -> int | None:
    text = _as_text(value)
    if not text:
        return None

    match = re.search(r"\d+", text)
    return int(match.group()) if match else None


def _normalize_duration(value: Any) -> str | None:
    text = _as_text(value)
    if not text:
        return None

    iso_match = re.fullmatch(
        r"P(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)",
        text,
        flags=re.IGNORECASE,
    )
    if not iso_match:
        return text

    hours = int(iso_match.group("hours") or 0)
    minutes = int(iso_match.group("minutes") or 0)
    seconds = int(iso_match.group("seconds") or 0)

    parts: list[str] = []
    if hours:
        parts.append(f"{hours} hr" if hours == 1 else f"{hours} hr")
    if minutes:
        parts.append(f"{minutes} min")
    if seconds and not parts:
        parts.append(f"{seconds} sec")

    return " ".join(parts) if parts else text


def _as_text(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        return value or None

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, list):
        parts = [_as_text(v) for v in value]
        parts = [p for p in parts if p]
        return ", ".join(parts) if parts else None

    if isinstance(value, dict):
        for key in ("name", "text", "@value"):
            if key in value:
                return _as_text(value.get(key))

    return None


def _fallback_title_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "Imported Recipe"

    slug = path.split("/")[-1]
    slug = slug.replace("-", " ").replace("_", " ").strip()
    return slug.title() if slug else "Imported Recipe"


def _build_recipe_id(url: str, title: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"url-{host}-{slug}" if slug else f"url-{host}"
