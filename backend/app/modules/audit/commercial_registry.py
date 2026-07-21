from __future__ import annotations

from importlib import import_module

from app.modules.audit.commercial_operations import (
    CommercialAuditSpec,
    commercial_audit_operation,
)
from app.modules.audit.operations import BeforeLoader


COMMERCIAL_AUDIT_SPECS = (
    # Sales and customer management.
    CommercialAuditSpec(
        "app.modules.sales.service",
        "SalesService",
        "create_customer",
        "sales",
        "CREATE",
        "Created a customer.",
        "Customer",
        static_metadata={
            "linked_effect": ("customer ledger opening balance may be created")
        },
    ),
    CommercialAuditSpec(
        "app.modules.sales.service",
        "SalesService",
        "update_customer",
        "sales",
        "UPDATE",
        "Updated a customer.",
        "Customer",
        "customer_id",
        BeforeLoader(
            "_get_customer",
            ("farm_id", "customer_id"),
        ),
    ),
    CommercialAuditSpec(
        "app.modules.sales.service",
        "SalesService",
        "create_sale",
        "sales",
        "CREATE",
        "Created a sale.",
        "Sale",
    ),
    CommercialAuditSpec(
        "app.modules.sales.service",
        "SalesService",
        "update_sale",
        "sales",
        "UPDATE",
        "Updated a draft sale.",
        "Sale",
        "sale_id",
        BeforeLoader(
            "_get_sale",
            ("farm_id", "sale_id"),
        ),
    ),
    CommercialAuditSpec(
        "app.modules.sales.service",
        "SalesService",
        "confirm_sale",
        "sales",
        "CONFIRM",
        "Confirmed a sale.",
        "Sale",
        "sale_id",
        BeforeLoader(
            "_get_sale",
            ("farm_id", "sale_id"),
        ),
        static_metadata={
            "linked_effect": ("egg inventory and customer ledger updated")
        },
    ),
    CommercialAuditSpec(
        "app.modules.sales.service",
        "SalesService",
        "cancel_sale",
        "sales",
        "CANCEL",
        "Cancelled a sale.",
        "Sale",
        "sale_id",
        BeforeLoader(
            "_get_sale",
            ("farm_id", "sale_id"),
        ),
        static_metadata={
            "linked_effect": ("sale inventory and customer ledger may be reversed")
        },
    ),
    CommercialAuditSpec(
        "app.modules.sales.service",
        "SalesService",
        "record_payment",
        "sales",
        "CREATE",
        "Recorded a customer payment.",
        "SalePayment",
        static_metadata={"linked_effect": ("sale balance and customer ledger updated")},
    ),
    CommercialAuditSpec(
        "app.modules.sales.service",
        "SalesService",
        "reverse_payment",
        "sales",
        "REVERSE",
        "Reversed a customer payment.",
        "SalePayment",
        "payment_id",
        BeforeLoader(
            "_get_payment",
            ("farm_id", "payment_id"),
        ),
        static_metadata={
            "linked_effect": ("sale balance and customer ledger restored")
        },
    ),
    CommercialAuditSpec(
        "app.modules.sales.service",
        "SalesService",
        "create_return",
        "sales",
        "CREATE",
        "Recorded a sale return.",
        "SaleReturn",
        static_metadata={
            "linked_effect": ("egg inventory and customer ledger updated")
        },
    ),
    CommercialAuditSpec(
        "app.modules.sales.service",
        "SalesService",
        "reverse_return",
        "sales",
        "REVERSE",
        "Reversed a sale return.",
        "SaleReturn",
        "return_id",
        BeforeLoader(
            "_get_return",
            ("farm_id", "return_id"),
        ),
        static_metadata={
            "linked_effect": ("return inventory and customer ledger restored")
        },
    ),
    # Finance and cash management.
    CommercialAuditSpec(
        "app.modules.finance.service",
        "FinanceService",
        "create_category",
        "finance",
        "CREATE",
        "Created an expense category.",
        "ExpenseCategory",
    ),
    CommercialAuditSpec(
        "app.modules.finance.service",
        "FinanceService",
        "update_category",
        "finance",
        "UPDATE",
        "Updated an expense category.",
        "ExpenseCategory",
        "category_id",
        BeforeLoader(
            "category",
            ("farm_id", "category_id"),
        ),
    ),
    CommercialAuditSpec(
        "app.modules.finance.service",
        "FinanceService",
        "create_expense",
        "finance",
        "CREATE",
        "Recorded an expense.",
        "Expense",
        static_metadata={"linked_effect": "cash ledger outflow created"},
    ),
    CommercialAuditSpec(
        "app.modules.finance.service",
        "FinanceService",
        "void_expense",
        "finance",
        "VOID",
        "Voided an expense.",
        "Expense",
        "expense_id",
        BeforeLoader(
            "expense",
            ("farm_id", "expense_id"),
        ),
        static_metadata={"linked_effect": ("cash ledger reversal created")},
    ),
    CommercialAuditSpec(
        "app.modules.finance.service",
        "FinanceService",
        "create_bill",
        "finance",
        "CREATE",
        "Recorded a supplier bill.",
        "SupplierBill",
    ),
    CommercialAuditSpec(
        "app.modules.finance.service",
        "FinanceService",
        "void_bill",
        "finance",
        "VOID",
        "Voided a supplier bill.",
        "SupplierBill",
        "bill_id",
        BeforeLoader(
            "bill",
            ("farm_id", "bill_id"),
        ),
    ),
    CommercialAuditSpec(
        "app.modules.finance.service",
        "FinanceService",
        "record_payment",
        "finance",
        "CREATE",
        "Recorded a supplier payment.",
        "SupplierBillPayment",
        static_metadata={
            "linked_effect": ("supplier bill balance and cash ledger updated")
        },
    ),
    CommercialAuditSpec(
        "app.modules.finance.service",
        "FinanceService",
        "reverse_payment",
        "finance",
        "REVERSE",
        "Reversed a supplier payment.",
        "SupplierBillPayment",
        "payment_id",
        BeforeLoader(
            "payment",
            ("farm_id", "payment_id"),
        ),
        static_metadata={
            "linked_effect": ("supplier bill balance and cash ledger restored")
        },
    ),
    CommercialAuditSpec(
        "app.modules.finance.service",
        "FinanceService",
        "cash_adjustment",
        "finance",
        "CREATE",
        "Recorded a cash-ledger adjustment.",
        "CashLedgerEntry",
    ),
    CommercialAuditSpec(
        "app.modules.finance.service",
        "FinanceService",
        "sync_receipts",
        "finance",
        "SYNC",
        "Synchronized sales receipts into the cash ledger.",
        "CashLedgerSync",
        result_labels=(
            "created_receipts",
            "reversed_receipts",
            "cash_balance",
        ),
        static_metadata={
            "linked_effect": ("cash ledger entries created from sales payments")
        },
    ),
    # Alerts and notification delivery.
    CommercialAuditSpec(
        "app.modules.alerts.service",
        "AlertsService",
        "refresh",
        "alerts",
        "SYNC",
        "Refreshed operational alerts.",
        "AlertRefreshRun",
    ),
    CommercialAuditSpec(
        "app.modules.alerts.service",
        "AlertsService",
        "process_deliveries",
        "alerts",
        "PROCESS",
        "Processed pending notification deliveries.",
        "NotificationDeliveryBatch",
    ),
    CommercialAuditSpec(
        "app.modules.alerts.service",
        "AlertsService",
        "retry_delivery",
        "alerts",
        "PROCESS",
        "Retried a notification delivery.",
        "NotificationDelivery",
        "delivery_id",
        BeforeLoader(
            "_delivery",
            ("farm_id", "delivery_id"),
        ),
    ),
    CommercialAuditSpec(
        "app.modules.alerts.service",
        "AlertsService",
        "mark_read",
        "alerts",
        "UPDATE",
        "Updated an alert read state.",
        "AlertUserState",
        "alert_id",
        snapshot_result=False,
    ),
    CommercialAuditSpec(
        "app.modules.alerts.service",
        "AlertsService",
        "dismiss",
        "alerts",
        "UPDATE",
        "Updated an alert dismissal state.",
        "AlertUserState",
        "alert_id",
        snapshot_result=False,
    ),
    CommercialAuditSpec(
        "app.modules.alerts.service",
        "AlertsService",
        "assign",
        "alerts",
        "ASSIGN",
        "Assigned an operational alert.",
        "OperationalAlert",
        "alert_id",
        BeforeLoader(
            "_alert",
            ("farm_id", "alert_id"),
        ),
    ),
    CommercialAuditSpec(
        "app.modules.alerts.service",
        "AlertsService",
        "acknowledge",
        "alerts",
        "CONFIRM",
        "Acknowledged an operational alert.",
        "OperationalAlert",
        "alert_id",
        BeforeLoader(
            "_alert",
            ("farm_id", "alert_id"),
        ),
    ),
    CommercialAuditSpec(
        "app.modules.alerts.service",
        "AlertsService",
        "resolve",
        "alerts",
        "RESOLVE",
        "Resolved an operational alert.",
        "OperationalAlert",
        "alert_id",
        BeforeLoader(
            "_alert",
            ("farm_id", "alert_id"),
        ),
    ),
    CommercialAuditSpec(
        "app.modules.alerts.service",
        "AlertsService",
        "reopen",
        "alerts",
        "REOPEN",
        "Reopened an operational alert.",
        "OperationalAlert",
        "alert_id",
        BeforeLoader(
            "_alert",
            ("farm_id", "alert_id"),
        ),
    ),
    CommercialAuditSpec(
        "app.modules.alerts.service",
        "AlertsService",
        "upsert_preference",
        "alerts",
        "UPDATE",
        "Saved a notification preference.",
        "NotificationPreference",
        before_loader=BeforeLoader(
            "repository.preference",
            (
                "farm_id",
                "user_id",
                "alert_type",
                "channel",
            ),
        ),
    ),
    CommercialAuditSpec(
        "app.modules.alerts.service",
        "AlertsService",
        "send_test_notification",
        "alerts",
        "PROCESS",
        "Sent a test notification.",
        "NotificationDelivery",
        excluded_metadata_arguments=("destination",),
    ),
)


_INSTALLED = False


def install_commercial_auditing() -> int:
    global _INSTALLED

    if _INSTALLED:
        return 0

    installed = 0

    for spec in COMMERCIAL_AUDIT_SPECS:
        module = import_module(spec.module_path)
        service_class = getattr(
            module,
            spec.class_name,
        )
        operation = getattr(
            service_class,
            spec.method_name,
        )

        if getattr(
            operation,
            "__poultrypulse_audit_wrapped__",
            False,
        ):
            continue

        setattr(
            service_class,
            spec.method_name,
            commercial_audit_operation(spec)(operation),
        )
        installed += 1

    _INSTALLED = True
    return installed
