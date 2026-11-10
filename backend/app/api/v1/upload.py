import os
import shutil
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.services.excel_ingestion import ExcelIngestionService
from app.api.deps import get_current_user

router = APIRouter(prefix="/upload", tags=["Upload & Ingestion"])


@router.post("", response_model=dict)
async def upload_temptable_files(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    user_scope = {
        "school_name": current_user.school_name,
        "division": current_user.division,
        "region": current_user.region
    }

    results = []
    overall_total = 0
    overall_inserted = 0
    overall_duplicates = 0
    overall_out_of_scope = 0

    for file in files:
        if not file.filename.lower().endswith((".xlsx", ".xlsm")):
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": "Only Excel files (.xlsx, .xlsm) are supported."
            })
            continue

        # Save to temporary file to allow streaming calamine processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        try:
            res = ExcelIngestionService.ingest_records(
                file_path_or_bytes=tmp_path,
                db=db,
                uploaded_by=current_user.username,
                user_role=current_user.role,
                user_scope=user_scope
            )
            overall_total += res["total_rows"]
            overall_inserted += res["inserted"]
            overall_duplicates += res["duplicates_skipped"]
            overall_out_of_scope += res["skipped_out_of_scope"]

            results.append({
                "filename": file.filename,
                "status": "success",
                "total_rows": res["total_rows"],
                "inserted": res["inserted"],
                "duplicates_skipped": res["duplicates_skipped"],
                "skipped_out_of_scope": res["skipped_out_of_scope"]
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": f"Processing error: {str(e)}"
            })
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return {
        "files_processed": len(files),
        "overall_summary": {
            "total_rows_read": overall_total,
            "total_inserted": overall_inserted,
            "total_duplicates_skipped": overall_duplicates,
            "total_skipped_out_of_scope": overall_out_of_scope
        },
        "file_details": results
    }
