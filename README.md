# Python Projects

![CI](https://github.com/yldrmerdem1-debug/python-projects/actions/workflows/ci.yml/badge.svg)

Three small Python packages built with the standard library only, each with unit tests.

| Package | What it covers |
|---|---|
| [`inventory`](inventory/) | Products, stock levels and sales: dataclasses (frozen and mutable), an abstract base class with interchangeable pricing policies (bulk and category discounts), a custom exception hierarchy, `Decimal` money, the container protocol (`len`, `in`, iteration), JSON save/load with a `classmethod` constructor |
| [`scheduler`](scheduler/) | Task dependency graph: execution order with Kahn's algorithm and a priority heap, cycle detection with depth-first search that reports the cycle, critical path (longest chain of dependent work) |
| [`textstats`](textstats/) | Word and sentence statistics streamed line by line: generators, regular expressions with Unicode letters, `collections.Counter`, `itertools.islice`, an `argparse` command line |

## Run the tests

Python 3.10 or newer, no dependencies:

```bash
python -m unittest -v
```

## Examples

```python
from decimal import Decimal
from inventory import BulkDiscount, Inventory, Product

shop = Inventory(pricing=BulkDiscount(min_quantity=10, percent=15))
shop.add_product(Product("CB-01", "USB cable", Decimal("4.50")), quantity=40, reorder_level=5)
shop.sell("CB-01", 10)   # Decimal('38.25')
shop.save("stock.json")
```

```python
from scheduler import Task, TaskGraph

plan = TaskGraph([
    Task("design", 3),
    Task("backend", 5, depends_on=("design",)),
    Task("frontend", 4, priority=1, depends_on=("design",)),
    Task("release", 1, depends_on=("backend", "frontend")),
])
plan.execution_order()   # ['design', 'frontend', 'backend', 'release']
plan.critical_path()     # (9.0, ['design', 'backend', 'release'])
```

```bash
python -m textstats article.txt --top 5
```
