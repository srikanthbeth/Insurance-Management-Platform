# Insurance Policy & Claim Management System

## Overview

The **Insurance Policy & Claim Management System** is a backend application developed using **FastAPI** for managing insurance operations such as customers, insurance plans, policies, beneficiaries, premium payments, claims, claim documents, claim assessments, settlements, policy renewals, dashboards, reports, notifications, and audit logs.

The system provides secure authentication, role-based access control, validation, database integrity, filtering, pagination, sorting, and comprehensive automated testing.

---

## Technology Stack

* Python 3.11+
* FastAPI
* Pydantic v2
* SQLAlchemy
* PostgreSQL
* Alembic
* JWT Authentication
* Passlib / Bcrypt
* Pytest
* SlowAPI
* Uvicorn

---

## User Roles

* Super Admin
* Insurance Agent
* Claims Officer
* Finance Officer
* Customer

---

## Core Features

### Authentication & User Management

* User registration
* User login
* JWT access tokens
* Refresh tokens
* Password hashing
* Password change
* Current user information
* Account activation and deactivation
* Role-based access control

### Insurance Plan Management

* Insurance plan creation
* Insurance plan retrieval
* Insurance plan updates
* Insurance plan deletion
* Plan type management
* Coverage management
* Premium management
* Eligibility validation

### Customer Management

* Customer profile management
* Customer information validation
* Customer identification management
* Customer retrieval
* Customer updates
* Customer deletion

### Policy Management

* Insurance policy creation
* Policy retrieval
* Policy updates
* Policy deletion
* Policy status management
* Customer-policy relationships
* Insurance plan relationships
* Agent assignment
* Policy period management
* Premium management
* Coverage management

### Beneficiary Management

* Beneficiary creation
* Beneficiary retrieval
* Beneficiary updates
* Beneficiary deletion
* Beneficiary percentage validation
* Total beneficiary percentage validation
* Duplicate beneficiary prevention

### Premium Payment Management

* Premium payment creation
* Payment retrieval
* Payment updates
* Payment deletion
* Payment status management
* Payment method validation
* Transaction ID uniqueness
* Premium amount validation
* Policy and customer payment relationships

### Claims Management

* Claim creation
* Claim retrieval
* Claim updates
* Claim deletion
* Claim status management
* Claim type management
* Claim amount validation
* Claim date management
* Policy and customer claim relationships

### Claim Document Management

* Claim document management
* Document creation
* Document retrieval
* Document updates
* Document deletion
* Document verification support
* Claim-document relationships

### Claim Assessment

* Claim assessment management
* Claim evaluation
* Assessment status tracking
* Assessment information management
* Claims officer authorization

### Settlement Management

* Claim settlement management
* Settlement amount management
* Settlement status tracking
* Finance officer authorization
* Claim-settlement relationships

### Policy Renewal

* Policy renewal management
* Renewal date tracking
* Renewal status management
* Premium updates
* Renewal history

### Dashboard & Reporting

* Insurance statistics
* Policy statistics
* Claim statistics
* Payment statistics
* Settlement statistics
* Operational reports

### Notifications

* Policy notifications
* Claim notifications
* Payment notifications
* Renewal notifications
* Role-based notifications

### Audit Logs

* User activity tracking
* Authentication activity tracking
* System action tracking
* Resource-level audit history

---

## Filtering, Pagination & Sorting

The system supports filtering, pagination, and sorting for major resources.

### Policies

* Policy status
* Plan type
* Customer
* Expiry date
* Pagination
* Sorting
* Sort order

### Claims

* Claim status
* Claim type
* Claim date range
* Claim amount range
* Pagination
* Sorting
* Sort order

### Premium Payments

* Payment status
* Payment method
* Payment date range
* Pagination
* Sorting
* Sort order

---

## Security

The application implements multiple security and data-integrity mechanisms:

* JWT authentication
* Role-based authorization
* Password hashing
* Protected API endpoints
* Active account verification
* Foreign key constraints
* Unique constraints
* Database transactions
* Global exception handling
* Audit logging
* Soft delete support
* CORS configuration
* Rate limiting
* Security response headers

---

## API Versioning

All application APIs use the versioned prefix:

```text
/api/v1
```

API versioning provides a consistent structure and supports future API versions without affecting existing clients.

---

## Architecture

The project follows a layered architecture:

```text
Routes
   ↓
Services
   ↓
Repositories
   ↓
Models
   ↓
PostgreSQL
```

### Routes

Responsible for:

* HTTP endpoints
* Request handling
* Authentication dependencies
* Authorization
* Query parameters
* API responses

### Services

Responsible for:

* Business logic
* Validation rules
* Application workflows
* Business constraints

### Repositories

Responsible for:

* Database queries
* Database CRUD operations
* Filtering
* Pagination
* Sorting

### Schemas

Responsible for:

* Request validation
* Response serialization
* Pydantic models
* Field validation

### Models

Responsible for:

* Database entities
* Relationships
* Constraints
* SQLAlchemy ORM mapping

---

## Project Structure

```text
Insurance-Policy-Claim-Management/
│
├── auth/
├── dependencies/
├── exceptions/
├── middleware/
├── models/
├── repositories/
├── routes/
├── schemas/
├── services/
├── tests/
├── utils/
│
├── alembic/
├── config.py
├── database.py
├── main.py
├── alembic.ini
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Database

The application uses **PostgreSQL** as its relational database.

SQLAlchemy is used for database interaction and Alembic is used for database schema migrations.

### Database Capabilities

* Relational data modeling
* Foreign key relationships
* Unique constraints
* Transaction management
* Data integrity
* Migration management

---

## Database Migrations

Alembic manages database schema changes.

The migration workflow is:

```text
Model Changes
     ↓
Alembic Migration
     ↓
Database Schema Update
```

---

## Testing

The project uses **Pytest** for automated testing.

The test suite covers:

* Authentication
* User management
* Insurance plans
* Customers
* Policies
* Beneficiaries
* Premium payments
* Claims
* Claim documents
* Claim assessments
* Settlements
* Policy renewals
* Authentication
* Authorization
* Validation
* Error handling
* Database integrity
* Filtering
* Pagination
* Sorting
* Business rules

### Final Test Status

The complete test suite successfully passed:

```text
419 passed
2 warnings
```

The beneficiary test suite was also successfully completed after updating the validation assertions to match the application's centralized validation response format.

Final beneficiary test result:

```text
19 passed
2 warnings
```

The previously failing three beneficiary tests were:

* Beneficiary percentage cannot exceed 100
* Beneficiary percentage cannot be zero
* Beneficiary percentage cannot be negative

All three tests have now been corrected and pass successfully.

---

## Test Database

Automated tests use a dedicated PostgreSQL test database to keep test data isolated from the main application database.

The test environment also disables rate limiting to prevent authentication rate limits from interfering with automated tests.

---

## Error Handling

The application provides centralized exception handling for:

* Request validation errors
* Database integrity errors
* SQLAlchemy errors
* General application exceptions
* Authentication errors
* Authorization errors
* Resource-not-found errors

Validation errors follow a consistent response structure throughout the API.

---

## Rate Limiting

SlowAPI is used for API rate limiting.

Rate limiting protects sensitive endpoints against excessive requests and abuse.

Testing mode disables rate limiting so the automated test suite can execute reliably.

---

## Security Headers

The application adds security response headers including:

* `X-Content-Type-Options`
* `X-Frame-Options`
* `X-XSS-Protection`
* `Referrer-Policy`
* `Permissions-Policy`

---

## CORS

Cross-Origin Resource Sharing is configured through FastAPI middleware.

Allowed origins are controlled through application configuration.

---

## API Documentation

FastAPI provides interactive API documentation through:

* Swagger UI
* ReDoc

The documentation exposes the versioned endpoints, request schemas, response schemas, authentication requirements, and API operations.

---

## Configuration

Application configuration is managed through environment variables.

Configuration includes:

* Database connection
* Secret key
* JWT algorithm
* Access token expiration
* Refresh token expiration
* CORS origins
* Testing configuration
* Rate limiting configuration

Sensitive configuration values should not be committed to source control.

---

## Running the Application

The application is designed to run using Uvicorn.

The development environment supports automatic reload for faster development.

---

## Testing Commands

The project supports running:

* Complete test suite
* Individual test modules
* Specific test cases

Pytest is used as the primary testing framework.

---

## Current Project Status

The following modules have been implemented:

* Authentication & User Management
* Insurance Plan Management
* Customer Management
* Policy Management
* Beneficiary Management
* Premium Payment Management
* Claims Management
* Claim Document Management
* Claim Assessment
* Settlement Management
* Policy Renewal
* Dashboard
* Reporting
* Notifications
* Audit Logs
* Filtering
* Pagination
* Sorting
* Security & Data Integrity

### Testing Status

```text
Total Tests: 419
Passed: 419
Failed: 0
Warnings: 2
```

The project currently has **100% passing automated tests**.

---

## Warnings

The test suite currently reports two non-blocking dependency/code warnings:

* Starlette `TestClient` / HTTPX deprecation warning
* Pydantic v2 class-based configuration deprecation warning in the beneficiary schema

These warnings do not affect the successful test results.

---

## Author

**Srikanth Bethamcharla**

---

## License

This project is intended for educational and development purposes.
