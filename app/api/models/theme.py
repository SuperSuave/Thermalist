from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel


class ThemeName(StrEnum):
    FRAMED_FOOD = "framed_food"
    COMPACT = "compact"
    MINIMAL = "minimal"
    BOLD = "bold"
    PLAYFUL = "playful"
    REMINDERS_NOTEBOOK = "reminders_notebook"


class Theme(BaseModel):
    name: ThemeName

    paper_width_px: int
    outer_margin: int
    inner_padding: int
    border_width: int
    corner_radius: int

    header_height: int | None = None
    badge_height: int | None = None
    badge_padding_x: int | None = None
    badge_radius: int | None = None
    section_gap: int | None = None
    text_gap: int | None = None
    rule_gap_above: int | None = None
    rule_gap_below: int | None = None
    footer_gap: int | None = None
    body_spacing: int | None = None
    subtext_spacing: int | None = None

    title_font_size: int
    badge_font_size: int
    body_font_size: int
    subtext_font_size: int | None = None

    background: int = 255
    foreground: int = 0
    threshold: int = 180

    header_text_offset_y: int = 0
    body_start_offset_y: int = 0
    content_shift_y: int = 0

    debug_guides: bool = False
    debug_color: tuple[int, int, int] = (255, 0, 0)

    frame_style: str | None = None
    line_style: str | None = None

    list_rows: int | None = None
    list_has_checkbox: bool = False
    meta_header_labels: tuple[str, str] | None = None


BASE_PAPER_WIDTH = 640


def _get_framed_food_theme() -> Theme:
    return Theme(
        name=ThemeName.FRAMED_FOOD,
        paper_width_px=BASE_PAPER_WIDTH,
        outer_margin=22,
        inner_padding=22,
        border_width=3,
        corner_radius=22,
        header_height=84,
        badge_height=38,
        badge_padding_x=18,
        badge_radius=12,
        section_gap=14,
        text_gap=12,
        rule_gap_above=12,
        rule_gap_below=10,
        footer_gap=10,
        body_spacing=6,
        subtext_spacing=4,
        title_font_size=74,
        badge_font_size=24,
        body_font_size=36,
        subtext_font_size=24,
        background=255,
        foreground=0,
        threshold=180,
        header_text_offset_y=-20,
        body_start_offset_y=15,
        content_shift_y=0,
        debug_guides=False,
        debug_color=(255, 0, 0),
        frame_style="framed",
        line_style="solid",
    )


def _get_compact_theme() -> Theme:
    return Theme(
        name=ThemeName.COMPACT,
        paper_width_px=BASE_PAPER_WIDTH,
        outer_margin=14,
        inner_padding=16,
        border_width=3,
        corner_radius=16,
        header_height=70,
        badge_height=34,
        badge_padding_x=14,
        badge_radius=10,
        section_gap=10,
        text_gap=8,
        rule_gap_above=8,
        rule_gap_below=7,
        footer_gap=8,
        body_spacing=4,
        subtext_spacing=3,
        title_font_size=64,
        badge_font_size=22,
        body_font_size=32,
        subtext_font_size=21,
        background=255,
        foreground=0,
        threshold=180,
        header_text_offset_y=-16,
        body_start_offset_y=10,
        content_shift_y=0,
        debug_guides=False,
        debug_color=(255, 0, 0),
        frame_style="framed",
        line_style="solid",
    )


def _get_minimal_theme() -> Theme:
    return Theme(
        name=ThemeName.MINIMAL,
        paper_width_px=BASE_PAPER_WIDTH,
        outer_margin=12,
        inner_padding=10,
        border_width=0,
        corner_radius=0,
        header_height=48,
        badge_height=28,
        badge_padding_x=8,
        badge_radius=4,
        section_gap=8,
        text_gap=8,
        rule_gap_above=6,
        rule_gap_below=4,
        footer_gap=6,
        body_spacing=4,
        subtext_spacing=3,
        title_font_size=42,
        badge_font_size=18,
        body_font_size=24,
        subtext_font_size=16,
        background=255,
        foreground=0,
        threshold=180,
        header_text_offset_y=-20,
        body_start_offset_y=15,
        content_shift_y=0,
        debug_guides=False,
        debug_color=(255, 0, 0),
        frame_style="minimal",
        line_style="solid",
    )


def _get_bold_theme() -> Theme:
    return Theme(
        name=ThemeName.BOLD,
        paper_width_px=BASE_PAPER_WIDTH,
        outer_margin=28,
        inner_padding=28,
        border_width=6,
        corner_radius=30,
        header_height=100,
        badge_height=48,
        badge_padding_x=22,
        badge_radius=16,
        section_gap=18,
        text_gap=16,
        rule_gap_above=14,
        rule_gap_below=12,
        footer_gap=14,
        body_spacing=8,
        subtext_spacing=6,
        title_font_size=84,
        badge_font_size=28,
        body_font_size=42,
        subtext_font_size=26,
        background=255,
        foreground=0,
        threshold=180,
        header_text_offset_y=-20,
        body_start_offset_y=15,
        content_shift_y=0,
        debug_guides=False,
        debug_color=(255, 0, 0),
        frame_style="bold",
        line_style="solid",
    )


def _get_playful_theme() -> Theme:
    return Theme(
        name=ThemeName.PLAYFUL,
        paper_width_px=BASE_PAPER_WIDTH,
        outer_margin=20,
        inner_padding=24,
        border_width=4,
        corner_radius=36,
        header_height=88,
        badge_height=44,
        badge_padding_x=20,
        badge_radius=20,
        section_gap=16,
        text_gap=14,
        rule_gap_above=12,
        rule_gap_below=10,
        footer_gap=12,
        body_spacing=7,
        subtext_spacing=5,
        title_font_size=66,
        badge_font_size=26,
        body_font_size=34,
        subtext_font_size=22,
        background=255,
        foreground=0,
        threshold=180,
        header_text_offset_y=-20,
        body_start_offset_y=15,
        content_shift_y=0,
        debug_guides=False,
        debug_color=(255, 0, 0),
        frame_style="playful",
        line_style="solid",
    )


def _get_reminders_notebook_theme() -> Theme:
    return Theme(
        name=ThemeName.REMINDERS_NOTEBOOK,
        paper_width_px=BASE_PAPER_WIDTH,
        outer_margin=18,
        inner_padding=18,
        border_width=2,
        corner_radius=8,
        header_height=76,
        badge_height=30,
        badge_padding_x=14,
        badge_radius=6,
        section_gap=8,
        text_gap=8,
        rule_gap_above=8,
        rule_gap_below=6,
        footer_gap=8,
        body_spacing=4,
        subtext_spacing=4,
        title_font_size=58,
        badge_font_size=20,
        body_font_size=28,
        subtext_font_size=20,
        background=255,
        foreground=0,
        threshold=180,
        frame_style="notebook",
        line_style="light",
        list_rows=14,
        list_has_checkbox=True,
        header_text_offset_y=-20,
        body_start_offset_y=15,
        content_shift_y=0,
        debug_guides=False,
        debug_color=(255, 0, 0),
        meta_header_labels=("MONTH", "YEAR"),
    )


THEME_BUILDERS = {
    ThemeName.FRAMED_FOOD: _get_framed_food_theme,
    ThemeName.COMPACT: _get_compact_theme,
    ThemeName.MINIMAL: _get_minimal_theme,
    ThemeName.BOLD: _get_bold_theme,
    ThemeName.PLAYFUL: _get_playful_theme,
    ThemeName.REMINDERS_NOTEBOOK: _get_reminders_notebook_theme,
}


def get_theme(name: ThemeName | str) -> Theme:
    if isinstance(name, str):
        try:
            name = ThemeName(name)
        except ValueError:
            name = ThemeName.REMINDERS_NOTEBOOK

    builder = THEME_BUILDERS.get(name, _get_reminders_notebook_theme)
    return builder()
