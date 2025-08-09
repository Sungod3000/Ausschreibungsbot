"""
Generate Germany NUTS hierarchy JSON (v2021) for the UI dropdowns.

Output file: config/nuts_de.json
Structure:
{
  "NUTS1": {
    "DE1": {"name": "Baden-Württemberg", "children": {
      "DE11": {"name": "Stuttgart", "children": {
        "DE111": {"name": "Stuttgart, Stadtkreis"},
        ...
      }},
      ...
    }},
    ...
  }
}

Requires: requests
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Dict, Any

import requests

DATA_URL = "https://raw.githubusercontent.com/datumorphism/dataset-eu-nuts/master/dataset/nuts_v2021__2021_.json"
ROOT = os.path.dirname(os.path.dirname(__file__))
OUTPUT = os.path.join(ROOT, "config", "nuts_de.json")


def fetch_dataset() -> Dict[str, Any]:
    r = requests.get(DATA_URL, timeout=30)
    r.raise_for_status()
    return r.json()


def build_hierarchy(ds: Dict[str, Any]) -> Dict[str, Any]:
    nuts1_list = [x for x in ds.get("nuts_1", []) if x["code"].startswith("DE") and x["code"] != "DEZ"]
    nuts2_list = [x for x in ds.get("nuts_2", []) if x["code"].startswith("DE") and x["code"] not in ("DEZZ",)]
    nuts3_list = [x for x in ds.get("nuts_3", []) if x["code"].startswith("DE") and x["code"] not in ("DEZZZ",)]

    # Index by code
    n1 = {x["code"]: x["value"] for x in nuts1_list}
    n2 = {x["code"]: x["value"] for x in nuts2_list}
    n3 = {x["code"]: x["value"] for x in nuts3_list}

    # Map parents: NUTS2 parent is first 3 chars (e.g., DE1 -> NUTS1), NUTS3 parent is first 4 or 5? In DE, NUTS2 is 3 or 4 chars? For DE it's 3 or 4 incl digits; parent for NUTS2 is first 3 (DE1, DE2, ...). For NUTS3 parent is first 4 (e.g., DE11 -> DE111..DE11A). We'll use length-based rule.
    def parent_n1(code: str) -> str:
        return code[:3]  # DE1, DE2, ...

    def parent_n2(code: str) -> str:
        return code[:4]  # DE11, DE12, DE13, ... or DE30, DE40, etc.

    # Build children mapping
    children_n1: Dict[str, Dict[str, Any]] = defaultdict(dict)
    for code, name in n2.items():
        p = parent_n1(code)
        if p in n1:
            children_n1[p][code] = {"name": name, "children": {}}

    children_n2: Dict[str, Dict[str, Any]] = defaultdict(dict)
    for code, name in n3.items():
        p = parent_n2(code)
        # Some NUTS3 parents like DE300 (Berlin) have NUTS2 as DE30, which exists
        if p in n2:
            children_n2[p][code] = {"name": name}

    # Merge NUTS3 under NUTS2 nodes
    for n2_code, kids in children_n2.items():
        # Find which NUTS1 this NUTS2 belongs to
        n1_code = parent_n1(n2_code)
        if n1_code in children_n1 and n2_code in children_n1[n1_code]:
            children_n1[n1_code][n2_code]["children"] = kids

    # Build final hierarchy
    result = {"NUTS1": {}}
    for n1_code, n1_name in n1.items():
        result["NUTS1"][n1_code] = {
            "name": n1_name,
            "children": children_n1.get(n1_code, {}),
        }
    return result


def main() -> None:
    print("Fetching NUTS dataset…")
    ds = fetch_dataset()
    print("Building Germany hierarchy…")
    hier = build_hierarchy(ds)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(hier, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUTPUT} ({len(hier['NUTS1'])} NUTS1 regions)")


if __name__ == "__main__":
    main()
