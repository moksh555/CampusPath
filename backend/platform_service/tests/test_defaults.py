from types import SimpleNamespace

from app.services.defaults import build_chat_title, slugify, unique_column_key


def test_slugify() -> None:
    assert slugify("Course Ranking") == "course-ranking"
    assert slugify("!!!") == "column"


def test_unique_column_key_avoids_collisions() -> None:
    assert unique_column_key("Ranking", set()) == "ranking"
    assert unique_column_key("Ranking", {"ranking"}) == "ranking-2"
    assert unique_column_key("Ranking", {"ranking", "ranking-2"}) == "ranking-3"


def test_build_chat_title() -> None:
    colleges = [
        SimpleNamespace(name="MIT"),
        SimpleNamespace(name="CMU"),
        SimpleNamespace(name="UT"),
    ]
    assert build_chat_title("CS", colleges) == "MIT, CMU +1"
    assert build_chat_title("Computer Science", []) == "Computer Science"
    assert build_chat_title(None, []) == "Untitled"
