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

# Official field alias mapping provided by user with descriptions and options
SEARCH_FIELD_ALIASES = {
    # Full text search
    "FT": {
        "alias": "full-text",
        "description": "Suche im gesamten Text der Ausschreibung",
        "example": 'FT~("school building")',
        "options": None
    },
    
    # IDs & Publication
    "ND": {
        "alias": "publication-number",
        "description": "Ausschreibungsnummer",
        "example": '"12345678-2025"',
        "options": None
    },
    "gazette-issue-id": {
        "alias": "gazette-issue-id",
        "description": "OJ S Ausgabe (Nr/Jahr)",
        "example": "180-2025",
        "options": None
    },
    
    # Geo
    "RC": {
        "alias": "place-of-performance",
        "description": "Ausführungsort (Land / NUTS / PLZ)",
        "example": '"DE" · "DE71" · "34117"',
        "options": None
    },
    "place-of-performance-country-proc": {
        "alias": "place-of-performance-country-proc",
        "description": "Land des Ausführungsorts",
        "example": '"DE"',
        "options": None
    },
    "place-of-performance-subdiv-proc": {
        "alias": "place-of-performance-subdiv-proc",
        "description": "Region des Ausführungsorts",
        "example": '"DE71"',
        "options": None
    },
    
    # Auftraggeber
    "CY": {
        "alias": "buyer-country",
        "description": "Land des Auftraggebers",
        "example": '"DE"',
        "options": None
    },
    "AU": {
        "alias": "buyer-name",
        "description": "Name des Auftraggebers",
        "example": '"Stadt Kassel"',
        "options": None
    },
    "authority-main-activity": {
        "alias": "authority-main-activity",
        "description": "Main activity of the contracting authority",
        "example": "hc-am (Housing and community amenities), education, health",
        "options": [
            "airport", "defence", "econ-aff", "education", "electricity", "env-pro", 
            "gas-heat", "gas-oil", "gen-pub", "hc-am", "health", "port", "post", 
            "pub-os", "rail", "rcr", "soc-pro", "solid-fuel", "urttb", "water"
        ],
        "option_labels": {
            "airport": "Airport-related activities",
            "defence": "Defence",
            "econ-aff": "Economic affairs",
            "education": "Education",
            "electricity": "Electricity-related activities",
            "env-pro": "Environmental protection",
            "gas-heat": "Production, transport or distribution of gas or heat",
            "gas-oil": "Extraction of gas or oil",
            "gen-pub": "General public services",
            "hc-am": "Housing and community amenities",
            "health": "Health",
            "port": "Port-related activities",
            "post": "Postal services",
            "pub-os": "Public order and safety",
            "rail": "Railway services",
            "rcr": "Recreation, culture and religion",
            "soc-pro": "Social protection",
            "solid-fuel": "Exploration or extraction of coal or other solid fuels",
            "urttb": "Urban railway, tramway, trolleybus or bus services",
            "water": "Water-related activities"
        }
    }, 
    # CPV & Verfahren
    "PC": {
        "alias": "classification-cpv",
        "description": "CPV-Hauptcode",
        "example": '"45214200"',
        "options": None
    },
    "classification-cpv-lot": {
        "alias": "classification-cpv-lot",
        "description": "CPV-Zusatzcodes (Los)",
        "example": '"71320000"',
        "options": None
    },
    "NC": {
        "alias": "contract-nature",
        "description": "Art des Auftrags",
        "example": "works | supplies | services",
        "options": ["works", "supplies", "services"]
    },
    "PR": {
        "alias": "procedure-type",
        "description": "Verfahrensart",
        "example": "OPEN / RESTRICTED",
        "options": ["OPEN", "RESTRICTED", "NEGOTIATED", "COMPETITIVE_DIALOGUE"]
    },
    "notice-type": {
        "alias": "notice-type",
        "description": "Bekanntmachungstyp / Formtyp",
        "example": "cn-standard / can-standard",
        "options": ["cn-standard", "cn-social", "can-standard", "can-social", "can-modif", "pin-only", "veat"]
    },
    "legal-basis-notice": {
        "alias": "legal-basis-notice",
        "description": "Rechtsgrundlage",
        "example": '"2014/24/EU"',
        "options": ["2014/24/EU", "2014/25/EU", "2009/81/EC", "2014/23/EU"]
    },
    
    # Datumsfilter
    "PD": {
        "alias": "publication-date",
        "description": "Veröffentlichungsdatum",
        "example": ">=20250101",
        "options": None
    },
    "DD": {
        "alias": "deadline",
        "description": "Einreichfrist (generisch)",
        "example": "<=20251231",
        "options": None
    },
    "deadline-receipt-tender-date-lot": {
        "alias": "deadline-receipt-tender-date-lot",
        "description": "Einreichfrist für Angebote",
        "example": "<=20251231",
        "options": None
    },
    
    # Lot information
    "LOT_NUMBER": {
        "alias": "lot-number",
        "description": "Losnummer",
        "example": '"1"',
        "options": None
    }
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
    region_code: str = None,
    cpv: str = None,
    cpv_lot: str = None,
    notice_type: str = None,
    procedure_type: str = None,
    contract_type: str = None,
    legal_basis: str = None,
    pub_date_from: str = None,
    pub_date_to: str = None,
    deadline_to: str = None,
    buyer_name: str = None,
    buyer_country: str = None,
    authority_activity: str = None,
    lot_no: str = None,
    pub_number: str = None,
    gazette_id: str = None,
    value_min: int = None,
    value_max: int = None,
    full_text: str = None,
) -> str:
    """Compose TED expert-search query string from UI inputs.

    Rules: • Values containing spaces are quoted. • Criteria are AND-combined.
    """
    parts: List[str] = []  # country implicitly Germany by using DE* NUTS codes

    # Full text search
    if full_text:
        parts.append(f"FT~(\"{full_text}\")")

    # Geographic information
    if region_code:
        region_code_only = region_code.split()[0]  # take "DE6" from "DE6 – Hamburg"
        # Use correct alias for region/NUTS filter (RC = place-of-performance)
        parts.append(f"RC=\"{region_code_only}\"")
    
    # CPV codes
    if cpv:
        parts.append(f"PC=\"{cpv}\"")
    if cpv_lot:
        parts.append(f"classification-cpv-lot=\"{cpv_lot}\"")

    # Procedure, notice, and contract types
    if notice_type:
        parts.append(f"notice-type={_NOTICE_TYPE_MAP.get(notice_type, notice_type)}")
    if procedure_type:
        parts.append(f"PR=\"{_PROCEDURE_TYPE_MAP.get(procedure_type, procedure_type)}\"")
    if contract_type:
        parts.append(f"NC=\"{contract_type}\"")
    if legal_basis:
        parts.append(f"legal-basis-notice=\"{legal_basis}\"")

    # Date filters
    if pub_date_from or pub_date_to:
        from_str = pub_date_from if pub_date_from else "*"
        to_str = pub_date_to if pub_date_to else "*"
        parts.append(f"PD>={from_str} AND PD<={to_str}")
    if deadline_to:
        parts.append(f"DD=\"{deadline_to}\"")

    # Buyer information
    if buyer_name:
        buyer_escaped = buyer_name.replace('"', "\"")
        parts.append(f"AU=\"{buyer_escaped}\"")
    if buyer_country:
        parts.append(f"CY=\"{buyer_country}\"")
    if authority_activity:
        parts.append(f"authority-main-activity=\"{authority_activity}\"")

    # Publication and lot information
    if lot_no:
        parts.append(f"LOT_NUMBER=\"{lot_no}\"")
    if pub_number:
        parts.append(f"ND=\"{pub_number}\"")
    if gazette_id:
        parts.append(f"gazette-issue-id=\"{gazette_id}\"")

    # Contract value filter currently commented out – suitable alias not confirmed
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

def run_search(full_text, region, cpv, cpv_lot, notice_type, procedure_type, contract_type,
               legal_basis, pub_from, pub_to, deadline_to, buyer, buyer_country, authority_activity,
               lot_no, pub_number, gazette_id, value_range, download_types, max_results):
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

    # Build expert query from UI inputs
    query = build_expert_query(
        region_code=region,
        cpv=cpv.strip() if cpv else None,
        cpv_lot=cpv_lot.strip() if cpv_lot else None,
        notice_type=notice_type or None,
        procedure_type=procedure_type or None,
        contract_type=contract_type or None,
        legal_basis=legal_basis or None,
        pub_date_from=pub_from.replace("-", "") if pub_from else None,
        pub_date_to=pub_to.replace("-", "") if pub_to else None,
        deadline_to=deadline_to.replace("-", "") if deadline_to else None,
        buyer_name=buyer.strip() if buyer else None,
        buyer_country=buyer_country.strip() if buyer_country else None,
        authority_activity=authority_activity or None,
        lot_no=lot_no.strip() if isinstance(lot_no, str) else str(lot_no) if lot_no else None,
        pub_number=pub_number.strip() if pub_number else None,
        gazette_id=gazette_id.strip() if gazette_id else None,
        value_min=value_min if value_min else None,
        value_max=value_max if value_max else None,
        full_text=full_text.strip() if full_text else None,
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

# ------------------- UI helper functions ---------------------------------------

def create_info_symbol(description: str, example: str = None, options: list = None) -> str:
    """Create an info symbol with tooltip containing description and examples."""
    tooltip_content = f"{description}"
    
    if example:
        tooltip_content += f"<br><br><b>Beispiel:</b> {example}"
    
    if options and isinstance(options, list):
        options_str = "<br>".join([f"• {opt}" for opt in options])
        tooltip_content += f"<br><br><b>Optionen:</b><br>{options_str}"
    
    # Use HTML for the info symbol with tooltip
    return f"ℹ️" # Simple info emoji that Gradio will render

def create_field_with_info(field_name, field_info, component_type="textbox", **kwargs):
    """Create a field with an info symbol"""
    label = field_name
    if "label" in field_info:
        label = field_info["label"]
    
    info_symbol = create_info_symbol(field_info)
    
    if component_type == "dropdown":
        options = field_info.get("options", [])
        # If option_labels are provided, use them for display
        if "option_labels" in field_info:
            choices = [(opt, field_info["option_labels"].get(opt, opt)) for opt in options]
        else:
            choices = options
        return gr.Dropdown(choices=choices, label=f"{label} {info_symbol}", **kwargs)
    else:  # Default to textbox
        placeholder = field_info.get("example", "")
        return gr.Textbox(label=f"{label} {info_symbol}", placeholder=placeholder, **kwargs)

# ------------------- build UI --------------------------------------------------

# Use Gradio built-in monochrome theme which adapts to dark mode automatically
with gr.Blocks(title="TED Expert-Search UI", theme="gradio/monochrome") as demo:
    gr.Markdown("""# TED Expert-Search (Deutschland)
Fill the fields below to craft an expert query. Empty fields are ignored.
""")
    
    # Full text search
    with gr.Row():
        ft_info = SEARCH_FIELD_ALIASES["FT"]
        full_text = gr.Textbox(
            label=f"Volltextsuche (FT) {create_info_symbol(ft_info['description'], ft_info['example'])}", 
            placeholder="z.B. school building"
        )
    
    # Geographic information
    with gr.Row():
        rc_info = SEARCH_FIELD_ALIASES["RC"]
        region = gr.Dropdown(
            [f"{code} – {label}" for code, label in GERMAN_NUTS_CODES],
            label=f"Region (RC) {create_info_symbol(rc_info['description'], rc_info['example'])}", 
            value="DE6 – Hamburg", 
            interactive=True
        )
        
        pc_info = SEARCH_FIELD_ALIASES["PC"]
        cpv = gr.Textbox(
            label=f"CPV-Code (PC) {create_info_symbol(pc_info['description'], pc_info['example'])}", 
            placeholder="z. B. 79412000", 
            interactive=True
        )
        
        cpv_lot_info = SEARCH_FIELD_ALIASES["classification-cpv-lot"]
        cpv_lot = gr.Textbox(
            label=f"CPV-Zusatzcode {create_info_symbol(cpv_lot_info['description'], cpv_lot_info['example'])}", 
            placeholder="z. B. 71320000", 
            interactive=True
        )

    # Procedure and notice types
    with gr.Row():
        pr_info = SEARCH_FIELD_ALIASES["PR"]
        procedure_type = gr.Dropdown(
            [''] + [t for t in PROCEDURE_TYPES if t], 
            label=f"Verfahrensart (PR) {create_info_symbol(pr_info['description'], pr_info['example'], pr_info['options'])}", 
            value=''
        )
        
        nt_info = SEARCH_FIELD_ALIASES["notice-type"]
        notice_type = gr.Dropdown(
            [''] + NOTICE_TYPES, 
            label=f"Formtyp {create_info_symbol(nt_info['description'], nt_info['example'], nt_info['options'])}", 
            value=''
        )
        
        nc_info = SEARCH_FIELD_ALIASES["NC"]
        contract_type = gr.Dropdown(
            [''] + [t for t in CONTRACT_TYPES if t], 
            label=f"Vertragsart (NC) {create_info_symbol(nc_info['description'], nc_info['example'], nc_info['options'])}", 
            value=''
        )
        
        lb_info = SEARCH_FIELD_ALIASES["legal-basis-notice"]
        legal_basis = gr.Dropdown(
            [''] + lb_info['options'], 
            label=f"Rechtsgrundlage {create_info_symbol(lb_info['description'], lb_info['example'])}", 
            value=''
        )

    # Date filters
    with gr.Row():
        pd_info = SEARCH_FIELD_ALIASES["PD"]
        pub_from = gr.Textbox(
            label=f"Veröffentlichung ab {create_info_symbol(pd_info['description'], '>=20250101')}", 
            placeholder="YYYYMMDD"
        )
        pub_to = gr.Textbox(
            label=f"Veröffentlichung bis {create_info_symbol(pd_info['description'], '<=20251231')}", 
            placeholder="YYYYMMDD"
        )
        
        dd_info = SEARCH_FIELD_ALIASES["DD"]
        deadline = gr.Textbox(
            label=f"Einreichfrist bis (DD) {create_info_symbol(dd_info['description'], dd_info['example'])}", 
            placeholder="YYYYMMDD"
        )

    # Buyer and lot information
    with gr.Row():
        au_info = SEARCH_FIELD_ALIASES["AU"]
        buyer = gr.Textbox(
            label=f"Auftraggeber-Name (AU) {create_info_symbol(au_info['description'], au_info['example'])}", 
            interactive=True
        )
        
        cy_info = SEARCH_FIELD_ALIASES["CY"]
        buyer_country = gr.Textbox(
            label=f"Land des Auftraggebers (CY) {create_info_symbol(cy_info['description'], cy_info['example'])}", 
            placeholder="DE", 
            interactive=True
        )
        
        ama_info = SEARCH_FIELD_ALIASES["authority-main-activity"]
        authority_activity = create_field_with_info(
            "Auftraggeber Tätigkeit",
            ama_info,
            component_type="dropdown"
        )

    # Lot number and publication number
    with gr.Row():
        lot_info = SEARCH_FIELD_ALIASES["LOT_NUMBER"]
        lot_no = gr.Textbox(
            label=f"Losnummer {create_info_symbol(lot_info['description'], lot_info['example'])}", 
            placeholder="1"
        )
        
        nd_info = SEARCH_FIELD_ALIASES["ND"]
        pub_number = gr.Textbox(
            label=f"Ausschreibungsnummer (ND) {create_info_symbol(nd_info['description'], nd_info['example'])}", 
            placeholder="12345678-2025"
        )
        
        gid_info = SEARCH_FIELD_ALIASES["gazette-issue-id"]
        gazette_id = gr.Textbox(
            label=f"OJ S Ausgabe {create_info_symbol(gid_info['description'], gid_info['example'])}", 
            placeholder="180-2025"
        )

    # Value range (currently not used as we don't have the correct alias)
    with gr.Row():
        value_range = gr.Slider(
            0, 1000000, value=0, step=1000, 
            label="Geschätzter Wert € (Min/Max)", 
            interactive=True
        )

    # Download options
    with gr.Row():
        download_types = gr.CheckboxGroup(
            ["XML", "PDF"], 
            label="Dateitypen herunterladen", 
            value=["XML"], 
            interactive=True
        )
        
        max_results = gr.Number(
            value=25, 
            precision=0, 
            label="Max. Treffer", 
            interactive=True
        )

    out = gr.Textbox(label="Status", interactive=False)
    run_btn = gr.Button("Search & Download")

    run_btn.click(
        fn=run_search,
        inputs=[
            full_text, region, cpv, cpv_lot, notice_type, procedure_type, contract_type,
            legal_basis, pub_from, pub_to, deadline, buyer, buyer_country, authority_activity,
            lot_no, pub_number, gazette_id, value_range, download_types, max_results
        ],
        outputs=out,
    )

if __name__ == "__main__":
    demo.launch()
