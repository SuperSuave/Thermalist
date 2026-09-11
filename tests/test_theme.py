import pytest
from app.renderers.label_bitmap import LabelThemeName, get_theme, LabelTheme


def test_get_theme_enum():
    for name in LabelThemeName:
        theme = get_theme(name)
        assert isinstance(theme, LabelTheme)


def test_get_theme_str_valid():
    for name in LabelThemeName:
        theme = get_theme(name.value)
        assert isinstance(theme, LabelTheme)


def test_get_theme_invalid_str_fallback():
    theme = get_theme("unknown_theme_name")
    assert isinstance(theme, LabelTheme)
