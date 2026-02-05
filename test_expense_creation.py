#!/usr/bin/env python
import os
import django
import json
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_backend.settings')
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Employee, ExpenseType

# Get admin user and create token
admin_user = Employee.objects.get(phone='1234')
refresh = RefreshToken.for_user(admin_user)
access_token = str(refresh.access_token)

# Get expense type and employee
expense_type = ExpenseType.objects.first()
employee = Employee.objects.first()

# Test expense creation
base_url = "http://127.0.0.1:8000/api"
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

expense_data = {
    'amount': 75000.00,
    'typeId': expense_type.id,
    'description': 'API orqali test xarajat',
    'employeeId': employee.id
}

try:
    response = requests.post(f"{base_url}/expenses/", 
                           json=expense_data, 
                           headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 201:
        print("✅ Xarajat muvaffaqiyatli yaratildi!")
        data = response.json()
        print(f"ID: {data.get('id')}")
        print(f"Amount: {data.get('amount')}")
        print(f"Type: {data.get('type', {}).get('display_name')}")
    else:
        print("❌ Xarajat yaratishda xatolik!")
        
except Exception as e:
    print(f"Request error: {e}")
