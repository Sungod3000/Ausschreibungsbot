"""
Core downloader utilities.

Provides a rate-limited file download function used by the UI.
This module contains no Streamlit dependencies and uses logging for diagnostics.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)


def download_with_rate_limit(
    url: str,
    dest_path: str,
    last_request_time: float,
    *,
    min_interval: float = 0.2,  # 5 requests/sec
    timeout: int = 30,
) -> Tuple[bool, Optional[int], Optional[str], float]:
    """
    Download a URL to dest_path while enforcing a minimum interval between requests.

    Returns (success, file_size, error_message, new_last_request_time).
    """
    try:
        # Enforce rate limit
        now = time.time()
        elapsed = now - last_request_time
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.debug("Rate limiting: sleeping %.2fs", sleep_time)
            time.sleep(sleep_time)

        # Perform request
        start = time.time()
        response = requests.get(url, timeout=timeout)
        new_last_request_time = start  # time of request initiation
        logger.debug("HTTP %s for %s (len=%d)", response.status_code, url, len(response.content))
        response.raise_for_status()

        # Ensure directory exists
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Write file
        with open(dest_path, "wb") as f:
            f.write(response.content)

        # Verify
        if os.path.exists(dest_path):
            size = os.path.getsize(dest_path)
            return True, size, None, new_last_request_time
        else:
            return False, None, "file not found after write", new_last_request_time

    except Exception as e:
        logger.exception("Download failed for %s -> %s: %s", url, dest_path, e)
        # Use current time as new last_request_time so subsequent calls respect spacing
        return False, None, str(e), time.time()
