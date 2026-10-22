"""Tests der reinen Workflow-Logik (Editor-Ereignisse, Spuren-/Zielverwaltung)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from models import ConditionRow, default_project
from workflow import (
    apply_editor_event,
    distribute_lanes,
    insert_lane,
    remove_lane,
    renumber_lanes,
    reset_markers,
    visible_arrows,
    visible_markers,
)


class LaneWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.panel = default_project().panels[0]

    def test_insert_lane_keeps_sorted_order_and_labels(self) -> None:
        index = insert_lane(self.panel, 0.315)
        self.assertEqual(len(self.panel.lanes), 11)
        xs = [lane.x_pos_rel for lane in self.panel.lanes]
        self.assertEqual(xs, sorted(xs))
        self.assertEqual(self.panel.lanes[index].label_top, "11")
        self.assertAlmostEqual(self.panel.lanes[index].x_pos_rel, 0.315)

    def test_insert_lane_tracks_marker_lane_objects(self) -> None:
        self.panel.marker_lane_indexes = [0, 9]
        labels = [self.panel.lanes[0].label_top, self.panel.lanes[9].label_top]
        insert_lane(self.panel, 0.008)
        tracked = [self.panel.lanes[i].label_top for i in self.panel.marker_lane_indexes]
        self.assertEqual(tracked, labels)
        self.assertEqual(self.panel.marker_lane_indexes, [1, 10])

    def test_insert_lane_shifts_condition_values(self) -> None:
        self.panel.conditions = [ConditionRow(name="DTT", values=[str(i) for i in range(10)])]
        index = insert_lane(self.panel, 0.0)
        values = self.panel.conditions[0].values
        self.assertEqual(len(values), 11)
        self.assertEqual(values[index], "")
        self.assertEqual(values[index + 1], "0")

    def test_remove_lane_keeps_marker_mapping_and_conditions(self) -> None:
        self.panel.marker_lane_indexes = [0, 9]
        self.panel.conditions = [ConditionRow(name="DTT", values=[str(i) for i in range(10)])]
        remove_lane(self.panel, 0)
        self.assertEqual(len(self.panel.lanes), 9)
        self.assertEqual(self.panel.marker_lane_indexes, [8])
        self.assertEqual(self.panel.conditions[0].values, [str(i) for i in range(1, 10)])

    def test_last_lane_cannot_be_removed(self) -> None:
        panel = default_project(1).panels[0]
        self.assertFalse(remove_lane(panel, 0))
        self.assertEqual(len(panel.lanes), 1)

    def test_lane_drag_event_updates_positions(self) -> None:
        values = [round(0.02 + i * 0.09, 4) for i in range(10)]
        outcome = apply_editor_event(self.panel, {"event": "lanes", "lanes": values})
        self.assertTrue(outcome.changed)
        self.assertEqual([round(l.x_pos_rel, 4) for l in self.panel.lanes], values)

    def test_lane_drag_with_wrong_length_is_ignored(self) -> None:
        original = [lane.x_pos_rel for lane in self.panel.lanes]
        outcome = apply_editor_event(self.panel, {"event": "lanes", "lanes": [0.1, 0.2]})
        self.assertFalse(outcome.changed)
        self.assertEqual([lane.x_pos_rel for lane in self.panel.lanes], original)

    def test_lane_positions_are_clamped(self) -> None:
        values = [-0.5] + [0.5] * 8 + [5.0]
        apply_editor_event(self.panel, {"event": "lanes", "lanes": values})
        self.assertEqual(self.panel.lanes[0].x_pos_rel, 0.0)
        self.assertEqual(self.panel.lanes[-1].x_pos_rel, 1.0)

    def test_add_and_delete_lane_events(self) -> None:
        outcome = apply_editor_event(self.panel, {"event": "add_lane", "x_pos_rel": 0.58})
        self.assertTrue(outcome.changed)
        self.assertEqual(len(self.panel.lanes), 11)
        outcome = apply_editor_event(self.panel, {"event": "delete_lane", "index": outcome.selected_lane})
        self.assertTrue(outcome.changed)
        self.assertEqual(len(self.panel.lanes), 10)

    def test_select_lane_event_clamps_index(self) -> None:
        outcome = apply_editor_event(self.panel, {"event": "select_lane", "index": 99})
        self.assertEqual(outcome.selected_lane, 9)
        self.assertTrue(outcome.rerun)
        self.assertFalse(outcome.changed)

    def test_distribute_and_renumber(self) -> None:
        distribute_lanes(self.panel)
        self.assertAlmostEqual(self.panel.lanes[0].x_pos_rel, 0.05)
        renumber_lanes(self.panel)
        self.assertEqual(self.panel.lanes[0].label_top, "1")


class MarkerWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.panel = default_project().panels[0]

    def test_marker_drag_updates_y_values(self) -> None:
        values = [round(0.10 + i * 0.08, 4) for i in range(9)]
        outcome = apply_editor_event(self.panel, {"event": "markers", "markers": values})
        self.assertTrue(outcome.changed)
        self.assertTrue(outcome.ui_bump)
        self.assertEqual([round(m.y_pos_rel, 4) for m in visible_markers(self.panel)], values)

    def test_hidden_markers_are_not_dragged(self) -> None:
        self.panel.markers[0].visible = False
        values = [round(0.20 + i * 0.05, 4) for i in range(8)]
        apply_editor_event(self.panel, {"event": "markers", "markers": values})
        self.assertAlmostEqual(self.panel.markers[0].y_pos_rel, 0.136)
        self.assertEqual(len(visible_markers(self.panel)), 8)

    def test_add_marker_estimates_mw_from_neighbours(self) -> None:
        outcome = apply_editor_event(self.panel, {"event": "add_marker", "y_pos_rel": 0.57})
        self.assertTrue(outcome.changed)
        added = visible_markers(self.panel)[outcome.selected_marker]
        self.assertAlmostEqual(added.y_pos_rel, 0.57)
        self.assertGreater(added.mw, 30.0)
        self.assertLess(added.mw, 55.0)

    def test_delete_marker_event_keeps_rest(self) -> None:
        before = len(self.panel.markers)
        apply_editor_event(self.panel, {"event": "delete_marker", "index": 0})
        self.assertEqual(len(self.panel.markers), before - 1)

    def test_select_marker_event(self) -> None:
        outcome = apply_editor_event(self.panel, {"event": "select_marker", "index": 3})
        self.assertEqual(outcome.selected_marker, 3)
        self.assertFalse(outcome.changed)

    def test_reset_markers_restores_reference_ladder(self) -> None:
        reset_markers(self.panel)
        self.assertEqual(
            [m.display_value for m in self.panel.markers],
            ["170", "130", "100", "70", "55", "40", "35", "25", "10"],
        )


class ArrowWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.panel = default_project().panels[0]

    def test_add_arrow_event(self) -> None:
        outcome = apply_editor_event(self.panel, {"event": "add_arrow", "y_pos_rel": 0.42, "side": "left"})
        self.assertTrue(outcome.changed)
        self.assertEqual(len(self.panel.arrows), 1)
        self.assertEqual(self.panel.arrows[0].side, "left")
        self.assertAlmostEqual(self.panel.arrows[0].y_pos_rel, 0.42)

    def test_arrow_drag_event(self) -> None:
        apply_editor_event(self.panel, {"event": "add_arrow", "y_pos_rel": 0.4, "side": "right"})
        apply_editor_event(self.panel, {"event": "add_arrow", "y_pos_rel": 0.6, "side": "right"})
        values = [0.25, 0.75]
        outcome = apply_editor_event(self.panel, {"event": "arrows", "arrows": values})
        self.assertTrue(outcome.changed)
        self.assertTrue(outcome.ui_bump)
        self.assertEqual([round(a.y_pos_rel, 4) for a in visible_arrows(self.panel)], values)

    def test_delete_and_select_arrow(self) -> None:
        apply_editor_event(self.panel, {"event": "add_arrow", "y_pos_rel": 0.4, "side": "right"})
        outcome = apply_editor_event(self.panel, {"event": "select_arrow", "index": 5})
        self.assertEqual(outcome.selected_arrow, 0)
        outcome = apply_editor_event(self.panel, {"event": "delete_arrow", "index": 0})
        self.assertTrue(outcome.changed)
        self.assertEqual(len(self.panel.arrows), 0)


class CornerWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.panel = default_project().panels[0]

    def test_corners_event_sets_perspective(self) -> None:
        corners = [[0.1, 0.1], [0.9, 0.05], [0.95, 0.95], [0.05, 0.9]]
        outcome = apply_editor_event(self.panel, {"event": "corners", "corners": corners})
        self.assertTrue(outcome.changed)
        self.assertEqual(self.panel.transform.perspective, corners)
        self.assertFalse(self.panel.transform.is_identity)

    def test_wrong_corner_count_is_ignored(self) -> None:
        original = [list(p) for p in self.panel.transform.perspective]
        outcome = apply_editor_event(self.panel, {"event": "corners", "corners": [[0, 0]]})
        self.assertFalse(outcome.changed)
        self.assertEqual(self.panel.transform.perspective, original)


class MiscWorkflowTest(unittest.TestCase):
    def test_unknown_event_is_noop(self) -> None:
        outcome = apply_editor_event(default_project().panels[0], {"event": "zoom", "factor": 2})
        self.assertFalse(outcome.changed)
        self.assertFalse(outcome.rerun)
        self.assertIsNone(outcome.selected_lane)

    def test_none_result_is_noop(self) -> None:
        self.assertFalse(apply_editor_event(default_project().panels[0], None).changed)


if __name__ == "__main__":
    unittest.main()
