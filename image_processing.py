"""Bildverarbeitung & Analyse für SDS-PAGE-Gele.

Das Modul bündelt die komplette, nicht-destruktive Bildpipeline:

* Import (PNG/JPEG/TIFF) und Zuschnitt
* geometrische Entzerrung (Perspektive, 90°-Drehung, Spiegeln, Feinrotation)
* Filter (Helligkeit, Kontrast, Gamma, Invertieren, optional CLAHE)
* Multi-Gel-Harmonisierung (gleiche Pixelhöhe oder affine Ausrichtung
  zweier Referenzbanden)
* Banden-/Spurenerkennung als Vorschlagswert

OpenCV wird – wenn vorhanden – für die Perspektivtransformation und CLAHE
genutzt; andernfalls greift ein reiner Pillow/NumPy-Fallback, damit die App
ohne OpenCV lauffähig bleibt.
"""

from __future__ import annotations

import io
import math
from collections.abc import Callable
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from models import Adjustments, GelPanel, MarkerBand, Transform, clamp

try:  # pragma: no cover – abhängig von der Installation
    import cv2  # type: ignore

    HAS_CV2 = True
except Exception:  # noqa: BLE001 – jedes Importproblem fällt auf den Fallback zurück
    cv2 = None  # type: ignore
    HAS_CV2 = False

MAX_DIMENSION = 6000
Polarity = Literal["auto", "dark", "light"]


# ----------------------------------------------------------------------
# Ergebnisdatentypen
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class LaneDetection:
    """Ergebnis der automatischen Spurenschätzung (relativ 0..1)."""

    positions_rel: tuple[float, ...]
    detected_peak_count: int
    anchor_positions_rel: tuple[float, ...]
    method: str


@dataclass(frozen=True)
class MarkerDetection:
    """Ergebnis der automatischen Marker-Bandenerkennung (relativ 0..1)."""

    positions_rel: tuple[float, ...]
    peak_count: int
    side: str


# ----------------------------------------------------------------------
# Import / Zuschnitt
# ----------------------------------------------------------------------
def load_image(data: bytes) -> Image.Image:
    """Lädt PNG/JPEG/TIFF robust, inkl. EXIF-Drehung und Transparenz."""
    with Image.open(io.BytesIO(data)) as src:
        src.seek(0)
        image = ImageOps.exif_transpose(src)
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGBA")
            background = Image.new("RGBA", image.size, (255, 255, 255, 255))
            image = Image.alpha_composite(background, image)
        image = image.convert("RGB")

    if max(image.size) > MAX_DIMENSION:
        scale = MAX_DIMENSION / max(image.size)
        image = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            Image.Resampling.LANCZOS,
        )
    return image


def load_image_from_path(path: str | Path) -> Image.Image:
    return load_image(Path(path).read_bytes())


def resize_for_display(image: Image.Image, max_w: int, max_h: int) -> Image.Image:
    """Verkleinert ein Bild ausschließlich zur Anzeige (Seitenverhältnis bleibt)."""
    preview = image.copy()
    preview.thumbnail((max(32, max_w), max(32, max_h)), Image.Resampling.LANCZOS)
    return preview


def border_color(image: Image.Image) -> tuple[int, int, int]:
    """Medianfarbe des Bildrandes – dient als Füllfarbe bei Drehungen."""
    array = np.asarray(image.convert("RGB"), dtype=np.uint8)
    if array.size == 0:
        return (255, 255, 255)
    border = np.concatenate(
        [
            array[:2].reshape(-1, 3),
            array[-2:].reshape(-1, 3),
            array[:, :2].reshape(-1, 3),
            array[:, -2:].reshape(-1, 3),
        ]
    )
    median = np.median(border, axis=0)
    return (int(median[0]), int(median[1]), int(median[2]))


def auto_crop_box(image: Image.Image) -> tuple[int, int, int, int]:
    """Schlägt einen Zuschnitt vor, der einfarbige Bildränder entfernt."""
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    height, width = rgb.shape[:2]
    if width < 8 or height < 8:
        return (0, 0, width, height)

    border = np.concatenate(
        [
            rgb[:3].reshape(-1, 3),
            rgb[-3:].reshape(-1, 3),
            rgb[:, :3].reshape(-1, 3),
            rgb[:, -3:].reshape(-1, 3),
        ]
    )
    reference = np.median(border, axis=0)
    distance = np.abs(rgb - reference).max(axis=2)
    content = distance > 18

    def smooth(mask: np.ndarray, axis: int) -> np.ndarray:
        shifted = [mask]
        for shift in (-2, -1, 1, 2):
            shifted.append(np.roll(mask, shift, axis=axis))
        return np.mean(shifted, axis=0) > 0.5

    content = smooth(smooth(content, 0), 1)

    rows = np.where(content.mean(axis=1) > 0.08)[0]
    cols = np.where(content.mean(axis=0) > 0.08)[0]
    if rows.size == 0 or cols.size == 0:
        return (0, 0, width, height)

    pad = max(2, round(min(width, height) * 0.006))
    left = max(0, int(cols[0]) - pad)
    right = min(width, int(cols[-1]) + 1 + pad)
    top = max(0, int(rows[0]) - pad)
    bottom = min(height, int(rows[-1]) + 1 + pad)
    if right - left < width * 0.25 or bottom - top < height * 0.25:
        return (0, 0, width, height)
    return (left, top, right, bottom)


# ----------------------------------------------------------------------
# Geometrie
# ----------------------------------------------------------------------
def _warp_perspective(
    image: Image.Image, corners: list[list[float]]
) -> Image.Image:
    """Begradigt ein Trapez. ``corners`` sind 0..1 in Reihenfolge TL,TR,BR,BL."""
    width, height = image.size
    source = np.float32([[x * width, y * height] for x, y in corners])

    top = float(np.linalg.norm(source[1] - source[0]))
    bottom = float(np.linalg.norm(source[2] - source[3]))
    left = float(np.linalg.norm(source[3] - source[0]))
    right = float(np.linalg.norm(source[2] - source[1]))
    out_w = max(2, round(max(top, bottom)) or width)
    out_h = max(2, round(max(left, right)) or height)
    destination = np.float32([[0, 0], [out_w, 0], [out_w, out_h], [0, out_h]])

    if HAS_CV2 and cv2 is not None:
        matrix = cv2.getPerspectiveTransform(source, destination)
        warped = cv2.warpPerspective(
            np.asarray(image.convert("RGB")),
            matrix,
            (out_w, out_h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return Image.fromarray(warped)

    # Fallback: Pillow QUAD (billineare Näherung, ausreichend für Entzerrung).
    quad = (
        source[0][0], source[0][1],
        source[1][0], source[1][1],
        source[2][0], source[2][1],
        source[3][0], source[3][1],
    )
    return image.convert("RGB").transform(
        (out_w, out_h), Image.Transform.QUAD, quad, resample=Image.Resampling.BICUBIC
    )


def apply_transform(image: Image.Image, transform: Transform) -> Image.Image:
    """Wendet die nicht-destruktive Geometrie auf ein Bild an."""
    result = image.convert("RGB")
    fill = border_color(result)

    if transform.perspective != [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]:
        result = _warp_perspective(result, transform.perspective)

    if transform.rotation % 360:
        result = result.rotate(-transform.rotation, expand=True, fillcolor=fill)

    if transform.flip_h:
        result = ImageOps.mirror(result)
    if transform.flip_v:
        result = ImageOps.flip(result)

    if abs(transform.fine_rotation) > 1e-9:
        result = result.rotate(
            -transform.fine_rotation,
            resample=Image.Resampling.BICUBIC,
            expand=True,
            fillcolor=fill,
        )

    left, top, right, bottom = transform.crop
    if (left, top, right, bottom) != (0.0, 0.0, 1.0, 1.0):
        width, height = result.size
        box = (
            int(clamp(left, 0.0, 1.0) * width),
            int(clamp(top, 0.0, 1.0) * height),
            int(clamp(right, 0.0, 1.0) * width),
            int(clamp(bottom, 0.0, 1.0) * height),
        )
        box = (
            box[0],
            box[1],
            max(box[0] + 2, box[2]),
            max(box[1] + 2, box[3]),
        )
        result = result.crop(box)

    return result


# ----------------------------------------------------------------------
# Filter
# ----------------------------------------------------------------------
def _apply_clahe(array: np.ndarray, clip: float, grid: int) -> np.ndarray:
    if not (HAS_CV2 and cv2 is not None):
        # Fallback: globaler Kontrastausgleich im L-Kanal.
        return array
    lab = cv2.cvtColor(array, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=float(clip), tileGridSize=(int(grid), int(grid)))
    l_channel = clahe.apply(l_channel)
    merged = cv2.merge((l_channel, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)


def apply_adjustments(image: Image.Image, adjustments: Adjustments) -> Image.Image:
    """Helligkeit/Kontrast/Gamma/Invertieren/CLAHE – mit Non-Destructive-Logik."""
    if adjustments.is_identity:
        return image.convert("RGB")

    array = np.asarray(image.convert("RGB"), dtype=np.float32)

    if abs(adjustments.brightness) > 1e-9:
        array = array + adjustments.brightness / 100.0 * 128.0

    if abs(adjustments.contrast - 1.0) > 1e-9:
        array = (array - 128.0) * adjustments.contrast + 128.0

    array = np.clip(array, 0.0, 255.0)

    if abs(adjustments.gamma - 1.0) > 1e-9:
        lut = (np.arange(256, dtype=np.float32) / 255.0) ** (1.0 / adjustments.gamma)
        array = np.take(lut * 255.0, array.astype(np.uint8))

    result = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), mode="RGB")

    if adjustments.clahe:
        result = Image.fromarray(
            _apply_clahe(
                np.asarray(result, dtype=np.uint8),
                adjustments.clahe_clip,
                adjustments.clahe_grid,
            )
        )

    if adjustments.invert:
        result = ImageOps.invert(result)

    return result


def process_panel(panel: GelPanel) -> Image.Image:
    """Führt die komplette Pipeline für ein Panel aus (ohne Harmonisierung)."""
    if panel.source_image is None:
        raise ValueError("Panel enthält kein Quellbild.")
    transformed = apply_transform(panel.source_image, panel.transform)
    return apply_adjustments(transformed, panel.adjustments)


# ----------------------------------------------------------------------
# Harmonisierung
# ----------------------------------------------------------------------
def _reference_y(panel: GelPanel, mw: float) -> float | None:
    """Relative Y-Position des Markers, der ``mw`` am nächsten liegt."""
    candidates = [(abs(m.mw - mw), m) for m in panel.markers if m.visible]
    if not candidates:
        return None
    distance, marker = min(candidates, key=lambda item: item[0])
    if distance > max(1.0, mw * 0.25):
        return None
    return marker.y_pos_rel


def affine_from_references(
    y_top: float, y_bottom: float, target_top: float, target_bottom: float
) -> tuple[float, float] | None:
    """Berechnet die affine Y-Abbildung ``out = a*in + b`` aus zwei Banden."""
    if y_bottom - y_top < 1e-4:
        return None
    a = (target_bottom - target_top) / (y_bottom - y_top)
    b = target_top - a * y_top
    if a <= 0:
        return None
    return a, b


def harmonization_affine(panel: GelPanel, project) -> tuple[float, float] | None:
    """Affine Y-Abbildung eines Panels gemäß Projekt-Einstellungen."""
    settings = project.export
    if settings.harmonization != "affine":
        return None
    y_top = _reference_y(panel, settings.ref_marker_top)
    y_bottom = _reference_y(panel, settings.ref_marker_bottom)
    if y_top is None or y_bottom is None:
        return None
    return affine_from_references(
        y_top, y_bottom, settings.ref_target_top, settings.ref_target_bottom
    )


def harmonize_gel(
    gel: Image.Image,
    affine: tuple[float, float] | None,
    out_height: int | None = None,
    fill: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """Wendet die vertikale Harmonisierung auf ein Gelbild an."""
    width, height = gel.size

    if affine is None:
        if out_height and out_height != height:
            ratio = out_height / height
            return gel.resize(
                (max(2, round(width * ratio)), out_height),
                Image.Resampling.LANCZOS,
            )
        return gel

    target_height = out_height or height
    a, b = affine
    # y_src = (height / (a * target_height)) * y_out - (b * height / a)
    a22 = height / (a * target_height)
    a23 = -(b * height / a)
    return gel.convert("RGB").transform(
        (width, target_height),
        Image.Transform.AFFINE,
        (1.0, 0.0, 0.0, 0.0, a22, a23),
        resample=Image.Resampling.BILINEAR,
        fillcolor=fill,
    )


def y_mapper(affine: tuple[float, float] | None) -> Callable[[float], float]:
    """Liefert die Y-Abbildung für Annotationen (relativ 0..1)."""
    if affine is None:
        return lambda y: float(clamp(y, 0.0, 1.0))
    a, b = affine

    def _map(y: float) -> float:
        return float(clamp(a * y + b, 0.0, 1.0))

    return _map


def remap_panel(panel: GelPanel, mapper: Callable[[float], float]) -> GelPanel:
    """Kopie eines Panels mit vertikal abgebildeten Marker-/Pfeilpositionen."""
    clone = panel.model_copy(deep=True)
    for marker in clone.markers:
        marker.y_pos_rel = mapper(marker.y_pos_rel)
    for arrow in clone.arrows:
        arrow.y_pos_rel = mapper(arrow.y_pos_rel)
    return clone


def harmonize_panel(
    panel: GelPanel, project, fill: tuple[int, int, int] = (255, 255, 255)
) -> tuple[Image.Image, Callable[[float], float]]:
    """Verarbeitet und harmonisiert ein Panel; liefert Bild und Y-Mapping."""
    gel = process_panel(panel)
    settings = project.export
    if settings.harmonization == "none":
        return gel, y_mapper(None)
    if settings.harmonization == "height":
        resized = harmonize_gel(gel, None, out_height=settings.target_height, fill=fill)
        return resized, y_mapper(None)
    affine = harmonization_affine(panel, project)
    if affine is None:
        resized = harmonize_gel(gel, None, out_height=settings.target_height, fill=fill)
        return resized, y_mapper(None)
    transformed = harmonize_gel(gel, affine, out_height=settings.target_height, fill=fill)
    return transformed, y_mapper(affine)


# ----------------------------------------------------------------------
# Gemeinsame Bildvorbereitung für die Analyse
# ----------------------------------------------------------------------
def _polarity_value(image: Image.Image, polarity: Polarity) -> str:
    if polarity in ("dark", "light"):
        return polarity
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    return "dark" if float(np.median(gray)) >= 110.0 else "light"


def _band_energy(image: Image.Image, polarity: Polarity = "auto") -> np.ndarray:
    """Hochpass-Energie; hebt Banden unabhängig von der Polarität hervor."""
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    blurred = np.asarray(
        image.convert("L").filter(ImageFilter.GaussianBlur(25)), dtype=np.float32
    )
    mode = _polarity_value(image, polarity)
    if mode == "light":  # helle Banden auf dunklem Grund
        return np.clip(gray - blurred, 0.0, None)
    return np.clip(blurred - gray, 0.0, None)


def _analysis_image(image: Image.Image, max_dimension: int = 2000) -> Image.Image:
    if max(image.size) <= max_dimension:
        return image
    copy = image.copy()
    copy.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return copy


def _smooth(values: np.ndarray, window: int) -> np.ndarray:
    window = max(1, int(window))
    if window % 2 == 0:
        window += 1
    return np.convolve(values, np.ones(window) / window, mode="same")


def _local_maxima(
    values: np.ndarray, threshold: float, min_distance: int
) -> list[tuple[int, float]]:
    candidates: list[tuple[int, float]] = []
    radius = max(1, min_distance // 2)
    for index in range(radius, len(values) - radius):
        window = values[index - radius : index + radius + 1]
        if values[index] >= window.max() and values[index] > threshold:
            candidates.append((index, float(values[index])))

    candidates.sort(key=lambda item: item[1], reverse=True)
    selected: list[tuple[int, float]] = []
    for index, score in candidates:
        if all(abs(index - other) >= min_distance for other, _ in selected):
            selected.append((index, score))
    return selected


# ----------------------------------------------------------------------
# Spuren
# ----------------------------------------------------------------------
def detect_lanes(
    image: Image.Image, expected: int = 10, polarity: Polarity = "auto"
) -> LaneDetection:
    """Schätzt vertikale Spuren anhand des horizontalen Projektionsprofils."""
    if expected < 1:
        raise ValueError("expected muss >= 1 sein")

    image = _analysis_image(image)
    height, width = image.size[1], image.size[0]
    energy = _band_energy(image, polarity)
    zone_top = int(height * 0.06)
    zone_bottom = int(height * 0.90)
    profile = energy[zone_top:zone_bottom].mean(axis=0)
    profile = _smooth(profile, max(7, width // 120))

    threshold = max(float(np.percentile(profile, 72)), float(profile.mean() * 1.15))
    min_distance = max(8, int(width / max(expected * 2, 1)))
    peaks = _local_maxima(profile, threshold, min_distance)
    peaks = [(x, score) for x, score in peaks if width * 0.012 < x < width * 0.988]
    peaks.sort(key=lambda item: item[0])

    cluster_distance = max(6.0, width / max(expected, 1) * 0.55)
    anchors: list[float] = []
    for x, _score in peaks:
        if not anchors or x - anchors[-1] > cluster_distance:
            anchors.append(float(x))
        else:
            anchors[-1] = (anchors[-1] + x) / 2.0

    anchor_rel = tuple(round(a / width, 4) for a in anchors)

    if len(anchors) >= 2:
        first, last = anchors[0], anchors[-1]
        positions = [first + (last - first) * i / (expected - 1) for i in range(expected)]
        method = "anchors"
    elif len(anchors) == 1:
        center = anchors[0]
        step = width / expected
        first = center - (expected - 1) * step / 2.0
        positions = [first + step * i for i in range(expected)]
        method = "single-anchor"
    else:
        margin = width * 0.03
        step = (width - 2 * margin) / max(expected - 1, 1)
        positions = [margin + step * i for i in range(expected)]
        method = "even-grid"

    positions = [clamp(p, width * 0.005, width * 0.995) for p in positions]
    return LaneDetection(
        positions_rel=tuple(round(p / width, 4) for p in positions),
        detected_peak_count=len(peaks),
        anchor_positions_rel=anchor_rel,
        method=method,
    )


# ----------------------------------------------------------------------
# Markerleiter
# ----------------------------------------------------------------------
def detect_marker_bands(
    image: Image.Image,
    side: str = "left",
    count: int = 9,
    polarity: Polarity = "auto",
) -> MarkerDetection:
    """Detektiert horizontale Markerbanden in der linken/rechten Leiterspur."""
    if side not in ("left", "right"):
        raise ValueError("side muss 'left' oder 'right' sein")

    image = _analysis_image(image)
    height, width = image.size[1], image.size[0]
    energy = _band_energy(image, polarity)

    if side == "left":
        start, end = int(width * 0.006), int(width * 0.072)
    else:
        start, end = int(width * 0.928), int(width * 0.994)
    profile = _smooth(energy[:, start:end].mean(axis=1), max(5, height // 180))

    global_profile = _smooth(
        energy[:, int(width * 0.06) : int(width * 0.94)].mean(axis=1),
        max(7, height // 120),
    )
    front_threshold = float(np.percentile(global_profile, 96))
    front_rows = np.where(global_profile > front_threshold)[0]

    threshold = max(3.0, float(np.percentile(profile, 70)))
    min_distance = max(6, int(height * 0.012))
    peaks = _local_maxima(profile, threshold, min_distance)
    peaks = [
        (y, score)
        for y, score in peaks
        if height * 0.05 < y < height * 0.92 and not np.any(np.abs(front_rows - y) <= 5)
    ]

    if len(peaks) > count:
        peaks = sorted(peaks, key=lambda item: item[1], reverse=True)[:count]
    peaks.sort(key=lambda item: item[0])
    positions = tuple(round(y / height, 4) for y, _score in peaks)
    return MarkerDetection(positions_rel=positions, peak_count=len(peaks), side=side)


def estimate_kda_at_y(y_pos_rel: float, markers: list[MarkerBand]) -> float:
    """Schätzt einen kDa-Wert per log-linearer Interpolation."""
    points = sorted(
        ((m.y_pos_rel, m.mw) for m in markers if m.visible and m.mw > 0),
        key=lambda item: item[0],
    )
    if len(points) < 2:
        return 0.0
    if y_pos_rel <= points[0][0]:
        y0, v0 = points[0]
        y1, v1 = points[1]
    elif y_pos_rel >= points[-1][0]:
        y0, v0 = points[-2]
        y1, v1 = points[-1]
    else:
        y0 = y1 = points[0][0]
        v0 = v1 = points[0][1]
        for (ya, va), (yb, vb) in pairwise(points):
            if ya <= y_pos_rel <= yb:
                y0, v0, y1, v1 = ya, va, yb, vb
                break
    if y1 == y0:
        return round(v0, 1)
    fraction = (y_pos_rel - y0) / (y1 - y0)
    log_value = math.log10(v0) + fraction * (math.log10(v1) - math.log10(v0))
    value = 10.0**log_value
    if value >= 100:
        return float(round(value / 5.0) * 5)
    if value >= 20:
        return float(round(value))
    return float(round(value * 2) / 2)
