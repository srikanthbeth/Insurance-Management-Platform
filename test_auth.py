
import os
import time
import uuid

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "insurance_management_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from dependencies import get_db
from main import app


# ============================================================
# TEST DATABASE
# ============================================================

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ============================================================
# DATABASE SETUP / TEARDOWN
# ============================================================

def setup_module():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def teardown_module():
    Base.metadata.drop_all(bind=test_engine)


# ============================================================
# HELPERS
# ============================================================

def unique_email(prefix: str = "user") -> str:
    return (
        f"{prefix}_{uuid.uuid4().hex[:8]}"
        "@example.com"
    )


def register_user(
    full_name="Test Customer",
    role="Customer",
    email=None,
    password="Test@12345",
):
    if email is None:
        email = unique_email("user")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": role,
        },
    )

    return response, email, password


def login_user(
    email: str,
    password: str,
):
    # Small delay prevents identical JWTs when the
    # current token implementation uses second-level exp.
    time.sleep(1.05)

    return client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def get_auth_header(access_token: str):
    return {
        "Authorization": f"Bearer {access_token}"
    }


# ============================================================
# REGISTER TESTS
# ============================================================

def test_register_customer():
    response, email, _ = register_user(
        full_name="Rajesh Kumar",
        role="Customer",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Rajesh Kumar"
    assert data["email"] == email
    assert data["role"] == "Customer"
    assert data["is_active"] is True

    assert "password" not in data
    assert "password_hash" not in data


def test_register_insurance_agent():
    response, email, _ = register_user(
        full_name="Arjun Sharma",
        role="Insurance Agent",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Arjun Sharma"
    assert data["email"] == email
    assert data["role"] == "Insurance Agent"


def test_register_claims_officer():
    response, email, _ = register_user(
        full_name="Priya Reddy",
        role="Claims Officer",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == email
    assert data["role"] == "Claims Officer"


def test_register_finance_officer():
    response, email, _ = register_user(
        full_name="Kiran Kumar",
        role="Finance Officer",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == email
    assert data["role"] == "Finance Officer"


def test_register_super_admin():
    response, email, _ = register_user(
        full_name="System Administrator",
        role="Super Admin",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == email
    assert data["role"] == "Super Admin"


def test_register_duplicate_email():
    email = unique_email("duplicate")

    first_response, _, _ = register_user(
        email=email,
    )

    assert first_response.status_code == 201

    second_response, _, _ = register_user(
        email=email,
    )

    assert second_response.status_code == 409

    assert second_response.json()["detail"] == (
        "Email already registered"
    )


# ============================================================
# REGISTER VALIDATION TESTS
# ============================================================

def test_register_invalid_email():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Invalid Email",
            "email": "invalid-email",
            "password": "Test@12345",
            "role": "Customer",
        },
    )

    assert response.status_code == 422


def test_register_short_password():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Short Password",
            "email": unique_email("short"),
            "password": "123",
            "role": "Customer",
        },
    )

    assert response.status_code == 422


def test_register_long_password():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Long Password",
            "email": unique_email("long"),
            "password": "A" * 73,
            "role": "Customer",
        },
    )

    assert response.status_code == 422


def test_register_missing_full_name():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email("missing"),
            "password": "Test@12345",
            "role": "Customer",
        },
    )

    assert response.status_code == 422


def test_register_invalid_role():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Invalid Role",
            "email": unique_email("role"),
            "password": "Test@12345",
            "role": "Invalid Role",
        },
    )

    assert response.status_code == 422


# ============================================================
# LOGIN TESTS
# ============================================================

def test_login_success():
    response, email, password = register_user(
        full_name="Login User",
    )

    assert response.status_code == 201

    login_response = login_user(
        email,
        password,
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email


def test_login_invalid_email():
    response = login_user(
        "does-not-exist@example.com",
        "Test@12345",
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Invalid email or password"
    )


def test_login_invalid_password():
    _, email, _ = register_user(
        full_name="Wrong Password User",
    )

    response = login_user(
        email,
        "WrongPassword@123",
    )

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Invalid email or password"
    )


# ============================================================
# /ME TESTS
# ============================================================

def test_get_current_user():
    _, email, password = register_user(
        full_name="Current User",
    )

    login_response = login_user(
        email,
        password,
    )

    assert login_response.status_code == 200

    access_token = login_response.json()[
        "access_token"
    ]

    response = client.get(
        "/api/v1/auth/me",
        headers=get_auth_header(access_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == email
    assert data["full_name"] == "Current User"
    assert data["role"] == "Customer"
    assert data["is_active"] is True


def test_get_current_user_without_token():
    response = client.get(
        "/api/v1/auth/me",
    )

    assert response.status_code == 401


def test_get_current_user_invalid_token():
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401


def test_get_current_user_refresh_token():
    _, email, password = register_user(
        full_name="Wrong Token User",
    )

    login_response = login_user(
        email,
        password,
    )

    refresh_token = login_response.json()[
        "refresh_token"
    ]

    response = client.get(
        "/api/v1/auth/me",
        headers=get_auth_header(refresh_token),
    )

    assert response.status_code == 401


# ============================================================
# REFRESH TOKEN TESTS
# ============================================================

def test_refresh_token():
    _, email, password = register_user(
        full_name="Refresh User",
    )

    login_response = login_user(
        email,
        password,
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()[
        "refresh_token"
    ]

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_refresh_token():
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid-refresh-token"
        },
    )

    assert response.status_code == 401


def test_empty_refresh_token():
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": ""
        },
    )

    assert response.status_code == 401


# ============================================================
# CHANGE PASSWORD TESTS
# ============================================================

def test_change_password():
    _, email, password = register_user(
        full_name="Password User",
    )

    login_response = login_user(
        email,
        password,
    )

    assert login_response.status_code == 200

    access_token = login_response.json()[
        "access_token"
    ]

    new_password = "NewPassword@123"

    response = client.put(
        "/api/v1/auth/change-password",
        headers=get_auth_header(access_token),
        json={
            "current_password": password,
            "new_password": new_password,
        },
    )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "Password changed successfully"
    )

    # Wait before logging in again so that an implementation
    # without jti does not create an identical refresh token.
    time.sleep(1.05)

    new_login = login_user(
        email,
        new_password,
    )

    assert new_login.status_code == 200

    assert "access_token" in new_login.json()
    assert "refresh_token" in new_login.json()


def test_change_password_wrong_current_password():
    _, email, password = register_user(
        full_name="Wrong Current Password",
    )

    login_response = login_user(
        email,
        password,
    )

    access_token = login_response.json()[
        "access_token"
    ]

    response = client.put(
        "/api/v1/auth/change-password",
        headers=get_auth_header(access_token),
        json={
            "current_password": "WrongPassword@123",
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Current password is incorrect"
    )


def test_change_password_same_password():
    _, email, password = register_user(
        full_name="Same Password User",
    )

    login_response = login_user(
        email,
        password,
    )

    access_token = login_response.json()[
        "access_token"
    ]

    response = client.put(
        "/api/v1/auth/change-password",
        headers=get_auth_header(access_token),
        json={
            "current_password": password,
            "new_password": password,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "New password must be different"
    )


def test_change_password_without_token():
    response = client.put(
        "/api/v1/auth/change-password",
        json={
            "current_password": "Test@12345",
            "new_password": "NewPassword@123",
        },
    )

    assert response.status_code == 401


# ============================================================
# ROLE / RBAC TESTS
# ============================================================

def test_customer_role():
    response, _, _ = register_user(
        full_name="Customer User",
        role="Customer",
    )

    assert response.status_code == 201
    assert response.json()["role"] == "Customer"


def test_insurance_agent_role():
    response, _, _ = register_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    assert response.status_code == 201
    assert response.json()["role"] == "Insurance Agent"


def test_claims_officer_role():
    response, _, _ = register_user(
        full_name="Claims Officer",
        role="Claims Officer",
    )

    assert response.status_code == 201
    assert response.json()["role"] == "Claims Officer"


def test_finance_officer_role():
    response, _, _ = register_user(
        full_name="Finance Officer",
        role="Finance Officer",
    )

    assert response.status_code == 201
    assert response.json()["role"] == "Finance Officer"


def test_super_admin_role():
    response, _, _ = register_user(
        full_name="Super Admin",
        role="Super Admin",
    )

    assert response.status_code == 201
    assert response.json()["role"] == "Super Admin"


# ============================================================
# ACCOUNT ACTIVATION / DEACTIVATION
# ============================================================

def test_super_admin_can_deactivate_user():
    admin_email = unique_email("admin")

    admin_response, _, admin_password = register_user(
        full_name="System Administrator",
        role="Super Admin",
        email=admin_email,
        password="Admin@12345",
    )

    assert admin_response.status_code == 201

    user_response, user_email, user_password = (
        register_user(
            full_name="Rajesh Kumar",
            role="Customer",
        )
    )

    assert user_response.status_code == 201

    user_id = user_response.json()["id"]

    admin_login = login_user(
        admin_email,
        admin_password,
    )

    assert admin_login.status_code == 200

    admin_token = admin_login.json()[
        "access_token"
    ]

    response = client.put(
        f"/api/v1/auth/users/{user_id}/status",
        headers=get_auth_header(admin_token),
        json={
            "is_active": False
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["is_active"] is False

    user_login = login_user(
        user_email,
        user_password,
    )

    assert user_login.status_code == 403

    assert user_login.json()["detail"] == (
        "User account is inactive"
    )


def test_super_admin_can_reactivate_user():
    admin_email = unique_email("admin")

    admin_response, _, admin_password = register_user(
        full_name="System Administrator",
        role="Super Admin",
        email=admin_email,
        password="Admin@12345",
    )

    assert admin_response.status_code == 201

    user_response, user_email, user_password = (
        register_user(
            full_name="Inactive Customer",
            role="Customer",
        )
    )

    assert user_response.status_code == 201

    user_id = user_response.json()["id"]

    admin_login = login_user(
        admin_email,
        admin_password,
    )

    admin_token = admin_login.json()[
        "access_token"
    ]

    deactivate_response = client.put(
        f"/api/v1/auth/users/{user_id}/status",
        headers=get_auth_header(admin_token),
        json={
            "is_active": False
        },
    )

    assert deactivate_response.status_code == 200

    activate_response = client.put(
        f"/api/v1/auth/users/{user_id}/status",
        headers=get_auth_header(admin_token),
        json={
            "is_active": True
        },
    )

    assert activate_response.status_code == 200

    assert activate_response.json()["is_active"] is True

    user_login = login_user(
        user_email,
        user_password,
    )

    assert user_login.status_code == 200


def test_customer_cannot_change_user_status():
    _, customer_email, customer_password = (
        register_user(
            full_name="Normal Customer",
            role="Customer",
        )
    )

    target_response, _, _ = register_user(
        full_name="Target Customer",
        role="Customer",
    )

    target_user_id = target_response.json()["id"]

    customer_login = login_user(
        customer_email,
        customer_password,
    )

    customer_token = customer_login.json()[
        "access_token"
    ]

    response = client.put(
        f"/api/v1/auth/users/{target_user_id}/status",
        headers=get_auth_header(customer_token),
        json={
            "is_active": False
        },
    )

    assert response.status_code == 403


def test_insurance_agent_cannot_change_user_status():
    _, agent_email, agent_password = register_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    target_response, _, _ = register_user(
        full_name="Target Customer",
        role="Customer",
    )

    target_user_id = target_response.json()["id"]

    agent_login = login_user(
        agent_email,
        agent_password,
    )

    agent_token = agent_login.json()[
        "access_token"
    ]

    response = client.put(
        f"/api/v1/auth/users/{target_user_id}/status",
        headers=get_auth_header(agent_token),
        json={
            "is_active": False
        },
    )

    assert response.status_code == 403


def test_claims_officer_cannot_change_user_status():
    _, officer_email, officer_password = (
        register_user(
            full_name="Claims Officer",
            role="Claims Officer",
        )
    )

    target_response, _, _ = register_user(
        full_name="Target Customer",
        role="Customer",
    )

    target_user_id = target_response.json()["id"]

    officer_login = login_user(
        officer_email,
        officer_password,
    )

    officer_token = officer_login.json()[
        "access_token"
    ]

    response = client.put(
        f"/api/v1/auth/users/{target_user_id}/status",
        headers=get_auth_header(officer_token),
        json={
            "is_active": False
        },
    )

    assert response.status_code == 403


def test_finance_officer_cannot_change_user_status():
    _, officer_email, officer_password = (
        register_user(
            full_name="Finance Officer",
            role="Finance Officer",
        )
    )

    target_response, _, _ = register_user(
        full_name="Target Customer",
        role="Customer",
    )

    target_user_id = target_response.json()["id"]

    officer_login = login_user(
        officer_email,
        officer_password,
    )

    officer_token = officer_login.json()[
        "access_token"
    ]

    response = client.put(
        f"/api/v1/auth/users/{target_user_id}/status",
        headers=get_auth_header(officer_token),
        json={
            "is_active": False
        },
    )

    assert response.status_code == 403


def test_super_admin_cannot_deactivate_self():
    admin_email = unique_email("self_admin")

    _, _, admin_password = register_user(
        full_name="Self Admin",
        role="Super Admin",
        email=admin_email,
        password="Admin@12345",
    )

    admin_login = login_user(
        admin_email,
        admin_password,
    )

    admin_token = admin_login.json()[
        "access_token"
    ]

    from models.user import User

    db = TestingSessionLocal()

    try:
        admin = (
            db.query(User)
            .filter(User.email == admin_email)
            .first()
        )

        admin_id = admin.id

    finally:
        db.close()

    response = client.put(
        f"/api/v1/auth/users/{admin_id}/status",
        headers=get_auth_header(admin_token),
        json={
            "is_active": False
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Super Admin cannot deactivate "
        "their own account"
    )


def test_change_status_user_not_found():
    admin_email = unique_email("admin")

    _, _, admin_password = register_user(
        full_name="Admin User",
        role="Super Admin",
        email=admin_email,
        password="Admin@12345",
    )

    login_response = login_user(
        admin_email,
        admin_password,
    )

    admin_token = login_response.json()[
        "access_token"
    ]

    response = client.put(
        "/api/v1/auth/users/999999/status",
        headers=get_auth_header(admin_token),
        json={
            "is_active": False
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "User not found"
    )

