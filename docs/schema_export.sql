-- ============================================================================
-- DepEd NCR BURS (Budget Utilization and Reporting System)
-- Complete SQLite Schema Export (DDL)
-- Extracted from: backend/data/bms_local.db
-- ============================================================================

-- Type: INDEX | Name: idx_div_ou_active
CREATE INDEX idx_div_ou_active ON bms_records (division, operating_unit, is_deleted);

-- Type: INDEX | Name: idx_division_active
CREATE INDEX idx_division_active ON bms_records (division, is_deleted);

-- Type: INDEX | Name: idx_financial_filter
CREATE INDEX idx_financial_filter ON bms_records (allotment_class, account_code, fund_source);

-- Type: INDEX | Name: idx_region_active
CREATE INDEX idx_region_active ON bms_records (region, is_deleted);

-- Type: INDEX | Name: idx_region_div_active
CREATE INDEX idx_region_div_active ON bms_records (region, division, is_deleted);

-- Type: INDEX | Name: idx_school_active
CREATE INDEX idx_school_active ON bms_records (operating_unit, is_deleted);

-- Type: INDEX | Name: idx_scope_query
CREATE INDEX idx_scope_query ON bms_records (region, division, operating_unit, is_deleted);

-- Type: INDEX | Name: ix_bms_records_account_code
CREATE INDEX ix_bms_records_account_code ON bms_records (account_code);

-- Type: INDEX | Name: ix_bms_records_allotment_class
CREATE INDEX ix_bms_records_allotment_class ON bms_records (allotment_class);

-- Type: INDEX | Name: ix_bms_records_date_bms
CREATE INDEX ix_bms_records_date_bms ON bms_records (date_bms);

-- Type: INDEX | Name: ix_bms_records_division
CREATE INDEX ix_bms_records_division ON bms_records (division);

-- Type: INDEX | Name: ix_bms_records_fund_source
CREATE INDEX ix_bms_records_fund_source ON bms_records (fund_source);

-- Type: INDEX | Name: ix_bms_records_is_deleted
CREATE INDEX ix_bms_records_is_deleted ON bms_records (is_deleted);

-- Type: INDEX | Name: ix_bms_records_operating_unit
CREATE INDEX ix_bms_records_operating_unit ON bms_records (operating_unit);

-- Type: INDEX | Name: ix_bms_records_org_code_uacs
CREATE INDEX ix_bms_records_org_code_uacs ON bms_records (org_code_uacs);

-- Type: INDEX | Name: ix_bms_records_ppa_control
CREATE INDEX ix_bms_records_ppa_control ON bms_records (ppa_control);

-- Type: INDEX | Name: ix_bms_records_region
CREATE INDEX ix_bms_records_region ON bms_records (region);

-- Type: INDEX | Name: ix_bms_records_row_hash
CREATE UNIQUE INDEX ix_bms_records_row_hash ON bms_records (row_hash);

-- Type: INDEX | Name: ix_bms_records_uacs_pap_code
CREATE INDEX ix_bms_records_uacs_pap_code ON bms_records (uacs_pap_code);

-- Type: INDEX | Name: ix_users_division
CREATE INDEX ix_users_division ON users (division);

-- Type: INDEX | Name: ix_users_email
CREATE UNIQUE INDEX ix_users_email ON users (email);

-- Type: INDEX | Name: ix_users_is_deleted
CREATE INDEX ix_users_is_deleted ON users (is_deleted);

-- Type: INDEX | Name: ix_users_region
CREATE INDEX ix_users_region ON users (region);

-- Type: INDEX | Name: ix_users_role
CREATE INDEX ix_users_role ON users (role);

-- Type: INDEX | Name: ix_users_school_name
CREATE INDEX ix_users_school_name ON users (school_name);

-- Type: INDEX | Name: ix_users_username
CREATE UNIQUE INDEX ix_users_username ON users (username);

-- Type: TABLE | Name: bms_records
CREATE TABLE bms_records (
	id VARCHAR(36) NOT NULL, 
	row_hash VARCHAR(64) NOT NULL, 
	ppa_control VARCHAR(255), 
	appropriation_type VARCHAR(100), 
	allotment_period VARCHAR(100), 
	allotment_class VARCHAR(50), 
	date_bms VARCHAR(50), 
	account_code VARCHAR(50), 
	obligations_incurred NUMERIC(16, 2) NOT NULL, 
	disbursement NUMERIC(16, 2) NOT NULL, 
	appropriations NUMERIC(16, 2) NOT NULL, 
	allotment NUMERIC(16, 2) NOT NULL, 
	transfer_to NUMERIC(16, 2) NOT NULL, 
	transfer_from NUMERIC(16, 2) NOT NULL, 
	particulars TEXT, 
	uacs_pap_code VARCHAR(100), 
	dv_amount NUMERIC(16, 2) NOT NULL, 
	region VARCHAR(150) NOT NULL, 
	division VARCHAR(150) NOT NULL, 
	operating_unit VARCHAR(150) NOT NULL, 
	org_code_uacs VARCHAR(50), 
	appro_adjust NUMERIC(16, 2) NOT NULL, 
	realignment NUMERIC(16, 2) NOT NULL, 
	fund_source VARCHAR(100), 
	locality VARCHAR(100), 
	legal_basis VARCHAR(150), 
	rc VARCHAR(50), 
	reg VARCHAR(50), 
	ccet_code VARCHAR(50), 
	ledger VARCHAR(50), 
	created_on DATETIME NOT NULL, 
	created_by VARCHAR(100) NOT NULL, 
	edited_on DATETIME, 
	edited_by VARCHAR(100), 
	deleted_on DATETIME, 
	deleted_by VARCHAR(100), 
	is_deleted BOOLEAN DEFAULT '0' NOT NULL, 
	PRIMARY KEY (id)
);

-- Type: TABLE | Name: users
CREATE TABLE users (
	id VARCHAR(36) NOT NULL, 
	username VARCHAR(100) NOT NULL, 
	email VARCHAR(150), 
	hashed_password VARCHAR(255) NOT NULL, 
	role VARCHAR(50) NOT NULL, 
	school_name VARCHAR(150), 
	division VARCHAR(150), 
	region VARCHAR(150), 
	is_active BOOLEAN NOT NULL, 
	created_on DATETIME NOT NULL, 
	created_by VARCHAR(100) NOT NULL, 
	edited_on DATETIME, 
	edited_by VARCHAR(100), 
	deleted_on DATETIME, 
	deleted_by VARCHAR(100), 
	is_deleted BOOLEAN DEFAULT '0' NOT NULL, 
	PRIMARY KEY (id)
);
