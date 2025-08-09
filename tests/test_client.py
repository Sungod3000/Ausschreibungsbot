from typing import List, Dict

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import responses

from ted_search_client import ted_search, BASE_URL


def _notice(pub_no: str, langs: List[str]) -> Dict:
    return {
        "publication-number": pub_no,
        "links": {
            "pdf": {lang: f"https://example/{pub_no}_{lang}.pdf" for lang in langs}
        },
    }


def test_ted_search_pagination_with_total_notices():
    # limit=2 so we expect two pages when totalNotices=3
    page1 = {
        "totalNotices": 3,
        "notices": [
            _notice("1-2025", ["DEU"]),
            _notice("2-2025", ["DEU", "ENG"]),
        ],
    }
    page2 = {
        "totalNotices": 3,
        "notices": [
            _notice("3-2025", ["ENG"]),
        ],
    }

    with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
        rsps.add(responses.POST, f"{BASE_URL}/v3/notices/search", json=page1, status=200)
        rsps.add(responses.POST, f"{BASE_URL}/v3/notices/search", json=page2, status=200)

        results = ted_search(query='RC="DE"', fields=["publication-number"], limit=2)
        assert len(results) == 3
        assert {r.get("publication-number") for r in results} == {"1-2025", "2-2025", "3-2025"}


def test_ted_search_pagination_without_total_uses_max_pages():
    # API omits totalNotices; we set max_pages=2; provide two non-empty pages
    page1 = {
        "notices": [
            _notice("1-2025", ["DEU"]),
        ],
    }
    page2 = {
        "notices": [
            _notice("2-2025", ["ENG"]),
        ],
    }

    with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
        rsps.add(responses.POST, f"{BASE_URL}/v3/notices/search", json=page1, status=200)
        rsps.add(responses.POST, f"{BASE_URL}/v3/notices/search", json=page2, status=200)

        results = ted_search(query='RC="DE"', fields=["publication-number"], limit=50, max_pages=2)
        assert len(results) == 2
        assert {r.get("publication-number") for r in results} == {"1-2025", "2-2025"}


def test_ted_search_lang_filter_keeps_only_given_language():
    page1 = {
        "totalNotices": 2,
        "notices": [
            _notice("1-2025", ["DEU"]),
            _notice("2-2025", ["ENG"])  # no DEU
        ],
    }

    with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
        rsps.add(responses.POST, f"{BASE_URL}/v3/notices/search", json=page1, status=200)

        results = ted_search(query='RC="DE"', fields=["publication-number"], limit=50, max_pages=1, lang_filter="DEU")
        assert len(results) == 1
        assert results[0].get("publication-number") == "1-2025"
