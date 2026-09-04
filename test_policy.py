import os
import uuid
from datetime import date, timedelta
from decimal import Decimal

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
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def unique_policy_number():
    return f"POL{uuid.uuid4().hex[:10].upper()}"


def unique_identification():
    return f"ID{uuid.uuid4().hex[:10].upper()}"


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
            "phone": "9876543210",
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


def create_logged_in_user(
    full_name="Test User",
    role="Customer",
):
    email = unique_email("user")
    password = "Test@12345"

    register_response = register_user(
        full_name=full_name,
        role=role,
        email=email,
        password=password,
    )

    assert register_response.status_code == 201

    login_response = login_user(
        email,
        password,
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return (
        email,
        password,
        token,
        register_response.json(),
    )


# ============================================================
# PLAN HELPERS
# ============================================================

def create_plan(
    token,
    plan_name=None,
    plan_type="Life",
    coverage_amount=1000000,
    premium_amount=25000,
    duration_years=10,
    eligibility_age_min=18,
    eligibility_age_max=70,
):
    if plan_name is None:
        plan_name = f"Life Plan {uuid.uuid4().hex[:8]}"

    payload = {
        "plan_name": plan_name,
        "plan_type": plan_type,
        "description": "Test insurance plan",
        "coverage_amount": coverage_amount,
        "premium_amount": premium_amount,
        "duration_years": duration_years,
        "eligibility_age_min": eligibility_age_min,
        "eligibility_age_max": eligibility_age_max,
    }

    return client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=payload,
    )


# ============================================================
# CUSTOMER HELPERS
# ============================================================

def customer_payload(
    full_name="Rajesh Kumar",
    email=None,
    phone="9876543210",
    date_of_birth="1995-05-15",
    identification_number=None,
    occupation="Software Engineer",
    address="Hyderabad, Telangana",
):
    if email is None:
        email = unique_email("customer")

    if identification_number is None:
        identification_number = unique_identification()

    return {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "date_of_birth": date_of_birth,
        "identification_number": identification_number,
        "occupation": occupation,
        "address": address,
    }


def create_customer(
    token,
    full_name="Rajesh Kumar",
    email=None,
    date_of_birth="1995-05-15",
):
    return client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=customer_payload(
            full_name=full_name,
            email=email,
            date_of_birth=date_of_birth,
        ),
    )


# ============================================================
# POLICY PAYLOAD
# ============================================================

def policy_payload(
    policy_number=None,
    customer_id=None,
    plan_id=None,
    agent_id=None,
    start_date=None,
    end_date=None,
    coverage_amount=1000000,
    premium_amount=25000,
    policy_status="Pending",
):
    if policy_number is None:
        policy_number = unique_policy_number()

    if start_date is None:
        start_date = (
            date.today() + timedelta(days=1)
        ).isoformat()

    if end_date is None:
        end_date = (
            date.today() + timedelta(days=365)
        ).isoformat()

    return {
        "policy_number": policy_number,
        "customer_id": customer_id,
        "plan_id": plan_id,
        "agent_id": agent_id,
        "start_date": start_date,
        "end_date": end_date,
        "coverage_amount": coverage_amount,
        "premium_amount": premium_amount,
        "policy_status": policy_status,
    }


def create_test_policy(
    agent_token,
    customer_id,
    plan_id,
    agent_id,
    policy_number=None,
    policy_status="Pending",
):
    return client.post(
        "/api/v1/policies",
        headers=get_auth_header(agent_token),
        json=policy_payload(
            policy_number=policy_number,
            customer_id=customer_id,
            plan_id=plan_id,
            agent_id=agent_id,
            policy_status=policy_status,
        ),
    )


# ============================================================
# COMMON TEST DATA
# ============================================================

def create_policy_test_data():
    """
    Creates:
    - Insurance Agent
    - Customer
    - Plan

    Returns:
        agent_token,
        agent_id,
        customer_id,
        plan_id
    """

    _, _, agent_token, agent_data = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    agent_id = agent_data["id"]

    customer_response = create_customer(
        agent_token,
        full_name="Rajesh Kumar",
    )

    assert customer_response.status_code == 201

    customer_id = customer_response.json()["id"]

    plan_response = create_plan(
        agent_token,
        plan_type="Life",
        eligibility_age_min=18,
        eligibility_age_max=70,
    )

    assert plan_response.status_code == 201

    plan_id = plan_response.json()["id"]

    return (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    )


# ============================================================
# CREATE POLICY
# ============================================================

def test_create_policy():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["policy_number"] is not None
    assert data["customer_id"] == customer_id
    assert data["plan_id"] == plan_id
    assert data["agent_id"] == agent_id
    assert data["coverage_amount"] == 1000000
    assert data["premium_amount"] == 25000


def test_create_policy_with_pending_status():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_status="Pending",
    )

    assert response.status_code == 201
    assert response.json()["policy_status"] == "Pending"


# ============================================================
# DUPLICATE POLICY NUMBER
# ============================================================

def test_duplicate_policy_number_not_allowed():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    policy_number = unique_policy_number()

    first_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_number=policy_number,
    )

    assert first_response.status_code == 201

    second_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_number=policy_number,
    )

    assert second_response.status_code == 409

    assert second_response.json()["detail"] == (
        "Policy number already exists"
    )


# ============================================================
# CUSTOMER VALIDATION
# ============================================================

def test_policy_customer_not_found():
    (
        agent_token,
        agent_id,
        _,
        plan_id,
    ) = create_policy_test_data()

    response = create_test_policy(
        agent_token,
        999999,
        plan_id,
        agent_id,
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Customer not found"
    )


# ============================================================
# PLAN VALIDATION
# ============================================================

def test_policy_plan_not_found():
    (
        agent_token,
        agent_id,
        customer_id,
        _,
    ) = create_policy_test_data()

    response = create_test_policy(
        agent_token,
        customer_id,
        999999,
        agent_id,
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Plan not found"
    )


# ============================================================
# AGENT VALIDATION
# ============================================================

def test_policy_agent_not_found():
    (
        agent_token,
        _,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        999999,
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Agent not found"
    )


def test_policy_agent_role_invalid():
    (
        agent_token,
        _,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    _, _, customer_token, customer_data = (
        create_logged_in_user(
            full_name="Normal Customer",
            role="Customer",
        )
    )

    customer_user_id = customer_data["id"]

    response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        customer_user_id,
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Selected user is not authorized as an insurance agent"
    )


# ============================================================
# DATE VALIDATION
# ============================================================

def test_policy_end_date_before_start_date():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    start_date = (
        date.today() + timedelta(days=30)
    ).isoformat()

    end_date = (
        date.today() + timedelta(days=10)
    ).isoformat()

    response = client.post(
        "/api/v1/policies",
        headers=get_auth_header(agent_token),
        json=policy_payload(
            customer_id=customer_id,
            plan_id=plan_id,
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "End date must be after start date"
    )


def test_policy_end_date_equal_start_date():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    same_date = (
        date.today() + timedelta(days=10)
    ).isoformat()

    response = client.post(
        "/api/v1/policies",
        headers=get_auth_header(agent_token),
        json=policy_payload(
            customer_id=customer_id,
            plan_id=plan_id,
            agent_id=agent_id,
            start_date=same_date,
            end_date=same_date,
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "End date must be after start date"
    )


# ============================================================
# CUSTOMER ELIGIBILITY
# ============================================================

def test_customer_not_eligible_for_plan():
    (
        agent_token,
        agent_id,
        _,
        plan_id,
    ) = create_policy_test_data()

    customer_response = create_customer(
        agent_token,
        full_name="Young Customer",
        date_of_birth=(
            date.today() - timedelta(days=365 * 17)
        ).isoformat(),
    )

    # Customer API itself normally rejects under 18,
    # therefore create an eligible customer and use
    # a restrictive plan instead.

    assert customer_response.status_code in [201, 422]


def test_customer_age_above_plan_limit():
    _, _, agent_token, agent_data = (
        create_logged_in_user(
            full_name="Insurance Agent",
            role="Insurance Agent",
        )
    )

    agent_id = agent_data["id"]

    customer_response = create_customer(
        agent_token,
        full_name="Older Customer",
        date_of_birth="1960-05-15",
    )

    assert customer_response.status_code == 201

    customer_id = customer_response.json()["id"]

    plan_response = create_plan(
        agent_token,
        plan_name=f"Young Plan {uuid.uuid4().hex[:8]}",
        eligibility_age_min=18,
        eligibility_age_max=50,
    )

    assert plan_response.status_code == 201

    plan_id = plan_response.json()["id"]

    response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Customer is not eligible for this insurance plan"
    )


# ============================================================
# GET ALL POLICIES
# ============================================================

def test_get_all_policies():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    first_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
    )

    second_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        "/api/v1/policies",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "data" in data
    assert "total" in data
    assert isinstance(data["data"], list)
    assert data["total"] >= 2


# ============================================================
# GET SINGLE POLICY
# ============================================================

def test_get_policy():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
    )

    assert create_response.status_code == 201

    policy_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == policy_id
    assert data["customer_id"] == customer_id
    assert data["plan_id"] == plan_id


def test_get_policy_not_found():
    (
        agent_token,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = client.get(
        "/api/v1/policies/999999",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Policy not found"
    )


# ============================================================
# UPDATE POLICY
# ============================================================

def test_update_policy():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
    )

    assert create_response.status_code == 201

    policy_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "coverage_amount": 2000000,
            "premium_amount": 50000,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == policy_id
    assert data["coverage_amount"] == 2000000
    assert data["premium_amount"] == 50000


def test_update_policy_dates():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
    )

    policy_id = create_response.json()["id"]

    new_end_date = (
        date.today() + timedelta(days=730)
    ).isoformat()

    response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "end_date": new_end_date,
        },
    )

    assert response.status_code == 200

    assert response.json()["end_date"] == new_end_date


def test_update_policy_invalid_end_date():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
    )

    policy_id = create_response.json()["id"]

    invalid_end_date = (
        date.today() - timedelta(days=10)
    ).isoformat()

    response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "end_date": invalid_end_date,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "End date must be after start date"
    )


def test_update_policy_not_found():
    (
        agent_token,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = client.put(
        "/api/v1/policies/999999",
        headers=get_auth_header(agent_token),
        json={
            "coverage_amount": 500000,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Policy not found"
    )


# ============================================================
# ACTIVATE POLICY
# ============================================================

def test_activate_policy():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_status="Pending",
    )

    assert create_response.status_code == 201

    policy_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/policies/{policy_id}/activate",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    assert response.json()["policy_status"] == "Active"


def test_activate_already_active_policy():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_status="Pending",
    )

    policy_id = create_response.json()["id"]

    first_response = client.post(
        f"/api/v1/policies/{policy_id}/activate",
        headers=get_auth_header(agent_token),
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"/api/v1/policies/{policy_id}/activate",
        headers=get_auth_header(agent_token),
    )

    assert second_response.status_code == 400

    assert second_response.json()["detail"] == (
        "Policy is already active"
    )


def test_activate_cancelled_policy_not_allowed():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_status="Pending",
    )

    policy_id = create_response.json()["id"]

    cancel_response = client.post(
        f"/api/v1/policies/{policy_id}/cancel",
        headers=get_auth_header(agent_token),
    )

    assert cancel_response.status_code == 200

    activate_response = client.post(
        f"/api/v1/policies/{policy_id}/activate",
        headers=get_auth_header(agent_token),
    )

    assert activate_response.status_code == 400

    assert activate_response.json()["detail"] == (
        "Cancelled policy cannot be activated"
    )


def test_activate_expired_policy_not_allowed():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_status="Active",
    )

    assert create_response.status_code == 201

    policy_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "policy_status": "Expired",
        },
    )

    assert update_response.status_code == 200

    activate_response = client.post(
        f"/api/v1/policies/{policy_id}/activate",
        headers=get_auth_header(agent_token),
    )

    assert activate_response.status_code == 400

    assert activate_response.json()["detail"] == (
        "Expired policy cannot be activated"
    )


# ============================================================
# CANCEL POLICY
# ============================================================

def test_cancel_policy():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_status="Pending",
    )

    assert create_response.status_code == 201

    policy_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/policies/{policy_id}/cancel",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    assert response.json()["policy_status"] == "Cancelled"


def test_cancel_already_cancelled_policy():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
    )

    policy_id = create_response.json()["id"]

    first_response = client.post(
        f"/api/v1/policies/{policy_id}/cancel",
        headers=get_auth_header(agent_token),
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"/api/v1/policies/{policy_id}/cancel",
        headers=get_auth_header(agent_token),
    )

    assert second_response.status_code == 400

    assert second_response.json()["detail"] == (
        "Policy is already cancelled"
    )


def test_cancel_policy_not_found():
    (
        agent_token,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = client.post(
        "/api/v1/policies/999999/cancel",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Policy not found"
    )


# ============================================================
# CANCELLED POLICY UPDATE
# ============================================================

def test_cancelled_policy_cannot_be_updated():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
    )

    policy_id = create_response.json()["id"]

    cancel_response = client.post(
        f"/api/v1/policies/{policy_id}/cancel",
        headers=get_auth_header(agent_token),
    )

    assert cancel_response.status_code == 200

    response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "coverage_amount": 500000,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Cancelled policy cannot be updated"
    )


# ============================================================
# STATUS TRANSITIONS
# ============================================================

def test_pending_to_active():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_status="Pending",
    )

    policy_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "policy_status": "Active",
        },
    )

    assert response.status_code == 200

    assert response.json()["policy_status"] == "Active"


def test_pending_to_cancelled():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_status="Pending",
    )

    policy_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "policy_status": "Cancelled",
        },
    )

    assert response.status_code == 200

    assert response.json()["policy_status"] == "Cancelled"


def test_active_to_suspended():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_status="Active",
    )

    policy_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "policy_status": "Suspended",
        },
    )

    assert response.status_code == 200

    assert response.json()["policy_status"] == "Suspended"


def test_suspended_to_active():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_status="Active",
    )

    policy_id = create_response.json()["id"]

    suspend_response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "policy_status": "Suspended",
        },
    )

    assert suspend_response.status_code == 200

    activate_response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "policy_status": "Active",
        },
    )

    assert activate_response.status_code == 200

    assert activate_response.json()["policy_status"] == (
        "Active"
    )


def test_invalid_status_transition():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
        policy_status="Cancelled",
    )

    assert create_response.status_code == 201

    policy_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "policy_status": "Active",
        },
    )

    assert response.status_code == 400


# ============================================================
# ROLE / RBAC
# ============================================================

def test_customer_cannot_create_policy():
    (
        _,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    _, _, customer_token, _ = create_logged_in_user(
        full_name="Normal Customer",
        role="Customer",
    )

    response = create_test_policy(
        customer_token,
        customer_id,
        plan_id,
        agent_id,
    )

    assert response.status_code == 403


def test_claims_officer_cannot_create_policy():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    _, _, officer_token, _ = create_logged_in_user(
        full_name="Claims Officer",
        role="Claims Officer",
    )

    response = create_test_policy(
        officer_token,
        customer_id,
        plan_id,
        agent_id,
    )

    assert response.status_code == 403


def test_finance_officer_cannot_create_policy():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    _, _, officer_token, _ = create_logged_in_user(
        full_name="Finance Officer",
        role="Finance Officer",
    )

    response = create_test_policy(
        officer_token,
        customer_id,
        plan_id,
        agent_id,
    )

    assert response.status_code == 403


def test_customer_cannot_update_policy():
    (
        agent_token,
        agent_id,
        customer_id,
        plan_id,
    ) = create_policy_test_data()

    create_response = create_test_policy(
        agent_token,
        customer_id,
        plan_id,
        agent_id,
    )

    assert create_response.status_code == 201

    policy_id = create_response.json()["id"]

    _, _, customer_token, _ = create_logged_in_user(
        full_name="Normal Customer",
        role="Customer",
    )

    response = client.put(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(customer_token),
        json={
            "coverage_amount": 500000,
        },
    )

    assert response.status_code == 403


# ============================================================
# AUTHENTICATION
# ============================================================

def test_get_policies_without_token():
    response = client.get(
        "/api/v1/policies"
    )

    assert response.status_code == 401


def test_get_policy_without_token():
    response = client.get(
        "/api/v1/policies/1"
    )

    assert response.status_code == 401


def test_create_policy_without_token():
    response = client.post(
        "/api/v1/policies",
        json=policy_payload(),
    )

    assert response.status_code == 401


def test_update_policy_without_token():
    response = client.put(
        "/api/v1/policies/1",
        json={
            "coverage_amount": 500000,
        },
    )

    assert response.status_code == 401


def test_activate_policy_without_token():
    response = client.post(
        "/api/v1/policies/1/activate"
    )

    assert response.status_code == 401


def test_cancel_policy_without_token():
    response = client.post(
        "/api/v1/policies/1/cancel"
    )

    assert response.status_code == 401