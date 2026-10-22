"""Zweisprachige Beschriftungen der Oberfläche (Deutsch / Englisch).

Alle sichtbaren Texte der App liegen hier zentral als ``key -> (de, en)``.
``t(key, lang)`` liefert den Text zur gewählten Sprache und fällt bei
fehlenden Einträgen auf Englisch bzw. den Schlüssel selbst zurück, damit
die Oberfläche nie mit leeren Labels bricht.
"""

from __future__ import annotations

LANGUAGES: dict[str, str] = {"de": "Deutsch", "en": "English"}
LANG_CODES: tuple[str, ...] = ("de", "en")
DEFAULT_LANG = "de"

#: key -> (deutsch, englisch)
STRINGS: dict[str, tuple[str, str]] = {
    # ------------------------------------------------------------------
    # Allgemein
    # ------------------------------------------------------------------
    "yes": ("Ja", "Yes"),
    "no": ("Nein", "No"),
    "none": ("Keine", "None"),
    "panel": ("Panel", "Panel"),
    "panels": ("Panels", "Panels"),
    "sample": ("Probe", "Sample"),
    "marker": ("Marker", "Marker"),
    "lane": ("Spur", "Lane"),
    "band": ("Bande", "Band"),
    "control": ("Kontrolle", "Control"),
    "unit": ("Einheit", "Unit"),
    "source": ("Quelle", "Source"),
    "visible": ("Sichtbar", "Visible"),
    "position": ("Position", "Position"),
    "delete": ("Löschen", "Delete"),
    "btn_load": ("Laden", "Load"),
    # ------------------------------------------------------------------
    # App-Kopf & Sidebar
    # ------------------------------------------------------------------
    "app_title": ("SDS-PAGE Abbildungs-Editor", "SDS-PAGE Figure Editor"),
    "app_subtitle": (
        "Gelbilder zuschneiden, Spuren beschriften, Marker kalibrieren, "
        "Zielbanden markieren und Abbildungen exportieren.",
        "Crop gel images, label lanes, calibrate markers, "
        "mark target bands and export figures.",
    ),
    "editor_options": ("Editor-Optionen", "Editor options"),
    "sb_language": ("Sprache", "Language"),
    "sb_theme": ("Farbschema (Abbildung)", "Color scheme (figure)"),
    "theme_light": ("Hell (weißer Rand)", "Light (white frame)"),
    "theme_dark": ("Dunkel (schwarzer Rand)", "Dark (black frame)"),
    "sb_ui_dark": ("Dunkelmodus", "Dark mode"),
    "sb_ui_dark_help": (
        "Dunkle Oberfläche der App. Das Farbschema der Abbildung bleibt davon unabhängig.",
        "Dark interface for the app. The figure's color scheme is independent of this.",
    ),
    "sb_project": ("Projekt", "Project"),
    "project_name": ("Projektname", "Project name"),
    "project_save": ("Projekt speichern", "Save project"),
    "project_saved": ("Projekt gespeichert: {name}", "Project saved: {name}"),
    "project_load": ("Projekt laden", "Load project"),
    "project_loaded": ("Projekt geladen: {name}", "Project loaded: {name}"),
    "project_delete": ("Projekt löschen", "Delete project"),
    "project_deleted": ("Projekt gelöscht: {name}", "Project deleted: {name}"),
    "project_none": ("Noch keine gespeicherten Projekte.", "No saved projects yet."),
    "project_download": ("Projekt als JSON", "Project as JSON"),
    "project_upload": ("Projekt-JSON laden", "Load project JSON"),
    "project_imported": ("Projekt aus Datei geladen.", "Project loaded from file."),
    "project_error": (
        "Projekt konnte nicht gelesen werden: {error}",
        "Project could not be read: {error}",
    ),
    "project_autosave": ("Automatisch speichern", "Autosave"),
    "project_persistence_hint": (
        "Projekte liegen als JSON inkl. eingebetteter Bilder in `projects/` "
        "und können jederzeit weiterbearbeitet werden.",
        "Projects are stored as JSON (including embedded images) in `projects/` "
        "and can be resumed at any time.",
    ),
    "sb_figure": ("Abbildung", "Figure"),
    "sb_typography": ("Typografie", "Typography"),
    "font_family": ("Schriftart", "Font family"),
    "font_scale": ("Schriftgröße", "Font size"),
    "label_rotation": ("Label-Drehung", "Label rotation"),
    "lane_numbers_position": ("Spurnummern", "Lane numbers"),
    "lane_numbers_help": (
        "Position der Spur-Nummern: unter dem Gel, darüber oder ganz aus.",
        "Position of the lane numbers: below the gel, above it, or off.",
    ),
    "unit_help": (
        "Einheit der Markerwerte, z. B. kDa, Da, bp, kb oder ng. kDa ist voreingestellt.",
        "Unit of the marker values, e.g. kDa, Da, bp, kb or ng. Default is kDa.",
    ),
    "ln_top": ("Oben", "Top"),
    "ln_bottom": ("Unten", "Bottom"),
    "lane_labels_bottom": ("Untere Labels 45°", "Bottom labels 45°"),
    "sb_export": ("Export", "Export"),
    "export_dpi": ("Auflösung", "Resolution"),
    "dpi_publication": ("300 DPI (Publikation)", "300 DPI (publication)"),
    "dpi_print": ("600 DPI (Druck)", "600 DPI (print)"),
    "dpi_preview": ("150 DPI (Vorschau)", "150 DPI (preview)"),
    "quality": ("Kantenglättung", "Anti-aliasing"),
    "quality_1": ("Standard (1×)", "Standard (1×)"),
    "quality_2": ("Hoch (2× Supersampling)", "High (2× supersampling)"),
    "quality_3": ("Maximal (3× Supersampling)", "Maximum (3× supersampling)"),
    "quality_help": (
        "Beschriftung wird höher aufgelöst gezeichnet und herunterskaliert. "
        "Das Gel selbst wird nie skaliert oder verändert.",
        "Labels are drawn at higher resolution and downscaled. The gel itself "
        "is never scaled or modified.",
    ),
    "sb_harmonization": ("Multi-Gel-Harmonisierung", "Multi-gel harmonization"),
    "harm_none": ("Keine", "None"),
    "harm_height": ("A · Gleiche Pixelhöhe", "A · Equal pixel height"),
    "harm_affine": ("B · Affin (2 Referenzbanden)", "B · Affine (2 reference bands)"),
    "harm_target_height": ("Zielhöhe (px)", "Target height (px)"),
    "harm_ref_top": ("Obere Referenz (kDa)", "Upper reference (kDa)"),
    "harm_ref_bottom": ("Untere Referenz (kDa)", "Lower reference (kDa)"),
    "harm_tip": (
        "Option A skaliert alle Gele auf dieselbe Pixelhöhe. Option B richtet "
        "zwei Referenzbanden (z. B. 100 & 10 kDa) vertikal aus.",
        "Option A scales all gels to the same pixel height. Option B aligns two "
        "reference bands (e.g. 100 & 10 kDa) vertically.",
    ),
    "sb_note": (
        "<b>Originalgel unberührt:</b> Spuren, Marker und Beschriftungen "
        "liegen ausschließlich im Canvas-Rahmen. Hilfslinien erscheinen nie im "
        "Export.",
        "<b>Original gel untouched:</b> lanes, markers and labels live only in "
        "the canvas frame. Guides never appear in the export.",
    ),
    # ------------------------------------------------------------------
    # Panel-Verwaltung
    # ------------------------------------------------------------------
    "panels_title": ("Gel-Panels", "Gel panels"),
    "panel_select": ("Aktives Panel", "Active panel"),
    "panel_letter": ("Panel-Buchstabe", "Panel letter"),
    "panel_name": ("Panel-Name", "Panel name"),
    "panel_add": ("＋ Panel", "＋ Panel"),
    "panel_duplicate": ("⧉ Duplizieren", "⧉ Duplicate"),
    "panel_delete": ("Panel löschen", "Delete panel"),
    "panel_last_keep": ("Das letzte Panel kann nicht gelöscht werden.", "The last panel cannot be deleted."),
    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------
    "tab_import": ("1 · Import & Geometrie", "1 · Import & geometry"),
    "tab_lanes": ("2 · Spuren & Labels", "2 · Lanes & labels"),
    "tab_markers": ("3 · Marker & Leiter", "3 · Markers & ladder"),
    "tab_targets": ("4 · Zielbanden", "4 · Target bands"),
    "tab_export": ("5 · Multi-Gel & Export", "5 · Multi-gel & export"),
    # ------------------------------------------------------------------
    # Tab 1 – Import & Geometrie
    # ------------------------------------------------------------------
    "import_title": ("Bild importieren", "Import image"),
    "import_upload": ("Gelbild (PNG, JPEG oder TIFF)", "Gel image (PNG, JPEG or TIFF)"),
    "import_upload_help": (
        "Drag & Drop oder Datei auswählen. TIFF wird als erstes Bild gelesen.",
        "Drag & drop or choose a file. TIFF is read as the first image.",
    ),
    "import_sample": ("Referenzgel laden", "Load reference gel"),
    "import_sample_hint": ("10 Spuren · Marker links · 9 Banden", "10 lanes · markers left · 9 bands"),
    "import_loaded": ("{name} geladen.", "{name} loaded."),
    "import_failed": ("Bild konnte nicht gelesen werden: {error}", "Image could not be read: {error}"),
    "import_none": ("Bitte ein Gelbild hochladen, um zu starten.", "Upload a gel image to start."),
    "crop_title": ("Zuschnitt", "Crop"),
    "crop_auto": ("Auto-Zuschnitt", "Auto crop"),
    "crop_full": ("↺ Volles Bild", "↺ Full image"),
    "crop_hint": (
        "Entfernt ungleichmäßige Ränder vor der Annotation. Der Zuschnitt "
        "betrifft nur das gelieferte Bild – nie die Beschriftung.",
        "Removes uneven borders before annotation. Cropping only affects the "
        "supplied image – never the labels.",
    ),
    "crop_preview": ("Zuschnitt-Vorschau", "Crop preview"),
    "preview_live_hint": (
        "Original, Ergebnis und Perspektive stehen links untereinander – rechts liegen "
        "alle Änderungen.",
        "Original, result and perspective are stacked on the left – all adjustments are "
        "on the right.",
    ),
    "crop_preview_caption": ("Rot = später sichtbarer Gelbereich", "Red = gel area visible later"),
    "crop_gel_size": ("Gelgröße", "Gel size"),
    "crop_aspect": ("Seitenverhältnis", "Aspect ratio"),
    "crop_min_warning": ("Der Zuschnitt ist sehr klein. Bitte die Werte prüfen.", "The crop is very small. Please check the values."),
    "persp_title": ("Perspektiven-Entzerrung", "Perspective correction"),
    "persp_hint": (
        "Vier Eckpunkte auf die Gel-Ecken ziehen. Der Trapez-Verzug wird via "
        "Perspektivtransformation begradigt.",
        "Drag the four corner points onto the gel corners. Trapezoidal distortion "
        "is straightened by a perspective transform.",
    ),
    "persp_reset": ("↺ Ecken zurücksetzen", "↺ Reset corners"),
    "transform_title": ("Transformation", "Transformation"),
    "rotate_cw": ("↻ 90° rechts", "↻ 90° CW"),
    "rotate_ccw": ("↺ 90° links", "↺ 90° CCW"),
    "flip_h": ("⇋ Horizontal spiegeln", "⇋ Flip horizontal"),
    "flip_v": ("⇅ Vertikal spiegeln", "⇅ Flip vertical"),
    "fine_rotation": ("Fein-Begradigung (°)", "Fine rotation (°)"),
    "transform_reset": ("↺ Transformation zurücksetzen", "↺ Reset transform"),
    "adjust_title": ("Bildanpassung (Live-Vorschau)", "Image adjustment (live preview)"),
    "brightness": ("Helligkeit", "Brightness"),
    "contrast": ("Kontrast", "Contrast"),
    "gamma": ("Gamma", "Gamma"),
    "invert": ("Invertieren (Weiß/Schwarz)", "Invert (white/black)"),
    "clahe": ("CLAHE (lokaler Kontrast)", "CLAHE (local contrast)"),
    "adjust_reset": ("↺ Anpassungen zurücksetzen", "↺ Reset adjustments"),
    "adjust_preview": ("Vorschau", "Preview"),
    "preview_original": ("Original", "Original"),
    "preview_processed": ("Verarbeitet", "Processed"),
    # ------------------------------------------------------------------
    # Tab 2 – Spuren & Labels
    # ------------------------------------------------------------------
    "lanes_title": ("Spuren definieren & Proben bezeichnen", "Define lanes & label samples"),
    "lanes_controls": ("Spuren & Labels", "Lanes & labels"),
    "lanes_hint": (
        "Vertikale Hilfslinien ziehen, einfügen oder löschen. Die Linien dienen "
        "nur der Platzierung und sind im Export unsichtbar.",
        "Drag, insert or delete vertical guides. Guides only aid placement and are "
        "invisible in the export.",
    ),
    "lanes_detect": ("Spuren schätzen", "Detect lanes"),
    "lanes_distribute": ("↔ Gleichmäßig verteilen", "↔ Distribute evenly"),
    "lanes_renumber": ("1…n zurücksetzen", "Reset to 1…n"),
    "lanes_add": ("＋ Spur hinzufügen", "＋ Add lane"),
    "lanes_add_help": (
        "Neue Spuren erhalten die nächste freie Nummer. '1…n zurücksetzen' "
        "nummeriert wieder von links nach rechts.",
        "New lanes get the next free number. 'Reset to 1…n' renumbers from left to right.",
    ),
    "lanes_delete": ("Ausgewählte Spur löschen", "Delete selected lane"),
    "lanes_count": ("Anzahl Spuren", "Number of lanes"),
    "lanes_count_help": (
        "Legt genau so viele Spuren an und verteilt sie gleichmäßig. Danach lassen "
        "sie sich im Editor frei verschieben.",
        "Creates exactly this many lanes, evenly distributed. Move them freely in the "
        "editor afterwards.",
    ),
    "lanes_count_set": ("{count} Spuren angelegt.", "{count} lanes created."),
    "count_apply": ("Anlegen", "Apply"),
    "lanes_selected": ("Ausgewählte Spur", "Selected lane"),
    "lanes_table_index": ("Spur", "Lane"),
    "lanes_table_sample": ("Probenbezeichnung", "Sample label"),
    "lanes_table_bottom": ("Unteres Label", "Bottom label"),
    "lanes_table_x": ("X-Position (%)", "X position (%)"),
    "lanes_role": ("Rolle", "Role"),
    "role_sample": ("Probe", "Sample"),
    "role_marker": ("Marker", "Marker"),
    "lanes_marker_lanes": ("Spur(en), die als Marker dienen", "Lane(s) serving as marker"),
    "lanes_marker_lanes_help": (
        "Typisch: erste und/oder letzte Spur. Die Skala wird unabhängig davon "
        "am Canvas-Rand platziert.",
        "Typically the first and/or last lane. The scale is placed at the canvas "
        "edge independently of this.",
    ),
    "lanes_editor_hint": (
        "**Bedienung:** Linie ziehen = verschieben · Klick auf freie Fläche = Spur "
        "einfügen · Doppelklick = Spur löschen · Klick auf Linie = auswählen.",
        "**Usage:** drag a line to move · click empty area to insert a lane · "
        "double-click to delete · click a line to select.",
    ),
    "lanes_markup_hint": (
        "Text markieren und x² (hoch) oder x₂ (tief) anklicken. Normal setzt die Formatierung zurück. Mit Übernehmen speichern.",
        "Select text and click x² (superscript) or x₂ (subscript). Normal clears formatting. Click Apply to save.",
    ),
    "editor_side": ("Bedienfeld-Seite", "Controls side"),
    "group_title": ("Gruppenüberschriften", "Group headings"),
    "group_add": ("＋ Gruppe", "＋ Group"),
    "group_text": ("Text", "Text"),
    "group_from": ("Von Spur", "From lane"),
    "group_to": ("Bis Spur", "To lane"),
    "group_underline": ("Trennlinie", "Underline"),
    "group_delete": ("Gruppe löschen", "Delete group"),
    "group_none": ("Noch keine Gruppen.", "No groups yet."),
    "cond_title": ("Bedingungs-Matrix", "Condition matrix"),
    "cond_add": ("＋ Bedingung", "＋ Condition"),
    "cond_name": ("Bedingung", "Condition"),
    "cond_hint": (
        "Eine Zeile pro Versuchsbedingung. Werte je Spur (z. B. `+`, `–`, `10 µM`). "
        "Wird über den Spuren zentriert dargestellt.",
        "One row per experimental condition. Values per lane (e.g. `+`, `–`, `10 µM`), "
        "centred above the lanes.",
    ),
    "cond_values_hint": ("Werte je Spur (kommagetrennt oder Leerzeichen)", "Values per lane (comma- or space-separated)"),
    "cond_delete": ("Bedingung löschen", "Delete condition"),
    "cond_none": ("Noch keine Bedingungen.", "No conditions yet."),
    "lanes_detected": ("{peaks} Banden-Peaks erkannt · Raster neu gesetzt.", "{peaks} band peaks detected · grid reset."),
    "lanes_none_remaining": ("Mindestens eine Spur muss erhalten bleiben.", "At least one lane must remain."),
    # ------------------------------------------------------------------
    # Tab 3 – Marker & Leiter
    # ------------------------------------------------------------------
    "markers_title": ("Molekulargewichts-Leiter kalibrieren", "Calibrate molecular weight ladder"),
    "markers_detect_left": ("Linke Leiter erkennen", "Detect left ladder"),
    "markers_detect_right": ("Rechte Leiter erkennen", "Detect right ladder"),
    "markers_reset": ("↺ Referenzwerte", "↺ Reference values"),
    "markers_count": ("Anzahl Marker", "Number of markers"),
    "markers_count_help": (
        "Legt genau so viele Marker an und verteilt sie gleichmäßig über die Leiter. "
        "Werte und Positionen lassen sich anschließend einzeln anpassen.",
        "Creates exactly this many markers, evenly spaced along the ladder. Adjust "
        "values and positions individually afterwards.",
    ),
    "markers_count_set": ("{count} Marker angelegt.", "{count} markers created."),
    "markers_editor_hint": (
        "**Bedienung:** horizontale Linie ziehen = Bande verschieben · Klick auf "
        "freie Fläche = Bande anlegen · Doppelklick = Bande entfernen.",
        "**Usage:** drag a horizontal line to move a band · click empty area to add "
        "a band · double-click to remove.",
    ),
    "markers_selected": ("Ausgewählte Bande", "Selected band"),
    "markers_y": ("Y-Position (% der Gelhöhe)", "Y position (% of gel height)"),
    "markers_value": ("Wert ({unit})", "Value ({unit})"),
    "markers_add": ("＋ Bande hinzufügen", "＋ Add band"),
    "markers_delete": ("Bande entfernen", "Remove band"),
    "markers_table_no": ("Nr.", "No."),
    "markers_table_kda": ("kDa", "kDa"),
    "markers_table_y": ("Y (%)", "Y (%)"),
    "markers_table_visible": ("Sichtbar", "Visible"),
    "markers_none": ("Noch keine Marker vorhanden.", "No markers yet."),
    "markers_detected_left": ("{count} Banden links erkannt.", "{count} bands detected on the left."),
    "markers_detected_right": ("{count} Banden rechts erkannt.", "{count} bands detected on the right."),
    "markers_too_few": ("Zu wenige Banden erkannt – bitte manuell justieren.", "Too few bands detected – adjust manually."),
    "markers_added": ("Bande {value} kDa angelegt.", "Band {value} kDa added."),
    "markers_removed": ("Bande entfernt.", "Band removed."),
    "markers_ladder_side": ("Leiter-Skala", "Ladder scale"),
    "ladder_left": ("Links", "Left"),
    "ladder_right": ("Rechts", "Right"),
    "ladder_both": ("Beidseitig", "Both sides"),
    # ------------------------------------------------------------------
    # Tab 4 – Zielbanden
    # ------------------------------------------------------------------
    "targets": ("Zielbanden", "Targets"),
    "targets_title": ("Zielbanden annotieren", "Annotate target bands"),
    "targets_hint": (
        "Pfeile docken an der Gelkante an und laufen in den Außenrand – exakt auf "
        "Bandenhöhe. Text frei wählbar (z. B. „37 kDa“ oder „GFP-Fusion“).",
        "Arrows dock at the gel edge and run into the outer margin – exactly at band "
        "height. Free text label (e.g. \u201c37 kDa\u201d or \u201cGFP fusion\u201d).",
    ),
    "targets_editor_hint": (
        "**Bedienung:** Pfeilgriff im Rand ziehen = Höhe ändern · Klick in den Rand "
        "= neuen Pfeil anlegen · Doppelklick = Pfeil löschen.",
        "**Usage:** drag the handle in the margin to change height · click the margin "
        "to add an arrow · double-click to delete.",
    ),
    "targets_add": ("＋ Pfeil hinzufügen", "＋ Add arrow"),
    "targets_selected": ("Ausgewählter Pfeil", "Selected arrow"),
    "targets_label": ("Beschriftung", "Label"),
    "targets_y": ("Y-Position (% der Gelhöhe)", "Y position (% of gel height)"),
    "targets_side": ("Seite", "Side"),
    "side_left": ("Links", "Left"),
    "side_right": ("Rechts", "Right"),
    "targets_delete": ("Pfeil löschen", "Delete arrow"),
    "targets_none": ("Noch keine Zielbanden definiert.", "No target bands defined yet."),
    "targets_table_no": ("Nr.", "No."),
    "targets_table_label": ("Beschriftung", "Label"),
    "targets_table_y": ("Y (%)", "Y (%)"),
    "targets_table_side": ("Seite", "Side"),
    "targets_scale_conflict": (
        "Zielpfeile und kDa-Skala belegen denselben Rand. Die Skala wird für die "
        "betroffene Seite ausgeblendet – bitte die Pfeile auf die andere Seite legen, "
        "falls die Skala benötigt wird.",
        "Target arrows and the kDa scale share the same margin. The scale is hidden on "
        "the affected side – move the arrows to the other side if the scale is needed.",
    ),
    "targets_added": ("Zielbande angelegt.", "Target band added."),
    "targets_removed": ("Zielbande entfernt.", "Target band removed."),
    "targets_guess_mw": ("MW schätzen", "Estimate MW"),
    # ------------------------------------------------------------------
    # Tab 5 – Export
    # ------------------------------------------------------------------
    "export_title": ("Publikations-Export", "Publication export"),
    "export_single": ("Einzelnes Panel", "Single panel"),
    "export_combined": ("Kombinierte Figur (alle Panels)", "Combined figure (all panels)"),
    "export_preview": ("Vorschau", "Preview"),
    "export_png": ("PNG herunterladen", "Download PNG"),
    "export_tiff": ("TIFF herunterladen", "Download TIFF"),
    "export_pdf": ("PDF herunterladen", "Download PDF"),
    "export_csv": ("Metadaten-CSV", "Metadata CSV"),
    "export_json": ("Metadaten-JSON", "Metadata JSON"),
    "export_zip": ("Alles als ZIP", "Everything as ZIP"),
    "export_working_view": ("Arbeitsansicht (mit Hilfslinien)", "Working view (with guides)"),
    "export_working_help": (
        "Nur zur Kontrolle – Hilfslinien sind im Publikations-Export unsichtbar.",
        "For checking only – guides are invisible in the publication export.",
    ),
    "export_canvas_info": (
        "Canvas: {cw} × {ch} px · Header {hh} px · linker Rand {lm} px · rechter Rand {rm} px",
        "Canvas: {cw} × {ch} px · header {hh} px · left margin {lm} px · right margin {rm} px",
    ),
    "export_success": (
        "**Publikations-Check:** Das Gel ist pixelgenau unverändert (keine Linien, "
        "Boxen oder Schriften im Bildbereich), Beschriftungen liegen ausschließlich "
        "im Canvas-Rahmen, und der Export enthält keine Hilfslinien.",
        "**Publication check:** the gel is pixel-identical (no lines, boxes or text "
        "inside the image area), labels live only in the canvas frame, and the export "
        "contains no guides.",
    ),
    "export_no_source": ("Kein Bild geladen.", "No image loaded."),
    "export_metadata_title": ("Metadaten", "Metadata"),
    "export_lanes_title": ("Spurenzuordnung", "Lane assignment"),
    "export_markers_title": ("Leiterkalibrierung", "Ladder calibration"),
    "export_targets_title": ("Zielbanden", "Target bands"),
    "export_panel_status": ("{letter} · {w}×{h} px", "{letter} · {w}×{h} px"),
    # ------------------------------------------------------------------
    # Metadaten-Spalten
    # ------------------------------------------------------------------
    "meta_panel": ("Panel", "Panel"),
    "meta_letter": ("Buchstabe", "Letter"),
    "meta_lane_index": ("spur_index", "lane_index"),
    "meta_sample": ("probenbezeichnung", "sample_label"),
    "meta_x_rel": ("x_position_rel", "x_position_rel"),
    "meta_role": ("spurrolle", "lane_role"),
    "meta_marker_kda": ("marker_kda", "marker_kda"),
    "meta_bottom_label": ("unteres_label", "bottom_label"),
    "meta_marker_index": ("marker_index", "marker_index"),
    "meta_kda": ("kda", "kda"),
    "meta_y_pct": ("y_position_pct", "y_position_pct"),
    "meta_y_px": ("y_position_px", "y_position_px"),
    "meta_y_rel": ("y_position_rel", "y_position_rel"),
    "meta_visible": ("sichtbar", "visible"),
    "meta_target_index": ("ziel_index", "target_index"),
    "meta_target_label": ("zielbezeichnung", "target_label"),
    "meta_side": ("seite", "side"),
    "meta_condition": ("bedingung", "condition"),
    "meta_values": ("werte", "values"),
    "meta_group": ("gruppe", "group"),
    "meta_group_from": ("von_spur", "from_lane"),
    "meta_group_to": ("bis_spur", "to_lane"),
    # ------------------------------------------------------------------
    # Statusmeldungen
    # ------------------------------------------------------------------
    "msg_lane_inserted": ("Spur {index} eingefügt.", "Lane {index} inserted."),
    "msg_lane_deleted": ("Spur gelöscht.", "Lane deleted."),
    "msg_marker_added": ("Bande {value} kDa angelegt.", "Band {value} kDa added."),
    "msg_marker_removed": ("Bande entfernt.", "Band removed."),
    "msg_arrow_added": ("Zielbande angelegt.", "Target band added."),
    "msg_arrow_removed": ("Zielbande entfernt.", "Target band removed."),
}


# Tutorial, demo and quick help
STRINGS.update({'onboard_start': ('Tutorial starten', 'Start Tour'),
 'onboard_demo': ('Beispiel-Gel laden', 'Load Sample Gel'),
 'onboard_help': ('? Schnellhilfe', '? Quick help'),
 'onboard_welcome_title': ('Willkommen in GelDoc Studio', 'Welcome to GelDoc Studio'),
 'onboard_welcome': ('Lerne die fünf Arbeitsschritte mit deinem Gel oder einem vorbereiteten Beispiel '
                     'kennen. Die Tour ist freiwillig und lässt sich jederzeit beenden.',
                     'Explore the five workflow steps with your gel or a prepared example. The tour is '
                     'optional and you can leave at any time.'),
 'onboard_demo_tour': ('Demo laden und Tour starten', 'Load demo and start tour'),
 'onboard_later': ('Später', 'Later'),
 'onboard_back': ('Zurück', 'Back'),
 'onboard_next': ('Weiter', 'Next'),
 'onboard_finish': ('Tour abschließen', 'Finish tour'),
 'onboard_close': ('Tour beenden', 'End tour'),
 'onboard_dismiss': ('Schließen', 'Close'),
 'onboard_step': ('Schritt {step} von 5', 'Step {step} of 5'),
 'onboard_task': ('Zum Ausprobieren', 'Try it'),
 'onboard_confirm_title': ('Aktuelles Projekt ersetzen?', 'Replace current project?'),
 'onboard_confirm': ('Das Demo-Projekt ersetzt das aktuelle Projekt. Nicht gespeicherte Änderungen gehen '
                     'dabei verloren. Speichere dein Projekt bei Bedarf zuerst über „Projekt als JSON“ in '
                     'der Seitenleiste.',
                     'The demo replaces your current project. Unsaved changes will be lost. If needed, save '
                     'your project using “Download project JSON” in the sidebar first.'),
 'onboard_cancel': ('Abbrechen', 'Cancel'),
 'onboard_loading': ('Demo wird geladen …', 'Loading demo …'),
 'onboard_storage': ('Die Hilfe-Einstellungen konnten in diesem Browser nicht gespeichert werden. Die '
                     'Anwendung bleibt nutzbar; die Einführung kann beim nächsten Besuch erneut erscheinen.',
                     'Help preferences could not be saved in this browser. You can still use the app; the '
                     'introduction may appear on your next visit.'),
 'onboard_missing': ('Dieser Bereich ist noch nicht verfügbar. Lade zuerst ein Bild oder das Demo-Projekt. '
                     'Du kannst trotzdem weitergehen.',
                     'This section is not available yet. Load an image or the demo project first. You can '
                     'still continue the tour.'),
 'onboard_fallback': ('Die Hervorhebung ist in dieser Browserumgebung nicht verfügbar. Öffne den unten '
                      'genannten Reiter; die Tour funktioniert weiterhin als Anleitung.',
                      'Highlighting is unavailable in this browser environment. Open the tab named below; '
                      'the tour remains available as a guide.'),
 'onboard_demo_note': ('Demonstrationsdaten zum Ausprobieren. Beschriftungen und Bedingungen sind Beispiele, '
                       'keine experimentell validierten Messwerte.',
                       'Demonstration data for practice. Labels and conditions are examples, not '
                       'experimentally validated measurements.'),
 'onboard_demo_error': ('Das Demo-Projekt konnte nicht geladen werden. Das bisherige Projekt bleibt '
                        'erhalten.',
                        'The demo project could not be loaded. Your previous project is preserved.'),
 'onboard_complete': ('Tour abgeschlossen. Du kannst sie jederzeit erneut starten.',
                      'Tour completed. You can restart it at any time.'),
 'onboard_title_1': ('Bild laden und Geometrie', 'Load image and geometry'),
 'onboard_body_1': ('Lade PNG, JPEG oder TIFF per Drag & Drop oder über die Dateiauswahl. Bei schräg '
                    'fotografierten Gelen verschiebst du die vier Eckpunkte im Perspektiven-Editor. Der '
                    'Zuschnitt begrenzt den relevanten Bildausschnitt.',
                    'Upload PNG, JPEG or TIFF by dragging a file or using the file picker. For tilted '
                    'photographs, move the four corners in the perspective editor. Crop selects the relevant '
                    'image region.'),
 'onboard_task_1': ('Lade ein Bild oder das Beispiel-Gel und prüfe die vier Ecken sowie den Zuschnitt.',
                    'Load an image or sample gel and check the four corners and crop.'),
 'onboard_title_2': ('Spuren festlegen', 'Define lanes'),
 'onboard_body_2': ('Richte die vertikalen Hilfslinien an den Spuren beziehungsweise Wells aus. Ziehen '
                    'verschiebt eine Linie, ein Klick auf freie Fläche fügt eine Spur hinzu und ein '
                    'Doppelklick auf eine Linie löscht sie. „Spuren schätzen“ und „Gleichmäßig verteilen“ '
                    'helfen bei der ersten Anordnung.',
                    'Align vertical guides with lanes or wells. Drag to move a guide, click an empty area to '
                    'add a lane, and double-click a guide to delete it. Lane estimation and even spacing '
                    'help create an initial layout.'),
 'onboard_task_2': ('Wähle eine Spur und verändere ihre Position. Kontrolliere die Ausrichtung am Gel.',
                    'Select a lane and move it. Check its alignment with the gel.'),
 'onboard_title_3': ('Marker und Zielbanden', 'Markers and target bands'),
 'onboard_body_3': ('Ordne horizontale Markerlinien den bekannten Banden der Proteinleiter zu und prüfe '
                    'Molekulargewichte sowie Positionen. Die Leiter kann links, rechts oder beidseitig '
                    'dargestellt werden. Im Reiter Zielbanden setzt du mit einem Klick in den Außenrand '
                    'einen Pfeil und bearbeitest seine Beschriftung.',
                    'Match horizontal guides to known ladder bands and verify molecular weights and '
                    'positions. Display the ladder on the left, right or both sides. In Target bands, click '
                    'the outer margin to add an arrow and edit its label.'),
 'onboard_task_3': ('Prüfe eine Markerposition. Öffne anschließend „Zielbanden“ und verschiebe einen Pfeil.',
                    'Check a marker position, then open Target bands and move an arrow.'),
 'onboard_title_4': ('Beschriftungen und Bedingungen', 'Labels and conditions'),
 'onboard_body_4': ('Bearbeite die Probenbezeichnung direkt in der Tabelle: Text markieren, x² oder x₂ '
                    'anklicken und „Übernehmen“ wählen. Die Label-Drehung in der Seitenleiste bietet 0°, 45° '
                    'und 90°. Gruppenbalken und Plus/Minus-Zeilen beschreiben zusammengehörige Spuren und '
                    'Versuchsbedingungen.',
                    'Edit sample names in the table: select text, click x² or x₂, then Apply. Label rotation '
                    'in the sidebar offers 0°, 45° and 90°. Group bars and plus/minus rows describe related '
                    'lanes and experimental conditions.'),
 'onboard_task_4': ('Formatiere einen Teil einer Probenbezeichnung und ändere einen Matrixwert. Übernimm die '
                    'Texteingaben vor weiteren Projektänderungen.',
                    'Format part of a sample name and change a matrix value. Apply text edits before making '
                    'other project changes.'),
 'onboard_title_5': ('Prüfung und Export', 'Review and export'),
 'onboard_body_5': ('Prüfe die Vorschau auf lesbare Beschriftungen und Überlappungen. Hilfslinien fehlen im '
                    'finalen Export; die Quelldatei bleibt erhalten, gewählte Bildanpassungen fließen aber '
                    'in die Darstellung ein. PNG, PDF und TIFF unterstützen 300 DPI; eine höhere '
                    'DPI-Einstellung allein erzeugt keine zusätzlichen Bilddetails.',
                    'Check the preview for readable labels and overlaps. Editing guides are excluded from '
                    'final exports; the source file is preserved, while selected image adjustments affect '
                    'the exported view. PNG, PDF and TIFF support 300 DPI; a higher DPI setting alone does '
                    'not add image detail.'),
 'onboard_task_5': ('Prüfe Vorschau und Auflösung. Wähle bei Bedarf selbst ein Exportformat; die Tour '
                    'startet keinen Download.',
                    'Check the preview and resolution. Choose an export format if needed; the tour does not '
                    'trigger downloads.'),
 'onboard_target_upload': ('Bild-Upload', 'Image upload'),
 'onboard_target_corners': ('Vier Eckpunkte', 'Four corners'),
 'onboard_target_crop': ('Zuschnitt', 'Crop'),
 'onboard_target_lanes': ('Spuren-Editor', 'Lane editor'),
 'onboard_target_markers': ('Marker & Leiter', 'Markers & ladder'),
 'onboard_target_arrows': ('Zielbanden', 'Target bands'),
 'onboard_target_labels': ('Probenbezeichnung', 'Sample names'),
 'onboard_target_groups': ('Gruppenbalken', 'Group bars'),
 'onboard_target_matrix': ('Bedingungsmatrix', 'Condition matrix'),
 'onboard_target_rotation': ('Label-Drehung', 'Label rotation'),
 'onboard_target_export': ('Vorschau & Export', 'Preview & export'),
 'onboard_help_title': ('Schnellhilfe', 'Quick help'),
 'onboard_help_mouse_title': ('Mausgesten', 'Mouse gestures'),
 'onboard_help_mouse': ('Im jeweiligen Gel-Editor: Linie oder Pfeil anklicken zum Auswählen, ziehen zum '
                        'Verschieben, doppelklicken zum Löschen. Ein Klick auf freie Gel-Fläche ergänzt eine '
                        'Spur oder einen Marker; Zielpfeile entstehen durch Klick in den linken oder rechten '
                        'Außenrand. Die vier Perspektivpunkte werden gezogen. Rechtsklick ist keine '
                        'Löschfunktion.',
                        'In the relevant gel editor: click a guide or arrow to select, drag to move, '
                        'double-click to delete. Click empty gel space to add a lane or marker; click the '
                        'left or right outer margin to add a target arrow. Drag the four perspective '
                        'handles. Right-click does not delete.'),
 'onboard_help_keys_title': ('Tastatur', 'Keyboard'),
 'onboard_help_keys': ('Tab / Umschalt+Tab: Bedienelemente wechseln. Eingabe oder Leertaste: fokussierte '
                       'Schaltflächen auslösen. Escape: dieses Hilfefenster oder die Tour schließen. In '
                       'Textfeldern gelten die üblichen Browserkürzel für Kopieren, Einfügen und Auswählen '
                       '(Strg unter Windows/Linux, ⌘ unter macOS). Es gibt keine globalen App-Kürzel zum '
                       'Löschen oder Verschieben von Gel-Linien. Nutze dafür die Positionsfelder und '
                       'Schaltflächen.',
                       'Tab / Shift+Tab: move between controls. Enter or Space: activate focused buttons. '
                       'Escape: close this help window or the tour. Text fields support standard browser '
                       'copy, paste and selection shortcuts (Ctrl on Windows/Linux, ⌘ on macOS). There are '
                       'no global app shortcuts to delete or move gel guides. Use position fields and '
                       'buttons instead.'),
 'onboard_help_labels_title': ('Beschriftung und Lesbarkeit', 'Labels and readability'),
 'onboard_help_labels': ('Text in der Probenbezeichnung markieren, x² oder x₂ wählen, dann Übernehmen. '
                         '„Normal“ entfernt die Formatierung. Vermeide Überlappungen durch kürzere Texte, '
                         'kleinere Schrift oder 45°/90°-Drehung. Gruppen reichen von einer Startspur bis zu '
                         'einer Endspur; eine verschachtelte Gruppenhierarchie steht nicht als eigene '
                         'Bearbeitungsfunktion bereit.',
                         'Select text in a sample name, choose x² or x₂, then Apply. Normal removes '
                         'formatting. Reduce overlaps with shorter labels, smaller fonts or 45°/90° '
                         'rotation. Groups span a start and end lane; nested group hierarchies are not a '
                         'separate editing feature.'),
 'onboard_help_color_title': ('Farben und Export', 'Colors and export'),
 'onboard_help_color': ('„Dunkelmodus“ verändert die Bedienoberfläche. „Farbschema (Abbildung)“ steuert die '
                        'exportierte Abbildung unabhängig davon. Prüfe vor dem Download die finale Vorschau; '
                        'Arbeitsansichten können Hilfslinien enthalten.',
                        'Dark mode changes the interface. Figure color scheme controls the exported figure '
                        'independently. Check the final preview before downloading; working views may '
                        'include guides.'),
 'onboard_help_save_title': ('Speichern und Hilfe-Einstellungen', 'Saving and help preferences'),
 'onboard_help_save': ('Speichere das Projekt als JSON für die spätere Weiterbearbeitung, möglichst mit '
                       'eingebetteten Bildern. PNG, PDF und TIFF sind Abbildungsexporte. Einführung und '
                       'Tourabschluss werden getrennt vom Projekt in diesem Browser für diese App-Adresse '
                       'gespeichert; ein anderer Browser oder Port hat eigene Einstellungen. '
                       'Demo-Standardtexte wechseln während der aktuellen Demo-Sitzung die Sprache; eigene '
                       'Änderungen bleiben erhalten. Nach dem Laden einer gespeicherten JSON-Datei werden '
                       'Beschriftungen wie eigene Projektdaten behandelt.',
                       'Save a project as JSON for future editing, preferably with embedded images. PNG, PDF '
                       'and TIFF are figure exports. Introduction and tour completion preferences are stored '
                       'separately from projects in this browser for this app address; other browsers or '
                       'ports have separate settings. Demo default labels change language during the current '
                       'demo session; custom edits are preserved. After loading a saved JSON file, labels '
                       'are treated as personal project data.'),
 'demo_name': ('GelDoc Demo', 'GelDoc Demo'),
 'demo_panel': ('Beispielgel', 'Sample gel'),
 'demo_ladder': ('Leiter', 'Ladder'),
 'demo_control': ('Kontrolle', 'Control'),
 'demo_sample': ('Probe {n}', 'Sample {n}'),
 'demo_condition_0': ('Induktion', 'Induction'),
 'demo_condition_1': ('Behandlung', 'Treatment'),
 'demo_group_0': ('Serie A', 'Series A'),
 'demo_group_1': ('Serie B', 'Series B'),
 'demo_target': ('Zielprotein', 'Target protein')})

def t(key: str, lang: str = DEFAULT_LANG, **kwargs: object) -> str:
    """Übersetzt ``key`` in die Sprache ``lang`` (Fallback: en → key)."""
    pair = STRINGS.get(key)
    if pair is None:
        return key
    index = 0 if lang == "de" else 1
    text = pair[index] or pair[1] or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def translator(lang: str):
    """Liefert eine an ``lang`` gebundene Übersetzungsfunktion ``_(key, **kw)``."""

    def _(key: str, **kwargs: object) -> str:
        return t(key, lang, **kwargs)

    return _


def missing_keys(*keys: str) -> list[str]:
    """Hilfsfunktion für Tests: Schlüssel, die im Wörterbuch fehlen."""
    return [key for key in keys if key not in STRINGS]
