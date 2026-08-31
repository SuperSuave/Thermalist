from app.modules.utils import compact_metadata


def test_compact_metadata_removes_none_values():
    input_data = {
        "title": "Recipe",
        "description": None,
        "author": "Alice",
        "notes": None,
    }
    expected = {
        "title": "Recipe",
        "author": "Alice",
    }
    assert compact_metadata(input_data) == expected


def test_compact_metadata_preserves_falsy_non_none_values():
    input_data = {
        "count": 0,
        "enabled": False,
        "text": "",
        "items": [],
        "mapping": {},
        "missing": None,
    }
    expected = {
        "count": 0,
        "enabled": False,
        "text": "",
        "items": [],
        "mapping": {},
    }
    assert compact_metadata(input_data) == expected


def test_compact_metadata_empty_dict():
    assert compact_metadata({}) == {}


def test_compact_metadata_all_none():
    input_data = {"a": None, "b": None}
    assert compact_metadata(input_data) == {}


def test_compact_metadata_no_none():
    input_data = {"a": 1, "b": "hello", "c": True}
    assert compact_metadata(input_data) == input_data
