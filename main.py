from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import settings
from utils.rate_limiter import limiter
from middleware.security_headers import SecurityHeadersMiddleware

from exceptions.handlers import (
    validation_exception_handler,
    integrity_error_handler,
    database_exception_handler,
    general_exception_handler,
)

from routes.auth import router as auth_router
from routes.plan import router as plan_router
from routes.customers import router as customer_router
from routes.policy import router as policy_router
from routes.beneficiary import router as beneficiary_router
from routes.premium_payment import router as premium_payment_router
from routes.claim import router as claim_router
from routes.claim_document import router as claim_document_router
from routes.claim_assessment import router as claim_assessment_router
from routes.settlement import router as settlement_router
from routes.policy_renewal import router as policy_renewal_router
from routes.dashboard import router as dashboard_router
from routes.report import router as report_router
from routes.notification import router as notification_router
from routes.audit_log import router as audit_log_router


app = FastAPI(
    title="Insurance Policy & Claim Management System",
    description=(
        "Insurance management platform for customers, "
        "policies, premiums, claims, assessments, "
        "settlements and renewals."
    ),
    version="1.0.0",
)

print("🔥 INSURANCE MAIN.PY LOADED")



# ============================================================
# SECURITY HEADERS
# ============================================================

app.add_middleware(
    SecurityHeadersMiddleware
)

# ============================================================
# RATE LIMITING
# ============================================================

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_middleware(SlowAPIMiddleware)


# ============================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    IntegrityError,
    integrity_error_handler,
)

app.add_exception_handler(
    SQLAlchemyError,
    database_exception_handler,
)

app.add_exception_handler(
    Exception,
    general_exception_handler,
)


# ============================================================
# CORS
# ============================================================

origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    plan_router,
    prefix="/api/v1",
)

app.include_router(
    customer_router,
    prefix="/api/v1",
)

app.include_router(
    policy_router,
    prefix="/api/v1",
)

app.include_router(
    beneficiary_router,
    prefix="/api/v1",
)

app.include_router(
    premium_payment_router,
    prefix="/api/v1",
)

app.include_router(
    claim_router,
    prefix="/api/v1",
)

app.include_router(
    claim_document_router,
    prefix="/api/v1",
)

app.include_router(
    claim_assessment_router,
    prefix="/api/v1",
)

app.include_router(
    settlement_router,
    prefix="/api/v1",
)

app.include_router(
    policy_renewal_router,
    prefix="/api/v1",
)

app.include_router(
    dashboard_router,
    prefix="/api/v1",
)

app.include_router(
    report_router,
    prefix="/api/v1",
)

app.include_router(
    notification_router,
    prefix="/api/v1",
)

app.include_router(
    audit_log_router,
    prefix="/api/v1",
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": (
            "Insurance Policy & Claim "
            "Management System is running"
        ),
        "version": "1.0.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/v1/health")
def health_check():
    return {
        "success": True,
        "message": "API is healthy",
    }