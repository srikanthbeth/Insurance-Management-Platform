
import os
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
# CUSTOMER
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
# AGENT
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
# PLAN
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
# POLICY
# ============================================================

def create_policy_test_data():
    customer_id, customer_token, _ = create_customer()

    agent_id, agent_token = create_agent()

    plan_id = create_plan(agent_token)

    from datetime import date, timedelta

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
    )


# ============================================================
# CLAIM
# ============================================================

def create_claim(
    token,
    policy_id,
    customer_id,
):
    from datetime import date

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
            "claim_amount": 50000,
            "description": "Hospitalization claim",
            "status": "Submitted",
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


def create_claim_test_data():
    (
        policy_id,
        agent_token,
        customer_token,
        customer_id,
    ) = create_policy_test_data()

    claim_id = create_claim(
        agent_token,
        policy_id,
        customer_id,
    )

    return (
        claim_id,
        agent_token,
        customer_token,
        customer_id,
    )


# ============================================================
# DOCUMENT UPLOAD HELPER
# ============================================================

def upload_document(
    token,
    claim_id,
    document_type="Medical Report",
    filename="medical_report.pdf",
):
    return client.post(
        f"/api/v1/claims/{claim_id}/documents",
        headers=get_auth_header(token),
        data={
            "document_type": document_type,
        },
        files={
            "file": (
                filename,
                b"Test document content",
                "application/pdf",
            )
        },
    )


# ============================================================
# CREATE / UPLOAD DOCUMENT
# ============================================================

def test_upload_claim_document():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = upload_document(
        agent_token,
        claim_id,
    )

    assert response.status_code == 201, (
        f"Document upload failed: "
        f"{response.text}"
    )

    data = response.json()

    assert data["claim_id"] == claim_id
    assert data["document_type"] == "Medical Report"
    assert data["file_name"] == "medical_report.pdf"
    assert data["verification_status"] == "Pending"
    assert "id" in data
    assert "file_path" in data
    assert "uploaded_at" in data


# ============================================================
# DOCUMENT TYPES
# ============================================================

def test_upload_id_proof():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = upload_document(
        agent_token,
        claim_id,
        document_type="ID Proof",
        filename="id_proof.pdf",
    )

    assert response.status_code == 201


def test_upload_invoice():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = upload_document(
        agent_token,
        claim_id,
        document_type="Invoice",
        filename="invoice.pdf",
    )

    assert response.status_code == 201


def test_upload_medical_report():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = upload_document(
        agent_token,
        claim_id,
        document_type="Medical Report",
        filename="medical.pdf",
    )

    assert response.status_code == 201


def test_upload_fir():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = upload_document(
        agent_token,
        claim_id,
        document_type="FIR",
        filename="fir.pdf",
    )

    assert response.status_code == 201


def test_upload_repair_estimate():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = upload_document(
        agent_token,
        claim_id,
        document_type="Repair Estimate",
        filename="repair.pdf",
    )

    assert response.status_code == 201


def test_upload_other_document():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = upload_document(
        agent_token,
        claim_id,
        document_type="Other",
        filename="other.pdf",
    )

    assert response.status_code == 201


# ============================================================
# INVALID DOCUMENT TYPE
# ============================================================

def test_invalid_document_type():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = upload_document(
        agent_token,
        claim_id,
        document_type="Invalid Type",
        filename="invalid.pdf",
    )

    assert response.status_code == 400

    assert "invalid document type" in (
        response.json()["detail"].lower()
    )


# ============================================================
# INVALID FILE EXTENSION
# ============================================================

def test_invalid_file_extension():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = client.post(
        f"/api/v1/claims/{claim_id}/documents",
        headers=get_auth_header(agent_token),
        data={
            "document_type": "Medical Report",
        },
        files={
            "file": (
                "document.txt",
                b"Invalid file",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    assert "file type not allowed" in (
        response.json()["detail"].lower()
    )


def test_doc_file_not_allowed():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = client.post(
        f"/api/v1/claims/{claim_id}/documents",
        headers=get_auth_header(agent_token),
        data={
            "document_type": "Medical Report",
        },
        files={
            "file": (
                "document.doc",
                b"Invalid file",
                "application/msword",
            )
        },
    )

    assert response.status_code == 400


# ============================================================
# ALLOWED FILE EXTENSIONS
# ============================================================

def test_pdf_file_allowed():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = upload_document(
        agent_token,
        claim_id,
        filename="document.pdf",
    )

    assert response.status_code == 201


def test_jpg_file_allowed():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = client.post(
        f"/api/v1/claims/{claim_id}/documents",
        headers=get_auth_header(agent_token),
        data={
            "document_type": "Medical Report",
        },
        files={
            "file": (
                "document.jpg",
                b"Test JPG content",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 201


def test_jpeg_file_allowed():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = client.post(
        f"/api/v1/claims/{claim_id}/documents",
        headers=get_auth_header(agent_token),
        data={
            "document_type": "Medical Report",
        },
        files={
            "file": (
                "document.jpeg",
                b"Test JPEG content",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 201


def test_png_file_allowed():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    response = client.post(
        f"/api/v1/claims/{claim_id}/documents",
        headers=get_auth_header(agent_token),
        data={
            "document_type": "Medical Report",
        },
        files={
            "file": (
                "document.png",
                b"Test PNG content",
                "image/png",
            )
        },
    )

    assert response.status_code == 201


# ============================================================
# CLAIM NOT FOUND
# ============================================================

def test_upload_document_claim_not_found():
    _, agent_token, _, _ = create_claim_test_data()

    response = upload_document(
        agent_token,
        999999,
    )

    assert response.status_code == 404

    assert "claim not found" in (
        response.json()["detail"].lower()
    )


def test_get_documents_claim_not_found():
    _, agent_token, _, _ = create_claim_test_data()

    response = client.get(
        "/api/v1/claims/999999/documents",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 404

    assert "claim not found" in (
        response.json()["detail"].lower()
    )


# ============================================================
# GET DOCUMENTS
# ============================================================

def test_get_claim_documents():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    upload_response = upload_document(
        agent_token,
        claim_id,
    )

    assert upload_response.status_code == 201

    response = client.get(
        f"/api/v1/claims/{claim_id}/documents",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    document = data[0]

    assert document["claim_id"] == claim_id
    assert document["document_type"] == "Medical Report"
    assert document["file_name"] == "medical_report.pdf"
    assert document["verification_status"] == "Pending"


def test_get_multiple_claim_documents():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    first = upload_document(
        agent_token,
        claim_id,
        document_type="Medical Report",
        filename="medical.pdf",
    )

    second = upload_document(
        agent_token,
        claim_id,
        document_type="Invoice",
        filename="invoice.pdf",
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        f"/api/v1/claims/{claim_id}/documents",
        headers=get_auth_header(agent_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["claim_id"] == claim_id
    assert data[1]["claim_id"] == claim_id


# ============================================================
# VERIFY DOCUMENT
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


def test_verify_claim_document():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    upload_response = upload_document(
        agent_token,
        claim_id,
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    officer_token = create_claims_officer()

    response = client.put(
        f"/api/v1/claims/documents/{document_id}/verify",
        headers=get_auth_header(officer_token),
        data={
            "verification_status": "Verified",
        },
    )

    assert response.status_code == 200, (
        f"Document verification failed: "
        f"{response.text}"
    )

    data = response.json()

    assert data["id"] == document_id
    assert data["claim_id"] == claim_id
    assert data["verification_status"] == "Verified"


def test_reject_claim_document():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    upload_response = upload_document(
        agent_token,
        claim_id,
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    officer_token = create_claims_officer()

    response = client.put(
        f"/api/v1/claims/documents/{document_id}/verify",
        headers=get_auth_header(officer_token),
        data={
            "verification_status": "Rejected",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == document_id
    assert data["verification_status"] == "Rejected"


# ============================================================
# INVALID VERIFICATION STATUS
# ============================================================

def test_invalid_verification_status():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    upload_response = upload_document(
        agent_token,
        claim_id,
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    officer_token = create_claims_officer()

    response = client.put(
        f"/api/v1/claims/documents/{document_id}/verify",
        headers=get_auth_header(officer_token),
        data={
            "verification_status": "Pending",
        },
    )

    assert response.status_code == 400

    assert "invalid verification status" in (
        response.json()["detail"].lower()
    )


# ============================================================
# DOCUMENT NOT FOUND
# ============================================================

def test_verify_document_not_found():
    officer_token = create_claims_officer()

    response = client.put(
        "/api/v1/claims/documents/999999/verify",
        headers=get_auth_header(officer_token),
        data={
            "verification_status": "Verified",
        },
    )

    assert response.status_code == 404

    assert "document not found" in (
        response.json()["detail"].lower()
    )


# ============================================================
# AUTHENTICATION
# ============================================================

def test_upload_document_without_token():
    claim_id, _, _, _ = create_claim_test_data()

    response = client.post(
        f"/api/v1/claims/{claim_id}/documents",
        data={
            "document_type": "Medical Report",
        },
        files={
            "file": (
                "medical.pdf",
                b"Test document",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 401


def test_get_documents_without_token():
    claim_id, _, _, _ = create_claim_test_data()

    response = client.get(
        f"/api/v1/claims/{claim_id}/documents",
    )

    assert response.status_code == 401


def test_verify_document_without_token():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    upload_response = upload_document(
        agent_token,
        claim_id,
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    response = client.put(
        f"/api/v1/claims/documents/{document_id}/verify",
        data={
            "verification_status": "Verified",
        },
    )

    assert response.status_code == 401


# ============================================================
# ROLE AUTHORIZATION
# ============================================================

def test_agent_cannot_verify_document():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    upload_response = upload_document(
        agent_token,
        claim_id,
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    response = client.put(
        f"/api/v1/claims/documents/{document_id}/verify",
        headers=get_auth_header(agent_token),
        data={
            "verification_status": "Verified",
        },
    )

    assert response.status_code == 403


def test_customer_can_upload_document():
    (
        claim_id,
        _,
        customer_token,
        _,
    ) = create_claim_test_data()

    response = upload_document(
        customer_token,
        claim_id,
    )

    assert response.status_code == 201


def test_customer_can_get_documents():
    (
        claim_id,
        _,
        customer_token,
        _,
    ) = create_claim_test_data()

    upload_response = upload_document(
        customer_token,
        claim_id,
    )

    assert upload_response.status_code == 201

    response = client.get(
        f"/api/v1/claims/{claim_id}/documents",
        headers=get_auth_header(customer_token),
    )

    assert response.status_code == 200


def test_claims_officer_can_verify_document():
    (
        claim_id,
        agent_token,
        _,
        _,
    ) = create_claim_test_data()

    upload_response = upload_document(
        agent_token,
        claim_id,
    )

    assert upload_response.status_code == 201

    document_id = upload_response.json()["id"]

    officer_token = create_claims_officer()

    response = client.put(
        f"/api/v1/claims/documents/{document_id}/verify",
        headers=get_auth_header(officer_token),
        data={
            "verification_status": "Verified",
        },
    )

    assert response.status_code == 200

    assert response.json()["verification_status"] == "Verified"

