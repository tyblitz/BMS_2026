import pytest
from decimal import Decimal
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.services.calculations import calculate_balances
from app.models.bms_record import BMSRecord
from app.models.user import User
from app.schemas.bms_record import BMSRecordResponse
from app.core.database import db_manager


def test_password_and_jwt():
    pwd = "SecurePassword2026!"
    hashed = get_password_hash(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    
    token = create_access_token({"sub": "admin", "role": "admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "admin"
    assert payload.get("role") == "admin"


def test_dynamic_calculations():
    balances = calculate_balances(
        appropriations=Decimal("500000.00"),
        appro_adjust=Decimal("20000.00"),
        allotment=Decimal("450000.00"),
        realignment=Decimal("10000.00"),
        transfer_from=Decimal("5000.00"),
        transfer_to=Decimal("15000.00"),
        obligations_incurred=Decimal("300000.00"),
        disbursement=Decimal("200000.00")
    )
    # Total Adjusted Appro = 500,000 + 20,000 = 520,000
    assert balances["total_adjusted_appro"] == Decimal("520000.00")
    # Total Adjusted Allotment = 450,000 + 10,000 + 5,000 - 15,000 = 450,000
    assert balances["total_adjusted_allotment"] == Decimal("450000.00")
    # Unobligated = 450,000 - 300,000 = 150,000
    assert balances["unobligated"] == Decimal("150000.00")
    # Unpaid = 300,000 - 200,000 = 100,000
    assert balances["unpaid"] == Decimal("100000.00")
    # Unreleased = 520,000 - 450,000 = 70,000
    assert balances["unreleased"] == Decimal("70000.00")


def test_audit_mixin_and_soft_delete():
    rec = BMSRecord(
        row_hash="test_hash_12345",
        region="NCR",
        division="Caloocan",
        operating_unit="Sample High School",
        created_by="test_encoder"
    )
    assert rec.is_deleted is False
    rec.soft_delete(username="editor_user")
    assert rec.is_deleted is True
    assert rec.deleted_by == "editor_user"
    assert rec.deleted_on is not None


def test_database_manager_test_connection():
    ok, msg = db_manager.test_connection(db_manager.active_url)
    assert ok is True
