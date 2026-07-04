import numpy as np
from datetime import datetime

from pyscnomics.econ.revenue import Lifting
from pyscnomics.econ.selection import (
    FluidType, FTPTaxRegime, DeprMethod, NPVSelection, DiscountingMode,
    InflationAppliedTo, TaxRegime, TaxSplitTypeCR, OtherRevenue, CostType,
)
from pyscnomics.econ.costs import CapitalCost, Intangible, OPEX, ASR, LBT, CostOfSales
from pyscnomics.contracts import CostRecovery


# ---------------------------------------------------------------------------
# Global setup
# ---------------------------------------------------------------------------
start_date = datetime.strptime("01/01/2023", "%d/%m/%Y").date()
end_date = datetime.strptime("31/12/2035", "%d/%m/%Y").date()
oil_onstream_date = datetime.strptime("01/01/2024", "%d/%m/%Y").date()
gas_onstream_date = datetime.strptime("01/01/2024", "%d/%m/%Y").date()
approval_year = 2023

# ---------------------------------------------------------------------------
# Lifting
# ---------------------------------------------------------------------------
lifting_oil_oil_source_1 = Lifting(
    start_year=2023,
    end_year=2035,
    lifting_rate=np.array([504.39079, 1083.14352, 1111.50503, 921.706476, 927.558709, 865.556002, 680.393586, 690.307944, 621.229015, 632.850801, 522.365888, 289.589131]),
    price=np.array([65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65]),
    prod_year=np.array([2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035]),
    fluid_type=FluidType.OIL,
)

lifting_gsa_gas_1_0 = Lifting(
    start_year=2023,
    end_year=2035,
    prod_rate=np.array([1.058999292, 2.3434749, 3.404866855, 4.530388211, 5.813033008, 5.409632856, 4.469681685, 4.419668114, 4.184602397, 3.262559568, 2.785680164, 1.808780726]),
    lifting_rate=np.array([1.058999292, 2.3434749, 3.404866855, 4.530388211, 5.813033008, 5.409632856, 4.469681685, 4.419668114, 4.184602397, 3.262559568, 2.785680164, 1.808780726]),
    price=np.array([5.287671054, 5.236625538, 5.205749129, 5.505818519, 5.50165717, 5.508195913, 5.665290571, 5.617809893, 5.70251656, 5.686425258, 5.692068851, 5.666436984]),
    prod_year=np.array([2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035]),
    ghv=np.array([1224, 1224, 1224, 1224, 1224, 1224, 1224, 1224, 1224, 1224, 1224, 1224]),
    fluid_type=FluidType.GAS,
)

# ---------------------------------------------------------------------------
# CapitalCost
# ---------------------------------------------------------------------------
capital_2_exploration_dry = CapitalCost(
    start_year=2023,
    end_year=2035,
    expense_year=np.array([2024, 2024, 2025, 2025, 2026, 2026, 2027, 2027, 2028, 2028, 2029, 2029, 2030, 2030, 2031, 2031, 2032, 2032, 2033, 2033, 2034, 2034]),
    cost_allocation=[FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS],
    cost=np.array([42133.6454, 9160.58879, 39967.8419, 8868.24984, 38856.2393, 12134.8413, 21886.5055, 11599.5862, 10943.1441, 7389.21709, 250.653872, 168.988758, 689.506009, 502.548556, 377.655725, 266.018169, 810.081733, 609.395528, 809.471362, 464.728536, 20000, 20000]),
    cost_type=[CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST],
    pis_year=np.array([2024, 2024, 2025, 2025, 2026, 2026, 2027, 2027, 2028, 2028, 2029, 2029, 2030, 2030, 2031, 2031, 2032, 2032, 2033, 2033, 2034, 2034]),
    useful_life=np.array([5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]),
    depreciation_factor=np.array([0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]),
    tax_portion=np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
)

# ---------------------------------------------------------------------------
# Intangible
# ---------------------------------------------------------------------------
intangible_2_exploration_dry = Intangible(
    start_year=2023,
    end_year=2035,
    expense_year=np.array([2024, 2024, 2025, 2025, 2026, 2026, 2027, 2027, 2028, 2028, 2029, 2029, 2030, 2030, 2031, 2031, 2032, 2032, 2033, 2033, 2034, 2034]),
    cost_allocation=[FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS],
    cost=np.array([47826.96158, 10398.41493, 48404.26246, 10740.16188, 28190.46986, 8803.911148, 20605.6122, 10920.7281, 19569.28369, 13213.90669, 578.0685023, 389.7289829, 1001.821274, 730.1804897, 743.2795074, 523.5611167, 1689.884506, 1271.239702, 1977.636737, 1135.38819, 4000, 4000]),
    cost_type=[CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST],
    tax_portion=np.array([0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
)

# ---------------------------------------------------------------------------
# OPEX
# ---------------------------------------------------------------------------
opex_2_exploration_dry = OPEX(
    start_year=2023,
    end_year=2035,
    expense_year=np.array([2024, 2024, 2025, 2025, 2026, 2026, 2027, 2027, 2028, 2028, 2029, 2029, 2030, 2030, 2031, 2031, 2032, 2032, 2033, 2033, 2034, 2034, 2035, 2035]),
    cost_allocation=[FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS],
    fixed_cost=np.array([882.335156, 191.835039, 4981.52524, 1105.32389, 5898.72414, 1842.17729, 6071.0637, 3217.59117, 6273.55964, 4236.14032, 5816.11935, 3921.17936, 4992.43538, 3638.75175, 4860.87702, 3423.96928, 8332.93029, 6268.56556, 4477.96396, 2570.86011, 3940.22104, 2342.33266, 3040.35371, 2107.36246]),
    cost_type=[CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST],
    tax_portion=np.array([0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4]),
)

# ---------------------------------------------------------------------------
# ASR
# ---------------------------------------------------------------------------
asr_2_exploration_dry = ASR(
    start_year=2023,
    end_year=2035,
    expense_year=np.array([2024, 2024, 2025, 2025, 2026, 2026, 2027, 2027, 2028, 2028, 2029, 2029, 2030, 2030, 2031, 2031, 2032, 2032, 2033, 2033, 2034, 2034, 2035, 2035]),
    cost_allocation=[FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS, FluidType.OIL, FluidType.GAS],
    cost=np.array([188.6494775, 41.015684, 443.6484088, 98.43876316, 611.9571213, 191.114804, 665.6949261, 352.8103516, 761.5857233, 514.2509476, 762.0612833, 513.7753877, 737.9671002, 537.8695708, 748.5576593, 527.2790116, 728.1074588, 547.7292121, 810.5111685, 465.3255025, 800.1648267, 475.6718442, 753.5370305, 522.2996405]),
    cost_type=[CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST, CostType.POST_ONSTREAM_COST],
    final_year=np.array([2024, 2024, 2025, 2025, 2026, 2026, 2027, 2027, 2028, 2028, 2029, 2029, 2030, 2030, 2031, 2031, 2032, 2032, 2033, 2033, 2034, 2034, 2035, 2035]),
)

# ---------------------------------------------------------------------------
# PSC fiscal terms (Cost Recovery)
# ---------------------------------------------------------------------------
oil_ftp_is_available = True
oil_ftp_is_shared = True
oil_ftp_portion = 0.05
gas_ftp_is_available = True
gas_ftp_is_shared = True
gas_ftp_portion = 0.05
tax_split_type = TaxSplitTypeCR.CONVENTIONAL
oil_ctr_pretax_share = 0.672269
gas_ctr_pretax_share = 0.672269
oil_ic_rate = 0
gas_ic_rate = 0
ic_is_available = False
oil_cr_cap_rate = 1
gas_cr_cap_rate = 1
oil_dmo_volume_portion = 0.25
oil_dmo_fee_portion = 1
oil_dmo_holiday_duration = 0
gas_dmo_volume_portion = 0.25
gas_dmo_fee_portion = 1
gas_dmo_holiday_duration = 0
oil_carry_forward_depreciation = 0
gas_carry_forward_depreciation = 0

# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------
project = CostRecovery(
    start_date=start_date,
    end_date=end_date,
    approval_year=approval_year,
    oil_onstream_date=oil_onstream_date,
    gas_onstream_date=gas_onstream_date,
    lifting=tuple([lifting_oil_oil_source_1, lifting_gsa_gas_1_0]),
    is_strict=True,
    is_pod_1=False,
    capital_cost=tuple([capital_2_exploration_dry]),
    intangible_cost=tuple([intangible_2_exploration_dry]),
    opex=tuple([opex_2_exploration_dry]),
    asr_cost=tuple([asr_2_exploration_dry]),
    oil_ftp_is_available=oil_ftp_is_available,
    oil_ftp_is_shared=oil_ftp_is_shared,
    oil_ftp_portion=oil_ftp_portion,
    gas_ftp_is_available=gas_ftp_is_available,
    gas_ftp_is_shared=gas_ftp_is_shared,
    gas_ftp_portion=gas_ftp_portion,
    tax_split_type=tax_split_type,
    oil_ctr_pretax_share=oil_ctr_pretax_share,
    gas_ctr_pretax_share=gas_ctr_pretax_share,
    oil_ic_rate=oil_ic_rate,
    gas_ic_rate=gas_ic_rate,
    ic_is_available=ic_is_available,
    oil_cr_cap_rate=oil_cr_cap_rate,
    gas_cr_cap_rate=gas_cr_cap_rate,
    oil_dmo_volume_portion=oil_dmo_volume_portion,
    oil_dmo_fee_portion=oil_dmo_fee_portion,
    oil_dmo_holiday_duration=oil_dmo_holiday_duration,
    gas_dmo_volume_portion=gas_dmo_volume_portion,
    gas_dmo_fee_portion=gas_dmo_fee_portion,
    gas_dmo_holiday_duration=gas_dmo_holiday_duration,
    oil_carry_forward_depreciation=oil_carry_forward_depreciation,
    gas_carry_forward_depreciation=gas_carry_forward_depreciation,
)

# ---------------------------------------------------------------------------
# Fiscal / contract-run arguments
# ---------------------------------------------------------------------------
fiscal = {
    "sulfur_revenue": OtherRevenue.REDUCTION_TO_OIL_OPEX,
    "electricity_revenue": OtherRevenue.REDUCTION_TO_OIL_OPEX,
    "co2_revenue": OtherRevenue.REDUCTION_TO_GAS_OPEX,
    "is_dmo_end_weighted": False,
    "tax_regime": TaxRegime.NAILED_DOWN,
    "effective_tax_rate": 0.405,
    "ftp_tax_regime": FTPTaxRegime.DIRECT_MODE,
    "depr_method": DeprMethod.PSC_DB,
    "decline_factor": 2,
    "vat_rate": 0.12,
    "inflation_rate": 0,
    "inflation_rate_applied_to": None,
    "post_uu_22_year2001": True,
    "amortization": False,
    "sum_undepreciated_cost": False,
    "oil_cost_of_sales_applied": False,
    "gas_cost_of_sales_applied": False,
}

# ---------------------------------------------------------------------------
# Summary arguments
# ---------------------------------------------------------------------------
summary_parameter = {
    "discount_rate_start_year": 2023,
    "inflation_rate": 0,
    "discount_rate": 0.1,
    "npv_mode": NPVSelection.NPV_SKK_NOMINAL_TERMS,
    "discounting_mode": DiscountingMode.MID_YEAR,
    "profitability_discounted": True,
}

# ---------------------------------------------------------------------------
# Run the project and print the summary
# ---------------------------------------------------------------------------
project.run(**fiscal)
summary = project.get_summary(**summary_parameter)

for key, value in summary.items():
    print(f"{key}: {value}")
