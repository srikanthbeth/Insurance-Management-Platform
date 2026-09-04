
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

    register_response = register_user(
        full_name="Test Insurance Agent",
        role="Insurance Agent",
        email=email,
    )

    assert register_response.status_code == 201, (
        f"Agent registration failed: "
        f"{register_response.text}"
    )

    data = register_response.json()

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
# FINANCE OFFICER HELPER
# ============================================================

def create_finance_officer():
    email = unique_email("finance_officer")

    register_response = register_user(
        full_name="Test Finance Officer",
        role="Finance Officer",
        email=email,
    )

    assert register_response.status_code == 201, (
        f"Finance Officer registration failed: "
        f"{register_response.text}"
    )

    login_response = login_user(
        email,
        "Test@12345",
    )

    assert login_response.status_code == 200, (
        f"Finance Officer login failed: "
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

def create_policy_test_data():
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
            "coverage_amount": 1000000,
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
# ASSESSMENT HELPER
# ============================================================

def create_assessment(
    token,
    claim_id,
    eligible_amount=40000,
):
    return client.post(
        f"/api/v1/claims/{claim_id}/assessment",
        headers=get_auth_header(token),
        json={
            "eligible_amount": eligible_amount,
            "assessment_notes": "Hospital bills verified",
            "recommendation": "Approved",
        },
    )


# ============================================================
# COMPLETE APPROVED CLAIM HELPER
# ============================================================

def create_approved_claim_test_data(
    claim_amount=50000,
    eligible_amount=40000,
):
    (
        policy_id,
        agent_token,
        customer_token,
        customer_id,
        agent_id,
        plan_id,
    ) = create_policy_test_data()

    claim_id = create_claim(
        agent_token,
        policy_id,
        customer_id,
        claim_amount=claim_amount,
        status="Under Review",
    )

    claims_officer_token = create_claims_officer()

    assessment_response = create_assessment(
        claims_officer_token,
        claim_id,
        eligible_amount=eligible_amount,
    )

    assert assessment_response.status_code == 201, (
        f"Assessment creation failed: "
        f"{assessment_response.text}"
    )

    # --------------------------------------------------------
    # APPROVE CLAIM
    # --------------------------------------------------------

    approve_response = client.post(
        f"/api/v1/claims/{claim_id}/approve",
        headers=get_auth_header(agent_token),
    )

    assert approve_response.status_code == 200, (
        f"Claim approval failed: "
        f"{approve_response.text}"
    )

    assert approve_response.json()["status"] == "Approved"

    finance_token = create_finance_officer()

    return (
        claim_id,
        finance_token,
        agent_token,
        customer_token,
        claims_officer_token,
        customer_id,
        policy_id,
        agent_id,
        plan_id,
    )


# ============================================================
# SETTLEMENT HELPER
# ============================================================

def create_settlement(
    token,
    claim_id,
    approved_amount=40000,
    payment_reference=None,
    settlement_status="Pending",
):
    if payment_reference is None:
        payment_reference = (
            f"PAY-{uuid4().hex[:10].upper()}"
        )

    return client.post(
        f"/api/v1/settlements/claims/{claim_id}/settle",
        headers=get_auth_header(token),
        json={
            "approved_amount": approved_amount,
            "payment_reference": payment_reference,
            "settlement_status": settlement_status,
        },
    )


# ============================================================
# CREATE SETTLEMENT
# ============================================================

def test_create_settlement():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
        settlement_status="Pending",
    )

    assert response.status_code == 201, (
        f"Settlement creation failed: "
        f"{response.text}"
    )

    data = response.json()

    assert data["claim_id"] == claim_id
    assert float(data["approved_amount"]) == 40000
    assert data["settlement_status"] == "Pending"
    assert "payment_reference" in data
    assert "settlement_date" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "id" in data


# ============================================================
# SETTLEMENT STATUSES
# ============================================================

def test_create_processing_settlement():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=30000,
        settlement_status="Processing",
    )

    assert response.status_code == 201

    assert response.json()["settlement_status"] == (
        "Processing"
    )


def test_create_completed_settlement():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
        settlement_status="Completed",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["settlement_status"] == "Completed"


def test_create_failed_settlement():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
        settlement_status="Failed",
    )

    assert response.status_code == 201

    assert response.json()["settlement_status"] == "Failed"


# ============================================================
# INVALID SETTLEMENT STATUS
# ============================================================

def test_invalid_settlement_status():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
        settlement_status="Invalid Status",
    )

    assert response.status_code == 400

    assert "invalid settlement status" in (
        response.json()["detail"].lower()
    )


# ============================================================
# CLAIM NOT FOUND
# ============================================================

def test_create_settlement_claim_not_found():
    finance_token = create_finance_officer()

    response = create_settlement(
        finance_token,
        999999,
        approved_amount=40000,
    )

    assert response.status_code == 404

    assert "claim not found" in (
        response.json()["detail"].lower()
    )


# ============================================================
# CLAIM STATUS VALIDATION
# ============================================================

def test_settlement_requires_approved_claim():
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
        status="Under Review",
    )

    finance_token = create_finance_officer()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
    )

    assert response.status_code == 400

    assert "approved" in (
        response.json()["detail"].lower()
    )


def test_settlement_not_allowed_for_rejected_claim():
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

    finance_token = create_finance_officer()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
    )

    assert response.status_code == 400

    assert "approved" in (
        response.json()["detail"].lower()
    )


# ============================================================
# ASSESSMENT VALIDATION
# ============================================================

def test_settlement_requires_assessment():
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

    finance_token = create_finance_officer()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
    )

    assert response.status_code == 404

    assert "assessment not found" in (
        response.json()["detail"].lower()
    )


# ============================================================
# APPROVED AMOUNT VALIDATION
# ============================================================

def test_settlement_amount_cannot_be_zero():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=0,
    )

    assert response.status_code == 422


def test_settlement_amount_cannot_be_negative():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=-1000,
    )

    assert response.status_code == 422


def test_settlement_amount_cannot_exceed_claim_amount():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data(
        claim_amount=50000,
        eligible_amount=50000,
    )

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=60000,
    )

    assert response.status_code == 400

    assert "claim amount" in (
        response.json()["detail"].lower()
    )


def test_settlement_amount_cannot_exceed_eligible_amount():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data(
        claim_amount=50000,
        eligible_amount=40000,
    )

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=45000,
    )

    assert response.status_code == 400

    assert "approved claim amount" in (
        response.json()["detail"].lower()
    )


def test_settlement_amount_within_allowed_amount():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data(
        claim_amount=50000,
        eligible_amount=40000,
    )

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=35000,
    )

    assert response.status_code == 201

    data = response.json()

    assert float(data["approved_amount"]) == 35000


# ============================================================
# DUPLICATE SETTLEMENT
# ============================================================

def test_duplicate_settlement_not_allowed():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    first = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
    )

    assert first.status_code == 201

    second = create_settlement(
        finance_token,
        claim_id,
        approved_amount=30000,
    )

    assert second.status_code == 400

    assert "already been settled" in (
        second.json()["detail"].lower()
    )


# ============================================================
# DUPLICATE PAYMENT REFERENCE
# ============================================================

def test_duplicate_payment_reference_not_allowed():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    payment_reference = (
        f"PAY-{uuid4().hex[:10].upper()}"
    )

    first = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
        payment_reference=payment_reference,
    )

    assert first.status_code == 201

    (
        claim_id_2,
        finance_token_2,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    second = create_settlement(
        finance_token_2,
        claim_id_2,
        approved_amount=30000,
        payment_reference=payment_reference,
    )

    assert second.status_code == 400

    assert "payment reference already exists" in (
        second.json()["detail"].lower()
    )


# ============================================================
# PAYMENT REFERENCE VALIDATION
# ============================================================

def test_payment_reference_too_short():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
        payment_reference="AB",
    )

    assert response.status_code == 422


def test_payment_reference_required():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = client.post(
        f"/api/v1/settlements/claims/{claim_id}/settle",
        headers=get_auth_header(finance_token),
        json={
            "approved_amount": 40000,
            "settlement_status": "Pending",
        },
    )

    assert response.status_code == 422


# ============================================================
# COMPLETED SETTLEMENT CLAIM STATUS
# ============================================================

def test_completed_settlement_marks_claim_settled():
    (
        claim_id,
        finance_token,
        agent_token,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
        settlement_status="Completed",
    )

    assert response.status_code == 201

    claim_response = client.get(
        f"/api/v1/claims/{claim_id}",
        headers=get_auth_header(agent_token),
    )

    assert claim_response.status_code == 200

    claim_data = claim_response.json()

    assert claim_data["status"] == "Settled"


def test_pending_settlement_does_not_settle_claim():
    (
        claim_id,
        finance_token,
        agent_token,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
        settlement_status="Pending",
    )

    assert response.status_code == 201

    claim_response = client.get(
        f"/api/v1/claims/{claim_id}",
        headers=get_auth_header(agent_token),
    )

    assert claim_response.status_code == 200

    assert claim_response.json()["status"] == "Approved"


# ============================================================
# GET ALL SETTLEMENTS
# ============================================================

def test_get_all_settlements():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    create_response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/settlements",
        headers=get_auth_header(finance_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == (
        "Settlements retrieved successfully"
    )
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1


# ============================================================
# GET SINGLE SETTLEMENT
# ============================================================

def test_get_settlement():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    create_response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
    )

    assert create_response.status_code == 201

    settlement_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/settlements/{settlement_id}",
        headers=get_auth_header(finance_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == settlement_id
    assert data["claim_id"] == claim_id
    assert float(data["approved_amount"]) == 40000


def test_get_settlement_not_found():
    finance_token = create_finance_officer()

    response = client.get(
        "/api/v1/settlements/999999",
        headers=get_auth_header(finance_token),
    )

    assert response.status_code == 404

    assert "settlement not found" in (
        response.json()["detail"].lower()
    )


# ============================================================
# AUTHENTICATION
# ============================================================

def test_create_settlement_without_token():
    (
        claim_id,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = client.post(
        f"/api/v1/settlements/claims/{claim_id}/settle",
        json={
            "approved_amount": 40000,
            "payment_reference": (
                f"PAY-{uuid4().hex[:10].upper()}"
            ),
            "settlement_status": "Pending",
        },
    )

    assert response.status_code == 401


def test_get_settlements_without_token():
    response = client.get(
        "/api/v1/settlements",
    )

    assert response.status_code == 401


def test_get_settlement_without_token():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    create_response = create_settlement(
        finance_token,
        claim_id,
    )

    assert create_response.status_code == 201

    settlement_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/settlements/{settlement_id}",
    )

    assert response.status_code == 401


# ============================================================
# ROLE AUTHORIZATION - CREATE
# ============================================================

def test_finance_officer_can_create_settlement():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        finance_token,
        claim_id,
        approved_amount=40000,
    )

    assert response.status_code == 201


def test_super_admin_can_create_settlement():
    (
        claim_id,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    super_admin_token = create_super_admin()

    response = create_settlement(
        super_admin_token,
        claim_id,
        approved_amount=40000,
    )

    assert response.status_code == 201


def test_claims_officer_cannot_create_settlement():
    (
        claim_id,
        _,
        _,
        _,
        claims_officer_token,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        claims_officer_token,
        claim_id,
        approved_amount=40000,
    )

    assert response.status_code == 403


def test_agent_cannot_create_settlement():
    (
        claim_id,
        _,
        agent_token,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        agent_token,
        claim_id,
        approved_amount=40000,
    )

    assert response.status_code == 403


def test_customer_cannot_create_settlement():
    (
        claim_id,
        _,
        _,
        customer_token,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    response = create_settlement(
        customer_token,
        claim_id,
        approved_amount=40000,
    )

    assert response.status_code == 403


# ============================================================
# ROLE AUTHORIZATION - GET ALL
# ============================================================

def test_super_admin_can_get_settlements():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    create_response = create_settlement(
        finance_token,
        claim_id,
    )

    assert create_response.status_code == 201

    super_admin_token = create_super_admin()

    response = client.get(
        "/api/v1/settlements",
        headers=get_auth_header(super_admin_token),
    )

    assert response.status_code == 200


def test_finance_officer_can_get_settlements():
    (
        claim_id,
        finance_token,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    create_response = create_settlement(
        finance_token,
        claim_id,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/settlements",
        headers=get_auth_header(finance_token),
    )

    assert response.status_code == 200


def test_claims_officer_can_get_settlements():
    (
        claim_id,
        finance_token,
        _,
        _,
        claims_officer_token,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    create_response = create_settlement(
        finance_token,
        claim_id,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/settlements",
        headers=get_auth_header(claims_officer_token),
    )

    assert response.status_code == 200


def test_agent_can_get_settlements():
    (
        claim_id,
        finance_token,
        agent_token,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    create_response = create_settlement(
        finance_token,
        claim_id,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/settlements",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200


def test_customer_can_get_settlements():
    (
        claim_id,
        finance_token,
        _,
        customer_token,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    create_response = create_settlement(
        finance_token,
        claim_id,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/settlements",
        headers=get_auth_header(customer_token),
    )

    assert response.status_code == 200


# ============================================================
# ROLE AUTHORIZATION - GET SINGLE
# ============================================================

def test_customer_can_get_single_settlement():
    (
        claim_id,
        finance_token,
        _,
        customer_token,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    create_response = create_settlement(
        finance_token,
        claim_id,
    )

    assert create_response.status_code == 201

    settlement_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/settlements/{settlement_id}",
        headers=get_auth_header(customer_token),
    )

    assert response.status_code == 200


def test_agent_can_get_single_settlement():
    (
        claim_id,
        finance_token,
        agent_token,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    create_response = create_settlement(
        finance_token,
        claim_id,
    )

    assert create_response.status_code == 201

    settlement_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/settlements/{settlement_id}",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200


def test_claims_officer_can_get_single_settlement():
    (
        claim_id,
        finance_token,
        _,
        _,
        claims_officer_token,
        _,
        _,
        _,
        _,
    ) = create_approved_claim_test_data()

    create_response = create_settlement(
        finance_token,
        claim_id,
    )

    assert create_response.status_code == 201

    settlement_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/settlements/{settlement_id}",
        headers=get_auth_header(claims_officer_token),
    )

    assert response.status_code == 200

