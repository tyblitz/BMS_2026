from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.api.deps import require_role

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("", response_model=dict)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    query = db.query(User).filter(User.is_deleted == False)
    if role:
        query = query.filter(User.role == role)
    if search:
        s = f"%{search}%"
        query = query.filter(User.username.ilike(s) | User.school_name.ilike(s) | User.division.ilike(s))

    total = query.count()
    items = query.order_by(User.created_on.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [UserResponse.model_validate(u) for u in items]
    }


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.username == payload.username, User.is_deleted == False).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username is already taken.")

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        school_name=payload.school_name,
        division=payload.division,
        region=payload.region,
        is_active=payload.is_active,
        created_by=current_user.username
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/{id}", response_model=UserResponse)
def get_user(
    id: str,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserResponse.model_validate(user)


@router.put("/{id}", response_model=UserResponse)
def update_user(
    id: str,
    payload: UserUpdate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        user.hashed_password = get_password_hash(update_data.pop("password"))

    for key, val in update_data.items():
        setattr(user, key, val)

    user.edited_by = current_user.username
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/{id}", response_model=dict)
def delete_user(
    id: str,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    if current_user.id == id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account.")

    user = db.query(User).filter(User.id == id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.soft_delete(username=current_user.username)
    db.commit()
    return {"status": "success", "message": f"User {user.username} soft-deleted successfully."}

