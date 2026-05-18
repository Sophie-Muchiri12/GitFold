# expense_tracker.py
# A personal expense tracker with budgeting and reporting

from datetime import datetime
from collections import defaultdict


CATEGORIES = ["food", "transport", "utilities", "entertainment", "health", "other"]


class Expense:
    def __init__(self, amount: float, category: str, description: str):
        if category not in CATEGORIES:
            raise ValueError(f"Invalid category. Choose from: {', '.join(CATEGORIES)}")
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        self.amount = amount
        self.category = category
        self.description = description
        self.date = datetime.now().strftime("%Y-%m-%d")

    def __repr__(self):
        return f"[{self.date}] {self.category.upper():15} ${self.amount:.2f} — {self.description}"


class ExpenseTracker:
    def __init__(self, monthly_budget: float = 0.0):
        self.expenses = []
        self.monthly_budget = monthly_budget

    def add_expense(self, amount: float, category: str, description: str):
        """Record a new expense."""
        expense = Expense(amount, category, description)
        self.expenses.append(expense)
        return expense

    def set_budget(self, amount: float):
        """Set or update the monthly budget."""
        if amount <= 0:
            raise ValueError("Budget must be greater than zero.")
        self.monthly_budget = amount

    def total_spent(self):
        """Return the total amount spent across all expenses."""
        return sum(e.amount for e in self.expenses)

    def spent_by_category(self):
        """Return a dictionary of total spending per category."""
        totals = defaultdict(float)
        for expense in self.expenses:
            totals[expense.category] += expense.amount
        return dict(totals)

    def remaining_budget(self):
        """Return how much budget is left for the month."""
        if self.monthly_budget <= 0:
            return None
        return self.monthly_budget - self.total_spent()

    def is_over_budget(self):
        """Check if spending has exceeded the monthly budget."""
        if self.monthly_budget <= 0:
            return False
        return self.total_spent() > self.monthly_budget

    def get_expenses_by_category(self, category: str):
        """Return all expenses for a specific category."""
        return [e for e in self.expenses if e.category == category]

    def largest_expense(self):
        """Return the single largest expense recorded."""
        if not self.expenses:
            return None
        return max(self.expenses, key=lambda e: e.amount)

    def summary(self):
        """Print a full financial summary report."""
        print("\n── Expense Summary ──────────────────────────")
        print(f"  Total spent:    ${self.total_spent():.2f}")

        if self.monthly_budget > 0:
            remaining = self.remaining_budget()
            status = "⚠ OVER BUDGET" if self.is_over_budget() else "✔ within budget"
            print(f"  Monthly budget: ${self.monthly_budget:.2f}")
            print(f"  Remaining:      ${remaining:.2f}  {status}")

        print("\n  Spending by category:")
        for category, total in sorted(self.spent_by_category().items()):
            bar = "█" * int(total / 10)
            print(f"    {category:15} ${total:.2f}  {bar}")

        largest = self.largest_expense()
        if largest:
            print(f"\n  Largest expense: ${largest.amount:.2f} — {largest.description}")

        print("─────────────────────────────────────────────\n")


def load_sample_expenses(tracker: ExpenseTracker):
    """Load sample expenses for demonstration."""
    tracker.add_expense(45.00, "food", "Weekly groceries")
    tracker.add_expense(12.50, "transport", "Uber to office")
    tracker.add_expense(9.99, "entertainment", "Netflix subscription")
    tracker.add_expense(85.00, "utilities", "Electricity bill")
    tracker.add_expense(30.00, "food", "Team lunch")
    tracker.add_expense(15.00, "health", "Vitamins")
    tracker.add_expense(200.00, "health", "Doctor appointment")
    tracker.add_expense(20.00, "transport", "Matatu fare for the week")
    tracker.add_expense(5.50, "food", "Coffee")
    tracker.add_expense(60.00, "entertainment", "Concert ticket")


if __name__ == "__main__":
    tracker = ExpenseTracker(monthly_budget=500.00)
    load_sample_expenses(tracker)

    tracker.summary()

    print("Food expenses:")
    for expense in tracker.get_expenses_by_category("food"):
        print(f"  {expense}")