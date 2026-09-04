
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
    """
    Creates:
    1. Auth user with Customer role
    2. Insurance Agent
    3. Customer profile using Agent authorization
    4. Returns customer ID and Customer login token
    """

    email = unique_email("customer")

    # ========================================================
    # REGISTER CUSTOMER AUTH USER
    # ========================================================

    register_response = register_user(
        full_name="Test Customer",
        role="Customer",
        email=email,
    )

    assert register_response.status_code == 201, (
        f"Customer registration failed: "
        f"{register_response.text}"
    )

    # ========================================================
    # LOGIN CUSTOMER
    # ========================================================

    login_response = login_user(
        email,
        "Test@12345",
    )

    assert login_response.status_code == 200, (
        f"Customer login failed: "
        f"{login_response.text}"
    )

    customer_token = login_response.json()["access_token"]

    # ========================================================
    # CREATE INSURANCE AGENT
    # ========================================================

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

    # ========================================================
    # CREATE CUSTOMER PROFILE USING AGENT TOKEN
    # ========================================================

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
    """
    Creates an InsurancePlan using the current PlanCreate schema.
    """

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
    # --------------------------------------------------------
    # Create Customer
    # --------------------------------------------------------

    customer_id, customer_token = create_customer()

    # --------------------------------------------------------
    # Create Insurance Agent
    # --------------------------------------------------------

    agent_id, agent_token = create_agent()

    # --------------------------------------------------------
    # Create Insurance Plan
    # --------------------------------------------------------

    plan_id = create_plan(agent_token)

    # --------------------------------------------------------
    # Create Policy
    # --------------------------------------------------------

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
        "premium_amount": 50000,
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
    )


# ============================================================
# BENEFICIARY HELPER
# ============================================================

def create_beneficiary(
    token,
    policy_id,
    name="Priya Reddy",
    relationship="Spouse",
    percentage=100,
    phone="9876543210",
    identification_number=None,
):
    if identification_number is None:
        identification_number = unique_id("BEN")

    return client.post(
        f"/api/v1/policies/{policy_id}/beneficiaries",
        headers=get_auth_header(token),
        json={
            "name": name,
            "relationship": relationship,
            "percentage": percentage,
            "phone": phone,
            "identification_number": identification_number,
        },
    )


# ============================================================
# CREATE BENEFICIARY TESTS
# ============================================================

def test_create_beneficiary():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = create_beneficiary(
        agent_token,
        policy_id,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["policy_id"] == policy_id
    assert data["name"] == "Priya Reddy"
    assert data["relationship"] == "Spouse"
    assert float(data["percentage"]) == 100
    assert data["phone"] == "9876543210"
    assert "identification_number" in data


def test_create_multiple_beneficiaries():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    first = create_beneficiary(
        agent_token,
        policy_id,
        name="Priya Reddy",
        relationship="Spouse",
        percentage=60,
    )

    assert first.status_code == 201

    second = create_beneficiary(
        agent_token,
        policy_id,
        name="Rahul Reddy",
        relationship="Son",
        percentage=40,
    )

    assert second.status_code == 201


# ============================================================
# BENEFICIARY PERCENTAGE TESTS
# ============================================================

def test_beneficiary_percentage_can_be_less_than_100():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = create_beneficiary(
        agent_token,
        policy_id,
        percentage=60,
    )

    assert response.status_code == 201

    data = response.json()

    assert float(data["percentage"]) == 60


def test_beneficiary_percentage_total_cannot_exceed_100():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    first = create_beneficiary(
        agent_token,
        policy_id,
        name="Priya Reddy",
        relationship="Spouse",
        percentage=60,
    )

    assert first.status_code == 201

    second = create_beneficiary(
        agent_token,
        policy_id,
        name="Rahul Reddy",
        relationship="Son",
        percentage=50,
    )

    assert second.status_code in [400, 422]

    data = second.json()

    assert "detail" in data

    if isinstance(data["detail"], list):
        error_text = " ".join(
            str(error)
            for error in data["detail"]
        ).lower()
    else:
        error_text = str(
            data["detail"]
        ).lower()

    assert "percentage" in error_text


def test_beneficiary_percentage_cannot_exceed_100():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = create_beneficiary(
        agent_token,
        policy_id,
        percentage=101,
    )

    assert response.status_code in [400, 422]

    data = response.json()

    assert "detail" in data


def test_beneficiary_percentage_cannot_exceed_100():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = create_beneficiary(
        agent_token,
        policy_id,
        percentage=101,
    )

    assert response.status_code == 422

    data = response.json()

    assert data["success"] is False
    assert data["message"] == "Request validation failed"
    assert "errors" in data

    assert any(
        "less than or equal to 100" in error["message"]
        or error["type"] == "less_than_equal"
        for error in data["errors"]
    )

def test_beneficiary_percentage_cannot_be_negative():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = create_beneficiary(
        agent_token,
        policy_id,
        percentage=-10,
    )

    assert response.status_code == 422

    data = response.json()

    assert data["success"] is False
    assert data["message"] == "Request validation failed"
    assert "errors" in data

    assert any(
        "greater than 0" in error["message"]
        for error in data["errors"]
    )


# ============================================================
# DUPLICATE BENEFICIARY TEST
# ============================================================

def test_duplicate_beneficiary_not_allowed():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    identification_number = unique_id("BEN")

    first = create_beneficiary(
        agent_token,
        policy_id,
        name="Priya Reddy",
        relationship="Spouse",
        percentage=100,
        identification_number=identification_number,
    )

    assert first.status_code == 201

    second = create_beneficiary(
        agent_token,
        policy_id,
        name="Priya Reddy",
        relationship="Spouse",
        percentage=100,
        identification_number=identification_number,
    )

    assert second.status_code in [400, 409]

    assert "duplicate" in (
        second.json()["detail"].lower()
    )


# ============================================================
# POLICY NOT FOUND
# ============================================================

def test_create_beneficiary_policy_not_found():
    _, agent_token, _, _, _, _ = (
        create_policy_test_data()
    )

    response = create_beneficiary(
        agent_token,
        999999,
    )

    assert response.status_code == 404


def test_get_beneficiaries_policy_not_found():
    _, agent_token, _, _, _, _ = (
        create_policy_test_data()
    )

    response = client.get(
        "/api/v1/policies/999999/beneficiaries",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404


# ============================================================
# GET BENEFICIARIES
# ============================================================

def test_get_policy_beneficiaries():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    first = create_beneficiary(
        agent_token,
        policy_id,
        name="Priya Reddy",
        relationship="Spouse",
        percentage=60,
    )

    assert first.status_code == 201

    second = create_beneficiary(
        agent_token,
        policy_id,
        name="Rahul Reddy",
        relationship="Son",
        percentage=40,
    )

    assert second.status_code == 201

    response = client.get(
        f"/api/v1/policies/{policy_id}/beneficiaries",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    if isinstance(data, dict):
        beneficiaries = data.get(
            "data",
            data.get(
                "beneficiaries",
                [],
            ),
        )
    else:
        beneficiaries = data

    assert len(beneficiaries) == 2

    names = {
        item["name"]
        for item in beneficiaries
    }

    assert "Priya Reddy" in names
    assert "Rahul Reddy" in names


# ============================================================
# UPDATE BENEFICIARY
# ============================================================

def test_update_beneficiary():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_beneficiary(
        agent_token,
        policy_id,
        name="Priya Reddy",
        relationship="Spouse",
        percentage=100,
    )

    assert create_response.status_code == 201

    beneficiary_data = create_response.json()

    beneficiary_id = beneficiary_data["id"]

    response = client.put(
        f"/api/v1/beneficiaries/{beneficiary_id}",
        headers=get_auth_header(agent_token),
        json={
            "name": "Priya Sharma",
            "relationship": "Mother",
            "percentage": 100,
            "phone": "9999999999",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == beneficiary_id
    assert data["name"] == "Priya Sharma"
    assert data["relationship"] == "Mother"
    assert float(data["percentage"]) == 100
    assert data["phone"] == "9999999999"


def test_update_beneficiary_not_found():
    _, agent_token, _, _, _, _ = (
        create_policy_test_data()
    )

    response = client.put(
        "/api/v1/beneficiaries/999999",
        headers=get_auth_header(agent_token),
        json={
            "name": "Updated Name",
            "percentage": 100,
        },
    )

    assert response.status_code == 404


# ============================================================
# DELETE BENEFICIARY
# ============================================================

def test_delete_beneficiary():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_beneficiary(
        agent_token,
        policy_id,
        percentage=100,
    )

    assert create_response.status_code == 201

    beneficiary_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/beneficiaries/{beneficiary_id}",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code in [200, 204]

    get_response = client.get(
        f"/api/v1/policies/{policy_id}/beneficiaries",
        headers=get_auth_header(agent_token),
    )

    assert get_response.status_code == 200


def test_delete_beneficiary_not_found():
    _, agent_token, _, _, _, _ = (
        create_policy_test_data()
    )

    response = client.delete(
        "/api/v1/beneficiaries/999999",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404


# ============================================================
# AUTHENTICATION TESTS
# ============================================================

def test_create_beneficiary_without_token():
    (
        policy_id,
        _,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = client.post(
        f"/api/v1/policies/{policy_id}/beneficiaries",
        json={
            "name": "Priya Reddy",
            "relationship": "Spouse",
            "percentage": 100,
            "phone": "9876543210",
            "identification_number": unique_id("BEN"),
        },
    )

    assert response.status_code == 401


def test_get_beneficiaries_without_token():
    (
        policy_id,
        _,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    response = client.get(
        f"/api/v1/policies/{policy_id}/beneficiaries",
    )

    assert response.status_code == 401


def test_update_beneficiary_without_token():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_beneficiary(
        agent_token,
        policy_id,
    )

    assert create_response.status_code == 201

    beneficiary_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/beneficiaries/{beneficiary_id}",
        json={
            "name": "Updated",
            "percentage": 100,
        },
    )

    assert response.status_code == 401


def test_delete_beneficiary_without_token():
    (
        policy_id,
        agent_token,
        _,
        _,
        _,
        _,
    ) = create_policy_test_data()

    create_response = create_beneficiary(
        agent_token,
        policy_id,
    )

    assert create_response.status_code == 201

    beneficiary_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/beneficiaries/{beneficiary_id}",
    )

    assert response.status_code == 401

