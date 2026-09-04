# Insurance Policy & Claim Management System

## Overview

The **Insurance Policy & Claim Management System** is a backend application developed using **FastAPI** to manage insurance operations including customers, insurance plans, policies, beneficiaries, premium payments, claims, claim documents, claim assessments, settlements, policy renewals, dashboards, reports, notifications, and audit logs.

The system provides secure authentication, role-based access control, data validation, database transactions, filtering, pagination, sorting, and security features.

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

The system supports the following roles:

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

* Create insurance plans
* View insurance plans
* Update insurance plans
* Delete insurance plans
* Plan type management
* Coverage and premium management
* Eligibility validation

### Customer Management

* Customer profile management
* Customer information validation
* Customer identification management
* Customer search and retrieval
* Customer update and deletion

### Policy Management

* Create insurance policies
* View policies
* Update policies
* Delete policies
* Policy status management
* Customer-policy relationship
* Insurance plan association
* Agent assignment
* Policy date management
* Premium and coverage management

### Beneficiary Management

* Add beneficiaries to policies
* View policy beneficiaries
* Update beneficiaries
* Delete beneficiaries
* Beneficiary percentage validation
* Total beneficiary percentage validation
* Duplicate beneficiary prevention

### Premium Payment Management

* Create premium payments
* View payment details
* Update payments
* Delete payments
* Payment status management
* Payment method validation
* Transaction ID uniqueness
* Premium amount validation
* Policy and customer payment relationships

### Claims Management

* Create insurance claims
* Retrieve claims
* Update claims
* Delete claims
* Claim status management
* Claim type management
* Claim amount validation
* Claim date management
* Policy and customer claim relationships

### Claim Document Management

* Upload claim documents
* Retrieve claim documents
* Update document information
* Delete claim documents
* Claim-document relationships
* Document verification support

### Claim Assessment

* Claim assessment management
* Assessment status tracking
* Assessment information
* Claim evaluation
* Claims officer authorization

### Settlement Management

* Claim settlement processing
* Settlement status management
* Settlement amount management
* Finance officer authorization
* Claim-settlement relationship

### Policy Renewal

* Policy renewal management
* Renewal date tracking
* Renewal status management
* Premium updates
* Policy renewal history

### Dashboard & Reporting

* Insurance management dashboard
* Policy statistics
* Claim statistics
* Payment statistics
* Settlement statistics
* Operational reporting

### Notifications

* Insurance-related notifications
* Policy notifications
* Claim notifications
* Payment notifications
* Renewal notifications
* Role-based notification support

### Audit Logs

* User activity tracking
* Authentication activity
* Important system actions
* Resource-level activity tracking
* Audit history

---

## Filtering, Pagination & Sorting

The system supports advanced listing functionality across major resources.

### Policies

* Policy status filtering
* Plan type filtering
* Customer filtering
* Expiry date filtering
* Pagination
* Sorting
* Sort order

### Claims

* Claim status filtering
* Claim type filtering
* Claim date range filtering
* Claim amount range filtering
* Pagination
* Sorting
* Sort order

### Premium Payments

* Payment status filtering
* Payment method filtering
* Payment date range filtering
* Pagination
* Sorting
* Sort order

---

## Security

The application includes multiple security mechanisms:

* JWT-based authentication
* Role-based authorization
* Password hashing
* Protected API endpoints
* Account status validation
* Foreign key constraints
* Unique database constraints
* Database transactions
* Global exception handling
* Audit logging
* Soft delete support
* CORS configuration
* Rate limiting
* Security response headers

---

## API Versioning

All application APIs are versioned under:

`/api/v1`

This provides a consistent API structure and allows future versions to be introduced without breaking existing clients.

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

The application uses **PostgreSQL** as the primary relational database.

SQLAlchemy is used as the ORM layer, while Alembic is used for database schema migrations.

### Database Features

* Relational data modeling
* Foreign key relationships
* Unique constraints
* Transaction management
* Data integrity
* Migration management

---

## Database Migrations

Alembic is used to manage database schema changes.

Migration workflow:

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
* Authorization
* Validation
* Error handling
* Filtering
* Pagination
* Sorting
* Database integrity

Tests use a dedicated PostgreSQL test database to isolate test data from the main application database.

---

## Error Handling

The application provides centralized exception handling for:

* Request validation errors
* Database integrity errors
* SQLAlchemy database errors
* General application exceptions
* Authentication errors
* Authorization errors
* Resource-not-found errors

Validation errors use a consistent API response structure.

---

## Rate Limiting

SlowAPI is used to provide API rate limiting.

Rate limiting helps protect authentication and other sensitive endpoints from excessive requests and abuse.

During automated testing, rate limiting is disabled through the testing configuration.

---

## Security Headers

The application adds security-related HTTP headers including:

* `X-Content-Type-Options`
* `X-Frame-Options`
* `X-XSS-Protection`
* `Referrer-Policy`
* `Permissions-Policy`

---

## CORS

Cross-Origin Resource Sharing is configured through FastAPI middleware.

Allowed origins are managed through application configuration.

---

## API Documentation

FastAPI automatically provides interactive API documentation.

Available documentation interfaces:

* Swagger UI
* ReDoc

The documentation exposes the versioned API endpoints and their request and response schemas.

---

## Configuration

Application configuration is managed through environment variables.

Configuration includes:

* Database URL
* Secret key
* JWT algorithm
* Access token expiration
* Refresh token expiration
* CORS origins
* Testing configuration

Sensitive configuration values should be stored securely and should not be committed to source control.

---

## Running the Application

The application runs using Uvicorn.

The development server supports automatic reload during development.

---

## Testing Commands

Run the complete test suite using Pytest.

Individual test modules can also be executed independently for faster development and debugging.

---

## Development Practices

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

Handle HTTP requests, authentication dependencies, query parameters, and responses.

### Services

Contain business logic and application rules.

### Repositories

Handle database operations.

### Models

Define SQLAlchemy database entities and relationships.

### Schemas

Define request validation and response serialization using Pydantic.

---

## API Architecture

The API follows REST-style design principles with:

* Resource-based endpoints
* HTTP status codes
* Request validation
* Response schemas
* Authentication dependencies
* Role-based authorization
* API versioning
* Pagination
* Filtering
* Sorting

---

## Project Status

The Insurance Policy & Claim Management System includes implemented functionality for:

* Authentication & User Management
* Insurance Plans
* Customers
* Policies
* Beneficiaries
* Premium Payments
* Claims
* Claim Documents
* Claim Assessments
* Settlements
* Policy Renewals
* Dashboards
* Reports
* Notifications
* Audit Logs
* Filtering
* Pagination
* Sorting
* Security & Data Integrity

---

## Author

**Srikanth Bethamcharla**

---

## License

This project is intended for educational and development purposes.
