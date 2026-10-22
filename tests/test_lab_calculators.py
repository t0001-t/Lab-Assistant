"""Boundary tests for the unit-aware calculator functions."""

from __future__ import annotations

import unittest

from lab_calculators import (
    convert_unit,
    dilution,
    mastermix,
    molarity,
    neubauer,
    positive,
    qpcr,
)


class NeubauerTests(unittest.TestCase):
    def test_counts_totals_and_seeding(self) -> None:
        result = neubauer([100, 120, 80, 100], [10, 10, 10, 10], 2, 3,
                          target_cells=200_000, target_concentration_per_ml=500_000)
        self.assertEqual(result.live_per_ml, 2_000_000)
        self.assertEqual(result.dead_per_ml, 200_000)
        self.assertEqual(result.total_per_ml, 2_200_000)
        self.assertEqual(result.total_cells_in_suspension, 6_600_000)
        self.assertEqual(result.total_dead_cells, 600_000)
        self.assertAlmostEqual(result.viability_percent, 1000 / 11)
        self.assertAlmostEqual(result.stock_volume_ml, 0.1)
        self.assertAlmostEqual(result.medium_volume_ml, 0.3)

    def test_without_dead_cells_and_without_target(self) -> None:
        result = neubauer([20], None, 1, 1)
        self.assertIsNone(result.viability_percent)
        self.assertIsNone(result.stock_volume_ml)
        self.assertEqual(result.live_per_ml, 200_000)
        self.assertEqual(result.total_live_cells, 200_000)

    def test_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            neubauer([], None, 1, 1)
        with self.assertRaises(ValueError):
            neubauer([1], [1, 2], 1, 1)
        with self.assertRaises(ValueError):
            neubauer([0], None, 1, 1, target_cells=100)
        with self.assertRaises(ValueError):
            neubauer([10], [0], 1, 1, target_cells=100_000,
                     target_concentration_per_ml=10_000_000)

    def test_dead_only_viability_is_zero(self) -> None:
        result = neubauer([0], [10], 1, 1)
        self.assertEqual(result.viability_percent, 0)


class MolarityTests(unittest.TestCase):
    def test_all_unknowns(self) -> None:
        self.assertAlmostEqual(molarity(solve="m", concentration_mol_l=.1,
                                        volume_l=.01, molar_mass_g_mol=100), .1)
        self.assertAlmostEqual(molarity(solve="c", mass_g=.1,
                                        volume_l=.01, molar_mass_g_mol=100), .1)
        self.assertAlmostEqual(molarity(solve="V", mass_g=.1,
                                        concentration_mol_l=.1, molar_mass_g_mol=100), .01)
        self.assertAlmostEqual(molarity(solve="M", mass_g=.1,
                                        concentration_mol_l=.1, volume_l=.01), 100)

    def test_rejects_missing_or_extra_unknown(self) -> None:
        with self.assertRaises(ValueError):
            molarity(solve="m", mass_g=1, concentration_mol_l=.1,
                     volume_l=.01, molar_mass_g_mol=100)
        with self.assertRaises(ValueError):
            molarity(solve="x", mass_g=1)


class DilutionTests(unittest.TestCase):
    def test_solve_each_variable(self) -> None:
        self.assertAlmostEqual(dilution(solve="v2", c1=1, v1=1, c2=.1), 10)
        self.assertAlmostEqual(dilution(solve="v1", c1=1, c2=.1, v2=10), 1)
        self.assertAlmostEqual(dilution(solve="c2", c1=1, v1=1, v2=10), .1)
        self.assertAlmostEqual(dilution(solve="c1", c2=.1, v1=1, v2=10), 1)

    def test_concentration_step_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            dilution(solve="v1", c1=1, c2=2, v2=1)
        with self.assertRaises(ValueError):
            dilution(solve="v2", c1=1, v1=1, c2=2)


class MasterMixTests(unittest.TestCase):
    def test_scaling_and_excess(self) -> None:
        rows = mastermix([("Buffer", 2), ("Enzyme", .5)], 10, 10)
        self.assertAlmostEqual(rows[0]["total_ul"], 22)
        self.assertAlmostEqual(rows[1]["total_ul"], 5.5)
        self.assertEqual(sum(row["per_reaction_ul"] for row in rows), 2.5)

    def test_invalid_reagents(self) -> None:
        with self.assertRaises(ValueError):
            mastermix([], 1, 0)
        with self.assertRaises(ValueError):
            mastermix([("A", 1), ("a", 2)], 1, 0)
        with self.assertRaises(ValueError):
            mastermix([("", 1)], 1, 0)
        with self.assertRaises(ValueError):
            mastermix([("A", 1)], 0, 0)
        with self.assertRaises(ValueError):
            mastermix([("A", 1)], 1, 501)


class UnitConversionTests(unittest.TestCase):
    def test_factor_based_conversions(self) -> None:
        self.assertAlmostEqual(convert_unit(1, "mass", "g", "mg"), 1000)
        self.assertAlmostEqual(convert_unit(1000, "volume", "µL", "mL"), 1)
        self.assertAlmostEqual(convert_unit(1, "concentration", "mol/L", "mmol/L"), 1000)
        self.assertAlmostEqual(convert_unit(1, "molar_mass", "kg/mol", "g/mol"), 1000)
        self.assertAlmostEqual(convert_unit(1, "time", "h", "min"), 60)

    def test_temperature_conversions(self) -> None:
        self.assertAlmostEqual(convert_unit(0, "temperature", "°C", "°F"), 32)
        self.assertAlmostEqual(convert_unit(32, "temperature", "°F", "°C"), 0)
        self.assertAlmostEqual(convert_unit(0, "temperature", "°C", "K"), 273.15)
        self.assertAlmostEqual(convert_unit(273.15, "temperature", "K", "°C"), 0)

    def test_rejects_unknown_groups_and_units(self) -> None:
        with self.assertRaises(ValueError):
            convert_unit(1, "unknown", "g", "mg")
        with self.assertRaises(ValueError):
            convert_unit(1, "mass", "g", "mL")
        with self.assertRaises(ValueError):
            convert_unit(float("nan"), "mass", "g", "mg")


class QpcrTests(unittest.TestCase):
    def test_standard_delta_delta_ct(self) -> None:
        result = qpcr(25, 20, 26, 20)
        self.assertAlmostEqual(result.delta_ct_sample, 5)
        self.assertAlmostEqual(result.delta_ct_control, 6)
        self.assertAlmostEqual(result.delta_delta_ct, -1)
        self.assertAlmostEqual(result.fold_change, 2)
        self.assertEqual(result.efficiency_percent, 100)

    def test_efficiency_changes_fold_change(self) -> None:
        result = qpcr(25, 20, 26, 20, efficiency_percent=90)
        self.assertAlmostEqual(result.fold_change, 1.9)

    def test_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            qpcr(-1, 20, 26, 20)
        with self.assertRaises(ValueError):
            qpcr(25, 20, 26, 20, efficiency_percent=0)
        with self.assertRaises(ValueError):
            qpcr(25, 20, 26, 20, efficiency_percent=201)


class PositiveTests(unittest.TestCase):
    def test_zero_and_negative(self) -> None:
        self.assertEqual(positive(0, "x", zero=True), 0)
        with self.assertRaises(ValueError):
            positive(0, "x")
        with self.assertRaises(ValueError):
            positive(-1, "x")
        with self.assertRaises(ValueError):
            positive(float("nan"), "x")


if __name__ == "__main__":
    unittest.main()
