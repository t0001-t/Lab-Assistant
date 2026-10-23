# Gel Annotator

Eigenständiger SDS-PAGE-Gel-Editor mit den Ladeoptimierungen des Lab Assistant.
Dieses Repository enthält ausschließlich den Gel-Annotator und seine benötigten
Module, Komponenten und Beispieldateien. Der vollständige Lab Assistant bleibt
in [Lab-Assistant-Complete](https://github.com/t0001-t/Lab-Assistant-Complete).

## Starten

Python 3.12 wird empfohlen.

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Bei Streamlit-Hosting: Repository `t0001-t/Lab-Assistant`, Branch `main`,
Startdatei **`app.py`**. Das gesamte Repository wird benötigt.

## Funktionen

Gelbilder importieren und zuschneiden, Perspektive korrigieren, Spuren und
Beschriftungen bearbeiten, Marker kalibrieren, Zielbanden markieren und mehrere
Gele kombinieren. Export als PNG, TIFF, PDF, CSV, JSON und ZIP.

## Geschwindigkeit

Exportbilder und Download-Dateien werden erst beim Öffnen des Export-Reiters
berechnet. Die Bearbeitungsreiter teilen identische Vorschaubilder. Bildqualität,
Originaldaten und Exportauflösung bleiben erhalten. Online-Ladezeiten hängen
zusätzlich vom Hosting ab.

## Tests

```sh
python -m unittest discover -s tests
```

Persönliche Bilder, gespeicherte Projekte und Zugangsdaten gehören nicht ins
Repository. Die bisherige Repository-Historie bleibt erhalten.
