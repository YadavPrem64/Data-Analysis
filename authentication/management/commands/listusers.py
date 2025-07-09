from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection


class Command(BaseCommand):
    help = 'List all users in the system with detailed information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='table',
            choices=['table', 'csv', 'json'],
            help='Output format (default: table)'
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Show only active users'
        )

    def handle(self, *args, **options):
        try:
            # Check database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM auth_user")
                total_users = cursor.fetchone()[0]

            self.stdout.write(
                self.style.SUCCESS(f'Database connection successful. Total users: {total_users}')
            )

            # Get users
            if options['active_only']:
                users = User.objects.filter(is_active=True)
                self.stdout.write(f'Showing active users only...\n')
            else:
                users = User.objects.all()

            if not users.exists():
                self.stdout.write(
                    self.style.WARNING('No users found in the database.')
                )
                self.stdout.write('\nTo create a user, run:')
                self.stdout.write('  python manage.py createsuperuser')
                self.stdout.write('  python manage.py createtestuser')
                return

            # Display users based on format
            if options['format'] == 'table':
                self._display_table(users)
            elif options['format'] == 'csv':
                self._display_csv(users)
            elif options['format'] == 'json':
                self._display_json(users)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )

    def _display_table(self, users):
        # Header
        header = f"{'ID':<4} {'Username':<20} {'Email':<25} {'Active':<8} {'Staff':<7} {'Super':<7} {'Last Login':<20}"
        self.stdout.write(header)
        self.stdout.write('-' * len(header))

        # Users
        for user in users:
            last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
            active_status = self.style.SUCCESS('✓') if user.is_active else self.style.ERROR('✗')
            staff_status = '✓' if user.is_staff else '✗'
            super_status = '✓' if user.is_superuser else '✗'

            row = f"{user.id:<4} {user.username:<20} {user.email:<25} {active_status:<8} {staff_status:<7} {super_status:<7} {last_login:<20}"
            self.stdout.write(row)

        self.stdout.write(f'\nTotal: {users.count()} users')

    def _display_csv(self, users):
        self.stdout.write('ID,Username,Email,First Name,Last Name,Active,Staff,Superuser,Last Login,Date Joined')
        for user in users:
            last_login = user.last_login.isoformat() if user.last_login else ''
            date_joined = user.date_joined.isoformat()
            self.stdout.write(
                f'{user.id},{user.username},{user.email},{user.first_name},{user.last_name},'
                f'{user.is_active},{user.is_staff},{user.is_superuser},{last_login},{date_joined}'
            )

    def _display_json(self, users):
        import json
        user_data = []
        for user in users:
            user_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'date_joined': user.date_joined.isoformat(),
            })
        self.stdout.write(json.dumps(user_data, indent=2))