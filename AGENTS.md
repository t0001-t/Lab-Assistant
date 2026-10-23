# Gel Annotator

Dieses Repository enthält nur den eigenständigen Gel-Editor. Einstieg: `app.py`.
Die vollständige Anwendung liegt separat in Lab-Assistant-Complete.

Originalbilder und Exportqualität nicht verändern. Koordinaten sind relativ.
UI-Texte über locales.py in Deutsch und Englisch pflegen. Caches bleiben pro
Streamlit-Session; keine persönlichen Bilder in gemeinsame persistente Caches
legen. Export nur bei `tab_export.open` berechnen. Die drei Bearbeitungsmodi
teilen identische Vorschauen. Keine projects/, Zugangsdaten oder lokale Daten
hochladen. Vor Änderungen Tests und Ruff ausführen.
