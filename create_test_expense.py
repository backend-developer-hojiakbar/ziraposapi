#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_backend.settings')
django.setup()

from api.models import Expense, ExpenseType, Employee

# Get test data
expense_type = ExpenseType.objects.first()
employee = Employee.objects.first()

print(f"Using expense type: {expense_type.display_name}")
print(f"Using employee: {employee.name}")

# Create test expense
expense = Expense.objects.create(
    id=f'exp_test_{django.utils.timezone.now().strftime("%Y%m%d%H%M%S")}',
    amount=50000.00,
    type=expense_type,
    description='Test xarajat',
    employee=employee
)

print(f"Created expense: {expense.id} - {expense.amount} UZS")
