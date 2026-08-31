import pytest
from app.api.models.theme import ThemeName, get_theme, Theme


def test_get_theme_enum():
    for name in ThemeName:
        theme = get_theme(name)
        assert isinstance(theme, Theme)
        assert theme.name == name


def test_get_theme_str_valid():
    for name in ThemeName:
        theme = get_theme(name.value)
        assert isinstance(theme, Theme)
        assert theme.name == name


def test_get_theme_invalid_str_fallback():
    theme = get_theme("unknown_theme_name")
    assert isinstance(theme, Theme)
    assert theme.name == ThemeName.REMINDERS_NOTEBOOK
