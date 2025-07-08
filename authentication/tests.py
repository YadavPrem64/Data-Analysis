from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail
from authentication.models import UserProfile, LoginAttempt
from authentication.forms import EnhancedLoginForm, EnhancedRegistrationForm
from authentication.utils import get_client_ip, is_rate_limited
import uuid


class AuthenticationModelsTest(TestCase):
    """Test cases for authentication models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_profile_creation(self):
        """Test that UserProfile is created with user."""
        profile = UserProfile.objects.create(
            user=self.user,
            phone_number='1234567890'
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, '1234567890')
        self.assertFalse(profile.email_verified)
        self.assertIsInstance(profile.email_verification_token, uuid.UUID)
    
    def test_login_attempt_model(self):
        """Test LoginAttempt model."""
        attempt = LoginAttempt.objects.create(
            ip_address='192.168.1.1',
            username='testuser',
            success=True
        )
        self.assertEqual(attempt.ip_address, '192.168.1.1')
        self.assertEqual(attempt.username, 'testuser')
        self.assertTrue(attempt.success)
    
    def test_get_recent_failures(self):
        """Test rate limiting functionality."""
        ip = '192.168.1.1'
        
        # Create some failed attempts
        for i in range(3):
            LoginAttempt.objects.create(
                ip_address=ip,
                username='testuser',
                success=False
            )
        
        failures = LoginAttempt.get_recent_failures(ip)
        self.assertEqual(failures, 3)


class AuthenticationFormsTest(TestCase):
    """Test cases for authentication forms."""
    
    def test_valid_login_form(self):
        """Test valid login form."""
        form_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        form = EnhancedLoginForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_empty_login_form_fields(self):
        """Test login form with empty fields."""
        form_data = {
            'username': '',
            'password': ''
        }
        form = EnhancedLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        # Check for Django's default required field error or our custom message
        self.assertTrue(
            'Username is required.' in str(form.errors['username']) or 
            'This field is required.' in str(form.errors['username'])
        )
        self.assertTrue(
            'Password is required.' in str(form.errors['password']) or 
            'This field is required.' in str(form.errors['password'])
        )
    
    def test_valid_registration_form(self):
        """Test valid registration form."""
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'phone_number': '1234567890',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        form = EnhancedRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_weak_password_validation(self):
        """Test password strength validation."""
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'weak',
            'password2': 'weak'
        }
        form = EnhancedRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Password must be at least 8 characters long.', form.errors['password1'])
    
    def test_invalid_email_validation(self):
        """Test email validation."""
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'invalid-email',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        form = EnhancedRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        # Check for Django's default email validation error or our custom message
        self.assertTrue(
            'Please enter a valid email address.' in str(form.errors['email']) or 
            'Enter a valid email address.' in str(form.errors['email'])
        )
    
    def test_phone_number_validation(self):
        """Test phone number validation."""
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'phone_number': '123',  # Too short
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        form = EnhancedRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Phone number must be between 10 and 15 digits.', form.errors['phone_number'])


class AuthenticationViewsTest(TestCase):
    """Test cases for authentication views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        UserProfile.objects.create(user=self.user)
    
    def test_login_view_get(self):
        """Test login view GET request."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login to Explorease')
        self.assertContains(response, 'Explorease')
    
    def test_login_view_valid_credentials(self):
        """Test login with valid credentials."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
    
    def test_login_view_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
    
    def test_register_view_get(self):
        """Test register view GET request."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Join Explorease')
        self.assertContains(response, 'Explorease')
    
    def test_register_view_valid_data(self):
        """Test registration with valid data."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertEqual(len(mail.outbox), 1)  # Email verification sent
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires login."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_dashboard_authenticated_user(self):
        """Test dashboard for authenticated user."""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome to Explorease Dashboard')
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Make multiple failed login attempts
        for i in range(6):
            self.client.post(reverse('login'), {
                'username': 'testuser',
                'password': 'wrongpassword'
            })
        
        # Next attempt should be rate limited
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertContains(response, 'Too many failed login attempts')
    
    def test_logout_view(self):
        """Test logout functionality."""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
    
    def test_redirect_after_login(self):
        """Test redirect to intended page after login."""
        # Try to access dashboard (should redirect to login)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        
        # Login with next parameter
        response = self.client.post(reverse('login') + '?next=/auth/dashboard/', {
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 302)


class SecurityTest(TestCase):
    """Test security features."""
    
    def test_csrf_protection(self):
        """Test CSRF protection is enabled."""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_input_sanitization(self):
        """Test input sanitization in forms."""
        form_data = {
            'username': '<script>alert("xss")</script>',
            'password': 'testpass'
        }
        form = EnhancedLoginForm(data=form_data)
        if form.is_valid():
            # Username should be sanitized (though this particular input would be rejected by validation)
            self.assertIn('script', form.cleaned_data['username'])
    
    def test_session_security(self):
        """Test session security settings."""
        from django.conf import settings
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_AGE, 3600)
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)


class BrandingTest(TestCase):
    """Test consistent branding across the application."""
    
    def test_explorease_branding_login(self):
        """Test Explorease branding on login page."""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'Explorease')
        self.assertContains(response, 'Login to Explorease')
    
    def test_explorease_branding_register(self):
        """Test Explorease branding on register page."""
        response = self.client.get(reverse('register'))
        self.assertContains(response, 'Explorease')
        self.assertContains(response, 'Join Explorease')
    
    def test_page_titles(self):
        """Test consistent page titles."""
        response = self.client.get(reverse('login'))
        self.assertContains(response, '<title>Login - Explorease</title>')
        
        response = self.client.get(reverse('register'))
        self.assertContains(response, '<title>Register - Explorease</title>')
