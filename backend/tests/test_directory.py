from unittest.mock import patch

import pytest

from app.services import college_directory as directory


@pytest.fixture(autouse=True)
def clear_cache():
    directory._load.cache_clear()
    yield
    directory._load.cache_clear()


def test_search_normalizes_deduplicates_and_caches():
    with patch("app.services.college_directory.httpx.Client") as client:
        client.return_value.__enter__.return_value.get.return_value.json.return_value = [
            {"name": " Example University ", "country": "Canada"},
            {"name": "EXAMPLE UNIVERSITY", "country": "Canada"},
            {"name": "Other Institute", "country": "Canada"},
            {"name": None},
            "invalid",
        ]
        assert directory.search("example canada")[0].name == "Example University"
        assert len(directory.search("CANADA")) == 2
        assert client.call_count == 1


def test_empty_query_avoids_network():
    with patch("app.services.college_directory.httpx.Client") as client:
        assert directory.search("   ") == []
        client.assert_not_called()


def test_malformed_dataset_rejected():
    with patch("app.services.college_directory.httpx.Client") as client:
        client.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "error": "unavailable"
        }
        with pytest.raises(ValueError):
            directory.search("Example")


def test_result_limit():
    with patch("app.services.college_directory.httpx.Client") as client:
        client.return_value.__enter__.return_value.get.return_value.json.return_value = [
            {"name": f"University {n}"} for n in range(30)
        ]
        assert len(directory.search("university")) == 12


def test_full_directory_is_not_limited_and_reuses_cache():
    with patch("app.services.college_directory.httpx.Client") as client:
        client.return_value.__enter__.return_value.get.return_value.json.return_value = [
            {"name": f"University {n}", "country": "Canada"} for n in range(30)
        ]
        assert len(directory.list_universities()) == 30
        assert len(directory.search("university")) == 12
        assert client.call_count == 1
