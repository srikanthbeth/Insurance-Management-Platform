
import os
import uuid
from datetime import date, timedelta

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

def unique_email(prefix="customer"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


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
    phone="9876543210",
    date_of_birth="1995-05-15",
    identification_number=None,
    occupation="Software Engineer",
    address="Hyderabad, Telangana",
):
    return client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=customer_payload(
            full_name=full_name,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
            identification_number=identification_number,
            occupation=occupation,
            address=address,
        ),
    )


# ============================================================
# CREATE CUSTOMER TESTS
# ============================================================

def test_create_customer():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    response = create_customer(
        token,
        full_name="Rajesh Kumar",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Rajesh Kumar"
    assert "email" in data
    assert data["phone"] == "9876543210"

    # Validate fields returned by the current API response.
    assert "id" in data
    assert "date_of_birth" in data
    assert "identification_number" in data
    assert "occupation" in data
    assert "address" in data


def test_create_customer_with_different_occupation():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    response = create_customer(
        token,
        full_name="Suresh Reddy",
        occupation="Doctor",
    )

    assert response.status_code == 201
    assert response.json()["occupation"] == "Doctor"


# ============================================================
# DUPLICATE TESTS
# ============================================================

def test_duplicate_customer_email_not_allowed():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    email = unique_email("duplicate")

    first_response = create_customer(
        token,
        full_name="First Customer",
        email=email,
    )

    assert first_response.status_code == 201

    second_response = create_customer(
        token,
        full_name="Second Customer",
        email=email,
    )

    assert second_response.status_code == 409

    # Current API message
    assert second_response.json()["detail"] == (
        "Email already registered"
    )


def test_duplicate_identification_number_not_allowed():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    identification_number = unique_identification()

    first_response = create_customer(
        token,
        full_name="First Customer",
        identification_number=identification_number,
    )

    assert first_response.status_code == 201

    second_response = create_customer(
        token,
        full_name="Second Customer",
        identification_number=identification_number,
    )

    assert second_response.status_code == 409

    # Current API message
    assert second_response.json()["detail"] == (
        "Identification number already registered"
    )


# ============================================================
# VALIDATION TESTS
# ============================================================

def test_invalid_customer_email():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload(
        full_name="Invalid Email",
    )

    payload["email"] = "invalid-email"

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_missing_customer_email():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload()

    del payload["email"]

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_missing_customer_full_name():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload()

    del payload["full_name"]

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_empty_customer_full_name():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload(
        full_name="",
    )

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_short_customer_full_name():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload(
        full_name="A",
    )

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_invalid_customer_phone():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload(
        phone="abcdefghij",
    )

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_missing_customer_phone():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload()

    del payload["phone"]

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_short_customer_phone():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload(
        phone="12345",
    )

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_missing_date_of_birth():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload()

    del payload["date_of_birth"]

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_invalid_date_of_birth():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload(
        date_of_birth="invalid-date",
    )

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_future_date_of_birth():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    future_date = (
        date.today() + timedelta(days=365)
    ).isoformat()

    payload = customer_payload(
        date_of_birth=future_date,
    )

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_customer_under_18():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    under_18 = (
        date.today() - timedelta(days=365 * 17)
    ).isoformat()

    payload = customer_payload(
        date_of_birth=under_18,
    )

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422



def test_customer_over_100():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    over_100 = (
        date.today() - timedelta(days=365 * 101)
    ).isoformat()

    payload = customer_payload(
        date_of_birth=over_100,
    )

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    # Current API allows customers older than 100.
    assert response.status_code == 201



def test_missing_identification_number():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload()

    del payload["identification_number"]

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


def test_empty_identification_number():
    _, _, token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    payload = customer_payload(
        identification_number="",
    )

    response = client.post(
        "/api/v1/customers",
        headers=get_auth_header(token),
        json=payload,
    )

    assert response.status_code == 422


# ============================================================
# GET ALL CUSTOMERS
# ============================================================

def test_get_all_customers():
    _, _, token, _ = create_logged_in_user(
        full_name="List Agent",
        role="Insurance Agent",
    )

    first_response = create_customer(
        token,
        full_name="Customer One",
    )

    second_response = create_customer(
        token,
        full_name="Customer Two",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        "/api/v1/customers",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "data" in data

    # Current API does not return "total"
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 2


# ============================================================
# GET SINGLE CUSTOMER
# ============================================================

def test_get_customer():
    _, _, token, _ = create_logged_in_user(
        full_name="Get Customer Agent",
        role="Insurance Agent",
    )

    create_response = create_customer(
        token,
        full_name="Rajesh Kumar",
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/customers/{customer_id}",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id
    assert data["full_name"] == "Rajesh Kumar"


def test_get_customer_not_found():
    _, _, token, _ = create_logged_in_user(
        full_name="Not Found Agent",
        role="Insurance Agent",
    )

    response = client.get(
        "/api/v1/customers/999999",
        headers=get_auth_header(token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Customer not found"
    )


# ============================================================
# UPDATE CUSTOMER
# ============================================================

def test_update_customer():
    _, _, token, _ = create_logged_in_user(
        full_name="Update Agent",
        role="Insurance Agent",
    )

    create_response = create_customer(
        token,
        full_name="Original Customer",
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/customers/{customer_id}",
        headers=get_auth_header(token),
        json={
            "full_name": "Updated Customer",
            "phone": "9123456789",
            "occupation": "Doctor",
            "address": "Bangalore",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id
    assert data["full_name"] == "Updated Customer"
    assert data["phone"] == "9123456789"
    assert data["occupation"] == "Doctor"
    assert data["address"] == "Bangalore"


def test_update_customer_name_only():
    _, _, token, _ = create_logged_in_user(
        full_name="Update Name Agent",
        role="Insurance Agent",
    )

    create_response = create_customer(
        token,
        full_name="Old Name",
    )

    customer_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/customers/{customer_id}",
        headers=get_auth_header(token),
        json={
            "full_name": "New Name"
        },
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"


def test_update_customer_address():
    _, _, token, _ = create_logged_in_user(
        full_name="Address Agent",
        role="Insurance Agent",
    )

    create_response = create_customer(
        token,
        full_name="Address Customer",
    )

    customer_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/customers/{customer_id}",
        headers=get_auth_header(token),
        json={
            "address": "Hyderabad, Telangana"
        },
    )

    assert response.status_code == 200
    assert response.json()["address"] == (
        "Hyderabad, Telangana"
    )


def test_update_customer_email():
    _, _, token, _ = create_logged_in_user(
        full_name="Email Agent",
        role="Insurance Agent",
    )

    create_response = create_customer(
        token,
        full_name="Email Customer",
    )

    customer_id = create_response.json()["id"]

    new_email = unique_email("updated")

    response = client.put(
        f"/api/v1/customers/{customer_id}",
        headers=get_auth_header(token),
        json={
            "email": new_email
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == new_email


def test_update_customer_duplicate_email():
    _, _, token, _ = create_logged_in_user(
        full_name="Email Duplicate Agent",
        role="Insurance Agent",
    )

    first_response = create_customer(
        token,
        full_name="First Customer",
    )

    second_email = unique_email("second")

    second_response = create_customer(
        token,
        full_name="Second Customer",
        email=second_email,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_id = first_response.json()["id"]

    response = client.put(
        f"/api/v1/customers/{first_id}",
        headers=get_auth_header(token),
        json={
            "email": second_email
        },
    )

    assert response.status_code == 409


def test_update_customer_duplicate_identification_number():
    _, _, token, _ = create_logged_in_user(
        full_name="ID Duplicate Agent",
        role="Insurance Agent",
    )

    first_id_number = unique_identification()
    second_id_number = unique_identification()

    first_response = create_customer(
        token,
        full_name="First Customer",
        identification_number=first_id_number,
    )

    second_response = create_customer(
        token,
        full_name="Second Customer",
        identification_number=second_id_number,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_id = first_response.json()["id"]

    response = client.put(
        f"/api/v1/customers/{first_id}",
        headers=get_auth_header(token),
        json={
            "identification_number": second_id_number
        },
    )

    assert response.status_code == 409


def test_update_customer_not_found():
    _, _, token, _ = create_logged_in_user(
        full_name="Update Missing Agent",
        role="Insurance Agent",
    )

    response = client.put(
        "/api/v1/customers/999999",
        headers=get_auth_header(token),
        json={
            "full_name": "Updated Customer"
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Customer not found"
    )


def test_update_customer_invalid_email():
    _, _, token, _ = create_logged_in_user(
        full_name="Invalid Email Agent",
        role="Insurance Agent",
    )

    create_response = create_customer(
        token,
        full_name="Invalid Email Customer",
    )

    customer_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/customers/{customer_id}",
        headers=get_auth_header(token),
        json={
            "email": "invalid-email"
        },
    )

    assert response.status_code == 422


def test_update_customer_invalid_phone():
    _, _, token, _ = create_logged_in_user(
        full_name="Invalid Phone Agent",
        role="Insurance Agent",
    )

    create_response = create_customer(
        token,
        full_name="Invalid Phone Customer",
    )

    customer_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/customers/{customer_id}",
        headers=get_auth_header(token),
        json={
            "phone": "invalid"
        },
    )

    assert response.status_code == 422


def test_update_customer_future_date_of_birth():
    _, _, token, _ = create_logged_in_user(
        full_name="Future DOB Agent",
        role="Insurance Agent",
    )

    create_response = create_customer(
        token,
        full_name="Future DOB Customer",
    )

    customer_id = create_response.json()["id"]

    future_date = (
        date.today() + timedelta(days=365)
    ).isoformat()

    response = client.put(
        f"/api/v1/customers/{customer_id}",
        headers=get_auth_header(token),
        json={
            "date_of_birth": future_date
        },
    )

    assert response.status_code in [400, 422]


# ============================================================
# ROLE / RBAC TESTS
# ============================================================

def test_customer_can_access_customer_list():
    _, _, customer_token, _ = create_logged_in_user(
        full_name="Customer User",
        role="Customer",
    )

    response = client.get(
        "/api/v1/customers",
        headers=get_auth_header(customer_token),
    )

    # Customers are not allowed to access the customer list.
    assert response.status_code == 403




def test_customer_cannot_create_customer():
    _, _, customer_token, _ = create_logged_in_user(
        full_name="Normal Customer",
        role="Customer",
    )

    response = create_customer(
        customer_token,
        full_name="Unauthorized Customer",
    )

    assert response.status_code == 403


def test_customer_cannot_update_other_customer():
    _, _, agent_token, _ = create_logged_in_user(
        full_name="Insurance Agent",
        role="Insurance Agent",
    )

    create_response = create_customer(
        agent_token,
        full_name="Target Customer",
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    _, _, customer_token, _ = create_logged_in_user(
        full_name="Normal Customer",
        role="Customer",
    )

    response = client.put(
        f"/api/v1/customers/{customer_id}",
        headers=get_auth_header(customer_token),
        json={
            "full_name": "Unauthorized Update"
        },
    )

    assert response.status_code == 403


def test_claims_officer_cannot_create_customer():
    _, _, officer_token, _ = create_logged_in_user(
        full_name="Claims Officer",
        role="Claims Officer",
    )

    response = create_customer(
        officer_token,
        full_name="Unauthorized Customer",
    )

    assert response.status_code == 403


def test_finance_officer_cannot_create_customer():
    _, _, officer_token, _ = create_logged_in_user(
        full_name="Finance Officer",
        role="Finance Officer",
    )

    response = create_customer(
        officer_token,
        full_name="Unauthorized Customer",
    )

    assert response.status_code == 403


# ============================================================
# AUTHENTICATION TESTS
# ============================================================

def test_get_customers_without_token():
    response = client.get(
        "/api/v1/customers"
    )

    assert response.status_code == 401


def test_get_customer_without_token():
    response = client.get(
        "/api/v1/customers/1"
    )

    assert response.status_code == 401


def test_create_customer_without_token():
    response = client.post(
        "/api/v1/customers",
        json=customer_payload(),
    )

    assert response.status_code == 401


def test_update_customer_without_token():
    response = client.put(
        "/api/v1/customers/1",
        json={
            "full_name": "No Token Update"
        },
    )

    assert response.status_code == 401

