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
from app.core.cache import get_analytics_cache, set_analytics_cache

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

    # Use context from authenticated user or quick lookup
    division_name = current_user.division or ""
    region_name = current_user.region or "National Capital Region (NCR)"
    if not division_name:
        sample_rec = (
            db.query(BMSRecord.division, BMSRecord.region)
            .filter(BMSRecord.operating_unit == target_school, BMSRecord.is_deleted == False)
            .first()
        )
        if sample_rec:
            division_name = sample_rec.division
            region_name = sample_rec.region

    # Fetch 5 records using lightweight column projection (avoids full ORM entity hydration)
    recent_records = (
        db.query(
            BMSRecord.id,
            BMSRecord.date_bms,
            BMSRecord.particulars,
            BMSRecord.uacs_pap_code,
            BMSRecord.account_code,
            BMSRecord.appropriations,
            BMSRecord.appro_adjust,
            BMSRecord.allotment,
            BMSRecord.realignment,
            BMSRecord.transfer_from,
            BMSRecord.transfer_to,
            BMSRecord.obligations_incurred,
            BMSRecord.disbursement,
        )
        .filter(BMSRecord.operating_unit == target_school, BMSRecord.is_deleted == False)
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


@router.get("/division-summary")
def get_division_summary(
    division_name: Optional[str] = Query(None, description="Division name to query (for admin/region)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns aggregated financial health and school compliance matrix for an SDO division.
    Strictly adheres to dynamic calculations (Rule 1) and division-level RBAC scoping.
    """
    if current_user.role == "sdo":
        target_division = current_user.division
    elif current_user.role in ["admin", "region"]:
        target_division = division_name or "Division of Caloocan"
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="School encoders cannot access division-wide consolidation analytics.",
        )

    if not target_division:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A division name must be specified.",
        )

    # 1. Division Totals
    div_query = db.query(
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
        BMSRecord.division == target_division,
    ).first()

    total_records = div_query.total_records if div_query else 0
    appro = to_decimal(div_query.sum_appro if div_query else 0)
    appro_adj = to_decimal(div_query.sum_appro_adjust if div_query else 0)
    allot = to_decimal(div_query.sum_allotment if div_query else 0)
    realign = to_decimal(div_query.sum_realignment if div_query else 0)
    trans_from = to_decimal(div_query.sum_transfer_from if div_query else 0)
    trans_to = to_decimal(div_query.sum_transfer_to if div_query else 0)
    obligations = to_decimal(div_query.sum_obligations if div_query else 0)
    disbursement = to_decimal(div_query.sum_disbursement if div_query else 0)

    bals = calculate_balances(
        appropriations=appro,
        appro_adjust=appro_adj,
        allotment=allot,
        realignment=realign,
        transfer_from=trans_from,
        transfer_to=trans_to,
        obligations_incurred=obligations,
        disbursement=disbursement,
    )

    adj_allotment = bals["total_adjusted_allotment"]
    unobligated = bals["unobligated"]
    unpaid = bals["unpaid"]
    adj_appro = bals["total_adjusted_appro"]

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

    # 2. School Breakdown Matrix under this Division
    school_rows = (
        db.query(
            BMSRecord.operating_unit.label("school_name"),
            func.count(BMSRecord.id).label("record_count"),
            func.coalesce(func.sum(BMSRecord.allotment), 0).label("sum_allot"),
            func.coalesce(func.sum(BMSRecord.realignment), 0).label("sum_realign"),
            func.coalesce(func.sum(BMSRecord.transfer_from), 0).label("sum_tfrom"),
            func.coalesce(func.sum(BMSRecord.transfer_to), 0).label("sum_tto"),
            func.coalesce(func.sum(BMSRecord.obligations_incurred), 0).label("sum_obli"),
            func.coalesce(func.sum(BMSRecord.disbursement), 0).label("sum_disb"),
        )
        .filter(
            BMSRecord.is_deleted == False,
            BMSRecord.division == target_division,
        )
        .group_by(BMSRecord.operating_unit)
        .order_by(BMSRecord.operating_unit.asc())
        .all()
    )

    schools_matrix = []
    for s in school_rows:
        s_allot = to_decimal(s.sum_allot) + to_decimal(s.sum_realign) + to_decimal(s.sum_tfrom) - to_decimal(s.sum_tto)
        s_obli = to_decimal(s.sum_obli)
        s_disb = to_decimal(s.sum_disb)
        s_unobli = s_allot - s_obli
        s_unpaid = s_obli - s_disb
        s_rate = (
            round(float((s_obli / s_allot) * Decimal("100")), 2)
            if s_allot > Decimal("0")
            else 0.0
        )
        
        status_label = "🟢 High Utilization" if s_rate >= 80 else "🟡 Active Submission" if s.record_count > 0 else "⚪ No Data"

        schools_matrix.append({
            "school_name": s.school_name,
            "record_count": s.record_count,
            "total_adjusted_allotment": float(s_allot),
            "total_obligations": float(s_obli),
            "total_disbursements": float(s_disb),
            "unobligated_balance": float(s_unobli),
            "unpaid_balance": float(s_unpaid),
            "utilization_rate": s_rate,
            "status": status_label,
        })

    return {
        "division": target_division,
        "region": "National Capital Region (NCR)",
        "total_schools": len(schools_matrix),
        "total_records": total_records,
        "total_adjusted_appro": float(adj_appro),
        "total_adjusted_allotment": float(adj_allotment),
        "total_obligations": float(obligations),
        "total_disbursements": float(disbursement),
        "unobligated_balance": float(unobligated),
        "unpaid_balance": float(unpaid),
        "utilization_rate": utilization_rate,
        "disbursement_rate": disbursement_rate,
        "schools_matrix": schools_matrix,
    }


@router.get("/region-summary")
def get_region_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns executive macro-level financial analytics across all 16 SDOs in NCR.
    Optimized single-pass aggregation with instant caching.
    Strictly adheres to dynamic balance formulas (Rule 1).
    """
    if current_user.role not in ["admin", "region"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Regional executive analytics require Regional Office or Administrator authorization.",
        )

    cache_key = "analytics_region_summary_ncr"
    cached = get_analytics_cache(cache_key)
    if cached is not None:
        return cached

    target_region = "National Capital Region (NCR)"

    # Single-pass grouped aggregation across all divisions (avoids second full table scan)
    div_rows = (
        db.query(
            BMSRecord.division.label("division_name"),
            func.count(BMSRecord.id).label("record_count"),
            func.count(func.distinct(BMSRecord.operating_unit)).label("schools_count"),
            func.coalesce(func.sum(BMSRecord.appropriations), 0).label("sum_appro"),
            func.coalesce(func.sum(BMSRecord.appro_adjust), 0).label("sum_appro_adjust"),
            func.coalesce(func.sum(BMSRecord.allotment), 0).label("sum_allot"),
            func.coalesce(func.sum(BMSRecord.realignment), 0).label("sum_realign"),
            func.coalesce(func.sum(BMSRecord.transfer_from), 0).label("sum_tfrom"),
            func.coalesce(func.sum(BMSRecord.transfer_to), 0).label("sum_tto"),
            func.coalesce(func.sum(BMSRecord.obligations_incurred), 0).label("sum_obli"),
            func.coalesce(func.sum(BMSRecord.disbursement), 0).label("sum_disb"),
        )
        .filter(
            BMSRecord.is_deleted == False,
            BMSRecord.region == target_region,
        )
        .group_by(BMSRecord.division)
        .all()
    )

    divisions_matrix = []
    grand_records = 0
    grand_schools = 0
    grand_appro = Decimal("0.00")
    grand_appro_adj = Decimal("0.00")
    grand_allot = Decimal("0.00")
    grand_realign = Decimal("0.00")
    grand_tfrom = Decimal("0.00")
    grand_tto = Decimal("0.00")
    grand_obli = Decimal("0.00")
    grand_disb = Decimal("0.00")

    for d in div_rows:
        d_appro = to_decimal(d.sum_appro)
        d_appro_adj = to_decimal(d.sum_appro_adjust)
        d_allot_raw = to_decimal(d.sum_allot)
        d_realign = to_decimal(d.sum_realign)
        d_tfrom = to_decimal(d.sum_tfrom)
        d_tto = to_decimal(d.sum_tto)
        d_obli = to_decimal(d.sum_obli)
        d_disb = to_decimal(d.sum_disb)

        # Accumulate regional grand totals in single pass
        grand_records += d.record_count
        grand_schools += d.schools_count
        grand_appro += d_appro
        grand_appro_adj += d_appro_adj
        grand_allot += d_allot_raw
        grand_realign += d_realign
        grand_tfrom += d_tfrom
        grand_tto += d_tto
        grand_obli += d_obli
        grand_disb += d_disb

        # Division-level dynamic balance formulas (Rule 1)
        d_bals = calculate_balances(
            appropriations=d_appro,
            appro_adjust=d_appro_adj,
            allotment=d_allot_raw,
            realignment=d_realign,
            transfer_from=d_tfrom,
            transfer_to=d_tto,
            obligations_incurred=d_obli,
            disbursement=d_disb,
        )

        d_adj_allot = d_bals["total_adjusted_allotment"]
        d_unobli = d_bals["unobligated"]
        d_unpaid = d_bals["unpaid"]
        d_rate = (
            round(float((d_obli / d_adj_allot) * Decimal("100")), 2)
            if d_adj_allot > Decimal("0")
            else 0.0
        )

        divisions_matrix.append({
            "division": d.division_name,
            "schools_count": d.schools_count,
            "record_count": d.record_count,
            "total_adjusted_allotment": float(d_adj_allot),
            "total_obligations": float(d_obli),
            "total_disbursements": float(d_disb),
            "unobligated_balance": float(d_unobli),
            "unpaid_balance": float(d_unpaid),
            "utilization_rate": d_rate,
        })

    # Sort divisions by utilization rate descending for leaderboard ranking
    divisions_matrix.sort(key=lambda x: x["utilization_rate"], reverse=True)

    # Regional macro balances (Rule 1)
    reg_bals = calculate_balances(
        appropriations=grand_appro,
        appro_adjust=grand_appro_adj,
        allotment=grand_allot,
        realignment=grand_realign,
        transfer_from=grand_tfrom,
        transfer_to=grand_tto,
        obligations_incurred=grand_obli,
        disbursement=grand_disb,
    )

    reg_adj_allot = reg_bals["total_adjusted_allotment"]
    reg_unobli = reg_bals["unobligated"]
    reg_unpaid = reg_bals["unpaid"]
    reg_adj_appro = reg_bals["total_adjusted_appro"]

    reg_utilization = (
        round(float((grand_obli / reg_adj_allot) * Decimal("100")), 2)
        if reg_adj_allot > Decimal("0")
        else 0.0
    )
    reg_disbursement = (
        round(float((grand_disb / grand_obli) * Decimal("100")), 2)
        if grand_obli > Decimal("0")
        else 0.0
    )

    result = {
        "region": target_region,
        "total_divisions": len(divisions_matrix),
        "total_schools": grand_schools,
        "total_records": grand_records,
        "total_adjusted_appro": float(reg_adj_appro),
        "total_adjusted_allotment": float(reg_adj_allot),
        "total_obligations": float(grand_obli),
        "total_disbursements": float(grand_disb),
        "unobligated_balance": float(reg_unobli),
        "unpaid_balance": float(reg_unpaid),
        "utilization_rate": reg_utilization,
        "disbursement_rate": reg_disbursement,
        "divisions_matrix": divisions_matrix,
    }

    # Store in cache with 60-second TTL
    set_analytics_cache(cache_key, result, ttl_seconds=60)
    return result


@router.get("/admin-summary")
def get_admin_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns administrative control center telemetry: database health, user metrics,
    and system-wide financial figures.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System telemetry requires Administrator authorization.",
        )

    # 1. Database telemetry
    from app.core.database import db_manager
    active_url = db_manager.active_url
    engine_name = "SQLite"
    if active_url.startswith("mysql"):
        engine_name = "MySQL / MariaDB"
    elif active_url.startswith("postgresql"):
        engine_name = "PostgreSQL"

    active_records_count = db.query(func.count(BMSRecord.id)).filter(BMSRecord.is_deleted == False).scalar() or 0
    deleted_records_count = db.query(func.count(BMSRecord.id)).filter(BMSRecord.is_deleted == True).scalar() or 0

    # 2. User directory metrics
    total_users = db.query(func.count(User.id)).scalar() or 0
    admin_users = db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0
    region_users = db.query(func.count(User.id)).filter(User.role == "region").scalar() or 0
    sdo_users = db.query(func.count(User.id)).filter(User.role == "sdo").scalar() or 0
    school_users = db.query(func.count(User.id)).filter(User.role == "school").scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0

    # 3. Operational Counts
    divisions_count = db.query(func.count(func.distinct(BMSRecord.division))).filter(BMSRecord.is_deleted == False).scalar() or 0
    schools_count = db.query(func.count(func.distinct(BMSRecord.operating_unit))).filter(BMSRecord.is_deleted == False).scalar() or 0

    # 4. Financial totals
    fin_query = db.query(
        func.coalesce(func.sum(BMSRecord.appropriations), 0).label("sum_appro"),
        func.coalesce(func.sum(BMSRecord.appro_adjust), 0).label("sum_appro_adjust"),
        func.coalesce(func.sum(BMSRecord.allotment), 0).label("sum_allotment"),
        func.coalesce(func.sum(BMSRecord.realignment), 0).label("sum_realignment"),
        func.coalesce(func.sum(BMSRecord.transfer_from), 0).label("sum_transfer_from"),
        func.coalesce(func.sum(BMSRecord.transfer_to), 0).label("sum_transfer_to"),
        func.coalesce(func.sum(BMSRecord.obligations_incurred), 0).label("sum_obligations"),
        func.coalesce(func.sum(BMSRecord.disbursement), 0).label("sum_disbursement"),
    ).filter(BMSRecord.is_deleted == False).first()

    appro = to_decimal(fin_query.sum_appro if fin_query else 0)
    appro_adj = to_decimal(fin_query.sum_appro_adjust if fin_query else 0)
    allot = to_decimal(fin_query.sum_allotment if fin_query else 0)
    realign = to_decimal(fin_query.sum_realignment if fin_query else 0)
    trans_from = to_decimal(fin_query.sum_transfer_from if fin_query else 0)
    trans_to = to_decimal(fin_query.sum_transfer_to if fin_query else 0)
    obligations = to_decimal(fin_query.sum_obligations if fin_query else 0)
    disbursement = to_decimal(fin_query.sum_disbursement if fin_query else 0)

    bals = calculate_balances(
        appropriations=appro,
        appro_adjust=appro_adj,
        allotment=allot,
        realignment=realign,
        transfer_from=trans_from,
        transfer_to=trans_to,
        obligations_incurred=obligations,
        disbursement=disbursement,
    )

    adj_allotment = bals["total_adjusted_allotment"]
    unobligated = bals["unobligated"]
    unpaid = bals["unpaid"]

    utilization_rate = (
        round(float((obligations / adj_allotment) * Decimal("100")), 2)
        if adj_allotment > Decimal("0")
        else 0.0
    )

    return {
        "database": {
            "engine": engine_name,
            "url_display": active_url.split("?")[0] if "@" not in active_url else active_url.split("@")[-1],
            "active_records": active_records_count,
            "deleted_records": deleted_records_count,
            "status": "Connected & Operational",
        },
        "users": {
            "total": total_users,
            "admin": admin_users,
            "region": region_users,
            "sdo": sdo_users,
            "school": school_users,
            "active": active_users,
        },
        "operational": {
            "divisions_count": divisions_count,
            "schools_count": schools_count,
        },
        "financial": {
            "total_adjusted_allotment": float(adj_allotment),
            "total_obligations": float(obligations),
            "total_disbursements": float(disbursement),
            "unobligated_balance": float(unobligated),
            "unpaid_balance": float(unpaid),
            "utilization_rate": utilization_rate,
        },
    }
