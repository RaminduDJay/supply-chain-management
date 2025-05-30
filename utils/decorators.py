"""
Supply Chain Management System - Decorators
Custom decorators for authentication, authorization, and other utilities.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify, g, current_app
from datetime import datetime
import logging
import time
from typing import List, Callable, Any

logger = logging.getLogger(__name__)

# =============================================
# AUTHENTICATION DECORATORS
# =============================================

def login_required(f):
    """
    Decorator to require user authentication
    
    Usage:
        @login_required
        def protected_route():
            return "Protected content"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' not in session:
            flash('Please log in to access this page.', 'warning')
            # Store the original URL to redirect after login
            session['next_url'] = request.url
            return redirect(url_for('auth.login'))
        
        # Check if session is still valid
        if not _is_session_valid():
            session.clear()
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def role_required(*allowed_roles):
    """
    Decorator to require specific user roles
    
    Args:
        *allowed_roles: List of allowed roles
        
    Usage:
        @role_required('admin', 'manager')
        def admin_only_route():
            return "Admin content"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_name' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            user_role = session.get('user_role')
            if user_role not in allowed_roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def customer_required(f):
    """Decorator to require customer role"""
    @wraps(f)
    @login_required
    @role_required('customer')
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    """Decorator to require manager role (store or main)"""
    @wraps(f)
    @login_required
    @role_required('store_manager', 'main_manager')
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def store_manager_required(f):
    """Decorator to require store manager role"""
    @wraps(f)
    @login_required
    @role_required('store_manager')
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def main_manager_required(f):
    """Decorator to require main manager role"""
    @wraps(f)
    @login_required
    @role_required('main_manager')
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

# =============================================
# API DECORATORS
# =============================================

def api_key_required(f):
    """
    Decorator to require API key for API endpoints
    
    Usage:
        @api_key_required
        def api_endpoint():
            return jsonify({"data": "secret"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key (you would implement actual validation)
        if not _validate_api_key(api_key):
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def json_required(f):
    """
    Decorator to require JSON content type
    
    Usage:
        @json_required
        def api_endpoint():
            data = request.get_json()
            return jsonify({"received": data})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    
    return decorated_function

def api_response(f):
    """
    Decorator to standardize API responses
    
    Usage:
        @api_response
        def api_endpoint():
            return {"data": "value"}  # Will be wrapped in standard format
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            
            # If it's already a Response object, return as-is
            if hasattr(result, 'status_code'):
                return result
            
            # Wrap in standard API response format
            if isinstance(result, dict):
                response = {
                    'success': True,
                    'data': result,
                    'timestamp': datetime.now().isoformat()
                }
                return jsonify(response)
            
            return result
            
        except Exception as e:
            logger.error(f"API error in {f.__name__}: {e}")
            error_response = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return jsonify(error_response), 500
    
    return decorated_function

# =============================================
# RATE LIMITING DECORATORS
# =============================================

def rate_limit(max_requests: int = 100, per_seconds: int = 3600, key_func: Callable = None):
    """
    Decorator for rate limiting
    
    Args:
        max_requests: Maximum number of requests
        per_seconds: Time window in seconds
        key_func: Function to generate unique key for rate limiting
        
    Usage:
        @rate_limit(max_requests=10, per_seconds=60)
        def limited_endpoint():
            return "Limited content"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func()
            else:
                key = _get_rate_limit_key()
            
            # Check rate limit (simplified implementation)
            if _is_rate_limited(key, max_requests, per_seconds):
                if request.is_json:
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                else:
                    flash('Too many requests. Please try again later.', 'warning')
                    return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# =============================================
# CACHING DECORATORS
# =============================================

def cache_response(timeout: int = 300, key_prefix: str = None):
    """
    Decorator to cache response
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
        
    Usage:
        @cache_response(timeout=600)
        def expensive_operation():
            return {"data": "expensive_result"}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(f.__name__, args, kwargs, key_prefix)
            
            # Try to get from cache
            cached_result = _get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            _set_cache(cache_key, result, timeout)
            
            return result
        
        return decorated_function
    return decorator

# =============================================
# LOGGING DECORATORS
# =============================================

def log_execution_time(f):
    """
    Decorator to log function execution time
    
    Usage:
        @log_execution_time
        def slow_function():
            time.sleep(1)
            return "done"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(f"Function {f.__name__} executed in {execution_time:.4f} seconds")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function {f.__name__} failed after {execution_time:.4f} seconds: {e}")
            raise
    
    return decorated_function

def audit_log(action: str = None, resource: str = None):
    """
    Decorator to log user actions for audit trail
    
    Args:
        action: Action being performed
        resource: Resource being acted upon
        
    Usage:
        @audit_log(action="CREATE", resource="ORDER")
        def create_order():
            return "Order created"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_name = session.get('user_name')
            user_role = session.get('user_role')
            ip_address = request.remote_addr
            
            # Determine action and resource if not provided
            action_name = action or f.__name__.upper()
            resource_name = resource or "UNKNOWN"
            
            try:
                result = f(*args, **kwargs)
                
                # Log successful action
                _log_audit_entry(
                    user_name=user_name,
                    user_role=user_role,
                    action=action_name,
                    resource=resource_name,
                    status="SUCCESS",
                    ip_address=ip_address,
                    details=f"Function: {f.__name__}"
                )
                
                return result
                
            except Exception as e:
                # Log failed action
                _log_audit_entry(
                    user_name=user_name,
                    user_role=user_role,
                    action=action_name,
                    resource=resource_name,
                    status="FAILED",
                    ip_address=ip_address,
                    details=f"Function: {f.__name__}, Error: {str(e)}"
                )
                raise
        
        return decorated_function
    return decorator

# =============================================
# VALIDATION DECORATORS
# =============================================

def validate_json(*required_fields):
    """
    Decorator to validate JSON request data
    
    Args:
        *required_fields: List of required field names
        
    Usage:
        @validate_json('name', 'email')
        def create_user():
            data = request.get_json()
            return f"Creating user {data['name']}"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON data'}), 400
            
            # Check required fields
            missing_fields = []
            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                return jsonify({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_form(*required_fields):
    """
    Decorator to validate form data
    
    Args:
        *required_fields: List of required field names
        
    Usage:
        @validate_form('username', 'password')
        def login():
            username = request.form['username']
            return f"Logging in {username}"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            missing_fields = []
            for field in required_fields:
                if field not in request.form or not request.form[field].strip():
                    missing_fields.append(field)
            
            if missing_fields:
                flash(f'Missing required fields: {", ".join(missing_fields)}', 'error')
                return redirect(request.referrer or url_for('index'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# =============================================
# HELPER FUNCTIONS
# =============================================

def _is_session_valid() -> bool:
    """Check if current session is valid"""
    last_activity = session.get('last_activity')
    if not last_activity:
        return False
    
    try:
        last_activity_dt = datetime.fromisoformat(last_activity)
        timeout = current_app.config.get('PERMANENT_SESSION_LIFETIME')
        
        if datetime.now() - last_activity_dt > timeout:
            return False
        
        return True
        
    except (ValueError, TypeError):
        return False

def _validate_api_key(api_key: str) -> bool:
    """Validate API key (implement actual validation logic)"""
    # This is a simplified implementation
    # In production, you would validate against a database or service
    valid_keys = current_app.config.get('API_KEYS', [])
    return api_key in valid_keys

def _get_rate_limit_key() -> str:
    """Generate rate limit key based on user or IP"""
    if 'user_name' in session:
        return f"rate_limit:user:{session['user_name']}"
    else:
        return f"rate_limit:ip:{request.remote_addr}"

def _is_rate_limited(key: str, max_requests: int, per_seconds: int) -> bool:
    """Check if request should be rate limited (simplified implementation)"""
    # This is a simplified in-memory implementation
    # In production, you would use Redis or another store
    if not hasattr(g, 'rate_limit_store'):
        g.rate_limit_store = {}
    
    now = time.time()
    window_start = now - per_seconds
    
    # Clean old entries
    if key in g.rate_limit_store:
        g.rate_limit_store[key] = [
            timestamp for timestamp in g.rate_limit_store[key]
            if timestamp > window_start
        ]
    else:
        g.rate_limit_store[key] = []
    
    # Check if limit exceeded
    if len(g.rate_limit_store[key]) >= max_requests:
        return True
    
    # Add current request
    g.rate_limit_store[key].append(now)
    return False

def _generate_cache_key(func_name: str, args: tuple, kwargs: dict, prefix: str = None) -> str:
    """Generate cache key for function call"""
    import hashlib
    
    key_parts = [func_name]
    if prefix:
        key_parts.insert(0, prefix)
    
    # Add args and kwargs to key
    if args:
        key_parts.extend(str(arg) for arg in args)
    if kwargs:
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    
    # Create hash for consistent key length
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def _get_from_cache(key: str):
    """Get value from cache (simplified implementation)"""
    # This is a simplified implementation
    # In production, you would use Redis or another cache store
    if not hasattr(g, 'cache_store'):
        g.cache_store = {}
    
    cache_entry = g.cache_store.get(key)
    if cache_entry:
        if time.time() < cache_entry['expires']:
            return cache_entry['value']
        else:
            del g.cache_store[key]
    
    return None

def _set_cache(key: str, value: Any, timeout: int):
    """Set value in cache (simplified implementation)"""
    if not hasattr(g, 'cache_store'):
        g.cache_store = {}
    
    g.cache_store[key] = {
        'value': value,
        'expires': time.time() + timeout
    }

def _log_audit_entry(user_name: str, user_role: str, action: str, resource: str, 
                    status: str, ip_address: str, details: str = None):
    """Log audit entry to database"""
    try:
        from database.connection import get_db
        
        db = get_db()
        db.log_audit_entry(
            table_name='system_audit',
            operation=action,
            record_id=resource,
            new_values={
                'user_name': user_name,
                'user_role': user_role,
                'action': action,
                'resource': resource,
                'status': status,
                'details': details
            },
            user_name=user_name,
            ip_address=ip_address
        )
        
    except Exception as e:
        logger.error(f"Failed to log audit entry: {e}")

# =============================================
# DECORATOR COMBINATIONS
# =============================================

def api_endpoint(methods: List[str] = None, require_auth: bool = True, 
                require_json: bool = False, rate_limit_config: dict = None):
    """
    Combined decorator for API endpoints
    
    Args:
        methods: HTTP methods allowed
        require_auth: Whether authentication is required
        require_json: Whether JSON content type is required
        rate_limit_config: Rate limiting configuration
        
    Usage:
        @api_endpoint(methods=['POST'], require_json=True)
        def api_create():
            return {"created": True}
    """
    def decorator(f):
        # Apply decorators in reverse order
        decorated = f
        
        # Add API response formatting
        decorated = api_response(decorated)
        
        # Add rate limiting if configured
        if rate_limit_config:
            decorated = rate_limit(**rate_limit_config)(decorated)
        
        # Add JSON requirement if needed
        if require_json:
            decorated = json_required(decorated)
        
        # Add authentication if required
        if require_auth:
            decorated = login_required(decorated)
        
        return decorated
    
    return decorator

def secure_route(roles: List[str] = None, audit_action: str = None, 
                cache_timeout: int = None):
    """
    Combined decorator for secure web routes
    
    Args:
        roles: Required user roles
        audit_action: Action to log for audit
        cache_timeout: Cache timeout in seconds
        
    Usage:
        @secure_route(roles=['admin'], audit_action='VIEW_REPORTS')
        def admin_reports():
            return render_template('reports.html')
    """
    def decorator(f):
        decorated = f
        
        # Add caching if specified
        if cache_timeout:
            decorated = cache_response(timeout=cache_timeout)(decorated)
        
        # Add audit logging if specified
        if audit_action:
            decorated = audit_log(action=audit_action)(decorated)
        
        # Add role requirement if specified
        if roles:
            decorated = role_required(*roles)(decorated)
        else:
            decorated = login_required(decorated)
        
        return decorated
    
    return decorator