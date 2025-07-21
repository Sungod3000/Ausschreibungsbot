# TED Expert-Search UI

Eine moderne Streamlit-basierte Benutzeroberfläche für erweiterte Abfragen der TED (Tenders Electronic Daily) API mit intelligenter Ergebnisvorschau und Bulk-Download-Funktionalität.

## 🎯 Projektbeschreibung

Die TED Expert-Search UI ist eine benutzerfreundliche Frontend-Anwendung, die es ermöglicht, komplexe Suchanfragen gegen die TED API zu erstellen, auszuführen und die Ergebnisse in verschiedenen Formaten herunterzuladen. Die Anwendung bietet eine zweistufige Workflow:

1. **Ergebnisvorschau**: Zeigt die Anzahl der gefundenen Ausschreibungen an
2. **Bulk-Download**: Lädt alle Ergebnisse in den gewählten Formaten (PDF, JSON) in organisierte Ordner herunter

### ✨ Hauptfunktionen

- **Vereinfachte Suchoberfläche**: 13 wesentliche Suchfelder mit Tooltips und Dropdown-Optionen
- **Expert Search Syntax**: Nutzt die offizielle TED API Expert Search Syntax
- **Intelligente Ergebniszählung**: Präzise Zählung über alle Seiten hinweg
- **Bulk-Download**: Automatischer Download aller Ergebnisse in gewählten Formaten
- **Organisierte Ordnerstruktur**: Ordner werden nach Suchparametern und Zeitstempel benannt
- **Mehrsprachige Downloads**: PDF und JSON in Deutsch und Englisch
- **Echtzeit-Fortschrittsanzeige**: Live-Updates während des Download-Prozesses

## 🔍 Suchfelder und TED API Aliases

Die Anwendung bietet 13 speziell ausgewählte Suchfelder, die die wichtigsten Aspekte öffentlicher Ausschreibungen abdecken:

### **1. Freitext-Suche**
- **Alias**: `FT`
- **Beschreibung**: Volltextsuche in allen Feldern der Ausschreibung
- **Beispiel**: `"Krankenhaus" OR "Hospital"`
- **Verwendung**: Allgemeine Stichwortsuche

### **2. Ort der Leistungserbringung (Place of Performance)**
- **Alias**: `RC`
- **Beschreibung**: NUTS-Code für den Ort, wo der Auftrag ausgeführt wird
- **Beispiel**: `"DE1"` (Baden-Württemberg)
- **Dropdown**: Deutsche Bundesländer (DE1-DEG)
- **Hinweis**: Unterscheidet sich vom Standort des Auftraggebers

### **3. Geschäftsbereich (CPV-Code)**
- **Alias**: `classification-cpv`
- **Beschreibung**: Common Procurement Vocabulary - Klassifizierung der Leistung
- **Beispiel**: `"45000000"` (Bauarbeiten)
- **Verwendung**: Spezifische Branchen- oder Leistungssuche

### **4. Art des Auftrags**
- **Alias**: `contract-type`
- **Beschreibung**: Grundtyp des Auftrags
- **Optionen**: 
  - `works` (Bauleistungen)
  - `supplies` (Lieferungen)
  - `services` (Dienstleistungen)

### **5. Auftragswert (Min/Max)**
- **Aliases**: `value_min`, `value_max`
- **Beschreibung**: Geschätzter oder tatsächlicher Auftragswert in Euro
- **Verwendung**: Filterung nach Auftragsgröße

### **6. Veröffentlichungsdatum (Von/Bis)**
- **Alias**: `publication-date`
- **Format**: `PD>=YYYYMMDD AND PD<=YYYYMMDD`
- **Standard**: Letzten 30 Tage
- **Beschreibung**: Zeitraum der Veröffentlichung in TED

### **7. Einreichungsfrist (Von/Bis)**
- **Alias**: `deadline-date`
- **Format**: `DD>=YYYYMMDD AND DD<=YYYYMMDD`
- **Beschreibung**: Frist für die Angebotsabgabe

### **8. Name des Auftraggebers**
- **Alias**: `buyer-name`
- **Beschreibung**: Name der ausschreibenden Behörde/Organisation
- **Beispiel**: `"Stadt Kassel"`

### **9. Ort des Auftraggebers**
- **Alias**: `buyer-town`
- **Beschreibung**: Stadt/Gemeinde des Auftraggebers
- **Hinweis**: Unterscheidet sich vom Leistungsort (RC)

### **10. Land des Auftraggebers**
- **Alias**: `buyer-country`
- **Beschreibung**: Land der ausschreibenden Behörde
- **Format**: ISO-Ländercodes (z.B. "DE", "FR")

### **11. Art des Auftraggebers**
- **Alias**: `buyer-type`
- **Beschreibung**: Kategorie der ausschreibenden Organisation
- **Optionen**: Öffentliche Behörden, Versorgungsunternehmen, etc.

### **12. Haupttätigkeit**
- **Alias**: `authority-main-activity`
- **Beschreibung**: Haupttätigkeitsbereich der ausschreibenden Behörde
- **Optionen**: 
  - `health` (Gesundheitswesen)
  - `education` (Bildung)
  - `defence` (Verteidigung)
  - `water` (Wasserversorgung)
  - `electricity` (Stromversorgung)
  - Und weitere...

### **13. Art der Bekanntmachung**
- **Alias**: `notice-type`
- **Beschreibung**: Typ der Ausschreibung
- **Optionen**:
  - `cn-standard` (Auftragsbekanntmachung)
  - `can-standard` (Bekanntmachung vergebener Aufträge)
  - `pin-standard` (Vorinformation)

## 🛠️ Technische Voraussetzungen

- **Python**: 3.8+
- **Hauptabhängigkeiten**: Streamlit, Requests, Pandas
- **TED API**: Öffentlich zugänglich, keine Authentifizierung erforderlich

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
