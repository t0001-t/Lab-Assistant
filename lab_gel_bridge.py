"""Deterministic bridge from notebook text to a GelDoc project.

The bridge deliberately does not call an AI service. It reads the lane maps and
pipetting tables that are already present in an experiment note, assigns the
labels to evenly spaced lanes, and leaves the ordinary gel editor in charge of
the image. Every change is reproducible and can be reviewed in the editor.
"""

from __future__ import annotations

import itertools
import math
import re
from dataclasses import dataclass, field

from PIL import Image

from models import ConditionRow, Project, TargetArrow, default_project

_LANE_WORDS = ("spur", "lane", "gleis", "track", "nummer", "nr", "#")
_LABEL_WORDS = ("probe", "sample", "auftrag", "bezeichnung", "label", "name")
_CONDITION_WORDS = (
    "bedingung",
    "condition",
    "temperatur",
    "temperature",
    "puffer",
    "buffer",
    "behandlung",
    "treatment",
)
_MARKER_WORDS = ("marker", "leiter", "ladder", "molekulargewichtsmarker")
_TARGET_WORDS = ("zielbande", "zielband", "target band", "target", "bande")
_LANE_LINE = re.compile(
    r"^\s*(?:spur|lane|gleis|track)\s*(\d+)\s*[:\-–]\s*(.+?)\s*$", re.IGNORECASE
)
_PROBE_LINE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*(.+?)\s*$")
_TARGET_LINE = re.compile(
    r"(?:zielbande|zielband|target(?:\s*band)?|bande)\s*[:\-]?\s*"
    r"(?:~|ca\.?|approx\.?)?\s*(\d+(?:[.,]\d+)?)\s*(kda|da)?",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"^\s*(\d+)\s*$")


@dataclass(frozen=True)
class LaneSpec:
    """One lane parsed from a note."""

    index: int
    label: str
    condition: str = ""
    marker: bool = False


@dataclass
class GelAnnotation:
    """Result of parsing a free-text note or pipetting table."""

    lanes: list[LaneSpec] = field(default_factory=list)
    targets: list[tuple[float, str]] = field(default_factory=list)
    source_lines: list[str] = field(default_factory=list)

    @property
    def lane_count(self) -> int:
        if not self.lanes:
            return 0
        return max(spec.index for spec in self.lanes)

    @property
    def marker_lanes(self) -> list[int]:
        return [spec.index for spec in self.lanes if spec.marker]

    @property
    def fully_empty(self) -> bool:
        return not self.lanes and not self.targets


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(
        cell and set(cell) <= {"-", ":", " "} for cell in cells
    )


def _index_of(cells: list[str], words: tuple[str, ...]) -> int | None:
    for position, cell in enumerate(cells):
        lowered = cell.lower().strip("*_ ")
        if any(word in lowered for word in words):
            return position
    return None


def _integer(value: str) -> int | None:
    match = _NUMBER.match(value)
    if match:
        return int(match.group(1))
    lane_match = re.search(r"\b(?:spur|lane|gleis|track)\s*(\d+)", value, re.IGNORECASE)
    return int(lane_match.group(1)) if lane_match else None


def _marker_lane(label: str) -> bool:
    lowered = label.lower()
    if lowered in {"m", "marker", "ladder", "leiter"}:
        return True
    return any(word in lowered for word in _MARKER_WORDS)


def _store_lane(lanes: dict[int, LaneSpec], spec: LaneSpec) -> None:
    if spec.index < 1 or not spec.label:
        return
    current = lanes.get(spec.index)
    if current is None or (not current.label and spec.label):
        lanes[spec.index] = spec


def _table_block(lines: list[str], lanes: dict[int, LaneSpec]) -> None:
    rows = [row for row in (_cells(line) for line in lines) if row]
    rows = [row for row in rows if not _is_separator(row)]
    if not rows:
        return
    header = rows[0] if any(
        "|" in line for line in lines[:1]
    ) else []
    # A table header is only used when it names at least one lane-related
    # column; otherwise a data table would be mistaken for a lane map.
    lane_col = _index_of(header, _LANE_WORDS) if header else None
    label_col = _index_of(header, _LABEL_WORDS) if header else None
    condition_col = _index_of(header, _CONDITION_WORDS) if header else None
    has_header = lane_col is not None or label_col is not None
    data = rows[1:] if has_header else rows
    for row in data:
        cells = list(row)
        index: int | None = None
        if lane_col is not None and lane_col < len(cells):
            index = _integer(cells[lane_col])
        if index is None and cells:
            index = _integer(cells[0])
            if index is not None:
                label_position = 1
            else:
                label_position = 0
        elif index is not None and cells:
            label_position = label_col if label_col is not None else 1
        else:
            continue
        if index is None:
            continue
        if label_col is not None and label_col < len(cells) and label_col != lane_col:
            label = cells[label_col]
        elif label_position < len(cells):
            label = cells[label_position]
        else:
            label = ""
        if not label and label_position < len(cells):
            label = cells[label_position]
        condition = ""
        if condition_col is not None and condition_col < len(cells):
            condition = cells[condition_col]
        elif label_position + 1 < len(cells):
            condition = cells[label_position + 1]
        _store_lane(
            lanes,
            LaneSpec(
                index=index,
                label=label.strip(),
                condition=condition.strip(),
                marker=_marker_lane(label),
            ),
        )


def _parse_lane_lines(lines: list[str], lanes: dict[int, LaneSpec]) -> None:
    for line in lines:
        match = _LANE_LINE.match(line)
        if not match:
            continue
        index = int(match.group(1))
        rest = match.group(2).strip()
        pieces = re.split(r"\s*[|;]\s*", rest, maxsplit=1)
        label = pieces[0].strip()
        condition = pieces[1].strip() if len(pieces) > 1 else ""
        _store_lane(
            lanes,
            LaneSpec(index=index, label=label, condition=condition,
                     marker=_marker_lane(label)),
        )


def _parse_probe_lines(lines: list[str], lanes: dict[int, LaneSpec]) -> None:
    """Use bullet lists as a last resort when no lane table exists."""
    if lanes:
        return
    next_index = 1
    for line in lines:
        match = _PROBE_LINE.match(line)
        if not match or "|" in line:
            continue
        text = match.group(1).strip()
        if not any(word in text.lower() for word in ("probe", "sample", "marker", "leiter")):
            continue
        if "µl" in text.lower() or "ul" in text.lower() or len(text) > 70:
            continue
        pieces = re.split(r"\s*[;:]\s*", text, maxsplit=1)
        label = pieces[0].strip()
        condition = pieces[1].strip() if len(pieces) > 1 else ""
        _store_lane(
            lanes,
            LaneSpec(index=next_index, label=label, condition=condition,
                     marker=_marker_lane(label)),
        )
        next_index += 1
        if next_index > 24:
            break


def parse_notes(text: str) -> GelAnnotation:
    """Extract lanes, conditions and target bands from a note string."""
    lines = text.splitlines()
    lanes: dict[int, LaneSpec] = {}
    block: list[str] = []
    for line in lines + [""]:
        if "|" in line:
            block.append(line)
            continue
        if block:
            _table_block(block, lanes)
            block = []
    _parse_lane_lines(lines, lanes)
    _parse_probe_lines(lines, lanes)
    targets: list[tuple[float, str]] = []
    for line in lines:
        for match in _TARGET_LINE.finditer(line):
            lowered = line.lower()
            if not any(word in lowered for word in _TARGET_WORDS):
                continue
            value = float(match.group(1).replace(",", "."))
            unit = (match.group(2) or "kDa").strip()
            if unit.lower() == "da":
                unit = "Da"
            targets.append((value, unit))
    # Keep the report compact and avoid duplicate values.
    unique: list[tuple[float, str]] = []
    for value, unit in targets:
        if (value, unit) not in unique:
            unique.append((value, unit))
    return GelAnnotation(
        lanes=[lanes[index] for index in sorted(lanes)],
        targets=unique[:8],
        source_lines=[line.strip() for line in lines if line.strip()],
    )


def _y_for_mw(project: Project, mw: float) -> float:
    """Invert the panel ladder so a target value gets a sensible y position."""
    panel = project.panels[0]
    points = sorted(
        ((marker.y_pos_rel, marker.mw) for marker in panel.markers
         if marker.visible and marker.mw > 0),
        key=lambda item: item[1],
    )
    if len(points) < 2 or mw <= 0:
        return 0.5
    if mw <= points[0][1]:
        return points[0][0]
    if mw >= points[-1][1]:
        return points[-1][0]
    for (y_low, mw_low), (y_high, mw_high) in itertools.pairwise(points):
        if mw_low <= mw <= mw_high:
            fraction = (math.log10(mw) - math.log10(mw_low)) / (
                math.log10(mw_high) - math.log10(mw_low)
            )
            return round(y_low + fraction * (y_high - y_low), 6)
    return 0.5


def build_project(
    annotation: GelAnnotation,
    image: Image.Image,
    *,
    lang: str = "de",
    name: str = "Gel aus Notizen",
    source_name: str = "",
) -> tuple[Project, dict[str, object]]:
    """Build a ready-to-edit GelDoc project from parsed notes and a gel image."""
    lane_count = max(annotation.lane_count, 1) if annotation.lanes else 10
    lane_count = min(lane_count, 24)
    project = default_project(lane_count)
    panel = project.panels[0]
    fallback = "Gel aus Notizen" if lang == "de" else "Gel from notes"
    project.lang = lang if lang in {"de", "en"} else "de"
    panel.source_image = image.convert("RGB")
    panel.source_name = source_name or name
    panel.name = "A"
    project.name = name or fallback
    if annotation.targets:
        panel.unit = annotation.targets[0][1]

    try:
        import image_processing as ip

        detection = ip.detect_lanes(panel.source_image, lane_count)
        for lane, position in zip(panel.lanes, detection.positions_rel, strict=False):
            lane.x_pos_rel = float(position)
    except (ValueError, RuntimeError):
        # Lane detection is an optional improvement; the even default grid is
        # still a valid starting point when the image profile is unusable.
        detection = None

    labels = {spec.index: spec for spec in annotation.lanes}
    for position, lane in enumerate(panel.lanes, start=1):
        spec = labels.get(position)
        lane.label_top = spec.label if spec and spec.label else str(position)
        if spec and spec.marker:
            lane.label_bottom = "Marker"
    marker_lanes = [index - 1 for index in annotation.marker_lanes if 1 <= index <= lane_count]
    panel.marker_lane_indexes = marker_lanes or [0]

    conditions = [labels[index].condition if index in labels else "" for index in range(1, lane_count + 1)]
    if any(conditions):
        label = "Bedingung" if project.lang == "de" else "Condition"
        panel.conditions = [ConditionRow(name=label, values=conditions)]

    arrows: list[TargetArrow] = []
    for value, unit in annotation.targets:
        mw = value * 1000.0 if unit == "Da" else value
        arrows.append(
            TargetArrow(
                label=f"{value:g} {unit}",
                y_pos_rel=_y_for_mw(project, mw),
                side="right",
            )
        )
    panel.arrows = arrows

    report: dict[str, object] = {
        "lane_count": lane_count,
        "labeled": sum(1 for spec in annotation.lanes if spec.label),
        "conditions": sum(1 for value in conditions if value),
        "marker_lanes": len(panel.marker_lane_indexes),
        "targets": len(arrows),
        "has_note_lanes": bool(annotation.lanes),
    }
    return project, report
