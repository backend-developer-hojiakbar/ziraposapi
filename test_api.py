#!/usr/bin/env python
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_backend.settings')
django.setup()

from api.models import ExpenseType, Expense, Employee
from api.serializers import ExpenseTypeSerializer, ExpenseSerializer

# Test expense types
expense_types = ExpenseType.objects.all()
print(f"Expense types count: {expense_types.count()}")
expense_types_data = ExpenseTypeSerializer(expense_types, many=True).data
print(f"Expense types data: {json.dumps(expense_types_data, indent=2, ensure_ascii=False)}")

# Test expenses
expenses = Expense.objects.select_related('type', 'employee').all()
print(f"\nExpenses count: {expenses.count()}")
expenses_data = ExpenseSerializer(expenses, many=True).data
print(f"Expenses data: {json.dumps(expenses_data, indent=2, ensure_ascii=False)}")

# Test employees
employees = Employee.objects.all()
print(f"\nEmployees count: {employees.count()}")
