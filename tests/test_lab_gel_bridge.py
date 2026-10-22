"""Tests for the deterministic notes-to-gel bridge."""

from __future__ import annotations

import unittest

from PIL import Image

from lab_gel_bridge import build_project, parse_notes


class GelBridgeTests(unittest.TestCase):
    def test_markdown_lane_table_and_target(self) -> None:
        annotation = parse_notes(
            "# SDS-PAGE\n\n"
            "| Spur | Probe | Bedingung |\n"
            "| --- | --- | --- |\n"
            "| 1 | Marker | |\n"
            "| 2 | Probe A | 37 °C |\n"
            "| 3 | Probe B | 42 °C |\n\n"
            "Zielbande: ~55 kDa\n"
        )
        self.assertEqual(annotation.lane_count, 3)
        self.assertEqual([spec.label for spec in annotation.lanes],
                         ["Marker", "Probe A", "Probe B"])
        self.assertEqual(annotation.marker_lanes, [1])
        self.assertEqual(annotation.targets, [(55.0, "kDa")])

    def test_lane_lines_and_bullet_fallback(self) -> None:
        annotation = parse_notes(
            "Spur 1: Marker\n"
            "Spur 2: Probe A; 37 °C\n"
            "Spur 3: Probe B\n"
        )
        self.assertEqual(annotation.lane_count, 3)
        self.assertEqual(annotation.lanes[1].condition, "37 °C")
        fallback = parse_notes("- Probe A\n- Probe B\n- Marker\n")
        self.assertEqual(fallback.lane_count, 3)
        self.assertEqual(fallback.marker_lanes, [3])

    def test_build_project_assigns_labels_conditions_and_arrow(self) -> None:
        annotation = parse_notes(
            "| Spur | Probe | Bedingung |\n"
            "| --- | --- | --- |\n"
            "| 1 | Marker | |\n"
            "| 2 | Probe A | 37 °C |\n"
            "| 3 | Probe B | 42 °C |\n"
            "Zielbande: 55 kDa\n"
        )
        image = Image.new("RGB", (240, 240), "white")
        project, report = build_project(annotation, image, lang="en", name="V1")
        panel = project.panels[0]
        self.assertEqual(project.lang, "en")
        self.assertEqual(panel.source_image.size, (240, 240))
        self.assertEqual(len(panel.lanes), 3)
        self.assertEqual(panel.lanes[1].label_top, "Probe A")
        self.assertEqual(panel.marker_lane_indexes, [0])
        self.assertEqual(panel.conditions[0].values, ["", "37 °C", "42 °C"])
        self.assertEqual(panel.arrows[0].label, "55 kDa")
        self.assertGreaterEqual(panel.arrows[0].y_pos_rel, 0.0)
        self.assertLessEqual(panel.arrows[0].y_pos_rel, 1.0)
        self.assertEqual(report["targets"], 1)
        self.assertEqual(report["labeled"], 3)

    def test_empty_prose_still_opens_editable_default_grid(self) -> None:
        annotation = parse_notes("Nur ein kurzer Freitext ohne Spurangaben.")
        image = Image.new("RGB", (100, 100), "white")
        project, report = build_project(annotation, image)
        self.assertEqual(len(project.panels[0].lanes), 10)
        self.assertEqual(report["has_note_lanes"], False)


if __name__ == "__main__":
    unittest.main()
