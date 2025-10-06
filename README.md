# Travel Website - Authentication Debug System

This project provides a comprehensive Django travel website with advanced authentication debugging capabilities to help diagnose and fix persistent login issues.

## Features

### 🔐 Authentication System
- **Enhanced Login View** with comprehensive logging
- **User Management** with detailed user information display
- **Session Management** with proper configuration
- **Password Hashing** using Django's secure defaults

### 🛠️ Debug Tools

#### 1. Debug Authentication View (`/auth/debug/`)
- Step-by-step authentication testing
- Real-time password verification
- Database connection testing
- Session configuration analysis
- Detailed error reporting with recommendations

#### 2. Database Status View (`/auth/database/`)
- Database connection verification
- Table existence checking
- Authentication configuration display
- Session settings overview
- Migration status

#### 3. User List View (`/auth/users/`)
- Complete user information display
- Password hash visibility
- User status indicators
- Management command examples

#### 4. Management Commands
- `listusers` - List all users with detailed information
- `createtestuser` - Create test users for debugging
- `resetpassword` - Reset user passwords securely
- `testauth` - Comprehensive authentication testing

### 📊 Comprehensive Logging
All authentication attempts are logged with:
- Raw input data (excluding passwords)
- User lookup results
- Password verification steps
- Django authentication flow
- Session creation/destruction
- Detailed error messages

## Quick Start

1. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

2. **Create a Test User**
   ```bash
   python manage.py createtestuser --username testuser --password testpass123
   ```

3. **Start the Server**
   ```bash
   python manage.py runserver
   ```

4. **Access Debug Tools**
   - Login Page: http://localhost:8000/auth/login/
   - Debug Authentication: http://localhost:8000/auth/debug/
   - Database Status: http://localhost:8000/auth/database/
   - User Management: http://localhost:8000/auth/users/

## Debugging Authentication Issues

### Common Issues and Solutions

1. **"Invalid username and password" errors**
   - Check if user exists: `python manage.py listusers`
   - Verify password: `python manage.py testauth --username [username]`
   - Reset password: `python manage.py resetpassword [username]`

2. **User exists but can't login**
   - Check user.is_active status
   - Verify authentication backends
   - Check session configuration

3. **Database issues**
   - Run migrations: `python manage.py migrate`
   - Check database status: Visit `/auth/database/`
   - Verify table creation

### Management Commands

```bash
# List all users
python manage.py listusers

# List only active users
python manage.py listusers --active-only

# Create a test user
python manage.py createtestuser --username myuser --password mypass123

# Test authentication
python manage.py testauth --username myuser --password mypass123

# Reset a user's password
python manage.py resetpassword myuser
```

### Debug Views

1. **Database Status** - Check database connectivity and configuration
2. **User List** - View all users and their status
3. **Debug Authentication** - Step-by-step authentication testing
4. **Login with Debugging** - Enhanced login with detailed logging

## Logging

Authentication events are logged to:
- Console output (with colors)
- `auth_debug.log` file
- Django's logging system

Log levels:
- **INFO**: Normal authentication flow
- **WARNING**: Suspicious activity
- **ERROR**: Authentication failures

## Security Features

- CSRF protection enabled
- Secure password hashing (PBKDF2)
- Session security configured
- Debug information only in DEBUG mode
- Secure authentication backends

## Project Structure

```
travel_website/
├── authentication/          # Authentication app
│   ├── management/
│   │   └── commands/        # Custom management commands
│   ├── templates/           # Authentication templates
│   ├── views.py            # Enhanced views with logging
│   └── urls.py             # URL configuration
├── templates/              # Base templates
├── travel_website/         # Project settings
├── manage.py              # Django management
└── README.md              # This file
```

## Contributing

This debugging system is designed to help developers quickly identify and fix authentication issues. Feel free to extend the debugging capabilities or add new features.

## License

This project is for educational and debugging purposes.
