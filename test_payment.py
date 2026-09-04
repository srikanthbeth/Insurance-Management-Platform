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
# COMMON HELPERS
# ============================================================

def unique_email(prefix="user"):
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def unique_id(prefix="ID"):
    return f"{prefix}-{uuid4().hex[:10].upper()}"


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

    customer_login = login_user(
        email,
        "Test@12345",
    )

    assert customer_login.status_code == 200, (
        f"Customer login failed: "
        f"{customer_login.text}"
    )

    customer_token = customer_login.json()["access_token"]

    # Create Agent
    agent_email = unique_email("agent")

    agent_register = register_user(
        full_name="Test Insurance Agent",
        role="Insurance Agent",
        email=agent_email,
    )

    assert agent_register.status_code == 201, (
        f"Agent registration failed: "
        f"{agent_register.text}"
    )

    agent_login = login_user(
        agent_email,
        "Test@12345",
    )

    assert agent_login.status_code == 200, (
        f"Agent login failed: "
        f"{agent_login.text}"
    )

    agent_token = agent_login.json()["access_token"]

    # Create Customer Profile
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
    email = unique_email("finance")

    register_response = register_user(
        full_name="Test Finance Officer",
        role="Finance Officer",
        email=email,
    )

    assert register_response.status_code == 201, (
        f"Finance Officer registration failed: "
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
        f"Finance Officer login failed: "
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
# POLICY TEST DATA
# ============================================================

def create_policy_test_data():
    customer_id, customer_token = create_customer()

    agent_id, agent_token = create_agent()

    plan_id = create_plan(agent_token)

    premium_amount = 50000

    policy_payload = {
        "policy_number": (
            f"POL-{uuid4().hex[:8].upper()}"
        ),
        "customer_id": customer_id,
        "plan_id": plan_id,
        "agent_id": agent_id,
        "start_date": date.today().isoformat(),
        "end_date": (
            date.today() + timedelta(days=365)
        ).isoformat(),
        "coverage_amount": 1000000,
        "premium_amount": premium_amount,
        "policy_status": "Pending",
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
        premium_amount,
    )


# ============================================================
# PAYMENT HELPER
# ============================================================

def create_payment(
    token,
    policy_id,
    customer_id,
    amount=50000,
    payment_method="UPI",
    transaction_id=None,
    payment_status="Completed",
    payment_date=None,
    premium_due_date=None,
):
    if transaction_id is None:
        transaction_id = (
            f"TXN-{uuid4().hex[:12].upper()}"
        )

    if payment_date is None:
        payment_date = date.today().isoformat()

    if premium_due_date is None:
        premium_due_date = (
            date.today() + timedelta(days=30)
        ).isoformat()

    return client.post(
        f"/api/v1/payments/policy/{policy_id}",
        headers=get_auth_header(token),
        json={
            "customer_id": customer_id,
            "amount": amount,
            "payment_date": payment_date,
            "payment_method": payment_method,
            "transaction_id": transaction_id,
            "payment_status": payment_status,
            "premium_due_date": premium_due_date,
        },
    )


# ============================================================
# CREATE PAYMENT TESTS
# ============================================================

def test_create_premium_payment():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert response.status_code == 201, (
        f"Payment creation failed: "
        f"{response.text}"
    )

    data = response.json()

    assert data["policy_id"] == policy_id
    assert data["customer_id"] == customer_id
    assert float(data["amount"]) == premium_amount
    assert data["payment_method"] == "UPI"
    assert data["payment_status"] == "Completed"
    assert "transaction_id" in data


def test_payment_using_card():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
        payment_method="Card",
    )

    assert response.status_code == 201
    assert response.json()["payment_method"] == "Card"


def test_payment_using_net_banking():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
        payment_method="Net Banking",
    )

    assert response.status_code == 201
    assert response.json()["payment_method"] == "Net Banking"


def test_payment_using_auto_debit():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
        payment_method="Auto Debit",
    )

    assert response.status_code == 201
    assert response.json()["payment_method"] == "Auto Debit"


# ============================================================
# PAYMENT VALIDATION
# ============================================================

def test_duplicate_transaction_not_allowed():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    transaction_id = (
        f"TXN-{uuid4().hex[:12].upper()}"
    )

    first = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
        transaction_id=transaction_id,
    )

    assert first.status_code == 201

    second = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
        transaction_id=transaction_id,
    )

    assert second.status_code in [400, 409]

    assert "duplicate" in (
        second.json()["detail"].lower()
    )


def test_payment_amount_must_match_premium():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount - 1000,
    )

    assert response.status_code == 400

    assert "amount" in (
        response.json()["detail"].lower()
    )


def test_zero_payment_amount_not_allowed():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=0,
    )

    assert response.status_code == 422


def test_negative_payment_amount_not_allowed():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=-5000,
    )

    assert response.status_code == 422
def test_invalid_payment_method():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
        payment_method="Cash",
    )

    assert response.status_code == 422

    data = response.json()

    assert data["success"] is False
    assert data["message"] == "Request validation failed"
    assert "errors" in data

    assert any(
        "Invalid payment method" in error["message"]
        for error in data["errors"]
    )

def test_invalid_payment_status():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
        payment_status="Success",
    )

    assert response.status_code == 422

    data = response.json()

    assert data["success"] is False
    assert data["message"] == "Request validation failed"
    assert "errors" in data

    assert any(
        "Invalid payment status" in error["message"]
        for error in data["errors"]
    )


# ============================================================
# FAILED PAYMENT
# ============================================================

def test_failed_payment_does_not_activate_policy():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
        payment_status="Failed",
    )

    assert response.status_code == 201

    payment_data = response.json()

    assert payment_data["payment_status"] == "Failed"

    policy_response = client.get(
        f"/api/v1/policies/{policy_id}",
        headers=get_auth_header(agent_token),
    )

    assert policy_response.status_code == 200

    policy_data = policy_response.json()

    assert policy_data["policy_status"] != "Active"


# ============================================================
# POLICY NOT FOUND
# ============================================================

def test_payment_policy_not_found():
    (
        _,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        999999,
        customer_id,
        amount=premium_amount,
    )

    assert response.status_code == 404


def test_get_policy_payments_not_found():
    _, agent_token, _, _, _, _, _ = (
        create_policy_test_data()
    )

    response = client.get(
        "/api/v1/payments/policy/999999",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404


# ============================================================
# GET ALL PAYMENTS
# ============================================================

def test_get_all_premium_payments():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    create_response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/payments",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == (
        "Premium payments retrieved successfully"
    )
    assert isinstance(data["data"], list)
    assert data["total"] >= 1
    assert data["page"] == 1
    assert data["limit"] == 10


def test_get_premium_payment():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    create_response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/payments/{payment_id}",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["policy_id"] == policy_id
    assert data["customer_id"] == customer_id


def test_get_premium_payment_not_found():
    _, agent_token, _, _, _, _, _ = (
        create_policy_test_data()
    )

    response = client.get(
        "/api/v1/payments/999999",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404


# ============================================================
# GET POLICY PAYMENTS
# ============================================================

def test_get_policy_premium_payments():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    first = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert first.status_code == 201

    response = client.get(
        f"/api/v1/payments/policy/{policy_id}",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert any(
        item["policy_id"] == policy_id
        for item in data
    )


# ============================================================
# GET CUSTOMER PAYMENTS
# ============================================================

def test_get_customer_premium_payments():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    create_response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/api/v1/payments/customer/{customer_id}",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert all(
        item["customer_id"] == customer_id
        for item in data
    )


def test_get_customer_payments_customer_not_found():
    _, agent_token, _, _, _, _, _ = (
        create_policy_test_data()
    )

    response = client.get(
        "/api/v1/payments/customer/999999",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404


# ============================================================
# UPDATE PAYMENT
# ============================================================

def test_update_premium_payment():
    (
        policy_id,
        _,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    _, finance_token = create_finance_officer()

    create_response = create_payment(
        finance_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/payments/{payment_id}",
        headers=get_auth_header(finance_token),
        json={
            "payment_method": "Card",
            "payment_status": "Refunded",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["payment_method"] == "Card"
    assert data["payment_status"] == "Refunded"


def test_update_premium_payment_not_found():
    _, _, _, _, _, _, _ = (
        create_policy_test_data()
    )

    _, finance_token = create_finance_officer()

    response = client.put(
        "/api/v1/payments/999999",
        headers=get_auth_header(finance_token),
        json={
            "payment_method": "Card",
            "payment_status": "Refunded",
        },
    )

    assert response.status_code == 404


# ============================================================
# DELETE PAYMENT
# ============================================================

def test_delete_premium_payment():
    (
        policy_id,
        _,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    _, finance_token = create_finance_officer()

    create_response = create_payment(
        finance_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/payments/{payment_id}",
        headers=get_auth_header(finance_token),
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/payments/{payment_id}",
        headers=get_auth_header(finance_token),
    )

    assert get_response.status_code == 404


def test_delete_premium_payment_not_found():
    _, _, _, _, _, _, _ = (
        create_policy_test_data()
    )

    _, finance_token = create_finance_officer()

    response = client.delete(
        "/api/v1/payments/999999",
        headers=get_auth_header(finance_token),
    )

    assert response.status_code == 404


# ============================================================
# AUTHENTICATION TESTS
# ============================================================

def test_create_payment_without_token():
    (
        policy_id,
        _,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = client.post(
        f"/api/v1/payments/policy/{policy_id}",
        json={
            "customer_id": customer_id,
            "amount": premium_amount,
            "payment_date": date.today().isoformat(),
            "payment_method": "UPI",
            "transaction_id": unique_id("TXN"),
            "payment_status": "Completed",
            "premium_due_date": (
                date.today() + timedelta(days=30)
            ).isoformat(),
        },
    )

    assert response.status_code == 401


def test_get_payments_without_token():
    response = client.get(
        "/api/v1/payments"
    )

    assert response.status_code == 401


def test_get_payment_without_token():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    create_response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/payments/{payment_id}"
    )

    assert response.status_code == 401


def test_get_policy_payments_without_token():
    (
        policy_id,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = client.get(
        f"/api/v1/payments/policy/{policy_id}"
    )

    assert response.status_code == 401


def test_get_customer_payments_without_token():
    (
        _,
        _,
        _,
        customer_id,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = client.get(
        f"/api/v1/payments/customer/{customer_id}"
    )

    assert response.status_code == 401


def test_update_payment_without_token():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    _, finance_token = create_finance_officer()

    create_response = create_payment(
        finance_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/payments/{payment_id}",
        json={
            "payment_method": "Card",
            "payment_status": "Refunded",
        },
    )

    assert response.status_code == 401


def test_delete_payment_without_token():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    _, finance_token = create_finance_officer()

    create_response = create_payment(
        finance_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/payments/{payment_id}"
    )

    assert response.status_code == 401


# ============================================================
# ROLE AUTHORIZATION TESTS
# ============================================================

def test_agent_cannot_update_payment():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    _, finance_token = create_finance_officer()

    create_response = create_payment(
        finance_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/payments/{payment_id}",
        headers=get_auth_header(agent_token),
        json={
            "payment_method": "Card",
            "payment_status": "Refunded",
        },
    )

    assert response.status_code == 403


def test_agent_cannot_delete_payment():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    _, finance_token = create_finance_officer()

    create_response = create_payment(
        finance_token,
        policy_id,
        customer_id,
        amount=premium_amount,
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/payments/{payment_id}",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 403

    
# ============================================================
# LEVEL 12
# PAYMENT FILTERING / PAGINATION / SORTING
# ============================================================

def test_filter_payments_by_status():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
        payment_status="Completed",
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/payments",
        params={
            "payment_status": "Completed",
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["total"] >= 1

    for payment in data["data"]:
        assert payment["payment_status"] == "Completed"


def test_filter_payments_by_method():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
        payment_method="Card",
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/payments",
        params={
            "payment_method": "Card",
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["total"] >= 1

    for payment in data["data"]:
        assert payment["payment_method"] == "Card"


def test_filter_payments_by_date_range():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    payment_date = (
        date.today() - timedelta(days=5)
    ).isoformat()

    response = create_payment(
        agent_token,
        policy_id,
        customer_id,
        amount=premium_amount,
        payment_date=payment_date,
    )

    assert response.status_code == 201

    date_from = (
        date.today() - timedelta(days=10)
    ).isoformat()

    date_to = date.today().isoformat()

    response = client.get(
        "/api/v1/payments",
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

    for payment in data["data"]:
        payment_date_value = date.fromisoformat(
            payment["payment_date"]
        )

        assert payment_date_value >= date.fromisoformat(
            date_from
        )

        assert payment_date_value <= date.fromisoformat(
            date_to
        )


def test_payment_pagination():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    for index in range(3):
        payment_date = (
            date.today()
            - timedelta(days=index)
        ).isoformat()

        response = create_payment(
            agent_token,
            policy_id,
            customer_id,
            amount=premium_amount,
            payment_date=payment_date,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/payments",
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


def test_payment_pagination_second_page():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    for index in range(3):
        payment_date = (
            date.today()
            - timedelta(days=index)
        ).isoformat()

        response = create_payment(
            agent_token,
            policy_id,
            customer_id,
            amount=premium_amount,
            payment_date=payment_date,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/payments",
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


def test_sort_payments_by_amount_ascending():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        _,
    ) = create_policy_test_data()

    amounts = [
        50000,
        50000,
        50000,
    ]

    for index, amount in enumerate(amounts):
        payment_date = (
            date.today()
            - timedelta(days=index)
        ).isoformat()

        response = create_payment(
            agent_token,
            policy_id,
            customer_id,
            amount=amount,
            payment_date=payment_date,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/payments",
        params={
            "sort_by": "amount",
            "sort_order": "asc",
            "limit": 100,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    amounts = [
        float(payment["amount"])
        for payment in data["data"]
    ]

    assert amounts == sorted(amounts)


def test_sort_payments_by_amount_descending():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        _,
    ) = create_policy_test_data()

    # Premium amount must match the policy premium,
    # so all payments have the same amount.
    for index in range(3):
        payment_date = (
            date.today()
            - timedelta(days=index)
        ).isoformat()

        response = create_payment(
            agent_token,
            policy_id,
            customer_id,
            amount=50000,
            payment_date=payment_date,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/payments",
        params={
            "sort_by": "amount",
            "sort_order": "desc",
            "limit": 100,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    amounts = [
        float(payment["amount"])
        for payment in data["data"]
    ]

    assert amounts == sorted(
        amounts,
        reverse=True,
    )


def test_sort_payments_by_date_ascending():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    dates = [
        date.today() - timedelta(days=1),
        date.today() - timedelta(days=10),
        date.today() - timedelta(days=5),
    ]

    for payment_date in dates:
        response = create_payment(
            agent_token,
            policy_id,
            customer_id,
            amount=premium_amount,
            payment_date=payment_date.isoformat(),
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/payments",
        params={
            "sort_by": "payment_date",
            "sort_order": "asc",
            "limit": 100,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    result_dates = [
        date.fromisoformat(
            payment["payment_date"]
        )
        for payment in data["data"]
    ]

    assert result_dates == sorted(result_dates)


def test_sort_payments_by_date_descending():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        premium_amount,
    ) = create_policy_test_data()

    dates = [
        date.today() - timedelta(days=2),
        date.today() - timedelta(days=8),
        date.today() - timedelta(days=4),
    ]

    for payment_date in dates:
        response = create_payment(
            agent_token,
            policy_id,
            customer_id,
            amount=premium_amount,
            payment_date=payment_date.isoformat(),
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/payments",
        params={
            "sort_by": "payment_date",
            "sort_order": "desc",
            "limit": 100,
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    result_dates = [
        date.fromisoformat(
            payment["payment_date"]
        )
        for payment in data["data"]
    ]

    assert result_dates == sorted(
        result_dates,
        reverse=True,
    )


def test_invalid_payment_sort_field():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = client.get(
        "/api/v1/payments",
        params={
            "sort_by": "invalid_field",
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 400

    assert "invalid sort field" in (
        response.json()["detail"].lower()
    )


def test_invalid_payment_sort_order():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = client.get(
        "/api/v1/payments",
        params={
            "sort_order": "invalid",
        },
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 400

    assert "invalid sort order" in (
        response.json()["detail"].lower()
    )


def test_invalid_payment_date_range():
    (
        policy_id,
        agent_token,
        _,
        customer_id,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = client.get(
        "/api/v1/payments",
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

