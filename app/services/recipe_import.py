from __future__ import annotations

from html.parser import HTMLParser
import ipaddress
import json
import re
import socket
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.models import RecipeIngredient, RecipeItem, RecipeStep


class RecipeImportError(Exception):
    pass


class _JSONLDParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self._in_script = False
        self._current_script: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script":
            attr_dict = {k.lower(): v for k, v in attrs if v is not None}
            if attr_dict.get("type", "").lower() == "application/ld+json":
                self._in_script = True
                self._current_script = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_script:
            script_text = "".join(self._current_script).strip()
            if script_text:
                self.scripts.append(script_text)
            self._in_script = False
            self._current_script = []

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._current_script.append(data)


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


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise RecipeImportError("Only HTTP and HTTPS URLs are allowed")

    hostname = parsed.hostname
    if not hostname:
        raise RecipeImportError("Invalid URL: missing hostname")

    hostname = hostname.strip("[]")

    try:
        try:
            ip = ipaddress.ip_address(hostname)
            _check_ip_allowed(ip)
            return
        except ValueError as exc:
            if "not allowed" in str(exc):
                raise RecipeImportError(str(exc)) from exc

        addr_info = socket.getaddrinfo(hostname, None)
        if not addr_info:
            raise RecipeImportError("Could not resolve URL hostname")

        for family, type_, proto, canonname, sockaddr in addr_info:
            ip = ipaddress.ip_address(sockaddr[0])
            _check_ip_allowed(ip)
    except socket.gaierror as exc:
        raise RecipeImportError(f"Failed to resolve URL hostname: {exc}") from exc


def _check_ip_allowed(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_unspecified
        or ip.is_multicast
    ):
        raise RecipeImportError(f"Access to private/local IP address ({ip}) is not allowed")


async def _fetch_html(url: str) -> str:
    _validate_url(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=15.0, headers=headers) as client:
            current_url = url
            for _ in range(5):
                response = await client.get(current_url)
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise RecipeImportError("Redirect missing Location header")
                    next_url = str(response.url.join(location))
                    _validate_url(next_url)
                    current_url = next_url
                else:
                    response.raise_for_status()
                    return response.text

            raise RecipeImportError("Too many redirects")
    except httpx.HTTPError as exc:
        raise RecipeImportError(f"Failed to fetch recipe URL: {exc}") from exc


def _extract_recipe_jsonld(html: str) -> dict[str, Any] | None:
    parser = _JSONLDParser()
    parser.feed(html)

    for raw in parser.scripts:
        for parsed in _parse_json_candidates(raw):
            recipe = _find_recipe_object(parsed)
            if recipe:
                return recipe

    return None


def _parse_json_candidates(raw: str) -> list[Any]:
    try:
        return [json.loads(raw)]
    except json.JSONDecodeError:
        cleaned = re.sub(r"<!--|-->", "", raw).strip()
        try:
            return [json.loads(cleaned)]
        except json.JSONDecodeError:
            return []


def _find_recipe_object(node: Any) -> dict[str, Any] | None:
    if isinstance(node, dict):
        if _is_recipe_type(node.get("@type")):
            return node

        for key in ("@graph", "mainEntity", "itemListElement"):
            val = node.get(key)
            if val:
                found = _find_recipe_object(val)
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
        if isinstance(item, str) and item.strip():
            ingredients.append(RecipeIngredient(text=item.strip(), original_text=item.strip()))
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
        return _as_text(item.get("text")) or ""

    parts = [_as_text(item.get("value")), _as_text(item.get("unitText")) or _as_text(item.get("unitCode")), _as_text(item.get("name"))]
    return " ".join(p for p in parts if p).strip()


def _normalize_instructions(value: Any) -> list[RecipeStep]:
    if not value:
        return []

    lines = _flatten_instruction_nodes(value)
    return [
        RecipeStep(number=idx, text=node["text"].strip(), metadata=node.get("metadata", {}))
        for idx, node in enumerate(lines, start=1)
        if node["text"].strip()
    ]


def _flatten_instruction_nodes(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, str):
        return [{"text": p.strip(), "metadata": {}} for p in value.splitlines() if p.strip()]

    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(_flatten_instruction_nodes(item))
        return out

    if isinstance(value, dict):
        node_type = value.get("@type")
        if node_type == "HowToStep":
            text = _as_text(value.get("text")) or _as_text(value.get("name"))
            return [{"text": text, "metadata": {"source": value}}] if text else []

        if node_type == "HowToSection":
            out = []
            section_name = _as_text(value.get("name"))
            if section_name:
                out.append({"text": section_name, "metadata": {"section_heading": True, "source": value}})
            steps = value.get("itemListElement") or value.get("steps")
            out.extend(_flatten_instruction_nodes(steps))
            return out

        if "text" in value or "name" in value:
            text = _as_text(value.get("text")) or _as_text(value.get("name"))
            return [{"text": text, "metadata": {"source": value}}] if text else []

        for k in ("itemListElement", "steps"):
            if k in value:
                return _flatten_instruction_nodes(value.get(k))

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

    parts = []
    if hours:
        parts.append(f"{hours} hr")
    if minutes:
        parts.append(f"{minutes} min")
    if seconds and not parts:
        parts.append(f"{seconds} sec")

    return " ".join(parts) if parts else text


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float)):
        s = str(value).strip()
        return s or None
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
    slug = path.split("/")[-1].replace("-", " ").replace("_", " ").strip()
    return slug.title() if slug else "Imported Recipe"


def _build_recipe_id(url: str, title: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"url-{host}-{slug}" if slug else f"url-{host}"
