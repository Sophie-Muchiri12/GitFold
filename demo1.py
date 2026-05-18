# demo_project.py
# A simple task manager — use this to demo Gitfold

from datetime import datetime


class Task:
    def __init__(self, title: str, priority: str = "medium", due_date: str = None):
        self.title = title
        self.priority = priority
        self.completed = False
        self.created_at = datetime.now()
        self.due_date = due_date  # Format: "YYYY-MM-DD"

    def complete(self):
        self.completed = True

    def is_overdue(self):
        """Check if the task is overdue based on due date."""
        if not self.due_date or self.completed:
            return False
        due = datetime.strptime(self.due_date, "%Y-%m-%d")
        return datetime.now() > due

    def __repr__(self):
        status = "✔" if self.completed else "○"
        due = f" | due: {self.due_date}" if self.due_date else ""
        overdue = " ⚠ OVERDUE" if self.is_overdue() else ""
        return f"[{status}] [{self.priority.upper()}] {self.title}{due}{overdue}"


class TaskManager:
    def __init__(self):
        self.tasks = []

    def add_task(self, title: str, priority: str = "medium", due_date: str = None):
        """Add a new task to the manager."""
        task = Task(title, priority, due_date)
        self.tasks.append(task)
        return task

    def get_overdue(self):
        """Return all overdue incomplete tasks."""
        return [t for t in self.tasks if t.is_overdue()]

    def complete_task(self, title: str):
        """Mark a task as completed by title."""
        for task in self.tasks:
            if task.title.lower() == title.lower():
                task.complete()
                return True
        return False

    def get_pending(self):
        """Return all incomplete tasks."""
        return [t for t in self.tasks if not t.completed]

    def get_by_priority(self, priority: str):
        """Return tasks filtered by priority level."""
        return [t for t in self.tasks if t.priority == priority]

    def summary(self):
        """Print a summary of all tasks."""
        total = len(self.tasks)
        done = len([t for t in self.tasks if t.completed])
        print(f"\n── Task Summary ──")
        print(f"  Total:     {total}")
        print(f"  Completed: {done}")
        print(f"  Pending:   {total - done}")
        print()
        for task in self.tasks:
            print(f"  {task}")
        print()


def load_sample_tasks(manager: TaskManager):
    """Load a set of sample tasks into the manager."""
    manager.add_task("Set up project structure", priority="high", due_date="2026-01-01")
    manager.add_task("Write unit tests", priority="high", due_date="2026-05-20")
    manager.add_task("Update README", priority="medium", due_date="2026-06-01")
    manager.add_task("Refactor database layer", priority="medium", due_date="2026-05-15")
    manager.add_task("Add dark mode support", priority="low", due_date="2026-07-01")


if __name__ == "__main__":
    manager = TaskManager()
    load_sample_tasks(manager)

    manager.complete_task("Set up project structure")
    manager.complete_task("Update README")

    manager.summary()

    print("High priority pending tasks:")
    for task in manager.get_by_priority("high"):
        if not task.completed:
            print(f"  {task}")

    print("\nOverdue tasks:")
    overdue = manager.get_overdue()
    if overdue:
        for task in overdue:
            print(f"  {task}")
    else:
        print("  None — you're all caught up!")