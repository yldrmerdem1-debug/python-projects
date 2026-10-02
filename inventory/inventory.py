from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from .errors import InventoryError, OutOfStockError, UnknownProductError
from .models import Product
from .pricing import DiscountPolicy, NoDiscount


@dataclass
class StockItem:
    product: Product
    quantity: int = 0
    reorder_level: int = 0

    @property
    def needs_reorder(self) -> bool:
        return self.quantity <= self.reorder_level

    @property
    def value(self) -> Decimal:
        return self.product.unit_price * self.quantity


class Inventory:
    """Stock per SKU. Sales are priced by a DiscountPolicy and recorded for revenue reports."""

    def __init__(self, pricing: DiscountPolicy | None = None) -> None:
        self._items: dict[str, StockItem] = {}
        self.pricing = pricing or NoDiscount()
        self.sales: list[tuple[str, int, Decimal]] = []

    # container protocol: len(inv), "SKU" in inv, for item in inv
    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, sku: object) -> bool:
        return sku in self._items

    def __iter__(self) -> Iterator[StockItem]:
        return iter(self._items.values())

    def add_product(self, product: Product, quantity: int = 0, reorder_level: int = 0) -> StockItem:
        if product.sku in self._items:
            raise InventoryError(f"{product.sku} already exists")
        if quantity < 0 or reorder_level < 0:
            raise ValueError("quantity and reorder_level cannot be negative")
        item = StockItem(product, quantity, reorder_level)
        self._items[product.sku] = item
        return item

    def item(self, sku: str) -> StockItem:
        try:
            return self._items[sku]
        except KeyError:
            raise UnknownProductError(sku) from None

    def receive(self, sku: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("received quantity must be positive")
        self.item(sku).quantity += quantity

    def sell(self, sku: str, quantity: int) -> Decimal:
        """Take `quantity` units out of stock and return the amount charged after discounts."""
        if quantity <= 0:
            raise ValueError("sold quantity must be positive")
        item = self.item(sku)
        if quantity > item.quantity:
            raise OutOfStockError(sku, quantity, item.quantity)
        total = self.pricing.line_total(item.product, quantity)
        item.quantity -= quantity
        self.sales.append((sku, quantity, total))
        return total

    def low_stock(self) -> list[StockItem]:
        """Items at or below their reorder level, emptiest first."""
        return sorted((item for item in self if item.needs_reorder), key=lambda item: item.quantity)

    def total_value(self) -> Decimal:
        return sum((item.value for item in self), Decimal(0))

    def revenue(self) -> Decimal:
        return sum((total for _, _, total in self.sales), Decimal(0))

    def save(self, path: str | Path) -> None:
        rows = [
            {
                "sku": item.product.sku,
                "name": item.product.name,
                "unit_price": str(item.product.unit_price),  # string keeps the exact decimal
                "category": item.product.category,
                "quantity": item.quantity,
                "reorder_level": item.reorder_level,
            }
            for item in self
        ]
        Path(path).write_text(json.dumps(rows, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path, pricing: DiscountPolicy | None = None) -> Inventory:
        inventory = cls(pricing)
        for row in json.loads(Path(path).read_text(encoding="utf-8")):
            product = Product(row["sku"], row["name"], Decimal(row["unit_price"]), row.get("category", "general"))
            inventory.add_product(product, row["quantity"], row.get("reorder_level", 0))
        return inventory
