import re
from typing import Optional

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import responses

from ted_search_client import BASE_URL
from core.naming import make_download_folder_name
from core.count import get_total_count_from_api


def test_create_download_folder_name_contains_expected_parts():
    query = 'RC="DE1" AND PD>=20250720 AND PD<=20250722 AND NT="cn-standard"'
    folder = make_download_folder_name(query, ["pdf_de", "json_en"])

    # Timestamp prefix: accept legacy YYYYMMDD_HHMMSS_ or new DD.MM.YYYY_HHMMSS_
    ts_ok = bool(re.match(r"^\d{8}_\d{6}_", folder)) or bool(re.match(r"^\d{2}\.\d{2}\.\d{4}_\d{6}_", folder))
    assert ts_ok, folder

    # Contains RC, dates and formats (order may vary slightly depending on code)
    assert "RC_DE1" in folder
    # Support legacy YYYYMMDD and new German dd.mm.yyyy patterns
    has_from = ("from_20250720" in folder) or ("PD_20250720" in folder) or ("PD_20.07.2025" in folder)
    has_to = ("to_20250722" in folder) or ("_to_20250722" in folder) or ("_to_22.07.2025" in folder)
    assert has_from, folder
    assert has_to, folder
    assert "pdf_de" in folder and "json_en" in folder


def test_get_total_count_from_api_success(monkeypatch):
    query = 'RC="DE1"'

    with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
        rsps.add(
            responses.POST,
            f"{BASE_URL}/v3/notices/search",
            json={"totalNotices": 123, "notices": []},
            status=200,
        )
        total: Optional[int] = get_total_count_from_api(query)
        assert total == 123


def test_get_total_count_from_api_missing_total_returns_none():
    query = 'RC="DE1"'

    with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
        rsps.add(
            responses.POST,
            f"{BASE_URL}/v3/notices/search",
            json={"notices": []},
            status=200,
        )
        total = get_total_count_from_api(query)
        assert total is None


def test_get_total_count_from_api_http_error_returns_none():
    query = 'RC="DE1"'

    with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
        rsps.add(
            responses.POST,
            f"{BASE_URL}/v3/notices/search",
            json={"error": "bad"},
            status=500,
        )
        total = get_total_count_from_api(query)
        assert total is None
