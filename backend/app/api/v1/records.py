from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.models.bms_record import BMSRecord
from app.models.user import User
from app.schemas.bms_record import BMSRecordCreate, BMSRecordUpdate, BMSRecordResponse
from app.services.excel_ingestion import compute_row_hash
from app.api.deps import get_current_user

router = APIRouter(prefix="/records", tags=["BMS Records"])


def apply_role_scope(query, current_user: User):
    """Enforces backend-level data isolation based on user role."""
    query = query.filter(BMSRecord.is_deleted == False)

    if current_user.role == "admin":
        return query
    elif current_user.role == "school":
        if not current_user.school_name:
            raise HTTPException(status_code=400, detail="User account missing assigned school_name")
        return query.filter(BMSRecord.operating_unit == current_user.school_name)
    elif current_user.role == "sdo":
        if not current_user.division:
            raise HTTPException(status_code=400, detail="User account missing assigned division")
        return query.filter(BMSRecord.division == current_user.division)
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
    if ppa_control:
        query = query.filter(BMSRecord.ppa_control.ilike(f"%{ppa_control}%"))
    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                BMSRecord.particulars.ilike(s),
                BMSRecord.ppa_control.ilike(s),
                BMSRecord.account_code.ilike(s),
                BMSRecord.operating_unit.ilike(s),
                BMSRecord.uacs_pap_code.ilike(s)
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
    # Enforce scope check on creation
    if current_user.role == "school" and payload.operating_unit != current_user.school_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"School users can only create records for their assigned school: '{current_user.school_name}'"
        )
    elif current_user.role == "sdo" and payload.division != current_user.division:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"SDO users can only create records for their assigned division: '{current_user.division}'"
        )
    elif current_user.role == "region" and payload.region != current_user.region:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Regional users can only create records for their assigned region: '{current_user.region}'"
        )

    row_data = payload.model_dump()
    # Normalize keys for row_hash calculation
    hash_input = {
        "OperatingUnit": row_data.get("operating_unit"),
        "DateBMS": row_data.get("date_bms"),
        "AccountCode": row_data.get("account_code"),
        "UACSPAPCODE": row_data.get("uacs_pap_code"),
        "Particulars": row_data.get("particulars"),
        "ObligationsIncurred": row_data.get("obligations_incurred"),
        "Disbursement": row_data.get("disbursement"),
        "Appropriations": row_data.get("appropriations"),
        "Allotment": row_data.get("allotment"),
        "FundSource": row_data.get("fund_source"),
        "TransferTo": row_data.get("transfer_to"),
        "TransferFrom": row_data.get("transfer_from"),
        "DVAmount": row_data.get("dv_amount")
    }
    row_hash = compute_row_hash(hash_input)

    # Check for existing duplicate
    existing = db.query(BMSRecord).filter(BMSRecord.row_hash == row_hash, BMSRecord.is_deleted == False).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A record with identical transaction values already exists."
        )

    record = BMSRecord(
        **row_data,
        row_hash=row_hash,
        created_by=current_user.username,
        is_deleted=False
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return BMSRecordResponse.model_validate(record)


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
    for field, val in update_data.items():
        setattr(record, field, val)

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

    db.commit()
    db.refresh(record)
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
    db.commit()
    return {"status": "success", "message": f"Record {id} soft-deleted successfully"}
