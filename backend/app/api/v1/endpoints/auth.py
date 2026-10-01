from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, hash_password
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, SignupRequest, LoginResponse, LogoutResponse, UserResponse
from app.services.audit.service import AuditService

router = APIRouter()


@router.post("/login", response_model=LoginResponse, summary="Authenticate user and issue JWT session")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticate against credentials, enforce role matching if selected, log to cryptographic audit trail, and issue secure session.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    normalized_email = payload.email.strip().lower()

    # 1. Lookup user in database
    user = db.query(User).filter(User.email == normalized_email).first()

    # 2. Check user existence and verify password
    is_valid = False
    if user and user.is_active:
        is_valid = verify_password(payload.password, user.password_hash)

    if not is_valid:
        # Log failure to immutable audit trail
        try:
            AuditService.log_event(
                db=db,
                actor_type="MANUAL_REVIEWER",
                actor_id=normalized_email,
                action="LOGIN_FAILURE",
                entity_type="USER_SESSION",
                entity_id=normalized_email,
                details=f"Failed authentication attempt for email '{normalized_email}' from IP {client_ip}.",
                ip_address=client_ip,
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Role verification (if role is specified by user on login)
    if payload.role:
        selected_role = payload.role.strip().upper()
        if selected_role != user.role.value:
            try:
                AuditService.log_event(
                    db=db,
                    actor_type="MANUAL_REVIEWER",
                    actor_id=normalized_email,
                    action="LOGIN_ROLE_MISMATCH",
                    entity_type="USER_SESSION",
                    entity_id=user.id,
                    details=f"Role mismatch for '{normalized_email}': selected '{selected_role}' but account is registered as '{user.role.value}'.",
                    ip_address=client_ip,
                )
            except Exception:
                pass

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Role mismatch: Credentials do not belong to role '{selected_role}'. Please select the role matching your credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 4. Successful login - update timestamp
    now = datetime.now(timezone.utc)
    user.last_login_at = now
    db.commit()
    db.refresh(user)

    # 4. Generate JWT token
    access_token = create_access_token(
        subject=user.id,
        email=user.email,
        role=user.role.value,
        name=user.name,
    )

    # 5. Set secure HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=not settings.DEBUG,
    )

    # 6. Record LOGIN_SUCCESS in Audit Trail
    try:
        AuditService.log_event(
            db=db,
            actor_type="MANUAL_REVIEWER",
            actor_id=user.email,
            action="LOGIN_SUCCESS",
            entity_type="USER_SESSION",
            entity_id=user.id,
            details=f"User '{user.name}' ({user.email}) successfully logged in with role '{user.role.value}'.",
            ip_address=client_ip,
        )
    except Exception:
        pass

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        ),
    )


@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED, summary="Register new user account")
def signup(
    payload: SignupRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Register a new user account with strictly the USER role.
    New users can manage their accounts by importing CSV files and using AI Assistant.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    normalized_email = payload.email.strip().lower()

    # 1. Ensure email uniqueness
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in instead.",
        )

    # 2. Persist new user strictly locked to USER role
    new_user = User(
        name=payload.name.strip(),
        email=normalized_email,
        password_hash=hash_password(payload.password),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 3. Generate session JWT token
    access_token = create_access_token(
        subject=new_user.id,
        email=new_user.email,
        role=new_user.role.value,
        name=new_user.name,
    )

    # 4. Set secure HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=not settings.DEBUG,
    )

    # 5. Audit trail registration event
    try:
        AuditService.log_event(
            db=db,
            actor_type="MANUAL_REVIEWER",
            actor_id=new_user.email,
            action="SIGNUP_SUCCESS",
            entity_type="USER_SESSION",
            entity_id=new_user.id,
            details=f"New user account registered for '{new_user.name}' ({new_user.email}) with role 'USER'.",
            ip_address=client_ip,
        )
    except Exception:
        pass

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=new_user.id,
            name=new_user.name,
            email=new_user.email,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            last_login_at=new_user.last_login_at,
        ),
    )


@router.get("/me", response_model=UserResponse, summary="Retrieve authenticated user profile and role")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns current authenticated user details and active role permissions.
    """
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
    )


@router.post("/logout", response_model=LogoutResponse, summary="Terminate active user session")
def logout(
    request: Request,
    response: Response,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Terminate session, clear HTTP-only cookie, and log LOGOUT event to audit trail.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Clear auth cookie
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")

    if current_user:
        try:
            AuditService.log_event(
                db=db,
                actor_type="MANUAL_REVIEWER",
                actor_id=current_user.email,
                action="LOGOUT",
                entity_type="USER_SESSION",
                entity_id=current_user.id,
                details=f"User '{current_user.name}' ({current_user.email}) signed out successfully.",
                ip_address=client_ip,
            )
        except Exception:
            pass

    return LogoutResponse(status="success", message="Session successfully terminated.")


@router.get("/demo-users", response_model=List[Dict[str, str]], summary="List development seed accounts for testing")
def list_demo_users():
    """
    Returns available demonstration accounts with their designated roles.
    """
    return [
        {
            "role": "USER",
            "name": "Alex Rivera",
            "email": "user@finrecon.com",
            "description": "Operational reconciliation analyst with file upload and matching execution permissions.",
        },
        {
            "role": "AUDITOR",
            "name": "Elena Rostova",
            "email": "auditor@finrecon.com",
            "description": "Compliance officer with read-only verification, audit trail inspection, and report export permissions.",
        },
        {
            "role": "MANAGER",
            "name": "Marcus Vance",
            "email": "manager@finrecon.com",
            "description": "Financial operations executive with reconciliation oversight and analytics dashboard access.",
        },
    ]
