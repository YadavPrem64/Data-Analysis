from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Reset password for a user'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Username of the user whose password to reset'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='New password (if not provided, will prompt)'
        )
        parser.add_argument(
            '--no-validation',
            action='store_true',
            help='Skip password validation'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" does not exist!')
            )
            return
        
        self.stdout.write(f'Resetting password for user: {username}')
        self.stdout.write(f'User Details:')
        self.stdout.write(f'  ID: {user.id}')
        self.stdout.write(f'  Email: {user.email}')
        self.stdout.write(f'  Active: {user.is_active}')
        self.stdout.write(f'  Staff: {user.is_staff}')
        self.stdout.write(f'  Superuser: {user.is_superuser}')
        self.stdout.write(f'  Last Login: {user.last_login or "Never"}')
        
        # Get new password
        new_password = options['password']
        if not new_password:
            import getpass
            new_password = getpass.getpass('Enter new password: ')
            confirm_password = getpass.getpass('Confirm password: ')
            
            if new_password != confirm_password:
                self.stdout.write(
                    self.style.ERROR('Passwords do not match!')
                )
                return
        
        # Validate password
        if not options['no_validation']:
            try:
                validate_password(new_password, user)
            except ValidationError as e:
                self.stdout.write(
                    self.style.ERROR(f'Password validation failed:')
                )
                for error in e.messages:
                    self.stdout.write(f'  - {error}')
                return
        
        # Store old password hash for comparison
        old_password_hash = user.password
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Password reset successfully for user: {username}')
        )
        
        # Show password hash change
        self.stdout.write('\nPassword Hash Information:')
        self.stdout.write(f'  Old Hash: {old_password_hash[:50]}...')
        self.stdout.write(f'  New Hash: {user.password[:50]}...')
        
        # Test authentication with new password
        self.stdout.write('\nTesting authentication with new password...')
        auth_user = authenticate(username=username, password=new_password)
        
        if auth_user:
            self.stdout.write(
                self.style.SUCCESS('✓ Authentication test successful!')
            )
            self.stdout.write(f'  Authenticated user: {auth_user}')
            self.stdout.write(f'  User active: {auth_user.is_active}')
        else:
            self.stdout.write(
                self.style.ERROR('✗ Authentication test failed!')
            )
            self.stdout.write('This might indicate an issue with:')
            self.stdout.write('  - Password hashing')
            self.stdout.write('  - User activation status')
            self.stdout.write('  - Authentication backends')
        
        # Test password verification directly
        self.stdout.write('\nTesting direct password verification...')
        if user.check_password(new_password):
            self.stdout.write(
                self.style.SUCCESS('✓ Direct password check successful!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Direct password check failed!')
            )
        
        self.stdout.write(f'\nUser can now login with:')
        self.stdout.write(f'  Username: {username}')
        self.stdout.write(f'  Password: [the password you just set]')