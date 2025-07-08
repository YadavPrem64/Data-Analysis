"""
Utility functions for the authentication app.
"""
from django.utils import timezone
from .models import LoginAttempt
import logging

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


def sanitize_input(input_string):
    """Sanitize user input to prevent XSS."""
    if not input_string:
        return input_string
    
    # Basic XSS prevention - Django's escape function is used in views
    # This is an additional layer for specific cases
    dangerous_chars = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;'
    }
    
    for char, replacement in dangerous_chars.items():
        input_string = input_string.replace(char, replacement)
    
    return input_string