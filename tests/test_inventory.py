import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from inventory import (
    BulkDiscount,
    CategoryDiscount,
    DiscountPolicy,
    Inventory,
    InventoryError,
    OutOfStockError,
    Product,
    UnknownProductError,
)


def sample(pricing: DiscountPolicy | None = None) -> Inventory:
    inv = Inventory(pricing)
    inv.add_product(Product("KB-01", "Keyboard", Decimal("49.90"), "peripherals"), quantity=10, reorder_level=3)
    inv.add_product(Product("MS-01", "Mouse", 19.99, "peripherals"), quantity=2, reorder_level=5)
    inv.add_product(Product("CB-01", "USB cable", Decimal("4.50"), "clearance"), quantity=40)
    return inv


class ProductTest(unittest.TestCase):
    def test_float_price_is_stored_as_exact_decimal(self):
        self.assertEqual(Product("X-1", "x", 19.99).unit_price, Decimal("19.99"))

    def test_invalid_products_are_rejected(self):
        with self.assertRaises(ValueError):
            Product(" ", "blank sku", 1)
        with self.assertRaises(ValueError):
            Product("X-2", "negative", -1)


class InventoryTest(unittest.TestCase):
    def test_sell_reduces_stock_and_records_revenue(self):
        inv = sample()
        self.assertEqual(inv.sell("KB-01", 2), Decimal("99.80"))
        self.assertEqual(inv.item("KB-01").quantity, 8)
        self.assertEqual(inv.revenue(), Decimal("99.80"))

    def test_cannot_sell_more_than_in_stock(self):
        inv = sample()
        with self.assertRaises(OutOfStockError) as ctx:
            inv.sell("MS-01", 3)
        self.assertEqual(ctx.exception.available, 2)
        self.assertEqual(inv.item("MS-01").quantity, 2)  # nothing changed
        self.assertEqual(inv.sales, [])

    def test_unknown_and_duplicate_products(self):
        inv = sample()
        with self.assertRaises(UnknownProductError):
            inv.receive("NOPE", 1)
        with self.assertRaises(InventoryError):
            inv.add_product(Product("KB-01", "Another keyboard", 10))

    def test_low_stock_lists_emptiest_first(self):
        inv = sample()
        inv.sell("KB-01", 7)  # 3 left: at the reorder level
        self.assertEqual([item.product.sku for item in inv.low_stock()], ["MS-01", "KB-01"])
        inv.receive("MS-01", 10)
        self.assertEqual([item.product.sku for item in inv.low_stock()], ["KB-01"])

    def test_container_protocol(self):
        inv = sample()
        self.assertEqual(len(inv), 3)
        self.assertIn("CB-01", inv)
        self.assertEqual({item.product.sku for item in inv}, {"KB-01", "MS-01", "CB-01"})


class PricingTest(unittest.TestCase):
    def test_bulk_discount_starts_at_the_threshold(self):
        inv = sample(BulkDiscount(min_quantity=10, percent=15))
        self.assertEqual(inv.sell("CB-01", 9), Decimal("40.50"))
        self.assertEqual(inv.sell("CB-01", 10), Decimal("38.25"))

    def test_category_discount_only_hits_its_category(self):
        inv = sample(CategoryDiscount({"clearance": 50}))
        self.assertEqual(inv.sell("CB-01", 3), Decimal("6.75"))
        self.assertEqual(inv.sell("KB-01", 1), Decimal("49.90"))

    def test_policy_cannot_be_instantiated_without_discount(self):
        with self.assertRaises(TypeError):
            DiscountPolicy()

    def test_invalid_bulk_settings(self):
        with self.assertRaises(ValueError):
            BulkDiscount(min_quantity=0, percent=10)
        with self.assertRaises(ValueError):
            BulkDiscount(min_quantity=5, percent=120)


class PersistenceTest(unittest.TestCase):
    def test_save_and_load_round_trip(self):
        inv = sample()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stock.json"
            inv.save(path)
            loaded = Inventory.load(path)
        self.assertEqual(len(loaded), 3)
        self.assertEqual(loaded.total_value(), inv.total_value())
        self.assertEqual(loaded.item("KB-01").reorder_level, 3)
        self.assertEqual(loaded.item("MS-01").product.unit_price, Decimal("19.99"))


if __name__ == "__main__":
    unittest.main()
