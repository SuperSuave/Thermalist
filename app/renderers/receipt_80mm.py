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
    lines = [" ".join(line.split()) for line in stripped.splitlines()]
    return "\n".join(lines)


class Receipt80mmRenderer(Renderer):
    name = "receipt_80mm"

    def __init__(self, width: int = 48, show_due: bool = True) -> None:
        self.width = width
        self.show_due = show_due

    def _center(self, text: str) -> str:
        text = text[:self.width]
        return text.center(self.width)

    def _divider(self, char: str = "-") -> str:
        repeated = (char * ((self.width // len(char)) + 1))[:self.width]
        return repeated

    def _box_line(self, text: str, inner: int) -> str:
        return "|" + text.center(inner) + "|"

    def _box_line_left(self, text: str, inner: int) -> str:
        return "|" + text.ljust(inner) + "|"

    def _wrap(self, text: str, indent: str = "") -> list[str]:
        if not text:
            return []

        wrapper = textwrap.TextWrapper(
            width=self.width,
            initial_indent=indent,
            subsequent_indent=indent,
            break_long_words=True,
            replace_whitespace=False,
            drop_whitespace=True,
        )

        lines: list[str] = []
        for raw_line in text.splitlines():
            if raw_line.strip() == "":
                lines.append("")
            else:
                lines.extend(wrapper.wrap(raw_line))

        return lines

    def _wrap_task(self, prefix: str, title: str, continuation_indent: str = "    ") -> list[str]:
        available_first = max(8, self.width - len(prefix))
        available_next = max(8, self.width - len(continuation_indent))

        wrapped = textwrap.wrap(
            title,
            width=available_first,
            break_long_words=True,
            drop_whitespace=True,
        )

        if not wrapped:
            return [prefix.rstrip()]

        lines = [f"{prefix}{wrapped[0]}"]

        if len(wrapped) > 1:
            remaining_text = " ".join(wrapped[1:])
            wrapper = textwrap.TextWrapper(
                width=available_next,
                initial_indent=continuation_indent,
                subsequent_indent=continuation_indent,
                break_long_words=True,
                drop_whitespace=True,
            )
            lines.extend(wrapper.wrap(remaining_text))

        return lines

    def _wrap_list_item(
        self,
        prefix: str,
        text: str,
        continuation_indent: str = "    ",
    ) -> list[str]:
        available_first = max(8, self.width - len(prefix))
        available_next = max(8, self.width - len(continuation_indent))

        wrapped = textwrap.wrap(
            text,
            width=available_first,
            break_long_words=True,
            drop_whitespace=True,
        )

        if not wrapped:
            return [prefix.rstrip()]

        lines = [f"{prefix}{wrapped[0]}"]

        if len(wrapped) > 1:
            remaining_text = " ".join(wrapped[1:])
            wrapper = textwrap.TextWrapper(
                width=available_next,
                initial_indent=continuation_indent,
                subsequent_indent=continuation_indent,
                break_long_words=True,
                drop_whitespace=True,
            )
            lines.extend(wrapper.wrap(remaining_text))

        return lines

    def _build_label_bytes(self, verb: str, date: str, note: str) -> bytes:
        parts: list[bytes] = []

        inner = self.width - 2
        border = ("+" + "-" * inner + "+").encode("utf-8")
        blank = ("|" + " " * inner + "|").encode("utf-8")
        lf = b"\x0a"

        double_size_on  = b"\x1d\x21\x11"  # GS ! 0x11 — double width + height
        double_size_off = b"\x1d\x21\x00"  # GS ! 0x00 — normal size
        center_on       = b"\x1b\x61\x01"  # ESC a 1 — center justify
        center_off      = b"\x1b\x61\x00"  # ESC a 0 — left justify

        def box_line_bytes(text: str, double: bool = False) -> bytes:
            if double:
                half_inner = inner // 2
                centered = text.center(half_inner)
                return (
                    center_on
                    + double_size_on
                    + f"|{centered}|".encode("utf-8")
                    + double_size_off
                    + lf
                )
            else:
                centered = text.center(inner)
                return f"|{centered}|".encode("utf-8") + lf

        parts.append(border + lf)
        parts.append(blank + lf)
        parts.append(box_line_bytes(verb, double=True))
        parts.append(box_line_bytes(date, double=True))
        parts.append(blank + lf)
        if note:
            parts.append(box_line_bytes(note, double=False))
            parts.append(blank + lf)
        parts.append(border + lf)
        parts.append(center_off)

        return b"".join(parts)

    def render(self, document: Document) -> RenderedReceipt:
        lines: list[str] = []
        label_raw: bytes | None = None
        task_indent = "    "
        subtask_indent = "        "

        for section in document.sections:
            if section.kind == "title" and section.text:
                title = _strip_unsupported_chars(section.text.strip().upper())
                today = datetime.now().strftime("%m/%d/%y")

                lines.append(self._center(f"{title}"))
                lines.append(self._center(today))
                lines.append(self._divider("^v"))
                lines.append("")

            elif section.kind == "text" and section.text:
                text = _strip_unsupported_chars(section.text)
                lines.extend(self._wrap(text))

            elif section.kind == "divider":
                lines.append(self._divider())

            elif section.kind == "spacer":
                lines.append("")

            elif section.kind == "label":
                verb = _strip_unsupported_chars(section.text or "")
                date = _strip_unsupported_chars(section.metadata.get("date", ""))
                note = _strip_unsupported_chars(section.metadata.get("note", ""))

                inner = self.width - 2
                border = "+" + "-" * inner + "+"
                blank = "|" + " " * inner + "|"

                lines.append(border)
                lines.append(blank)

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

                label_raw = self._build_label_bytes(verb, date, note)

            elif section.kind == "task_list":
                for item in section.tasks:
                    title = _strip_unsupported_chars(item.title or "")
                    prefix = "[x] " if item.completed else "[ ] "
                    lines.extend(self._wrap_task(prefix, title, continuation_indent=task_indent))

                    if item.description:
                        desc = _strip_unsupported_chars(item.description)
                        lines.extend(self._wrap(desc, indent=task_indent))

                    for sub in getattr(item, "subtasks", []) or []:
                        sub_title = _strip_unsupported_chars(sub.title or "")
                        sub_prefix = "    [x] " if sub.completed else "    [ ] "
                        lines.extend(
                            self._wrap_task(
                                sub_prefix,
                                sub_title,
                                continuation_indent=subtask_indent,
                            )
                        )

                        if sub.description:
                            sub_desc = _strip_unsupported_chars(sub.description)
                            lines.extend(self._wrap(sub_desc, indent=subtask_indent))

                        if self.show_due and sub.due:
                            sub_due_text = _strip_unsupported_chars(f"Due: {sub.due}")
                            lines.extend(self._wrap(sub_due_text, indent=subtask_indent))

                    if self.show_due and item.due:
                        due_text = _strip_unsupported_chars(f"Due: {item.due}")
                        lines.extend(self._wrap(due_text, indent=task_indent))
                    lines.append("")

            elif section.kind == "ingredient_list":
                for ingredient in section.ingredients:
                    display = (
                        ingredient.text
                        or ingredient.original_text
                        or ""
                    )
                    text = _strip_unsupported_chars(display)
                    lines.extend(self._wrap_list_item("- ", text, continuation_indent="   "))
                lines.append("")

            elif section.kind == "step_list":
                for step in section.steps:
                    text = _strip_unsupported_chars(step.text or "")
                    prefix = f"{step.number}. "
                    lines.extend(
                        self._wrap_list_item(prefix, text, continuation_indent="   ")
                    )
                lines.append("")


        while lines and lines[-1] == "":
            lines.pop()

        lines.extend(["", ""])
        preview = "\n".join(lines)

        return RenderedReceipt(
            text_preview=preview,
            raw_bytes=label_raw,
            metadata={"renderer": self.name, "width": self.width},
        )
