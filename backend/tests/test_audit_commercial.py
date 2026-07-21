from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.modules.audit.commercial_operations import (
    CommercialAuditSpec,
    commercial_audit_operation,
)
from app.modules.audit.commercial_registry import (
    COMMERCIAL_AUDIT_SPECS,
    install_commercial_auditing,
)
from app.modules.audit.constants import AuditOutcome
from app.modules.audit.context import (
    AuditRequestContext,
    reset_audit_context,
    set_audit_context,
)
from app.modules.audit.models import AuditLog


def test_commercial_registry_is_complete() -> None:
    installed = install_commercial_auditing()

    assert installed >= 0
    assert len(COMMERCIAL_AUDIT_SPECS) == 31

    for spec in COMMERCIAL_AUDIT_SPECS:
        module = __import__(
            spec.module_path,
            fromlist=[spec.class_name],
        )
        service_class = getattr(
            module,
            spec.class_name,
        )
        operation = getattr(
            service_class,
            spec.method_name,
        )
        assert getattr(
            operation,
            "__poultrypulse_audit_wrapped__",
            False,
        )


class DemoFinanceService:
    def __init__(self, database_session: Session) -> None:
        self.db = database_session

    def sync_receipts(
        self,
        farm_id: UUID,
        user_id: UUID,
    ) -> tuple[int, int, Decimal]:
        return 2, 1, Decimal("125.50")


class DemoSalesService:
    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def update_customer(
        self,
        farm_id: UUID,
        customer_id: UUID,
        payload: dict[str, object],
    ) -> None:
        raise BusinessRuleError(
            "The demo customer update failed.",
            error_code="demo_customer_update_failed",
        )


class DemoAlertsService:
    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def send_test_notification(
        self,
        farm_id: UUID,
        user_id: UUID,
        *,
        channel: str,
        destination: str,
    ) -> dict[str, object]:
        return {
            "id": uuid4(),
            "farm_id": farm_id,
            "user_id": user_id,
            "channel": channel,
            "status": "SENT",
        }


def test_commercial_wrapper_supports_finance_db_alias(
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    spec = CommercialAuditSpec(
        "tests.test_audit_commercial",
        "DemoFinanceService",
        "sync_receipts",
        "finance_demo",
        "SYNC",
        "Synchronized demo sales receipts.",
        "CashLedgerSync",
        result_labels=(
            "created_receipts",
            "reversed_receipts",
            "cash_balance",
        ),
    )
    service = DemoFinanceService(database_session)
    wrapped = commercial_audit_operation(spec)(DemoFinanceService.sync_receipts)

    token = set_audit_context(
        AuditRequestContext(
            request_id="stage17c2-finance-success",
            actor_user_id=auth_context["user"].id,
            actor_farm_id=auth_context["farm"].id,
            actor_username=auth_context["user"].username,
        )
    )
    try:
        result = wrapped(
            service,
            auth_context["farm"].id,
            auth_context["user"].id,
        )
    finally:
        reset_audit_context(token)

    assert result == (2, 1, Decimal("125.50"))

    item = database_session.scalar(
        select(AuditLog)
        .where(AuditLog.request_id == "stage17c2-finance-success")
        .order_by(AuditLog.occurred_at.desc())
    )

    assert item is not None
    assert item.outcome == AuditOutcome.SUCCESS.value
    assert item.after_values["created_receipts"] == 2
    assert item.after_values["reversed_receipts"] == 1


def test_commercial_wrapper_records_failure(
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    spec = CommercialAuditSpec(
        "tests.test_audit_commercial",
        "DemoSalesService",
        "update_customer",
        "sales_demo",
        "UPDATE",
        "Updated a demo customer.",
        "Customer",
        "customer_id",
    )
    service = DemoSalesService(database_session)
    wrapped = commercial_audit_operation(spec)(DemoSalesService.update_customer)
    customer_id = uuid4()

    token = set_audit_context(
        AuditRequestContext(
            request_id="stage17c2-sales-failure",
            actor_user_id=auth_context["user"].id,
            actor_farm_id=auth_context["farm"].id,
            actor_username=auth_context["user"].username,
        )
    )
    try:
        with pytest.raises(BusinessRuleError):
            wrapped(
                service,
                auth_context["farm"].id,
                customer_id,
                {"name": "Demo Customer"},
            )
    finally:
        reset_audit_context(token)

    item = database_session.scalar(
        select(AuditLog)
        .where(AuditLog.request_id == "stage17c2-sales-failure")
        .order_by(AuditLog.occurred_at.desc())
    )

    assert item is not None
    assert item.outcome == AuditOutcome.FAILURE.value
    assert item.resource_id == str(customer_id)
    assert item.error_code == ("demo_customer_update_failed")


def test_commercial_wrapper_excludes_destination_metadata(
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    spec = CommercialAuditSpec(
        "tests.test_audit_commercial",
        "DemoAlertsService",
        "send_test_notification",
        "alerts_demo",
        "PROCESS",
        "Sent a demo notification.",
        "NotificationDelivery",
        excluded_metadata_arguments=("destination",),
    )
    service = DemoAlertsService(database_session)
    wrapped = commercial_audit_operation(spec)(DemoAlertsService.send_test_notification)

    token = set_audit_context(
        AuditRequestContext(
            request_id="stage17c2-alert-success",
            actor_user_id=auth_context["user"].id,
            actor_farm_id=auth_context["farm"].id,
            actor_username=auth_context["user"].username,
        )
    )
    try:
        wrapped(
            service,
            auth_context["farm"].id,
            auth_context["user"].id,
            channel="EMAIL",
            destination="private@example.com",
        )
    finally:
        reset_audit_context(token)

    item = database_session.scalar(
        select(AuditLog)
        .where(AuditLog.request_id == "stage17c2-alert-success")
        .order_by(AuditLog.occurred_at.desc())
    )

    assert item is not None
    assert item.metadata_json is not None
    assert "destination" not in item.metadata_json
    assert "private@example.com" not in str(item.metadata_json)
