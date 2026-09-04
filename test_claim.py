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

    customer_id = customer_data["id"]

    return (
        customer_id,
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
# PLAN HELPER
# ============================================================

def create_plan(agent_token):
    plan_payload = {
        "plan_name": f"Health Plan {uuid4().hex[:6]}",
        "plan_type": "Health",
        "description": "Test health insurance plan",
        "coverage_amount": 1000000,
        "premium_amount": 50000,
        "duration_years": 1,
        "eligibility_age_min": 18,
        "eligibility_age_max": 65,
    }

    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(agent_token),
        json=plan_payload,
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
):
    customer_id, customer_token, _ = create_customer()

    agent_id, agent_token = create_agent()

    plan_id = create_plan(agent_token)

    policy_payload = {
        "policy_number": (
            f"POL-{uuid4().hex[:8].upper()}"
        ),
        "customer_id": customer_id,
        "plan_id": plan_id,
        "agent_id": agent_id,
        "start_date": (
            date.today() - timedelta(days=30)
        ).isoformat(),
        "end_date": (
            date.today() + timedelta(days=335)
        ).isoformat(),
        "coverage_amount": 1000000,
        "premium_amount": 50000,
        "policy_status": policy_status,
    }

    response = client.post(
        "/api/v1/policies",
        headers=get_auth_header(agent_token),
        json=policy_payload,
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

    policy_id = data["id"]

    return (
        policy_id,
        agent_token,
        customer_token,
        customer_id,
        agent_id,
        plan_id,
    )


# ============================================================
# CLAIM HELPER
# ============================================================

def create_claim(
    token,
    policy_id,
    customer_id,
    claim_number=None,
    claim_type="Health",
    incident_date=None,
    claim_amount=50000,
    description="Hospitalization claim",
    status="Submitted",
):
    if claim_number is None:
        claim_number = (
            f"CLM-{uuid4().hex[:10].upper()}"
        )

    if incident_date is None:
        incident_date = date.today().isoformat()

    return client.post(
        "/api/v1/claims",
        headers=get_auth_header(token),
        json={
            "claim_number": claim_number,
            "policy_id": policy_id,
            "customer_id": customer_id,
            "claim_type": claim_type,
            "incident_date": incident_date,
            "claim_amount": claim_amount,
            "description": description,
            "status": status,
        },
    )


# ============================================================
# CREATE CLAIM
# ============================================================

def test_create_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
    )

    assert response.status_code == 201, (
        f"Claim creation failed: "
        f"{response.text}"
    )

    data = response.json()

    assert data["policy_id"] == policy_id
    assert data["customer_id"] == customer_id
    assert data["claim_type"] == "Health"
    assert float(data["claim_amount"]) == 50000
    assert data["status"] == "Submitted"
    assert "claim_number" in data


# ============================================================
# CLAIM TYPES
# ============================================================

def test_create_life_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_type="Life",
    )

    assert response.status_code == 201


def test_create_vehicle_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_type="Vehicle",
    )

    assert response.status_code == 201


def test_create_property_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_type="Property",
    )

    assert response.status_code == 201


def test_create_travel_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_type="Travel",
    )

    assert response.status_code == 201


def test_create_other_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_type="Other",
    )

    assert response.status_code == 201


def test_invalid_claim_type():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_type="Invalid Type",
    )

    assert response.status_code == 422


# ============================================================
# CLAIM STATUS
# ============================================================

def test_invalid_claim_status():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        status="Invalid Status",
    )

    assert response.status_code == 422


# ============================================================
# DUPLICATE CLAIM NUMBER
# ============================================================

def test_duplicate_claim_number_not_allowed():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    claim_number = (
        f"CLM-{uuid4().hex[:10].upper()}"
    )

    first = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_number=claim_number,
    )

    assert first.status_code == 201

    second = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_number=claim_number,
        incident_date=(
            date.today() - timedelta(days=1)
        ).isoformat(),
    )

    assert second.status_code in [400, 409]


# ============================================================
# DUPLICATE INCIDENT
# ============================================================

def test_duplicate_claim_for_same_incident_not_allowed():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    incident_date = date.today().isoformat()

    first = create_claim(
        agent_token,
        policy_id,
        customer_id,
        incident_date=incident_date,
    )

    assert first.status_code == 201

    second = create_claim(
        agent_token,
        policy_id,
        customer_id,
        incident_date=incident_date,
    )

    assert second.status_code in [400, 409]

    assert "duplicate" in (
        second.json()["detail"].lower()
    )


# ============================================================
# POLICY VALIDATION
# ============================================================

def test_claim_policy_not_found():
    (
        _,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        999999,
        customer_id,
    )

    assert response.status_code == 404


def test_claim_only_for_active_policy():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data(
        policy_status="Pending"
    )

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
    )

    assert response.status_code in [400, 422]

    assert "active" in (
        response.json()["detail"].lower()
    )


def test_customer_must_belong_to_policy():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    other_customer_id, _, _ = create_customer()

    response = create_claim(
        agent_token,
        policy_id,
        other_customer_id,
    )

    assert response.status_code in [400, 422]

    assert "customer" in (
        response.json()["detail"].lower()
    )


# ============================================================
# INCIDENT DATE VALIDATION
# ============================================================

def test_incident_date_before_policy_start_not_allowed():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    incident_date = (
        date.today() - timedelta(days=60)
    ).isoformat()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        incident_date=incident_date,
    )

    assert response.status_code in [400, 422]

    assert "incident" in (
        response.json()["detail"].lower()
    )


def test_incident_date_after_policy_end_not_allowed():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    incident_date = (
        date.today() + timedelta(days=400)
    ).isoformat()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        incident_date=incident_date,
    )

    assert response.status_code in [400, 422]

    assert "incident" in (
        response.json()["detail"].lower()
    )


# ============================================================
# CLAIM AMOUNT VALIDATION
# ============================================================

def test_claim_amount_cannot_exceed_coverage():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_amount=2000000,
    )

    assert response.status_code in [400, 422]

    assert "coverage" in (
        response.json()["detail"].lower()
    )


def test_claim_amount_cannot_be_zero():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_amount=0,
    )

    assert response.status_code == 422


def test_claim_amount_cannot_be_negative():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_amount=-1000,
    )

    assert response.status_code == 422


# ============================================================
# GET ALL CLAIMS
# ============================================================

def test_get_all_claims():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/claims",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    if isinstance(data, dict):
        claims = data.get(
            "data",
            data.get(
                "claims",
                [],
            ),
        )
    else:
        claims = data

    assert len(claims) >= 1


# ============================================================
# GET SINGLE CLAIM
# ============================================================

def test_get_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/claims/{claim_id}",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == claim_id
    assert data["policy_id"] == policy_id
    assert data["customer_id"] == customer_id


def test_get_claim_not_found():
    _, agent_token, _, _, _, _ = (
        create_policy_test_data()
    )

    response = client.get(
        "/api/v1/claims/999999",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404


# ============================================================
# UPDATE CLAIM
# ============================================================

def test_update_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/claims/{claim_id}",
        headers=get_auth_header(agent_token),
        json={
            "claim_type": "Vehicle",
            "claim_amount": 75000,
            "description": "Updated vehicle claim",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == claim_id
    assert data["claim_type"] == "Vehicle"
    assert float(data["claim_amount"]) == 75000
    assert data["description"] == "Updated vehicle claim"


def test_update_claim_not_found():
    _, agent_token, _, _, _, _ = (
        create_policy_test_data()
    )

    response = client.put(
        "/api/v1/claims/999999",
        headers=get_auth_header(agent_token),
        json={
            "claim_type": "Health",
            "claim_amount": 50000,
        },
    )

    assert response.status_code == 404


# ============================================================
# STATUS TRANSITIONS
# ============================================================

def test_submit_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        status="Submitted",
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/claims/{claim_id}/submit",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Under Review"


def test_approve_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        status="Under Review",
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/claims/{claim_id}/approve",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Approved"


def test_reject_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        status="Under Review",
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/claims/{claim_id}/reject",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Rejected"


def test_submit_claim_not_found():
    _, agent_token, _, _, _, _ = (
        create_policy_test_data()
    )

    response = client.post(
        "/api/v1/claims/999999/submit",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404


def test_approve_claim_not_found():
    _, agent_token, _, _, _, _ = (
        create_policy_test_data()
    )

    response = client.post(
        "/api/v1/claims/999999/approve",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404


def test_reject_claim_not_found():
    _, agent_token, _, _, _, _ = (
        create_policy_test_data()
    )

    response = client.post(
        "/api/v1/claims/999999/reject",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404


# ============================================================
# INVALID STATUS TRANSITIONS
# ============================================================

def test_cannot_approve_submitted_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        status="Submitted",
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/claims/{claim_id}/approve",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 400


def test_cannot_submit_under_review_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        status="Under Review",
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/claims/{claim_id}/submit",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 400


def test_cannot_approve_rejected_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        status="Rejected",
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/claims/{claim_id}/approve",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 400


def test_cannot_update_settled_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        status="Settled",
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/claims/{claim_id}",
        headers=get_auth_header(agent_token),
        json={
            "description": "Updated description",
        },
    )

    assert response.status_code == 400


# ============================================================
# AUTHENTICATION
# ============================================================

def test_create_claim_without_token():
    (
        policy_id,
        _,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = client.post(
        "/api/v1/claims",
        json={
            "claim_number": (
                f"CLM-{uuid4().hex[:10].upper()}"
            ),
            "policy_id": policy_id,
            "customer_id": customer_id,
            "claim_type": "Health",
            "incident_date": date.today().isoformat(),
            "claim_amount": 50000,
            "description": "Hospitalization claim",
            "status": "Submitted",
        },
    )

    assert response.status_code == 401


def test_get_claims_without_token():
    response = client.get(
        "/api/v1/claims",
    )

    assert response.status_code == 401


def test_get_claim_without_token():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/claims/{claim_id}",
    )

    assert response.status_code == 401


def test_update_claim_without_token():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/claims/{claim_id}",
        json={
            "claim_amount": 75000,
        },
    )

    assert response.status_code == 401


def test_submit_claim_without_token():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/claims/{claim_id}/submit",
    )

    assert response.status_code == 401


def test_approve_claim_without_token():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        status="Under Review",
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/claims/{claim_id}/approve",
    )

    assert response.status_code == 401


def test_reject_claim_without_token():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        status="Under Review",
    )

    assert create_response.status_code == 201

    claim_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/claims/{claim_id}/reject",
    )

    assert response.status_code == 401

    # ============================================================
# LEVEL 12
# CLAIM FILTERING / PAGINATION / SORTING
# ============================================================


def test_filter_claims_by_status():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    submitted = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_type="Health",
        claim_amount=30000,
        status="Submitted",
    )

    assert submitted.status_code == 201

    response = client.get(
        "/api/v1/claims?claim_status=Submitted",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["total"] >= 1

    for claim in data["data"]:
        assert claim["status"] == "Submitted"


def test_filter_claims_by_type():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_type="Life",
        claim_amount=40000,
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/claims?claim_type=Life",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["total"] >= 1

    for claim in data["data"]:
        assert claim["claim_type"] == "Life"


def test_filter_claims_by_date_range():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    incident_date = (
        date.today() - timedelta(days=5)
    ).isoformat()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        incident_date=incident_date,
        claim_amount=45000,
    )

    assert response.status_code == 201

    date_from = (
        date.today() - timedelta(days=10)
    ).isoformat()

    date_to = date.today().isoformat()

    response = client.get(
        "/api/v1/claims",
        params={
            "date_from": date_from,
            "date_to": date_to,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["total"] >= 1

    for claim in data["data"]:
        claim_date = date.fromisoformat(
            claim["incident_date"]
        )

        assert claim_date >= date.fromisoformat(
            date_from
        )

        assert claim_date <= date.fromisoformat(
            date_to
        )


def test_filter_claims_by_amount_range():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_amount=75000,
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/claims",
        params={
            "amount_from": 50000,
            "amount_to": 100000,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["total"] >= 1

    for claim in data["data"]:
        amount = float(
            claim["claim_amount"]
        )

        assert amount >= 50000
        assert amount <= 100000


def test_claim_pagination():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    for index, amount in enumerate(
        [10000, 20000, 30000]
    ):
        incident_date = (
            date.today()
            - timedelta(days=index)
        ).isoformat()

        response = create_claim(
            agent_token,
            policy_id,
            customer_id,
            claim_amount=amount,
            incident_date=incident_date,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/claims",
        params={
            "page": 1,
            "limit": 2,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["page"] == 1
    assert data["limit"] == 2
    assert len(data["data"]) == 2
    assert data["total"] >= 3


def test_claim_pagination_second_page():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    for index, amount in enumerate(
        [11000, 22000, 33000]
    ):
        incident_date = (
            date.today()
            - timedelta(days=index)
        ).isoformat()

        response = create_claim(
            agent_token,
            policy_id,
            customer_id,
            claim_amount=amount,
            incident_date=incident_date,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/claims",
        params={
            "page": 2,
            "limit": 2,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["page"] == 2
    assert data["limit"] == 2
    assert len(data["data"]) <= 2
    assert data["total"] >= 3


def test_sort_claims_by_amount_ascending():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    amounts = [
        70000,
        20000,
        50000,
    ]

    for index, amount in enumerate(amounts):

        incident_date = (
            date.today()
            - timedelta(days=index)
        ).isoformat()

        response = create_claim(
            agent_token,
            policy_id,
            customer_id,
            claim_amount=amount,
            incident_date=incident_date,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/claims",
        params={
            "sort_by": "claim_amount",
            "sort_order": "asc",
            "limit": 100,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    amounts = [
        float(claim["claim_amount"])
        for claim in data["data"]
    ]

    assert amounts == sorted(amounts)


def test_sort_claims_by_amount_descending():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    amounts = [
        15000,
        90000,
        45000,
    ]

    for index, amount in enumerate(amounts):

        incident_date = (
            date.today()
            - timedelta(days=index)
        ).isoformat()

        response = create_claim(
            agent_token,
            policy_id,
            customer_id,
            claim_amount=amount,
            incident_date=incident_date,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/claims",
        params={
            "sort_by": "claim_amount",
            "sort_order": "desc",
            "limit": 100,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    amounts = [
        float(claim["claim_amount"])
        for claim in data["data"]
    ]

    assert amounts == sorted(
        amounts,
        reverse=True,
    )


def test_sort_claims_by_incident_date_ascending():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    dates = [
        date.today() - timedelta(days=1),
        date.today() - timedelta(days=10),
        date.today() - timedelta(days=5),
    ]

    for index, incident_date in enumerate(dates):

        response = create_claim(
            agent_token,
            policy_id,
            customer_id,
            claim_amount=10000 + (index * 1000),
            incident_date=incident_date.isoformat(),
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/claims",
        params={
            "sort_by": "incident_date",
            "sort_order": "asc",
            "limit": 100,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    result_dates = [
        date.fromisoformat(
            claim["incident_date"]
        )
        for claim in data["data"]
    ]

    assert result_dates == sorted(
        result_dates
    )


def test_sort_claims_by_incident_date_descending():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    dates = [
        date.today() - timedelta(days=2),
        date.today() - timedelta(days=8),
        date.today() - timedelta(days=4),
    ]

    for index, incident_date in enumerate(dates):

        response = create_claim(
            agent_token,
            policy_id,
            customer_id,
            claim_amount=15000 + (index * 1000),
            incident_date=incident_date.isoformat(),
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/claims",
        params={
            "sort_by": "incident_date",
            "sort_order": "desc",
            "limit": 100,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    result_dates = [
        date.fromisoformat(
            claim["incident_date"]
        )
        for claim in data["data"]
    ]

    assert result_dates == sorted(
        result_dates,
        reverse=True,
    )


def test_invalid_claim_sort_field():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = client.get(
        "/api/v1/claims",
        params={
            "sort_by": "invalid_field",
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 400

    assert "invalid sort field" in (
        response.json()["detail"].lower()
    )


def test_invalid_claim_sort_order():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = client.get(
        "/api/v1/claims",
        params={
            "sort_order": "invalid",
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 400

    assert "invalid sort order" in (
        response.json()["detail"].lower()
    )


def test_invalid_claim_date_range():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = client.get(
        "/api/v1/claims",
        params={
            "date_from": "2026-12-31",
            "date_to": "2026-01-01",
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 400

    assert "date_from" in (
        response.json()["detail"].lower()
    )


def test_invalid_claim_amount_range():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    response = client.get(
        "/api/v1/claims",
        params={
            "amount_from": 100000,
            "amount_to": 10000,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 400

    assert "amount_from" in (
        response.json()["detail"].lower()
    )