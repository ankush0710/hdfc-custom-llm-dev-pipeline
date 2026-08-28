from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_dependency import (
    create_access_token,
    get_current_user,
    hash_password,
    require_roles,
    verify_password,
)
from app.dbConfig.database_config import get_db
from app.model.user_model import User_Model
from app.schema.auth_schema.auth_schema import (
    RoleUpdate,
    TokenResponse,
    UserLogin,
    UserResponse,
    UserSignup,
    UserStatusUpdate,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

VALID_ROLES = {"ADMIN", "DS", "REVIEWER", "VIEWER"}


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    payload: UserSignup,
    db: Session = Depends(get_db),
):
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )

    existing_user = (
        db.query(User_Model)
        .filter(User_Model.email == payload.email.lower().strip())
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An account with email '{payload.email}' already exists.",
        )

    # Safe Default Role: Public signup always creates a VIEWER account
    user = User_Model(
        full_name=payload.full_name.strip(),
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        role="VIEWER",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    """Authenticate user with email & password and issue JWT token."""
    email_clean = payload.email.lower().strip()
    user = db.query(User_Model).filter(User_Model.email == email_clean).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact system administrator.",
        )

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User_Model = Depends(get_current_user),
):
    """Return profile details for the currently authenticated user."""
    return current_user


@router.post(
    "/logout",
)
def logout(
    current_user: User_Model = Depends(get_current_user),
):
    """Acknowledge logout for active session."""
    return {"message": "Logged out successfully", "user_id": current_user.id}


@router.get(
    "/users",
    response_model=List[UserResponse],
)
def list_users(
    db: Session = Depends(get_db),
    admin: User_Model = Depends(require_roles("ADMIN")),
):
    """List all registered platform users (ADMIN only)."""
    return db.query(User_Model).order_by(User_Model.created_at.desc()).all()


@router.put(
    "/users/{user_id}/role",
    response_model=UserResponse,
)
def update_user_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    admin: User_Model = Depends(require_roles("ADMIN")),
):
    """Update a user's authorization role (ADMIN only)."""
    raw_role = payload.role.upper().strip()
    new_role = "DS" if raw_role in {"DATA_SCIENTIST", "DS"} else raw_role

    if new_role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Valid roles are: {sorted(VALID_ROLES)}",
        )

    user = db.query(User_Model).filter(User_Model.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    # Protect against accidental removal of the sole system admin
    if user.role == "ADMIN" and new_role != "ADMIN":
        active_admin_count = (
            db.query(User_Model)
            .filter(User_Model.role == "ADMIN", User_Model.is_active == True)
            .count()
        )
        if active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the only active Administrator in the system.",
            )

    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User_Model = Depends(require_roles("ADMIN")),
):
    """Activate or deactivate a user account (ADMIN only)."""
    user = db.query(User_Model).filter(User_Model.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    # Protect admin from deactivating themselves
    if admin.id == user_id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own active account.",
        )

    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user

