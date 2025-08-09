from typing import Optional
import json
import requests

from ted_search_client import BASE_URL, _throttle_api


def get_total_count_from_api(query: str) -> Optional[int]:
    """Get the true total count from TED API without fetching all results.
    Behaviour preserved from UI implementation.
    """
    try:
        # Make a single API call with minimal data to get totalNotices
        payload = {
            "query": query,
            "page": 1,
            "limit": 1,  # Minimal limit to get count
            "fields": ["notice-type"],  # Minimal field set
        }

        print(f"DEBUG - Getting total count for query: {query}")
        print(f"DEBUG - Payload: {json.dumps(payload, indent=2)}")

        # throttle to ~3 req/s and handle 429
        retries = 0
        backoff = 5
        while True:
            _throttle_api()
            response = requests.post(
                f"{BASE_URL}/v3/notices/search",
                json=payload,
                timeout=30,
            )
            if response.status_code != 429:
                break
            retry_after = int(response.headers.get("Retry-After", backoff))
            print(f"DEBUG - Count got 429; sleeping {retry_after}s…")
            import time as _t
            _t.sleep(retry_after)
            retries += 1
            backoff = min(backoff * 2, 60)
            if retries >= 5:
                response.raise_for_status()

        print(f"DEBUG - Response status: {response.status_code}")

        response.raise_for_status()
        data = response.json()

        # Get total count from API response (support both keys)
        raw_total = data.get("totalNotices")
        src = "totalNotices"
        if raw_total is None:
            raw_total = data.get("totalNoticeCount")
            src = "totalNoticeCount"
        print(f"DEBUG - API returned {src}: {raw_total}")

        # Coerce to int when possible; otherwise None
        try:
            total_count = int(raw_total) if raw_total is not None else None
        except (TypeError, ValueError):
            total_count = None

        # Fallback: if API did not supply a usable total, return None so caller can decide
        return total_count
    except Exception as e:
        print(f"DEBUG - Error getting total count: {str(e)}")
        return None
