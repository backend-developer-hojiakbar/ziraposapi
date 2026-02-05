#!/usr/bin/env python
"""
Script to add initial expense types to the database
"""
import os
import sys
import django
import shortuuid

# Add the project directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_backend.settings')

django.setup()

from api.models import ExpenseType

def add_initial_expense_types():
    """Add some initial expense types to the database"""
    
    initial_expense_types = [
        {
            'name': 'ish_haqi',
            'display_name': 'Ish haqi'
        },
        {
            'name': 'elektrika',
            'display_name': 'Elektrik to\'lovi'
        },
        {
            'name': 'suv',
            'display_name': 'Suv to\'lovi'
        },
        {
            'name': 'gaz',
            'display_name': 'Gaz to\'lovi'
        },
        {
            'name': 'marketing',
            'display_name': 'Marketing sarfi'
        },
        {
            'name': 'arzonlashish',
            'display_name': 'Arzonlashish'
        },
        {
            'name': 'boshqa',
            'display_name': 'Boshqa sarflar'
        }
    ]
    
    for expense_type_data in initial_expense_types:
        # Check if expense type already exists
        existing = ExpenseType.objects.filter(name=expense_type_data['name']).first()
        if existing:
            print(f"Expense type already exists: {existing.display_name}")
            continue
            
        # Create new expense type with proper ID
        expense_type = ExpenseType.objects.create(
            id=f"exp_type_{shortuuid.random(length=8)}",
            name=expense_type_data['name'],
            display_name=expense_type_data['display_name']
        )
        
        print(f"Created expense type: {expense_type.display_name}")

if __name__ == "__main__":
    add_initial_expense_types()
    print("Initial expense types added successfully!")