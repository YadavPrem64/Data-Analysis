from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


class Command(BaseCommand):
    help = 'Create a test user for authentication debugging'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='testuser',
            help='Username for the test user (default: testuser)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='test@example.com',
            help='Email for the test user (default: test@example.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='testpass123',
            help='Password for the test user (default: testpass123)'
        )
        parser.add_argument(
            '--staff',
            action='store_true',
            help='Make the user a staff member'
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Make the user a superuser'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Test',
            help='First name for the test user (default: Test)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='User',
            help='Last name for the test user (default: User)'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        
        self.stdout.write(f'Creating test user: {username}')
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists!')
            )
            
            # Ask if user wants to update
            response = input('Do you want to update the existing user? (y/n): ')
            if response.lower() != 'y':
                self.stdout.write('Aborted.')
                return
            
            user = User.objects.get(username=username)
            self.stdout.write(f'Updating existing user: {username}')
        else:
            user = User()
            user.username = username
            self.stdout.write(f'Creating new user: {username}')
        
        # Set user fields
        user.email = email
        user.first_name = options['first_name']
        user.last_name = options['last_name']
        user.is_staff = options['staff'] or options['superuser']
        user.is_superuser = options['superuser']
        user.is_active = True
        
        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Password validation failed: {e}')
            )
            return
        
        # Set password
        user.set_password(password)
        
        try:
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created/updated user: {username}')
            )
            
            # Display user information
            self.stdout.write('\nUser Details:')
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  First Name: {user.first_name}')
            self.stdout.write(f'  Last Name: {user.last_name}')
            self.stdout.write(f'  Active: {user.is_active}')
            self.stdout.write(f'  Staff: {user.is_staff}')
            self.stdout.write(f'  Superuser: {user.is_superuser}')
            self.stdout.write(f'  Password Hash: {user.password[:30]}...')
            
            self.stdout.write('\nYou can now test login with:')
            self.stdout.write(f'  Username: {username}')
            self.stdout.write(f'  Password: {password}')
            
            # Test authentication
            self.stdout.write('\nTesting authentication...')
            from django.contrib.auth import authenticate
            
            auth_user = authenticate(username=username, password=password)
            if auth_user:
                self.stdout.write(
                    self.style.SUCCESS('✓ Authentication test successful!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Authentication test failed!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {str(e)}')
            )