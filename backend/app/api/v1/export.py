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

    records = query.order_by(BMSRecord.operating_unit, BMSRecord.date_bms).all()

    output = io.BytesIO()
    ExcelExportService.export_to_stream(records, output)

    filename = f"CONSO_tempTable_{current_user.role}_{current_user.username}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

