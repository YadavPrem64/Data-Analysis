import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import connection
from django.contrib.auth.hashers import check_password, make_password
import json
import traceback
from datetime import datetime

# Set up logger for authentication debugging
logger = logging.getLogger('auth_debug')

def debug_log(message, level='info'):
    """Helper function to log debug messages with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"[{timestamp}] {message}"
    
    if level == 'error':
        logger.error(full_message)
    elif level == 'warning':
        logger.warning(full_message)
    else:
        logger.info(full_message)

def login_view(request):
    """Enhanced login view with comprehensive debugging"""
    debug_log("=== LOGIN VIEW ACCESSED ===")
    debug_log(f"Request method: {request.method}")
    debug_log(f"Request user: {request.user}")
    debug_log(f"Is user authenticated: {request.user.is_authenticated}")
    debug_log(f"Session key: {request.session.session_key}")
    
    if request.method == 'POST':
        debug_log("=== POST REQUEST RECEIVED ===")
        
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        debug_log(f"Received username: '{username}'")
        debug_log(f"Password length: {len(password) if password else 0}")
        debug_log(f"POST data keys: {list(request.POST.keys())}")
        
        # Log raw form data (without password)
        safe_post_data = {k: v for k, v in request.POST.items() if k != 'password'}
        debug_log(f"Safe POST data: {safe_post_data}")
        
        if not username:
            debug_log("ERROR: Empty username provided", 'error')
            messages.error(request, "Username is required")
            return render(request, 'authentication/login.html')
        
        if not password:
            debug_log("ERROR: Empty password provided", 'error')
            messages.error(request, "Password is required")
            return render(request, 'authentication/login.html')
        
        # Check if user exists
        debug_log(f"Checking if user '{username}' exists in database...")
        try:
            user_obj = User.objects.get(username=username)
            debug_log(f"User found: {user_obj}")
            debug_log(f"User ID: {user_obj.id}")
            debug_log(f"User is_active: {user_obj.is_active}")
            debug_log(f"User is_staff: {user_obj.is_staff}")
            debug_log(f"User last_login: {user_obj.last_login}")
            debug_log(f"User date_joined: {user_obj.date_joined}")
            debug_log(f"Stored password hash: {user_obj.password[:20]}...")
            
            # Test password verification
            debug_log("Testing password verification...")
            password_check = check_password(password, user_obj.password)
            debug_log(f"Password check result: {password_check}")
            
        except User.DoesNotExist:
            debug_log(f"ERROR: User '{username}' does not exist in database", 'error')
            messages.error(request, "Invalid username or password")
            return render(request, 'authentication/login.html')
        except Exception as e:
            debug_log(f"ERROR: Exception while checking user: {str(e)}", 'error')
            debug_log(f"Exception traceback: {traceback.format_exc()}", 'error')
            messages.error(request, "Database error occurred")
            return render(request, 'authentication/login.html')
        
        # Attempt authentication
        debug_log("Attempting Django authentication...")
        try:
            user = authenticate(request, username=username, password=password)
            debug_log(f"Authentication result: {user}")
            
            if user is not None:
                debug_log("Authentication successful!")
                debug_log(f"Authenticated user: {user}")
                debug_log(f"User is_active: {user.is_active}")
                
                if user.is_active:
                    debug_log("User is active, proceeding with login...")
                    login(request, user)
                    debug_log("Login successful!")
                    debug_log(f"Session after login: {request.session.session_key}")
                    messages.success(request, "Login successful!")
                    return redirect('dashboard')
                else:
                    debug_log("ERROR: User account is inactive", 'error')
                    messages.error(request, "Account is inactive")
            else:
                debug_log("ERROR: Authentication failed - invalid credentials", 'error')
                messages.error(request, "Invalid username or password")
                
        except Exception as e:
            debug_log(f"ERROR: Exception during authentication: {str(e)}", 'error')
            debug_log(f"Exception traceback: {traceback.format_exc()}", 'error')
            messages.error(request, "Authentication error occurred")
    
    debug_log("Rendering login template...")
    return render(request, 'authentication/login.html')

@csrf_exempt
def debug_auth_view(request):
    """Dedicated debug view for testing authentication step by step"""
    debug_log("=== DEBUG AUTH VIEW ACCESSED ===")
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            debug_log(f"Debug test for username: '{username}'")
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'input_received': {
                    'username': username,
                    'password_length': len(password) if password else 0,
                    'password_provided': bool(password)
                },
                'database_check': {},
                'password_verification': {},
                'django_auth': {},
                'session_info': {},
                'recommendations': []
            }
            
            # Database connection test
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM auth_user")
                    user_count = cursor.fetchone()[0]
                    result['database_check'] = {
                        'connection': 'SUCCESS',
                        'total_users': user_count
                    }
                    debug_log(f"Database connection successful, {user_count} users found")
            except Exception as e:
                result['database_check'] = {
                    'connection': 'FAILED',
                    'error': str(e)
                }
                debug_log(f"Database connection failed: {str(e)}", 'error')
            
            # User lookup
            if username:
                try:
                    user_obj = User.objects.get(username=username)
                    result['database_check']['user_exists'] = True
                    result['database_check']['user_info'] = {
                        'id': user_obj.id,
                        'username': user_obj.username,
                        'email': user_obj.email,
                        'is_active': user_obj.is_active,
                        'is_staff': user_obj.is_staff,
                        'is_superuser': user_obj.is_superuser,
                        'last_login': user_obj.last_login.isoformat() if user_obj.last_login else None,
                        'date_joined': user_obj.date_joined.isoformat(),
                        'password_hash_start': user_obj.password[:20] + '...'
                    }
                    debug_log(f"User lookup successful: {user_obj}")
                    
                    # Password verification test
                    if password:
                        password_valid = check_password(password, user_obj.password)
                        result['password_verification'] = {
                            'check_password_result': password_valid,
                            'hash_algorithm': user_obj.password.split('$')[0] if '$' in user_obj.password else 'unknown'
                        }
                        debug_log(f"Password verification: {password_valid}")
                    
                except User.DoesNotExist:
                    result['database_check']['user_exists'] = False
                    result['recommendations'].append("User does not exist - check username spelling")
                    debug_log(f"User '{username}' not found")
                except Exception as e:
                    result['database_check']['user_lookup_error'] = str(e)
                    debug_log(f"User lookup error: {str(e)}", 'error')
            
            # Django authentication test
            if username and password:
                try:
                    auth_user = authenticate(username=username, password=password)
                    result['django_auth'] = {
                        'authenticate_result': auth_user is not None,
                        'user_object': str(auth_user) if auth_user else None
                    }
                    debug_log(f"Django authenticate result: {auth_user}")
                except Exception as e:
                    result['django_auth'] = {
                        'authenticate_error': str(e)
                    }
                    debug_log(f"Django authentication error: {str(e)}", 'error')
            
            # Session information
            result['session_info'] = {
                'session_key': request.session.session_key,
                'session_engine': settings.SESSION_ENGINE,
                'is_authenticated': request.user.is_authenticated,
                'current_user': str(request.user) if request.user.is_authenticated else 'AnonymousUser'
            }
            
            # Add recommendations based on findings
            if not result['database_check'].get('user_exists'):
                result['recommendations'].append("Create a test user with: python manage.py createsuperuser")
            elif result['password_verification'].get('check_password_result') is False:
                result['recommendations'].append("Password is incorrect - reset it or try a different password")
            elif result['django_auth'].get('authenticate_result') is False:
                result['recommendations'].append("Django authentication failed - check authentication backends")
            
            debug_log(f"Debug result: {result}")
            return JsonResponse(result, indent=2)
            
        except Exception as e:
            debug_log(f"Debug view error: {str(e)}", 'error')
            return JsonResponse({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)
    
    return render(request, 'authentication/debug_auth.html')

@login_required
def dashboard_view(request):
    """Dashboard view for authenticated users"""
    debug_log(f"Dashboard accessed by user: {request.user}")
    return render(request, 'authentication/dashboard.html', {
        'user': request.user
    })

def logout_view(request):
    """Logout view with debugging"""
    debug_log(f"Logout requested by user: {request.user}")
    logout(request)
    debug_log("User logged out successfully")
    messages.success(request, "You have been logged out successfully")
    return redirect('login')

def user_list_view(request):
    """Debug view to list all users"""
    debug_log("User list view accessed")
    
    try:
        users = User.objects.all()
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
                'last_login': user.last_login,
                'date_joined': user.date_joined,
                'password_hash': user.password[:30] + '...' if user.password else 'No password'
            })
        
        debug_log(f"Found {len(user_data)} users")
        
        return render(request, 'authentication/user_list.html', {
            'users': user_data,
            'total_count': len(user_data)
        })
        
    except Exception as e:
        debug_log(f"Error in user list view: {str(e)}", 'error')
        messages.error(request, f"Error loading users: {str(e)}")
        return render(request, 'authentication/user_list.html', {
            'users': [],
            'error': str(e)
        })

def database_status_view(request):
    """View to check database status and configuration"""
    debug_log("Database status view accessed")
    
    status = {
        'database': {},
        'tables': {},
        'auth_config': {},
        'session_config': {}
    }
    
    try:
        # Database connection test
        with connection.cursor() as cursor:
            # Get database info
            cursor.execute("SELECT sqlite_version()")
            db_version = cursor.fetchone()[0]
            
            status['database'] = {
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME'],
                'version': db_version,
                'connection': 'SUCCESS'
            }
            
            # Check if tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'auth_%' OR name LIKE 'django_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            status['tables'] = {
                'available': tables,
                'auth_user_exists': 'auth_user' in tables,
                'auth_permission_exists': 'auth_permission' in tables,
                'django_session_exists': 'django_session' in tables
            }
            
            # Get user count
            if 'auth_user' in tables:
                cursor.execute("SELECT COUNT(*) FROM auth_user")
                user_count = cursor.fetchone()[0]
                status['tables']['user_count'] = user_count
            
    except Exception as e:
        status['database'] = {
            'connection': 'FAILED',
            'error': str(e)
        }
        debug_log(f"Database status check failed: {str(e)}", 'error')
    
    # Authentication configuration
    status['auth_config'] = {
        'auth_user_model': settings.AUTH_USER_MODEL,
        'login_url': settings.LOGIN_URL,
        'login_redirect_url': settings.LOGIN_REDIRECT_URL,
        'logout_redirect_url': settings.LOGOUT_REDIRECT_URL,
        'authentication_backends': settings.AUTHENTICATION_BACKENDS,
        'password_hashers': [hasher.split('.')[-1] for hasher in settings.PASSWORD_HASHERS]
    }
    
    # Session configuration
    status['session_config'] = {
        'session_engine': settings.SESSION_ENGINE,
        'session_cookie_age': settings.SESSION_COOKIE_AGE,
        'session_cookie_secure': settings.SESSION_COOKIE_SECURE,
        'session_cookie_httponly': settings.SESSION_COOKIE_HTTPONLY,
        'session_save_every_request': settings.SESSION_SAVE_EVERY_REQUEST
    }
    
    debug_log(f"Database status check complete: {status}")
    
    return render(request, 'authentication/database_status.html', {
        'status': status
    })
