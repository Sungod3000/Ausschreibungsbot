from typing import Optional
import json
import requests

from ted_search_client import BASE_URL


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

        response = requests.post(
            f"{BASE_URL}/v3/notices/search",
            json=payload,
            timeout=30,
        )

        print(f"DEBUG - Response status: {response.status_code}")

        response.raise_for_status()
        data = response.json()

        # Get total count from API response
        total_count = data.get("totalNotices")
        print(f"DEBUG - API returned totalNotices: {total_count}")

        # Fallback: if API did not supply totalNotices, return None so caller can decide
        return total_count
    except Exception as e:
        print(f"DEBUG - Error getting total count: {str(e)}")
        return None
