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
    coverage_amount=1000000,
):
    customer_id, customer_token, _ = create_customer()

    agent_id, agent_token = create_agent()

    plan_id = create_plan(agent_token)

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
            "start_date": (
                date.today() - timedelta(days=30)
            ).isoformat(),
            "end_date": (
                date.today() + timedelta(days=335)
            ).isoformat(),
            "coverage_amount": coverage_amount,
            "premium_amount": 50000,
            "policy_status": "Active",
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
    claim_amount=50000,
    status="Under Review",
):
    response = client.post(
        "/api/v1/claims",
        headers=get_auth_header(token),
        json={
            "claim_number": (
                f"CLM-{uuid4().hex[:10].upper()}"
            ),
            "policy_id": policy_id,
            "customer_id": customer_id,
            "claim_type": "Health",
            "incident_date": date.today().isoformat(),
            "claim_amount": claim_amount,
            "description": "Hospitalization claim",
            "status": status,
        },
    )

    assert response.status_code == 201, (
        f"Claim creation failed: "
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
# COMPLETE CLAIM TEST DATA
# ============================================================

def create_claim_test_data(
    claim_amount=50000,
    policy_coverage=1000000,
    claim_status="Under Review",
):
    (
        policy_id,
        agent_token,
        customer_token,
        customer_id,
        agent_id,
        plan_id,
    ) = create_policy_test_data(
        coverage_amount=policy_coverage,
    )

    claim_id = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_amount=claim_amount,
        status=claim_status,
    )

    officer_token = create_claims_officer()

    return (
        claim_id,
        agent_token,
        customer_token,
        officer_token,
        customer_id,
        policy_id,
        agent_id,
        plan_id,
    )


# ============================================================
# ASSESSMENT HELPER
# ============================================================

def create_assessment(
    token,
    claim_id,
    eligible_amount=40000,
    assessment_notes="Claim verified and eligible",
    recommendation="Approved",
):
    return client.post(
        f"/api/v1/claims/{claim_id}/assessment",
        headers=get_auth_header(token),
        json={
            "eligible_amount": eligible_amount,
            "assessment_notes": assessment_notes,
            "recommendation": recommendation,
        },
    )


# ============================================================
# CREATE ASSESSMENT
# ============================================================

def test_create_claim_assessment():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
        assessment_notes="Hospital bills verified",
        recommendation="Approved",
    )

    assert response.status_code == 201, (
        f"Assessment creation failed: "
        f"{response.text}"
    )

    data = response.json()

    assert data["claim_id"] == claim_id
    assert data["assessor_id"] > 0
    assert float(data["eligible_amount"]) == 40000
    assert data["assessment_notes"] == (
        "Hospital bills verified"
    )
    assert data["recommendation"] == "Approved"
    assert "assessed_at" in data
    assert "id" in data


# ============================================================
# RECOMMENDATIONS
# ============================================================

def test_approved_recommendation():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
        recommendation="Approved",
    )

    assert response.status_code == 201


def test_partially_approved_recommendation():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=25000,
        recommendation="Partially Approved",
    )

    assert response.status_code == 201


def test_rejected_recommendation():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=1000,
        recommendation="Rejected",
    )

    assert response.status_code == 201


# ============================================================
# INVALID RECOMMENDATION
# ============================================================

def test_invalid_recommendation():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
        recommendation="Pending",
    )

    assert response.status_code == 400

    assert "invalid recommendation" in (
        response.json()["detail"].lower()
    )


# ============================================================
# ELIGIBLE AMOUNT VALIDATION
# ============================================================

def test_eligible_amount_cannot_be_zero():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=0,
    )

    assert response.status_code == 422


def test_eligible_amount_cannot_be_negative():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=-1000,
    )

    assert response.status_code == 422


def test_eligible_amount_cannot_exceed_claim_amount():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data(
        claim_amount=50000,
        policy_coverage=1000000,
    )

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=60000,
    )

    assert response.status_code == 400

    assert "claim amount" in (
        response.json()["detail"].lower()
    )


def test_eligible_amount_cannot_exceed_policy_coverage():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data(
        claim_amount=100000,
        policy_coverage=100000,
    )

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=110000,
    )

    assert response.status_code == 400

    assert "policy coverage" in (
        response.json()["detail"].lower()
    )


# ============================================================
# ELIGIBLE AMOUNT WITHIN CLAIM AND COVERAGE
# ============================================================

def test_eligible_amount_within_claim_and_coverage():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data(
        claim_amount=50000,
        policy_coverage=100000,
    )

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=45000,
    )

    assert response.status_code == 201

    data = response.json()

    assert float(data["eligible_amount"]) == 45000


# ============================================================
# DUPLICATE ASSESSMENT
# ============================================================

def test_duplicate_assessment_not_allowed():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    first = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
    )

    assert first.status_code == 201

    second = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=30000,
    )

    assert second.status_code == 400

    assert "assessment already exists" in (
        second.json()["detail"].lower()
    )


# ============================================================
# CLAIM NOT FOUND
# ============================================================

def test_create_assessment_claim_not_found():
    officer_token = create_claims_officer()

    response = create_assessment(
        officer_token,
        999999,
        eligible_amount=40000,
    )

    assert response.status_code == 404

    assert "claim not found" in (
        response.json()["detail"].lower()
    )


def test_get_assessment_claim_not_found():
    officer_token = create_claims_officer()

    response = client.get(
        "/api/v1/claims/999999/assessment",
        headers=get_auth_header(officer_token),
    )

    assert response.status_code == 404

    assert "claim not found" in (
        response.json()["detail"].lower()
    )


# ============================================================
# GET ASSESSMENT
# ============================================================

def test_get_claim_assessment():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    create_response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
        assessment_notes="All documents verified",
        recommendation="Approved",
    )

    assert create_response.status_code == 201

    assessment_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/claims/{claim_id}/assessment",
        headers=get_auth_header(officer_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == assessment_id
    assert data["claim_id"] == claim_id
    assert float(data["eligible_amount"]) == 40000
    assert data["assessment_notes"] == (
        "All documents verified"
    )
    assert data["recommendation"] == "Approved"


# ============================================================
# GET ASSESSMENT BEFORE CREATION
# ============================================================

def test_get_assessment_not_found():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = client.get(
        f"/api/v1/claims/{claim_id}/assessment",
        headers=get_auth_header(officer_token),
    )

    assert response.status_code == 404

    assert "assessment not found" in (
        response.json()["detail"].lower()
    )


# ============================================================
# CLAIM STATUS VALIDATION
# ============================================================

def test_assessment_requires_under_review_claim():
    (
        policy_id,
        agent_token,
        customer_token,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    claim_id = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_amount=50000,
        status="Submitted",
    )

    officer_token = create_claims_officer()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
    )

    assert response.status_code == 400

    assert "under review" in (
        response.json()["detail"].lower()
    )


def test_assessment_not_allowed_for_rejected_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    claim_id = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_amount=50000,
        status="Rejected",
    )

    officer_token = create_claims_officer()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
    )

    assert response.status_code == 400

    assert "under review" in (
        response.json()["detail"].lower()
    )


def test_assessment_not_allowed_for_approved_claim():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
    ) = create_policy_test_data()

    claim_id = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_amount=50000,
        status="Approved",
    )

    officer_token = create_claims_officer()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
    )

    assert response.status_code == 400

    assert "under review" in (
        response.json()["detail"].lower()
    )


# ============================================================
# ASSESSMENT NOTES VALIDATION
# ============================================================

def test_assessment_notes_required():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
        assessment_notes="",
    )

    assert response.status_code == 422


def test_assessment_notes_minimum_length():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
        assessment_notes="abc",
    )

    assert response.status_code == 422


# ============================================================
# AUTHENTICATION
# ============================================================

def test_create_assessment_without_token():
    (
        claim_id,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = client.post(
        f"/api/v1/claims/{claim_id}/assessment",
        json={
            "eligible_amount": 40000,
            "assessment_notes": "Claim verified",
            "recommendation": "Approved",
        },
    )

    assert response.status_code == 401


def test_get_assessment_without_token():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    create_response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/api/v1/claims/{claim_id}/assessment",
    )

    assert response.status_code == 401


# ============================================================
# ROLE AUTHORIZATION
# ============================================================

def test_agent_cannot_create_assessment():
    (
        claim_id,
        agent_token,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        agent_token,
        claim_id,
        eligible_amount=40000,
    )

    assert response.status_code == 403


def test_customer_cannot_create_assessment():
    (
        claim_id,
        _,
        customer_token,
        _,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        customer_token,
        claim_id,
        eligible_amount=40000,
    )

    assert response.status_code == 403


def test_claims_officer_can_create_assessment():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
    )

    assert response.status_code == 201


def test_super_admin_can_create_assessment():
    (
        claim_id,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    super_admin_token = create_super_admin()

    response = create_assessment(
        super_admin_token,
        claim_id,
        eligible_amount=40000,
    )

    assert response.status_code == 201


# ============================================================
# GET ROLE ACCESS
# ============================================================

def test_customer_can_get_assessment():
    (
        claim_id,
        _,
        customer_token,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    create_response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/api/v1/claims/{claim_id}/assessment",
        headers=get_auth_header(customer_token),
    )

    assert response.status_code == 200


def test_agent_can_get_assessment():
    (
        claim_id,
        agent_token,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    create_response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/api/v1/claims/{claim_id}/assessment",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200


def test_claims_officer_can_get_assessment():
    (
        claim_id,
        _,
        _,
        officer_token,
        _,
        _,
        _,
        _,
    ) = create_claim_test_data()

    create_response = create_assessment(
        officer_token,
        claim_id,
        eligible_amount=40000,
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/api/v1/claims/{claim_id}/assessment",
        headers=get_auth_header(officer_token),
    )

    assert response.status_code == 200