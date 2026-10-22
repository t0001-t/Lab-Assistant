"""Reine Workflow-Logik (ohne Streamlit-Abhängigkeit).

Alle Funktionen arbeiten direkt auf einem :class:`models.GelPanel` und
sind damit unabhängig von der UI testbar. Nachrichten werden als
Übersetzungsschlüssel (``message_key``) zurückgegeben und erst in der UI
lokalisiert.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models import (
    ConditionRow,
    GelPanel,
    GroupLabel,
    Lane,
    MarkerBand,
    TargetArrow,
    clamp,
)


@dataclass
class EditorOutcome:
    """Ergebnis der Verarbeitung eines Editor-Ereignisses."""

    changed: bool = False
    rerun: bool = False
    selected_lane: int | None = None
    selected_marker: int | None = None
    selected_arrow: int | None = None
    ui_bump: bool = False
    message_key: str = ""
    message_args: dict[str, Any] = field(default_factory=dict)


def visible_markers(panel: GelPanel) -> list[MarkerBand]:
    """Sichtbare Marker, von oben nach unten sortiert."""
    return panel.sorted_markers()


def visible_arrows(panel: GelPanel) -> list[TargetArrow]:
    return panel.visible_arrows()


def index_of_identity(items: list, target: object) -> int:
    """Index über Objektidentität (robust gegen Wert-Duplikate)."""
    for index, item in enumerate(items):
        if item is target:
            return index
    return 0


def next_lane_label(panel: GelPanel) -> str:
    numeric = [int(lane.label_top) for lane in panel.lanes if lane.label_top.isdigit()]
    if numeric and len(numeric) == len(panel.lanes):
        return str(max(numeric) + 1)
    return str(len(panel.lanes) + 1)


def _sync_condition_lengths(panel: GelPanel) -> None:
    count = len(panel.lanes)
    for condition in panel.conditions:
        values = list(condition.values)
        if len(values) < count:
            values += [""] * (count - len(values))
        condition.values = values[:count]


def insert_lane(panel: GelPanel, x_pos_rel: float) -> int:
    """Fügt eine Spur ein und liefert ihren Index in ``panel.lanes``."""
    marker_objects = [
        panel.lanes[i] for i in panel.marker_lane_indexes if 0 <= i < len(panel.lanes)
    ]
    new_lane = Lane(x_pos_rel=float(clamp(x_pos_rel, 0.0, 1.0)), label_top=next_lane_label(panel))
    panel.lanes.append(new_lane)
    panel.lanes.sort(key=lambda lane: lane.x_pos_rel)
    new_index = index_of_identity(panel.lanes, new_lane)

    for condition in panel.conditions:
        values = list(condition.values)
        while len(values) < len(panel.lanes) - 1:
            values.append("")
        values.insert(min(new_index, len(values)), "")
        condition.values = values[: len(panel.lanes)]

    panel.marker_lane_indexes = [
        index
        for index, lane in enumerate(panel.lanes)
        if any(lane is marker_lane for marker_lane in marker_objects)
    ]
    return new_index


def remove_lane(panel: GelPanel, index: int) -> bool:
    """Entfernt eine Spur; mindestens eine Spur bleibt erhalten."""
    if len(panel.lanes) <= 1 or not (0 <= index < len(panel.lanes)):
        return False
    marker_objects = [
        panel.lanes[i] for i in panel.marker_lane_indexes if 0 <= i < len(panel.lanes)
    ]
    panel.lanes.pop(index)

    for condition in panel.conditions:
        values = list(condition.values)
        if 0 <= index < len(values):
            values.pop(index)
        condition.values = values

    panel.marker_lane_indexes = [
        new_index
        for new_index, lane in enumerate(panel.lanes)
        if any(lane is marker_lane for marker_lane in marker_objects)
    ]
    last = len(panel.lanes) - 1
    for group in panel.groups:
        group.start_index = min(group.start_index, last)
        group.end_index = min(group.end_index, last)
    return True


def renumber_lanes(panel: GelPanel) -> None:
    for index, lane in enumerate(panel.lanes):
        lane.label_top = str(index + 1)


def distribute_lanes(panel: GelPanel) -> None:
    count = len(panel.lanes)
    for index, lane in enumerate(panel.lanes):
        lane.x_pos_rel = round((index + 0.5) / count, 6)


def reset_markers(panel: GelPanel) -> None:
    from models import default_markers

    panel.markers = default_markers()


def set_lane_count(panel: GelPanel, count: int) -> None:
    """Legt genau ``count`` Spuren an und verteilt sie gleichmäßig.

    Vorhandene Beschriftungen bleiben erhalten: fehlende Spuren kommen leer
    dazu, überzählige werden am Ende entfernt. Anschließend lassen sich alle
    Spuren wie gewohnt im Editor verschieben.
    """
    count = max(1, int(count))
    lanes = list(panel.lanes)
    if count < len(lanes):
        lanes = lanes[:count]
    while len(lanes) < count:
        lanes.append(Lane(index=len(lanes)))
    panel.lanes = lanes
    distribute_lanes(panel)


def set_marker_count(panel: GelPanel, count: int) -> None:
    """Legt genau ``count`` Marker an und verteilt sie gleichmäßig.

    Bleibt die Anzahl gleich, werden nur die Y-Positionen verteilt. Ändert sie
    sich, entsteht eine neue Leiter mit log-interpolierten Werten zwischen dem
    bisherigen obersten und untersten Marker (sonst 170 bis 10).
    """
    count = max(1, int(count))
    markers = sorted(panel.markers, key=lambda item: item.y_pos_rel)
    values = [m.mw for m in markers if m.mw > 0] or [170.0]
    top = max(values)
    bottom = min(values) if len(values) > 1 else top / 17.0
    if bottom <= 0 or bottom >= top:
        top, bottom = 170.0, 10.0

    if count != len(markers):
        markers = [
            MarkerBand(
                mw=round(top * (bottom / top) ** (index / (count - 1)), 2) if count > 1 else top,
                unit=panel.unit,
            )
            for index in range(count)
        ]

    lo, hi = 0.14, 0.85
    if len(markers) >= 2:
        lo, hi = markers[0].y_pos_rel, markers[-1].y_pos_rel
        if hi - lo < 0.2:
            lo, hi = 0.14, 0.85

    for index, marker in enumerate(markers):
        frac = index / (len(markers) - 1) if len(markers) > 1 else 0.5
        marker.y_pos_rel = round(lo + (hi - lo) * frac, 6)
        marker.visible = True
    panel.markers = markers


# ----------------------------------------------------------------------
# Editor-Ereignisse
# ----------------------------------------------------------------------
def apply_editor_event(panel: GelPanel, result: dict[str, Any] | None) -> EditorOutcome:
    """Übersetzt ein Editor-Ereignis in Änderungen am Panel."""
    outcome = EditorOutcome()
    if not result or not isinstance(result, dict):
        return outcome

    event = result.get("event")

    if event == "lanes":
        values = list(result.get("lanes", []))
        if len(values) == len(panel.lanes):
            for lane, value in zip(panel.lanes, values, strict=False):
                lane.x_pos_rel = float(clamp(float(value), 0.0, 1.0))
            outcome.changed = outcome.rerun = True
        return outcome

    if event == "markers":
        markers = visible_markers(panel)
        values = list(result.get("markers", []))
        if len(values) == len(markers):
            for marker, value in zip(markers, values, strict=False):
                marker.y_pos_rel = float(clamp(float(value), 0.0, 1.0))
            outcome.changed = outcome.rerun = outcome.ui_bump = True
        return outcome

    if event == "arrows":
        arrows = visible_arrows(panel)
        values = list(result.get("arrows", []))
        if len(values) == len(arrows):
            for arrow, value in zip(arrows, values, strict=False):
                arrow.y_pos_rel = float(clamp(float(value), 0.0, 1.0))
            # UI-Version erhöhen, damit der Y-Regler den neuen Wert übernimmt
            # und die Verschiebung nicht sofort zurückschreibt.
            outcome.changed = outcome.rerun = outcome.ui_bump = True
        return outcome

    if event == "corners":
        corners = result.get("corners", [])
        if isinstance(corners, (list, tuple)) and len(corners) == 4:
            panel.transform.perspective = [
                [float(clamp(float(point[0]), 0.0, 1.0)), float(clamp(float(point[1]), 0.0, 1.0))]
                for point in corners
            ]
            outcome.changed = outcome.rerun = True
        return outcome

    if event == "add_lane":
        x_pos_rel = float(clamp(float(result.get("x_pos_rel", 0.5)), 0.0, 1.0))
        outcome.selected_lane = insert_lane(panel, x_pos_rel)
        outcome.changed = outcome.rerun = True
        outcome.message_key = "msg_lane_inserted"
        outcome.message_args = {"index": outcome.selected_lane + 1}
        return outcome

    if event == "delete_lane":
        index = int(result.get("index", 0))
        if remove_lane(panel, index):
            outcome.selected_lane = max(0, min(index, len(panel.lanes) - 1))
            outcome.changed = outcome.rerun = True
            outcome.message_key = "msg_lane_deleted"
        return outcome

    if event == "select_lane":
        outcome.selected_lane = int(clamp(int(result.get("index", 0)), 0, len(panel.lanes) - 1))
        outcome.rerun = True
        return outcome

    if event == "add_marker":
        y_pos_rel = float(clamp(float(result.get("y_pos_rel", 0.5)), 0.0, 1.0))
        value = panel.marker_mw_at(y_pos_rel) or 50.0
        new_marker = MarkerBand(mw=value, y_pos_rel=y_pos_rel)
        panel.markers.append(new_marker)
        panel.markers.sort(key=lambda item: item.y_pos_rel)
        outcome.selected_marker = index_of_identity(visible_markers(panel), new_marker)
        outcome.changed = outcome.rerun = outcome.ui_bump = True
        outcome.message_key = "msg_marker_added"
        outcome.message_args = {"value": new_marker.display_value}
        return outcome

    if event == "delete_marker":
        markers = visible_markers(panel)
        index = int(result.get("index", 0))
        if 0 <= index < len(markers):
            panel.markers.remove(markers[index])
            outcome.selected_marker = max(0, min(index, len(markers) - 2))
            outcome.changed = outcome.rerun = outcome.ui_bump = True
            outcome.message_key = "msg_marker_removed"
        return outcome

    if event == "select_marker":
        count = len(visible_markers(panel))
        outcome.selected_marker = int(clamp(int(result.get("index", 0)), 0, max(0, count - 1)))
        outcome.rerun = True
        return outcome

    if event == "add_arrow":
        y_pos_rel = float(clamp(float(result.get("y_pos_rel", 0.5)), 0.0, 1.0))
        side = "left" if result.get("side") == "left" else "right"
        new_arrow = TargetArrow(label="", y_pos_rel=y_pos_rel, side=side)
        panel.arrows.append(new_arrow)
        outcome.selected_arrow = index_of_identity(visible_arrows(panel), new_arrow)
        outcome.changed = outcome.rerun = True
        outcome.message_key = "msg_arrow_added"
        return outcome

    if event == "delete_arrow":
        arrows = visible_arrows(panel)
        index = int(result.get("index", 0))
        if 0 <= index < len(arrows):
            panel.arrows.remove(arrows[index])
            outcome.selected_arrow = max(0, min(index, len(arrows) - 2))
            outcome.changed = outcome.rerun = True
            outcome.message_key = "msg_arrow_removed"
        return outcome

    if event == "select_arrow":
        count = len(visible_arrows(panel))
        outcome.selected_arrow = int(clamp(int(result.get("index", 0)), 0, max(0, count - 1)))
        outcome.rerun = True
        return outcome

    return outcome


__all__ = [
    "ConditionRow",
    "EditorOutcome",
    "GroupLabel",
    "_sync_condition_lengths",
    "apply_editor_event",
    "distribute_lanes",
    "index_of_identity",
    "insert_lane",
    "next_lane_label",
    "remove_lane",
    "renumber_lanes",
    "reset_markers",
    "visible_arrows",
    "visible_markers",
]
