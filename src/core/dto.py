from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import QuerySet


@dataclass
class UsageBreakdown:
    item_name: str
    percentage: int


@dataclass
class IngredientBalance:
    name: str
    ordered: Decimal
    used: Decimal
    remaining: Decimal
    unit: str
    breakdown: list[UsageBreakdown] = field(default_factory=list)


@dataclass
class HomeContext:
    recent_orders: QuerySet
    recent_sales: QuerySet


@dataclass
class IngredientsContext:
    ingredients: QuerySet
    past_orders: QuerySet
    today: str


@dataclass
class SalesContext:
    items: QuerySet
    past_sales: QuerySet
    today: str


@dataclass
class ReportContext:
    today: str
    ing_start_date: str
    ing_end_date: str
    sales_start_date: str
    sales_end_date: str
    sales: QuerySet
    total_revenue: Decimal
    orders: QuerySet
    total_ingredient_cost: Decimal
    ingredient_balance: list[IngredientBalance]
    profit: Decimal
    has_report: bool = True
