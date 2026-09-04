from sqlalchemy.orm import Session

from repositories.report_repository import (
    get_policy_premium_report,
    get_customer_policy_history,
    get_claim_settlement_report,
    get_agent_performance_report,
    get_monthly_premium_report,
    get_monthly_claim_report,
)


def get_policy_premium_report_service(
    db: Session,
):
    return get_policy_premium_report(db)


def get_customer_policy_history_service(
    db: Session,
):
    return get_customer_policy_history(db)


def get_claim_settlement_report_service(
    db: Session,
):
    return get_claim_settlement_report(db)


def get_agent_performance_report_service(
    db: Session,
):
    return get_agent_performance_report(db)


def get_monthly_premium_report_service(
    db: Session,
):
    return get_monthly_premium_report(db)


def get_monthly_claim_report_service(
    db: Session,
):
    return get_monthly_claim_report(db)