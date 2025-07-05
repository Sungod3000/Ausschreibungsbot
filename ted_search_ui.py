"""Gradio UI for TED expert-search client.

This lightweight UI lets users craft common TED expert-search queries via
simple form fields and download the raw XML of each returned notice.

Prerequisites
-------------
    pip install -r requirements.txt   # ensures gradio is present

Running
-------
    python ted_search_ui.py

The UI opens in the browser. Fill the fields, hit "Search & Download" and
wait for completion. Each run creates a folder named with the current date (dd.mm.yyyy)
inside the current working directory containing all XML files plus the JSON/Excel export that
`ted_search_client.ted_search` already writes.
"""
from __future__ import annotations

import json
import os
import re

import shutil
import pathlib
from datetime import datetime
from typing import List, Dict
import time

import gradio as gr
import requests

from ted_search_client import ted_search  # reuse the existing logic

# Official field alias mapping provided by user
SEARCH_FIELD_ALIASES = {
    # Geo
    "RC": "place-of-performance",
    "place-of-performance-country-proc": "place-of-performance-country-proc",
    "place-of-performance-subdiv-proc": "place-of-performance-subdiv-proc",

    # CPV & Verfahren
    "PC": "classification-cpv",
    "PR": "procedure-type",
    "notice-type": "notice-type",
    "TYPE_CONTRACT": "contract-nature",

    # Datumsfilter
    "PD": "publication-date",
    "DD": "deadline",  # generic
    "deadline-receipt-tender-date-lot": "deadline-receipt-tender-date-lot",

    # IDs & Auftraggeber
    "ND": "publication-number",
    "AU": "buyer-name",
    "CY": "buyer-country",
}

# ------------------- helper data ------------------------------------------------

GERMAN_NUTS_CODES = [
    # level-1 Bundesländer codes (DE1 … DE9)
    ("DE1", "Baden-Württemberg"),
    ("DE2", "Bayern"),
    ("DE3", "Berlin"),
    ("DE4", "Brandenburg"),
    ("DE5", "Bremen"),
    ("DE6", "Hamburg"),
    ("DE7", "Hessen"),
    ("DE8", "Mecklenburg-Vorpommern"),
    ("DE9", "Niedersachsen"),
    ("DEA", "Nordrhein-Westfalen"),
    ("DEB", "Rheinland-Pfalz"),
    ("DEC", "Saarland"),
    ("DED", "Sachsen"),
    ("DEE", "Sachsen-Anhalt"),
    ("DEF", "Schleswig-Holstein"),
    ("DEG", "Thüringen"),
]

# notice-type label to API code mapping (subset)
_NOTICE_TYPE_MAP = {
    "Contract notice – standard": "cn-standard",
    "Contract notice – light": "cn-social",
    "Contract award – standard": "can-standard",
    "Contract award – light": "can-social",
    "Contract modification": "can-modif",
    "Prior information only": "pin-only",
    "Voluntary ex-ante transparency": "veat",
}
NOTICE_TYPES = list(_NOTICE_TYPE_MAP.keys())

PROCEDURE_TYPES = [
    "OPEN",
    "RESTRICTED",
    "NEGOTIATED",
    "COMPETITIVE_DIALOGUE",
]

CONTRACT_TYPES = [
    "services",
    "supplies",
    "works",
]

# ------------------- query builder ---------------------------------------------

# Mapping from UI labels to canonical TED values
# procedure type values are already API codes
_PROCEDURE_TYPE_MAP = {
    "OPEN": "OPEN",
    "RESTRICTED": "RESTRICTED",
    "NEGOTIATED": "NEGOTIATED",
    "COMPETITIVE_DIALOGUE": "COMPETITIVE_DIALOGUE",
}
# contract types in UI already match API but keep map for clarity
_CONTRACT_TYPE_MAP = {
    "services": "services",
    "supplies": "supplies",
    "works": "works",
}


def build_expert_query(
    region_code: str,
    cpv: str,
    notice_type: str | None,
    procedure_type: str | None,
    contract_type: str | None,
    pub_date_from: str | None,
    pub_date_to: str | None,
    deadline_to: str | None,
    buyer_name: str | None,
    lot_no: str | None,
    value_min: int | None,
    value_max: int | None,
) -> str:
    """Compose TED expert-search query string from UI inputs.

    Rules: • Values containing spaces are quoted. • Criteria are AND-combined.
    """
    parts: List[str] = []  # country implicitly Germany by using DE* NUTS codes

    if region_code:
        region_code_only = region_code.split()[0]  # take "DE6" from "DE6 – Hamburg"
        # Use correct alias for region/NUTS filter (RC = place-of-performance)
        parts.append(f"RC=\"{region_code_only}\"")
    if cpv:
        parts.append(f"PC=\"{cpv}\"")

    if notice_type:
        parts.append(f"notice-type={_NOTICE_TYPE_MAP.get(notice_type, notice_type)}")
    if procedure_type:
        parts.append(f"PR=\"{_PROCEDURE_TYPE_MAP.get(procedure_type, procedure_type)}\"")
    if contract_type:
        parts.append(f"NC=\"{_CONTRACT_TYPE_MAP.get(contract_type, contract_type)}\"")
    if pub_date_from or pub_date_to:
        from_str = pub_date_from if pub_date_from else "*"
        to_str = pub_date_to if pub_date_to else "*"
        parts.append(f"PD>={from_str} AND PD<={to_str}")
    if deadline_to:
        parts.append(f"DD<=\"{deadline_to}\"")
    if buyer_name:
        buyer_escaped = buyer_name.replace('"', "\"")
        parts.append(f"AU=\"{buyer_escaped}\"")
    if lot_no:
        parts.append(f"LOT_NUMBER=\"{lot_no}\"")
    # Contract value filter currently commented out – suitable alias not confirmed in provided mapping
    # if value_min is not None or value_max is not None:
    #     vmin = value_min if value_min is not None else 0
    #     vmax = value_max if value_max is not None else 10**12
    #     parts.append(f"VAL>={vmin} AND VAL<={vmax}")  # TODO: replace VAL with correct alias when known

    return " AND ".join(parts)

# ------------------- download helpers ------------------------------------------

def save_pdf_files(notices: List[Dict], folder: pathlib.Path, lang: str = "DEU") -> None:
    """Fetch and store PDF for each notice in the desired language."""
    folder.mkdir(parents=True, exist_ok=True)
    for n in notices:
        pub_no = n.get("publication-number")
        pdf_url = n.get("links", {}).get("pdf", {}).get(lang)
        if not pdf_url:
            continue
        try:
            r = requests.get(pdf_url, timeout=30)
            r.raise_for_status()
            pdf_path = folder / f"{pub_no}.pdf"
            with pdf_path.open("wb") as f:
                f.write(r.content)
            time.sleep(1.0)
        except Exception as exc:
            print(f"Failed to download PDF for {pub_no}: {exc}")

def save_xml_files(notices: List[Dict], folder: pathlib.Path) -> None:
    """Fetch and store XML for each notice (multilingual XML link)."""
    folder.mkdir(parents=True, exist_ok=True)
    for n in notices:
        pub_no = n.get("publication-number")
        xml_url = n.get("links", {}).get("xml", {}).get("MUL")
        if not xml_url:
            continue
        try:
            r = requests.get(xml_url, timeout=30)
            r.raise_for_status()
            xml_path = folder / f"{pub_no}.xml"
            with xml_path.open("wb") as f:
                f.write(r.content)
            # Respect TED limit ~600 downloads / 6 min (≈1.6/s)
            time.sleep(1.0)
        except Exception as exc:
            print(f"Failed to download XML for {pub_no}: {exc}")

# ------------------- Gradio actions -------------------------------------------

def run_search(region, cpv, notice_type, procedure_type, contract_type,
               pub_from, pub_to, deadline_to, buyer, lot_no, value_range, download_types,
               max_results):
    """Run TED search and save results.
    Returns a status string for the UI. In case of errors we return the
    exception message so the user sees what went wrong instead of just
    a generic "Error" message from Gradio.
    """
    # Handle slider returning either a tuple (min,max) or a single int
    if isinstance(value_range, (list, tuple)) and len(value_range) == 2:
        value_min, value_max = value_range
    else:
        # Slider returned a single int; treat it as max value with no minimum
        value_min, value_max = 0, value_range if value_range else None
    query = build_expert_query(
        region_code=region,
        cpv=cpv.strip(),
        notice_type=notice_type or None,
        procedure_type=procedure_type or None,
        contract_type=contract_type or None,
        pub_date_from=pub_from.replace("-", "") if pub_from else None,
        pub_date_to=pub_to.replace("-", "") if pub_to else None,
        deadline_to=deadline_to.replace("-", "") if deadline_to else None,
        buyer_name=buyer.strip() if buyer else None,
        lot_no=lot_no.strip() if lot_no else None,
        value_min=value_min if value_min else None,
        value_max=value_max if value_max else None,
    )

    human_date = datetime.now().strftime("%d.%m.%Y")
    safe_query = re.sub(r"[^A-Za-z0-9_-]+", "_", query)[:50]
    out_dir = pathlib.Path(f"search_{human_date}_{safe_query}")

    # perform TED search – we return German PDFs by default (lang filter)
    try:
        notices = ted_search(query=query, fields=["publication-number", "publication-date"], limit=int(max_results), lang_filter="DEU")
    except Exception as exc:
        return f"TED search failed: {exc}"

    # save JSON & Excel via existing export helpers
    json_path = out_dir / "results.json"
    excel_path = out_dir / "results.xlsx"
    out_dir.mkdir(exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(notices, f, ensure_ascii=False, indent=2)

    try:
        import pandas as pd
        import openpyxl  # noqa: F401 – required by pandas for excel
        pd.DataFrame(notices).to_excel(excel_path, index=False)
    except Exception as exc:
        print(f"Excel export failed: {exc}")

    # download selected file types
    if "XML" in download_types:
        save_xml_files(notices, out_dir / "xml")
    if "PDF" in download_types:
        save_pdf_files(notices, out_dir / "pdf")

    return f"Saved {len(notices)} notices to {out_dir}"

# ------------------- build UI --------------------------------------------------

# Use Gradio built-in monochrome theme which adapts to dark mode automatically
with gr.Blocks(title="TED Expert-Search UI", theme="gradio/monochrome") as demo:
    gr.Markdown("""# TED Expert-Search (Deutschland)
Fill the fields below to craft an expert query. Empty fields are ignored.
""")

    with gr.Row():
        region = gr.Dropdown([f"{code} – {label}" for code, label in GERMAN_NUTS_CODES],
                             label="Region (NUTS)", value="DE6 – Hamburg", interactive=True)
        cpv = gr.Textbox(label="CPV-Hauptcode", placeholder="z. B. 79412000", interactive=True)
        procedure_type = gr.Dropdown([''] + [t for t in PROCEDURE_TYPES if t], label="Verfahrensart", value='')
        notice_type = gr.Dropdown([''] + NOTICE_TYPES, label="Formtyp", value='')

    with gr.Row():
        contract_type = gr.Dropdown([''] + [t for t in CONTRACT_TYPES if t], label="Vertragsart", value='')
        pub_from = gr.Textbox(label="Veröffentlichung ab (YYYYMMDD)", placeholder="20250101")
        pub_to = gr.Textbox(label="Veröffentlichung bis (YYYYMMDD)", placeholder="20251231")
        deadline = gr.Textbox(label="Einreichfrist bis (YYYYMMDD)", placeholder="20250831")



    with gr.Row():
        buyer = gr.Textbox(label="Auftraggeber-Name", interactive=True)
        lot_no = gr.Number(label="Losnummer")
        value_range = gr.Slider(0, 1000000, value=0, step=1000, label="Geschätzter Wert € (Min/Max)", interactive=True)

    download_types = gr.CheckboxGroup(["XML", "PDF"], label="Dateitypen herunterladen", value=["XML"], interactive=True)

    max_results = gr.Number(value=25, precision=0, label="Max. Treffer", interactive=True)

    out = gr.Textbox(label="Status", interactive=False)
    run_btn = gr.Button("Search & Download")

    run_btn.click(
        fn=run_search,
        inputs=[
            region, cpv, notice_type, procedure_type, contract_type,
            pub_from, pub_to, deadline, buyer, lot_no, value_range, download_types, max_results
        ],
        outputs=out,
    )

if __name__ == "__main__":
    demo.launch()
