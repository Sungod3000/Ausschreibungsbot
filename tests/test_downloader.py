import os
import sys
import time
from typing import Optional

import responses

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.downloader import download_with_rate_limit


@responses.activate
def test_download_success_writes_file_and_reports_size(tmp_path):
    url = "https://example.com/file.bin"
    content = b"hello world"
    responses.add(responses.GET, url, body=content, status=200)

    dest_path = tmp_path / "out" / "file.bin"

    success, size, err, new_last = download_with_rate_limit(
        url=str(url),
        dest_path=str(dest_path),
        last_request_time=0.0,  # long ago, no sleep
        min_interval=0.2,
        timeout=5,
    )

    assert success is True
    assert err is None
    assert size == len(content)
    assert os.path.exists(dest_path)
    assert os.path.getsize(dest_path) == len(content)
    assert isinstance(new_last, float) and new_last > 0


@responses.activate
def test_download_http_error_returns_failure(tmp_path):
    url = "https://example.com/err.bin"
    responses.add(responses.GET, url, body="boom", status=500)

    dest_path = tmp_path / "out" / "err.bin"

    success, size, err, new_last = download_with_rate_limit(
        url=str(url),
        dest_path=str(dest_path),
        last_request_time=time.time(),  # may trigger short sleep
        min_interval=0.01,
        timeout=5,
    )

    assert success is False
    assert size is None
    assert err is not None and len(err) > 0
    # file should not be created on failure
    assert not os.path.exists(dest_path)
    assert isinstance(new_last, float) and new_last > 0
