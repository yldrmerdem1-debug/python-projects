from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from .models import Product

CENT = Decimal("0.01")


class DiscountPolicy(ABC):
    """Decides how much comes off an order line. Subclasses only implement discount()."""

    @abstractmethod
    def discount(self, product: Product, quantity: int) -> Decimal:
        """Return the discount amount (not the rate) for `quantity` units of `product`."""

    def line_total(self, product: Product, quantity: int) -> Decimal:
        gross = product.unit_price * quantity
        return (gross - self.discount(product, quantity)).quantize(CENT)


class NoDiscount(DiscountPolicy):
    def discount(self, product: Product, quantity: int) -> Decimal:
        return Decimal(0)


class BulkDiscount(DiscountPolicy):
    """`percent` off the whole line once it reaches `min_quantity` units."""

    def __init__(self, min_quantity: int, percent: Decimal | int) -> None:
        if min_quantity < 1 or not 0 <= Decimal(percent) <= 100:
            raise ValueError("min_quantity must be at least 1 and percent between 0 and 100")
        self.min_quantity = min_quantity
        self.rate = Decimal(percent) / 100

    def discount(self, product: Product, quantity: int) -> Decimal:
        if quantity < self.min_quantity:
            return Decimal(0)
        return product.unit_price * quantity * self.rate


class CategoryDiscount(DiscountPolicy):
    """A rate per category, e.g. CategoryDiscount({"clearance": 50})."""

    def __init__(self, percent_by_category: dict[str, Decimal | int]) -> None:
        self.rates = {category: Decimal(p) / 100 for category, p in percent_by_category.items()}

    def discount(self, product: Product, quantity: int) -> Decimal:
        return product.unit_price * quantity * self.rates.get(product.category, Decimal(0))
