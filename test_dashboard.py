
from decimal import Decimal
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
# USER HELPERS
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

    login_response = login_user(
        email,
        "Test@12345",
    )

    assert login_response.status_code == 200, (
        f"Agent login failed: "
        f"{login_response.text}"
    )

    data = register_response.json()

    if isinstance(data, dict):
        data = data.get("data", data)

    return (
        data["id"],
        login_response.json()["access_token"],
    )


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

    _, agent_token = create_agent()

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

    data = customer_response.json()

    if isinstance(data, dict):
        data = data.get("data", data)

    return (
        data["id"],
        customer_token,
        agent_token,
    )


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
        data = data.get("data", data)

    return data["id"]


# ============================================================
# POLICY HELPER
# ============================================================

def create_policy(
    policy_status="Active",
    start_date=None,
    end_date=None,
):
    customer_id, customer_token, _ = create_customer()

    agent_id, agent_token = create_agent()

    plan_id = create_plan(agent_token)

    if start_date is None:
        start_date = date.today() - timedelta(days=30)

    if end_date is None:
        end_date = date.today() + timedelta(days=335)

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
        data = data.get("data", data)

    return {
        "policy_id": data["id"],
        "customer_id": customer_id,
        "agent_id": agent_id,
        "plan_id": plan_id,
        "agent_token": agent_token,
        "customer_token": customer_token,
    }




# ============================================================
# PREMIUM PAYMENT HELPER
# ============================================================

def create_payment(
    policy_id,
    customer_id,
    agent_token,
    amount=50000,
    payment_status="Completed",
):
    response = client.post(
        f"/api/v1/payments/policy/{policy_id}",
        headers=get_auth_header(agent_token),
        json={
            "customer_id": customer_id,
            "amount": amount,
            "payment_date": date.today().isoformat(),
            "payment_method": "UPI",
            "transaction_id": (
                f"TXN-{uuid4().hex[:10].upper()}"
            ),
            "payment_status": payment_status,
            "premium_due_date": (
                date.today() + timedelta(days=30)
            ).isoformat(),
        },
    )

    assert response.status_code == 201, (
        f"Payment creation failed: "
        f"{response.text}"
    )

    return response


# ============================================================
# CLAIM HELPER
# ============================================================

def create_claim(
    policy_id,
    customer_id,
    agent_token,
    claim_amount=50000,
    status="Under Review",
):
    response = client.post(
        "/api/v1/claims",
        headers=get_auth_header(agent_token),
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
        data = data.get("data", data)

    return data["id"]


# ============================================================
# DASHBOARD
# ============================================================

def test_get_dashboard():
    policy = create_policy()

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200, (
        f"Dashboard request failed: "
        f"{response.text}"
    )

    body = response.json()

    assert body["success"] is True
    assert "message" in body
    assert "data" in body
    assert isinstance(body["data"], dict)


def test_dashboard_requires_authentication():
    response = client.get(
        "/api/v1/dashboard",
    )

    assert response.status_code == 401


def test_dashboard_contains_customer_count():
    create_policy()

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200

    body = response.json()
    data = body["data"]

    assert "total_customers" in data
    assert data["total_customers"] >= 1


def test_dashboard_contains_policy_counts():
    create_policy()

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200

    body = response.json()
    data = body["data"]

    assert "active_policies" in data
    assert "expired_policies" in data

    assert data["active_policies"] >= 1
    assert data["expired_policies"] >= 0


def test_dashboard_contains_claim_counts():
    policy = create_policy()

    create_claim(
        policy["policy_id"],
        policy["customer_id"],
        policy["agent_token"],
        status="Under Review",
    )

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200

    body = response.json()
    data = body["data"]

    assert "total_claims" in data
    assert "approved_claims" in data
    assert "rejected_claims" in data
    assert "pending_claims" in data

    assert data["total_claims"] >= 1
    assert data["approved_claims"] >= 0
    assert data["rejected_claims"] >= 0
    assert data["pending_claims"] >= 0


def test_dashboard_contains_premium_values():
    policy = create_policy()

    create_payment(
        policy["policy_id"],
        policy["customer_id"],
        policy["agent_token"],
        amount=50000,
        payment_status="Completed",
    )

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200

    body = response.json()
    data = body["data"]

    assert "total_premium_collected" in data
    assert "pending_premium" in data

    assert Decimal(str(data["total_premium_collected"])) >= 0
    assert Decimal(str(data["pending_premium"])) >= 0


def test_dashboard_contains_settlement_amount():
    create_policy()

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200

    body = response.json()
    data = body["data"]

    assert "total_settlement_amount" in data

    assert Decimal(
        str(data["total_settlement_amount"])
    ) >= 0


# ============================================================
# REPORTS - AUTHENTICATION
# ============================================================

def test_policy_premium_report_requires_authentication():
    response = client.get(
        "/api/v1/reports/policy-premium"
    )

    assert response.status_code == 401


def test_customer_policy_history_requires_authentication():
    response = client.get(
        "/api/v1/reports/customer-policy-history"
    )

    assert response.status_code == 401


def test_claim_settlement_report_requires_authentication():
    response = client.get(
        "/api/v1/reports/claim-settlement"
    )

    assert response.status_code == 401


def test_agent_performance_report_requires_authentication():
    response = client.get(
        "/api/v1/reports/agent-performance"
    )

    assert response.status_code == 401


def test_monthly_premium_report_requires_authentication():
    response = client.get(
        "/api/v1/reports/monthly-premium"
    )

    assert response.status_code == 401


def test_monthly_claim_report_requires_authentication():
    response = client.get(
        "/api/v1/reports/monthly-claims"
    )

    assert response.status_code == 401


# ============================================================
# POLICY PREMIUM REPORT
# ============================================================

def test_policy_premium_report():
    policy = create_policy()

    create_payment(
        policy["policy_id"],
        policy["customer_id"],
        policy["agent_token"],
        amount=50000,
        payment_status="Completed",
    )

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/reports/policy-premium",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200, (
        f"Policy premium report failed: "
        f"{response.text}"
    )

    body = response.json()

    assert body["success"] is True
    assert "data" in body
    assert isinstance(body["data"], list)


# ============================================================
# CUSTOMER POLICY HISTORY
# ============================================================

def test_customer_policy_history():
    policy = create_policy()

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/reports/customer-policy-history",
        headers=get_auth_header(admin_token),
        params={
            "customer_id": policy["customer_id"],
        },
    )

    assert response.status_code == 200, (
        f"Customer policy history failed: "
        f"{response.text}"
    )

    body = response.json()

    assert body["success"] is True
    assert "data" in body
    assert isinstance(body["data"], list)


# ============================================================
# CLAIM SETTLEMENT REPORT
# ============================================================

def test_claim_settlement_report():
    policy = create_policy()

    create_claim(
        policy["policy_id"],
        policy["customer_id"],
        policy["agent_token"],
        claim_amount=50000,
        status="Approved",
    )

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/reports/claim-settlement",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200, (
        f"Claim settlement report failed: "
        f"{response.text}"
    )

    body = response.json()

    assert body["success"] is True
    assert "data" in body
    assert isinstance(body["data"], list)


# ============================================================
# AGENT PERFORMANCE REPORT
# ============================================================

def test_agent_performance_report():
    create_policy()

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/reports/agent-performance",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200, (
        f"Agent performance report failed: "
        f"{response.text}"
    )

    body = response.json()

    assert body["success"] is True
    assert "data" in body
    assert isinstance(body["data"], list)


# ============================================================
# MONTHLY PREMIUM REPORT
# ============================================================

def test_monthly_premium_report():
    policy = create_policy()

    create_payment(
        policy["policy_id"],
        policy["customer_id"],
        policy["agent_token"],
        amount=50000,
        payment_status="Completed",
    )

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/reports/monthly-premium",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200, (
        f"Monthly premium report failed: "
        f"{response.text}"
    )

    body = response.json()

    assert body["success"] is True
    assert "data" in body
    assert isinstance(body["data"], list)


# ============================================================
# MONTHLY CLAIM REPORT
# ============================================================

def test_monthly_claim_report():
    policy = create_policy()

    create_claim(
        policy["policy_id"],
        policy["customer_id"],
        policy["agent_token"],
        claim_amount=50000,
        status="Under Review",
    )

    admin_token = create_super_admin()

    response = client.get(
        "/api/v1/reports/monthly-claims",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200, (
        f"Monthly claim report failed: "
        f"{response.text}"
    )

    body = response.json()

    assert body["success"] is True
    assert "data" in body
    assert isinstance(body["data"], list)


# ============================================================
# SUPER ADMIN ACCESS
# ============================================================

def test_super_admin_can_get_dashboard():
    token = create_super_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200


def test_super_admin_can_get_policy_premium_report():
    token = create_super_admin()

    response = client.get(
        "/api/v1/reports/policy-premium",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200


def test_super_admin_can_get_customer_policy_history():
    token = create_super_admin()

    response = client.get(
        "/api/v1/reports/customer-policy-history",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200


def test_super_admin_can_get_claim_settlement_report():
    token = create_super_admin()

    response = client.get(
        "/api/v1/reports/claim-settlement",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200


def test_super_admin_can_get_agent_performance_report():
    token = create_super_admin()

    response = client.get(
        "/api/v1/reports/agent-performance",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200


def test_super_admin_can_get_monthly_premium_report():
    token = create_super_admin()

    response = client.get(
        "/api/v1/reports/monthly-premium",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200


def test_super_admin_can_get_monthly_claim_report():
    token = create_super_admin()

    response = client.get(
        "/api/v1/reports/monthly-claims",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200

