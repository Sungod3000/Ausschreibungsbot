# TED Expert-Search UI

Eine moderne Streamlit-basierte Benutzeroberfläche für erweiterte Abfragen der TED (Tenders Electronic Daily) API mit intelligenter Ergebnisvorschau und Bulk-Download-Funktionalität.

## 🎯 Projektbeschreibung

Die TED Expert-Search UI ist eine benutzerfreundliche Frontend-Anwendung, die es ermöglicht, komplexe Suchanfragen gegen die TED API zu erstellen, auszuführen und die Ergebnisse in verschiedenen Formaten herunterzuladen. Die Anwendung bietet eine zweistufige Workflow:
```bash
pip install -r requirements.txt
```

### 2. Streamlit-Server starten
```bash
streamlit run ted_search_ui_streamlit.py
```

Die Anwendung öffnet sich automatisch im Browser unter `http://localhost:8501`.

## Zwei-Schritt-Suchverfahren

### Schritt 1: Suchparameter eingeben und Ergebnisanzahl prüfen

1. **Suchparameter festlegen** in der Seitenleiste:
   - Volltext-Suche (optional)
   - Geschäftsmöglichkeiten (Bekanntmachungsart)
   - Geschäftsbereich (CPV-Code)
   - Ausführungsort (NUTS-Code)
   - Auftragsart, Auftragswert, Termine
   - Auftraggeber-Informationen

2. **Download-Formate auswählen**: PDF/JSON (Deutsch/Englisch)

3. **"Ergebnisse zählen"** klicken → Zeigt Anzahl gefundener Ausschreibungen

### Schritt 2: Bulk-Download durchführen

4. **" Alle Ergebnisse herunterladen"** klicken
   - Erstellt automatisch Ordner mit Suchparametern im Namen
   - Lädt alle Dateien in ausgewählten Formaten herunter
   - Zeigt Echtzeit-Fortschritt (Rate-Limit: 5 Downloads/Sekunde)

### Download-Ordner-Struktur
```bash
downloads/
└── YYYYMMDD_HHMMSS_RC_[region]_PD_[dates]_[formats]/
    ├── 473043-2025_DE.pdf
    └── ...
```

## Suchfelder und Aliase

### Volltext und Kategorisierung
- **FT (Volltext)**: Suche in allen Feldern
- **NT (Bekanntmachungsart)**: Art der Geschäftsmöglichkeit
- **PC (CPV-Code)**: Common Procurement Vocabulary

### Geografische Parameter
- **RC (Regionalcode)**: NUTS-Code für Ausführungsort
- **CY (Auftraggeber-Land)**: Ländercode der Vergabestelle

### Vertragliche Parameter
- **NC (Auftragsart)**: Bauleistungen/Lieferungen/Dienstleistungen
- **VL/VH (Auftragswert)**: Mindest-/Höchstauftragswert

### Zeitliche Parameter
- **PD (Veröffentlichungsdatum)**: Bekanntmachungsveröffentlichung
- **DD (Einreichungsfrist)**: Einreichungsfrist-Bereich

### Auftraggeber-Informationen
- **BN/BT (Name/Ort)**: Vergabestelle
- **TY (Typ)**: Behördenkategorie
- **MA (Haupttätigkeit)**: Hauptsektor

## Technische Architektur

### Hauptdateien

#### `ted_search_ui_streamlit.py` (Hauptanwendung - 49KB)
**Hauptfunktionen**:
- `main()` - Streamlit-UI und Session-Management
- `build_expert_query()` - UI-Parameter → TED API-Syntax
- `run_search()` - Suchausführung mit Parametern
- `check_result_count()` - Ergebnisanzahl + Prefetching
- `fetch_results()` - Bulk-Download mit Rate-Limiting
- `get_total_count_from_api()` - Echte API-Gesamtanzahl
- `create_download_folder_name()` - Intelligente Ordnernamen

**Konstanten**:
- `SEARCH_FIELD_ALIASES` - UI→API Feldmapping (13 Suchfelder)
- `_NOTICE_TYPE_MAP` - 16 Bekanntmachungsarten
- `_CONTRACT_TYPE_MAP` - 3 Auftragsarten

#### `ted_search_client.py` (API-Client - 8KB)
**Hauptfunktionen**:
- `ted_search()` - TED API mit Paginierung
- `export_to_excel()` - Excel-Export
- `export_to_json()` - JSON-Export
- `_throttle_api()` - Rate-Limiting (3 req/sec)

### Referenzdateien (in `docs/`)
- **`API Aliases`** (4KB) - TED API-Feldaliase
- **`List_of_search_fields.csv`** (90KB) - Vollständige Felddokumentation
- **`NUTS fields.txt`** (13KB) - NUTS-Code-Referenz
- **`Auswahlkriterien VGV-Verfahren_draft.docx`** (26KB) - Anforderungen
- **`Mindestkriterien.xlsx`** (12KB) - Kriterienkatalog

### Archivierte Dateien (in `archive/`)
- **`ted_search_ui.py`** (24KB) - Legacy Gradio-UI
- **Testdaten** - JSON/Excel Beispieldaten

## API-Integration

### TED API v3
- **Endpoint**: `https://api.ted.europa.eu/v3/notices/search`
- **Rate-Limits**: 5 req/sec (implementiert)
- **Paginierung**: Automatisch
- **Authentifizierung**: Keine (öffentlich)

### Abfragesyntax-Beispiel
```
RC="DE1" AND PD>=20250720 AND PD<=20250722 AND PC="45000000"
```

### Unterstützte Formate
- **PDF/JSON**: Deutsch (DEU), Englisch (ENG)
- **XML**: Mehrsprachig (MUL)

## Abhängigkeiten
```
streamlit>=1.28.0
requests>=2.31.0
pandas>=2.0.0
openpyxl>=3.1.0
```

## Projektstruktur
```bash
├── ted_search_ui_streamlit.py    # Hauptanwendung
├── ted_search_client.py          # API-Client
├── requirements.txt              # Abhängigkeiten
├── downloads/                    # Download-Ordner
├── docs/                        # Referenzdokumentation
└── archive/                     # Legacy-Dateien
```

## Features

- **Expert Search Interface** - Vereinfachte UI für komplexe TED-Abfragen
- **Bulk Download** - Massendownload mit intelligenter Ordnerstruktur
- **Two-Step Workflow** - Ergebnisvorschau vor Download
- **Rate Limiting** - Respektiert TED API-Limits
- **Progress Tracking** - Echtzeit-Fortschritt und Fehlerbehandlung
- **Smart Filtering** - 13 relevante Suchparameter
- **Multi-Format** - PDF/JSON in Deutsch/Englisch

## Dokumentation

- **TED API**: https://docs.ted.europa.eu/api/latest/
- **OpenAPI**: https://api.ted.europa.eu/api-v3.yaml
- **Suchsyntax**: https://docs.ted.europa.eu/api/latest/search.html
