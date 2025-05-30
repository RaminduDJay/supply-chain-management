"""
Supply Chain Management System - Helper Functions
Utility functions for common tasks throughout the application.
"""

from flask import session, request, current_app, url_for
from datetime import datetime, date, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
import re
import hashlib
import secrets
import string
from typing import Any, Dict, List, Optional, Union
import logging
import json
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

# =============================================
# AUTHENTICATION & SESSION HELPERS
# =============================================

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user information from session"""
    if 'user_name' not in session:
        return None
    
    return {
        'user_name': session.get('user_name'),
        'user_role': session.get('user_role'),
        'full_name': session.get('full_name'),
        'customer_id': session.get('customer_id'),
        'store_name': session.get('store_name'),
        'manager_id': session.get('manager_id')
    }

def get_user_role() -> Optional[str]:
    """Get current user's role"""
    return session.get('user_role')

def is_logged_in() -> bool:
    """Check if user is logged in"""
    return 'user_name' in session

def is_customer() -> bool:
    """Check if current user is a customer"""
    return session.get('user_role') == 'customer'

def is_store_manager() -> bool:
    """Check if current user is a store manager"""
    return session.get('user_role') == 'store_manager'

def is_main_manager() -> bool:
    """Check if current user is a main manager"""
    return session.get('user_role') == 'main_manager'

def is_manager() -> bool:
    """Check if current user is any type of manager"""
    return session.get('user_role') in ['store_manager', 'main_manager']

def get_user_store() -> Optional[str]:
    """Get current user's store (for store managers)"""
    return session.get('store_name')

def create_user_session(user_data: Dict[str, Any]):
    """Create user session with provided data"""
    session['user_name'] = user_data.get('user_name')
    session['user_role'] = user_data.get('role')
    session['full_name'] = user_data.get('full_name')
    session['customer_id'] = user_data.get('customer_id')
    session['store_name'] = user_data.get('store_name')
    session['manager_id'] = user_data.get('manager_id')
    session['last_activity'] = datetime.now().isoformat()
    session.permanent = True

def clear_user_session():
    """Clear user session"""
    session.clear()

# =============================================
# FORMATTING HELPERS
# =============================================

def format_currency(amount: Union[float, Decimal, str], currency: str = 'LKR') -> str:
    """
    Format currency values
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    try:
        if amount is None:
            return f"{currency} 0.00"
        
        # Convert to Decimal for precise calculation
        if isinstance(amount, str):
            amount = Decimal(amount)
        elif isinstance(amount, float):
            amount = Decimal(str(amount))
        elif not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        # Round to 2 decimal places
        amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Format with comma separators
        formatted = f"{amount:,.2f}"
        
        return f"{currency} {formatted}"
        
    except (ValueError, TypeError, AttributeError):
        return f"{currency} 0.00"

def format_number(number: Union[int, float, Decimal], decimals: int = 0) -> str:
    """
    Format numbers with comma separators
    
    Args:
        number: Number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted number string
    """
    try:
        if number is None:
            return "0"
        
        if decimals > 0:
            return f"{float(number):,.{decimals}f}"
        else:
            return f"{int(number):,}"
            
    except (ValueError, TypeError):
        return "0"

def format_date(date_obj: Union[datetime, date, str], format_str: str = '%Y-%m-%d') -> str:
    """
    Format date objects
    
    Args:
        date_obj: Date to format
        format_str: Format string
        
    Returns:
        Formatted date string
    """
    try:
        if date_obj is None:
            return ""
        
        if isinstance(date_obj, str):
            # Try to parse common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y']:
                try:
                    date_obj = datetime.strptime(date_obj, fmt)
                    break
                except ValueError:
                    continue
            else:
                return date_obj  # Return original string if parsing fails
        
        if isinstance(date_obj, datetime):
            return date_obj.strftime(format_str)
        elif isinstance(date_obj, date):
            return date_obj.strftime(format_str)
        
        return str(date_obj)
        
    except (ValueError, AttributeError):
        return str(date_obj) if date_obj else ""

def format_time(time_obj: Union[time, datetime, str], format_str: str = '%H:%M') -> str:
    """
    Format time objects
    
    Args:
        time_obj: Time to format
        format_str: Format string
        
    Returns:
        Formatted time string
    """
    try:
        if time_obj is None:
            return ""
        
        if isinstance(time_obj, str):
            try:
                time_obj = datetime.strptime(time_obj, '%H:%M:%S').time()
            except ValueError:
                try:
                    time_obj = datetime.strptime(time_obj, '%H:%M').time()
                except ValueError:
                    return time_obj
        
        if isinstance(time_obj, datetime):
            return time_obj.strftime(format_str)
        elif isinstance(time_obj, time):
            return time_obj.strftime(format_str)
        
        return str(time_obj)
        
    except (ValueError, AttributeError):
        return str(time_obj) if time_obj else ""

def format_percentage(value: Union[float, Decimal], decimals: int = 1) -> str:
    """
    Format percentage values
    
    Args:
        value: Value to format (0-100)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    try:
        if value is None:
            return "0%"
        
        return f"{float(value):.{decimals}f}%"
        
    except (ValueError, TypeError):
        return "0%"

def format_weight(weight: Union[float, Decimal], unit: str = 'kg') -> str:
    """
    Format weight values
    
    Args:
        weight: Weight value
        unit: Weight unit
        
    Returns:
        Formatted weight string
    """
    try:
        if weight is None or weight == 0:
            return f"0 {unit}"
        
        if weight >= 1000 and unit == 'kg':
            return f"{weight/1000:.2f} tonnes"
        
        return f"{float(weight):,.2f} {unit}"
        
    except (ValueError, TypeError):
        return f"0 {unit}"

def format_volume(volume: Union[float, Decimal], unit: str = 'm³') -> str:
    """
    Format volume values
    
    Args:
        volume: Volume value
        unit: Volume unit
        
    Returns:
        Formatted volume string
    """
    try:
        if volume is None or volume == 0:
            return f"0 {unit}"
        
        return f"{float(volume):,.2f} {unit}"
        
    except (ValueError, TypeError):
        return f"0 {unit}"

# =============================================
# VALIDATION HELPERS
# =============================================

def is_valid_email(email: str) -> bool:
    """Validate email address format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone: str) -> bool:
    """Validate Sri Lankan phone number format"""
    if not phone:
        return False
    
    # Remove spaces and dashes
    phone = re.sub(r'[\s-]', '', phone)
    
    # Sri Lankan phone number patterns
    patterns = [
        r'^\+94[0-9]{9}$',  # +94xxxxxxxxx
        r'^94[0-9]{9}$',    # 94xxxxxxxxx
        r'^0[0-9]{9}$',     # 0xxxxxxxxx
        r'^[0-9]{10}$'      # xxxxxxxxxx
    ]
    
    return any(re.match(pattern, phone) for pattern in patterns)

def is_valid_password(password: str) -> tuple[bool, List[str]]:
    """
    Validate password strength
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not password:
        errors.append("Password is required")
        return False, errors
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors

def is_valid_date(date_str: str, format_str: str = '%Y-%m-%d') -> bool:
    """Validate date string format"""
    if not date_str:
        return False
    
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False

def is_future_date(date_obj: Union[date, datetime, str], days_ahead: int = 0) -> bool:
    """Check if date is in the future (with optional minimum days ahead)"""
    try:
        if isinstance(date_obj, str):
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        elif isinstance(date_obj, datetime):
            date_obj = date_obj.date()
        
        min_date = date.today() + timedelta(days=days_ahead)
        return date_obj >= min_date
        
    except (ValueError, TypeError, AttributeError):
        return False

def sanitize_input(text: str, max_length: int = None) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\';]', '', text)
    
    # Strip whitespace
    text = text.strip()
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text

# =============================================
# CALCULATION HELPERS
# =============================================

def calculate_discount(amount: Decimal, discount_rate: Decimal) -> Decimal:
    """Calculate discount amount"""
    try:
        if not amount or not discount_rate:
            return Decimal('0.00')
        
        return (amount * discount_rate / 100).quantize(Decimal('0.01'))
        
    except (ValueError, TypeError):
        return Decimal('0.00')

def calculate_tax(amount: Decimal, tax_rate: Decimal = Decimal('0.00')) -> Decimal:
    """Calculate tax amount"""
    try:
        if not amount or not tax_rate:
            return Decimal('0.00')
        
        return (amount * tax_rate / 100).quantize(Decimal('0.01'))
        
    except (ValueError, TypeError):
        return Decimal('0.00')

def calculate_percentage(part: Union[int, float, Decimal], 
                        total: Union[int, float, Decimal]) -> float:
    """Calculate percentage"""
    try:
        if not total or total == 0:
            return 0.0
        
        return (float(part) / float(total)) * 100
        
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0

def round_to_nearest(value: Union[float, Decimal], nearest: Union[float, Decimal] = Decimal('0.01')) -> Decimal:
    """Round value to nearest specified amount"""
    try:
        if isinstance(value, (int, float)):
            value = Decimal(str(value))
        if isinstance(nearest, (int, float)):
            nearest = Decimal(str(nearest))
        
        return (value / nearest).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * nearest
        
    except (ValueError, TypeError):
        return Decimal('0.00')

# =============================================
# URL & SECURITY HELPERS
# =============================================

def is_safe_url(target: str) -> bool:
    """Check if URL is safe for redirects"""
    if not target:
        return False
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def generate_token(length: int = 32) -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(length)

def generate_password(length: int = 12) -> str:
    """Generate secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_string(text: str, salt: str = None) -> str:
    """Hash string with optional salt"""
    if salt:
        text = f"{text}{salt}"
    
    return hashlib.sha256(text.encode()).hexdigest()

def get_client_ip() -> str:
    """Get client IP address"""
    # Check for forwarded headers first (for load balancers/proxies)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    return request.remote_addr or 'unknown'

# =============================================
# FILE & DATA HELPERS
# =============================================

def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """Check if file extension is allowed"""
    if not filename:
        return False
    
    if not allowed_extensions:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_size_mb(file_size_bytes: int) -> float:
    """Convert file size from bytes to MB"""
    return file_size_bytes / (1024 * 1024)

def serialize_datetime(obj: Any) -> str:
    """Serialize datetime objects to ISO format"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, time):
        return obj.strftime('%H:%M:%S')
    return str(obj)

def parse_json_safe(json_str: str) -> Optional[Dict]:
    """Safely parse JSON string"""
    try:
        return json.loads(json_str) if json_str else None
    except (json.JSONDecodeError, TypeError):
        return None

# =============================================
# PAGINATION HELPERS
# =============================================

def paginate_query(query_result: List, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """
    Paginate query results
    
    Args:
        query_result: List of query results
        page: Current page number
        per_page: Items per page
        
    Returns:
        Dictionary with pagination info
    """
    if not query_result:
        return {
            'items': [],
            'total': 0,
            'page': 1,
            'per_page': per_page,
            'pages': 0,
            'has_prev': False,
            'has_next': False,
            'prev_num': None,
            'next_num': None
        }
    
    total = len(query_result)
    pages = (total + per_page - 1) // per_page  # Ceiling division
    
    # Ensure page is within valid range
    if page < 1:
        page = 1
    elif page > pages and pages > 0:
        page = pages
    
    # Calculate slice indices
    start = (page - 1) * per_page
    end = start + per_page
    items = query_result[start:end]
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages,
        'has_prev': page > 1,
        'has_next': page < pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < pages else None
    }

def get_pagination_info(total: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """Get pagination information without actual data"""
    pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    # Ensure page is within valid range
    if page < 1:
        page = 1
    elif page > pages and pages > 0:
        page = pages
    
    return {
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages,
        'has_prev': page > 1,
        'has_next': page < pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < pages else None,
        'start_index': (page - 1) * per_page + 1 if total > 0 else 0,
        'end_index': min(page * per_page, total)
    }

# =============================================
# FLASH MESSAGE HELPERS
# =============================================

def flash_success(message: str):
    """Flash success message"""
    from flask import flash
    flash(message, 'success')

def flash_error(message: str):
    """Flash error message"""
    from flask import flash
    flash(message, 'error')

def flash_warning(message: str):
    """Flash warning message"""
    from flask import flash
    flash(message, 'warning')

def flash_info(message: str):
    """Flash info message"""
    from flask import flash
    flash(message, 'info')

# =============================================
# BUSINESS LOGIC HELPERS
# =============================================

def get_order_status_color(status: str) -> str:
    """Get Bootstrap color class for order status"""
    status_colors = {
        'pending': 'warning',
        'confirmed': 'info',
        'assigned_train': 'primary',
        'in_transit_rail': 'primary',
        'at_warehouse': 'secondary',
        'assigned_truck': 'info',
        'out_for_delivery': 'warning',
        'delivered': 'success',
        'cancelled': 'danger',
        'returned': 'dark'
    }
    return status_colors.get(status, 'secondary')

def get_priority_color(priority: str) -> str:
    """Get Bootstrap color class for priority"""
    priority_colors = {
        'standard': 'secondary',
        'high': 'warning',
        'urgent': 'danger'
    }
    return priority_colors.get(priority, 'secondary')

def calculate_delivery_date(order_date: date = None, min_days: int = 7) -> date:
    """Calculate minimum delivery date"""
    if not order_date:
        order_date = date.today()
    
    return order_date + timedelta(days=min_days)

def get_customer_type_info(customer_type: str) -> Dict[str, Any]:
    """Get customer type information"""
    from config import BusinessRules
    return BusinessRules.CUSTOMER_TYPES.get(customer_type, {
        'discount_rate': 0.00,
        'min_order_qty': 1,
        'description': 'Unknown'
    })

def format_order_number(order_id: int) -> str:
    """Format order ID as order number"""
    return f"ORD-{order_id:06d}"

def format_tracking_number(order_id: int, prefix: str = "TRK") -> str:
    """Generate tracking number for order"""
    timestamp = int(datetime.now().timestamp())
    return f"{prefix}-{order_id:06d}-{timestamp}"

# =============================================
# DEBUGGING HELPERS
# =============================================

def debug_log(message: str, data: Any = None):
    """Log debug information"""
    if current_app.debug:
        if data:
            logger.debug(f"{message}: {data}")
        else:
            logger.debug(message)

def get_debug_info() -> Dict[str, Any]:
    """Get debug information for troubleshooting"""
    if not current_app.debug:
        return {}
    
    return {
        'user_session': dict(session),
        'request_method': request.method,
        'request_path': request.path,
        'request_args': dict(request.args),
        'request_form': dict(request.form),
        'client_ip': get_client_ip(),
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'timestamp': datetime.now().isoformat()
    }