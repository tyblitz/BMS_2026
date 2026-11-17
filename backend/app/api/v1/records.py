import json
import re
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.models.bms_record import BMSRecord
from app.models.user import User
from app.models.record_audit_log import RecordAuditLog
from app.schemas.bms_record import BMSRecordCreate, BMSRecordUpdate, BMSRecordResponse
from app.services.excel_ingestion import compute_row_hash
from app.api.deps import get_current_user
from app.core.cache import clear_analytics_cache

router = APIRouter(prefix="/records", tags=["BMS Records"])


def apply_role_scope(query, current_user: User):
    """Enforces backend-level data isolation based on hierarchical user role."""
    query = query.filter(BMSRecord.is_deleted == False)

    if current_user.role == "admin":
        return query
    elif current_user.role == "school":
        if not current_user.school_name:
            raise HTTPException(status_code=400, detail="User account missing assigned school_name")
        filters = [BMSRecord.operating_unit == current_user.school_name]
        if current_user.division:
            filters.append(BMSRecord.division == current_user.division)
        if current_user.region:
            filters.append(BMSRecord.region == current_user.region)
        return query.filter(*filters)
    elif current_user.role == "sdo":
        if not current_user.division:
            raise HTTPException(status_code=400, detail="User account missing assigned division")
        filters = [BMSRecord.division == current_user.division]
        if current_user.region:
            filters.append(BMSRecord.region == current_user.region)
        return query.filter(*filters)
    elif current_user.role == "region":
        if not current_user.region:
            raise HTTPException(status_code=400, detail="User account missing assigned region")
        return query.filter(BMSRecord.region == current_user.region)
    else:
        raise HTTPException(status_code=403, detail="Unrecognized role scope")


@router.get("", response_model=dict)
def list_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    operating_unit: Optional[str] = None,
    division: Optional[str] = None,
    region: Optional[str] = None,
    allotment_class: Optional[str] = None,
    account_code: Optional[str] = None,
    fund_source: Optional[str] = None,
    ppa_control: Optional[str] = None,
    ppa_code: Optional[str] = None,
    appropriation_type: Optional[str] = None,
    allotment_period: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(BMSRecord)
    query = apply_role_scope(query, current_user)

    # Optional filters
    if operating_unit:
        query = query.filter(BMSRecord.operating_unit == operating_unit)
    if division:
        query = query.filter(BMSRecord.division == division)
    if region:
        query = query.filter(BMSRecord.region == region)
    if allotment_class:
        query = query.filter(BMSRecord.allotment_class == allotment_class)
    if account_code:
        query = query.filter(BMSRecord.account_code == account_code)
    if fund_source:
        query = query.filter(BMSRecord.fund_source == fund_source)
    if ppa_code:
        query = query.filter(BMSRecord.ppa_code == ppa_code)
    if ppa_control:
        query = query.filter(BMSRecord.ppa_control.ilike(f"%{ppa_control}%"))
    if appropriation_type:
        query = query.filter(BMSRecord.appropriation_type == appropriation_type)
    if allotment_period:
        query = query.filter(BMSRecord.allotment_period == allotment_period)
    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                BMSRecord.particulars.ilike(s),
                BMSRecord.ppa_control.ilike(s),
                BMSRecord.ppa_code.ilike(s),
                BMSRecord.account_code.ilike(s),
                BMSRecord.operating_unit.ilike(s),
                BMSRecord.uacs_pap_code.ilike(s),
                BMSRecord.legal_basis.ilike(s)
            )
        )

    total = query.count()
    items = query.order_by(BMSRecord.created_on.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [BMSRecordResponse.model_validate(item) for item in items]
    }


@router.post("", response_model=BMSRecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: BMSRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Enforce hierarchical scope check on creation
    if current_user.role == "school":
        if payload.operating_unit != current_user.school_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"School users can only create records for their assigned school: '{current_user.school_name}'"
            )
        if current_user.division and payload.division != current_user.division:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"School users can only create records for their assigned division: '{current_user.division}'"
            )
        if current_user.region and payload.region != current_user.region:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"School users can only create records for their assigned region: '{current_user.region}'"
            )
    elif current_user.role == "sdo":
        if payload.division != current_user.division:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"SDO users can only create records for their assigned division: '{current_user.division}'"
            )
        if current_user.region and payload.region != current_user.region:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"SDO users can only create records for their assigned region: '{current_user.region}'"
            )
    elif current_user.role == "region" and payload.region != current_user.region:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Regional users can only create records for their assigned region: '{current_user.region}'"
        )

    row_data = payload.model_dump()
    row_hash = compute_row_hash(row_data)

    # Check for existing duplicate
    existing = db.query(BMSRecord).filter(BMSRecord.row_hash == row_hash, BMSRecord.is_deleted == False).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A record with identical transaction values already exists."
        )

    # Auto-extract PPA code and description
    if "ppa_control" in row_data and row_data["ppa_control"]:
        raw_ppa = str(row_data["ppa_control"]).strip()
        m = re.match(r"^(PPA\d+)\s*-\s*(.+)$", raw_ppa)
        if m:
            row_data["ppa_code"] = m.group(1)
            row_data["ppa_description"] = m.group(2)
        else:
            row_data["ppa_code"] = raw_ppa[:20]
            row_data["ppa_description"] = raw_ppa

    record = BMSRecord(
        **row_data,
        row_hash=row_hash,
        created_by=current_user.username,
        is_deleted=False
    )
    db.add(record)
    db.flush()

    # Immutable audit history
    audit_entry = RecordAuditLog(
        record_id=record.id,
        action="CREATE",
        changed_by=current_user.username,
        new_values=json.dumps(row_data, default=str),
        reason="Manual record creation"
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(record)
    clear_analytics_cache()
    return BMSRecordResponse.model_validate(record)


@router.get("/operating-units", response_model=list[str])
def list_operating_units(
    division: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns distinct operating units available under the user's role scope."""
    query = db.query(BMSRecord.operating_unit).distinct()
    query = apply_role_scope(query, current_user)
    if division:
        query = query.filter(BMSRecord.division == division)
    results = query.order_by(BMSRecord.operating_unit.asc()).all()
    return [r[0] for r in results if r[0]]


@router.get("/divisions", response_model=list[str])
def list_divisions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns distinct divisions available under the user's role scope."""
    query = db.query(BMSRecord.division).distinct()
    query = apply_role_scope(query, current_user)
    results = query.order_by(BMSRecord.division.asc()).all()
    return [r[0] for r in results if r[0]]


@router.get("/{id}", response_model=BMSRecordResponse)
def get_record(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(BMSRecord).filter(BMSRecord.id == id)
    query = apply_role_scope(query, current_user)
    record = query.first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found or outside authorized scope")
    return BMSRecordResponse.model_validate(record)


@router.put("/{id}", response_model=BMSRecordResponse)
def update_record(
    id: str,
    payload: BMSRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(BMSRecord).filter(BMSRecord.id == id)
    query = apply_role_scope(query, current_user)
    record = query.first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found or outside authorized scope")

    update_data = payload.model_dump(exclude_unset=True)

    # Validate that updating organizational ownership does not violate user's role scope
    if current_user.role == "school":
        if "operating_unit" in update_data and update_data["operating_unit"] != current_user.school_name:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="School users cannot change record operating_unit.")
        if "division" in update_data and current_user.division and update_data["division"] != current_user.division:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="School users cannot change record division.")
        if "region" in update_data and current_user.region and update_data["region"] != current_user.region:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="School users cannot change record region.")
    elif current_user.role == "sdo":
        if "division" in update_data and update_data["division"] != current_user.division:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SDO users cannot change record division.")
        if "region" in update_data and current_user.region and update_data["region"] != current_user.region:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SDO users cannot change record region.")
    elif current_user.role == "region":
        if "region" in update_data and update_data["region"] != current_user.region:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Regional users cannot change record region.")

    old_values = {f: getattr(record, f) for f in update_data.keys()}
    for field, val in update_data.items():
        setattr(record, field, val)

    # Auto-update PPA code/description if ppa_control was updated
    if "ppa_control" in update_data and update_data["ppa_control"]:
        raw_ppa = str(update_data["ppa_control"]).strip()
        m = re.match(r"^(PPA\d+)\s*-\s*(.+)$", raw_ppa)
        if m:
            record.ppa_code = m.group(1)
            record.ppa_description = m.group(2)
        else:
            record.ppa_code = raw_ppa[:20]
            record.ppa_description = raw_ppa

    # Recompute row_hash with updated values
    hash_input = {
        "OperatingUnit": record.operating_unit,
        "DateBMS": record.date_bms,
        "AccountCode": record.account_code,
        "UACSPAPCODE": record.uacs_pap_code,
        "Particulars": record.particulars,
        "ObligationsIncurred": record.obligations_incurred,
        "Disbursement": record.disbursement,
        "Appropriations": record.appropriations,
        "Allotment": record.allotment,
        "FundSource": record.fund_source,
        "TransferTo": record.transfer_to,
        "TransferFrom": record.transfer_from,
        "DVAmount": record.dv_amount
    }
    record.row_hash = compute_row_hash(hash_input)
    record.edited_on = datetime.now(timezone.utc)
    record.edited_by = current_user.username

    # Immutable audit history
    audit_entry = RecordAuditLog(
        record_id=record.id,
        action="UPDATE",
        changed_by=current_user.username,
        old_values=json.dumps(old_values, default=str),
        new_values=json.dumps(update_data, default=str),
        reason="Manual record update"
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(record)
    clear_analytics_cache()
    return BMSRecordResponse.model_validate(record)


@router.delete("/{id}", response_model=dict)
def delete_record(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete only. Never physically removes from database."""
    query = db.query(BMSRecord).filter(BMSRecord.id == id)
    query = apply_role_scope(query, current_user)
    record = query.first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found or outside authorized scope")

    record.soft_delete(username=current_user.username)

    # Immutable audit history
    audit_entry = RecordAuditLog(
        record_id=record.id,
        action="DELETE",
        changed_by=current_user.username,
        old_values=json.dumps({"is_deleted": False}, default=str),
        new_values=json.dumps({"is_deleted": True}, default=str),
        reason="Soft deletion"
    )
    db.add(audit_entry)

    db.commit()
    clear_analytics_cache()
    return {"status": "success", "message": f"Record {id} soft-deleted successfully"}


@router.post("/{id}/restore", response_model=BMSRecordResponse)
def restore_record(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restores a soft-deleted record back to active status with strict role scope checking."""
    query = db.query(BMSRecord).filter(BMSRecord.id == id, BMSRecord.is_deleted == True)

    # Enforce role scope on restore
    if current_user.role == "school":
        filters = [BMSRecord.operating_unit == current_user.school_name]
        if current_user.division:
            filters.append(BMSRecord.division == current_user.division)
        if current_user.region:
            filters.append(BMSRecord.region == current_user.region)
        query = query.filter(*filters)
    elif current_user.role == "sdo":
        filters = [BMSRecord.division == current_user.division]
        if current_user.region:
            filters.append(BMSRecord.region == current_user.region)
        query = query.filter(*filters)
    elif current_user.role == "region":
        query = query.filter(BMSRecord.region == current_user.region)

    record = query.first()
    if not record:
        raise HTTPException(status_code=404, detail="Archived record not found or outside authorized scope.")

    record.is_deleted = False
    record.deleted_on = None
    record.deleted_by = None
    record.edited_on = datetime.now(timezone.utc)
    record.edited_by = current_user.username

    # Immutable audit history
    audit_entry = RecordAuditLog(
        record_id=record.id,
        action="RESTORE",
        changed_by=current_user.username,
        old_values=json.dumps({"is_deleted": True}, default=str),
        new_values=json.dumps({"is_deleted": False}, default=str),
        reason="Restored archived record"
    )
    db.add(audit_entry)

    db.commit()
    db.refresh(record)
    clear_analytics_cache()
    return BMSRecordResponse.model_validate(record)


