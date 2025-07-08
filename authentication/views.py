from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.html import escape
import logging
import uuid

from .forms import EnhancedLoginForm, EnhancedRegistrationForm
from .models import LoginAttempt, UserProfile


logger = logging.getLogger('authentication.security')


def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_rate_limited(ip_address, max_attempts=5, window_minutes=15):
    """Check if an IP address is rate limited."""
    return LoginAttempt.get_recent_failures(ip_address, window_minutes) >= max_attempts


def log_security_event(event_type, details, ip_address=None, username=None):
    """Log security events."""
    logger.info(f"Security Event: {event_type} | IP: {ip_address} | User: {username} | Details: {details}")


@csrf_protect
@never_cache
def login_view(request):
    """Enhanced login view with rate limiting and security features."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    ip_address = get_client_ip(request)
    
    # Check rate limiting
    if is_rate_limited(ip_address):
        log_security_event('RATE_LIMITED', 'Too many failed login attempts', ip_address)
        messages.error(request, 'Too many failed login attempts. Please try again in 15 minutes.')
        return render(request, 'authentication/login.html', {'form': EnhancedLoginForm()})
    
    if request.method == 'POST':
        form = EnhancedLoginForm(request.POST)
        if form.is_valid():
            username = escape(form.cleaned_data['username'])
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Log successful login
                    LoginAttempt.objects.create(
                        ip_address=ip_address,
                        username=username,
                        success=True
                    )
                    log_security_event('LOGIN_SUCCESS', f'User {username} logged in successfully', ip_address, username)
                    
                    # Handle session timeout based on remember me
                    if not remember_me:
                        request.session.set_expiry(0)  # Session expires when browser closes
                    else:
                        request.session.set_expiry(86400 * 7)  # 7 days
                    
                    # Redirect to intended page or dashboard
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Your account has been disabled. Please contact support.')
            else:
                # Log failed login attempt
                LoginAttempt.objects.create(
                    ip_address=ip_address,
                    username=username,
                    success=False
                )
                log_security_event('LOGIN_FAILED', f'Failed login attempt for username: {username}', ip_address, username)
                
                remaining_attempts = 5 - LoginAttempt.get_recent_failures(ip_address)
                if remaining_attempts > 0:
                    messages.error(request, f'Invalid username or password. You have {remaining_attempts} attempts remaining.')
                else:
                    messages.error(request, 'Too many failed attempts. Please try again in 15 minutes.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EnhancedLoginForm()
    
    return render(request, 'authentication/login.html', {'form': form})


@csrf_protect
@never_cache
def register_view(request):
    """Enhanced registration view with comprehensive validation."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    ip_address = get_client_ip(request)
    
    if request.method == 'POST':
        form = EnhancedRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    
                    # Send email verification
                    profile = UserProfile.objects.get(user=user)
                    send_verification_email(user, profile.email_verification_token)
                    
                    log_security_event('USER_REGISTERED', f'New user registered: {user.username}', ip_address, user.username)
                    
                    messages.success(request, 'Registration successful! Please check your email to verify your account.')
                    return redirect('login')
            except Exception as e:
                log_security_event('REGISTRATION_ERROR', f'Registration failed: {str(e)}', ip_address)
                messages.error(request, 'Registration failed. Please try again.')
        else:
            # Form has validation errors - they will be displayed in the template
            log_security_event('REGISTRATION_VALIDATION_ERROR', 'Form validation failed', ip_address)
    else:
        form = EnhancedRegistrationForm()
    
    return render(request, 'authentication/register.html', {'form': form})


def send_verification_email(user, token):
    """Send email verification to user."""
    verification_url = f"http://localhost:8000{reverse('verify_email', kwargs={'token': token})}"
    subject = 'Explorease - Verify your email address'
    message = f"""
    Hi {user.first_name},
    
    Welcome to Explorease! Please click the link below to verify your email address:
    
    {verification_url}
    
    If you didn't create an account with us, please ignore this email.
    
    Best regards,
    The Explorease Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@explorease.com',
        [user.email],
        fail_silently=False,
    )


def verify_email(request, token):
    """Verify user email address."""
    try:
        profile = UserProfile.objects.get(email_verification_token=token)
        if not profile.email_verified:
            profile.email_verified = True
            profile.save()
            
            log_security_event('EMAIL_VERIFIED', f'Email verified for user: {profile.user.username}', 
                             get_client_ip(request), profile.user.username)
            
            messages.success(request, 'Email verified successfully! You can now log in.')
        else:
            messages.info(request, 'Email is already verified.')
        
        return redirect('login')
    except UserProfile.DoesNotExist:
        log_security_event('EMAIL_VERIFICATION_FAILED', 'Invalid verification token', get_client_ip(request))
        raise Http404("Invalid verification link.")


@login_required
def dashboard_view(request):
    """User dashboard view."""
    return render(request, 'authentication/dashboard.html', {
        'user': request.user
    })


def logout_view(request):
    """Logout view with security logging."""
    if request.user.is_authenticated:
        username = request.user.username
        ip_address = get_client_ip(request)
        log_security_event('LOGOUT', f'User {username} logged out', ip_address, username)
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    
    return redirect('login')


def home_view(request):
    """Home page view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')
