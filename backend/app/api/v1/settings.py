from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.database import db_manager
from app.models.user import User
from app.api.deps import require_role

router = APIRouter(prefix="/settings", tags=["Settings & Administration"])


class DatabaseConfigRequest(BaseModel):
    database_url: str


@router.get("/db", response_model=dict)
def get_database_info(current_user: User = Depends(require_role("admin"))):
    active_url = db_manager.active_url
    masked_url = active_url
    if "@" in active_url:
        prefix = active_url.split("@")[0]
        suffix = active_url.split("@")[1]
        proto = prefix.split("://")[0]
        masked_url = f"{proto}://*****:*****@{suffix}"

    dialect = "sqlite"
    if "mysql" in active_url:
        dialect = "mysql"
    elif "postgres" in active_url:
        dialect = "postgresql"

    return {
        "active_database_url": masked_url,
        "dialect": dialect,
        "mode": "local_sqlite" if "sqlite" in active_url else "external_server"
    }


@router.post("/db/test", response_model=dict)
def test_database_connection(
    payload: DatabaseConfigRequest,
    current_user: User = Depends(require_role("admin"))
):
    success, message = db_manager.test_connection(payload.database_url)
    return {"success": success, "message": message}


@router.post("/db/switch", response_model=dict)
def switch_database_connection(
    payload: DatabaseConfigRequest,
    current_user: User = Depends(require_role("admin"))
):
    success, message = db_manager.switch_database(payload.database_url)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return {"success": True, "message": message}
