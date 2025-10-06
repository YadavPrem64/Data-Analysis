from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re
from .models import UserProfile


class EnhancedLoginForm(forms.Form):
    """Enhanced login form with validation."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError("Username is required.")
        if len(username.strip()) == 0:
            raise ValidationError("Username cannot be empty.")
        return username.strip()

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise ValidationError("Password is required.")
        if len(password.strip()) == 0:
            raise ValidationError("Password cannot be empty.")
        return password


class EnhancedRegistrationForm(UserCreationForm):
    """Enhanced registration form with comprehensive validation."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number (optional)'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to inherited fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })

    def clean_email(self):
        """Validate email format and uniqueness."""
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")
        
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Please enter a valid email address.")
        
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        
        return email.lower()

    def clean_phone_number(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove all non-digit characters
            phone = re.sub(r'\D', '', phone)
            
            # Check if it's a valid length (10-15 digits)
            if len(phone) < 10 or len(phone) > 15:
                raise ValidationError("Phone number must be between 10 and 15 digits.")
            
            # Format phone number (add country code if missing)
            if len(phone) == 10:
                phone = '1' + phone  # Add US country code
            
            return phone
        return phone

    def clean_first_name(self):
        """Validate first name."""
        first_name = self.cleaned_data.get('first_name')
        if not first_name or len(first_name.strip()) == 0:
            raise ValidationError("First name is required.")
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", first_name):
            raise ValidationError("First name can only contain letters, spaces, hyphens, and apostrophes.")
        
        return first_name.strip().title()

    def clean_last_name(self):
        """Validate last name."""
        last_name = self.cleaned_data.get('last_name')
        if not last_name or len(last_name.strip()) == 0:
            raise ValidationError("Last name is required.")
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", last_name):
            raise ValidationError("Last name can only contain letters, spaces, hyphens, and apostrophes.")
        
        return last_name.strip().title()

    def clean_password1(self):
        """Enhanced password validation."""
        password = self.cleaned_data.get('password1')
        if not password:
            raise ValidationError("Password is required.")
        
        # Minimum length check
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        
        # Check for digit
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit.")
        
        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>).")
        
        return password

    def save(self, commit=True):
        """Save user with additional profile information."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number', '')
            )
        
        return user