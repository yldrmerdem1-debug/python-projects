import unittest

from scheduler import CycleError, Task, TaskGraph


def release_plan() -> TaskGraph:
    return TaskGraph(
        [
            Task("design", 3),
            Task("backend", 5, depends_on=("design",)),
            Task("frontend", 4, priority=1, depends_on=("design",)),
            Task("docs", 1, priority=5),
            Task("tests", 2, depends_on=("backend", "frontend")),
            Task("release", 1, depends_on=("tests", "docs")),
        ]
    )


class TaskGraphTest(unittest.TestCase):
    def test_order_respects_dependencies_then_priority(self):
        self.assertEqual(
            release_plan().execution_order(),
            ["docs", "design", "frontend", "backend", "tests", "release"],
        )

    def test_critical_path(self):
        total, path = release_plan().critical_path()
        self.assertEqual(total, 11)
        self.assertEqual(path, ["design", "backend", "tests", "release"])

    def test_cycle_is_reported_with_its_path(self):
        graph = TaskGraph(
            [
                Task("a", 1, depends_on=("c",)),
                Task("b", 1, depends_on=("a",)),
                Task("c", 1, depends_on=("b",)),
            ]
        )
        with self.assertRaises(CycleError) as ctx:
            graph.execution_order()
        self.assertEqual(ctx.exception.cycle, ["a", "c", "b", "a"])

    def test_unknown_dependency(self):
        with self.assertRaises(KeyError):
            TaskGraph([Task("a", 1, depends_on=("ghost",))]).execution_order()

    def test_duplicates_and_negative_durations_are_rejected(self):
        graph = release_plan()
        with self.assertRaises(ValueError):
            graph.add(Task("docs", 1))
        with self.assertRaises(ValueError):
            Task("x", -1)

    def test_empty_graph(self):
        self.assertEqual(TaskGraph().execution_order(), [])
        self.assertEqual(TaskGraph().critical_path(), (0.0, []))


if __name__ == "__main__":
    unittest.main()
