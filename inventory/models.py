from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Product:
    """A sellable item. Prices are Decimal so totals never pick up float rounding errors."""

    sku: str
    name: str
    unit_price: Decimal
    category: str = "general"

    def __post_init__(self) -> None:
        if not self.sku.strip():
            raise ValueError("sku must not be empty")
        if not isinstance(self.unit_price, Decimal):
            # Accept 19.99 or "19.99" but store the exact decimal value.
            object.__setattr__(self, "unit_price", Decimal(str(self.unit_price)))
        if self.unit_price < 0:
            raise ValueError(f"{self.sku}: price cannot be negative")
