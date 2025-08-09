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
    min_interval: float = 0.2,  # 5 requests/sec (UI may override to ~0.35s)
    timeout: int = 30,
    max_retries: int = 5,
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

        # Perform request with 429 retry handling
        attempt = 0
        backoff = 1.0
        new_last_request_time = last_request_time
        while True:
            start = time.time()
            response = requests.get(url, timeout=timeout)
            new_last_request_time = start  # time of request initiation
            status = response.status_code
            content_len = len(response.content) if getattr(response, "content", None) is not None else -1
            logger.debug("HTTP %s for %s (len=%d)", status, url, content_len)

            # 429 Too Many Requests: honor Retry-After when present
            if status == 429:
                attempt += 1
                if attempt > max_retries:
                    response.raise_for_status()
                retry_after_hdr = response.headers.get("Retry-After")
                try:
                    retry_after = float(retry_after_hdr) if retry_after_hdr is not None else None
                except Exception:
                    retry_after = None
                # Fallback exponential backoff when header missing
                delay = retry_after if retry_after is not None else min(backoff, 30.0)
                logger.warning("429 Too Many Requests for %s. Sleeping %.2fs before retry #%d", url, delay, attempt)
                time.sleep(delay)
                backoff = min(backoff * 2.0, 30.0)
                # After sleeping, loop to retry (min_interval will be enforced on next call by caller's last_request_time)
                continue

            # For other non-429 statuses, break and let raise_for_status() handle errors
            response.raise_for_status()
            break

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
