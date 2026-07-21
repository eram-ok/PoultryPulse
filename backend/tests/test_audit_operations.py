from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.modules.audit.constants import AuditOutcome
from app.modules.audit.context import (
    AuditRequestContext,
    reset_audit_context,
    set_audit_context,
)
from app.modules.audit.models import AuditLog
from app.modules.audit.operational_registry import (
    OPERATIONAL_AUDIT_SPECS,
    install_operational_auditing,
)
from app.modules.audit.operations import (
    OperationAuditSpec,
    audit_operation,
    model_snapshot,
)
from app.modules.feed.models import FeedItem


def test_operational_registry_is_complete() -> None:
    installed = install_operational_auditing()

    assert installed >= 0
    assert len(OPERATIONAL_AUDIT_SPECS) == 35

    for spec in OPERATIONAL_AUDIT_SPECS:
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


def test_model_snapshot_uses_mapped_columns() -> None:
    item = FeedItem(
        id=uuid4(),
        farm_id=uuid4(),
        feed_code="LAYERS-MASH",
        name="Layers Mash",
        category="LAYERS",
        reorder_level_kg=25,
        is_active=True,
    )

    snapshot = model_snapshot(item)

    assert snapshot is not None
    assert snapshot["feed_code"] == "LAYERS-MASH"
    assert snapshot["name"] == "Layers Mash"
    assert "farm" not in snapshot


class DemoOperationalService:
    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session

    def succeed(
        self,
        farm_id,
        created_by,
        payload,
    ):
        return {
            "id": uuid4(),
            "farm_id": farm_id,
            "name": payload["name"],
        }

    def fail(
        self,
        farm_id,
        created_by,
        payload,
    ):
        raise BusinessRuleError(
            "The demo operation failed.",
            error_code="demo_operation_failed",
        )


def test_operational_decorator_records_success(
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    spec = OperationAuditSpec(
        "tests.test_audit_operations",
        "DemoOperationalService",
        "succeed",
        "demo",
        "CREATE",
        "Created a demo record.",
        "DemoRecord",
    )
    service = DemoOperationalService(database_session)
    wrapped = audit_operation(spec)(DemoOperationalService.succeed)

    token = set_audit_context(
        AuditRequestContext(
            request_id="stage17c1-success",
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
            {"name": "Demo"},
        )
    finally:
        reset_audit_context(token)

    item = database_session.scalar(
        select(AuditLog)
        .where(AuditLog.request_id == "stage17c1-success")
        .order_by(AuditLog.occurred_at.desc())
    )

    assert item is not None
    assert item.outcome == AuditOutcome.SUCCESS.value
    assert item.resource_id == str(result["id"])
    assert item.after_values["name"] == "Demo"


def test_operational_decorator_records_failure(
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    spec = OperationAuditSpec(
        "tests.test_audit_operations",
        "DemoOperationalService",
        "fail",
        "demo",
        "CREATE",
        "Created a demo record.",
        "DemoRecord",
    )
    service = DemoOperationalService(database_session)
    wrapped = audit_operation(spec)(DemoOperationalService.fail)

    token = set_audit_context(
        AuditRequestContext(
            request_id="stage17c1-failure",
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
                auth_context["user"].id,
                {"name": "Demo"},
            )
    finally:
        reset_audit_context(token)

    item = database_session.scalar(
        select(AuditLog)
        .where(AuditLog.request_id == "stage17c1-failure")
        .order_by(AuditLog.occurred_at.desc())
    )

    assert item is not None
    assert item.outcome == AuditOutcome.FAILURE.value
    assert item.error_code == "demo_operation_failed"
