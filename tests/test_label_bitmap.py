from unittest.mock import MagicMock
from PIL import Image, ImageDraw, ImageFont

from app.renderers.label_bitmap import DEFAULT_TITLE_FONT_PATH, fit_font_size, wrap_text


def test_wrap_text_empty_and_whitespace():
    draw = MagicMock()
    font = MagicMock()

    assert wrap_text(draw, "", font, 100) == []
    assert wrap_text(draw, "   \n\t  ", font, 100) == []
    draw.textlength.assert_not_called()


def test_wrap_text_single_line_fit():
    draw = MagicMock()
    font = MagicMock()
    # Mock textlength to return 50 for any string
    draw.textlength.side_effect = lambda text, font: len(text) * 5

    text = "hello world"
    # len("hello world") * 5 = 55 <= 100 max_width
    lines = wrap_text(draw, text, font, 100)
    assert lines == ["hello world"]


def test_wrap_text_word_wrapping():
    draw = MagicMock()
    font = MagicMock()

    # Each character is width 10
    draw.textlength.side_effect = lambda text, font: len(text) * 10

    # "hello world test"
    # "hello" (50) fits in 60
    # "hello world" (110) > 60 -> wrap line 1: "hello"
    # "world" (50) fits in 60
    # "world test" (100) > 60 -> wrap line 2: "world"
    # "test" (40) fits -> line 3: "test"
    lines = wrap_text(draw, "hello world test", font, 60)
    assert lines == ["hello", "world", "test"]


def test_wrap_text_long_word_character_wrapping():
    draw = MagicMock()
    font = MagicMock()

    # Each character is width 10
    draw.textlength.side_effect = lambda text, font: len(text) * 10

    # "supercalifragilistic" is 20 chars = 200 width. max_width = 50 (fits 5 chars max per chunk)
    lines = wrap_text(draw, "supercalifragilistic", font, 50)
    assert lines == ["super", "calif", "ragil", "istic"]


def test_fit_font_size_missing_or_none_font_path():
    img = Image.new("L", (100, 100))
    draw = ImageDraw.Draw(img)
    default_font = ImageFont.load_default()

    font_none = fit_font_size(draw, "TEST", None, max_width=50, start=30)
    assert type(font_none) is type(default_font)

    font_missing = fit_font_size(
        draw, "TEST", "/nonexistent/font.ttf", max_width=50, start=30
    )
    assert type(font_missing) is type(default_font)


def test_fit_font_size_fits_at_start_size():
    img = Image.new("L", (100, 100))
    draw = ImageDraw.Draw(img)

    draw.textlength = MagicMock(return_value=100)

    font = fit_font_size(
        draw, "TEST", str(DEFAULT_TITLE_FONT_PATH), max_width=150, start=40
    )

    assert font.size == 40
    assert draw.textlength.call_count == 1


def test_fit_font_size_decrements_until_fit():
    img = Image.new("L", (100, 100))
    draw = ImageDraw.Draw(img)

    # Return width 200 for size 40, width 180 for size 39, width 150 for size 38
    def mock_textlength(text, font):
        if font.size == 40:
            return 200
        elif font.size == 39:
            return 180
        elif font.size == 38:
            return 150
        return 100

    draw.textlength = MagicMock(side_effect=mock_textlength)

    font = fit_font_size(
        draw, "TEST", str(DEFAULT_TITLE_FONT_PATH), max_width=150, start=40, min_size=14
    )

    assert font.size == 38
    assert draw.textlength.call_count == 3


def test_fit_font_size_falls_back_to_min_size_when_exceeding_width():
    img = Image.new("L", (100, 100))
    draw = ImageDraw.Draw(img)

    draw.textlength = MagicMock(return_value=500)

    font = fit_font_size(
        draw, "TEST", str(DEFAULT_TITLE_FONT_PATH), max_width=150, start=20, min_size=14
    )

    assert font.size == 14
    # loop from start=20 down to min_size=14 is 7 checks
    assert draw.textlength.call_count == 7


def test_fit_font_size_falls_back_to_min_size_when_start_smaller_than_min_size():
    img = Image.new("L", (100, 100))
    draw = ImageDraw.Draw(img)

    draw.textlength = MagicMock(return_value=100)

    font = fit_font_size(
        draw, "TEST", str(DEFAULT_TITLE_FONT_PATH), max_width=150, start=10, min_size=14
    )

    assert font.size == 14
    assert draw.textlength.call_count == 0
