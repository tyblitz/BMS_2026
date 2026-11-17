"""
Phase 2 Database Schema Migration Script (High Performance).
Applies:
1. Table creation: record_audit_logs
2. Column additions: ppa_code, ppa_description to bms_records
3. Instant single-pass SQL backfill for ppa_code and ppa_description
4. Drops UNIQUE constraint on row_hash and replaces with standard index
5. Creates composite pagination indexes for sub-millisecond retrieval
"""
import sqlite3
import time
from pathlib import Path


def apply_migration(db_path: Path):
    start_t = time.time()
    print(f"Applying Phase 2 schema migration to {db_path}...")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Fast pragmas for bulk schema changes
    c.execute("PRAGMA journal_mode = WAL;")
    c.execute("PRAGMA synchronous = OFF;")
    c.execute("PRAGMA cache_size = -64000;")

    # 1. Create record_audit_logs table
    c.execute("""
    CREATE TABLE IF NOT EXISTS record_audit_logs (
        id VARCHAR(36) NOT NULL,
        record_id VARCHAR(36) NOT NULL,
        action VARCHAR(20) NOT NULL,
        changed_by VARCHAR(100) NOT NULL,
        changed_at DATETIME NOT NULL,
        old_values TEXT,
        new_values TEXT,
        reason TEXT,
        PRIMARY KEY (id)
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS ix_audit_record_id ON record_audit_logs (record_id);")
    c.execute("CREATE INDEX IF NOT EXISTS ix_audit_action ON record_audit_logs (action);")
    c.execute("CREATE INDEX IF NOT EXISTS ix_audit_changed_by ON record_audit_logs (changed_by);")
    c.execute("CREATE INDEX IF NOT EXISTS ix_audit_changed_at ON record_audit_logs (changed_at);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_audit_record_time ON record_audit_logs (record_id, changed_at);")
    print("✓ Created record_audit_logs table and indexes.")

    # 2. Add ppa_code and ppa_description to bms_records if missing
    c.execute("PRAGMA table_info(bms_records);")
    existing_cols = set(r[1] for r in c.fetchall())

    if "ppa_code" not in existing_cols:
        c.execute("ALTER TABLE bms_records ADD COLUMN ppa_code VARCHAR(20);")
        print("✓ Added column ppa_code to bms_records.")
    
    if "ppa_description" not in existing_cols:
        c.execute("ALTER TABLE bms_records ADD COLUMN ppa_description VARCHAR(255);")
        print("✓ Added column ppa_description to bms_records.")

    # 3. High-speed single-pass SQL backfill for ppa_code and ppa_description
    print("Executing single-pass SQL backfill for ppa_code and ppa_description...")
    c.execute("""
    UPDATE bms_records
    SET ppa_code = substr(ppa_control, 1, instr(ppa_control, ' - ') - 1),
        ppa_description = substr(ppa_control, instr(ppa_control, ' - ') + 3)
    WHERE ppa_control LIKE 'PPA% - %' AND (ppa_code IS NULL OR ppa_code = '');
    """)
    conn.commit()
    print("✓ Backfilled ppa_code and ppa_description in single pass.")

    # 4. Remove UNIQUE index on row_hash and recreate as standard index
    c.execute("DROP INDEX IF EXISTS ix_bms_records_row_hash;")
    c.execute("CREATE INDEX IF NOT EXISTS ix_bms_records_row_hash ON bms_records (row_hash);")
    print("✓ Converted row_hash index to standard non-unique index.")

    # 5. Composite pagination indexes
    print("Building composite pagination indexes...")
    c.execute("CREATE INDEX IF NOT EXISTS idx_school_page ON bms_records (operating_unit, is_deleted, created_on);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_division_page ON bms_records (division, is_deleted, created_on);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_region_page ON bms_records (region, is_deleted, created_on);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_admin_page ON bms_records (is_deleted, created_on);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ppa_code_active ON bms_records (ppa_code, is_deleted);")
    print("✓ Created composite pagination and PPA indexes.")

    # Restore safe synchronous mode
    c.execute("PRAGMA synchronous = NORMAL;")
    conn.commit()
    conn.close()
    elapsed = time.time() - start_t
    print(f"✓ Phase 2 database migration completed successfully in {elapsed:.2f}s.")


if __name__ == "__main__":
    db_file = Path("backend/data/bms_local.db")
    apply_migration(db_file)
