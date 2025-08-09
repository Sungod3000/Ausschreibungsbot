import re
from datetime import datetime
from typing import List


def make_download_folder_name(query: str, download_types: List[str], timestamp: str | None = None) -> str:
    """Create a folder name based on search parameters.
    This mirrors the logic previously embedded in fetch_results() to preserve behavior.
    Pattern example: YYYYMMDD_HHMMSS_RC_DE1_PD_20250720_to_20250722_pdf_de_json_en
    """
    ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_parts = [ts]

    # RC part
    if 'RC=' in query:
        rc_match = re.search(r'RC="?([^"\s]+)"?', query)
        if rc_match:
            folder_parts.append(f"RC_{rc_match.group(1)}")

    # PD part (from/to or single)
    if 'PD>=' in query or 'PD<=' in query:
        pd_matches = re.findall(r'PD[><=]+([0-9]{8})', query)
        if len(pd_matches) >= 2:
            folder_parts.append(f"PD_{pd_matches[0]}_to_{pd_matches[1]}")
        elif pd_matches:
            folder_parts.append(f"PD_{pd_matches[0]}")

    # download types (sorted for stability)
    if download_types:
        folder_parts.append("_".join(sorted(download_types)))

    # Join and limit length
    folder_name = "_".join(folder_parts)
    if len(folder_name) > 100:
        folder_name = folder_name[:100]

    # replace invalid chars for Windows
    folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
    return folder_name
