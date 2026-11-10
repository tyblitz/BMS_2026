from decimal import Decimal
from typing import Any


def to_decimal(val: Any) -> Decimal:
    if val is None or val == "" or val == "NA":
        return Decimal("0.00")
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0.00")


def calculate_balances(
    appropriations: Any = 0,
    appro_adjust: Any = 0,
    allotment: Any = 0,
    realignment: Any = 0,
    transfer_from: Any = 0,
    transfer_to: Any = 0,
    obligations_incurred: Any = 0,
    disbursement: Any = 0,
) -> dict[str, Decimal]:
    """
    Computes the 5 non-stored dynamic financial balances.
    Matches MS Access BMS formulas verified from sample file:
    - Col AC (TOTAL ADJUSTED APPRO) = Appropriations (I) + ApproAdjust (T)
    - Col AD (TOTAL ADJUSTED ALLOTMENT ) = Allotment (J) + Realignment (U) + TransferFrom (L) - TransferTo (K)
    - Col AE (UNOBLIGATED) = TOTAL ADJUSTED ALLOTMENT (AD) - ObligationsIncurred (G)
    - Col AF (UNPAID) = ObligationsIncurred (G) - Disbursement (H)
    - Col AG (UNRELEASED) = TOTAL ADJUSTED APPRO (AC) - TOTAL ADJUSTED ALLOTMENT (AD)
    """
    appro = to_decimal(appropriations)
    appro_adj = to_decimal(appro_adjust)
    allot = to_decimal(allotment)
    realign = to_decimal(realignment)
    trans_from = to_decimal(transfer_from)
    trans_to = to_decimal(transfer_to)
    obli = to_decimal(obligations_incurred)
    disb = to_decimal(disbursement)

    total_adj_appro = appro + appro_adj
    total_adj_allot = allot + realign + trans_from - trans_to
    unobligated = total_adj_allot - obli
    unpaid = obli - disb
    unreleased = total_adj_appro - total_adj_allot

    return {
        "total_adjusted_appro": total_adj_appro,
        "total_adjusted_allotment": total_adj_allot,
        "unobligated": unobligated,
        "unpaid": unpaid,
        "unreleased": unreleased,
    }
