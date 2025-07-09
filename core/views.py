from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import logging

logger = logging.getLogger(__name__)


@csrf_protect
def login_view(request):
    """
    Enhanced login function that supports both username and email login
    with proper error handling and logging
    """
    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        logger.debug(f"Login attempt for: {username_or_email}")
        
        if not username_or_email or not password:
            messages.error(request, 'Please provide both username/email and password.')
            return render(request, 'registration/login.html', {
                'username': username_or_email
            })
        
        # Try to authenticate with username first
        user = authenticate(request, username=username_or_email, password=password)
        
        # If authentication failed and input looks like email, try to find user by email
        if user is None and '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
                logger.debug(f"Attempted email login for: {username_or_email}, found username: {user_obj.username}")
            except User.DoesNotExist:
                logger.debug(f"No user found with email: {username_or_email}")
                user = None
        
        if user is not None:
            if user.is_active:
                login(request, user)
                logger.info(f"Successful login for user: {user.username}")
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect('home')  # Redirect to home page after successful login
            else:
                logger.warning(f"Login attempt for inactive user: {user.username}")
                messages.error(request, 'Your account has been disabled.')
        else:
            logger.warning(f"Failed login attempt for: {username_or_email}")
            messages.error(request, 'Invalid username/email or password.')
        
        # Return to login page with form data preserved on error
        return render(request, 'registration/login.html', {
            'username': username_or_email
        })
    
    return render(request, 'registration/login.html')


@csrf_protect
def logout_view(request):
    """
    Logout function that logs out the user and redirects to home
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        logger.info(f"User {username} logged out")
        messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@csrf_protect
def register_view(request):
    """
    Enhanced registration function with comprehensive validation,
    transaction handling, and logging
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        logger.debug(f"Registration attempt for username: {username}, email: {email}")
        
        # Preserve form data for re-rendering on errors
        form_data = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        }
        
        # Validation
        errors = []
        
        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        if not password1:
            errors.append('Password is required.')
        elif password1 != password2:
            errors.append('Passwords do not match.')
        else:
            try:
                validate_password(password1)
            except ValidationError as e:
                errors.extend(e.messages)
        
        if errors:
            for error in errors:
                messages.error(request, error)
            logger.warning(f"Registration validation failed for {username}: {errors}")
            return render(request, 'registration/register.html', form_data)
        
        # Create user with transaction handling
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name
                )
                logger.info(f"Successfully created user: {username} with email: {email}")
                messages.success(request, 'Registration successful! You can now log in.')
                return redirect('login')
                
        except Exception as e:
            logger.error(f"Error creating user {username}: {str(e)}")
            messages.error(request, 'Registration failed. Please try again.')
            return render(request, 'registration/register.html', form_data)
    
    return render(request, 'registration/register.html')


def home_view(request):
    """
    Simple home page view
    """
    return render(request, 'home.html')
