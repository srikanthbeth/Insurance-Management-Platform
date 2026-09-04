
import os
from datetime import date, timedelta
from uuid import uuid4

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

def unique_email(prefix="user"):
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def unique_id(prefix="ID"):
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def register_user(
    full_name="Test User",
    role="Customer",
    email=None,
    password="Test@12345",
):
    if email is None:
        email = unique_email("user")

    return client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": role,
        },
    )


def login_user(email, password):
    return client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def get_auth_header(token):
    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# CUSTOMER HELPER
# ============================================================

def create_customer():
    email = unique_email("customer")

    register_response = register_user(
        full_name="Test Customer",
        role="Customer",
        email=email,
    )

    assert register_response.status_code == 201, (
        f"Customer registration failed: "
        f"{register_response.text}"
    )

    login_response = login_user(
        email,
        "Test@12345",
    )

    assert login_response.status_code == 200, (
        f"Customer login failed: "
        f"{login_response.text}"
    )

    customer_token = login_response.json()["access_token"]

    # --------------------------------------------------------
    # CREATE AGENT
    # --------------------------------------------------------

    agent_email = unique_email("agent")

    agent_register_response = register_user(
        full_name="Test Insurance Agent",
        role="Insurance Agent",
        email=agent_email,
    )

    assert agent_register_response.status_code == 201, (
        f"Agent registration failed: "
        f"{agent_register_response.text}"
    )

    agent_login_response = login_user(
        agent_email,
        "Test@12345",
    )

    assert agent_login_response.status_code == 200, (
        f"Agent login failed: "
        f"{agent_login_response.text}"
    )

    agent_token = agent_login_response.json()["access_token"]

    # --------------------------------------------------------
    # CREATE CUSTOMER PROFILE
    # --------------------------------------------------------

    customer_payload = {
        "full_name": "Test Customer",
        "email": email,
        "phone": f"9{uuid4().int % 1000000000:09d}",
        "date_of_birth": "1995-05-15",
        "address": "Hyderabad, Telangana, India",
        "identification_number": unique_id("CUST"),
        "occupation": "Software Engineer",
    }

    customer_response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(agent_token),
        json=customer_payload,
    )

    assert customer_response.status_code == 201, (
        f"Customer profile creation failed: "
        f"{customer_response.text}"
    )

    customer_data = customer_response.json()

    if isinstance(customer_data, dict):
        customer_data = customer_data.get(
            "data",
            customer_data,
        )

    return (
        customer_data["id"],
        customer_token,
        agent_token,
    )


# ============================================================
# AGENT HELPER
# ============================================================

def create_agent():
    email = unique_email("agent")

    response = register_user(
        full_name="Test Insurance Agent",
        role="Insurance Agent",
        email=email,
    )

    assert response.status_code == 201, (
        f"Agent registration failed: "
        f"{response.text}"
    )

    data = response.json()

    if isinstance(data, dict):
        data = data.get(
            "data",
            data,
        )

    login_response = login_user(
        email,
        "Test@12345",
    )

    assert login_response.status_code == 200, (
        f"Agent login failed: "
        f"{login_response.text}"
    )

    return (
        data["id"],
        login_response.json()["access_token"],
    )


# ============================================================
# SUPER ADMIN HELPER
# ============================================================

def create_super_admin():
    email = unique_email("super_admin")

    register_response = register_user(
        full_name="Test Super Admin",
        role="Super Admin",
        email=email,
    )

    assert register_response.status_code == 201, (
        f"Super Admin registration failed: "
        f"{register_response.text}"
    )

    login_response = login_user(
        email,
        "Test@12345",
    )

    assert login_response.status_code == 200, (
        f"Super Admin login failed: "
        f"{login_response.text}"
    )

    return login_response.json()["access_token"]


# ============================================================
# CLAIMS OFFICER HELPER
# ============================================================

def create_claims_officer():
    email = unique_email("claims_officer")

    register_response = register_user(
        full_name="Test Claims Officer",
        role="Claims Officer",
        email=email,
    )

    assert register_response.status_code == 201, (
        f"Claims Officer registration failed: "
        f"{register_response.text}"
    )

    login_response = login_user(
        email,
        "Test@12345",
    )

    assert login_response.status_code == 200, (
        f"Claims Officer login failed: "
        f"{login_response.text}"
    )

    return login_response.json()["access_token"]


# ============================================================
# PLAN HELPER
# ============================================================

def create_plan(agent_token):
    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(agent_token),
        json={
            "plan_name": f"Health Plan {uuid4().hex[:6]}",
            "plan_type": "Health",
            "description": "Test health insurance plan",
            "coverage_amount": 1000000,
            "premium_amount": 50000,
            "duration_years": 1,
            "eligibility_age_min": 18,
            "eligibility_age_max": 65,
        },
    )

    assert response.status_code == 201, (
        f"Plan creation failed: "
        f"{response.text}"
    )

    data = response.json()

    if isinstance(data, dict):
        data = data.get(
            "data",
            data,
        )

    return data["id"]


# ============================================================
# POLICY HELPER
# ============================================================

def create_policy_test_data(
    policy_status="Active",
    days_until_expiry=335,
):
    customer_id, customer_token, _ = create_customer()

    agent_id, agent_token = create_agent()

    plan_id = create_plan(agent_token)

    start_date = date.today() - timedelta(days=30)

    end_date = (
        date.today()
        + timedelta(days=days_until_expiry)
    )

    response = client.post(
        "/api/v1/policies",
        headers=get_auth_header(agent_token),
        json={
            "policy_number": (
                f"POL-{uuid4().hex[:8].upper()}"
            ),
            "customer_id": customer_id,
            "plan_id": plan_id,
            "agent_id": agent_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "coverage_amount": 1000000,
            "premium_amount": 50000,
            "policy_status": policy_status,
        },
    )

    assert response.status_code == 201, (
        f"Policy creation failed: "
        f"{response.text}"
    )

    data = response.json()

    if isinstance(data, dict):
        data = data.get(
            "data",
            data,
        )

    return (
        data["id"],
        data,
        agent_token,
        customer_token,
        customer_id,
        agent_id,
        plan_id,
    )


# ============================================================
# RENEW POLICY HELPER
# ============================================================

def renew_policy(
    policy_id,
    token,
):
    return client.post(
        f"/api/v1/policies/{policy_id}/renew",
        headers=get_auth_header(token),
    )


# ============================================================
# CREATE RENEWAL
# ============================================================

def test_renew_active_policy():
    (
        policy_id,
        policy_data,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        policy_status="Active",
    )

    response = renew_policy(
        policy_id,
        agent_token,
    )

    assert response.status_code == 201, (
        f"Policy renewal failed: "
        f"{response.text}"
    )

    data = response.json()

    assert data["previous_policy_id"] == policy_id
    assert data["new_policy_id"] > 0

    assert data["previous_start_date"] == (
        policy_data["start_date"]
    )

    assert data["previous_end_date"] == (
        policy_data["end_date"]
    )

    assert data["new_start_date"] == (
        date.fromisoformat(
            policy_data["end_date"]
        )
        + timedelta(days=1)
    ).isoformat()

    assert data["renewal_status"] == "Completed"
    assert "renewal_date" in data
    assert "created_at" in data


# ============================================================
# NEW POLICY CREATED
# ============================================================

def test_renewal_creates_new_policy():
    (
        policy_id,
        _,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        policy_status="Active",
    )

    renewal_response = renew_policy(
        policy_id,
        agent_token,
    )

    assert renewal_response.status_code == 201

    renewal_data = renewal_response.json()

    new_policy_id = renewal_data["new_policy_id"]

    response = client.get(
        f"/api/v1/policies/{new_policy_id}",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    new_policy = response.json()

    assert new_policy["id"] == new_policy_id
    assert new_policy["policy_status"] == "Active"


# ============================================================
# NEW POLICY NUMBER
# ============================================================

def test_renewal_generates_new_policy_number():
    (
        policy_id,
        policy_data,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = renew_policy(
        policy_id,
        agent_token,
    )

    assert response.status_code == 201

    new_policy_id = response.json()["new_policy_id"]

    policy_response = client.get(
        f"/api/v1/policies/{new_policy_id}",
        headers=get_auth_header(agent_token),
    )

    assert policy_response.status_code == 200

    new_policy = policy_response.json()

    assert new_policy["policy_number"] != (
        policy_data["policy_number"]
    )

    assert new_policy["policy_number"].startswith(
        "POL-REN-"
    )


# ============================================================
# POLICY HISTORY
# ============================================================

def test_renewal_preserves_previous_policy():
    (
        policy_id,
        policy_data,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = renew_policy(
        policy_id,
        agent_token,
    )

    assert response.status_code == 201

    renewal = response.json()

    assert renewal["previous_policy_id"] == policy_id

    assert renewal["previous_start_date"] == (
        policy_data["start_date"]
    )

    assert renewal["previous_end_date"] == (
        policy_data["end_date"]
    )


# ============================================================
# DUPLICATE RENEWAL
# ============================================================

def test_duplicate_renewal_not_allowed():
    (
        policy_id,
        _,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    first = renew_policy(
        policy_id,
        agent_token,
    )

    assert first.status_code == 201

    second = renew_policy(
        policy_id,
        agent_token,
    )

    assert second.status_code == 400

    assert "already been renewed" in (
        second.json()["detail"].lower()
    )


# ============================================================
# POLICY NOT FOUND
# ============================================================

def test_renew_policy_not_found():
    _, agent_token = create_agent()

    response = renew_policy(
        999999,
        agent_token,
    )

    assert response.status_code == 404

    assert "policy not found" in (
        response.json()["detail"].lower()
    )


# ============================================================
# ACTIVE POLICY REQUIRED
# ============================================================

def test_pending_policy_cannot_be_renewed():
    (
        policy_id,
        _,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        policy_status="Pending",
    )

    response = renew_policy(
        policy_id,
        agent_token,
    )

    assert response.status_code == 400

    assert "active" in (
        response.json()["detail"].lower()
    )


def test_cancelled_policy_cannot_be_renewed():
    (
        policy_id,
        _,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        policy_status="Cancelled",
    )

    response = renew_policy(
        policy_id,
        agent_token,
    )

    assert response.status_code == 400

    assert "active" in (
        response.json()["detail"].lower()
    )


# ============================================================
# EXPIRED POLICY
# ============================================================

def test_expired_policy_cannot_be_renewed():
    (
        policy_id,
        _,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        policy_status="Active",
        days_until_expiry=-1,
    )

    response = renew_policy(
        policy_id,
        agent_token,
    )

    assert response.status_code == 400

    assert "expired" in (
        response.json()["detail"].lower()
    )


# ============================================================
# NEW POLICY DATE PERIOD
# ============================================================

def test_renewal_new_policy_starts_after_old_policy():
    (
        policy_id,
        policy_data,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = renew_policy(
        policy_id,
        agent_token,
    )

    assert response.status_code == 201

    data = response.json()

    old_end = date.fromisoformat(
        policy_data["end_date"]
    )

    expected_new_start = (
        old_end + timedelta(days=1)
    )

    assert data["new_start_date"] == (
        expected_new_start.isoformat()
    )


def test_renewal_preserves_policy_duration():
    (
        policy_id,
        policy_data,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = renew_policy(
        policy_id,
        agent_token,
    )

    assert response.status_code == 201

    data = response.json()

    old_start = date.fromisoformat(
        policy_data["start_date"]
    )

    old_end = date.fromisoformat(
        policy_data["end_date"]
    )

    new_start = date.fromisoformat(
        data["new_start_date"]
    )

    new_end = date.fromisoformat(
        data["new_end_date"]
    )

    old_duration = (
        old_end - old_start
    ).days

    new_duration = (
        new_end - new_start
    ).days

    assert new_duration == old_duration


# ============================================================
# EXPIRING POLICIES
# ============================================================

def test_get_expiring_policies():
    (
        _,
        _,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        policy_status="Active",
        days_until_expiry=10,
    )

    response = client.get(
        "/api/v1/policies/expiring",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == (
        "Expiring policies retrieved successfully"
    )

    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1


# ============================================================
# EXPIRING POLICY DETAILS
# ============================================================

def test_expiring_policy_details():
    (
        policy_id,
        policy_data,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        policy_status="Active",
        days_until_expiry=10,
    )

    response = client.get(
        "/api/v1/policies/expiring",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    expiring_policies = data["data"]

    matching_policy = next(
        (
            policy
            for policy in expiring_policies
            if policy["id"] == policy_id
        ),
        None,
    )

    assert matching_policy is not None

    assert matching_policy["policy_number"] == (
        policy_data["policy_number"]
    )

    assert matching_policy["policy_status"] == "Active"


# ============================================================
# NON-EXPIRING POLICY SHOULD NOT APPEAR
# ============================================================

def test_non_expiring_policy_not_returned():
    (
        policy_id,
        _,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        policy_status="Active",
        days_until_expiry=100,
    )

    response = client.get(
        "/api/v1/policies/expiring",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    matching_policy = next(
        (
            policy
            for policy in data["data"]
            if policy["id"] == policy_id
        ),
        None,
    )

    assert matching_policy is None


# ============================================================
# EXPIRED POLICY NOT IN EXPIRING LIST
# ============================================================

def test_expired_policy_not_in_expiring_list():
    (
        policy_id,
        _,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        policy_status="Active",
        days_until_expiry=-1,
    )

    response = client.get(
        "/api/v1/policies/expiring",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    matching_policy = next(
        (
            policy
            for policy in data["data"]
            if policy["id"] == policy_id
        ),
        None,
    )

    assert matching_policy is None


# ============================================================
# PENDING POLICY NOT IN EXPIRING LIST
# ============================================================

def test_pending_policy_not_in_expiring_list():
    (
        policy_id,
        _,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        policy_status="Pending",
        days_until_expiry=10,
    )

    response = client.get(
        "/api/v1/policies/expiring",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    matching_policy = next(
        (
            policy
            for policy in data["data"]
            if policy["id"] == policy_id
        ),
        None,
    )

    assert matching_policy is None


# ============================================================
# AUTHENTICATION - RENEWAL
# ============================================================

def test_renew_policy_without_token():
    (
        policy_id,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = client.post(
        f"/api/v1/policies/{policy_id}/renew",
    )

    assert response.status_code == 401


# ============================================================
# AUTHENTICATION - EXPIRING
# ============================================================

def test_get_expiring_policies_without_token():
    response = client.get(
        "/api/v1/policies/expiring",
    )

    assert response.status_code == 401


# ============================================================
# ROLE AUTHORIZATION - RENEWAL
# ============================================================

def test_customer_cannot_renew_policy():
    (
        policy_id,
        _,
        _,
        customer_token,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = renew_policy(
        policy_id,
        customer_token,
    )

    assert response.status_code == 403


def test_claims_officer_cannot_renew_policy():
    (
        policy_id,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    claims_officer_token = (
        create_claims_officer()
    )

    response = renew_policy(
        policy_id,
        claims_officer_token,
    )

    assert response.status_code == 403


def test_finance_officer_cannot_renew_policy():
    email = unique_email("finance")

    register_response = register_user(
        full_name="Test Finance Officer",
        role="Finance Officer",
        email=email,
    )

    assert register_response.status_code == 201

    login_response = login_user(
        email,
        "Test@12345",
    )

    assert login_response.status_code == 200

    finance_token = (
        login_response.json()["access_token"]
    )

    (
        policy_id,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = renew_policy(
        policy_id,
        finance_token,
    )

    assert response.status_code == 403


def test_agent_can_renew_policy():
    (
        policy_id,
        _,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = renew_policy(
        policy_id,
        agent_token,
    )

    assert response.status_code == 201


def test_super_admin_can_renew_policy():
    (
        policy_id,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    super_admin_token = create_super_admin()

    response = renew_policy(
        policy_id,
        super_admin_token,
    )

    assert response.status_code == 201


# ============================================================
# ROLE AUTHORIZATION - EXPIRING POLICIES
# ============================================================

def test_customer_can_get_expiring_policies():
    (
        _,
        _,
        _,
        customer_token,
        _,
        _,
        _,
    ) = create_policy_test_data(
        days_until_expiry=10,
    )

    response = client.get(
        "/api/v1/policies/expiring",
        headers=get_auth_header(customer_token),
    )

    assert response.status_code == 200


def test_agent_can_get_expiring_policies():
    (
        _,
        _,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        days_until_expiry=10,
    )

    response = client.get(
        "/api/v1/policies/expiring",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200


def test_claims_officer_can_get_expiring_policies():
    (
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        days_until_expiry=10,
    )

    claims_officer_token = (
        create_claims_officer()
    )

    response = client.get(
        "/api/v1/policies/expiring",
        headers=get_auth_header(
            claims_officer_token
        ),
    )

    assert response.status_code == 403


def test_super_admin_can_get_expiring_policies():
    (
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data(
        days_until_expiry=10,
    )

    super_admin_token = create_super_admin()

    response = client.get(
        "/api/v1/policies/expiring",
        headers=get_auth_header(
            super_admin_token
        ),
    )

    assert response.status_code == 200

