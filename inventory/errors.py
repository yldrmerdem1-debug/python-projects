class InventoryError(Exception):
    """Base class for every inventory error, so callers can catch them all at once."""


class UnknownProductError(InventoryError):
    def __init__(self, sku: str) -> None:
        super().__init__(f"unknown product {sku!r}")
        self.sku = sku


class OutOfStockError(InventoryError):
    def __init__(self, sku: str, requested: int, available: int) -> None:
        super().__init__(f"{sku}: requested {requested}, only {available} in stock")
        self.sku = sku
        self.requested = requested
        self.available = available
