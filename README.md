# TED Ausschreibungs-Search-Client

Ein schlankes Python-Skript für anonyme Abfragen der TED-Search-API mit Ausgabe als JSON/Excel.

## Übersicht

Dieses Tool ermöglicht die Abfrage der Tenders Electronic Daily (TED) API, um öffentliche Ausschreibungen in der EU zu durchsuchen. Es unterstützt:

- Anonyme Abfragen (keine Authentifizierung erforderlich)
- API-Gesundheitsprüfung
- Paginierte Suche
- Export der Ergebnisse als Excel (.xlsx) oder JSON
- Parametrisierte Suchfunktion

## Voraussetzungen

- Python 3.12
- Pakete: requests, pandas, openpyxl

## Installation

```bash
# Virtuelle Umgebung erstellen und aktivieren
python -m venv venv

# Unter Windows
venv\Scripts\activate

# Unter Linux/Mac
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

## Verwendung

### Einfache Ausführung

```bash
python ted_search_client.py
```

Dies führt eine Beispielsuche nach "kassel" durch und exportiert die Ergebnisse als Excel und JSON.

### Als Modul verwenden

```python
import ted_search_client as tsc

# API-Gesundheitsprüfung
sdk_info = tsc.health_check()
print(f"SDK-Version: {sdk_info['latestSupported']}")

# Suche durchführen
results = tsc.ted_search(
    query="FT=\"berlin\" AND PC=[45000000 TO 45999999]",  # Bauaufträge in Berlin
    fields=["publicationNumber", "noticeTitle", "buyerName", "publicationDate"],
    limit=50,
    max_pages=3  # Maximal 3 Seiten abrufen
)

# Als Excel exportieren
excel_file = tsc.export_to_excel(results, "berlin_bau")
print(f"Excel-Export: {excel_file}")
```

## API-Dokumentation

- OpenAPI-Datei: [https://api.ted.europa.eu/api-v3.yaml](https://api.ted.europa.eu/api-v3.yaml)
- Entwicklerportal: [https://docs.ted.europa.eu/api/latest/index.html](https://docs.ted.europa.eu/api/latest/index.html)
- Suchdokumentation: [https://docs.ted.europa.eu/api/latest/search.html](https://docs.ted.europa.eu/api/latest/search.html)
