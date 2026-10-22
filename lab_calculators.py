"""Unit-aware, UI-independent laboratory calculations.

Inputs are the numbers as entered by the user. Results are not rounded
internally; the interface decides how many digits to display. All functions
raise :class:`ValueError` with a human-readable reason for invalid input.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

MASS_UNITS = {"g": 1.0, "mg": 1e-3, "µg": 1e-6}
VOLUME_UNITS = {"L": 1.0, "mL": 1e-3, "µL": 1e-6}
CONCENTRATION_UNITS = {"mol/L": 1.0, "mmol/L": 1e-3, "µmol/L": 1e-6}
MOLAR_MASS_UNITS = {"g/mol": 1.0, "kg/mol": 1e3, "mg/mmol": 1.0}
TIME_UNITS = {"s": 1.0, "min": 60.0, "h": 3600.0}
TEMPERATURE_UNITS = ("°C", "°F", "K")
UNIT_GROUPS = {
    "mass": MASS_UNITS,
    "volume": VOLUME_UNITS,
    "concentration": CONCENTRATION_UNITS,
    "molar_mass": MOLAR_MASS_UNITS,
    "time": TIME_UNITS,
}
UNIT_GROUP_KEYS = ("mass", "volume", "concentration", "molar_mass", "time", "temperature")


def positive(value: float, name: str, *, zero: bool = False) -> float:
    """Convert to float and reject non-finite, negative or (optionally) zero values."""
    value = float(value)
    if not isfinite(value) or value < 0 or (value == 0 and not zero):
        raise ValueError(f"{name} must be {'non-negative' if zero else 'positive'}")
    return value


def units_for(group: str) -> tuple[str, ...]:
    """Return the unit symbols available for a converter group."""
    if group == "temperature":
        return TEMPERATURE_UNITS
    if group not in UNIT_GROUPS:
        raise ValueError("Unsupported unit group")
    return tuple(UNIT_GROUPS[group])


def convert_unit(value: float, group: str, from_unit: str, to_unit: str) -> float:
    """Convert a value between units of the same quantity.

    Temperature is affine, while mass, volume, concentration, molar mass and
    time use simple factors. Unknown groups and units raise ``ValueError``.
    """
    value = float(value)
    if not isfinite(value):
        raise ValueError("Value must be finite")
    units = units_for(group)
    if from_unit not in units or to_unit not in units:
        raise ValueError("Unsupported unit")
    if group == "temperature":
        if from_unit == "°C":
            celsius = value
        elif from_unit == "°F":
            celsius = (value - 32) * 5 / 9
        else:
            celsius = value - 273.15
        if to_unit == "°C":
            return celsius
        if to_unit == "°F":
            return celsius * 9 / 5 + 32
        return celsius + 273.15
    return value * UNIT_GROUPS[group][from_unit] / UNIT_GROUPS[group][to_unit]


@dataclass(frozen=True)
class CountResult:
    live_per_ml: float
    dead_per_ml: float
    total_per_ml: float
    total_live_cells: float
    viability_percent: float | None
    stock_volume_ml: float | None
    medium_volume_ml: float | None
    total_cells_in_suspension: float = 0.0
    total_dead_cells: float = 0.0


@dataclass(frozen=True)
class QpcrResult:
    delta_ct_sample: float
    delta_ct_control: float
    delta_delta_ct: float
    fold_change: float
    efficiency_percent: float


def qpcr(
    target_sample_ct: float,
    reference_sample_ct: float,
    target_control_ct: float,
    reference_control_ct: float,
    efficiency_percent: float = 100.0,
) -> QpcrResult:
    """Evaluate relative qPCR expression with the ΔΔCt method.

    ``fold_change`` is the expression of the sample relative to the control.
    The primer efficiency is entered as a percentage; 100 % gives the familiar
    ``2^(-ΔΔCt)`` result.
    """
    target_sample = positive(target_sample_ct, "target sample Ct", zero=True)
    reference_sample = positive(reference_sample_ct, "reference sample Ct", zero=True)
    target_control = positive(target_control_ct, "target control Ct", zero=True)
    reference_control = positive(reference_control_ct, "reference control Ct", zero=True)
    efficiency = positive(efficiency_percent, "efficiency")
    if efficiency > 200:
        raise ValueError("Efficiency above 200% is not supported")
    delta_sample = target_sample - reference_sample
    delta_control = target_control - reference_control
    delta_delta = delta_sample - delta_control
    fold_change = (1 + efficiency / 100) ** (-delta_delta)
    return QpcrResult(
        delta_ct_sample=delta_sample,
        delta_ct_control=delta_control,
        delta_delta_ct=delta_delta,
        fold_change=fold_change,
        efficiency_percent=efficiency,
    )


def neubauer(
    live_counts: list[float],
    dead_counts: list[float] | None,
    dilution: float,
    suspension_ml: float,
    target_cells: float | None = None,
    target_concentration_per_ml: float | None = None,
) -> CountResult:
    """Calculate a Neubauer chamber count.

    The standard volume of one large square is 10^-4 mL. Live cells are used
    for seeding; dead cells are optional and omitted dead counts do not imply
    100 % viability. ``target_cells`` is the absolute number of live cells
    wanted for the experiment. If ``target_concentration_per_ml`` is given as
    well, the required medium volume is calculated from the final volume.
    """
    if not live_counts:
        raise ValueError("At least one large-square count is required")
    live = [positive(value, "live count", zero=True) for value in live_counts]
    dead = (
        [positive(value, "dead count", zero=True) for value in dead_counts]
        if dead_counts is not None else None
    )
    if dead is not None and len(dead) != len(live):
        raise ValueError("Live and dead counts must cover the same squares")

    factor = positive(dilution, "dilution") * 10_000 / len(live)
    live_per_ml = sum(live) * factor
    dead_per_ml = sum(dead) * factor if dead is not None else 0.0
    total_per_ml = live_per_ml + dead_per_ml
    suspension = positive(suspension_ml, "suspension volume")
    viability = 100 * live_per_ml / total_per_ml if dead is not None and total_per_ml else None

    stock_ml = medium_ml = None
    if target_cells is not None:
        target = positive(target_cells, "target cells")
        if live_per_ml == 0:
            raise ValueError("No live cells available for seeding")
        stock_ml = target / live_per_ml
        if target_concentration_per_ml is not None:
            final_ml = target / positive(target_concentration_per_ml, "target concentration")
            medium_ml = final_ml - stock_ml
            if medium_ml < -1e-10:
                raise ValueError("Target concentration exceeds the available live-cell concentration")
            medium_ml = max(0.0, medium_ml)

    return CountResult(
        live_per_ml=live_per_ml,
        dead_per_ml=dead_per_ml,
        total_per_ml=total_per_ml,
        total_live_cells=live_per_ml * suspension,
        viability_percent=viability,
        stock_volume_ml=stock_ml,
        medium_volume_ml=medium_ml,
        total_cells_in_suspension=total_per_ml * suspension,
        total_dead_cells=dead_per_ml * suspension,
    )


def molarity(
    *,
    solve: str,
    mass_g: float | None = None,
    concentration_mol_l: float | None = None,
    volume_l: float | None = None,
    molar_mass_g_mol: float | None = None,
) -> float:
    """Solve ``m = c × V × M`` in canonical g, mol/L, L and g/mol units."""
    values = {"m": mass_g, "c": concentration_mol_l, "V": volume_l, "M": molar_mass_g_mol}
    if solve not in values or values[solve] is not None:
        raise ValueError("Exactly the requested variable must be unknown")
    known = {key: positive(value, key) for key, value in values.items() if key != solve}
    if solve == "m":
        return known["c"] * known["V"] * known["M"]
    if solve == "c":
        return known["m"] / (known["V"] * known["M"])
    if solve == "V":
        return known["m"] / (known["c"] * known["M"])
    return known["m"] / (known["c"] * known["V"])


def dilution(
    *,
    solve: str,
    c1: float | None = None,
    v1: float | None = None,
    c2: float | None = None,
    v2: float | None = None,
) -> float:
    """Solve ``C1 × V1 = C2 × V2``; concentrations and volumes use matched units.

    The function rejects a concentration step (``C2 > C1`` or ``V1 > V2``)
    because that is not a stock-solution dilution. This also prevents a
    negative amount of solvent from being presented as a valid preparation.
    """
    values = {"c1": c1, "v1": v1, "c2": c2, "v2": v2}
    if solve not in values or values[solve] is not None:
        raise ValueError("Exactly the requested variable must be unknown")
    known = {key: positive(value, key) for key, value in values.items() if key != solve}
    result = {
        "c1": lambda: known["c2"] * known["v2"] / known["v1"],
        "v1": lambda: known["c2"] * known["v2"] / known["c1"],
        "c2": lambda: known["c1"] * known["v1"] / known["v2"],
        "v2": lambda: known["c1"] * known["v1"] / known["c2"],
    }[solve]()
    completed = {**known, solve: result}
    if completed["c2"] > completed["c1"] + 1e-12 or completed["v1"] > completed["v2"] + 1e-12:
        raise ValueError("This is a concentration step, not a stock-solution dilution")
    return result


def mastermix(
    reagents: list[tuple[str, float]],
    reactions: int,
    excess_percent: float,
) -> list[dict[str, float | str]]:
    """Scale reagent volumes to ``reactions`` plus a pipetting excess.

    The returned dictionaries contain ``reagent``, ``per_reaction_ul`` and
    ``total_ul``. The total includes the excess and is not rounded.
    """
    if int(reactions) != reactions or reactions < 1:
        raise ValueError("Reactions must be a positive integer")
    excess = positive(excess_percent, "excess", zero=True)
    if excess > 500:
        raise ValueError("Excess above 500% is not supported")
    if not reagents:
        raise ValueError("Provide at least one reagent")
    if len({name.strip().casefold() for name, _ in reagents}) != len(reagents):
        raise ValueError("Provide unique reagent names")
    factor = int(reactions) * (1 + excess / 100)
    rows: list[dict[str, float | str]] = []
    for name, per_reaction in reagents:
        if not name.strip():
            raise ValueError("A reagent name is required")
        per = positive(per_reaction, name, zero=True)
        rows.append({
            "reagent": name.strip(),
            "per_reaction_ul": per,
            "total_ul": per * factor,
        })
    return rows
