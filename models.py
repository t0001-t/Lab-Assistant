"""Domänenmodell (Pydantic v2) für die SDS-PAGE-Publikationsdokumentation.

Alle relativen Koordinaten (``*_rel``) liegen im Bereich **0.0–1.0**
(0 = oben/links der Gelmatrix, 1 = unten/rechts). Dadurch bleiben Layouts
unabhängig von der Auflösung des importierten Bildes.

Das Modul enthält ausschließlich Datenstrukturen, Validierung und
Persistenz. Bildverarbeitung liegt in :mod:`image_processing`, das
Rendering in :mod:`canvas_renderer`.
"""

from __future__ import annotations

import base64
import io
import json
import uuid
from itertools import pairwise
from pathlib import Path
from typing import Any, Literal

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RGB = tuple[int, int, int]
Lang = Literal["de", "en"]
Theme = Literal["light", "dark"]
LadderSide = Literal["left", "right", "both"]
HarmonizationMode = Literal["none", "height", "affine"]
LabelRotation = Literal[0, 45, 90]

DEFAULT_LANE_COUNT = 10
DEFAULT_LADDER_MW: tuple[float, ...] = (
    170.0,
    130.0,
    100.0,
    70.0,
    55.0,
    40.0,
    35.0,
    25.0,
    10.0,
)
#: Aus dem Referenzgel vermessene Bandenpositionen (relativ 0..1).
DEFAULT_LADDER_Y: tuple[float, ...] = (
    0.136,
    0.177,
    0.249,
    0.310,
    0.404,
    0.516,
    0.630,
    0.737,
    0.844,
)

PROJECT_VERSION = 2
CORNER_ORDER = ("tl", "tr", "br", "bl")
IDENTITY_CORNERS: list[list[float]] = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]

#: Basis-Konfiguration aller Modelle: PIL-Bilder erlaubt, Zuweisungen
#: werden validiert (dadurch greift das Klemmen automatisch), unbekannte
#: Felder älterer Projektdateien werden ignoriert.
CONFIG = ConfigDict(
    arbitrary_types_allowed=True,
    validate_assignment=True,
    extra="ignore",
)


def clamp(value: float, low: float, high: float) -> float:
    """Begrenzt ``value`` auf das geschlossene Intervall [low, high]."""
    return max(low, min(high, value))


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int) -> int:
    try:
        return round(float(value))
    except (TypeError, ValueError):
        return default


# ----------------------------------------------------------------------
# Geometrie & Bildanpassung
# ----------------------------------------------------------------------
class Transform(BaseModel):
    """Geometrische Entzerrung eines Panels (nicht-destruktiv)."""

    model_config = CONFIG

    perspective: list[list[float]] = Field(
        default_factory=lambda: [list(point) for point in IDENTITY_CORNERS]
    )
    rotation: int = 0
    flip_h: bool = False
    flip_v: bool = False
    fine_rotation: float = 0.0
    crop: list[float] = Field(default_factory=lambda: [0.0, 0.0, 1.0, 1.0])

    @field_validator("perspective", mode="before")
    @classmethod
    def _v_perspective(cls, value: Any) -> list[list[float]]:
        if isinstance(value, (list, tuple)) and len(value) == 4:
            points: list[list[float]] = []
            for point in value:
                try:
                    x = clamp(float(point[0]), 0.0, 1.0)
                    y = clamp(float(point[1]), 0.0, 1.0)
                except (TypeError, ValueError, IndexError):
                    return [list(p) for p in IDENTITY_CORNERS]
                points.append([round(x, 6), round(y, 6)])
            return points
        return [list(p) for p in IDENTITY_CORNERS]

    @field_validator("rotation", mode="before")
    @classmethod
    def _v_rotation(cls, value: Any) -> int:
        step = _as_int(value, 0) % 360
        return int(round(step / 90.0) * 90) % 360

    @field_validator("fine_rotation", mode="before")
    @classmethod
    def _v_fine(cls, value: Any) -> float:
        return round(clamp(_as_float(value, 0.0), -45.0, 45.0), 2)

    @field_validator("crop", mode="before")
    @classmethod
    def _v_crop(cls, value: Any) -> list[float]:
        default = [0.0, 0.0, 1.0, 1.0]
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            return default
        left = clamp(_as_float(value[0], 0.0), 0.0, 1.0)
        top = clamp(_as_float(value[1], 0.0), 0.0, 1.0)
        right = clamp(_as_float(value[2], 1.0), 0.0, 1.0)
        bottom = clamp(_as_float(value[3], 1.0), 0.0, 1.0)
        if right - left < 0.02:
            right = min(1.0, left + 0.02)
        if bottom - top < 0.02:
            bottom = min(1.0, top + 0.02)
        return [round(left, 5), round(top, 5), round(right, 5), round(bottom, 5)]

    @property
    def is_identity(self) -> bool:
        return (
            self.perspective == [list(p) for p in IDENTITY_CORNERS]
            and self.rotation == 0
            and not self.flip_h
            and not self.flip_v
            and abs(self.fine_rotation) < 1e-9
            and self.crop == [0.0, 0.0, 1.0, 1.0]
        )

    def reset(self) -> None:
        self.perspective = [list(p) for p in IDENTITY_CORNERS]
        self.rotation = 0
        self.flip_h = False
        self.flip_v = False
        self.fine_rotation = 0.0
        self.crop = [0.0, 0.0, 1.0, 1.0]


class Adjustments(BaseModel):
    """Nicht-destruktive Bildfilter (Echtzeit-Schieberegler)."""

    model_config = CONFIG

    brightness: float = 0.0  # -100 .. +100 (additiv)
    contrast: float = 1.0  # 0.1 .. 3.0 (multiplikativ)
    gamma: float = 1.0  # 0.1 .. 3.0
    invert: bool = False
    clahe: bool = False
    clahe_clip: float = 2.0
    clahe_grid: int = 8

    @field_validator("brightness", mode="before")
    @classmethod
    def _v_brightness(cls, value: Any) -> float:
        return round(clamp(_as_float(value, 0.0), -100.0, 100.0), 2)

    @field_validator("contrast", mode="before")
    @classmethod
    def _v_contrast(cls, value: Any) -> float:
        return round(clamp(_as_float(value, 1.0), 0.1, 3.0), 3)

    @field_validator("gamma", mode="before")
    @classmethod
    def _v_gamma(cls, value: Any) -> float:
        return round(clamp(_as_float(value, 1.0), 0.1, 3.0), 3)

    @field_validator("clahe_clip", mode="before")
    @classmethod
    def _v_clip(cls, value: Any) -> float:
        return round(clamp(_as_float(value, 2.0), 1.0, 10.0), 2)

    @field_validator("clahe_grid", mode="before")
    @classmethod
    def _v_grid(cls, value: Any) -> int:
        return int(clamp(_as_int(value, 8), 2, 32))

    @property
    def is_identity(self) -> bool:
        return (
            abs(self.brightness) < 1e-9
            and abs(self.contrast - 1.0) < 1e-9
            and abs(self.gamma - 1.0) < 1e-9
            and not self.invert
            and not self.clahe
        )

    def reset(self) -> None:
        self.brightness = 0.0
        self.contrast = 1.0
        self.gamma = 1.0
        self.invert = False
        self.clahe = False


# ----------------------------------------------------------------------
# Annotationselemente
# ----------------------------------------------------------------------
class MarkerBand(BaseModel):
    """Eine Bande der Molekulargewichtsleiter."""

    model_config = CONFIG

    mw: float = 0.0
    unit: str = "kDa"
    y_pos_rel: float = 0.5
    visible: bool = True

    @field_validator("mw", mode="before")
    @classmethod
    def _v_mw(cls, value: Any) -> float:
        return round(max(0.0, _as_float(value, 0.0)), 4)

    @field_validator("y_pos_rel", mode="before")
    @classmethod
    def _v_y(cls, value: Any) -> float:
        return round(clamp(_as_float(value, 0.5), 0.0, 1.0), 6)

    @field_validator("unit", mode="before")
    @classmethod
    def _v_unit(cls, value: Any) -> str:
        text = str(value or "").strip()
        return text or "kDa"

    @property
    def display_value(self) -> str:
        """Formatiert den kDa-Wert ohne überflüssige Nachkommastellen."""
        return f"{self.mw:g}"


class TargetArrow(BaseModel):
    """Zielbanden-Pfeil im linken oder rechten Außenrand."""

    model_config = CONFIG

    label: str = ""
    y_pos_rel: float = 0.5
    side: Literal["left", "right"] = "right"
    visible: bool = True

    @field_validator("y_pos_rel", mode="before")
    @classmethod
    def _v_y(cls, value: Any) -> float:
        return round(clamp(_as_float(value, 0.5), 0.0, 1.0), 6)

    @field_validator("side", mode="before")
    @classmethod
    def _v_side(cls, value: Any) -> str:
        return "left" if value == "left" else "right"


class ConditionRow(BaseModel):
    """Eine Zeile der Bedingungs-Matrix über den Spuren."""

    model_config = CONFIG

    name: str = ""
    values: list[str] = Field(default_factory=list)

    @field_validator("values", mode="before")
    @classmethod
    def _v_values(cls, value: Any) -> list[str]:
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value]
        if value is None:
            return []
        return [str(value)]

    def value_for(self, lane_index: int) -> str:
        if 0 <= lane_index < len(self.values):
            return self.values[lane_index]
        return ""


class GroupLabel(BaseModel):
    """Gruppenüberschrift über mehreren Spuren (mit Trennlinie)."""

    model_config = CONFIG

    text: str = ""
    start_index: int = 0
    end_index: int = 0
    underline: bool = True

    @field_validator("start_index", "end_index", mode="before")
    @classmethod
    def _v_index(cls, value: Any) -> int:
        return max(0, _as_int(value, 0))

    @field_validator("text", mode="before")
    @classmethod
    def _v_text(cls, value: Any) -> str:
        return str(value or "").strip()


class Lane(BaseModel):
    """Eine Probenspur."""

    model_config = CONFIG

    index: int = 0
    x_pos_rel: float = 0.5
    label_top: str = ""
    label_bottom: str = ""

    @field_validator("index", mode="before")
    @classmethod
    def _v_index(cls, value: Any) -> int:
        return max(0, _as_int(value, 0))

    @field_validator("x_pos_rel", mode="before")
    @classmethod
    def _v_x(cls, value: Any) -> float:
        return round(clamp(_as_float(value, 0.5), 0.0, 1.0), 6)


# ----------------------------------------------------------------------
# Panel
# ----------------------------------------------------------------------
def default_lanes(count: int = DEFAULT_LANE_COUNT) -> list[Lane]:
    """Gleichmäßig verteilte Spuren (Standard: 1…10)."""
    count = max(1, int(count))
    return [
        Lane(index=i, x_pos_rel=round((i + 0.5) / count, 6), label_top=str(i + 1))
        for i in range(count)
    ]


def default_markers() -> list[MarkerBand]:
    """Referenzleiter: 170 … 10 kDa mit vermessenen Y-Positionen."""
    return [
        MarkerBand(mw=mw, y_pos_rel=y)
        for mw, y in zip(DEFAULT_LADDER_MW, DEFAULT_LADDER_Y, strict=True)
    ]


class GelPanel(BaseModel):
    """Ein Gel mit Quellbild, Transformation und allen Annotationen."""

    model_config = CONFIG

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    letter: str = "A"
    name: str = ""
    source_name: str = ""
    source_image: Image.Image | None = Field(default=None, exclude=True)
    transform: Transform = Field(default_factory=Transform)
    adjustments: Adjustments = Field(default_factory=Adjustments)
    lanes: list[Lane] = Field(default_factory=default_lanes)
    conditions: list[ConditionRow] = Field(default_factory=list)
    groups: list[GroupLabel] = Field(default_factory=list)
    markers: list[MarkerBand] = Field(default_factory=default_markers)
    arrows: list[TargetArrow] = Field(default_factory=list)
    marker_lane_indexes: list[int] = Field(default_factory=lambda: [0])
    ladder_sides: LadderSide = "left"
    unit: str = "kDa"

    @field_validator("letter", mode="before")
    @classmethod
    def _v_letter(cls, value: Any) -> str:
        text = str(value or "").strip()
        return text or "A"

    @field_validator("unit", mode="before")
    @classmethod
    def _v_unit(cls, value: Any) -> str:
        return str(value or "kDa").strip() or "kDa"

    @field_validator("ladder_sides", mode="before")
    @classmethod
    def _v_sides(cls, value: Any) -> str:
        return value if value in ("left", "right", "both") else "left"

    @field_validator("lanes", mode="before")
    @classmethod
    def _v_lanes(cls, value: Any) -> Any:
        if isinstance(value, (list, tuple)) and len(value) >= 1:
            return list(value)
        return default_lanes()

    # ------------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------------
    @property
    def lane_count(self) -> int:
        return len(self.lanes)

    def sorted_markers(self) -> list[MarkerBand]:
        """Sichtbare Marker, von oben nach unten sortiert."""
        return sorted((m for m in self.markers if m.visible), key=lambda m: m.y_pos_rel)

    def visible_arrows(self) -> list[TargetArrow]:
        return [a for a in self.arrows if a.visible]

    def arrows_on(self, side: str) -> list[TargetArrow]:
        return [a for a in self.visible_arrows() if a.side == side]

    def lane_pitch_rel(self, index: int) -> float:
        """Geschätzte Spurbreite (relativ), Abstand zu den Nachbarn."""
        xs = [lane.x_pos_rel for lane in self.lanes]
        if len(xs) < 2:
            return 0.1
        if index <= 0:
            return max(0.02, xs[1] - xs[0])
        if index >= len(xs) - 1:
            return max(0.02, xs[-1] - xs[-2])
        return max(0.02, (xs[index + 1] - xs[index - 1]) / 2.0)

    def is_marker_lane(self, index: int) -> bool:
        return index in self.marker_lane_indexes

    def marker_mw_at(self, y_pos_rel: float) -> float:
        """Log-lineare kDa-Schätzung an einer relativen Y-Position."""
        points = sorted(
            ((m.y_pos_rel, m.mw) for m in self.markers if m.visible and m.mw > 0),
            key=lambda item: item[0],
        )
        if len(points) < 2:
            return 0.0
        import math

        if y_pos_rel <= points[0][0]:
            (y0, v0), (y1, v1) = points[0], points[1]
        elif y_pos_rel >= points[-1][0]:
            (y0, v0), (y1, v1) = points[-2], points[-1]
        else:
            (y0, v0), (y1, v1) = points[0], points[1]
            for (ya, va), (yb, vb) in pairwise(points):
                if ya <= y_pos_rel <= yb:
                    y0, v0, y1, v1 = ya, va, yb, vb
                    break
        if y1 == y0:
            return float(round(v0, 1))
        fraction = (y_pos_rel - y0) / (y1 - y0)
        value = 10.0 ** (math.log10(v0) + fraction * (math.log10(v1) - math.log10(v0)))
        if value >= 100:
            return float(round(value / 5.0) * 5)
        if value >= 20:
            return float(round(value))
        return float(round(value * 2) / 2)

    def processed_image(self) -> Image.Image:
        """Liefert das verarbeitete Gel (Transformation + Filter)."""
        import image_processing as ip

        return ip.process_panel(self)


# ----------------------------------------------------------------------
# Export-Einstellungen
# ----------------------------------------------------------------------
class ExportSettings(BaseModel):
    """Globale Export- und Renderingparameter."""

    model_config = CONFIG

    dpi: int = 300
    supersample: int = 2
    font_family: str = "Arial"
    font_scale: float = 1.0
    theme: Theme = "light"
    label_rotation: LabelRotation = 0
    #: Spurnummern klein an der Spur: "none" | "top" | "bottom".
    lane_numbers_position: str = "bottom"
    show_lane_labels_bottom: bool = False
    harmonization: HarmonizationMode = "none"
    target_height: int = 700
    ref_marker_top: float = 100.0
    ref_marker_bottom: float = 10.0
    ref_target_top: float = 0.15
    ref_target_bottom: float = 0.85
    gutter_px: int = 40
    embed_images: bool = True

    @field_validator("dpi", mode="before")
    @classmethod
    def _v_dpi(cls, value: Any) -> int:
        return int(clamp(_as_int(value, 300), 72, 1200))

    @field_validator("supersample", mode="before")
    @classmethod
    def _v_super(cls, value: Any) -> int:
        return int(clamp(_as_int(value, 2), 1, 3))

    @field_validator("font_scale", mode="before")
    @classmethod
    def _v_scale(cls, value: Any) -> float:
        return round(clamp(_as_float(value, 1.0), 0.6, 2.0), 3)

    @field_validator("theme", mode="before")
    @classmethod
    def _v_theme(cls, value: Any) -> str:
        return value if value in ("light", "dark") else "light"

    @field_validator("label_rotation", mode="before")
    @classmethod
    def _v_rot(cls, value: Any) -> int:
        step = _as_int(value, 0)
        return step if step in (0, 45, 90) else 0

    @field_validator("lane_numbers_position", mode="before")
    @classmethod
    def _v_lane_numbers(cls, value: Any) -> str:
        if isinstance(value, bool):
            return "bottom" if value else "none"
        return value if value in ("none", "top", "bottom") else "bottom"

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy(cls, data: Any) -> Any:
        """Übernimmt das alte boolesche Feld ``show_lane_numbers_bottom``."""
        if isinstance(data, dict) and "lane_numbers_position" not in data and "show_lane_numbers_bottom" in data:
            legacy = data.get("show_lane_numbers_bottom")
            data = {**data, "lane_numbers_position": "bottom" if legacy else "none"}
        return data

    @field_validator("harmonization", mode="before")
    @classmethod
    def _v_harm(cls, value: Any) -> str:
        return value if value in ("none", "height", "affine") else "none"

    @field_validator("target_height", mode="before")
    @classmethod
    def _v_height(cls, value: Any) -> int:
        return int(clamp(_as_int(value, 700), 120, 6000))

    @field_validator("ref_target_top", "ref_target_bottom", mode="before")
    @classmethod
    def _v_ref_target(cls, value: Any) -> float:
        return round(clamp(_as_float(value, 0.5), 0.0, 1.0), 4)

    @field_validator("gutter_px", mode="before")
    @classmethod
    def _v_gutter(cls, value: Any) -> int:
        return int(clamp(_as_int(value, 40), 0, 400))


# ----------------------------------------------------------------------
# Projekt
# ----------------------------------------------------------------------
class Project(BaseModel):
    """Gesamter Projektstand (mehrere Panels, Sprache, Theme, Export)."""

    model_config = CONFIG

    version: int = PROJECT_VERSION
    name: str = "GelDoc-Projekt"
    lang: Lang = "de"
    theme: Theme = "light"
    export: ExportSettings = Field(default_factory=ExportSettings)
    panels: list[GelPanel] = Field(default_factory=lambda: [GelPanel()])

    @field_validator("lang", mode="before")
    @classmethod
    def _v_lang(cls, value: Any) -> str:
        return value if value in ("de", "en") else "de"

    @field_validator("theme", mode="before")
    @classmethod
    def _v_theme(cls, value: Any) -> str:
        return value if value in ("light", "dark") else "light"

    @field_validator("panels", mode="before")
    @classmethod
    def _v_panels(cls, value: Any) -> Any:
        if isinstance(value, (list, tuple)) and len(value) >= 1:
            return list(value)
        return [GelPanel()]

    # ------------------------------------------------------------------
    # Panel-Verwaltung
    # ------------------------------------------------------------------
    def panel_letters(self) -> list[str]:
        return [panel.letter for panel in self.panels]

    def next_letter(self) -> str:
        """Nächster freier Buchstabe (A…Z, danach A1, B1, …)."""
        used = {panel.letter for panel in self.panels}
        for index in range(26):
            letter = chr(ord("A") + index)
            if letter not in used:
                return letter
        cycle = 1
        while True:
            for index in range(26):
                letter = f"{chr(ord('A') + index)}{cycle}"
                if letter not in used:
                    return letter
            cycle += 1

    def add_panel(self) -> GelPanel:
        panel = GelPanel(letter=self.next_letter())
        panel.name = f"{panel.letter}"
        self.panels.append(panel)
        return panel

    def duplicate_panel(self, index: int) -> GelPanel:
        source = self.panels[index]
        clone = source.model_copy(deep=True)
        clone.id = uuid.uuid4().hex[:12]
        clone.letter = self.next_letter()
        clone.name = f"{clone.letter}"
        clone.arrows = [TargetArrow(**a.model_dump()) for a in source.arrows]
        self.panels.append(clone)
        return clone

    def remove_panel(self, index: int) -> bool:
        if len(self.panels) <= 1 or not (0 <= index < len(self.panels)):
            return False
        self.panels.pop(index)
        return True

    def has_any_image(self) -> bool:
        return any(panel.source_image is not None for panel in self.panels)

    # ------------------------------------------------------------------
    # Persistenz
    # ------------------------------------------------------------------
    def to_dict(self, embed_images: bool = True) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        images: dict[str, dict[str, str]] = {}
        if embed_images:
            for panel in self.panels:
                if panel.source_image is None:
                    continue
                images[panel.id] = {
                    "name": panel.source_name,
                    "png_b64": encode_image_png_b64(panel.source_image),
                }
        data["images"] = images
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        payload = dict(data)
        images = payload.pop("images", {}) or {}
        project = cls.model_validate(payload)
        for panel in project.panels:
            entry = images.get(panel.id)
            if isinstance(entry, dict) and entry.get("png_b64"):
                try:
                    panel.source_image = decode_image_png_b64(entry["png_b64"])
                    if not panel.source_name:
                        panel.source_name = str(entry.get("name", ""))
                except (ValueError, OSError):
                    panel.source_image = None
        return project

    def to_json(self, embed_images: bool = True, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(embed_images=embed_images), indent=indent, ensure_ascii=False
        )

    def to_json_bytes(self, embed_images: bool = True) -> bytes:
        return self.to_json(embed_images=embed_images).encode("utf-8")

    @classmethod
    def from_json(cls, text: str) -> Project:
        return cls.from_dict(json.loads(text))

    @classmethod
    def from_json_bytes(cls, data: bytes) -> Project:
        return cls.from_json(data.decode("utf-8"))

    def save(self, path: str | Path, embed_images: bool | None = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        embed = self.export.embed_images if embed_images is None else embed_images
        path.write_text(self.to_json(embed_images=embed), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: str | Path) -> Project:
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


# ----------------------------------------------------------------------
# Bildkodierung (Projekt-Persistenz)
# ----------------------------------------------------------------------
def encode_image_png_b64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG", compress_level=6)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def decode_image_png_b64(data: str) -> Image.Image:
    with Image.open(io.BytesIO(base64.b64decode(data))) as image:
        return image.convert("RGB")


def default_project(lane_count: int = DEFAULT_LANE_COUNT) -> Project:
    """Standardprojekt mit einem Panel (10 Spuren, Referenzleiter)."""
    panel = GelPanel(lanes=default_lanes(lane_count))
    panel.name = "A"
    return Project(panels=[panel])
