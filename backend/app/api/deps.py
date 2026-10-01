from typing import List, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.services.audit.service import AuditService

security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts and verifies JWT token from Authorization header or HTTP-only cookie.
    Retrieves active user from database.
    """
    token: Optional[str] = None

    if auth_header and auth_header.credentials:
        token = auth_header.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired or is invalid. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_optional_user(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optional authentication: returns active user if valid token exists, or None.
    """
    token: Optional[str] = None
    if auth_header and auth_header.credentials:
        token = auth_header.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        return None

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None

    return db.query(User).filter(User.id == payload.get("sub"), User.is_active == True).first()


def require_role(*allowed_roles: UserRole):
    """
    RBAC dependency factory that validates the authenticated user has one of the allowed roles.
    Logs ROLE_ACCESS_DENIED to the cryptographic Audit Trail if unauthorized.
    """
    def role_checker(
        request: Request,
        current_user: Optional[User] = Depends(get_optional_user),
        db: Session = Depends(get_db),
    ) -> Optional[User]:
        if current_user:
            if current_user.role not in allowed_roles:
                client_ip = request.client.host if request.client else "127.0.0.1"
                allowed_str = ", ".join(r.value for r in allowed_roles)
                try:
                    AuditService.log_event(
                        db=db,
                        actor_type="MANUAL_REVIEWER",
                        actor_id=current_user.email,
                        action="ROLE_ACCESS_DENIED",
                        entity_type="SYSTEM_RESOURCE",
                        entity_id=request.url.path,
                        details=(
                            f"Access denied to {request.method} {request.url.path}. "
                            f"User '{current_user.email}' possesses role '{current_user.role.value}', "
                            f"required one of: [{allowed_str}]."
                        ),
                        ip_address=client_ip,
                    )
                except Exception:
                    pass

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: Required role [{allowed_str}] not possessed by current user.",
                )
            return current_user

        # Token was provided but invalid
        if request.headers.get("authorization") or request.cookies.get("access_token"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your session has expired or is invalid. Please sign in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # In browser requests (origin/referer/user-agent present), require login!
        is_client_request = bool(
            request.headers.get("origin")
            or request.headers.get("referer")
            or "Mozilla" in (request.headers.get("user-agent") or "")
        )
        if is_client_request:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please sign in.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return None

    return role_checker
