from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, computed_field, ConfigDict
from app.services.calculations import calculate_balances


class BMSRecordBase(BaseModel):
    ppa_control: Optional[str] = None
    appropriation_type: Optional[str] = None
    allotment_period: Optional[str] = None
    allotment_class: Optional[str] = None
    date_bms: Optional[str] = None
    account_code: Optional[str] = None
    
    obligations_incurred: Decimal = Decimal("0.00")
    disbursement: Decimal = Decimal("0.00")
    appropriations: Decimal = Decimal("0.00")
    allotment: Decimal = Decimal("0.00")
    transfer_to: Decimal = Decimal("0.00")
    transfer_from: Decimal = Decimal("0.00")
    
    particulars: Optional[str] = None
    uacs_pap_code: Optional[str] = None
    dv_amount: Decimal = Decimal("0.00")
    
    region: str
    division: str
    operating_unit: str
    org_code_uacs: Optional[str] = None
    
    appro_adjust: Decimal = Decimal("0.00")
    realignment: Decimal = Decimal("0.00")
    fund_source: Optional[str] = None
    locality: Optional[str] = None
    legal_basis: Optional[str] = None
    rc: Optional[str] = None
    reg: Optional[str] = "NA"
    ccet_code: Optional[str] = "NA"
    ledger: Optional[str] = "NA"


class BMSRecordCreate(BMSRecordBase):
    pass


class BMSRecordUpdate(BaseModel):
    ppa_control: Optional[str] = None
    appropriation_type: Optional[str] = None
    allotment_period: Optional[str] = None
    allotment_class: Optional[str] = None
    date_bms: Optional[str] = None
    account_code: Optional[str] = None
    
    obligations_incurred: Optional[Decimal] = None
    disbursement: Optional[Decimal] = None
    appropriations: Optional[Decimal] = None
    allotment: Optional[Decimal] = None
    transfer_to: Optional[Decimal] = None
    transfer_from: Optional[Decimal] = None
    
    particulars: Optional[str] = None
    uacs_pap_code: Optional[str] = None
    dv_amount: Optional[Decimal] = None
    
    region: Optional[str] = None
    division: Optional[str] = None
    operating_unit: Optional[str] = None
    org_code_uacs: Optional[str] = None
    
    appro_adjust: Optional[Decimal] = None
    realignment: Optional[Decimal] = None
    fund_source: Optional[str] = None
    locality: Optional[str] = None
    legal_basis: Optional[str] = None
    rc: Optional[str] = None
    reg: Optional[str] = None
    ccet_code: Optional[str] = None
    ledger: Optional[str] = None


class BMSRecordResponse(BMSRecordBase):
    id: str
    row_hash: str
    is_deleted: bool
    created_on: datetime
    created_by: str
    edited_on: Optional[datetime] = None
    edited_by: Optional[str] = None
    deleted_on: Optional[datetime] = None
    deleted_by: Optional[str] = None

    @computed_field
    def total_adjusted_appro(self) -> Decimal:
        return calculate_balances(
            appropriations=self.appropriations,
            appro_adjust=self.appro_adjust
        )["total_adjusted_appro"]

    @computed_field
    def total_adjusted_allotment(self) -> Decimal:
        return calculate_balances(
            allotment=self.allotment,
            realignment=self.realignment,
            transfer_from=self.transfer_from,
            transfer_to=self.transfer_to
        )["total_adjusted_allotment"]

    @computed_field
    def unobligated(self) -> Decimal:
        return calculate_balances(
            allotment=self.allotment,
            realignment=self.realignment,
            transfer_from=self.transfer_from,
            transfer_to=self.transfer_to,
            obligations_incurred=self.obligations_incurred
        )["unobligated"]

    @computed_field
    def unpaid(self) -> Decimal:
        return calculate_balances(
            obligations_incurred=self.obligations_incurred,
            disbursement=self.disbursement
        )["unpaid"]

    @computed_field
    def unreleased(self) -> Decimal:
        return calculate_balances(
            appropriations=self.appropriations,
            appro_adjust=self.appro_adjust,
            allotment=self.allotment,
            realignment=self.realignment,
            transfer_from=self.transfer_from,
            transfer_to=self.transfer_to
        )["unreleased"]

    model_config = ConfigDict(from_attributes=True)


class BMSRecordFilter(BaseModel):
    region: Optional[str] = None
    division: Optional[str] = None
    operating_unit: Optional[str] = None
    allotment_class: Optional[str] = None
    fund_source: Optional[str] = None
    account_code: Optional[str] = None
    ppa_control: Optional[str] = None
    date_bms: Optional[str] = None
    search: Optional[str] = None
    skip: int = 0
    limit: int = 50
