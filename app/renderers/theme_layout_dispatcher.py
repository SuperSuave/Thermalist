from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw

from app.api.models.theme_layout import (
    Align,
    BadgeElement,
    BoxElement,
    CheckBoxElement,
    GridElement,
    ImageElement,
    LabelLayout,
    LayoutElementBase,
    LineElement,
    ListElement,
    ListRowData,
    RepeatDirection,
    TextElement,
    ThemeElement,
    ThemeStyle,
    TitleElement,
    RenderPayload,
)


class ThemeLayoutRenderer:
    def __init__(self, style: ThemeStyle, fonts: Any):
        self.style = style
        self.fonts = fonts

    def render(self, layout: LabelLayout, payload: RenderPayload) -> Image.Image:
        if getattr(layout, "kind", "generic") == "quickverb":
            return self.render_quickverb_label(layout, payload)
        height = self.estimate_height(layout)
        mode = "RGB" if self.style.debug_guides else "L"
        bg = (255, 255, 255) if mode == "RGB" else self.style.background
        image = Image.new(mode, (layout.paper_width_px, height), color=bg)
        draw = ImageDraw.Draw(image)

        for element in layout.elements:
            if element.visible:
                self.draw_element(draw, element, layout, payload)

        return image

    def render_quickverb_label(self, layout: LabelLayout, payload: RenderPayload) -> Image.Image:
        theme = self.style  # ThemeStyle now carries header_height, badge_height, etc.

        width = layout.paper_width_px
        # Probe canvas for measurements if needed:
        probe = Image.new("L", (width, 2400), color=theme.background)
        probe_draw = ImageDraw.Draw(probe)

        left = layout.outer_margin
        right = width - layout.outer_margin - 1
        inner_left = left + layout.inner_padding + theme.border_width
        inner_right = right - layout.inner_padding - theme.border_width
        frame_inner_width = inner_right - inner_left

        title_font = self.fonts.title(theme.title_font_size)
        badge_font = self.fonts.body(theme.badge_font_size)
        body_font = self.fonts.body(theme.body_font_size)
        sub_font = self.fonts.body(theme.badge_font_size)  # or a subtext size you add

        verb = (payload.title or layout.name).upper()
        date_text = payload.values.get("date_text", "")

        # Compute body/subtext lines using your wrap_text helper
        body_text = payload.values.get("body", "")
        sub_text = payload.values.get("subtext", "")
        body_lines = self.wrap_text(body_text, body_font, frame_inner_width, probe_draw)
        sub_lines = self.wrap_text(sub_text, sub_font, frame_inner_width, probe_draw)

        # Compute badge width, body height, subtext height — porting logic from render_standard
        ...

        total_h = (
            layout.outer_margin * 2
            + theme.border_width * 2
            + theme.header_height
            + layout.inner_padding
            + theme.badge_height
            + theme.section_gap
            + body_h
            + (theme.rule_gap_above + theme.rule_gap_below + sub_h if sub_lines else 0)
            + theme.footer_gap
            + layout.inner_padding
        )

        mode = "RGB" if theme.debug_guides else "L"
        bg = (255, 255, 255) if mode == "RGB" else theme.background
        image = Image.new(mode, (width, total_h), color=bg)
        draw = ImageDraw.Draw(image)

        # Draw frame (rounded vs minimal) using theme.corner_radius, theme.border_width
        ...

        # Header band (black rectangle) and centered verb
        ...

        # Date badge, body text, rule, subtext – all ported from render_standard
        ...

        return image

    def draw_element(
        self,
        draw: ImageDraw.ImageDraw,
        element: ThemeElement,
        layout: LabelLayout,
        data: dict[str, Any],
    ) -> None:
        match element.type:
            case "title":
                self.draw_title(draw, element, layout, data)
            case "text":
                self.draw_text(draw, element, layout, data)
            case "badge":
                self.draw_badge(draw, element, layout, data)
            case "line":
                self.draw_line(draw, element, layout)
            case "box":
                self.draw_box(draw, element, layout)
            case "grid":
                self.draw_grid(draw, element, layout, data)
            case "list":
                self.draw_list(draw, element, layout, data)
            case "checkbox":
                self.draw_checkbox(draw, element, layout)
            case "image":
                self.draw_image(draw, element, layout, data)

    def resolve_xy(
        self, element: LayoutElementBase, layout: LabelLayout
    ) -> tuple[int, int]:
        return layout.outer_margin + element.x, layout.outer_margin + element.y

    def anchor_for(self, element: LayoutElementBase) -> str:
        if element.align == Align.CENTER:
            return "mm"
        if element.align == Align.RIGHT:
            return "ra"
        return "la"

    def iter_repeated_positions(
        self, element: LayoutElementBase
    ) -> list[tuple[int, int]]:
        x0 = element.x
        y0 = element.y
        positions = []

        for i in range(max(1, element.repeat)):
            if element.repeat_direction == RepeatDirection.RIGHT:
                positions.append((x0 + i * ((element.width or 0) + element.gap), y0))
            else:
                positions.append((x0, y0 + i * ((element.height or 0) + element.gap)))

        return positions

    def draw_title(
        self, draw, element: TitleElement, layout, payload: RenderPayload
    ) -> None:
        text = element.props.get("text", "")
        bind = element.props.get("bind")
        if bind:
            text = payload.values.get(bind, text)
        if not text:
            text = payload.title or layout.name

        font = self.fonts.title(self.style.title_font_size)

        base_x, base_y = self.resolve_xy(element, layout)
        available_w = layout.paper_width_px - 2 * layout.outer_margin
        center_x = layout.outer_margin + available_w // 2

        # Header band: use element.height if present
        if getattr(element, "height", None):
            band_height = element.height
            # Filled rectangle for header band
            draw.rectangle(
                [
                    layout.outer_margin,
                    base_y,
                    layout.outer_margin + available_w,
                    base_y + band_height,
                ],
                fill=self.style.foreground,   # black band
                outline=None,
            )
            _, _, _, text_h = draw.textbbox((0, 0), text, font=font)
            center_y = base_y + band_height // 2
            text_fill = self.style.background  # white text on black
        else:
            center_y = base_y
            text_fill = self.style.foreground

        draw.text(
            (center_x, center_y),
            text,
            fill=text_fill,
            font=font,
            anchor=self.anchor_for(element),
        )

    def draw_text(
        self, draw, element: TextElement, layout, payload: RenderPayload
    ) -> None:
        text = element.props.get("text", "")
        bind = element.props.get("bind")
        if bind:
            text = payload.values.get(bind, text)
        font = self.fonts.body(self.style.body_font_size)
        x, y = self.resolve_xy(element, layout)
        draw.text(
            (x, y),
            text,
            fill=self.style.foreground,
            font=font,
            anchor=self.anchor_for(element),
        )

    def draw_badge(
        self, draw, element: BadgeElement, layout, payload: RenderPayload
    ) -> None:
        x, y = self.resolve_xy(element, layout)
        w = element.width or 80
        h = element.height or 30
        radius = element.props.get("radius", 8)
        text = element.props.get("text", "")
        bind = element.props.get("bind")
        if bind:
            text = payload.values.get(bind, text)
        if not text:
            text = payload.title or ""
        draw.rounded_rectangle(
            [x, y, x + w, y + h],
            radius=radius,
            outline=self.style.foreground,
            width=self.style.border_width,
        )
        font = self.fonts.body(self.style.badge_font_size)
        draw.text(
            (x + w / 2, y + h / 2),
            text,
            fill=self.style.foreground,
            font=font,
            anchor="mm",
        )

    def draw_line(self, draw, element: LineElement, layout) -> None:
        x, y = self.resolve_xy(element, layout)
        w = element.width or (layout.paper_width_px - 2 * layout.outer_margin)
        draw.line(
            (x, y, x + w, y),
            fill=self.style.foreground,
            width=element.props.get("width", 1),
        )

    def draw_box(self, draw, element: BoxElement, layout) -> None:
        x, y = self.resolve_xy(element, layout)
        w = element.width or 100
        h = element.height or 40
        draw.rectangle(
            [x, y, x + w, y + h],
            outline=self.style.foreground,
            width=self.style.border_width,
        )

    def draw_grid(
        self, draw, element: GridElement, layout, payload: RenderPayload
    ) -> None:
        x, y = self.resolve_xy(element, layout)
        w = element.width or (layout.paper_width_px - 2 * layout.outer_margin)
        h = element.height or 40
        cols = element.columns or []
        if not cols:
            return

        widths = self.weighted_widths(w, [c.width for c in cols])
        col_x = x
        for col, col_w in zip(cols, widths):
            draw.rectangle(
                [col_x, y, col_x + col_w, y + h], outline=self.style.foreground, width=1
            )
            if col.label:
                font = self.fonts.body(self.style.badge_font_size)
                draw.text(
                    (col_x + 8, y + 4), col.label, fill=self.style.foreground, font=font
                )
            col_x += col_w

    def wrap_text(self, text: str, font, max_width: float, draw) -> list[str]:
        """Wrap long text into multiple lines that fit within max_width."""
        if not text:
            return []

        # Quick path: if the whole text fits, no wrapping needed
        try:
            w = draw.textlength(text, font=font)
        except Exception:
            w = 0

        if w <= max_width:
            return [text]

        words = text.split()
        lines = []
        current = ["words[0]"] if words else []
        current = []
        for word in words:
            test = " ".join(current + [word])
            try:
                tw = draw.textlength(test, font=font)
            except Exception:
                tw = 0

            if tw <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        return lines

    def wrap_text_to_lines(self, draw, text: str, font, max_width: float) -> list[str]:
        """Wrap text into lines that fit within max_width using Pillow's textlength."""
        if not text:
            return [""]

        words = text.split()

        # Quick path: if the whole text fits, no wrapping needed
        try:
            if draw.textlength(text, font=font) <= max_width:
                return [text]
        except Exception:
            pass

        lines: list[str] = []
        current = []
        for word in words:
            test = " ".join(current + [word])
            try:
                tw = draw.textlength(test, font=font)
            except Exception:
                tw = 0

            if tw <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))

        return lines if lines else [""]

    def draw_list(
        self, draw, element: ListElement, layout, payload: RenderPayload
    ) -> None:
        base_x, base_y = self.resolve_xy(element, layout)
        row_h = element.height or 34
        cols = element.columns or []
        row_count = max(1, element.repeat)
        rows = payload.rows

        if not cols:
            for i in range(row_count):
                row_y = base_y + i * (row_h + element.gap)
                draw.line(
                    (
                        base_x,
                        row_y,
                        base_x + (layout.paper_width_px - 2 * layout.outer_margin),
                        row_y,
                    ),
                    fill=self.style.foreground,
                    width=1,
                )
            return

        weights = [c.width for c in cols]
        available_w = layout.paper_width_px - 2 * layout.outer_margin
        widths = self.weighted_widths(available_w, weights)

        line_gap = 2

        for row_idx in range(row_count):
            row_y = base_y + row_idx * (row_h + element.gap)
            draw.line(
                (base_x, row_y, base_x + available_w, row_y),
                fill=self.style.foreground,
                width=1,
            )

            row_data: ListRowData = (
                rows[row_idx] if row_idx < len(rows) else ListRowData()
            )
            values = row_data.values
            checked = row_data.checked

            col_x = base_x
            field_index = 0
            check_index = 0

            for col_idx, (col, col_w) in enumerate(zip(cols, widths)):
                if col.type == "checkbox":
                    box_x = col_x + 4
                    box_y = row_y + 8
                    is_checked = (
                        bool(checked[check_index])
                        if check_index < len(checked)
                        else False
                    )
                    check_index += 1

                    self.draw_checkbox(
                        draw,
                        CheckBoxElement(
                            x=box_x - layout.outer_margin,
                            y=box_y - layout.outer_margin,
                            width=14,
                            height=14,
                            props={"checked": is_checked},
                        ),
                        layout,
                    )
                elif col.type == "text":
                    font = self.fonts.body(self.style.body_font_size)
                    raw_text = (
                        values[field_index]
                        if field_index < len(values)
                        else (col.label or "")
                    )
                    field_index += 1

                    max_text_w = col_w - 12
                    wrapped = self.wrap_text_to_lines(draw, raw_text, font, max_text_w)

                    # Measure total text block height
                    total_text_h = 0
                    for line in wrapped:
                        _, _, _, lh = draw.textbbox((0, 0), line, font=font)
                        total_text_h += lh + line_gap
                    total_text_h -= line_gap

                    # Center vertically
                    tx = col_x + 8
                    ty = row_y + (row_h - total_text_h) // 2

                    for line in wrapped:
                        draw.text(
                            (tx, ty),
                            line,
                            fill=self.style.foreground,
                            font=font,
                        )
                        _, _, _, lh = draw.textbbox((0, 0), line, font=font)
                        ty += lh + line_gap

                elif col.type == "badge":
                    badge_w = max(30, col_w - 12)
                    badge_h = row_h - 10
                    bx = col_x + 6
                    by = row_y + 5
                    raw_text = (
                        values[field_index]
                        if field_index < len(values)
                        else (col.label or "")
                    )
                    field_index += 1

                    draw.rounded_rectangle(
                        [bx, by, bx + badge_w, by + badge_h],
                        radius=6,
                        outline=self.style.foreground,
                        width=1,
                    )

                    font = self.fonts.body(self.style.badge_font_size)

                    max_badge_text_w = badge_w - 10
                    wrapped = self.wrap_text_to_lines(
                        draw, raw_text, font, max_badge_text_w
                    )

                    # Measure total badge text height
                    total_text_h = 0
                    for line in wrapped:
                        _, _, _, lh = draw.textbbox((0, 0), line, font=font)
                        total_text_h += lh + line_gap
                    total_text_h -= line_gap

                    # Center vertically in badge
                    text_tx = bx + 5
                    text_ty = by + (badge_h - total_text_h) // 2

                    for line in wrapped:
                        draw.text(
                            (text_tx, text_ty),
                            line,
                            fill=self.style.foreground,
                            font=font,
                        )
                        _, _, _, lh = draw.textbbox((0, 0), line, font=font)
                        text_ty += lh + line_gap

                else:
                    # unknown column type — still advance x
                    pass

                col_x += col_w

    def draw_checkbox(self, draw, element: CheckBoxElement, layout) -> None:
        x, y = self.resolve_xy(element, layout)
        w = element.width or 14
        h = element.height or 14
        draw.rectangle([x, y, x + w, y + h], outline=self.style.foreground, width=1)

        if element.props.get("checked"):
            draw.line(
                (x + 3, y + 7, x + 6, y + 10), fill=self.style.foreground, width=1
            )
            draw.line(
                (x + 6, y + 10, x + 11, y + 3), fill=self.style.foreground, width=1
            )

    def draw_image(
        self, draw, element: ImageElement, layout, payload: RenderPayload
    ) -> None:
        pass

    def estimate_height(self, layout: LabelLayout) -> int:
        if not layout.elements:
            return 200

        max_bottom = 0
        for el in layout.elements:
            row_h = el.height or 40
            span = max(1, el.repeat)

            if el.repeat_direction == RepeatDirection.RIGHT:
                bottom = el.y + row_h
                right = el.x + (row_h + el.gap) * (span - 1) + (el.width or 0)
                max_bottom = max(max_bottom, bottom)
            else:
                bottom = el.y + row_h + (span - 1) * (row_h + el.gap)
                max_bottom = max(max_bottom, bottom)

        return max_bottom + layout.outer_margin * 2 + 20

    def weighted_widths(self, total_width: int, weights: list[float]) -> list[int]:
        if not weights:
            return []
        total = sum(weights)
        if total <= 0:
            return [0 for _ in weights]
        raw = [total_width * (w / total) for w in weights]
        ints = [int(v) for v in raw]
        remainder = total_width - sum(ints)
        for i in range(remainder):
            ints[i % len(ints)] += 1
        return ints
