import uuid
from sqlalchemy import Column, String, Numeric, Text, Integer, Index
from app.models.base import Base, AuditMixin


class BMSRecord(Base, AuditMixin):
    """
    Budget Monitoring System (BMS) Line Record.
    Stores the 28 raw business fields + UUID primary key + row_hash deduplication key + audit trail.
    Calculated columns (TOTAL ADJUSTED APPRO, TOTAL ADJUSTED ALLOTMENT, UNOBLIGATED, UNPAID, UNRELEASED)
    are strictly dynamically calculated and NOT stored.
    """
    __tablename__ = "bms_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Deterministic SHA-256 deduplication fingerprint (Non-unique to prevent collapsing legitimate distinct lines)
    row_hash = Column(String(64), unique=False, nullable=False, index=True)

    # 28 Raw Business Fields + Normalized PPA structure
    ppa_control = Column(String(255), nullable=True, index=True)       # A: PPAControl
    ppa_code = Column(String(20), nullable=True, index=True)           # Normalized PPA Code (e.g. PPA350)
    ppa_description = Column(String(255), nullable=True)               # Normalized PPA Description
    appropriation_type = Column(String(100), nullable=True)            # B: AppropriationType
    allotment_period = Column(String(100), nullable=True)              # C: AllotmentPeriod
    allotment_class = Column(String(50), nullable=True, index=True)    # D: AllotmentClass (PS, MOOE, CO)
    date_bms = Column(String(50), nullable=True, index=True)           # E: DateBMS (Excel serial or date)
    account_code = Column(String(50), nullable=True, index=True)       # F: AccountCode (UACS object code)
    
    obligations_incurred = Column(Numeric(16, 2), default=0.00, nullable=False) # G: ObligationsIncurred
    disbursement = Column(Numeric(16, 2), default=0.00, nullable=False)         # H: Disbursement
    appropriations = Column(Numeric(16, 2), default=0.00, nullable=False)       # I: Appropriations
    allotment = Column(Numeric(16, 2), default=0.00, nullable=False)            # J: Allotment
    transfer_to = Column(Numeric(16, 2), default=0.00, nullable=False)          # K: TransferTo
    transfer_from = Column(Numeric(16, 2), default=0.00, nullable=False)        # L: TransferFrom
    
    particulars = Column(Text, nullable=True)                          # M: Particulars
    uacs_pap_code = Column(String(100), nullable=True, index=True)     # N: UACSPAPCODE
    dv_amount = Column(Numeric(16, 2), default=0.00, nullable=False)   # O: DVAmount
    
    # Scoping Fields
    region = Column(String(150), nullable=False, index=True)           # P: Region
    division = Column(String(150), nullable=False, index=True)         # Q: Division
    operating_unit = Column(String(150), nullable=False, index=True)   # R: OperatingUnit (School/Station)
    org_code_uacs = Column(String(50), nullable=True, index=True)      # S: OrgCodeUACS
    
    appro_adjust = Column(Numeric(16, 2), default=0.00, nullable=False)# T: ApproAdjust
    realignment = Column(Numeric(16, 2), default=0.00, nullable=False) # U: Realignment
    fund_source = Column(String(100), nullable=True, index=True)       # V: FundSource
    locality = Column(String(100), nullable=True)                      # W: Locality
    legal_basis = Column(String(150), nullable=True)                   # X: LegalBasis
    rc = Column(String(50), nullable=True)                             # Y: RC
    reg = Column(String(50), nullable=True)                            # Z: Reg
    ccet_code = Column(String(50), nullable=True)                      # AA: CCETCode
    ledger = Column(String(50), nullable=True)                         # AB: Ledger

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)

    __table_args__ = (
        Index("idx_scope_query", "region", "division", "operating_unit", "is_deleted"),
        Index("idx_school_active", "operating_unit", "is_deleted"),
        Index("idx_division_active", "division", "is_deleted"),
        Index("idx_region_active", "region", "is_deleted"),
        Index("idx_region_div_active", "region", "division", "is_deleted"),
        Index("idx_div_ou_active", "division", "operating_unit", "is_deleted"),
        Index("idx_financial_filter", "allotment_class", "account_code", "fund_source"),
        # Composite pagination indexes with created_on for sub-millisecond retrieval
        Index("idx_school_page", "operating_unit", "is_deleted", "created_on"),
        Index("idx_division_page", "division", "is_deleted", "created_on"),
        Index("idx_region_page", "region", "is_deleted", "created_on"),
        Index("idx_admin_page", "is_deleted", "created_on"),
        Index("idx_ppa_code_active", "ppa_code", "is_deleted"),
    )

