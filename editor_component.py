"""Anbindung des interaktiven HTML-Canvas-Editors an Streamlit.

Der Editor zeigt die gerenderte Abbildung (oder das Quellbild für die
Perspektiv-Ecken) und erlaubt das direkte Ziehen von Spuren, Markern,
Zielbanden-Pfeilen und Eckpunkten. Die Rückgabe ist ein JSON-Dictionary,
das :func:`workflow.apply_editor_event` verarbeitet.
"""

from __future__ import annotations

import base64
import hashlib
import io
from pathlib import Path
from typing import Any

import streamlit.components.v1 as components
from PIL import Image

from canvas_renderer import Layout
from models import GelPanel

_COMPONENT_DIR = Path(__file__).parent / "components" / "gel_editor"
_gel_editor = components.declare_component("gel_editor", path=str(_COMPONENT_DIR))

MAX_EDITOR_WIDTH = 1000
_DATA_URL_CACHE: dict[str, str] = {}
_DATA_URL_CACHE_LIMIT = 12


def _data_url(image: Image.Image) -> tuple[str, float]:
    """Kodiert die Abbildung als PNG und liefert den Skalierungsfaktor.

    Das Ergebnis wird über einen Bild-Hash zwischengespeichert: sonst würde
    bei jedem Rerun dieselbe Vorschau erneut kodiert (der teuerste Schritt).
    """
    rgb = image.convert("RGB")
    cache_key = hashlib.sha1(f"{rgb.size}".encode("ascii") + rgb.tobytes()).hexdigest()
    cached = _DATA_URL_CACHE.get(cache_key)
    if cached is not None:
        return cached, min(1.0, MAX_EDITOR_WIDTH / image.width)

    factor = min(1.0, MAX_EDITOR_WIDTH / image.width)
    if factor < 1.0:
        display = rgb.resize(
            (max(1, round(rgb.width * factor)), max(1, round(rgb.height * factor))),
            Image.Resampling.LANCZOS,
        )
    else:
        display = rgb
    buffer = io.BytesIO()
    display.save(buffer, format="PNG", compress_level=6)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    if len(_DATA_URL_CACHE) >= _DATA_URL_CACHE_LIMIT:
        _DATA_URL_CACHE.clear()
    _DATA_URL_CACHE[cache_key] = f"data:image/png;base64,{encoded}"
    return _DATA_URL_CACHE[cache_key], factor


def corners_layout(size: tuple[int, int]) -> Layout:
    """Layout, bei dem das Bild die gesamte Editorfläche einnimmt."""
    width, height = size
    return Layout(
        canvas_w=width,
        canvas_h=height,
        gel_left=0,
        gel_top=0,
        gel_w=width,
        gel_h=height,
        header_h=0,
        left_margin=0,
        right_margin=0,
        bottom_margin=0,
        tick_len=0,
        tick_gap=0,
        pad=0,
        column_left=0,
        column_right=0,
        label_font_px=12,
        number_font_px=12,
        letter_font_px=12,
        arrow_len=0,
        arrow_gap=0,
        label_block_h=0,
        group_block_h=0,
        condition_block_h=0,
        effective_sides=(),
    )


def gel_editor(
    *,
    figure: Image.Image,
    panel: GelPanel,
    layout: Layout,
    mode: str,
    selected: int = 0,
    labels: dict[str, str] | None = None,
    key: str,
    show_lane_numbers: bool = True,
) -> dict[str, Any] | None:
    """Zeigt das Gel mit ziehbaren Hilfslinien.

    Rückgabe (oder ``None``) je nach ``mode``:
      ``{"event": "lanes"|"markers"|"arrows", ...: [rel, ...]}``
      ``{"event": "corners", "corners": [[x, y], ...]}``
      ``{"event": "add_lane", "x_pos_rel": 0.42}``
      ``{"event": "add_marker"|"add_arrow", "y_pos_rel": 0.55, "side": "right"}``
      ``{"event": "delete_lane"|"select_lane", "index": 0}`` (analog marker/arrow)
    """
    image_data, factor = _data_url(figure)
    args: dict[str, Any] = {
        "image": image_data,
        "layout": layout.scaled(factor),
        "lanes": [
            {"x_rel": round(lane.x_pos_rel, 5), "label": lane.label_top}
            for lane in panel.lanes
        ],
        "markers": [
            {"mw": marker.display_value, "y_rel": round(marker.y_pos_rel, 5)}
            for marker in panel.sorted_markers()
        ],
        "arrows": [
            {"label": arrow.label, "y_rel": round(arrow.y_pos_rel, 5), "side": arrow.side}
            for arrow in panel.visible_arrows()
        ],
        "corners": [
            [round(float(point[0]), 5), round(float(point[1]), 5)]
            for point in panel.transform.perspective
        ],
        "mode": mode,
        "selected": int(selected),
        "labels": labels or {},
        "laneNumbers": bool(show_lane_numbers),
    }
    return _gel_editor(**args, key=key, default=None)
