from __future__ import annotations
import textwrap
import unicodedata
from datetime import datetime

from app.core.models import Document, RenderedReceipt
from app.renderers.base import Renderer


def _strip_unsupported_chars(text: str) -> str:
    stripped = "".join(
        ch for ch in text
        if unicodedata.category(ch) not in {"So", "Cf"}
    )
    return "\n".join(" ".join(line.split()) for line in stripped.splitlines())


class Receipt80mmRenderer(Renderer):
    name = "receipt_80mm"

    def __init__(self, width: int = 48, show_due: bool = True) -> None:
        self.width = width
        self.show_due = show_due

    def _center(self, text: str) -> str:
        return text[:self.width].center(self.width)

    def _divider(self, char: str = "-") -> str:
        return (char * ((self.width // len(char)) + 1))[:self.width]

    def _box_line(self, text: str, inner: int) -> str:
        return "|" + text.center(inner) + "|"

    def _wrap_indented(self, prefix: str, text: str, indent: str = "    ") -> list[str]:
        if not text:
            return [prefix.rstrip()] if prefix else []

        avail_first = max(8, self.width - len(prefix))

        wrapped = textwrap.wrap(text, width=avail_first, break_long_words=True, drop_whitespace=True)
        if not wrapped:
            return [prefix.rstrip()]

        lines = [f"{prefix}{wrapped[0]}"]
        if len(wrapped) > 1:
            rem = " ".join(wrapped[1:])
            lines.extend(textwrap.wrap(rem, width=self.width, initial_indent=indent, subsequent_indent=indent, break_long_words=True, drop_whitespace=True))
        return lines

    def _wrap(self, text: str, indent: str = "") -> list[str]:
        if not text:
            return []
        wrapper = textwrap.TextWrapper(
            width=self.width, initial_indent=indent, subsequent_indent=indent, break_long_words=True, drop_whitespace=True
        )
        lines = []
        for raw in text.splitlines():
            if not raw.strip():
                lines.append("")
            else:
                lines.extend(wrapper.wrap(raw))
        return lines

    def _build_label_bytes(self, verb: str, date: str, note: str) -> bytes:
        parts: list[bytes] = []
        inner = self.width - 2
        border = ("+" + "-" * inner + "+").encode("utf-8")
        blank = ("|" + " " * inner + "|").encode("utf-8")
        lf = b"\x0a"

        double_size_on  = b"\x1d\x21\x11"
        double_size_off = b"\x1d\x21\x00"
        center_on       = b"\x1b\x61\x01"
        center_off      = b"\x1b\x61\x00"

        def box_line_bytes(text: str, double: bool = False) -> bytes:
            if double:
                centered = text.center(inner // 2)
                return center_on + double_size_on + f"|{centered}|".encode("utf-8") + double_size_off + lf
            centered = text.center(inner)
            return f"|{centered}|".encode("utf-8") + lf

        parts.extend([border + lf, blank + lf, box_line_bytes(verb, double=True), box_line_bytes(date, double=True), blank + lf])
        if note:
            parts.extend([box_line_bytes(note, double=False), blank + lf])
        parts.extend([border + lf, center_off])
        return b"".join(parts)

    def _render_label_section(self, section) -> tuple[list[str], bytes]:
        lines: list[str] = []
        verb = _strip_unsupported_chars(section.text or "")
        date = _strip_unsupported_chars(section.metadata.get("date", ""))
        note = _strip_unsupported_chars(section.metadata.get("note", ""))

        inner = self.width - 2
        border = "+" + "-" * inner + "+"
        blank = "|" + " " * inner + "|"

        lines.extend([border, blank])
        if verb:
            lines.append(self._box_line(verb, inner))
        if date:
            lines.append(self._box_line(date, inner))
        if verb or date:
            lines.append(blank)

        if note:
            wrapped_note = textwrap.wrap(note, width=inner - 2) or [""]
            if len(wrapped_note) == 1:
                lines.append(self._box_line(wrapped_note[0], inner))
            else:
                for part in wrapped_note:
                    lines.append("| " + part.ljust(inner - 2) + " |")
            lines.append(blank)

        lines.append(border)
        return lines, self._build_label_bytes(verb, date, note)

    def _render_task_list_section(self, section) -> list[str]:
        lines: list[str] = []
        for item in section.tasks:
            title = _strip_unsupported_chars(item.title or "")
            prefix = "[x] " if item.completed else "[ ] "
            lines.extend(self._wrap_indented(prefix, title, indent="    "))

            if item.description:
                lines.extend(self._wrap(_strip_unsupported_chars(item.description), indent="    "))

            for sub in getattr(item, "subtasks", []) or []:
                sub_title = _strip_unsupported_chars(sub.title or "")
                sub_prefix = "    [x] " if sub.completed else "    [ ] "
                lines.extend(self._wrap_indented(sub_prefix, sub_title, indent="        "))
                if sub.description:
                    lines.extend(self._wrap(_strip_unsupported_chars(sub.description), indent="        "))
                if self.show_due and sub.due:
                    lines.extend(self._wrap(_strip_unsupported_chars(f"Due: {sub.due}"), indent="        "))

            if self.show_due and item.due:
                lines.extend(self._wrap(_strip_unsupported_chars(f"Due: {item.due}"), indent="    "))
            lines.append("")

        return lines

    def render(self, document: Document) -> RenderedReceipt:
        lines: list[str] = []
        label_raw: bytes | None = None

        for section in document.sections:
            if section.kind == "title" and section.text:
                title = _strip_unsupported_chars(section.text.strip().upper())
                today = datetime.now().strftime("%m/%d/%y")
                lines.extend([self._center(title), self._center(today), self._divider("^v"), ""])
            elif section.kind == "text" and section.text:
                lines.extend(self._wrap(_strip_unsupported_chars(section.text)))
            elif section.kind == "divider":
                lines.append(self._divider())
            elif section.kind == "spacer":
                lines.append("")
            elif section.kind == "label":
                sec_lines, label_raw = self._render_label_section(section)
                lines.extend(sec_lines)
            elif section.kind == "task_list":
                lines.extend(self._render_task_list_section(section))
            elif section.kind == "ingredient_list":
                for ing in section.ingredients:
                    lines.extend(self._wrap_indented("- ", _strip_unsupported_chars(ing.text or ing.original_text or ""), indent="   "))
                lines.append("")
            elif section.kind == "step_list":
                for step in section.steps:
                    lines.extend(self._wrap_indented(f"{step.number}. ", _strip_unsupported_chars(step.text or ""), indent="   "))
                lines.append("")

        while lines and lines[-1] == "":
            lines.pop()

        lines.extend(["", ""])
        return RenderedReceipt(
            text_preview="\n".join(lines),
            raw_bytes=label_raw,
            metadata={"renderer": self.name, "width": self.width},
        )
