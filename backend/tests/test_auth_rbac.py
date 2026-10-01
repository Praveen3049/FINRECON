import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.utils.seed_users import seed_demo_users
from sqlalchemy import desc

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def ensure_seed_users():
    with SessionLocal() as db:
        seed_demo_users(db)


class TestPasswordHashingAndTokens:
    def test_bcrypt_hashing_and_verification(self):
        plain = "SuperSecretSecurePass123!"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed) is True
        assert verify_password("WrongPassword!", hashed) is False

    def test_jwt_token_creation_and_decoding(self):
        token = create_access_token(
            subject="user-uuid-1234",
            email="test@finrecon.com",
            role="USER",
            name="Test User",
        )
        assert isinstance(token, str)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-uuid-1234"
        assert payload["email"] == "test@finrecon.com"
        assert payload["role"] == "USER"

    def test_invalid_token_returns_none(self):
        assert decode_access_token("corrupted.jwt.token") is None


class TestAuthenticationEndpoints:
    def test_login_success_user(self):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "user@finrecon.com", "password": "User@123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "user@finrecon.com"
        assert data["user"]["role"] == "USER"

    def test_login_success_auditor(self):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "auditor@finrecon.com", "password": "Auditor@123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["user"]["role"] == "AUDITOR"

    def test_login_success_manager(self):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "manager@finrecon.com", "password": "Manager@123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["user"]["role"] == "MANAGER"

    def test_login_invalid_password(self):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "user@finrecon.com", "password": "IncorrectPassword!"},
        )
        assert res.status_code == 401
        assert "Invalid email or password" in res.json()["detail"]

    def test_login_unknown_email(self):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@finrecon.com", "password": "SomePassword123"},
        )
        assert res.status_code == 401
        assert "Invalid email or password" in res.json()["detail"]

    def test_login_with_role_success(self):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "auditor@finrecon.com", "password": "Auditor@123", "role": "AUDITOR"},
        )
        assert res.status_code == 200
        assert res.json()["user"]["role"] == "AUDITOR"

    def test_login_with_role_mismatch_fails(self):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "user@finrecon.com", "password": "User@123", "role": "MANAGER"},
        )
        assert res.status_code == 401
        assert "Role mismatch" in res.json()["detail"]

    def test_signup_creates_new_user_with_user_role(self):
        test_email = "analyst.new@finrecon.com"
        # Cleanup if exists
        with SessionLocal() as db:
            existing = db.query(User).filter(User.email == test_email).first()
            if existing:
                db.delete(existing)
                db.commit()

        res = client.post(
            "/api/v1/auth/signup",
            json={"name": "Sarah Connor", "email": test_email, "password": "SecurePassword@123"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["user"]["email"] == test_email
        assert data["user"]["role"] == "USER"
        assert "access_token" in data

    def test_signup_duplicate_email_fails(self):
        res = client.post(
            "/api/v1/auth/signup",
            json={"name": "Duplicate User", "email": "user@finrecon.com", "password": "Password@123"},
        )
        assert res.status_code == 400
        assert "already exists" in res.json()["detail"]

    def test_get_me_authenticated(self):
        # 1. Login
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "user@finrecon.com", "password": "User@123"},
        )
        token = login_res.json()["access_token"]

        # 2. Get Profile
        me_res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["email"] == "user@finrecon.com"
        assert me_data["role"] == "USER"

    def test_get_me_unauthorized(self):
        anon_client = TestClient(app)
        res = anon_client.get("/api/v1/auth/me")
        assert res.status_code == 401

    def test_logout(self):
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "user@finrecon.com", "password": "User@123"},
        )
        token = login_res.json()["access_token"]
        logout_res = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_res.status_code == 200
        assert logout_res.json()["status"] == "success"

    def test_demo_users_endpoint(self):
        res = client.get("/api/v1/auth/demo-users")
        assert res.status_code == 200
        users = res.json()
        assert len(users) == 3
        roles = [u["role"] for u in users]
        assert "USER" in roles
        assert "AUDITOR" in roles
        assert "MANAGER" in roles


class TestRoleBasedAccessControl:
    @pytest.fixture
    def user_token(self):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "user@finrecon.com", "password": "User@123", "role": "USER"},
        )
        return res.json()["access_token"]

    @pytest.fixture
    def auditor_token(self):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "auditor@finrecon.com", "password": "Auditor@123", "role": "AUDITOR"},
        )
        return res.json()["access_token"]

    @pytest.fixture
    def manager_token(self):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "manager@finrecon.com", "password": "Manager@123", "role": "MANAGER"},
        )
        return res.json()["access_token"]

    def test_user_blocked_from_reconciliation_trigger(self, user_token):
        res = client.post(
            "/api/v1/reconciliation/run",
            json={"case_title": "User Attempt Run", "amount_tolerance": 0.01, "date_tolerance_days": 1},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert res.status_code == 403
        assert "Access denied" in res.json()["detail"]

    def test_auditor_can_trigger_reconciliation(self, auditor_token):
        res = client.post(
            "/api/v1/reconciliation/run",
            json={"case_title": "Auditor Reconciliation Run", "amount_tolerance": 0.01, "date_tolerance_days": 1},
            headers={"Authorization": f"Bearer {auditor_token}"},
        )
        assert res.status_code in (200, 201)

    def test_manager_can_trigger_reconciliation(self, manager_token):
        res = client.post(
            "/api/v1/reconciliation/run",
            json={"case_title": "Manager Reconciliation Run", "amount_tolerance": 0.01, "date_tolerance_days": 1},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert res.status_code in (200, 201)

    def test_user_blocked_from_exception_write_actions(self, user_token):
        res = client.post(
            "/api/v1/exceptions/disc-001/action",
            json={"reviewer_name": "User", "action": "CONFIRM_MATCH", "notes": "Test unauthorized override"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert res.status_code == 403
        assert "Access denied" in res.json()["detail"]

    def test_auditor_can_execute_exception_action(self, auditor_token):
        res = client.post(
            "/api/v1/exceptions/disc-001/action",
            json={"reviewer_name": "Elena Rostova", "action": "ESCALATE", "notes": "Escalating variance to manager"},
            headers={"Authorization": f"Bearer {auditor_token}"},
        )
        # Should NOT be 403 Forbidden!
        assert res.status_code in (200, 404)

    def test_manager_can_execute_exception_action(self, manager_token):
        res = client.post(
            "/api/v1/exceptions/disc-001/action",
            json={"reviewer_name": "Marcus Vance", "action": "ASSIGN_AUDITOR", "notes": "Elena Rostova"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        # Should NOT be 403 Forbidden!
        assert res.status_code in (200, 404)

    def test_audit_trail_captures_auth_and_denial_events(self, user_token):
        # Trigger an access denied event by user on reconciliation run
        client.post(
            "/api/v1/reconciliation/run",
            json={"case_title": "Audit Denial Test", "amount_tolerance": 0.01, "date_tolerance_days": 1},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        with SessionLocal() as db:
            denied_logs = (
                db.query(AuditLog)
                .filter(AuditLog.action == "ROLE_ACCESS_DENIED")
                .order_by(desc(AuditLog.timestamp))
                .all()
            )
            assert len(denied_logs) > 0
            latest = denied_logs[0]
            assert latest.actor_id == "user@finrecon.com"
            assert "ROLE_ACCESS_DENIED" == latest.action
            assert latest.entry_hash is not None
