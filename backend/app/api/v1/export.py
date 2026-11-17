import io
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.bms_record import BMSRecord
from app.models.user import User
from app.services.excel_export import ExcelExportService
from app.api.v1.records import apply_role_scope
from app.api.deps import get_current_user

router = APIRouter(prefix="/export", tags=["Excel Export"])


@router.get("")
@router.get("/excel")
def export_consolidated_excel(
    operating_unit: Optional[str] = None,
    division: Optional[str] = None,
    region: Optional[str] = None,
    allotment_class: Optional[str] = None,
    fund_source: Optional[str] = None,
    account_code: Optional[str] = None,
    appropriation_type: Optional[str] = None,
    allotment_period: Optional[str] = None,
    ppa_code: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(BMSRecord)
    query = apply_role_scope(query, current_user)

    if operating_unit:
        query = query.filter(BMSRecord.operating_unit == operating_unit)
    if division:
        query = query.filter(BMSRecord.division == division)
    if region:
        query = query.filter(BMSRecord.region == region)
    if allotment_class:
        query = query.filter(BMSRecord.allotment_class == allotment_class)
    if fund_source:
        query = query.filter(BMSRecord.fund_source == fund_source)
    if account_code:
        query = query.filter(BMSRecord.account_code == account_code)
    if appropriation_type:
        query = query.filter(BMSRecord.appropriation_type == appropriation_type)
    if allotment_period:
        query = query.filter(BMSRecord.allotment_period == allotment_period)
    if ppa_code:
        query = query.filter(BMSRecord.ppa_code == ppa_code)

    # Use yield_per for memory-safe chunked streaming
    records = query.order_by(BMSRecord.operating_unit, BMSRecord.date_bms).yield_per(1000)

    output = io.BytesIO()
    ExcelExportService.export_to_stream(records, output)

    filename = f"CONSO_tempTable_{current_user.role}_{current_user.username}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/ppa-summary")
def export_ppa_summary_excel(
    operating_unit: Optional[str] = None,
    division: Optional[str] = None,
    region: Optional[str] = None,
    allotment_class: Optional[str] = None,
    fund_source: Optional[str] = None,
    appropriation_type: Optional[str] = None,
    allotment_period: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.api.v1.records import list_records_by_ppa
    from openpyxl import Workbook

    ppa_list = list_records_by_ppa(
        operating_unit=operating_unit,
        division=division,
        region=region,
        allotment_class=allotment_class,
        fund_source=fund_source,
        appropriation_type=appropriation_type,
        allotment_period=allotment_period,
        search=search,
        current_user=current_user,
        db=db
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "PPA Summary"

    headers = [
        "PPA Code", "PPA Description", "Transaction Count",
        "Total Adjusted Appro", "Total Adjusted Allotment",
        "Obligations Incurred", "Disbursements",
        "Unobligated Balance", "Unpaid Obligations", "Unreleased Balance"
    ]
    ws.append(headers)

    for item in ppa_list:
        ws.append([
            item["ppa_code"],
            item["ppa_description"],
            item["transaction_count"],
            float(item["total_adjusted_appro"]),
            float(item["total_adjusted_allotment"]),
            float(item["obligations_incurred"]),
            float(item["disbursement"]),
            float(item["unobligated"]),
            float(item["unpaid"]),
            float(item["unreleased"])
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"PPA_Summary_{current_user.role}_{current_user.username}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

