from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import connection
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Test authentication system with detailed debugging'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to test (if not provided, will prompt)'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password to test (if not provided, will prompt)'
        )
        parser.add_argument(
            '--create-if-missing',
            action='store_true',
            help='Create user if it doesn\'t exist'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Authentication System Test ===\n')
        )
        
        # Get credentials
        username = options['username']
        password = options['password']
        
        if not username:
            username = input('Enter username to test: ')
        
        if not password:
            import getpass
            password = getpass.getpass('Enter password: ')
        
        # Test 1: Database Connection
        self.stdout.write('1. Testing database connection...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM auth_user")
                user_count = cursor.fetchone()[0]
                self.stdout.write(
                    self.style.SUCCESS(f'   ✓ Database connection successful ({user_count} users)')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ✗ Database connection failed: {e}')
            )
            return
        
        # Test 2: User Existence
        self.stdout.write('\n2. Checking user existence...')
        try:
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.SUCCESS(f'   ✓ User "{username}" exists')
            )
            self.stdout.write(f'      ID: {user.id}')
            self.stdout.write(f'      Email: {user.email}')
            self.stdout.write(f'      Active: {user.is_active}')
            self.stdout.write(f'      Staff: {user.is_staff}')
            self.stdout.write(f'      Superuser: {user.is_superuser}')
            self.stdout.write(f'      Last Login: {user.last_login or "Never"}')
            self.stdout.write(f'      Password Hash: {user.password[:30]}...')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'   ✗ User "{username}" does not exist')
            )
            
            if options['create_if_missing']:
                self.stdout.write('   Creating user...')
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'   ✓ User "{username}" created')
                )
            else:
                self.stdout.write('   Use --create-if-missing to create the user')
                return
        
        # Test 3: User Status
        self.stdout.write('\n3. Checking user status...')
        if user.is_active:
            self.stdout.write(
                self.style.SUCCESS('   ✓ User is active')
            )
        else:
            self.stdout.write(
                self.style.ERROR('   ✗ User is inactive')
            )
            self.stdout.write('   Run: User.objects.filter(username="{}").update(is_active=True)'.format(username))
        
        # Test 4: Password Verification
        self.stdout.write('\n4. Testing password verification...')
        if user.check_password(password):
            self.stdout.write(
                self.style.SUCCESS('   ✓ Password is correct')
            )
        else:
            self.stdout.write(
                self.style.ERROR('   ✗ Password is incorrect')
            )
            self.stdout.write('   To reset password, run:')
            self.stdout.write(f'   python manage.py resetpassword {username}')
        
        # Test 5: Django Authentication
        self.stdout.write('\n5. Testing Django authentication...')
        try:
            auth_user = authenticate(username=username, password=password)
            if auth_user:
                self.stdout.write(
                    self.style.SUCCESS('   ✓ Django authentication successful')
                )
                self.stdout.write(f'      Authenticated user: {auth_user}')
                self.stdout.write(f'      User object ID: {auth_user.id}')
            else:
                self.stdout.write(
                    self.style.ERROR('   ✗ Django authentication failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ✗ Django authentication error: {e}')
            )
        
        # Test 6: Settings Check
        self.stdout.write('\n6. Checking authentication settings...')
        self.stdout.write(f'   AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}')
        self.stdout.write(f'   LOGIN_URL: {settings.LOGIN_URL}')
        self.stdout.write(f'   LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}')
        
        backends = settings.AUTHENTICATION_BACKENDS
        self.stdout.write('   AUTHENTICATION_BACKENDS:')
        for backend in backends:
            self.stdout.write(f'     - {backend}')
        
        hashers = settings.PASSWORD_HASHERS
        self.stdout.write('   PASSWORD_HASHERS:')
        for hasher in hashers:
            self.stdout.write(f'     - {hasher.split(".")[-1]}')
        
        # Test 7: Summary
        self.stdout.write('\n7. Test Summary:')
        
        all_tests_pass = (
            user.is_active and
            user.check_password(password) and
            authenticate(username=username, password=password) is not None
        )
        
        if all_tests_pass:
            self.stdout.write(
                self.style.SUCCESS('   ✓ All tests passed! Authentication should work.')
            )
            self.stdout.write('\n   You can now login with:')
            self.stdout.write(f'     Username: {username}')
            self.stdout.write(f'     Password: [the password you tested]')
        else:
            self.stdout.write(
                self.style.ERROR('   ✗ Some tests failed. Check the issues above.')
            )
            
            # Provide specific recommendations
            self.stdout.write('\n   Recommendations:')
            if not user.is_active:
                self.stdout.write('     - Activate the user account')
            if not user.check_password(password):
                self.stdout.write('     - Reset the password')
            if not authenticate(username=username, password=password):
                self.stdout.write('     - Check authentication backends configuration')
        
        self.stdout.write('\n=== Test Complete ===')
        
        if all_tests_pass:
            sys.exit(0)
        else:
            sys.exit(1)