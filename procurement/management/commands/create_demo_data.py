from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

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

        self.stdout.write(
            self.style.SUCCESS('Demo data created successfully!')
        )