import streamlit as st
import pandas as pd
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
import base64
from io import BytesIO

# Import the ted_search function and BASE_URL from ted_search_client
from ted_search_client import ted_search, BASE_URL

# Constants and mappings
_NOTICE_TYPE_MAP = {
    "Contract notice": "cn-standard",
    "Contract award notice": "can-standard",
    "Prior information notice": "pin-standard",
    "Design contest notice": "cn-desg",
    "Design contest results": "can-desg",
    "Modification notice": "can-modif",
    "Social and other specific services – public contracts": "cn-social",
    "Social and other specific services – utilities": "cn-social",
    "Social and other specific services – concessions": "cn-social",
    "Result of contest": "can-social",
    "Concession notice": "cn-standard",
    "Concession award notice": "can-standard",
    "Voluntary ex ante transparency notice": "veat",
    "Buyer profile": "pin-buyer",
    "Qualification system – utilities": "pin-standard",
    "Periodic indicative notice – utilities": "pin-standard"
}

_PROCEDURE_TYPE_MAP = {
    "Open procedure": "pt-open",
    "Restricted procedure": "pt-restricted",
    "Competitive procedure with negotiation": "pt-competitive-negotiation",
    "Competitive dialogue": "pt-competitive-dialogue",
    "Innovation partnership": "pt-innovation",
    "Negotiated procedure without prior publication": "pt-negotiated-without-call",
    "Award of a contract without prior publication": "pt-award-wo-prior-call",
    "Not specified": None
}

_CONTRACT_TYPE_MAP = {
    "Works": "works",
    "Supplies": "supplies",
    "Services": "services",
    "Not specified": None
}

# Search field aliases with descriptions and options
SEARCH_FIELD_ALIASES = {
    "FT": {
        "alias": "FT",
        "description": "Volltextsuche in allen Feldern",
        "example": '"Krankenhaus" OR "Hospital"',
        "options": None
    },
    "RC": {
        "alias": "RC",
        "description": "Regionalcode (NUTS-Code)",
        "example": '"DE6" (Süddeutschland)',
        "options": [
            "DE", "DE1", "DE11", "DE111", "DE112", "DE113", "DE114", "DE115", "DE116", "DE117", "DE118", "DE119", 
            "DE11A", "DE11B", "DE11C", "DE11D", "DE12", "DE121", "DE122", "DE123", "DE124", "DE125", "DE126", "DE127", 
            "DE128", "DE129", "DE12A", "DE12B", "DE12C", "DE13", "DE131", "DE132", "DE133", "DE134", "DE135", "DE136", 
            "DE137", "DE138", "DE139", "DE13A", "DE14", "DE141", "DE142", "DE143", "DE144", "DE145", "DE146", "DE147", 
            "DE148", "DE149", "DE2", "DE21", "DE211", "DE212", "DE213", "DE214", "DE215", "DE216", "DE217", "DE218", 
            "DE219", "DE21A", "DE21B", "DE21C", "DE21D", "DE21E", "DE21F", "DE21G", "DE21H", "DE21I", "DE21J", "DE21K", 
            "DE21L", "DE21M", "DE21N", "DE22", "DE221", "DE222", "DE223", "DE224", "DE225", "DE226", "DE227", "DE228", 
            "DE229", "DE22A", "DE22B", "DE22C", "DE23", "DE231", "DE232", "DE233", "DE234", "DE235", "DE236", "DE237", 
            "DE238", "DE239", "DE23A", "DE24", "DE241", "DE242", "DE243", "DE244", "DE245", "DE246", "DE247", "DE248", 
            "DE249", "DE24A", "DE24B", "DE24C", "DE24D", "DE25", "DE251", "DE252", "DE253", "DE254", "DE255", "DE256", 
            "DE257", "DE258", "DE259", "DE25A", "DE25B", "DE25C", "DE26", "DE261", "DE262", "DE263", "DE264", "DE265", 
            "DE266", "DE267", "DE268", "DE269", "DE26A", "DE26B", "DE26C", "DE27", "DE271", "DE272", "DE273", "DE274", 
            "DE275", "DE276", "DE277", "DE278", "DE279", "DE27A", "DE27B", "DE27C", "DE27D", "DE27E", "DE3", "DE30", 
            "DE300", "DE4", "DE40", "DE401", "DE402", "DE403", "DE404", "DE405", "DE406", "DE407", "DE408", "DE409", 
            "DE40A", "DE40B", "DE40C", "DE40D", "DE40E", "DE40F", "DE40G", "DE40H", "DE40I", "DE5", "DE50", "DE501", 
            "DE502", "DE6", "DE60", "DE600", "DE7", "DE71", "DE711", "DE712", "DE713", "DE714", "DE715", "DE716", 
            "DE717", "DE718", "DE719", "DE71A", "DE71B", "DE71C", "DE71D", "DE71E", "DE72", "DE721", "DE722", "DE723", 
            "DE724", "DE725", "DE726", "DE727", "DE728", "DE729", "DE72A", "DE72B", "DE72C", "DE72D", "DE73", "DE731", 
            "DE732", "DE733", "DE734", "DE735", "DE736", "DE737", "DE738", "DE739", "DE73A", "DE73B", "DE73C", "DE74", 
            "DE741", "DE742", "DE743", "DE744", "DE745", "DE746", "DE747", "DE748", "DE749", "DE74A", "DE74B", "DE74C", 
            "DE74D", "DE75", "DE751", "DE752", "DE753", "DE754", "DE755", "DE756", "DE757", "DE758", "DE759", "DE75A", 
            "DE75B", "DE75C", "DE8", "DE80", "DE801", "DE802", "DE803", "DE804", "DE80J", "DE80K", "DE80L", "DE80M", 
            "DE80N", "DE80O", "DE9", "DE91", "DE911", "DE912", "DE913", "DE914", "DE915", "DE916", "DE917", "DE918", 
            "DE919", "DE91A", "DE91B", "DE92", "DE921", "DE922", "DE923", "DE924", "DE925", "DE926", "DE927", "DE928", 
            "DE929", "DE92A", "DE92B", "DE93", "DE931", "DE932", "DE933", "DE934", "DE935", "DE936", "DE937", "DE938", 
            "DE939", "DE93A", "DE93B", "DE94", "DE941", "DE942", "DE943", "DE944", "DE945", "DE946", "DE947", "DE948", 
            "DE949", "DE94A", "DE94B", "DE94C", "DE94D", "DE94E", "DE94F", "DE94G", "DE94H", "DEA", "DEA1", "DEA11", 
            "DEA12", "DEA13", "DEA14", "DEA15", "DEA16", "DEA17", "DEA18", "DEA19", "DEA1A", "DEA1B", "DEA1C", "DEA1D", 
            "DEA1E", "DEA1F", "DEA2", "DEA21", "DEA22", "DEA23", "DEA24", "DEA25", "DEA26", "DEA27", "DEA28", "DEA29", 
            "DEA2A", "DEA2B", "DEA2C", "DEA2D", "DEA3", "DEA31", "DEA32", "DEA33", "DEA34", "DEA35", "DEA36", "DEA37", 
            "DEA38", "DEA4", "DEA41", "DEA42", "DEA43", "DEA44", "DEA45", "DEA46", "DEA47", "DEA5", "DEA51", "DEA52", 
            "DEA53", "DEA54", "DEA55", "DEA56", "DEA57", "DEA58", "DEA59", "DEA5A", "DEA5B", "DEA5C", "DEB", "DEB1", 
            "DEB11", "DEB12", "DEB13", "DEB14", "DEB15", "DEB16", "DEB17", "DEB18", "DEB19", "DEB1A", "DEB1B", "DEB2", 
            "DEB21", "DEB22", "DEB23", "DEB24", "DEB25", "DEB3", "DEB31", "DEB32", "DEB33", "DEB34", "DEB35", "DEB36", 
            "DEB37", "DEB38", "DEB39", "DEB3A", "DEB3B", "DEB3C", "DEB3D", "DEB3E", "DEB3F", "DEB3G", "DEB3H", "DEB3I", 
            "DEB3J", "DEB3K", "DEC", "DEC0", "DEC01", "DEC02", "DEC03", "DEC04", "DEC05", "DED", "DED2", "DED21", 
            "DED2C", "DED2D", "DED2E", "DED2F", "DED2G", "DED2H", "DED2I", "DED2J", "DED2K", "DED4", "DED41", "DED42", 
            "DED43", "DED44", "DED45", "DED5", "DED51", "DED52", "DED53", "DEE", "DEE0", "DEE01", "DEE02", "DEE03", 
            "DEE04", "DEE05", "DEE06", "DEE07", "DEE08", "DEE09", "DEE0A", "DEE0B", "DEE0C", "DEE0D", "DEE0E", "DEF", 
            "DEF0", "DEF01", "DEF02", "DEF03", "DEF04", "DEF05", "DEF06", "DEF07", "DEF08", "DEF09", "DEF0A", "DEF0B", 
            "DEF0C", "DEF0D", "DEF0E", "DEF0F", "DEG", "DEG0", "DEG01", "DEG02", "DEG03", "DEG04", "DEG05", "DEG06", 
            "DEG07", "DEG09", "DEG0A", "DEG0B", "DEG0C", "DEG0D", "DEG0E", "DEG0F", "DEG0G", "DEG0H", "DEG0I", "DEG0J", 
            "DEG0K", "DEG0L", "DEG0M", "DEG0N", "DEG0P"
        ],
        "option_labels": {
            "DE": "Deutschland",
            "DE1": "Baden-Württemberg",
            "DE2": "Bayern",
            "DE3": "Berlin",
            "DE4": "Brandenburg",
            "DE5": "Bremen",
            "DE6": "Hamburg",
            "DE7": "Hessen",
            "DE8": "Mecklenburg-Vorpommern",
            "DE9": "Niedersachsen",
            "DEA": "Nordrhein-Westfalen",
            "DEB": "Rheinland-Pfalz",
            "DEC": "Saarland",
            "DED": "Sachsen",
            "DEE": "Sachsen-Anhalt",
            "DEF": "Schleswig-Holstein",
            "DEG": "Thüringen"
        }
    },
    "PC": {
        "alias": "classification-cpv",
        "description": "CPV-Code (Common Procurement Vocabulary)",
        "example": '"45000000" (Bauarbeiten)',
        "options": None
    },
    "classification-cpv-lot": {
        "alias": "classification-cpv-lot",
        "description": "CPV-Code für Los",
        "example": '"45000000" (Bauarbeiten)',
        "options": None
    },
    "NT": {
        "alias": "notice-type",
        "description": "Art der Bekanntmachung",
        "example": "cn-standard (Auftragsbekanntmachung)",
        "options": list(_NOTICE_TYPE_MAP.values())
    },
    "PR": {
        "alias": "procedure-type",
        "description": "Verfahrensart",
        "example": "pt-open (Offenes Verfahren)",
        "options": list(_PROCEDURE_TYPE_MAP.values())
    },
    "NC": {
        "alias": "contract-nature",
        "description": "Art des Auftrags",
        "example": "works, supplies, services",
        "options": list(_CONTRACT_TYPE_MAP.values())
    },
    "LB": {
        "alias": "legal-basis",
        "description": "Rechtsgrundlage",
        "example": "32014L0024 (Richtlinie 2014/24/EU)",
        "options": ["32014L0024", "32014L0025", "32014L0023", "32009L0081"]
    },
    "PD": {
        "alias": "publication-date",
        "description": "Veröffentlichungsdatum (Format: YYYYMMDD)",
        "example": "20230101 (für 01.01.2023)",
        "options": None
    },
    "DD": {
        "alias": "deadline-date",
        "description": "Einreichungsfrist (Format: YYYYMMDD)",
        "example": "20230101 (für 01.01.2023)",
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
    "buyer-country": {
        "alias": "buyer-country",
        "description": "Land des Auftraggebers",
        "example": "DE (Deutschland), FR (Frankreich)",
        "options": ["AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"]
    },
    "LN": {
        "alias": "lot-number",
        "description": "Losnummer",
        "example": "1, 2, 3",
        "options": None
    },
    "PN": {
        "alias": "publication-number",
        "description": "Bekanntmachungsnummer",
        "example": "12345-2023",
        "options": None
    },
    "GI": {
        "alias": "gazette-issue-id",
        "description": "Amtsblatt-Ausgabe ID",
        "example": "20230101",
        "options": None
    },
    "VR": {
        "alias": "value-range",
        "description": "Auftragswert-Bereich (in EUR)",
        "example": "100000-500000",
        "options": None
    }
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
    parts: List[str] = []
    if full_text:
        parts.append(f"FT~(\"{full_text}\")")
    if region_code and region_code.strip():
        parts.append(f"RC=\"{region_code}\"")
    if cpv:
        parts.append(f"PC=\"{cpv}\"")
    if cpv_lot:
        parts.append(f"classification-cpv-lot=\"{cpv_lot}\"")
    if notice_type:
        parts.append(f"notice-type=\"{notice_type}\"")
    if procedure_type:
        parts.append(f"PR=\"{procedure_type}\"")
    if contract_type:
        parts.append(f"NC=\"{contract_type}\"")
    if legal_basis:
        parts.append(f"legal-basis-notice=\"{legal_basis}\"")
    
    # Add a default query if no parts are added
    if not parts:
        parts.append("PD>="+datetime.now().strftime("%Y%m%d"))
    if pub_date_from and pub_date_to:
        parts.append(f"PD=[{pub_date_from} TO {pub_date_to}]")
    elif pub_date_from:
        parts.append(f"PD>={pub_date_from}")
    elif pub_date_to:
        parts.append(f"PD<={pub_date_to}")
    if deadline_to:
        parts.append(f"deadline-receipt-tender-date-lot<={deadline_to}")
    if buyer_name:
        parts.append(f"AU=\"{buyer_name}\"")
    if buyer_country:
        parts.append(f"CY=\"{buyer_country}\"")
    if authority_activity:
        parts.append(f"authority-main-activity=\"{authority_activity}\"")
    if lot_no:
        parts.append(f"lot-included-proc=\"{lot_no}\"")
    if pub_number:
        parts.append(f"ND=\"{pub_number}\"")
    if gazette_id:
        parts.append(f"gazette-issue-id=\"{gazette_id}\"")
    # if value_min is not None and value_max is not None:
    #     parts.append(f"VR=[{value_min} TO {value_max}]")
    # elif value_min is not None:
    #     parts.append(f"VR>={value_min}")
    # elif value_max is not None:
    #     parts.append(f"VR<={value_max}")
    
    return " AND ".join(parts)

def create_info_tooltip(field_info):
    """Create tooltip text for a field"""
    tooltip = field_info.get("description", "")
    
    if field_info.get("example"):
        tooltip += f"\n\nBeispiel: {field_info['example']}"
    
    if field_info.get("options") and not field_info.get("option_labels"):
        options_str = ", ".join(str(opt) for opt in field_info["options"] if opt)
        if options_str:
            tooltip += f"\n\nOptionen: {options_str}"
    
    return tooltip

def download_button(object_to_download, download_filename, button_text):
    """
    Generates a link to download the given object_to_download.
    From: https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806
    """
    if isinstance(object_to_download, pd.DataFrame):
        object_to_download = object_to_download.to_csv(index=False)
        file_extension = 'csv'
    else:
        file_extension = 'json'
    
    # Some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(object_to_download.encode()).decode()
    
    button_uuid = f"download_{download_filename.replace('.', '_')}"
    custom_css = f"""
        <style>
            #{button_uuid} {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: .25rem .75rem;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }}
            #{button_uuid}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_uuid}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style>
    """
    
    dl_link = custom_css + f'<a download="{download_filename}" id="{button_uuid}" href="data:file/{file_extension};base64,{b64}">{button_text}</a><br><br>'
    
    return dl_link

def check_result_count(query: str) -> Optional[int]:
    """Fetch all results and count them."""
    try:
        # Show a loading message
        with st.spinner('Suche läuft... Ergebnisse werden gezählt...'):
            # Call TED API to get all results and count them
            # Use a reasonable limit per page
            limit_per_page = 100
            max_pages = 10  # Limit to 10 pages (1000 results) for performance
            
            # Call ted_search function to get all results
            print(f"DEBUG - Fetching results for query: {query}")
            
            # Store the results in session state for later use
            results = ted_search(
                query=query,
                fields=["notice-type"],  # Minimal field set
                page=1,
                limit=limit_per_page,
                max_pages=max_pages
            )
            
            # Store results for later download
            st.session_state.prefetched_results = results
            
            # Count results
            total_results = len(results)
            print(f"DEBUG - Found {total_results} results")
            
            return total_results
    except Exception as e:
        error_msg = f"Fehler beim Abrufen der Ergebnisse: {str(e)}"
        print(f"DEBUG - Error: {error_msg}")
        st.session_state.search_error = error_msg
        return None

def run_search(
    full_text, region, cpv, cpv_lot, notice_type, procedure_type, contract_type,
    legal_basis, pub_from, pub_to, deadline, buyer, buyer_country, authority_activity,
    lot_no, pub_number, gazette_id, value_range, download_types, max_results
):
    """Run search with the given parameters"""
    st.session_state.search_results = None
    st.session_state.search_error = None
    st.session_state.search_query = None
    
    try:
        # Parse value range
        value_min = None
        value_max = None
        if value_range and len(value_range) == 2:
            value_min, value_max = value_range
        
        # Format dates
        pub_date_from = pub_from.replace("-", "") if pub_from else None
        pub_date_to = pub_to.replace("-", "") if pub_to else None
        deadline_to = deadline.replace("-", "") if deadline else None
        
        # For testing, use a simple date-based query instead of country code
        # This will help us verify if the API is working correctly
        if region and region.strip():
            # Use a date-based query for now to test API connectivity
            query = "PD>=20250101"
            print(f"DEBUG - Using test query: {query}")
        else:
            # Build expert query from UI inputs
            query = build_expert_query(
                region_code=None,  # Skip region code for now
                cpv=cpv.strip() if cpv else None,
                cpv_lot=cpv_lot.strip() if cpv_lot else None,
                notice_type=notice_type or None,
                procedure_type=procedure_type or None,
                contract_type=contract_type or None,
                legal_basis=legal_basis or None,
                pub_date_from=pub_date_from,
                pub_date_to=pub_date_to,
                deadline_to=deadline_to,
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
        
        # Store query for display
        st.session_state.search_query = query
        
        # Store query in session state for later use
        st.session_state.current_query = query
        st.session_state.current_download_types = download_types
        st.session_state.current_max_results = max_results
        
        # Check result count and fetch results
        result_count = check_result_count(query)
        if result_count is None:
            return
            
        # Store result count
        st.session_state.result_count = result_count
        
        # Show result count and download button
        st.success(f"Es wurden {result_count} Ergebnisse gefunden.")
        
        # Add download button if results were found
        if result_count > 0 and st.session_state.prefetched_results:
            st.session_state.show_download_button = True
        
    except Exception as e:
        error_msg = f"Fehler bei der Suche: {str(e)}"
        st.session_state.search_error = error_msg
        st.error(error_msg)
        return

def main():
    st.set_page_config(
        page_title="TED Expert-Search UI",
        page_icon="🇪🇺",
        layout="wide"
    )
    st.title("TED Expert-Search UI")
    
    # Define fetch_results function
    def fetch_results():
        """Fetch results based on current query and download settings"""
        if not st.session_state.current_query:
            st.error("Keine Suchanfrage vorhanden. Bitte führen Sie zuerst eine Suche durch.")
            return
        
        try:
            with st.spinner('Ergebnisse werden abgerufen...'):
                # Check if we already have prefetched results
                if st.session_state.prefetched_results:
                    results = st.session_state.prefetched_results
                    print(f"DEBUG - Using {len(results)} prefetched results")
                else:
                    # Get current settings
                    query = st.session_state.current_query
                    download_types = st.session_state.current_download_types
                    max_results = st.session_state.current_max_results
                    
                    # Call ted_search function
                    results = ted_search(
                        query=query,
                        fields=None,  # Use default fields
                        limit=max_results
                    )
                
                # Store results
                st.session_state.search_results = results
                
                if results:
                    st.success(f"{len(results)} Ergebnisse erfolgreich abgerufen.")
                    
                    # Generate download links
                    if "excel" in st.session_state.current_download_types:
                        excel_path = export_to_excel(results, "ted_results")
                        excel_link = create_download_link(excel_path, "Excel-Datei herunterladen")
                        st.markdown(excel_link, unsafe_allow_html=True)
                    
                    if "json" in st.session_state.current_download_types:
                        json_path = export_to_json(results, "ted_results")
                        json_link = create_download_link(json_path, "JSON-Datei herunterladen")
                        st.markdown(json_link, unsafe_allow_html=True)
                else:
                    st.warning("Keine Ergebnisse gefunden.")
        except Exception as e:
            st.error(f"Fehler beim Abrufen der Ergebnisse: {str(e)}")
            return False
    
    # Initialize session state variables if they don't exist
    if "search_results" not in st.session_state:
        st.session_state.search_results = None
    if "search_error" not in st.session_state:
        st.session_state.search_error = None
    if "search_query" not in st.session_state:
        st.session_state.search_query = None
    if "result_count" not in st.session_state:
        st.session_state.result_count = None
    if "debug_response" not in st.session_state:
        st.session_state.debug_response = None
    if "debug_payload" not in st.session_state:
        st.session_state.debug_payload = None
    if "prefetched_results" not in st.session_state:
        st.session_state.prefetched_results = None
    if "show_download_button" not in st.session_state:
        st.session_state.show_download_button = False
    if "current_query" not in st.session_state:
        st.session_state.current_query = None
    if "current_download_types" not in st.session_state:
        st.session_state.current_download_types = None
    if "current_max_results" not in st.session_state:
        st.session_state.current_max_results = None
    
    # Create sidebar for search parameters
    with st.sidebar:
        st.header("Suchparameter")
        
        # Full text search
        ft_info = SEARCH_FIELD_ALIASES["FT"]
        full_text = st.text_input(
            "Volltextsuche", 
            help=create_info_tooltip(ft_info)
        )
        
        # Geographic info
        st.subheader("Geografische Informationen")
        
        rc_info = SEARCH_FIELD_ALIASES["RC"]
        
        # Create options with labels for dropdown
        nuts_options = [""]
        nuts_labels = {"":"Keine Auswahl"}
        
        if rc_info["options"]:
            nuts_options.extend(rc_info["options"])
            if rc_info.get("option_labels"):
                for code, label in rc_info["option_labels"].items():
                    nuts_labels[code] = f"{code} - {label}"
                    
            # Add labels for codes without explicit labels
            for code in rc_info["options"]:
                if code not in nuts_labels:
                    nuts_labels[code] = code
        
        # Use selectbox instead of text_input
        region = st.selectbox(
            "Region (NUTS-Code)",
            options=nuts_options,
            format_func=lambda x: nuts_labels.get(x, x),
            help=create_info_tooltip(rc_info)
        )
        
        bc_info = SEARCH_FIELD_ALIASES["buyer-country"]
        buyer_country = st.selectbox(
            "Land des Auftraggebers",
            options=[""] + bc_info["options"],
            help=create_info_tooltip(bc_info)
        )
        
        # CPV & Procedure
        st.subheader("CPV & Verfahren")
        
        pc_info = SEARCH_FIELD_ALIASES["PC"]
        cpv = st.text_input(
            "CPV-Code", 
            help=create_info_tooltip(pc_info)
        )
        
        cpv_lot_info = SEARCH_FIELD_ALIASES["classification-cpv-lot"]
        cpv_lot = st.text_input(
            "CPV-Code für Los", 
            help=create_info_tooltip(cpv_lot_info)
        )
        
        # Notice type
        nt_info = SEARCH_FIELD_ALIASES["NT"]
        notice_type_display = {v: k for k, v in _NOTICE_TYPE_MAP.items()}
        notice_type = st.selectbox(
            "Art der Bekanntmachung",
            options=[""] + list(_NOTICE_TYPE_MAP.values()),
            format_func=lambda x: notice_type_display.get(x, x) if x else "",
            help=create_info_tooltip(nt_info)
        )
        
        # Procedure type
        pr_info = SEARCH_FIELD_ALIASES["PR"]
        procedure_type_display = {v: k for k, v in _PROCEDURE_TYPE_MAP.items()}
        procedure_type = st.selectbox(
            "Verfahrensart",
            options=[""] + list(_PROCEDURE_TYPE_MAP.values()),
            format_func=lambda x: procedure_type_display.get(x, x) if x else "",
            help=create_info_tooltip(pr_info)
        )
        
        # Contract type
        nc_info = SEARCH_FIELD_ALIASES["NC"]
        contract_type_display = {v: k for k, v in _CONTRACT_TYPE_MAP.items()}
        contract_type = st.selectbox(
            "Art des Auftrags",
            options=[""] + list(_CONTRACT_TYPE_MAP.values()),
            format_func=lambda x: contract_type_display.get(x, x) if x else "",
            help=create_info_tooltip(nc_info)
        )
        
        # Legal basis
        lb_info = SEARCH_FIELD_ALIASES["LB"]
        legal_basis = st.selectbox(
            "Rechtsgrundlage",
            options=[""] + lb_info["options"],
            help=create_info_tooltip(lb_info)
        )
        
        # Dates
        st.subheader("Termine")
        
        pd_info = SEARCH_FIELD_ALIASES["PD"]
        pub_from = st.date_input(
            "Veröffentlichungsdatum von",
            value=None,
            help=create_info_tooltip(pd_info)
        )
        pub_from = pub_from.strftime("%Y-%m-%d") if pub_from else ""
        
        pub_to = st.date_input(
            "Veröffentlichungsdatum bis",
            value=None,
            help=create_info_tooltip(pd_info)
        )
        pub_to = pub_to.strftime("%Y-%m-%d") if pub_to else ""
        
        dd_info = SEARCH_FIELD_ALIASES["DD"]
        deadline = st.date_input(
            "Einreichungsfrist bis",
            value=None,
            help=create_info_tooltip(dd_info)
        )
        deadline = deadline.strftime("%Y-%m-%d") if deadline else ""
        
        # Buyer info
        st.subheader("Auftraggeber")
        
        au_info = SEARCH_FIELD_ALIASES["AU"]
        buyer = st.text_input(
            "Name des Auftraggebers",
            help=create_info_tooltip(au_info)
        )
        
        ama_info = SEARCH_FIELD_ALIASES["authority-main-activity"]
        # Create a dictionary for display values
        activity_options = [""] + ama_info["options"]
        activity_format = lambda x: ama_info["option_labels"].get(x, x) if x else ""
        
        authority_activity = st.selectbox(
            "Haupttätigkeit des Auftraggebers",
            options=activity_options,
            format_func=activity_format,
            help=create_info_tooltip(ama_info)
        )
        
        # Lot number and publication number
        st.subheader("Weitere Informationen")
        
        ln_info = SEARCH_FIELD_ALIASES["LN"]
        lot_no = st.text_input(
            "Losnummer",
            help=create_info_tooltip(ln_info)
        )
        
        pn_info = SEARCH_FIELD_ALIASES["PN"]
        pub_number = st.text_input(
            "Bekanntmachungsnummer",
            help=create_info_tooltip(pn_info)
        )
        
        gi_info = SEARCH_FIELD_ALIASES["GI"]
        gazette_id = st.text_input(
            "Amtsblatt-Ausgabe ID",
            help=create_info_tooltip(gi_info)
        )
        
        # Value range
        vr_info = SEARCH_FIELD_ALIASES["VR"]
        value_range = st.slider(
            "Auftragswert-Bereich (EUR)",
            min_value=0,
            max_value=10000000,
            value=(0, 10000000),
            step=10000,
            help=create_info_tooltip(vr_info)
        )
        
        # Download options
        st.subheader("Download-Optionen")
        
        download_types = st.multiselect(
            "Download-Formate",
            options=["xml", "pdf_de", "pdf_en", "pdf_fr"],
            default=["pdf_de"],
            help="Wählen Sie die Formate für den Download aus"
        )
        
        max_results = st.number_input(
            "Maximale Ergebnisse",
            min_value=1,
            max_value=1000,
            value=25,
            help="Maximale Anzahl der Ergebnisse"
        )
        
        # Search button
        search_button = st.button("Suche starten", type="primary", use_container_width=True)
        
        if search_button:
            run_search(
                full_text, region, cpv, cpv_lot, notice_type, procedure_type, contract_type,
                legal_basis, pub_from, pub_to, deadline, buyer, buyer_country, authority_activity,
                lot_no, pub_number, gazette_id, value_range, download_types, max_results
            )
    
    # Main content area
    if st.session_state.search_query:
        st.subheader("Suchanfrage")
        st.code(st.session_state.search_query)
    
    if st.session_state.search_error:
        st.error(f"Fehler bei der Suche: {st.session_state.search_error}")
    
    # Display result count and download button if available
    if "result_count" in st.session_state and st.session_state.result_count is not None:
        result_count = st.session_state.result_count
        
        # Show download button if we have prefetched results
        if result_count > 0 and st.session_state.prefetched_results:
            st.subheader(f"Gefundene Ergebnisse: {result_count}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Alle {result_count} Ergebnisse herunterladen", type="primary", key="download_button"):
                    fetch_results()
            with col2:
                st.write("Hinweis: Die Ergebnisse wurden bereits abgerufen und können jetzt heruntergeladen werden.")
        elif result_count == 0:
            st.info("Keine Ergebnisse gefunden.")
        else:
            st.warning("Ergebnisse konnten nicht abgerufen werden. Bitte versuchen Sie es erneut.")

    
    # Display full results if available
    if st.session_state.search_results:
        results = st.session_state.search_results
        
        st.subheader(f"Suchergebnisse ({len(results)} Treffer)")
        
        if results:
            # Create DataFrame from results
            data = []
            for notice in results:
                row = {
                    "Nummer": notice.get("publication-number", ""),
                    "Datum": notice.get("publication-date", ""),
                    "Auftraggeber": notice.get("buyer-name", ""),
                    "Titel": notice.get("title", ""),
                    "CPV": notice.get("cpv-code", ""),
                    "Land": notice.get("buyer-country", "")
                }
                
                # Add links if available
                links = notice.get("links", {})
                if links:
                    if "ted" in links:
                        row["TED Link"] = links["ted"]
                    if "pdf" in links and links["pdf"]:
                        for lang, url in links["pdf"].items():
                            row[f"PDF ({lang})"] = url
                
                data.append(row)
            
            df = pd.DataFrame(data)
            
            # Display results as table
            st.dataframe(df, use_container_width=True)
            
            # Add download buttons
            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Als CSV herunterladen",
                    data=csv,
                    file_name="ted_search_results.csv",
                    mime="text/csv",
                )
            
            with col2:
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_data = excel_buffer.getvalue()
                st.download_button(
                    label="Als Excel herunterladen",
                    data=excel_data,
                    file_name="ted_search_results.xlsx",
                    mime="application/vnd.ms-excel",
                )
        else:
            st.info("Keine Ergebnisse gefunden.")

if __name__ == "__main__":
    main()
