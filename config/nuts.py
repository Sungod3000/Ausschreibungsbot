from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Dict, Any, Optional

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "nuts_de.json")


@lru_cache(maxsize=1)
def load_nuts_de(path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load Germany NUTS hierarchy from a local JSON file.
    Returns a dict with keys: {"NUTS1": { code: {"name": str, "children": { nuts2: {"name": str, "children": { nuts3: {"name": str} } } } } } }
    """
    p = path or DEFAULT_PATH
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
