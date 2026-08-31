from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Iterable
import warnings

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = PROJECT_ROOT / "fonts"
DEFAULT_TITLE_FONT_PATH = FONT_DIR / "Dongle-Regular.ttf"
DEFAULT_BODY_FONT_PATH = FONT_DIR / "ElmsSans-Regular.ttf"


@dataclass
class LabelTheme:
    paper_width_px: int = 576
    outer_margin: int = 22
    inner_padding: int = 22
    border_width: int = 3
    corner_radius: int = 22
    header_height: int = 84
    badge_height: int = 38
    badge_padding_x: int = 18
    badge_radius: int = 12
    section_gap: int = 14
    text_gap: int = 12
    rule_gap_above: int = 12
    rule_gap_below: int = 10
    footer_gap: int = 10
    body_spacing: int = 6
    subtext_spacing: int = 4
    title_font_size: int = 74
    badge_font_size: int = 24
    body_font_size: int = 36
    subtext_font_size: int = 24
    background: int = 255
    foreground: int = 0
    threshold: int = 180
    header_text_offset_y: int = 0
    body_start_offset_y: int = 0
    content_shift_y: int = 0
    debug_guides: bool = False
    debug_color: tuple[int, int, int] = (255, 0, 0)
    debug_margin_px: int = 8
    frame_style: str = "framed"
    line_style: str = "solid"
    list_rows: int | None = None
    list_has_checkbox: bool = False
    meta_header_labels: tuple[str, str] | None = None


class LabelThemeName(StrEnum):
    FRAMED_FOOD = ("framed_food", "Framed Food (default)")
    MINIMAL = ("minimal", "Minimal (top/bottom lines only)")
    COMPACT = ("compact", "Compact")
    BOLD = ("bold", "Bold (thick frame)")
    PLAYFUL = ("playful", "Playful (rounded, softer)")
    REMINDERS_NOTEBOOK = ("reminders_notebook", "Reminders Notebook")

    def __new__(cls, value: str, label: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.label = label
        return obj


def get_theme(name: LabelThemeName | str) -> LabelTheme:
    if isinstance(name, str):
        name = LabelThemeName(name)

    base_paper = 640

    if name == LabelThemeName.FRAMED_FOOD:
        return LabelTheme(
            paper_width_px=base_paper,
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
        )
    if name == LabelThemeName.MINIMAL:
        return LabelTheme(
            paper_width_px=base_paper,
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
        )
    if name == LabelThemeName.BOLD:
        return LabelTheme(
            paper_width_px=base_paper,
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
        )
    if name == LabelThemeName.PLAYFUL:
        return LabelTheme(
            paper_width_px=base_paper,
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
        )

    if name == LabelThemeName.REMINDERS_NOTEBOOK:
        return LabelTheme(
            paper_width_px=base_paper,
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


class FontSet:
    def __init__(self, title_path: str | None = None, body_path: str | None = None):
        self.title_path = str(title_path or DEFAULT_TITLE_FONT_PATH)
        self.body_path = str(body_path or DEFAULT_BODY_FONT_PATH)

        if not Path(self.title_path).exists():
            warnings.warn(
                f"Title font not found at {self.title_path}. Falling back to Pillow default font."
            )
            self.title_path = None

        if not Path(self.body_path).exists():
            warnings.warn(
                f"Body font not found at {self.body_path}. Falling back to Pillow default font."
            )
            self.body_path = None

    def _load_font(self, path: str | None, size: int) -> ImageFont.ImageFont:
        if path and Path(path).exists():
            return ImageFont.truetype(str(path), size=size)
        return ImageFont.load_default()

    def title(self, size: int) -> ImageFont.ImageFont:
        return self._load_font(self.title_path, size)

    def body(self, size: int) -> ImageFont.ImageFont:
        return self._load_font(self.body_path, size)


def fit_font_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str | None,
    max_width: int,
    start: int,
    min_size: int = 14,
) -> ImageFont.ImageFont:
    if not font_path or not Path(font_path).exists():
        return ImageFont.load_default()
    size = start
    while size >= min_size:
        font = ImageFont.truetype(str(font_path), size=size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 1
    return ImageFont.truetype(str(font_path), size=min_size)


@dataclass
class LabelData:
    verb: str
    date_text: str
    body: str
    subtext: str | None = None


def wrap_text(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int
) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    words = text.split(" ")
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word]) if current else word
        if draw.textlength(trial, font=font) <= max_width:
            current.append(word)
            continue
        if current:
            lines.append(" ".join(current))
            current = [word]
            continue
        chunk = ""
        for ch in word:
            trial_chunk = chunk + ch
            if draw.textlength(trial_chunk, font=font) <= max_width:
                chunk = trial_chunk
            else:
                if chunk:
                    lines.append(chunk)
                chunk = ch
        if chunk:
            current = [chunk]
    if current:
        lines.append(" ".join(current))
    return lines


def multiline_height(
    draw: ImageDraw.ImageDraw,
    lines: Iterable[str],
    font: ImageFont.ImageFont,
    spacing: int = 4,
) -> int:
    lines = list(lines)
    if not lines:
        return 0
    text = "\n".join(lines)
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
    return bbox[3] - bbox[1]


@dataclass
class _StandardLayout:
    width: int
    total_h: int
    left: int
    top: int
    right: int
    bottom: int
    inner_left: int
    inner_right: int
    header_bottom: int
    title_font: ImageFont.ImageFont
    badge_font: ImageFont.ImageFont
    body_font: ImageFont.ImageFont
    sub_font: ImageFont.ImageFont
    body_lines: list[str]
    sub_lines: list[str]
    badge_text: str
    badge_left: int
    badge_top: int
    badge_right: int
    badge_bottom: int
    cursor_y: int
    rule_y: int
    subtext_y: int


class LabelBitmapRenderer:
    def __init__(self, theme: LabelTheme, fonts: FontSet):
        self.theme = theme
        self.fonts = fonts

    @staticmethod
    def draw_debug_rect(
        draw: ImageDraw.ImageDraw,
        bbox: tuple[int, int, int, int],
        color: tuple[int, int, int] | int = (255, 0, 0),
    ) -> None:
        draw.rectangle(bbox, outline=color, width=1)

    @staticmethod
    def draw_debug_hline(
        draw: ImageDraw.ImageDraw,
        x1: int,
        y: int,
        x2: int,
        color: tuple[int, int, int] | int = (255, 0, 0),
        pad: int = 8,
    ) -> None:
        draw.line((x1 - pad, y, x2 + pad, y), fill=color, width=1)

    @staticmethod
    def draw_debug_vline(
        draw: ImageDraw.ImageDraw,
        x: int,
        y1: int,
        y2: int,
        color: tuple[int, int, int] | int = (255, 0, 0),
        pad: int = 8,
    ) -> None:
        draw.line((x, y1 - pad, x, y2 + pad), fill=color, width=1)

    def render(self, data: LabelData) -> Image.Image:
        if self.theme.frame_style == "notebook":
            return self.render_notebook(data)
        return self.render_standard(data)

    def render_standard(self, data: LabelData) -> Image.Image:
        layout = self._calculate_standard_layout(data)

        mode = "RGB" if self.theme.debug_guides else "L"
        bg = (255, 255, 255) if mode == "RGB" else self.theme.background
        image = Image.new(mode, (layout.width, layout.total_h), color=bg)
        draw = ImageDraw.Draw(image)

        self._draw_standard_frame(draw, layout)
        self._draw_standard_header(draw, data.verb, layout)
        self._draw_standard_badge(draw, layout)
        self._draw_standard_content(draw, layout)

        if self.theme.debug_guides:
            self._draw_standard_debug_guides(draw, layout)

        return image

    def _calculate_standard_layout(self, data: LabelData) -> _StandardLayout:
        width = self.theme.paper_width_px
        probe = Image.new("L", (width, 2400), color=self.theme.background)
        probe_draw = ImageDraw.Draw(probe)

        left = self.theme.outer_margin
        top = self.theme.outer_margin
        right = width - self.theme.outer_margin - 1
        inner_left = left + self.theme.inner_padding + self.theme.border_width
        inner_right = right - self.theme.inner_padding - self.theme.border_width
        frame_inner_width = inner_right - inner_left

        title_font = fit_font_size(
            probe_draw,
            data.verb.upper(),
            self.fonts.title_path,
            frame_inner_width,
            start=self.theme.title_font_size,
            min_size=24,
        )
        badge_font = self.fonts.body(self.theme.badge_font_size)
        body_font = self.fonts.body(self.theme.body_font_size)
        sub_font = self.fonts.body(self.theme.subtext_font_size)

        body_lines = wrap_text(probe_draw, data.body, body_font, frame_inner_width)
        sub_lines = (
            wrap_text(probe_draw, data.subtext or "", sub_font, frame_inner_width)
            if data.subtext
            else []
        )

        badge_text = data.date_text
        badge_bbox = probe_draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_text_w = badge_bbox[2] - badge_bbox[0]
        badge_w = badge_text_w + (self.theme.badge_padding_x * 2)
        badge_h = self.theme.badge_height

        body_h = multiline_height(
            probe_draw, body_lines, body_font, spacing=self.theme.body_spacing
        )
        sub_h = multiline_height(
            probe_draw, sub_lines, sub_font, spacing=self.theme.subtext_spacing
        )

        total_h = (
            self.theme.outer_margin * 2
            + self.theme.border_width * 2
            + self.theme.header_height
            + self.theme.inner_padding
            + badge_h
            + self.theme.section_gap
            + body_h
            + (
                self.theme.rule_gap_above + self.theme.rule_gap_below + sub_h
                if sub_lines
                else 0
            )
            + self.theme.footer_gap
            + self.theme.inner_padding
        )

        bottom = total_h - self.theme.outer_margin - 1
        header_bottom = top + self.theme.header_height
        badge_left = inner_left
        badge_top = header_bottom + self.theme.inner_padding
        badge_right = badge_left + badge_w
        badge_bottom = badge_top + badge_h

        cursor_y = (
            badge_bottom + self.theme.section_gap + self.theme.body_start_offset_y
        )
        body_bottom_y = cursor_y + body_h
        rule_y = body_bottom_y + self.theme.rule_gap_above
        subtext_y = rule_y + self.theme.rule_gap_below

        return _StandardLayout(
            width=width,
            total_h=total_h,
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            inner_left=inner_left,
            inner_right=inner_right,
            header_bottom=header_bottom,
            title_font=title_font,
            badge_font=badge_font,
            body_font=body_font,
            sub_font=sub_font,
            body_lines=body_lines,
            sub_lines=sub_lines,
            badge_text=badge_text,
            badge_left=badge_left,
            badge_top=badge_top,
            badge_right=badge_right,
            badge_bottom=badge_bottom,
            cursor_y=cursor_y,
            rule_y=rule_y,
            subtext_y=subtext_y,
        )

    def _draw_standard_frame(
        self, draw: ImageDraw.ImageDraw, layout: _StandardLayout
    ) -> None:
        if self.theme.frame_style != "minimal":
            draw.rounded_rectangle(
                [layout.left, layout.top, layout.right, layout.bottom],
                radius=self.theme.corner_radius,
                fill=self.theme.background,
                outline=self.theme.foreground,
                width=self.theme.border_width,
            )
        else:
            draw.line(
                (layout.left, layout.top, layout.right, layout.top),
                fill=self.theme.foreground,
                width=2,
            )
            draw.line(
                (layout.left, layout.bottom, layout.right, layout.bottom),
                fill=self.theme.foreground,
                width=2,
            )

    def _draw_standard_header(
        self, draw: ImageDraw.ImageDraw, verb: str, layout: _StandardLayout
    ) -> None:
        draw.rounded_rectangle(
            [layout.left, layout.top, layout.right, layout.header_bottom],
            radius=self.theme.corner_radius,
            fill=self.theme.foreground,
        )
        draw.rectangle(
            [
                layout.left,
                layout.top + (self.theme.header_height // 2),
                layout.right,
                layout.header_bottom,
            ],
            fill=self.theme.foreground,
        )

        header_center_x = (layout.left + layout.right) / 2
        content_y = layout.top + self.theme.content_shift_y
        header_center_y = (
            content_y
            + (self.theme.header_height / 2)
            + self.theme.header_text_offset_y
        )
        draw.text(
            (header_center_x, header_center_y),
            verb.upper(),
            fill=self.theme.background,
            font=layout.title_font,
            anchor="mm",
        )

    def _draw_standard_badge(
        self, draw: ImageDraw.ImageDraw, layout: _StandardLayout
    ) -> None:
        draw.rounded_rectangle(
            [
                layout.badge_left,
                layout.badge_top,
                layout.badge_right,
                layout.badge_bottom,
            ],
            radius=self.theme.badge_radius,
            fill=self.theme.background,
            outline=self.theme.foreground,
            width=2,
        )
        draw.text(
            (
                (layout.badge_left + layout.badge_right) / 2,
                (layout.badge_top + layout.badge_bottom) / 2,
            ),
            layout.badge_text,
            fill=self.theme.foreground,
            font=layout.badge_font,
            anchor="mm",
        )

    def _draw_standard_content(
        self, draw: ImageDraw.ImageDraw, layout: _StandardLayout
    ) -> None:
        draw.multiline_text(
            (layout.inner_left, layout.cursor_y),
            "\n".join(layout.body_lines),
            fill=self.theme.foreground,
            font=layout.body_font,
            spacing=self.theme.body_spacing,
        )

        if layout.sub_lines:
            draw.line(
                (
                    layout.inner_left,
                    layout.rule_y,
                    layout.inner_right,
                    layout.rule_y,
                ),
                fill=self.theme.foreground,
                width=2,
            )
            draw.multiline_text(
                (layout.inner_left, layout.subtext_y),
                "\n".join(layout.sub_lines),
                fill=self.theme.foreground,
                font=layout.sub_font,
                spacing=self.theme.subtext_spacing,
            )

    def _draw_standard_debug_guides(
        self, draw: ImageDraw.ImageDraw, layout: _StandardLayout
    ) -> None:
        pad = self.theme.debug_margin_px
        c = self.theme.debug_color

        self.draw_debug_rect(
            draw, (layout.left, layout.top, layout.right, layout.bottom), color=c
        )
        self.draw_debug_hline(
            draw, layout.left, layout.header_bottom, layout.right, color=c, pad=pad
        )
        self.draw_debug_rect(
            draw,
            (
                layout.badge_left,
                layout.badge_top,
                layout.badge_right,
                layout.badge_bottom,
            ),
            color=c,
        )
        self.draw_debug_hline(
            draw,
            layout.inner_left,
            layout.cursor_y,
            layout.inner_right,
            color=c,
            pad=pad,
        )

        if layout.sub_lines:
            self.draw_debug_hline(
                draw,
                layout.inner_left,
                layout.rule_y,
                layout.inner_right,
                color=c,
                pad=pad,
            )

    def render_notebook(self, data: LabelData) -> Image.Image:
        width = self.theme.paper_width_px
        left = self.theme.outer_margin
        top = self.theme.outer_margin
        right = width - self.theme.outer_margin - 1

        probe = Image.new("L", (width, 2400), color=self.theme.background)
        probe_draw = ImageDraw.Draw(probe)

        title_font = fit_font_size(
            probe_draw,
            data.verb.upper(),
            self.fonts.title_path,
            right - left - 2 * self.theme.inner_padding,
            start=self.theme.title_font_size,
            min_size=24,
        )
        meta_font = self.fonts.body(20)

        title_bbox = probe_draw.textbbox((0, 0), data.verb.upper(), font=title_font)
        title_h = title_bbox[3] - title_bbox[1]

        meta_h = 40 if self.theme.meta_header_labels else 0
        header_h = 22 if self.theme.list_has_checkbox else 0
        row_h = 34
        list_h = (self.theme.list_rows or 12) * row_h

        total_h = (
            self.theme.outer_margin * 2
            + 16
            + title_h
            + meta_h
            + (8 if meta_h else 0)
            + header_h
            + (10 if header_h else 0)
            + list_h
            + self.theme.inner_padding
        )

        mode = "RGB" if self.theme.debug_guides else "L"
        bg = (255, 255, 255) if mode == "RGB" else self.theme.background
        image = Image.new(mode, (width, total_h), color=bg)
        draw = ImageDraw.Draw(image)

        inner_left = left + self.theme.inner_padding
        inner_right = right - self.theme.inner_padding
        bottom = total_h - self.theme.outer_margin - 1

        draw.rectangle(
            [left, top, right, bottom], outline=self.theme.foreground, width=1
        )

        content_y = top + self.theme.content_shift_y
        title_y = content_y + 8 + self.theme.header_text_offset_y
        draw.text(
            ((left + right) / 2, title_y),
            data.verb.upper(),
            fill=self.theme.foreground,
            font=title_font,
            anchor="ma",
        )

        body_y = content_y + title_h + 12 + self.theme.body_start_offset_y

        if self.theme.meta_header_labels:
            mid_x = (inner_left + inner_right) // 2
            draw.rectangle(
                [inner_left, body_y, inner_right, body_y + 40],
                outline=self.theme.foreground,
                width=1,
            )
            draw.line(
                (mid_x, body_y, mid_x, body_y + 40), fill=self.theme.foreground, width=1
            )
            draw.text(
                (inner_left + 10, body_y + 6),
                self.theme.meta_header_labels[0],
                fill=self.theme.foreground,
                font=meta_font,
            )
            draw.text(
                (mid_x + 10, body_y + 6),
                self.theme.meta_header_labels[1],
                fill=self.theme.foreground,
                font=meta_font,
            )
            body_y += 48

        if self.theme.list_has_checkbox:
            draw.text(
                (inner_left + 28, body_y),
                "ITEM",
                fill=self.theme.foreground,
                font=meta_font,
            )
            draw.line(
                (inner_left, body_y + 24, inner_right, body_y + 24),
                fill=self.theme.foreground,
                width=1,
            )
            body_y += 34

        for i in range(self.theme.list_rows or 12):
            line_y = body_y + i * row_h
            draw.line(
                (inner_left, line_y, inner_right, line_y),
                fill=self.theme.foreground,
                width=1,
            )
            if self.theme.list_has_checkbox:
                box_top = line_y + 8
                draw.rectangle(
                    [inner_left + 6, box_top, inner_left + 20, box_top + 14],
                    outline=self.theme.foreground,
                    width=1,
                )

        if self.theme.debug_guides:
            pad = self.theme.debug_margin_px
            c = self.theme.debug_color

            self.draw_debug_rect(draw, (left, top, right, bottom), color=c)
            self.draw_debug_hline(draw, left, title_y, right, color=c, pad=pad)

            if self.theme.meta_header_labels:
                self.draw_debug_rect(
                    draw, (inner_left, body_y, inner_right, body_y + 40), color=c
                )
                self.draw_debug_hline(
                    draw, inner_left, body_y + 40, inner_right, color=c, pad=pad
                )

            if self.theme.list_has_checkbox:
                self.draw_debug_hline(
                    draw, inner_left, body_y + 24, inner_right, color=c, pad=pad
                )

            for i in range(self.theme.list_rows or 12):
                line_y = body_y + i * row_h
                self.draw_debug_hline(
                    draw, inner_left, line_y, inner_right, color=c, pad=pad
                )

        return image
