#!/bin/bash
# Complete API Workflow Test for IST Africa Procure-to-Pay System
# This script demonstrates the full procurement workflow including authentication

API_BASE="https://procure-to-pay.onrender.com"
echo "🚀 Testing IST Africa Procure-to-Pay API Workflow"
echo "=================================================="

# Test 1: Check API is responding
echo -e "\n1️⃣ Testing API Root Endpoint..."
curl -s "$API_BASE/" | jq .

# Test 2: Try to access protected endpoint without auth (should fail)
echo -e "\n2️⃣ Testing Protected Endpoint (should require auth)..."
response=$(curl -s "$API_BASE/api/procurement/requests/")
echo "$response"

# Test 3: Create demo data via admin (we'll use the management command after deployment)
echo -e "\n3️⃣ Demo data should be created via: python manage.py create_demo_data"
echo "Demo users: staff1/staff123, approver1/approver123, approver2/approver123"

# Test 4: Authenticate as staff user
echo -e "\n4️⃣ Authenticating as staff user (staff1/staff123)..."
auth_response=$(curl -s -X POST "$API_BASE/api/token/" \
  -H "Content-Type: application/json" \
  -d '{"username": "staff1", "password": "staff123"}')

if echo "$auth_response" | jq -e .access > /dev/null 2>&1; then
    TOKEN=$(echo "$auth_response" | jq -r .access)
    echo "✅ Authentication successful! Token obtained."
    
    # Test 5: Access protected endpoint with token
    echo -e "\n5️⃣ Accessing procurement requests with authentication..."
    curl -s "$API_BASE/api/procurement/requests/" \
      -H "Authorization: Bearer $TOKEN" | jq .
    
    # Test 6: Create a new procurement request
    echo -e "\n6️⃣ Creating new procurement request..."
    new_request=$(curl -s -X POST "$API_BASE/api/procurement/requests/" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "title": "Test Procurement Request", 
        "description": "API workflow test request",
        "amount": "299.99"
      }')
    
    echo "$new_request" | jq .
    
else
    echo "❌ Authentication failed. Response: $auth_response"
    echo "Note: Demo data needs to be created first with: python manage.py create_demo_data"
fi

echo -e "\n🎯 API Workflow Test Complete!"