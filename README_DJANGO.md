# Explorease - Django Authentication System

This project implements a robust Django authentication system with comprehensive security features, user experience enhancements, and proper code structure.

## Features

### 🔐 Security Features
- **Rate Limiting**: 5 failed login attempts per 15 minutes per IP address
- **Strong Password Validation**: Minimum 8 characters with uppercase, lowercase, digits, and special characters
- **CSRF Protection**: Built-in Django CSRF protection on all forms
- **Input Sanitization**: Proper escaping and validation of user inputs
- **Session Security**: Configurable session timeouts and secure cookie settings
- **Security Logging**: Comprehensive logging of authentication events

### 👤 User Experience
- **Form Data Persistence**: Form data preserved on validation errors
- **Redirect After Login**: Users redirected to intended page after authentication
- **Comprehensive Error Messages**: Clear, helpful error messages for all validation failures
- **Email Verification**: Email verification workflow with UUID tokens
- **Responsive Design**: Mobile-friendly Bootstrap-based interface
- **Remember Me**: Optional extended session duration

### 📱 User Interface
- **Consistent Branding**: "Explorease" branding throughout the application
- **Professional Design**: Clean, modern interface with Bootstrap components
- **Responsive Layout**: Works on desktop, tablet, and mobile devices
- **Accessibility**: Proper form labels and ARIA attributes

### 🛠 Code Quality
- **Database Transactions**: User creation wrapped in atomic transactions
- **Model Extensions**: Extended User model with UserProfile for additional fields
- **Comprehensive Testing**: 25+ test cases covering all functionality
- **Admin Interface**: Custom admin interface for user and security management
- **Helper Functions**: Reusable utility functions for common operations

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Data-Analysis
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   - Login: http://localhost:8000/auth/login/
   - Register: http://localhost:8000/auth/register/
   - Admin: http://localhost:8000/admin/

## Usage

### User Registration
1. Navigate to the registration page
2. Fill in all required fields:
   - First Name and Last Name
   - Username (unique)
   - Email address (unique, valid format)
   - Phone number (optional, 10-15 digits)
   - Password (meeting complexity requirements)
3. Submit the form
4. Check email for verification link
5. Click verification link to activate account

### User Login
1. Navigate to the login page
2. Enter username and password
3. Optionally check "Remember Me" for extended session
4. Submit the form
5. Access the secure dashboard

### Security Features
- **Rate Limiting**: After 5 failed attempts, users must wait 15 minutes
- **Session Management**: Sessions expire based on user preference
- **Password Requirements**: Strong passwords enforced during registration
- **Email Verification**: Accounts require email verification before full access

## Testing

Run the comprehensive test suite:

```bash
python manage.py test
```

Test coverage includes:
- Model functionality and relationships
- Form validation and security
- View authentication and authorization
- Rate limiting and security features
- User interface and branding consistency

## Security Configuration

### Environment Variables (Production)
```python
# Security settings for production
SECRET_KEY = 'your-secret-key-here'
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@domain.com'
EMAIL_HOST_PASSWORD = 'your-email-password'

# Session security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## File Structure

```
├── authentication/
│   ├── models.py          # User profile and login attempt models
│   ├── forms.py           # Enhanced forms with validation
│   ├── views.py           # Secure authentication views
│   ├── utils.py           # Helper functions
│   ├── admin.py           # Admin interface configuration
│   ├── urls.py            # URL routing
│   └── tests.py           # Comprehensive test suite
├── templates/
│   ├── base.html          # Base template
│   └── authentication/
│       ├── login.html     # Login page
│       ├── register.html  # Registration page
│       └── dashboard.html # User dashboard
├── static/
│   └── css/
│       └── styles.css     # Custom styling
├── explorease_project/
│   ├── settings.py        # Django settings
│   └── urls.py            # Main URL configuration
└── requirements.txt       # Project dependencies
```

## API Endpoints

- `GET /auth/login/` - Display login form
- `POST /auth/login/` - Process login credentials
- `GET /auth/register/` - Display registration form
- `POST /auth/register/` - Process registration data
- `GET /auth/dashboard/` - User dashboard (authenticated)
- `GET /auth/logout/` - Log out user
- `GET /auth/verify-email/<token>/` - Email verification

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.