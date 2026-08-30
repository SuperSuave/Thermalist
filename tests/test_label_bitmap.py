from unittest.mock import MagicMock
from app.renderers.label_bitmap import wrap_text


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
