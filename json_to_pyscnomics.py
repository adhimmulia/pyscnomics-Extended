"""
json_to_pyscnomics.py
======================

Generic converter: takes a PSC project-definition JSON (the export format
used by Adhim's pyscnomics-based application/dashboard) and generates a
standalone, runnable pyscnomics Python script in the same style as his
reference scripts (explicit Lifting / CapitalCost / Intangible / OPEX / ASR
objects, a CostRecovery contract, a `fiscal` dict passed to `project.run()`,
and a `summary_parameter` dict passed to `project.get_summary()`).

Usage
-----
    python json_to_pyscnomics.py input.json -o output.py

Design notes
------------
The converter is schema-driven rather than hard-coded to one example: every
top-level JSON block is mapped to a family of pyscnomics objects using the
JSON's own key names as constructor keyword arguments. This means it will
keep working if new fields are added to the JSON export later (they just
get passed straight through), and it only needs special-casing for:

  1. Enum-like string values (e.g. "Direct Mode" -> FTPTaxRegime.DIRECT_MODE)
  2. Date strings (dd/mm/YYYY -> datetime.date)
  3. Trivial/placeholder fields (all-None, all-zero, empty containers)
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


# --------------------------------------------------------------------------- #
# 1. Enum-mapping helpers
# --------------------------------------------------------------------------- #

def map_fluid_type(value: str) -> str:
    """'Oil' / 'Gas' / 'Sulfur' / 'Electricity' / 'CO2' / 'All' -> FluidType.X"""
    v = value.strip().lower()
    table = {
        "oil": "OIL",
        "gas": "GAS",
        "sulfur": "SULFUR",
        "electricity": "ELECTRICITY",
        "co2": "CO2",
        "all": "ALL",
    }
    return f"FluidType.{table.get(v, value.strip().upper())}"


def map_cost_type(value: str) -> str:
    """'postonstream_cost' -> CostType.POST_ONSTREAM_COST (pattern based)."""
    s = value.strip()
    if s.lower().endswith("_cost"):
        prefix = s[: -len("_cost")]
    else:
        prefix = s
    for p in ("post", "pre"):
        if prefix.lower().startswith(p) and prefix.lower() != p:
            prefix = p + "_" + prefix[len(p):]
            break
    name = (prefix + "_cost").upper()
    name = re.sub(r"_+", "_", name)
    return f"CostType.{name}"


def map_ftp_tax_regime(value: str) -> str:
    v = value.strip().lower()
    if "direct" in v:
        return "FTPTaxRegime.DIRECT_MODE"
    if "pre" in v:
        return "FTPTaxRegime.PRE_PDJP_20_2017"
    return "FTPTaxRegime.PDJP_20_2017"


def map_depr_method(value: str) -> str:
    v = value.strip().lower()
    if "declining" in v and "psc" in v:
        return "DeprMethod.PSC_DB"
    if "declining" in v:
        return "DeprMethod.DB"
    if "straight" in v:
        return "DeprMethod.SL"
    if "unit" in v:
        return "DeprMethod.UOP"
    return "DeprMethod.PSC_DB"


def map_npv_mode(value: str) -> str:
    v = value.strip().lower()
    if "skk" in v and "real" in v:
        return "NPVSelection.NPV_SKK_REAL_TERMS"
    if "skk" in v:
        return "NPVSelection.NPV_SKK_NOMINAL_TERMS"
    if "point forward" in v:
        return "NPVSelection.NPV_POINT_FORWARD"
    if "real" in v:
        return "NPVSelection.NPV_REAL_TERMS"
    return "NPVSelection.NPV_NOMINAL_TERMS"


def map_discounting_mode(value: str) -> str:
    return "DiscountingMode.MID_YEAR" if "mid" in value.lower() else "DiscountingMode.END_YEAR"


def map_tax_regime(value: str) -> str:
    v = value.strip().lower()
    if "36" in v:
        return "TaxRegime.UU_36_2008"
    if "02" in v or "2020" in v:
        return "TaxRegime.UU_02_2020"
    if "07" in v or "2021" in v:
        return "TaxRegime.UU_07_2021"
    if "prevailing" in v:
        return "TaxRegime.PREVAILING"
    return "TaxRegime.NAILED_DOWN"


def map_tax_split_type(value: str) -> str:
    v = value.strip().lower()
    if "sliding" in v:
        return "TaxSplitTypeCR.SLIDING_SCALE"
    if "r/c" in v or "r2c" in v:
        return "TaxSplitTypeCR.R2C"
    return "TaxSplitTypeCR.CONVENTIONAL"


def map_inflation_applied_to(value: Any) -> str | None:
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in ("none", ""):
        return None
    has_capex = "capex" in v or "tangible" in v
    has_opex = "opex" in v or "operating" in v
    if has_capex and has_opex:
        return "InflationAppliedTo.CAPEX_AND_OPEX"
    if has_capex:
        return "InflationAppliedTo.CAPEX"
    if has_opex:
        return "InflationAppliedTo.OPEX"
    return None


def map_other_revenue(value: str) -> str:
    v = value.strip().lower()
    is_addition = "addition" in v
    is_oil = "oil" in v
    if is_addition and is_oil:
        return "OtherRevenue.ADDITION_TO_OIL_REVENUE"
    if is_addition:
        return "OtherRevenue.ADDITION_TO_GAS_REVENUE"
    if is_oil:
        return "OtherRevenue.REDUCTION_TO_OIL_OPEX"
    return "OtherRevenue.REDUCTION_TO_GAS_OPEX"


# Keys whose (single) string value should go through an enum mapper.
SCALAR_ENUM_MAPPERS = {
    "ftp_tax_regime": map_ftp_tax_regime,
    "depr_method": map_depr_method,
    "npv_mode": map_npv_mode,
    "discounting_mode": map_discounting_mode,
    "tax_regime": map_tax_regime,
    "tax_split_type": map_tax_split_type,
    "inflation_rate_applied_to": map_inflation_applied_to,
    "sulfur_revenue": map_other_revenue,
    "electricity_revenue": map_other_revenue,
    "co2_revenue": map_other_revenue,
}

# Keys whose *list* values are lists of fluid-type / cost-type strings.
LIST_ENUM_MAPPERS = {
    "cost_allocation": map_fluid_type,
    "cost_type": map_cost_type,
}


# --------------------------------------------------------------------------- #
# 2. Generic value -> python-source-code rendering
# --------------------------------------------------------------------------- #

DATE_KEYS = {"start_date", "end_date", "oil_onstream_date", "gas_onstream_date"}


def is_trivial(value: Any) -> bool:
    """True if a value carries no real information and can be omitted."""
    if value is None:
        return True
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            return True
        if all(v is None for v in value):
            return True
        if all(isinstance(v, bool) and v is False for v in value):
            return True
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) and v == 0 for v in value):
            return True
        return False
    if isinstance(value, dict):
        return len(value) == 0
    if isinstance(value, str):
        return value.strip() in ("", "-")
    return False


def render_date(value: str) -> str:
    return f'datetime.strptime("{value}", "%d/%m/%Y").date()'


def render_scalar(key: str, value: Any) -> str:
    if key in DATE_KEYS and isinstance(value, str):
        return render_date(value)
    if key in SCALAR_ENUM_MAPPERS and isinstance(value, str):
        mapped = SCALAR_ENUM_MAPPERS[key](value)
        return "None" if mapped is None else mapped
    if key == "fluid_type" and isinstance(value, str):
        return map_fluid_type(value)
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (int, float)):
        return repr(value)
    return repr(value)


def render_list(key: str, values: list) -> str:
    mapper = LIST_ENUM_MAPPERS.get(key)
    if mapper is not None and all(isinstance(v, str) for v in values):
        items = ", ".join(mapper(v) for v in values)
        return f"[{items}]"
    if all(v is None or isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
        cleaned = [0 if v is None else v for v in values]
        return f"np.array([{', '.join(repr(v) for v in cleaned)}])"
    if all(isinstance(v, str) for v in values):
        items = ", ".join(json.dumps(v) for v in values)
        return f"[{items}]"
    # mixed / fallback
    return repr(values)


def render_value(key: str, value: Any) -> str:
    if isinstance(value, list):
        return render_list(key, value)
    return render_scalar(key, value)


# --------------------------------------------------------------------------- #
# 3. Identifier helpers
# --------------------------------------------------------------------------- #

def sanitize_identifier(name: str, prefix: str = "") -> str:
    ident = re.sub(r"[^0-9a-zA-Z_]+", "_", name.strip()).strip("_").lower()
    if not ident:
        ident = "item"
    if ident[0].isdigit():
        ident = f"{prefix}_{ident}" if prefix else f"_{ident}"
    elif prefix:
        ident = f"{prefix}_{ident}"
    return ident


def kwargs_block(data: dict, skip_keys: set[str] = frozenset(), indent: str = "    ") -> str:
    lines = []
    for key, value in data.items():
        if key in skip_keys or key == "description":
            continue
        if is_trivial(value):
            continue
        lines.append(f"{indent}{key}={render_value(key, value)},")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 4. Section generators
# --------------------------------------------------------------------------- #

def generate_lifting(data: dict) -> tuple[str, list[str]]:
    blocks, var_names = [], []
    for name, obj in data.items():
        var = sanitize_identifier(name, prefix="lifting")
        var_names.append(var)
        body = kwargs_block(obj)
        blocks.append(f"{var} = Lifting(\n{body}\n)")
    return "\n\n".join(blocks), var_names


def generate_cost_block(data: dict, class_name: str, var_prefix: str) -> tuple[str, list[str]]:
    blocks, var_names = [], []
    for name, obj in data.items():
        if is_trivial(obj.get("cost")) and is_trivial(obj.get("fixed_cost")):
            continue  # skip empty placeholder cases (e.g. unused LBT / cost_of_sales)
        var = sanitize_identifier(name, prefix=var_prefix)
        var_names.append(var)
        body = kwargs_block(obj)
        blocks.append(f"{var} = {class_name}(\n{body}\n)")
    return "\n\n".join(blocks), var_names


# --------------------------------------------------------------------------- #
# 5. Main generator
# --------------------------------------------------------------------------- #

HEADER = '''\
import numpy as np
from datetime import datetime

from pyscnomics.econ.revenue import Lifting
from pyscnomics.econ.selection import (
    FluidType, FTPTaxRegime, DeprMethod, NPVSelection, DiscountingMode,
    InflationAppliedTo, TaxRegime, TaxSplitTypeCR, OtherRevenue, CostType,
)
from pyscnomics.econ.costs import CapitalCost, Intangible, OPEX, ASR, LBT, CostOfSales
from pyscnomics.contracts import CostRecovery

'''


def generate_script(data: dict) -> str:
    parts = [HEADER]

    setup = data.get("setup", {})
    costrecovery = data.get("costrecovery", {})
    contract_args = data.get("contract_arguments", {})
    summary_args = data.get("summary_arguments", {})

    # --- global setup / date variables ---------------------------------- #
    parts.append("# ---------------------------------------------------------------------------\n"
                 "# Global setup\n"
                 "# ---------------------------------------------------------------------------")
    setup_lines = []
    for key in ("start_date", "end_date", "oil_onstream_date", "gas_onstream_date"):
        if key in setup and setup[key]:
            setup_lines.append(f"{key} = {render_date(setup[key])}")
    if "approval_year" in setup:
        setup_lines.append(f"approval_year = {setup['approval_year']}")
    parts.append("\n".join(setup_lines))
    parts.append("")

    # --- lifting objects --------------------------------------------------- #
    parts.append("# ---------------------------------------------------------------------------\n"
                 "# Lifting\n"
                 "# ---------------------------------------------------------------------------")
    lifting_code, lifting_vars = generate_lifting(data.get("lifting", {}))
    parts.append(lifting_code)
    parts.append("")

    # --- cost objects ------------------------------------------------------- #
    cost_specs = [
        ("capital", "CapitalCost", "capital"),
        ("intangible", "Intangible", "intangible"),
        ("opex", "OPEX", "opex"),
        ("asr", "ASR", "asr"),
        ("lbt", "LBT", "lbt"),
        ("cost_of_sales", "CostOfSales", "cost_of_sales"),
    ]
    cost_var_map: dict[str, list[str]] = {}
    for json_key, class_name, prefix in cost_specs:
        block = data.get(json_key, {})
        if not block:
            continue
        code, var_names = generate_cost_block(block, class_name, prefix)
        if code:
            parts.append(f"# ---------------------------------------------------------------------------\n"
                         f"# {class_name}\n"
                         f"# ---------------------------------------------------------------------------")
            parts.append(code)
            parts.append("")
        cost_var_map[json_key] = var_names

    # --- PSC fiscal terms (costrecovery block) -> plain variables ----------- #
    parts.append("# ---------------------------------------------------------------------------\n"
                 "# PSC fiscal terms (Cost Recovery)\n"
                 "# ---------------------------------------------------------------------------")
    cr_lines = []
    for key, value in costrecovery.items():
        if is_trivial(value):
            continue
        cr_lines.append(f"{key} = {render_value(key, value)}")
    parts.append("\n".join(cr_lines))
    parts.append("")

    # --- CostRecovery contract ------------------------------------------ #
    parts.append("# ---------------------------------------------------------------------------\n"
                 "# Contract\n"
                 "# ---------------------------------------------------------------------------")
    contract_lines = ["project = CostRecovery("]
    contract_lines.append("    start_date=start_date,")
    contract_lines.append("    end_date=end_date,")
    contract_lines.append("    approval_year=approval_year,")
    if "oil_onstream_date" in setup:
        contract_lines.append("    oil_onstream_date=oil_onstream_date,")
    if "gas_onstream_date" in setup:
        contract_lines.append("    gas_onstream_date=gas_onstream_date,")
    contract_lines.append(f"    lifting=tuple([{', '.join(lifting_vars)}]),")
    if "is_strict" in setup:
        contract_lines.append(f"    is_strict={render_value('is_strict', setup['is_strict'])},")
    if "is_pod_1" in setup:
        contract_lines.append(f"    is_pod_1={render_value('is_pod_1', setup['is_pod_1'])},")
    for json_key, ctor_key in (
        ("capital", "capital_cost"),
        ("intangible", "intangible_cost"),
        ("opex", "opex"),
        ("asr", "asr_cost"),
        ("lbt", "lbt_cost"),
        ("cost_of_sales", "cost_of_sales"),
    ):
        var_names = cost_var_map.get(json_key, [])
        if var_names:
            contract_lines.append(f"    {ctor_key}=tuple([{', '.join(var_names)}]),")
    for key in costrecovery:
        if is_trivial(costrecovery[key]):
            continue
        contract_lines.append(f"    {key}={key},")
    contract_lines.append(")")
    parts.append("\n".join(contract_lines))
    parts.append("")

    # --- fiscal dict (project.run arguments) ----------------------------- #
    parts.append("# ---------------------------------------------------------------------------\n"
                 "# Fiscal / contract-run arguments\n"
                 "# ---------------------------------------------------------------------------")
    fiscal_lines = ["fiscal = {"]
    for key, value in contract_args.items():
        if is_trivial(value):
            continue
        fiscal_lines.append(f'    "{key}": {render_value(key, value)},')
    fiscal_lines.append("}")
    parts.append("\n".join(fiscal_lines))
    parts.append("")

    # --- summary_parameter dict ------------------------------------------ #
    parts.append("# ---------------------------------------------------------------------------\n"
                 "# Summary arguments\n"
                 "# ---------------------------------------------------------------------------")
    summary_lines = ["summary_parameter = {"]
    for key, value in summary_args.items():
        if is_trivial(value):
            continue
        summary_lines.append(f'    "{key}": {render_value(key, value)},')
    summary_lines.append("}")
    parts.append("\n".join(summary_lines))
    parts.append("")

    # --- run + print ------------------------------------------------------- #
    parts.append("# ---------------------------------------------------------------------------\n"
                 "# Run the project and print the summary\n"
                 "# ---------------------------------------------------------------------------")
    parts.append(
        "project.run(**fiscal)\n"
        "summary = project.get_summary(**summary_parameter)\n\n"
        "for key, value in summary.items():\n"
        "    print(f\"{key}: {value}\")\n"
    )

    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# 6. CLI entry point
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description="Convert a PSC project JSON into a pyscnomics Python script.")
    parser.add_argument("input", type=str, help="Path to the input JSON file.")
    parser.add_argument("-o", "--output", type=str, default=None, help="Path to the output .py file.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".py")

    with open(input_path, "r") as f:
        data = json.load(f)

    script = generate_script(data)

    with open(output_path, "w") as f:
        f.write(script)

    print(f"Wrote generated script to: {output_path}")


if __name__ == "__main__":
    main()
