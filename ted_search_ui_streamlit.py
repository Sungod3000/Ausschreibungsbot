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
    full_text: str = None,
    notice_type: str = None,
    cpv: str = None,
    place_of_performance: str = None,
    contract_type: str = None,
    value_min: int = None,
    value_max: int = None,
    pub_date_from: str = None,
    pub_date_to: str = None,
    deadline_from: str = None,
    deadline_to: str = None,
    buyer_name: str = None,
    buyer_town: str = None,
    buyer_country: str = None,
    buyer_type: str = None,
    authority_activity: str = None,
) -> str:
    """Build TED API expert query from simplified parameters."""
    parts: List[str] = []
    
    # 1. Free text search
    if full_text and full_text.strip():
        parts.append(f'FT~("{full_text.strip()}")')
    
    # 2. Notice type (business opportunities)
    if notice_type:
        parts.append(f'NT="{notice_type}"')
    
    # 3. CPV code (business section)
    if cpv and cpv.strip():
        parts.append(f'PC="{cpv.strip()}"')
    
    # 4. Place of performance (where the work will be done)
    if place_of_performance and place_of_performance.strip():
        parts.append(f'RC="{place_of_performance.strip()}"')
    
    # 5. Contract type (nature of contract)
    if contract_type:
        parts.append(f'NC="{contract_type}"')
    
    # 5. Procurement value
    if value_min is not None and value_max is not None:
        parts.append(f'VR=[{value_min} TO {value_max}]')
    elif value_min is not None:
        parts.append(f'VR>={value_min}')
    elif value_max is not None:
        parts.append(f'VR<={value_max}')
    
    # 6. Publication date
    if pub_date_from and pub_date_to:
        # Use separate >= and <= operators instead of TO syntax
        parts.append(f'PD>={pub_date_from}')
        parts.append(f'PD<={pub_date_to}')
    elif pub_date_from:
        parts.append(f'PD>={pub_date_from}')
    elif pub_date_to:
        parts.append(f'PD<={pub_date_to}')
    
    # 7. Deadline
    if deadline_from and deadline_to:
        # Use separate >= and <= operators instead of TO syntax
        parts.append(f'DD>={deadline_from}')
        parts.append(f'DD<={deadline_to}')
    elif deadline_from:
        parts.append(f'DD>={deadline_from}')
    elif deadline_to:
        parts.append(f'DD<={deadline_to}')
    
    # 8. Buyer information
    if buyer_name and buyer_name.strip():
        parts.append(f'AU~("{buyer_name.strip()}")')
    
    if buyer_town and buyer_town.strip():
        parts.append(f'buyer-town~("{buyer_town.strip()}")')
    
    if buyer_country:
        parts.append(f'CY="{buyer_country}"')  # Use CY for country
    
    if buyer_type:
        parts.append(f'buyer-type="{buyer_type}"')
    
    if authority_activity:
        parts.append(f'authority-main-activity="{authority_activity}"')
    
    # If no conditions specified, return empty query (this shouldn't happen with default dates)
    if not parts:
        # This should not happen since we have default publication dates
        print("WARNING - No search criteria specified, this should not happen!")
        return ""
    
    return ' AND '.join(parts)

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

def get_total_count_from_api(query: str) -> Optional[int]:
    """Get the true total count from TED API without fetching all results."""
    try:
        # Make a single API call with minimal data to get totalNotices
        payload = {
            "query": query,
            "page": 1,
            "limit": 1,  # Minimal limit to get count
            "fields": ["notice-type"]  # Minimal field set
        }
        
        print(f"DEBUG - Getting total count for query: {query}")
        print(f"DEBUG - Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/v3/notices/search",
            json=payload,
            timeout=30
        )
        
        print(f"DEBUG - Response status: {response.status_code}")
        
        response.raise_for_status()
        data = response.json()
        
        # Get total count from API response
        total_count = data.get("totalNotices")
        print(f"DEBUG - API returned totalNotices: {total_count}")

        # Fallback: if API did not supply totalNotices, return None so caller can decide
        return total_count
    except Exception as e:
        print(f"DEBUG - Error getting total count: {str(e)}")
        return None

def create_download_folder_name(query: str, download_types: list) -> str:
    """Create a folder name based on search parameters."""
    import re
    from datetime import datetime
    
    # Extract key search terms from query
    folder_parts = []
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_parts.append(timestamp)
    
    # Extract key terms from query
    if "RC=" in query:
        rc_match = re.search(r'RC="([^"]+)"', query)
        if rc_match:
            folder_parts.append(f"RC_{rc_match.group(1)}")
    
    if "PD>=" in query:
        pd_match = re.search(r'PD>=([0-9]+)', query)
        if pd_match:
            folder_parts.append(f"from_{pd_match.group(1)}")
    
    if "PD<=" in query:
        pd_match = re.search(r'PD<=([0-9]+)', query)
        if pd_match:
            folder_parts.append(f"to_{pd_match.group(1)}")
    
    if "NT=" in query:
        nt_match = re.search(r'NT="([^"]+)"', query)
        if nt_match:
            folder_parts.append(f"NT_{nt_match.group(1)}")
    
    # Add download types
    if download_types:
        folder_parts.append("_".join(download_types))
    
    # Join with underscores and limit length
    folder_name = "_".join(folder_parts)
    # Replace invalid characters
    folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
    # Limit length
    if len(folder_name) > 100:
        folder_name = folder_name[:100]
    
    return folder_name

def fetch_results():
    """Download files from prefetched results with verbose debugging and rate limiting."""
    import os
    import requests
    import time
    from datetime import datetime
    
    print("\n" + "="*60)
    print("🔥 FETCH_RESULTS STARTED")
    print("="*60)
    
    # STEP 1: Check if we have results
    print("\n📋 STEP 1: Checking for prefetched results...")
    if not hasattr(st.session_state, 'prefetched_results'):
        print("❌ ERROR: No 'prefetched_results' attribute in session state")
        st.error("Keine Ergebnisse gefunden. Bitte führen Sie zuerst eine Suche durch.")
        return
    
    if not st.session_state.prefetched_results:
        print("❌ ERROR: prefetched_results is empty")
        st.error("Keine Ergebnisse zum Herunterladen gefunden.")
        return
    
    results = st.session_state.prefetched_results
    print(f"✅ Found {len(results)} prefetched results")
    
    # STEP 2: Get download types and search parameters
    print("\n📋 STEP 2: Getting download parameters...")
    download_types = st.session_state.get('current_download_types', ['pdf_de'])
    query = st.session_state.get('current_query', 'unknown_query')
    
    print(f"📥 Download types: {download_types}")
    print(f"🔍 Search query: {query}")
    
    if not download_types:
        print("❌ ERROR: No download types selected")
        st.error("Bitte wählen Sie mindestens ein Download-Format aus.")
        return
    
    # STEP 3: Create folder with search parameters in name
    print("\n📋 STEP 3: Creating download folder...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extract key search parameters for folder name
    folder_parts = [timestamp]
    
    # Add query parts to folder name
    if 'RC=' in query:
        import re
        rc_match = re.search(r'RC="?([^"\s]+)"?', query)
        if rc_match:
            folder_parts.append(f"RC_{rc_match.group(1)}")
    
    if 'PD>=' in query:
        pd_matches = re.findall(r'PD[><=]+([0-9]{8})', query)
        if len(pd_matches) >= 2:
            folder_parts.append(f"PD_{pd_matches[0]}_to_{pd_matches[1]}")
        elif pd_matches:
            folder_parts.append(f"PD_{pd_matches[0]}")
    
    # Add download types
    types_str = "_".join(sorted(download_types))
    folder_parts.append(types_str)
    
    folder_name = "_".join(folder_parts)
    # Limit folder name length
    if len(folder_name) > 100:
        folder_name = folder_name[:100]
    
    download_folder = os.path.join(os.getcwd(), "downloads", folder_name)
    
    print(f"📁 Creating folder: {folder_name}")
    print(f"📁 Full path: {download_folder}")
    
    try:
        os.makedirs(download_folder, exist_ok=True)
        print(f"✅ Folder created successfully")
    except Exception as e:
        print(f"❌ ERROR creating folder: {e}")
        st.error(f"Konnte Download-Ordner nicht erstellen: {e}")
        return
    
    if not os.path.exists(download_folder):
        print(f"❌ ERROR: Folder does not exist after creation")
        st.error(f"Download-Ordner wurde nicht erstellt: {download_folder}")
        return
    
    st.success(f"📁 Download-Ordner erstellt: {folder_name}")
    
    # STEP 4: Count and analyze available files
    print("\n📋 STEP 4: Analyzing available files...")
    
    total_files = 0
    file_analysis = []
    
    for i, result in enumerate(results):
        pub_number = result.get("publication-number", f"notice_{i}")
        links = result.get("links", {})
        
        print(f"\n📄 Result {i+1}/{len(results)}: {pub_number}")
        print(f"   Available link types: {list(links.keys()) if links else 'No links'}")
        
        result_files = []
        
        # Check PDF links
        if "pdf" in links and isinstance(links["pdf"], dict):
            print(f"   📕 PDF languages: {list(links['pdf'].keys())}")
            for lang, url in links["pdf"].items():
                should_download = False
                file_suffix = ""
                
                if "pdf_de" in download_types and lang.upper() in ['DEU', 'DE']:
                    should_download = True
                    file_suffix = "_DE.pdf"
                    print(f"   ✅ Will download PDF (German): {lang}")
                elif "pdf_en" in download_types and lang.upper() in ['ENG', 'EN']:
                    should_download = True
                    file_suffix = "_EN.pdf"
                    print(f"   ✅ Will download PDF (English): {lang}")
                else:
                    print(f"   ⏭️  Skipping PDF language: {lang}")
                
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
            print(f"   📗 JSON languages: {list(links['json'].keys())}")
            for lang, url in links["json"].items():
                should_download = False
                file_suffix = ""
                
                if "json_de" in download_types and lang.upper() in ['DEU', 'DE']:
                    should_download = True
                    file_suffix = "_DE.json"
                    print(f"   ✅ Will download JSON (German): {lang}")
                elif "json_en" in download_types and lang.upper() in ['ENG', 'EN']:
                    should_download = True
                    file_suffix = "_EN.json"
                    print(f"   ✅ Will download JSON (English): {lang}")
                else:
                    print(f"   ⏭️  Skipping JSON language: {lang}")
                
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
    
    print(f"\n📊 ANALYSIS COMPLETE:")
    print(f"   📄 Total results: {len(results)}")
    print(f"   📥 Total files to download: {total_files}")
    print(f"   📁 Download folder: {folder_name}")
    
    if total_files == 0:
        print("❌ No files to download!")
        st.warning("Keine Dateien zum Herunterladen gefunden. Überprüfen Sie die ausgewählten Formate.")
        return
    
    # STEP 5: Download files with rate limiting
    print("\n📋 STEP 5: Starting downloads with rate limiting (max 5/sec)...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    downloaded_count = 0
    failed_count = 0
    last_request_time = 0
    
    st.info(f"📥 Beginne Download von {total_files} Dateien...")
    
    for result_info in file_analysis:
        pub_number = result_info['pub_number']
        files = result_info['files']
        
        if not files:
            continue
            
        print(f"\n📄 Downloading files for: {pub_number}")
        
        for file_info in files:
            filename = file_info['filename']
            url = file_info['url']
            file_type = file_info['type']
            lang = file_info['lang']
            
            # Rate limiting: max 5 requests per second
            current_time = time.time()
            time_since_last = current_time - last_request_time
            if time_since_last < 0.2:  # 0.2 seconds = 5 requests per second
                sleep_time = 0.2 - time_since_last
                print(f"⏱️  Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            filepath = os.path.join(download_folder, filename)
            
            print(f"\n🔽 Downloading: {filename}")
            print(f"   📎 URL: {url[:80]}...")
            print(f"   📁 Path: {filepath}")
            
            try:
                last_request_time = time.time()
                response = requests.get(url, timeout=30)
                print(f"   📡 HTTP Status: {response.status_code}")
                print(f"   📏 Content Length: {len(response.content)} bytes")
                
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Verify file was written
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    print(f"   ✅ SUCCESS: {filename} ({file_size} bytes)")
                    downloaded_count += 1
                else:
                    print(f"   ❌ ERROR: File not found after writing: {filename}")
                    failed_count += 1
                
            except Exception as e:
                print(f"   ❌ ERROR downloading {filename}: {e}")
                st.warning(f"Fehler beim Herunterladen von {filename}: {str(e)}")
                failed_count += 1
            
            # Update progress
            progress = downloaded_count / total_files if total_files > 0 else 1
            progress_bar.progress(progress)
            status_text.text(f"📥 Heruntergeladen: {downloaded_count}/{total_files} ({failed_count} Fehler)")
    
    # FINAL STATUS
    print("\n" + "="*60)
    print("🎉 DOWNLOAD COMPLETE")
    print(f"✅ Successfully downloaded: {downloaded_count} files")
    print(f"❌ Failed downloads: {failed_count} files")
    print(f"📁 Saved to: {download_folder}")
    print("="*60)
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ Download abgeschlossen! {downloaded_count} Dateien heruntergeladen.")
    
    if downloaded_count > 0:
        st.success(f"🎉 {downloaded_count} Dateien erfolgreich heruntergeladen in: {folder_name}")
    
    if failed_count > 0:
        st.warning(f"⚠️ {failed_count} Dateien konnten nicht heruntergeladen werden.")
    
    # Show folder contents
    try:
        folder_files = os.listdir(download_folder)
        print(f"\n📁 Folder contents ({len(folder_files)} files):")
        for f in folder_files[:10]:  # Show first 10 files
            print(f"   📄 {f}")
        if len(folder_files) > 10:
            print(f"   ... and {len(folder_files) - 10} more files")
    except Exception as e:
        print(f"Error listing folder contents: {e}")

def check_result_count(query: str) -> Optional[int]:
    """Get total count and optionally prefetch some results."""
    try:
        with st.spinner('Ergebnisse werden gezählt...'):
            # First, get the true total count from API
            total_count = get_total_count_from_api(query)
            
            if total_count is None:
                # Fallback – API did not provide count. Fetch ALL results and count manually
                print("DEBUG - totalNotices is None – falling back to manual counting of ALL results …")
                results = ted_search(
                    query=query,
                    fields=["notice-type"],
                    page=1,
                    limit=100,
                    max_pages=None  # fetch ALL pages, no limit
                )
                st.session_state.prefetched_results = results
                total_count = len(results)
                print(f"DEBUG - Fallback fetched ALL {total_count} results")
            else:
                print(f"DEBUG - Total count from API: {total_count}")
            
            # If there are results and not too many, prefetch them for faster download
            if total_count > 0 and total_count <= 2000:  # Reasonable limit for prefetching
                print(f"DEBUG - Prefetching ALL {total_count} results...")
                results = ted_search(
                    query=query,
                    fields=["notice-type"],  # Minimal field set for prefetch
                    page=1,
                    limit=100,  # Reasonable page size
                    max_pages=None  # Get ALL pages
                )
                st.session_state.prefetched_results = results
                print(f"DEBUG - Prefetched ALL {len(results)} results")
            else:
                # Too many results to prefetch, will fetch on demand
                st.session_state.prefetched_results = None
                print(f"DEBUG - Too many results ({total_count}) to prefetch - will fetch on demand")
            
            return total_count
    except Exception as e:
        error_msg = f"Fehler beim Abrufen der Ergebnisanzahl: {str(e)}"
        print(f"DEBUG - Error: {error_msg}")
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
        
        # Store query for display
        st.session_state.search_query = query
        
        # Debug: Show the constructed query
        print(f"DEBUG - Constructed query: {query}")
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
            st.success(f"Es wurden {result_count} Ergebnisse gefunden.")
            
            # Set search_results to prefetched results so the results table appears
            if st.session_state.prefetched_results:
                st.session_state.search_results = st.session_state.prefetched_results
        
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
        place_of_performance = st.text_input(
            "Ort der Leistungserbringung",
            help="Land (DE), NUTS-Code (DE71) oder PLZ (34117) wo die Arbeit ausgeführt wird"
        )
        
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
        
        col1, col2 = st.columns(2)
        with col1:
            pub_from = st.date_input(
                "Von",
                value=one_month_ago,
                help="Veröffentlichungsdatum ab"
            )
        with col2:
            pub_to = st.date_input(
                "Bis",
                value=today,
                help="Veröffentlichungsdatum bis"
            )
        
        # 8. Deadline (from/to)
        st.subheader("Einreichungsfrist")
        col1, col2 = st.columns(2)
        with col1:
            deadline_from = st.date_input(
                "Von",
                value=None,
                help="Einreichungsfrist ab"
            )
        with col2:
            deadline_to = st.date_input(
                "Bis",
                value=None,
                help="Einreichungsfrist bis"
            )
        
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
        
        download_types = st.multiselect(
            "Dateiformate",
            options=["pdf_de", "pdf_en", "json_de", "json_en"],
            default=["pdf_de", "json_de"],
            format_func=lambda x: {
                "pdf_de": "PDF (Deutsch)",
                "pdf_en": "PDF (English)", 
                "json_de": "JSON (Deutsch)",
                "json_en": "JSON (English)"
            }.get(x, x),
            help="Wählen Sie die gewünschten Dateiformate und Sprachen für den Download."
        )
        
        max_results = st.number_input(
            "Maximale Anzahl Ergebnisse",
            min_value=1,
            max_value=10000,
            value=1000,
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
                st.write(f"Lädt alle Ergebnisse herunter in: {', '.join(download_types)}")
            else:
                st.write("Lädt alle gefundenen Ergebnisse in den ausgewählten Formaten herunter.")
    
    # Separate results info section
    if "result_count" in st.session_state and st.session_state.result_count is not None:
        result_count = st.session_state.result_count
        if result_count > 0:
            st.info(f"Gefundene Ergebnisse: {result_count}")
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
