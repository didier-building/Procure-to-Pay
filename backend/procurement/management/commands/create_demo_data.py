from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
from procurement.models import PurchaseRequest, RequestItem, Approval

User = get_user_model()

class Command(BaseCommand):
    help = 'Create demo users with different roles for testing'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Create superuser for admin
            if not User.objects.filter(username='admin').exists():
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@procuretopay.com',
                    password='admin123',
                    first_name='Admin',
                    last_name='User'
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created admin user: admin/admin123')
                )

            # Create demo users
            demo_users = [
                {
                    'username': 'staff1',
                    'email': 'staff@procuretopay.com',
                    'password': 'staff123',
                    'first_name': 'John',
                    'last_name': 'Staff',
                    'role': 'staff'
                },
                {
                    'username': 'approver1',
                    'email': 'approver1@procuretopay.com', 
                    'password': 'approver123',
                    'first_name': 'Alice',
                    'last_name': 'Approver1',
                    'role': 'approver1'
                },
                {
                    'username': 'approver2',
                    'email': 'approver2@procuretopay.com',
                    'password': 'approver123',
                    'first_name': 'Bob',
                    'last_name': 'Approver2',
                    'role': 'approver2'
                },
                {
                    'username': 'finance',
                    'email': 'finance@procuretopay.com',
                    'password': 'finance123',
                    'first_name': 'Carol',
                    'last_name': 'Finance',
                    'role': 'finance'
                }
            ]

            for user_data in demo_users:
                if not User.objects.filter(username=user_data['username']).exists():
                    user = User.objects.create_user(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=user_data['password'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name']
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created {user_data["role"]} user: {user_data["username"]}/{user_data["password"]}'
                        )
                    )

            # Create sample procurement requests
            staff_user = User.objects.get(username='staff1')
            approver1_user = User.objects.get(username='approver1')
            approver2_user = User.objects.get(username='approver2')
            
            sample_requests = [
                {
                    'title': 'Office Supplies Purchase',
                    'description': 'Monthly office supplies including paper, pens, and stationery for Administration department',
                    'amount': Decimal('500.00'),
                    'items': [
                        {'description': 'A4 Paper (10 reams)', 'quantity': 10, 'unit_price': Decimal('15.00')},
                        {'description': 'Ballpoint Pens (100 pack)', 'quantity': 5, 'unit_price': Decimal('25.00')},
                        {'description': 'Printer Cartridges', 'quantity': 4, 'unit_price': Decimal('75.00')},
                    ]
                },
                {
                    'title': 'IT Equipment Upgrade',
                    'description': 'New laptops for development team in IT department',
                    'amount': Decimal('3000.00'),
                    'items': [
                        {'description': 'Dell Laptop - Intel i7, 16GB RAM', 'quantity': 2, 'unit_price': Decimal('1500.00')},
                    ]
                },
                {
                    'title': 'Marketing Materials',
                    'description': 'Brochures and business cards for Q1 campaign - Marketing department',
                    'amount': Decimal('800.00'),
                    'items': [
                        {'description': 'Tri-fold Brochures (1000 pcs)', 'quantity': 1, 'unit_price': Decimal('400.00')},
                        {'description': 'Business Cards (500 pcs)', 'quantity': 1, 'unit_price': Decimal('400.00')},
                    ]
                }
            ]
            
            for req_data in sample_requests:
                if not PurchaseRequest.objects.filter(title=req_data['title']).exists():
                    # Create purchase request
                    purchase_request = PurchaseRequest.objects.create(
                        title=req_data['title'],
                        description=req_data['description'],
                        amount=req_data['amount'],
                        created_by=staff_user
                    )
                    
                    # Create request items
                    for item_data in req_data['items']:
                        RequestItem.objects.create(
                            request=purchase_request,
                            name=item_data['description'],
                            quantity=item_data['quantity'],
                            unit_price=item_data['unit_price']
                        )
                    
                    # Create approval workflow (first level approved for demo)
                    if req_data['title'] == 'Office Supplies Purchase':
                        # First approval approved
                        Approval.objects.create(
                            request=purchase_request,
                            approver=approver1_user,
                            level=1,
                            approved=True,
                            comment='Approved for regular office supplies'
                        )
                        # Second approval pending
                        Approval.objects.create(
                            request=purchase_request,
                            approver=approver2_user,
                            level=2,
                            approved=None,
                            comment=''
                        )
                    elif req_data['title'] == 'IT Equipment Upgrade':
                        # Both approvals pending (high value)
                        Approval.objects.create(
                            request=purchase_request,
                            approver=approver1_user,
                            level=1,
                            approved=None,
                            comment=''
                        )
                        Approval.objects.create(
                            request=purchase_request,
                            approver=approver2_user,
                            level=2,
                            approved=None,
                            comment=''
                        )
                    else:
                        # Marketing materials - first approval pending
                        Approval.objects.create(
                            request=purchase_request,
                            approver=approver1_user,
                            level=1,
                            approved=None,
                            comment=''
                        )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Created procurement request: {req_data["title"]}')
                    )

        self.stdout.write(
            self.style.SUCCESS('Demo data created successfully!')
        )