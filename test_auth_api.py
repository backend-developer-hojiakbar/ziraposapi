#!/usr/bin/env python
import os
import django
import json
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_backend.settings')
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Employee

# Get admin user
admin_user = Employee.objects.get(phone='1234')

# Generate token
refresh = RefreshToken.for_user(admin_user)
access_token = str(refresh.access_token)

print(f"Access token: {access_token}")

# Test API with token
base_url = "http://127.0.0.1:8000/api"
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# Test initial data endpoint
try:
    response = requests.get(f"{base_url}/data/initial/", headers=headers)
    print(f"\nInitial data status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Expense types count: {len(data.get('expenseTypes', []))}")
        print(f"Expenses count: {len(data.get('expenses', []))}")
        print(f"Employees count: {len(data.get('employees', []))}")
        
        # Show expense types
        print("\nExpense types:")
        for et in data.get('expenseTypes', []):
            print(f"  - {et['display_name']} (ID: {et['id']})")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Request error: {e}")
