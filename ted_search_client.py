""" TED Ausschreibungs-Search-Client - Read-Only API Client

A lean Python script for querying the TED (Tenders Electronic Daily) Search API
and exporting results as JSON or Excel.

Requires Python 3.12
Dependencies: requests, pandas, openpyxl
"""

import requests
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Callable
import os
from datetime import datetime
import time

# ------------------ global rate limiter ------------------
_MIN_API_INTERVAL = 0.35  # seconds – ~2.9 requests/second (cap at ~3 rps per API limits)
_last_api_call = 0.0

def _throttle_api() -> None:
    """Sleep just enough to keep overall request rate within TED limits."""
    global _last_api_call
    wait = _MIN_API_INTERVAL - (time.time() - _last_api_call)
    if wait > 0:
        time.sleep(wait)
    _last_api_call = time.time()

# Base URL for TED API
BASE_URL = "https://api.ted.europa.eu"


def ted_search(
    query: str,
    fields: Optional[List[str]] = None,
    page: int = 1,
    limit: int = 20,
    max_pages: Optional[int] = None,
    lang_filter: Optional[str] = None,
    progress_cb: Optional[Callable[[int, Optional[int], int, Optional[int]], None]] = None,
) -> List[Dict[str, Any]]:
    """Search TED notices with pagination support.
    
    Args:
        query: Expert syntax query string (e.g., "FT=\"kassel\"")
        fields: Optional list of fields to return; if None, a minimal default field list is used
        lang_filter: Optional ISO-3 language code (e.g., "DEU"). If set, only notices having a PDF in that language are kept
        page: Starting page number (default: 1)
        limit: Results per page (default: 20)
        max_pages: Maximum number of pages to retrieve (default: None = all pages)
        
    Returns:
        List of notice results
    """
    all_results: List[Dict[str, Any]] = []
    current_page = page
    start_page = page
    total_pages: Optional[int] = None  # unknown yet; will update after first response
    total_results: Optional[int] = None
    
    while True:
        # Build request payload
        payload = {
            "query": query,
            "page": current_page,
            "limit": limit,
            # Always include at least one valid field - 'notice-type' is a safe choice
            # The API requires the fields parameter to be present and not empty
            "fields": fields if fields else ["notice-type"]
        }
        
        try:
            retries = 0
            backoff = 5  # seconds – initial wait on 429
            while True:
                print(f"Fetching page {current_page} (attempt {retries+1})...")
                print(f"Request payload: {json.dumps(payload, indent=2)}")
                _throttle_api()
                
                response = requests.post(
                    f"{BASE_URL}/v3/notices/search",
                    json=payload,
                    timeout=30
                )
                if response.status_code != 429:
                    break
                # 429 Too Many Requests – honour Retry-After if present, else exponential back-off
                retry_after = int(response.headers.get("Retry-After", backoff))
                print(f"Received 429 Too Many Requests – sleeping {retry_after} s before retrying…")
                time.sleep(retry_after)
                retries += 1
                backoff = min(backoff * 2, 60)
                if retries >= 5:
                    response.raise_for_status()
            
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            
            # Try to get response content even if status code is not 200
            try:
                print(f"Response content: {response.text[:500]}...")
            except Exception as e:
                print(f"Could not print response content: {e}")
                
            # Now raise for status to handle errors
            response.raise_for_status()
            data = response.json()
            
            # Update total pages after first response if API sent total count
            if total_pages is None:
                total_results = data.get("totalNotices")
                if total_results is None:
                    total_results = data.get("totalNoticeCount")
                if total_results is not None:
                    tp = (int(total_results) + limit - 1) // limit
                    total_pages = tp
                    print(f"Found {total_results} results, expecting {total_pages} pages")
                else:
                    # API did not return total count – we'll continue until an empty page
                    total_pages = None
            
            # Add results to our collection
            results = data.get("notices", data.get("results", []))
            if lang_filter:
                results = [r for r in results if r.get('links', {}).get('pdf', {}).get(lang_filter)]
            all_results.extend(results)
            if progress_cb:
                progress_cb(current_page, total_pages, len(all_results), total_results)
            
            # Stop if no more results
            if not results:
                break
            
            # Enforce max_pages if set (relative to start_page)
            if max_pages is not None and (current_page - start_page + 1) >= max_pages:
                break
            
            # Stop if we reached the computed last page
            if total_pages is not None and current_page >= (start_page + total_pages - 1):
                break
            
            current_page += 1
            
        except requests.RequestException as e:
            print(f"Error fetching page {current_page}: {e}")
            break
    
    return all_results


def export_to_excel(data: List[Dict[str, Any]], filename: str) -> str:
    """Export results to Excel file.
    
    Args:
        data: List of notice results
        filename: Base filename (without extension)
        
    Returns:
        Path to the created Excel file
    """
    if not data:
        print("No data to export")
        return ""
    
    # Create DataFrame from results
    df = pd.json_normalize(data)
    
    # Add timestamp to filename to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = f"{filename}_{timestamp}.xlsx"
    
    # Export to Excel
    df.to_excel(excel_path, index=False)
    return excel_path


def export_to_json(data: List[Dict[str, Any]], filename: str) -> str:
    """Export results to JSON file.
    
    Args:
        data: List of notice results
        filename: Base filename (without extension)
        
    Returns:
        Path to the created JSON file
    """
    if not data:
        print("No data to export")
        return ""
    
    # Add timestamp to filename to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = f"{filename}_{timestamp}.json"
    
    # Export to JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return json_path


def main():
    """Main function to demonstrate the TED search client."""
    print("TED Ausschreibungs-Search-Client")
    print("--------------------------------")
    
    # Example: retrieve Hamburg notices and keep only German-language PDFs
    query = 'FT="Hamburg"'
    fields = ["publication-number", "publication-date"]
    
    print(f"Searching for: {query}")
    print("Retrieving data from TED API...")
    
    try:
        # Perform search with pagination (limit to 1 page for testing)
        results = ted_search(query=query, fields=fields, limit=50, max_pages=None, lang_filter="DEU")
        
        if results:
            print(f"Retrieved {len(results)} notices")
            
            # Export to Excel
            excel_file = export_to_excel(results, "ted_kassel")
            if excel_file:
                print(f"Exported to Excel: {excel_file}")
            
            # Export to JSON
            json_file = export_to_json(results, "ted_kassel")
            if json_file:
                print(f"Exported to JSON: {json_file}")
        else:
            print("No results found")
    except Exception as e:
        print(f"Error: {e}")
        print("Please check your internet connection and try again.")



if __name__ == "__main__":
    main()
