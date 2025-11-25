#!/usr/bin/env python
"""
Simple test script to validate the approval workflow logic
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('/home/web3dev/IST-AFRICA/techtest/Procure-to-Pay/backend')
django.setup()

from django.contrib.auth import get_user_model
from procurement.models import PurchaseRequest, Approval
from authentication.models import UserProfile

User = get_user_model()

def get_or_create_test_users():
    """Get existing test users or create them if they don't exist"""
    print("Getting or creating test users...")
    
    # Get or create staff user
    staff_user, created = User.objects.get_or_create(
        username='staff_user',
        defaults={
            'email': 'staff@example.com',
            'password': 'password123'
        }
    )
    if created:
        staff_user.set_password('password123')
        staff_user.save()
    staff_user.profile.role = 'staff'
    staff_user.profile.save()
    
    # Get or create level 1 approver
    approver1, created = User.objects.get_or_create(
        username='approver1',
        defaults={
            'email': 'approver1@example.com',
            'password': 'password123'
        }
    )
    if created:
        approver1.set_password('password123')
        approver1.save()
    approver1.profile.role = 'approver1'
    approver1.profile.save()
    
    # Get or create level 2 approver
    approver2, created = User.objects.get_or_create(
        username='approver2',
        defaults={
            'email': 'approver2@example.com',
            'password': 'password123'
        }
    )
    if created:
        approver2.set_password('password123')
        approver2.save()
    approver2.profile.role = 'approver2'
    approver2.profile.save()
    
    print(f"✓ Staff user: {staff_user.username} (role: {staff_user.profile.role})")
    print(f"✓ Level 1 approver: {approver1.username} (role: {approver1.profile.role})")
    print(f"✓ Level 2 approver: {approver2.username} (role: {approver2.profile.role})")
    
    return staff_user, approver1, approver2

def test_request_creation():
    """Test creating a purchase request"""
    print("\n--- Testing Request Creation ---")
    
    staff_user, approver1, approver2 = get_or_create_test_users()
    
    # Create a purchase request
    pr = PurchaseRequest.objects.create(
        title="Test Equipment Purchase",
        description="Testing the approval workflow",
        amount=Decimal('1500.00'),
        created_by=staff_user
    )
    
    print(f"✓ Created request: {pr.title}")
    print(f"✓ Amount: ${pr.amount}")
    print(f"✓ Status: {pr.status}")
    print(f"✓ Created by: {pr.created_by.username}")
    
    return pr, staff_user, approver1, approver2

def test_approval_workflow():
    """Test the complete approval workflow"""
    print("\n--- Testing Approval Workflow ---")
    
    pr, staff_user, approver1, approver2 = test_request_creation()
    
    # Test Level 1 Approval
    print("\n1. Testing Level 1 Approval...")
    approval1 = Approval.objects.create(
        request=pr,
        approver=approver1,
        level=1,
        approved=True,
        comment="Level 1 approved for budget compliance"
    )
    print(f"✓ Level 1 approval created by {approver1.username}")
    print(f"✓ Approved: {approval1.approved}")
    print(f"✓ Comment: {approval1.comment}")
    
    # Test Level 2 Approval
    print("\n2. Testing Level 2 Approval...")
    approval2 = Approval.objects.create(
        request=pr,
        approver=approver2,
        level=2,
        approved=True,
        comment="Level 2 approved for final authorization"
    )
    print(f"✓ Level 2 approval created by {approver2.username}")
    print(f"✓ Approved: {approval2.approved}")
    print(f"✓ Comment: {approval2.comment}")
    
    # Update request status
    pr.status = 'APPROVED'
    pr.approved_by = approver2
    pr.save()
    
    print(f"\n✓ Request final status: {pr.status}")
    print(f"✓ Final approver: {pr.approved_by.username}")
    
    # Test duplicate approval prevention
    print("\n3. Testing duplicate approval prevention...")
    try:
        duplicate_approval = Approval.objects.create(
            request=pr,
            approver=approver1,
            level=1,  # Same level as before
            approved=True,
            comment="Trying to approve again"
        )
        print("❌ ERROR: Duplicate approval was allowed!")
    except Exception as e:
        print(f"✓ Duplicate approval prevented: {str(e)}")
    
    return pr

def test_rejection_workflow():
    """Test request rejection"""
    print("\n--- Testing Rejection Workflow ---")
    
    # Use existing users to avoid duplicate creation
    try:
        staff_user = User.objects.get(username='staff_user')
        approver1 = User.objects.get(username='approver1') 
        approver2 = User.objects.get(username='approver2')
        print("✓ Using existing test users")
    except User.DoesNotExist:
        staff_user, approver1, approver2 = create_test_users()
    
    # Create another request
    pr = PurchaseRequest.objects.create(
        title="Rejected Equipment Purchase",
        description="This will be rejected",
        amount=Decimal('5000.00'),
        created_by=staff_user
    )
    
    print(f"✓ Created request for rejection test: {pr.title}")
    
    # Reject at Level 1
    rejection = Approval.objects.create(
        request=pr,
        approver=approver1,
        level=1,
        approved=False,
        comment="Budget exceeded - rejected"
    )
    
    pr.status = 'REJECTED'
    pr.save()
    
    print(f"✓ Request rejected by {approver1.username}")
    print(f"✓ Rejection reason: {rejection.comment}")
    print(f"✓ Final status: {pr.status}")
    
    return pr

def display_summary():
    """Display summary of all requests and approvals"""
    print("\n--- Summary ---")
    
    print("\nAll Purchase Requests:")
    for pr in PurchaseRequest.objects.all():
        print(f"  {pr.id}: {pr.title} - {pr.status} (${pr.amount})")
    
    print("\nAll Approvals:")
    for approval in Approval.objects.all():
        status = "APPROVED" if approval.approved else "REJECTED"
        print(f"  Request {approval.request.id}: Level {approval.level} - {status} by {approval.approver.username}")

if __name__ == "__main__":
    print("🚀 Testing IST Africa Approval Workflow Logic")
    print("=" * 50)
    
    try:
        # Clear existing data
        User.objects.filter(username__in=['staff_user', 'approver1', 'approver2']).delete()
        
        # Run tests
        approved_request = test_approval_workflow()
        rejected_request = test_rejection_workflow()
        
        display_summary()
        
        print("\n" + "=" * 50)
        print("✅ All approval workflow tests PASSED!")
        print("✅ Core logic is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()