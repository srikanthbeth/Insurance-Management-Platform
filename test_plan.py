import os

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


def setup_module():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def teardown_module():
    Base.metadata.drop_all(bind=test_engine)


# ============================================================
# HELPERS
# ============================================================


def unique_email(prefix: str) -> str:
    import uuid

    return (
        f"{prefix}_{uuid.uuid4().hex[:8]}"
        "@example.com"
    )


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


def login_user(
    email: str,
    password: str,
):
    return client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def get_auth_header(
    access_token: str,
):
    return {
        "Authorization": f"Bearer {access_token}"
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

    token = login_response.json()[
        "access_token"
    ]

    return (
        email,
        password,
        token,
        register_response.json(),
    )


def plan_payload(
    plan_name="Life Secure Plus",
    plan_type="Life",
):
    return {
        "plan_name": plan_name,
        "plan_type": plan_type,
        "description": (
            "Comprehensive insurance coverage"
        ),
        "coverage_amount": 1000000,
        "premium_amount": 25000,
        "duration_years": 10,
        "eligibility_age_min": 18,
        "eligibility_age_max": 60,
    }


def create_plan(
    token: str,
    plan_name="Life Secure Plus",
    plan_type="Life",
):
    return client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=plan_payload(
            plan_name,
            plan_type,
        ),
    )


# ============================================================
# CREATE PLAN TESTS
# ============================================================


def test_create_life_plan():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    response = create_plan(
        token,
        plan_name="Life Secure Plan",
        plan_type="Life",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["plan_name"] == (
        "Life Secure Plan"
    )

    assert data["plan_type"] == "Life"

    assert data["description"] == (
        "Comprehensive insurance coverage"
    )

    assert float(data["coverage_amount"]) == 1000000

    assert float(data["premium_amount"]) == 25000

    assert data["duration_years"] == 10

    assert data["eligibility_age_min"] == 18

    assert data["eligibility_age_max"] == 60

    assert data["status"] == "Active"

    assert "id" in data


def test_create_health_plan():
    _, _, token, _ = create_logged_in_user(
        full_name="Health Agent",
        role="Insurance Agent",
    )

    response = create_plan(
        token,
        plan_name="Health Protect Plus",
        plan_type="Health",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["plan_type"] == "Health"


def test_create_vehicle_plan():
    _, _, token, _ = create_logged_in_user(
        full_name="Vehicle Agent",
        role="Insurance Agent",
    )

    response = create_plan(
        token,
        plan_name="Vehicle Secure",
        plan_type="Vehicle",
    )

    assert response.status_code == 201

    assert response.json()["plan_type"] == (
        "Vehicle"
    )


def test_create_property_plan():
    _, _, token, _ = create_logged_in_user(
        full_name="Property Agent",
        role="Insurance Agent",
    )

    response = create_plan(
        token,
        plan_name="Property Protect",
        plan_type="Property",
    )

    assert response.status_code == 201

    assert response.json()["plan_type"] == (
        "Property"
    )


def test_create_travel_plan():
    _, _, token, _ = create_logged_in_user(
        full_name="Travel Agent",
        role="Insurance Agent",
    )

    response = create_plan(
        token,
        plan_name="Travel Secure",
        plan_type="Travel",
    )

    assert response.status_code == 201

    assert response.json()["plan_type"] == (
        "Travel"
    )


# ============================================================
# DUPLICATE PLAN TEST
# ============================================================


def test_duplicate_plan_name_not_allowed():
    _, _, token, _ = create_logged_in_user(
        full_name="Duplicate Agent",
        role="Insurance Agent",
    )

    first_response = create_plan(
        token,
        plan_name="Duplicate Plan",
        plan_type="Life",
    )

    assert first_response.status_code == 201

    second_response = create_plan(
        token,
        plan_name="Duplicate Plan",
        plan_type="Health",
    )

    assert second_response.status_code == 409

    assert second_response.json()["detail"] == (
        "Plan name already exists"
    )


# ============================================================
# VALIDATION TESTS
# ============================================================


def test_invalid_plan_type():
    _, _, token, _ = create_logged_in_user(
        full_name="Invalid Type Agent",
        role="Insurance Agent",
    )

    payload = plan_payload(
        plan_name="Invalid Type Plan",
    )

    payload["plan_type"] = "Invalid"

    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_zero_coverage_amount():
    _, _, token, _ = create_logged_in_user(
        full_name="Zero Coverage Agent",
        role="Insurance Agent",
    )

    payload = plan_payload(
        plan_name="Zero Coverage Plan",
    )

    payload["coverage_amount"] = 0

    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_negative_coverage_amount():
    _, _, token, _ = create_logged_in_user(
        full_name="Negative Coverage Agent",
        role="Insurance Agent",
    )

    payload = plan_payload(
        plan_name="Negative Coverage Plan",
    )

    payload["coverage_amount"] = -100

    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_zero_premium_amount():
    _, _, token, _ = create_logged_in_user(
        full_name="Zero Premium Agent",
        role="Insurance Agent",
    )

    payload = plan_payload(
        plan_name="Zero Premium Plan",
    )

    payload["premium_amount"] = 0

    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_negative_premium_amount():
    _, _, token, _ = create_logged_in_user(
        full_name="Negative Premium Agent",
        role="Insurance Agent",
    )

    payload = plan_payload(
        plan_name="Negative Premium Plan",
    )

    payload["premium_amount"] = -500

    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_zero_duration_years():
    _, _, token, _ = create_logged_in_user(
        full_name="Zero Duration Agent",
        role="Insurance Agent",
    )

    payload = plan_payload(
        plan_name="Zero Duration Plan",
    )

    payload["duration_years"] = 0

    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_negative_minimum_age():
    _, _, token, _ = create_logged_in_user(
        full_name="Negative Age Agent",
        role="Insurance Agent",
    )

    payload = plan_payload(
        plan_name="Negative Age Plan",
    )

    payload["eligibility_age_min"] = -1

    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_invalid_age_range():
    _, _, token, _ = create_logged_in_user(
        full_name="Age Range Agent",
        role="Insurance Agent",
    )

    payload = plan_payload(
        plan_name="Invalid Age Range Plan",
    )

    payload["eligibility_age_min"] = 60
    payload["eligibility_age_max"] = 18

    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_equal_age_range():
    _, _, token, _ = create_logged_in_user(
        full_name="Equal Age Agent",
        role="Insurance Agent",
    )

    payload = plan_payload(
        plan_name="Equal Age Plan",
    )

    payload["eligibility_age_min"] = 30
    payload["eligibility_age_max"] = 30

    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_missing_plan_name():
    _, _, token, _ = create_logged_in_user(
        full_name="Missing Name Agent",
        role="Insurance Agent",
    )

    payload = plan_payload(
        plan_name="Missing Name Plan",
    )

    del payload["plan_name"]

    response = client.post(
        "/api/v1/plans",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


# ============================================================
# GET ALL PLANS
# ============================================================


def test_get_all_plans():
    _, _, token, _ = create_logged_in_user(
        full_name="List Agent",
        role="Insurance Agent",
    )

    create_plan(
        token,
        plan_name="List Plan One",
        plan_type="Life",
    )

    create_plan(
        token,
        plan_name="List Plan Two",
        plan_type="Health",
    )

    response = client.get(
        "/api/v1/plans",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert "data" in data

    assert "total" in data

    assert len(data["data"]) >= 2


# ============================================================
# GET SINGLE PLAN
# ============================================================


def test_get_plan():
    _, _, token, _ = create_logged_in_user(
        full_name="Get Plan Agent",
        role="Insurance Agent",
    )

    create_response = create_plan(
        token,
        plan_name="Get Single Plan",
        plan_type="Life",
    )

    assert create_response.status_code == 201

    plan_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == plan_id

    assert data["plan_name"] == (
        "Get Single Plan"
    )


def test_get_plan_not_found():
    _, _, token, _ = create_logged_in_user(
        full_name="Not Found Agent",
        role="Insurance Agent",
    )

    response = client.get(
        "/api/v1/plans/999999",
        headers=get_auth_header(token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Plan not found"
    )


# ============================================================
# UPDATE PLAN
# ============================================================


def test_update_plan():
    _, _, token, _ = create_logged_in_user(
        full_name="Update Agent",
        role="Insurance Agent",
    )

    create_response = create_plan(
        token,
        plan_name="Original Plan",
        plan_type="Life",
    )

    assert create_response.status_code == 201

    plan_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        headers=get_auth_header(token),
        json={
            "plan_name": "Updated Life Plan",
            "plan_type": "Health",
            "description": (
                "Updated insurance plan"
            ),
            "coverage_amount": 2000000,
            "premium_amount": 40000,
            "duration_years": 15,
            "eligibility_age_min": 21,
            "eligibility_age_max": 65,
            "status": "Active",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == plan_id

    assert data["plan_name"] == (
        "Updated Life Plan"
    )

    assert data["plan_type"] == "Health"

    assert float(data["coverage_amount"]) == 2000000

    assert float(data["premium_amount"]) == 40000

    assert data["duration_years"] == 15

    assert data["eligibility_age_min"] == 21

    assert data["eligibility_age_max"] == 65


def test_update_plan_status_to_inactive():
    _, _, token, _ = create_logged_in_user(
        full_name="Status Agent",
        role="Insurance Agent",
    )

    create_response = create_plan(
        token,
        plan_name="Status Plan",
        plan_type="Life",
    )

    plan_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        headers=get_auth_header(token),
        json={
            "status": "Inactive"
        },
    )

    assert response.status_code == 200

    assert response.json()["status"] == (
        "Inactive"
    )


def test_update_plan_not_found():
    _, _, token, _ = create_logged_in_user(
        full_name="Update Missing Agent",
        role="Insurance Agent",
    )

    response = client.put(
        "/api/v1/plans/999999",
        headers=get_auth_header(token),
        json={
            "plan_name": "Updated Plan"
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Plan not found"
    )


def test_update_plan_invalid_age_range():
    _, _, token, _ = create_logged_in_user(
        full_name="Update Age Agent",
        role="Insurance Agent",
    )

    create_response = create_plan(
        token,
        plan_name="Update Age Plan",
        plan_type="Life",
    )

    plan_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        headers=get_auth_header(token),
        json={
            "eligibility_age_min": 60,
            "eligibility_age_max": 18,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Maximum eligibility age must be greater "
        "than minimum eligibility age"
    )


# ============================================================
# DELETE PLAN
# ============================================================


def test_super_admin_can_delete_plan():
    _, _, admin_token, _ = create_logged_in_user(
        full_name="Plan Super Admin",
        role="Super Admin",
    )

    create_response = create_plan(
        admin_token,
        plan_name="Delete Plan",
        plan_type="Life",
    )

    assert create_response.status_code == 201

    plan_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert data["message"] == (
        "Plan deleted successfully"
    )

    get_response = client.get(
        f"/api/v1/plans/{plan_id}",
        headers=get_auth_header(admin_token),
    )

    assert get_response.status_code == 404


def test_insurance_agent_cannot_delete_plan():
    _, _, agent_token, _ = create_logged_in_user(
        full_name="Delete Agent",
        role="Insurance Agent",
    )

    create_response = create_plan(
        agent_token,
        plan_name="Agent Delete Plan",
        plan_type="Life",
    )

    assert create_response.status_code == 201

    plan_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/plans/{plan_id}",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "You do not have permission to delete plans"
    )


def test_customer_cannot_create_plan():
    _, _, customer_token, _ = create_logged_in_user(
        full_name="Plan Customer",
        role="Customer",
    )

    response = create_plan(
        customer_token,
        plan_name="Customer Plan",
        plan_type="Life",
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "You do not have permission to create plans"
    )


def test_customer_cannot_update_plan():
    _, _, agent_token, _ = create_logged_in_user(
        full_name="Create Plan Agent",
        role="Insurance Agent",
    )

    create_response = create_plan(
        agent_token,
        plan_name="Customer Update Plan",
        plan_type="Life",
    )

    assert create_response.status_code == 201

    plan_id = create_response.json()["id"]

    _, _, customer_token, _ = create_logged_in_user(
        full_name="Update Plan Customer",
        role="Customer",
    )

    response = client.put(
        f"/api/v1/plans/{plan_id}",
        headers=get_auth_header(customer_token),
        json={
            "plan_name": "Customer Updated Plan"
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "You do not have permission to update plans"
    )


# ============================================================
# AUTHENTICATION TESTS
# ============================================================


def test_get_plans_without_token():
    response = client.get(
        "/api/v1/plans"
    )

    assert response.status_code == 401


def test_get_plan_without_token():
    response = client.get(
        "/api/v1/plans/1"
    )

    assert response.status_code == 401


def test_create_plan_without_token():
    response = client.post(
        "/api/v1/plans",
        json=plan_payload(
            "No Token Plan"
        ),
    )

    assert response.status_code == 401


def test_update_plan_without_token():
    response = client.put(
        "/api/v1/plans/1",
        json={
            "plan_name": "No Token Update"
        },
    )

    assert response.status_code == 401


def test_delete_plan_without_token():
    response = client.delete(
        "/api/v1/plans/1"
    )

    assert response.status_code == 401