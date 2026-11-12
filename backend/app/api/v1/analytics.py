from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.bms_record import BMSRecord
from app.services.calculations import calculate_balances

router = APIRouter(prefix="/analytics", tags=["Analytics & Summaries"])


def to_decimal(val) -> Decimal:
    if val is None:
        return Decimal("0.00")
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0.00")


@router.get("/school-summary")
def get_school_summary(
    school_name: Optional[str] = Query(None, description="School name to query (for admin/sdo/region)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns aggregated financial health summary for a specific school operating unit.
    Calculations strictly adhere to dynamic balance formulas (Rule 1).
    """
    target_school = None

    if current_user.role == "school":
        target_school = current_user.school_name
    elif current_user.role in ["admin", "region", "sdo"]:
        target_school = school_name or current_user.school_name
        # If SDO, ensure the school requested belongs to their division
        if current_user.role == "sdo" and target_school:
            school_in_div = (
                db.query(BMSRecord)
                .filter(
                    BMSRecord.is_deleted == False,
                    BMSRecord.division == current_user.division,
                    BMSRecord.operating_unit == target_school,
                )
                .first()
            )
            if not school_in_div:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"School '{target_school}' is not within your division scope ({current_user.division}).",
                )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if not target_school:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A school operating unit name must be specified.",
        )

    # Base query for this school
    query = db.query(
        func.count(BMSRecord.id).label("total_records"),
        func.coalesce(func.sum(BMSRecord.appropriations), 0).label("sum_appro"),
        func.coalesce(func.sum(BMSRecord.appro_adjust), 0).label("sum_appro_adjust"),
        func.coalesce(func.sum(BMSRecord.allotment), 0).label("sum_allotment"),
        func.coalesce(func.sum(BMSRecord.realignment), 0).label("sum_realignment"),
        func.coalesce(func.sum(BMSRecord.transfer_from), 0).label("sum_transfer_from"),
        func.coalesce(func.sum(BMSRecord.transfer_to), 0).label("sum_transfer_to"),
        func.coalesce(func.sum(BMSRecord.obligations_incurred), 0).label("sum_obligations"),
        func.coalesce(func.sum(BMSRecord.disbursement), 0).label("sum_disbursement"),
    ).filter(
        BMSRecord.is_deleted == False,
        BMSRecord.operating_unit == target_school,
    )

    result = query.first()

    total_records = result.total_records if result else 0
    appro = to_decimal(result.sum_appro if result else 0)
    appro_adj = to_decimal(result.sum_appro_adjust if result else 0)
    allot = to_decimal(result.sum_allotment if result else 0)
    realign = to_decimal(result.sum_realignment if result else 0)
    trans_from = to_decimal(result.sum_transfer_from if result else 0)
    trans_to = to_decimal(result.sum_transfer_to if result else 0)
    obligations = to_decimal(result.sum_obligations if result else 0)
    disbursement = to_decimal(result.sum_disbursement if result else 0)

    # Derived Dynamic Balances (Rule 1)
    balances = calculate_balances(
        appropriations=appro,
        appro_adjust=appro_adj,
        allotment=allot,
        realignment=realign,
        transfer_from=trans_from,
        transfer_to=trans_to,
        obligations_incurred=obligations,
        disbursement=disbursement,
    )

    adj_allotment = balances["total_adjusted_allotment"]
    unobligated = balances["unobligated"]
    unpaid = balances["unpaid"]
    unreleased = balances["unreleased"]
    adj_appro = balances["total_adjusted_appro"]

    utilization_rate = (
        round(float((obligations / adj_allotment) * Decimal("100")), 2)
        if adj_allotment > Decimal("0")
        else 0.0
    )
    disbursement_rate = (
        round(float((disbursement / obligations) * Decimal("100")), 2)
        if obligations > Decimal("0")
        else 0.0
    )

    # Fetch Division and Region for context
    sample_rec = (
        db.query(BMSRecord.division, BMSRecord.region)
        .filter(BMSRecord.operating_unit == target_school, BMSRecord.is_deleted == False)
        .first()
    )
    division_name = sample_rec.division if sample_rec else current_user.division or ""
    region_name = sample_rec.region if sample_rec else current_user.region or "National Capital Region (NCR)"

    # Fetch 5 most recent records
    recent_records = (
        db.query(BMSRecord)
        .filter(BMSRecord.operating_unit == target_school, BMSRecord.is_deleted == False)
        .order_by(BMSRecord.created_on.desc())
        .limit(5)
        .all()
    )

    recent_list = []
    for r in recent_records:
        r_bals = calculate_balances(
            appropriations=to_decimal(r.appropriations),
            appro_adjust=to_decimal(r.appro_adjust),
            allotment=to_decimal(r.allotment),
            realignment=to_decimal(r.realignment),
            transfer_from=to_decimal(r.transfer_from),
            transfer_to=to_decimal(r.transfer_to),
            obligations_incurred=to_decimal(r.obligations_incurred),
            disbursement=to_decimal(r.disbursement),
        )
        recent_list.append({
            "id": r.id,
            "date_bms": str(r.date_bms) if r.date_bms else "",
            "particulars": r.particulars or "",
            "uacs_pap_code": r.uacs_pap_code or "",
            "account_code": r.account_code or "",
            "allotment": float(to_decimal(r.allotment)),
            "obligations_incurred": float(to_decimal(r.obligations_incurred)),
            "disbursement": float(to_decimal(r.disbursement)),
            "total_adjusted_allotment": float(r_bals["total_adjusted_allotment"]),
            "unobligated": float(r_bals["unobligated"]),
            "unpaid": float(r_bals["unpaid"]),
        })

    return {
        "school_name": target_school,
        "division": division_name,
        "region": region_name,
        "total_records": total_records,
        "total_adjusted_appro": float(adj_appro),
        "total_adjusted_allotment": float(adj_allotment),
        "total_obligations": float(obligations),
        "total_disbursements": float(disbursement),
        "unobligated_balance": float(unobligated),
        "unpaid_balance": float(unpaid),
        "unreleased_balance": float(unreleased),
        "utilization_rate": utilization_rate,
        "disbursement_rate": disbursement_rate,
        "recent_records": recent_list,
    }
