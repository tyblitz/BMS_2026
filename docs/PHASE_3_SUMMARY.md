# Phase 3 Summary: Authentication, Scoped RBAC, Dynamic Balances & CRUD APIs

## 1. Overview & Objectives Achieved
Phase 3 completed the core REST API layer, integrating authentication, role-based scoping, soft deletion, dynamic calculations, upload consolidation, and export endpoints.

- **Authentication & Security (`backend/app/api/deps.py`, `backend/app/api/v1/auth.py`)**:
  - Stateless JWT access tokens using `HS256`.
  - Password hashing via `bcrypt`.
  - Endpoint protection with OAuth2 bearer token scheme.
  - `/api/v1/auth/login` and `/api/v1/auth/me` endpoints.
- **Hierarchical Role-Based Access Control (RBAC)**:
  - Backend query-level data isolation enforced in `apply_role_scope`:
    - **School Role**: Strictly locked to `operating_unit == current_user.school_name`. School users can only query, create, update, delete, and export records for their school.
    - **SDO Role**: Scoped to `division == current_user.division`. SDO officers view and consolidate data across all schools in their division.
    - **Region Role**: Scoped to `region == current_user.region`. Regional officers view and consolidate data across all divisions/schools in their region.
    - **Admin Role**: Full system-wide visibility and administrative management.
- **Scoped CRUD API (`backend/app/api/v1/records.py`)**:
  - `GET /api/v1/records`: Paginated, multi-field filtered listing with dynamic balance calculations.
  - `POST /api/v1/records`: Single-record creation with duplicate prevention via deterministic SHA-256 fingerprinting.
  - `GET /api/v1/records/{id}`: Single record detail verification.
  - `PUT /api/v1/records/{id}`: Updates record data and stamps `edited_by` / `edited_on`.
  - `DELETE /api/v1/records/{id}`: **Soft-delete only** (`is_deleted = True`, `deleted_by`, `deleted_on`). No physical deletion occurs.
- **Consolidation Upload Endpoint (`backend/app/api/v1/upload.py`)**:
  - Accepts single files or multi-file batches (`.xlsx`).
  - Processes files via `ExcelIngestionService` using the high-performance Calamine engine.
  - Returns file-by-file and overall summary stats (rows read, inserted, duplicates skipped, out-of-scope skipped).
- **Consolidation Export Endpoint (`backend/app/api/v1/export.py`)**:
  - `GET /api/v1/export/excel`: Generates and streams down an exact 33-column `tempTable.xlsx` (sheet: `Combine Sheet`) compatible with MS Access BMS.
- **Database Switcher API (`backend/app/api/v1/settings.py`)**:
  - `GET /api/v1/settings/db`: Returns masked active database configuration.
  - `POST /api/v1/settings/db/test`: Tests candidate database connection.
  - `POST /api/v1/settings/db/switch`: Switches the active database engine dynamically at runtime.

---

## 2. Test Verification
All Phase 3 integration and security tests in `backend/tests/test_phase3.py` passed with 100% success rate:
- `test_auth_login`: Validates user authentication and token generation.
- `test_rbac_scoping`: Proves data isolation across School, SDO, and Regional scopes.
- `test_crud_lifecycle_and_soft_delete`: Validates creation, dynamic balance calculation response, update tracking, soft-deletion, and DB-level retention.
- `test_upload_and_export_api`: Validates batch upload ingestion and round-trip streaming export.
- `test_database_settings_api`: Validates dynamic database switcher endpoints.

