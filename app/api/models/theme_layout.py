from __future__ import annotations

from enum import StrEnum
from typing import Any, Annotated, Literal, Union

from pydantic import BaseModel, Field

from app.api.models.theme import Theme


class Align(StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class RepeatDirection(StrEnum):
    DOWN = "down"
    RIGHT = "right"


class ThemeStyle(BaseModel):
    name: str

    # Directly mirror relevant Theme fields so renderers
    # can use them without re-resolving Theme.
    title_font_size: int = 58
    body_font_size: int = 28
    badge_font_size: int = 20
    subtext_font_size: int | None = None

    border_width: int = 2
    corner_radius: int = 12
    foreground: int = 0
    background: int = 255
    threshold: int = 180

    # Geometry copied from Theme – needed for Quick Verb
    header_height: int | None = None
    badge_height: int | None = None
    badge_padding_x: int | None = None
    badge_radius: int | None = None
    section_gap: int | None = None
    rule_gap_above: int | None = None
    rule_gap_below: int | None = None
    footer_gap: int | None = None
    body_spacing: int | None = None
    subtext_spacing: int | None = None

    # Behavior / hints
    header_text_offset_y: int = 0
    body_start_offset_y: int = 0
    content_shift_y: int = 0

    frame_style: str | None = None
    line_style: str | None = None

    debug_guides: bool = False
    debug_color: tuple[int, int, int] = (255, 0, 0)
    debug_margin_px: int = 8


class GridColumn(BaseModel):
    label: str | None = None
    width: float = 1.0
    align: Align = Align.LEFT
    props: dict[str, Any] = Field(default_factory=dict)


class ListColumn(BaseModel):
    type: Literal["text", "checkbox", "badge"] = "text"
    label: str | None = None
    width: float = 1.0
    align: Align = Align.LEFT
    props: dict[str, Any] = Field(default_factory=dict)


class LayoutElementBase(BaseModel):
    x: int = 0
    y: int = 0
    width: int | None = None
    height: int | None = None
    repeat: int = 1
    repeat_direction: RepeatDirection = RepeatDirection.DOWN
    gap: int = 0
    align: Align = Align.LEFT
    visible: bool = True
    props: dict[str, Any] = Field(default_factory=dict)


class ListRowData(BaseModel):
    values: list[str] = Field(default_factory=list)
    checked: list[bool] = Field(default_factory=list)


class RenderPayload(BaseModel):
    title: str | None = None
    rows: list[ListRowData] = Field(default_factory=list)
    values: dict[str, Any] = Field(default_factory=dict)


class RenderRequest(BaseModel):
    layout: LabelLayout
    payload: RenderPayload


class TitleElement(LayoutElementBase):
    type: Literal["title"] = "title"


class TextElement(LayoutElementBase):
    type: Literal["text"] = "text"


class BadgeElement(LayoutElementBase):
    type: Literal["badge"] = "badge"


class LineElement(LayoutElementBase):
    type: Literal["line"] = "line"


class BoxElement(LayoutElementBase):
    type: Literal["box"] = "box"


class GridElement(LayoutElementBase):
    type: Literal["grid"] = "grid"
    columns: list[GridColumn] = Field(default_factory=list)


class ListElement(LayoutElementBase):
    type: Literal["list"] = "list"
    columns: list[ListColumn] = Field(default_factory=list)


class CheckBoxElement(LayoutElementBase):
    type: Literal["checkbox"] = "checkbox"


class ImageElement(LayoutElementBase):
    type: Literal["image"] = "image"
    props: dict[str, Any] = Field(default_factory=dict)


ThemeElement = Annotated[
    Union[
        TitleElement,
        TextElement,
        BadgeElement,
        LineElement,
        BoxElement,
        GridElement,
        ListElement,
        CheckBoxElement,
        ImageElement,
    ],
    Field(discriminator="type"),
]


class LabelLayout(BaseModel):
    name: str
    kind: str = "generic"  # e.g. "generic", "quickverb", "notebook"
    paper_width_px: int = 640
    outer_margin: int = 18
    inner_padding: int = 18
    elements: list[ThemeElement] = Field(default_factory=list)
