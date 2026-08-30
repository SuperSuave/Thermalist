from app.renderers.label_bitmap import LabelTheme, LabelThemeName, get_theme


def test_get_theme_all_enum_values():
    for theme_name in LabelThemeName:
        theme = get_theme(theme_name)
        assert isinstance(theme, LabelTheme)
        assert theme.paper_width_px == 640


def test_get_theme_string_inputs():
    theme_framed = get_theme("framed_food")
    assert theme_framed.frame_style == "framed"

    theme_compact = get_theme("compact")
    assert theme_compact.frame_style == "compact"

    theme_minimal = get_theme("minimal")
    assert theme_minimal.frame_style == "minimal"

    theme_bold = get_theme("bold")
    assert theme_bold.frame_style == "bold"

    theme_playful = get_theme("playful")
    assert theme_playful.frame_style == "playful"

    theme_notebook = get_theme("reminders_notebook")
    assert theme_notebook.frame_style == "notebook"


def test_get_theme_unknown_fallback():
    theme_fallback = get_theme("unknown_theme_name")
    assert isinstance(theme_fallback, LabelTheme)
    assert theme_fallback.frame_style == "framed"
