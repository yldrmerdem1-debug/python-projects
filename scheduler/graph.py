from __future__ import annotations

import heapq
from dataclasses import dataclass


class CycleError(ValueError):
    def __init__(self, cycle: list[str]) -> None:
        super().__init__("dependency cycle: " + " -> ".join(cycle))
        self.cycle = cycle


@dataclass(frozen=True)
class Task:
    name: str
    duration: float
    priority: int = 0  # when several tasks are ready, the highest priority goes first
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.duration < 0:
            raise ValueError(f"{self.name}: duration cannot be negative")


class TaskGraph:
    """Tasks with dependencies: a valid execution order, cycle detection and the critical path."""

    def __init__(self, tasks: list[Task] | None = None) -> None:
        self._tasks: dict[str, Task] = {}
        for task in tasks or []:
            self.add(task)

    def add(self, task: Task) -> None:
        if task.name in self._tasks:
            raise ValueError(f"duplicate task {task.name!r}")
        self._tasks[task.name] = task

    def __len__(self) -> int:
        return len(self._tasks)

    def _check_references(self) -> None:
        for task in self._tasks.values():
            missing = [d for d in task.depends_on if d not in self._tasks]
            if missing:
                raise KeyError(f"{task.name} depends on unknown task(s): {', '.join(missing)}")

    def find_cycle(self) -> list[str] | None:
        """One dependency cycle as a list of names (first == last), or None. Depth-first search."""
        self._check_references()
        unvisited, in_progress, done = 0, 1, 2
        state = dict.fromkeys(self._tasks, unvisited)
        path: list[str] = []

        def visit(name: str) -> list[str] | None:
            state[name] = in_progress
            path.append(name)
            for dep in self._tasks[name].depends_on:
                if state[dep] == in_progress:
                    return path[path.index(dep):] + [dep]
                if state[dep] == unvisited and (cycle := visit(dep)):
                    return cycle
            path.pop()
            state[name] = done
            return None

        for name in self._tasks:
            if state[name] == unvisited and (cycle := visit(name)):
                return cycle
        return None

    def execution_order(self) -> list[str]:
        """Kahn's algorithm with a heap: every task after its dependencies, highest priority first."""
        if cycle := self.find_cycle():
            raise CycleError(cycle)
        waiting = {name: len(task.depends_on) for name, task in self._tasks.items()}
        dependents: dict[str, list[str]] = {name: [] for name in self._tasks}
        for task in self._tasks.values():
            for dep in task.depends_on:
                dependents[dep].append(task.name)

        ready = [(-task.priority, task.name) for task in self._tasks.values() if not task.depends_on]
        heapq.heapify(ready)
        order: list[str] = []
        while ready:
            _, name = heapq.heappop(ready)
            order.append(name)
            for nxt in dependents[name]:
                waiting[nxt] -= 1
                if waiting[nxt] == 0:
                    heapq.heappush(ready, (-self._tasks[nxt].priority, nxt))
        return order

    def critical_path(self) -> tuple[float, list[str]]:
        """The longest chain of dependent work: the shortest possible total time with unlimited workers."""
        finish: dict[str, float] = {}
        came_from: dict[str, str | None] = {}
        for name in self.execution_order():
            task = self._tasks[name]
            start, previous = 0.0, None
            for dep in task.depends_on:
                if finish[dep] > start:
                    start, previous = finish[dep], dep
            finish[name] = start + task.duration
            came_from[name] = previous
        if not finish:
            return 0.0, []

        last = max(finish, key=finish.__getitem__)
        path = [last]
        while (previous := came_from[path[-1]]) is not None:
            path.append(previous)
        return finish[last], path[::-1]
