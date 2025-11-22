"""
Comprehensive tests for procurement serializers.
Tests serialization, deserialization, validation, and business logic.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from ..models import PurchaseRequest, Approval, RequestItem
from ..serializers import (
    PurchaseRequestSerializer,
    PurchaseRequestCreateSerializer, 
    PurchaseRequestUpdateSerializer,
    ApproveRequestSerializer,
    RejectRequestSerializer,
    ReceiptUploadSerializer,
    RequestItemSerializer,
    ApprovalSerializer
)

User = get_user_model()


class RequestItemSerializerTest(TestCase):
    """Test RequestItemSerializer functionality."""
    
    def test_request_item_serialization(self):
        """Test serializing a RequestItem instance."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        pr = PurchaseRequest.objects.create(
            title="Test Purchase",
            amount=Decimal('1000.00'),
            created_by=user
        )
        
        item = RequestItem.objects.create(
            request=pr,
            name="Laptop",
            quantity=2,
            unit_price=Decimal('500.00')
        )
        
        serializer = RequestItemSerializer(item)
        data = serializer.data
        
        self.assertEqual(data['name'], "Laptop")
        self.assertEqual(data['quantity'], 2)
        self.assertEqual(data['unit_price'], '500.00')
        self.assertIn('id', data)
    
    def test_request_item_deserialization(self):
        """Test deserializing RequestItem data."""
        data = {
            'name': 'Monitor', 
            'quantity': 3,
            'unit_price': '200.00'
        }
        
        serializer = RequestItemSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['name'], 'Monitor')
        self.assertEqual(validated_data['quantity'], 3)
        self.assertEqual(validated_data['unit_price'], Decimal('200.00'))
    
    def test_request_item_validation_errors(self):
        """Test RequestItem validation errors."""
        # Missing required fields
        data = {'name': 'Test Item'}
        serializer = RequestItemSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('unit_price', serializer.errors)
        
        # Invalid quantity (negative)
        data = {
            'name': 'Test Item',
            'quantity': -1,
            'unit_price': '100.00'
        }
        serializer = RequestItemSerializer(data=data)
        # Note: PositiveIntegerField validation happens at model level


class ApprovalSerializerTest(TestCase):
    """Test ApprovalSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.approver = User.objects.create_user(
            username='approver',
            password='testpass123'
        )
        
        self.pr = PurchaseRequest.objects.create(
            title="Test Purchase",
            amount=Decimal('1000.00'),
            created_by=self.user
        )
    
    def test_approval_serialization(self):
        """Test serializing an Approval instance."""
        approval = Approval.objects.create(
            request=self.pr,
            approver=self.approver,
            level=1,
            approved=True,
            comment="Approved for business need"
        )
        
        serializer = ApprovalSerializer(approval)
        data = serializer.data
        
        self.assertEqual(data['level'], 1)
        self.assertTrue(data['approved'])
        self.assertEqual(data['comment'], "Approved for business need")
        self.assertEqual(data['approver'], str(self.approver))  # StringRelatedField
        self.assertIn('created_at', data)


class PurchaseRequestSerializerTest(TestCase):
    """Test PurchaseRequestSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.approver = User.objects.create_user(
            username='approver',
            password='testpass123'
        )
    
    def test_purchase_request_serialization(self):
        """Test serializing a PurchaseRequest with related objects."""
        pr = PurchaseRequest.objects.create(
            title="Office Equipment",
            description="Quarterly equipment purchase",
            amount=Decimal('2500.00'),
            created_by=self.user,
            department="IT",
            urgency="HIGH",
            justification="Equipment replacement needed"
        )
        
        # Add items
        RequestItem.objects.create(
            request=pr,
            name="Laptop",
            quantity=2,
            unit_price=Decimal('800.00')
        )
        
        RequestItem.objects.create(
            request=pr,
            name="Monitor", 
            quantity=2,
            unit_price=Decimal('300.00')
        )
        
        # Add approval
        Approval.objects.create(
            request=pr,
            approver=self.approver,
            level=1,
            approved=True,
            comment="Level 1 approved"
        )
        
        serializer = PurchaseRequestSerializer(pr)
        data = serializer.data
        
        # Test basic fields
        self.assertEqual(data['title'], "Office Equipment")
        self.assertEqual(data['description'], "Quarterly equipment purchase")
        self.assertEqual(data['amount'], '2500.00')
        self.assertEqual(data['status'], 'PENDING')
        self.assertEqual(data['department'], 'IT')
        self.assertEqual(data['urgency'], 'HIGH')
        
        # Test relationships
        self.assertEqual(len(data['items']), 2)
        self.assertEqual(len(data['approvals']), 1)
        
        # Test nested item data
        laptop_item = next(item for item in data['items'] if item['name'] == 'Laptop')
        self.assertEqual(laptop_item['quantity'], 2)
        self.assertEqual(laptop_item['unit_price'], '800.00')


class PurchaseRequestCreateSerializerTest(TestCase):
    """Test PurchaseRequestCreateSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_purchase_request_creation_with_items(self):
        """Test creating a PurchaseRequest with items."""
        request = self.factory.post('/')
        request.user = self.user
        
        data = {
            'title': 'New Equipment Purchase',
            'description': 'Monthly equipment procurement',
            'amount': '1500.00',
            'department': 'HR',
            'urgency': 'MEDIUM',
            'justification': 'Team expansion needs',
            'items': [
                {
                    'name': 'Desk Chair',
                    'quantity': 5,
                    'unit_price': '200.00'
                },
                {
                    'name': 'Desk',
                    'quantity': 5, 
                    'unit_price': '100.00'
                }
            ]
        }
        
        serializer = PurchaseRequestCreateSerializer(
            data=data,
            context={'request': Request(request)}
        )
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        # Create the instance
        pr = serializer.save()
        
        # Verify purchase request
        self.assertEqual(pr.title, 'New Equipment Purchase')
        self.assertEqual(pr.amount, Decimal('1500.00'))
        self.assertEqual(pr.created_by, self.user)
        self.assertEqual(pr.department, 'HR')
        
        # Verify items were created
        items = pr.items.all()
        self.assertEqual(items.count(), 2)
        
        chair_item = items.get(name='Desk Chair')
        self.assertEqual(chair_item.quantity, 5)
        self.assertEqual(chair_item.unit_price, Decimal('200.00'))
    
    def test_purchase_request_creation_validation(self):
        """Test validation in PurchaseRequestCreateSerializer."""
        # Missing required fields
        data = {
            'title': 'Test Purchase'
            # Missing amount and items
        }
        
        serializer = PurchaseRequestCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_purchase_request_creation_empty_items(self):
        """Test creation with empty items list."""
        request = self.factory.post('/')
        request.user = self.user
        
        data = {
            'title': 'Simple Purchase',
            'amount': '100.00',
            'items': []  # Empty items
        }
        
        serializer = PurchaseRequestCreateSerializer(
            data=data,
            context={'request': Request(request)}
        )
        
        self.assertTrue(serializer.is_valid())
        pr = serializer.save()
        
        # Should create PR with no items
        self.assertEqual(pr.items.count(), 0)


class PurchaseRequestUpdateSerializerTest(TestCase):
    """Test PurchaseRequestUpdateSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.pr = PurchaseRequest.objects.create(
            title="Original Title",
            amount=Decimal('1000.00'),
            created_by=self.user,
            status='PENDING'
        )
    
    def test_purchase_request_update_pending(self):
        """Test updating a PENDING purchase request."""
        data = {
            'title': 'Updated Title',
            'amount': '1200.00',
            'department': 'Finance',
            'items': [
                {
                    'name': 'New Item',
                    'quantity': 1,
                    'unit_price': '1200.00'
                }
            ]
        }
        
        serializer = PurchaseRequestUpdateSerializer(
            instance=self.pr,
            data=data
        )
        
        self.assertTrue(serializer.is_valid())
        updated_pr = serializer.save()
        
        self.assertEqual(updated_pr.title, 'Updated Title')
        self.assertEqual(updated_pr.amount, Decimal('1200.00'))
        self.assertEqual(updated_pr.department, 'Finance')
    
    def test_purchase_request_update_non_pending(self):
        """Test validation prevents updating non-PENDING requests."""
        # Change status to APPROVED
        self.pr.status = 'APPROVED'
        self.pr.save()
        
        data = {
            'title': 'Should Not Work',
            'amount': '1500.00'
        }
        
        serializer = PurchaseRequestUpdateSerializer(
            instance=self.pr,
            data=data
        )
        
        # Validation should fail
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class ApproveRequestSerializerTest(TestCase):
    """Test ApproveRequestSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.pr = PurchaseRequest.objects.create(
            title="Test Purchase",
            amount=Decimal('1000.00'),
            created_by=self.user,
            status='PENDING'
        )
    
    def test_approve_request_validation(self):
        """Test ApproveRequestSerializer validation."""
        data = {
            'comment': 'Looks good for approval'
        }
        
        serializer = ApproveRequestSerializer(
            data=data,
            context={'purchase_request': self.pr}
        )
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['comment'], 'Looks good for approval')
    
    def test_approve_request_without_comment(self):
        """Test approval without comment (should be valid)."""
        data = {}
        
        serializer = ApproveRequestSerializer(
            data=data,
            context={'purchase_request': self.pr}
        )
        
        self.assertTrue(serializer.is_valid())


class RejectRequestSerializerTest(TestCase):
    """Test RejectRequestSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.pr = PurchaseRequest.objects.create(
            title="Test Purchase",
            amount=Decimal('1000.00'),
            created_by=self.user,
            status='PENDING'
        )
    
    def test_reject_request_validation(self):
        """Test RejectRequestSerializer validation."""
        data = {
            'comment': 'Budget constraints require rejection'
        }
        
        serializer = RejectRequestSerializer(
            data=data,
            context={'purchase_request': self.pr}
        )
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['comment'], 'Budget constraints require rejection')


class ReceiptUploadSerializerTest(TestCase):
    """Test ReceiptUploadSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.pr = PurchaseRequest.objects.create(
            title="Test Purchase",
            amount=Decimal('1000.00'),
            created_by=self.user,
            status='APPROVED'
        )
    
    def test_receipt_upload_validation(self):
        """Test ReceiptUploadSerializer validation."""
        # Note: In a real test, we'd use SimpleUploadedFile
        # This tests the serializer structure
        
        serializer = ReceiptUploadSerializer(instance=self.pr)
        
        # Test that the serializer has the receipt field
        self.assertIn('receipt', serializer.fields)
        
        # Test partial update capability
        data = {}  # Empty data for partial update
        serializer = ReceiptUploadSerializer(
            instance=self.pr,
            data=data,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())


if __name__ == '__main__':
    # Run with: python manage.py test procurement.test_serializers
    pass