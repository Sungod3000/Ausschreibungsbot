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
from core.query_builder import build_expert_query
from core.count import get_total_count_from_api
from core.downloader import download_with_rate_limit
from core.naming import make_download_folder_name
from config.constants import (
    NOTICE_TYPE_MAP as _NOTICE_TYPE_MAP,
    PROCEDURE_TYPE_MAP as _PROCEDURE_TYPE_MAP,
    CONTRACT_TYPE_MAP as _CONTRACT_TYPE_MAP,
)
from config.nuts import load_nuts_de
import logging
from config.logging import setup_logging

# Initialize root logging once, then get module logger
setup_logging()
logger = logging.getLogger(__name__)

# Streamlit page config must be the first Streamlit command
st.set_page_config(
    page_title="TED Expert-Search UI",
    page_icon="🇪🇺",
    layout="wide",
)

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

# build_expert_query is now imported from core.query_builder

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

"""get_total_count_from_api is now imported from core.count"""

def create_download_folder_name(query: str, download_types: list) -> str:
    """Compatibility wrapper for tests; delegates to core.naming.make_download_folder_name."""
    return make_download_folder_name(query, download_types)

def fetch_results():
    """Download files from prefetched results with verbose debugging and rate limiting."""
    import os
    import requests
    import time
    from datetime import datetime
    
    logger.info("\n" + "="*60)
    logger.info("🔥 FETCH_RESULTS STARTED")
    logger.info("="*60)
    
    # STEP 1: Check if we have results (prefetched or fetch limited on-demand)
    logger.info("\n📋 STEP 1: Checking for prefetched results...")
    results = None
    if hasattr(st.session_state, 'prefetched_results') and st.session_state.prefetched_results:
        results = st.session_state.prefetched_results
        logger.info(f"✅ Found {len(results)} prefetched results")
    else:
        # Fallback: fetch first N results on-demand according to max_results
        query = st.session_state.get('current_query')
        desired_max = st.session_state.get('current_max_results', 100)
        if not query:
            logger.error("❌ ERROR: No query available for on-demand fetch")
            st.error("Keine Ergebnisse gefunden. Bitte führen Sie zuerst eine Suche durch.")
            return
        st.info(f"Prefetch war deaktiviert. Lade die ersten {desired_max} Ergebnisse…")
        logger.info(f"Prefetch disabled – fetching first {desired_max} results for download")
        from math import ceil
        pages_needed = max(1, ceil(int(desired_max) / 100))
        # Use progress callback to surface progress to UI
        page_progress = st.progress(0.0)
        page_info = st.empty()
        res_info = st.empty()
        def _progress_cb(current_page, total_pages, results_so_far, total_results):
            if pages_needed:
                page_progress.progress(min(current_page / pages_needed, 1.0))
            page_info.text(f"Seiten: {current_page}/{pages_needed}")
            res_info.text(f"Ergebnisse gesammelt: {results_so_far}")
        results = ted_search(
            query=query,
            fields=["publication-number", "links", "notice-type"],
            page=1,
            limit=100,
            max_pages=pages_needed,
            progress_cb=_progress_cb,
        )
        st.session_state.prefetched_results = results
        try:
            page_progress.progress(1.0)
        except Exception:
            pass
        logger.info(f"✅ Fetched {len(results)} results for download")
    
    # STEP 2: Get download types and search parameters
    logger.info("\n📋 STEP 2: Getting download parameters...")
    download_types = st.session_state.get('current_download_types', ['pdf_de'])
    query = st.session_state.get('current_query', 'unknown_query')
    
    logger.info(f"📥 Download types: {download_types}")
    logger.info(f"🔍 Search query: {query}")
    
    if not download_types:
        logger.error("❌ ERROR: No download types selected")
        st.error("Bitte wählen Sie mindestens ein Download-Format aus.")
        return
    
    # STEP 3: Create folder with search parameters in name
    logger.info("\n📋 STEP 3: Creating download folder...")
    folder_name = make_download_folder_name(query, download_types)
    download_folder = os.path.join(os.getcwd(), "downloads", folder_name)
    
    logger.info(f"📁 Creating folder: {folder_name}")
    logger.info(f"📁 Full path: {download_folder}")
    
    try:
        os.makedirs(download_folder, exist_ok=True)
        logger.info("✅ Folder created successfully")
    except Exception as e:
        logger.error(f"❌ ERROR creating folder: {e}")
        st.error(f"Konnte Download-Ordner nicht erstellen: {e}")
        return
    
    if not os.path.exists(download_folder):
        logger.error("❌ ERROR: Folder does not exist after creation")
        st.error(f"Download-Ordner wurde nicht erstellt: {download_folder}")
        return
    
    st.success(f"📁 Download-Ordner erstellt: {folder_name}")
    
    # Respect max results limit before analysis
    limit_for_download = st.session_state.get('current_max_results')
    if limit_for_download is not None and isinstance(limit_for_download, int) and limit_for_download > 0:
        if len(results) > limit_for_download:
            results = results[:limit_for_download]
            st.warning(f"Es wurden mehr Ergebnisse gefunden als erlaubt. Es werden nur die ersten {limit_for_download} Ergebnisse heruntergeladen.")
            logger.info(f"Truncating results to max_results={limit_for_download} for download")

    # STEP 4: Count and analyze available files
    logger.info("\n📋 STEP 4: Analyzing available files...")
    
    total_files = 0
    file_analysis = []
    
    for i, result in enumerate(results):
        pub_number = result.get("publication-number", f"notice_{i}")
        links = result.get("links", {})
        
        logger.info(f"\n📄 Result {i+1}/{len(results)}: {pub_number}")
        logger.debug(f"   Available link types: {list(links.keys()) if links else 'No links'}")
        
        result_files = []
        
        # Check PDF links
        if "pdf" in links and isinstance(links["pdf"], dict):
            logger.debug(f"   📕 PDF languages: {list(links['pdf'].keys())}")
            for lang, url in links["pdf"].items():
                should_download = False
                file_suffix = ""
                
                if "pdf_de" in download_types and lang.upper() in ['DEU', 'DE']:
                    should_download = True
                    file_suffix = "_DE.pdf"
                    logger.info(f"   ✅ Will download PDF (German): {lang}")
                elif "pdf_en" in download_types and lang.upper() in ['ENG', 'EN']:
                    should_download = True
                    file_suffix = "_EN.pdf"
                    logger.info(f"   ✅ Will download PDF (English): {lang}")
                else:
                    logger.debug(f"   ⏭️  Skipping PDF language: {lang}")
                
                if should_download:
                    filename = f"{pub_number}{file_suffix}"
                    result_files.append({
                        'filename': filename,
                        'url': url,
                        'type': 'PDF',
                        'lang': lang
                    })
                    total_files += 1
        
        # Check JSON links
        if "json" in links and isinstance(links["json"], dict):
            logger.debug(f"   📗 JSON languages: {list(links['json'].keys())}")
            for lang, url in links["json"].items():
                should_download = False
                file_suffix = ""
                
                if "json_de" in download_types and lang.upper() in ['DEU', 'DE']:
                    should_download = True
                    file_suffix = "_DE.json"
                    logger.info(f"   ✅ Will download JSON (German): {lang}")
                elif "json_en" in download_types and lang.upper() in ['ENG', 'EN']:
                    should_download = True
                    file_suffix = "_EN.json"
                    logger.info(f"   ✅ Will download JSON (English): {lang}")
                else:
                    logger.debug(f"   ⏭️  Skipping JSON language: {lang}")
                
                if should_download:
                    filename = f"{pub_number}{file_suffix}"
                    result_files.append({
                        'filename': filename,
                        'url': url,
                        'type': 'JSON',
                        'lang': lang
                    })
                    total_files += 1
        
        file_analysis.append({
            'pub_number': pub_number,
            'files': result_files
        })
    
    logger.info(f"\n📊 ANALYSIS COMPLETE:")
    logger.info(f"   📄 Total results: {len(results)}")
    logger.info(f"   📥 Total files to download: {total_files}")
    logger.info(f"   📁 Download folder: {folder_name}")
    
    if total_files == 0:
        logger.warning("❌ No files to download!")
        st.warning("Keine Dateien zum Herunterladen gefunden. Überprüfen Sie die ausgewählten Formate.")
        return
    
    # STEP 5: Download files with rate limiting
    logger.info("\n📋 STEP 5: Starting downloads with rate limiting (max ~3/sec)…")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    downloaded_count = 0
    failed_count = 0
    last_request_time = 0
    
    st.info(f"📥 Beginne Download von {total_files} Dateien… (Rate-Limit ~3/s)")
    
    for result_info in file_analysis:
        pub_number = result_info['pub_number']
        files = result_info['files']
        
        if not files:
            continue
            
        logger.info(f"\n📄 Downloading files for: {pub_number}")
        
        for file_info in files:
            filename = file_info['filename']
            url = file_info['url']
            file_type = file_info['type']
            lang = file_info['lang']
            
            filepath = os.path.join(download_folder, filename)
            
            logger.info(f"\n🔽 Downloading: {filename}")
            logger.debug(f"   📎 URL: {url[:80]}...")
            logger.debug(f"   📁 Path: {filepath}")

            success, file_size, error_msg, last_request_time = download_with_rate_limit(
                url,
                filepath,
                last_request_time,
                min_interval=0.5,  # ~2 req/s base; downloader will backoff further on 429
                timeout=60,
                max_retries=7,
            )
            if success:
                logger.info(f"   ✅ SUCCESS: {filename} ({file_size} bytes)")
                downloaded_count += 1
            else:
                logger.error(f"   ❌ ERROR: {filename} - {error_msg}")
                st.warning(f"Fehler beim Herunterladen von {filename}: {error_msg}")
                failed_count += 1
            
            # Update progress
            progress = downloaded_count / total_files if total_files > 0 else 1
            progress_bar.progress(progress)
            status_text.text(f"📥 Heruntergeladen: {downloaded_count}/{total_files} ({failed_count} Fehler)")
    
    # FINAL STATUS
    logger.info("\n" + "="*60)
    logger.info("🎉 DOWNLOAD COMPLETE")
    logger.info(f"✅ Successfully downloaded: {downloaded_count} files")
    logger.info(f"❌ Failed downloads: {failed_count} files")
    logger.info(f"📁 Saved to: {download_folder}")
    logger.info("="*60)
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ Download abgeschlossen! {downloaded_count} Dateien heruntergeladen.")
    
    if downloaded_count > 0:
        st.success(f"🎉 {downloaded_count} Dateien erfolgreich heruntergeladen in: {folder_name}")
    
    if failed_count > 0:
        st.warning(f"⚠️ {failed_count} Dateien konnten nicht heruntergeladen werden.")
    
    # Show folder contents
    try:
        folder_files = os.listdir(download_folder)
        logger.info(f"\n📁 Folder contents ({len(folder_files)} files):")
        for f in folder_files[:10]:  # Show first 10 files
            logger.info(f"   📄 {f}")
        if len(folder_files) > 10:
            logger.info(f"   ... and {len(folder_files) - 10} more files")
    except Exception as e:
        logger.error(f"Error listing folder contents: {e}")

def check_result_count(query: str) -> Optional[int]:
    """Get total count and optionally prefetch some results."""
    try:
        with st.spinner('Ergebnisse werden gezählt...'):
            # Progress UI elements
            st.caption("Rate limit aktiv: 3 Anfragen/Sekunde; 429 mit Retry-After")
            page_progress = st.progress(0.0)
            page_info = st.empty()
            res_info = st.empty()
            
            def _progress_cb(current_page: int, total_pages: Optional[int], results_so_far: int, total_results: Optional[int]):
                if total_pages and total_pages > 0:
                    pct = min(current_page / total_pages, 1.0)
                    page_progress.progress(pct)
                    page_info.text(f"Seiten: {current_page}/{total_pages}")
                else:
                    page_progress.progress(0.0)
                    page_info.text(f"Seiten: {current_page} (Gesamt unbekannt)")
                if total_results is not None:
                    res_info.text(f"Ergebnisse gesammelt: {results_so_far}/{total_results}")
                else:
                    res_info.text(f"Ergebnisse gesammelt: {results_so_far}")
            # First, get the true total count from API
            total_count = get_total_count_from_api(query)
            
            if total_count is None:
                # Fallback – API did not provide count. Fetch up to max_results then count
                logger.debug("totalNotices is None – falling back to manual counting up to max_results …")
                max_results_limit = st.session_state.get('current_max_results', 100)
                from math import ceil
                pages_needed = max(1, ceil(int(max_results_limit) / 100)) if max_results_limit else None
                results = ted_search(
                    query=query,
                    fields=["publication-number", "links", "notice-type"],
                    page=1,
                    limit=100,
                    max_pages=pages_needed,  # limit by max_results if available
                    progress_cb=_progress_cb
                )
                st.session_state.prefetched_results = results
                total_count = len(results)  # unknown true total; we know how many we fetched
                logger.debug(f"Fallback fetched {total_count} results (true total unbekannt)")
            else:
                logger.info(f"Total count from API: {total_count}")
            
            # If there are results and not too many, prefetch up to max_results (and not beyond a reasonable cap)
            if total_count and total_count > 0:
                max_results_limit = st.session_state.get('current_max_results', 100)
                target = min(int(total_count), int(max_results_limit)) if max_results_limit else int(total_count)
                from math import ceil
                pages_needed = ceil(target / 100)
                if target <= 2000:
                    logger.debug(f"Prefetching up to {target} results (pages: {pages_needed})…")
                    results = ted_search(
                        query=query,
                        fields=["publication-number", "links", "notice-type"],  # Minimal but sufficient for downloads
                        page=1,
                        limit=100,
                        max_pages=pages_needed,
                        progress_cb=_progress_cb
                    )
                    # Truncate safety (in case last page over-fetches)
                    if len(results) > target:
                        results = results[:target]
                    st.session_state.prefetched_results = results
                    logger.debug(f"Prefetched {len(results)} results (target {target})")
                else:
                    # Too many results to prefetch, will fetch on demand
                    st.session_state.prefetched_results = None
                    logger.info(f"Too many results ({total_count}) to prefetch - will fetch on demand (limit {max_results_limit})")
            else:
                st.session_state.prefetched_results = None
                logger.info("No results to prefetch")
            
            # finalize progress bar
            try:
                page_progress.progress(1.0)
            except Exception:
                pass
            return total_count
    except Exception as e:
        error_msg = f"Fehler beim Abrufen der Ergebnisanzahl: {str(e)}"
        logger.error(f"Error: {error_msg}")
        st.session_state.search_error = error_msg
        return None

def run_search(
    full_text, notice_type, cpv, place_of_performance, contract_type, value_min, value_max,
    pub_from, pub_to, deadline_from, deadline_to, buyer_name, buyer_town, 
    buyer_country, buyer_type, authority_activity, download_types, max_results
):
    """Run search with the given parameters"""
    st.session_state.search_results = None
    st.session_state.search_error = None
    st.session_state.search_query = None
    
    try:
        # Convert dates to strings if provided
        pub_from_str = pub_from.strftime("%Y%m%d") if pub_from else None
        pub_to_str = pub_to.strftime("%Y%m%d") if pub_to else None
        deadline_from_str = deadline_from.strftime("%Y%m%d") if deadline_from else None
        deadline_to_str = deadline_to.strftime("%Y%m%d") if deadline_to else None
        
        # Build query
        query = build_expert_query(
            full_text=full_text,
            notice_type=notice_type,
            cpv=cpv,
            place_of_performance=place_of_performance,
            contract_type=contract_type,
            value_min=value_min if value_min > 0 else None,
            value_max=value_max if value_max > 0 else None,
            pub_date_from=pub_from_str,
            pub_date_to=pub_to_str,
            deadline_from=deadline_from_str,
            deadline_to=deadline_to_str,
            buyer_name=buyer_name,
            buyer_town=buyer_town,
            buyer_country=buyer_country,
            buyer_type=buyer_type,
            authority_activity=authority_activity
        )

        # If Germany-wide override active, expand RC="DE" into OR of NUTS1 codes
        try:
            if st.session_state.get("rc_override") == "DE":
                nuts = load_nuts_de()
                if nuts and isinstance(nuts, dict) and "NUTS1" in nuts:
                    nuts1_codes = sorted(nuts["NUTS1"].keys())
                    rc_clause = "(" + " OR ".join([f'RC="{c}"' for c in nuts1_codes]) + ")"
                    if 'RC="DE"' in query:
                        query = query.replace('RC="DE"', rc_clause)
                    elif 'RC=' not in query:
                        query = f"{query} AND {rc_clause}"
        except Exception:
            # If anything goes wrong, fall back to the built query
            pass
        
        # Store query for display
        st.session_state.search_query = query
        
        # Debug: Show the constructed query
        logger.debug(f"Constructed query: {query}")
        st.info(f"Suchanfrage: {query}")
        
        # Store query in session state for later use
        st.session_state.current_query = query
        st.session_state.current_download_types = download_types
        st.session_state.current_max_results = max_results
        
        # Check result count and fetch results
        result_count = check_result_count(query)
        
        # Store result count (even if None)
        st.session_state.result_count = result_count
        
        if result_count is None:
            st.error("Fehler beim Abrufen der Ergebnisanzahl. Bitte versuchen Sie es erneut.")
            return
        elif result_count == 0:
            st.info("Keine Ergebnisse gefunden.")
            return
        else:
            # Show result count - download button will appear in main section below
            cap = int(max_results) if max_results else result_count
            if result_count > cap:
                st.warning(f"Es wurden {result_count} Ergebnisse gefunden, es werden jedoch nur die ersten {cap} berücksichtigt.")
                st.success(f"Es wurden {result_count} Ergebnisse gefunden (Anzeige/Download bis {cap}).")
            else:
                st.success(f"Es wurden {result_count} Ergebnisse gefunden.")
            # store for later UI use
            st.session_state.display_cap = cap
            
            # Set search_results to prefetched results so the results table appears
            if st.session_state.prefetched_results:
                st.session_state.search_results = st.session_state.prefetched_results
        
    except Exception as e:
        error_msg = f"Fehler bei der Suche: {str(e)}"
        logger.error(f"Error: {error_msg}")
        st.session_state.search_error = error_msg
        st.error(error_msg)
        return

def main():
    st.title("TED Expert-Search UI")
    
    # fetch_results function is now defined globally above main()
    
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
    if "rc_override" not in st.session_state:
        st.session_state.rc_override = None
    if "rc_version" not in st.session_state:
        st.session_state.rc_version = 0
    
    # Create sidebar for search parameters
    with st.sidebar:
        st.header("Suchparameter")
        
        # 1. Free text search
        full_text = st.text_input(
            "Volltext", 
            help="Volltextsuche in allen Feldern"
        )
        
        # 2. Business opportunities (Notice type)
        st.subheader("Geschäftsmöglichkeiten")
        notice_type_display = {v: k for k, v in _NOTICE_TYPE_MAP.items()}
        notice_type = st.selectbox(
            "Art der Bekanntmachung",
            options=[""] + list(_NOTICE_TYPE_MAP.values()),
            format_func=lambda x: notice_type_display.get(x, x) if x else "",
            help="Wählen Sie die Art der Geschäftsmöglichkeit"
        )
        
        # 3. Business section (CPV)
        st.subheader("Geschäftsbereich")
        cpv = st.text_input(
            "CPV-Code", 
            help="CPV-Code (Common Procurement Vocabulary), z.B. 45000000 für Bauarbeiten"
        )
        
        # 4. Place of performance (where the work will be done)
        st.subheader("Ausführungsort")
        # Quick actions for country-wide search and reset
        rc_col1, rc_col2 = st.columns(2)
        with rc_col1:
            if st.button("🇩🇪 Ganz Deutschland (DE)"):
                st.session_state.rc_override = "DE"
                st.session_state.rc_version += 1
                try:
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
                except Exception:
                    pass
        with rc_col2:
            if st.button("Auswahl löschen"):
                st.session_state.rc_override = None
                st.session_state.rc_version += 1
                try:
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
                except Exception:
                    pass
        if st.session_state.get("rc_override") == "DE":
            st.info("Deutschland (DE) ausgewählt – Suche umfasst ganz Deutschland.")
        nuts_data = load_nuts_de()
        if nuts_data and isinstance(nuts_data, dict) and "NUTS1" in nuts_data:
            # NUTS1 (Bundesland)
            nuts1_nodes = nuts_data["NUTS1"]
            nuts1_codes = sorted(nuts1_nodes.keys())
            nuts1_labels = {c: f"{c} – {nuts1_nodes[c]['name']}" for c in nuts1_codes}
            selected_nuts1 = st.selectbox(
                "Bundesland (NUTS 1)",
                options=[""] + nuts1_codes,
                format_func=lambda c: nuts1_labels.get(c, "") if c else "",
                key=f"nuts1_{st.session_state['rc_version']}",
                help="Wählen Sie ein Bundesland"
            )

            selected_nuts2 = ""
            selected_nuts3 = ""

            # NUTS2 (Region) depends on NUTS1
            if selected_nuts1:
                nuts2_nodes = nuts1_nodes[selected_nuts1].get("children", {})
                nuts2_codes = sorted(nuts2_nodes.keys())
                nuts2_labels = {c: f"{c} – {nuts2_nodes[c]['name']}" for c in nuts2_codes}
                selected_nuts2 = st.selectbox(
                    "Region (NUTS 2)",
                    options=[""] + nuts2_codes,
                    format_func=lambda c: nuts2_labels.get(c, "") if c else "",
                    key=f"nuts2_{st.session_state['rc_version']}",
                    help="Optional: Wählen Sie eine Region"
                )

                # NUTS3 (Kreis/Stadt) depends on NUTS2
                if selected_nuts2:
                    nuts3_nodes = nuts2_nodes[selected_nuts2].get("children", {})
                    nuts3_codes = sorted(nuts3_nodes.keys())
                    nuts3_labels = {c: f"{c} – {nuts3_nodes[c]['name']}" for c in nuts3_codes}
                    selected_nuts3 = st.selectbox(
                        "Kreis/Stadt (NUTS 3)",
                        options=[""] + nuts3_codes,
                        format_func=lambda c: nuts3_labels.get(c, "") if c else "",
                        key=f"nuts3_{st.session_state['rc_version']}",
                        help="Optional: Wählen Sie Kreis/Stadt"
                    )

            # Determine the code to search with (prefer deepest selection)
            if selected_nuts3:
                place_of_performance = selected_nuts3
            elif selected_nuts2:
                place_of_performance = selected_nuts2
            elif selected_nuts1:
                place_of_performance = selected_nuts1
            else:
                # No selection; allow manual fallback
                place_of_performance = st.text_input(
                    "Ort der Leistungserbringung (Fallback)",
                    help="Land (DE), NUTS-Code (DE71) oder PLZ (34117) wo die Arbeit ausgeführt wird"
                )
        else:
            # Fallback to manual input if NUTS config is missing
            place_of_performance = st.text_input(
                "Ort der Leistungserbringung",
                help="Land (DE), NUTS-Code (DE71) oder PLZ (34117) wo die Arbeit ausgeführt wird"
            )
        
        # Apply Germany override if set
        rc_override = st.session_state.get("rc_override")
        if rc_override:
            place_of_performance = rc_override
            st.caption("Ausführungsort: Deutschland (DE)")
        
        # 5. Nature of contract
        st.subheader("Auftragsart")
        contract_type_display = {v: k for k, v in _CONTRACT_TYPE_MAP.items()}
        contract_type = st.selectbox(
            "Art des Auftrags",
            options=[""] + list(_CONTRACT_TYPE_MAP.values()),
            format_func=lambda x: contract_type_display.get(x, x) if x else "",
            help="Wählen Sie die Art des Auftrags"
        )
        
        # 6. Procurement value (min/max)
        st.subheader("Auftragswert")
        col1, col2 = st.columns(2)
        with col1:
            value_min = st.number_input(
                "Mindestbetrag (EUR)",
                min_value=0,
                value=0,
                step=1000,
                help="Mindestauftragswert in Euro"
            )
        with col2:
            value_max = st.number_input(
                "Höchstbetrag (EUR)",
                min_value=0,
                value=0,
                step=1000,
                help="Höchstauftragswert in Euro (0 = unbegrenzt)"
            )
        
        # 7. Publication date (from/to)
        st.subheader("Veröffentlichungsdatum")
        
        # Default to one month before today until today
        from datetime import datetime, timedelta
        today = datetime.now().date()
        one_month_ago = today - timedelta(days=30)
        # Initialize date defaults and version once
        if "pub_from_default" not in st.session_state:
            st.session_state["pub_from_default"] = one_month_ago
        if "pub_to_default" not in st.session_state:
            st.session_state["pub_to_default"] = today
        if "pub_date_version" not in st.session_state:
            st.session_state["pub_date_version"] = 0
        
        # Quick selections BEFORE the date inputs so state is set first
        qcol1, qcol2, qcol3, qcol4 = st.columns(4)
        def _apply_date_range(days: int):
            st.session_state["pub_from_default"] = today - timedelta(days=days)
            st.session_state["pub_to_default"] = today
            st.session_state["pub_date_version"] += 1
            try:
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()
            except Exception:
                pass
        with qcol1:
            if st.button("Letzter Tag"):
                _apply_date_range(1)
        with qcol2:
            if st.button("Letzte 3 Tage"):
                _apply_date_range(3)
        with qcol3:
            if st.button("Letzte Woche"):
                _apply_date_range(7)
        with qcol4:
            if st.button("Letzter Monat"):
                _apply_date_range(30)

        # Helper: date input with German format if supported by Streamlit
        def _date_input_de(label: str, value, key=None, help: str | None = None):
            try:
                # Streamlit newer versions support 'format' argument
                return st.date_input(label, value=value, key=key, help=help, format="DD.MM.YYYY")
            except TypeError:
                # Fallback for older Streamlit versions
                return st.date_input(label, value=value, key=key, help=help)

        col1, col2 = st.columns(2)
        with col1:
            pub_from = _date_input_de(
                "Von",
                value=st.session_state.get("pub_from_default", one_month_ago),
                key=f"pub_from_date_{st.session_state['pub_date_version']}",
                help="Veröffentlichungsdatum ab"
            )
            try:
                st.caption(f"Ausgewählt: {pub_from.strftime('%d.%m.%Y')}")
            except Exception:
                pass
        with col2:
            pub_to = _date_input_de(
                "Bis",
                value=st.session_state.get("pub_to_default", today),
                key=f"pub_to_date_{st.session_state['pub_date_version']}",
                help="Veröffentlichungsdatum bis"
            )
            try:
                st.caption(f"Ausgewählt: {pub_to.strftime('%d.%m.%Y')}")
            except Exception:
                pass
        
        # 8. Deadline (from/to)
        st.subheader("Einreichungsfrist")
        col1, col2 = st.columns(2)
        with col1:
            deadline_from = _date_input_de(
                "Von",
                value=None,
                help="Einreichungsfrist ab"
            )
            if deadline_from:
                try:
                    st.caption(f"Ausgewählt: {deadline_from.strftime('%d.%m.%Y')}")
                except Exception:
                    pass
        with col2:
            deadline_to = _date_input_de(
                "Bis",
                value=None,
                help="Einreichungsfrist bis"
            )
            if deadline_to:
                try:
                    st.caption(f"Ausgewählt: {deadline_to.strftime('%d.%m.%Y')}")
                except Exception:
                    pass
        
        # 9. Buyer information
        st.subheader("Auftraggeber")
        
        buyer_name = st.text_input(
            "Name des Auftraggebers", 
            help="Name oder Teil des Namens des Auftraggebers"
        )
        
        buyer_town = st.text_input(
            "Stadt des Auftraggebers", 
            help="Stadt oder Ort des Auftraggebers"
        )
        
        buyer_country = st.selectbox(
            "Land des Auftraggebers",
            options=["", "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"],
            help="Land des Auftraggebers (ISO-Code)"
        )
        
        buyer_type = st.selectbox(
            "Art des Auftraggebers",
            options=["", "body-public", "ministry", "national-agency", "regional-agency", "regional-authority", "local-authority", "body-governed-public-law", "eu-institution", "international-organisation", "other"],
            help="Typ/Art des Auftraggebers"
        )
        
        authority_activity = st.selectbox(
            "Haupttätigkeit des Auftraggebers",
            options=["", "airport", "defence", "econ-aff", "education", "electricity", "env-pro", "gas-heat", "gas-oil", "gen-pub", "hc-am", "health", "port", "post", "pub-os", "rail", "rcr", "soc-pro", "solid-fuel", "urttb", "water"],
            format_func=lambda x: {
                "airport": "Flughafen", "defence": "Verteidigung", "econ-aff": "Wirtschaft", 
                "education": "Bildung", "electricity": "Elektrizität", "env-pro": "Umweltschutz",
                "gas-heat": "Gas/Wärme", "gas-oil": "Gas/Öl", "gen-pub": "Öffentliche Verwaltung",
                "hc-am": "Wohnen/Gemeinde", "health": "Gesundheit", "port": "Hafen",
                "post": "Post", "pub-os": "Öffentliche Sicherheit", "rail": "Eisenbahn",
                "rcr": "Erholung/Kultur", "soc-pro": "Sozialschutz", "solid-fuel": "Feste Brennstoffe",
                "urttb": "Stadtverkehr", "water": "Wasser"
            }.get(x, x) if x else "",
            help="Haupttätigkeit des Auftraggebers"
        )
        
        # Download options
        st.subheader("Download-Optionen")
        lang_col, fmt_col = st.columns(2)
        with lang_col:
            lang_de = st.checkbox("Deutsch", value=True)
            lang_en = st.checkbox("Englisch", value=False)
        with fmt_col:
            fmt_pdf = st.checkbox("PDF", value=True)
            fmt_json = st.checkbox("JSON", value=False)

        # Build download types from language/format checkboxes
        download_types = []
        if fmt_pdf:
            if lang_de:
                download_types.append("pdf_de")
            if lang_en:
                download_types.append("pdf_en")
        if fmt_json:
            if lang_de:
                download_types.append("json_de")
            if lang_en:
                download_types.append("json_en")
        
        max_results = st.number_input(
            "Maximale Anzahl Ergebnisse",
            min_value=1,
            max_value=10000,
            value=100,
            step=100,
            help="Begrenzen Sie die Anzahl der heruntergeladenen Ergebnisse."
        )
        
        # Search button
        if st.button("Suche starten", type="primary"):
            run_search(
                full_text, notice_type, cpv, place_of_performance, contract_type, value_min, value_max,
                pub_from, pub_to, deadline_from, deadline_to, buyer_name, buyer_town, 
                buyer_country, buyer_type, authority_activity, download_types, max_results
            )
    
    # Main content area
    if st.session_state.search_query:
        st.subheader("Suchanfrage")
        st.code(st.session_state.search_query)
    
    if st.session_state.search_error:
        st.error(f"Fehler bei der Suche: {st.session_state.search_error}")
    
    # Independent download section - always show after search
    if st.session_state.get('current_query'):
        st.subheader("🔽 Download")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Alle Ergebnisse herunterladen", type="primary", key="download_button"):
                fetch_results()
        with col2:
            download_types = st.session_state.get('current_download_types', [])
            if download_types:
                cap = st.session_state.get('display_cap') or st.session_state.get('current_max_results')
                if st.session_state.get('result_count') and cap and st.session_state['result_count'] > cap:
                    st.write(f"Lädt bis zu {cap} Ergebnisse herunter in: {', '.join(download_types)}")
                else:
                    st.write(f"Lädt alle Ergebnisse herunter in: {', '.join(download_types)}")
            else:
                st.write("Lädt alle gefundenen Ergebnisse in den ausgewählten Formaten herunter.")
    
    # Separate results info section
    if "result_count" in st.session_state and st.session_state.result_count is not None:
        result_count = st.session_state.result_count
        if result_count > 0:
            cap = st.session_state.get('display_cap') or st.session_state.get('current_max_results')
            if cap and result_count > cap:
                st.info(f"Gefundene Ergebnisse: {result_count} (Anzeige/Download bis {cap})")
            else:
                st.info(f"Gefundene Ergebnisse: {result_count}")
        elif result_count == 0:
            st.info("Keine Ergebnisse gefunden.")
        else:
            st.warning("Ergebnisse konnten nicht abgerufen werden. Bitte versuchen Sie es erneut.")

    
    # Display full results if available
    if st.session_state.search_results:
        results = st.session_state.search_results
        
        cap = st.session_state.get('display_cap') or st.session_state.get('current_max_results')
        display_results = results
        if cap and isinstance(cap, int) and len(results) > cap:
            display_results = results[:cap]
            st.warning(f"Anzeige auf die ersten {cap} Ergebnisse begrenzt.")
        st.subheader(f"Suchergebnisse ({len(display_results)} Treffer)")
        
        if display_results:
            # Create DataFrame from results
            data = []
            for notice in display_results:
                row = {
                    "Nummer": notice.get("publication-number", ""),
                    "Datum": notice.get("publication-date", ""),
                    "Auftraggeber": notice.get("buyer-name", ""),
                    "Titel": notice.get("title", ""),
                    "CPV": notice.get("cpv-code", ""),
                    "Land": notice.get("buyer-country", "")
                }
                
                # Add links if available - only for requested formats/languages
                links = notice.get("links", {})
                download_types = st.session_state.get('current_download_types', [])
                
                if links:
                    if "ted" in links:
                        row["TED Link"] = links["ted"]
                    
                    # Add PDF links only for requested languages
                    if "pdf" in links and links["pdf"]:
                        for lang, url in links["pdf"].items():
                            lang_lower = lang.lower()
                            if f"pdf_de" in download_types and lang_lower in ['deu', 'de', 'ger']:
                                row["PDF (Deutsch)"] = url
                            elif f"pdf_en" in download_types and lang_lower in ['eng', 'en', 'english']:
                                row["PDF (English)"] = url
                    
                    # Add JSON links only for requested languages  
                    if "json" in links and links["json"]:
                        for lang, url in links["json"].items():
                            lang_lower = lang.lower()
                            if f"json_de" in download_types and lang_lower in ['deu', 'de', 'ger']:
                                row["JSON (Deutsch)"] = url
                            elif f"json_en" in download_types and lang_lower in ['eng', 'en', 'english']:
                                row["JSON (English)"] = url
                    
                    # Add XML link if available (always show)
                    if "xml" in links and links["xml"]:
                        if "MUL" in links["xml"]:
                            row["XML"] = links["xml"]["MUL"]
                
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
