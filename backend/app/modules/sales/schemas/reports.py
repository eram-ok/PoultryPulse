from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class SalesSummaryResponse(BaseModel):
    as_of_date: date
    active_customers: int
    draft_sales: int
    confirmed_sales: int
    paid_sales: int
    outstanding_receivables: Decimal
    gross_sales_value: Decimal
    posted_payments: Decimal
    posted_returns: Decimal
    inventory_by_grade: dict[str, int]
