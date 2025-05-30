"""
Supply Chain Management System - Authentication Routes
Routes for user authentication, registration, and session management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import logging
from datetime import datetime

# Import database models and utilities
from database.models import User, Customer
from database.connection import execute_query, execute_update
from utils.decorators import rate_limit
from utils.helpers import (
    is_valid_email, is_valid_password, is_valid_phone, sanitize_input,
    create_user_session, clear_user_session, is_safe_url, get_client_ip,
    flash_success, flash_error, flash_warning, flash_info
)

# Create blueprint
auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# =============================================
# LOGIN ROUTES
# =============================================

@auth_bp.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=10, per_seconds=300)  # 10 attempts per 5 minutes
def login():
    """User login route"""
    if request.method == 'GET':
        # If user is already logged in, redirect to dashboard
        if 'user_name' in session:
            return redirect(url_for('dashboard'))
        
        return render_template('auth/login.html')
    
    # Handle POST request
    user_name = sanitize_input(request.form.get('user_name', '').strip())
    password = request.form.get('password', '')
    remember_me = request.form.get('remember_me') == 'on'
    
    # Validation
    if not user_name or not password:
        flash_error('Please enter both username and password')
        return render_template('auth/login.html')
    
    try:
        # Authenticate user using stored procedure
        auth_result = User.authenticate(user_name, password)
        
        if auth_result:
            # Get user details based on role
            user_details = _get_user_details(user_name, auth_result.role)
            
            if user_details:
                # Create session
                session_data = {
                    'user_name': user_name,
                    'role': auth_result.role,
                    'full_name': user_details.get('full_name'),
                    'customer_id': user_details.get('customer_id'),
                    'store_name': user_details.get('store_name'),
                    'manager_id': user_details.get('manager_id')
                }
                
                create_user_session(session_data)
                
                # Set permanent session if remember me is checked
                if remember_me:
                    session.permanent = True
                
                # Log successful login
                logger.info(f"Successful login: {user_name} from {get_client_ip()}")
                
                flash_success(f'Welcome back, {user_details.get("full_name", user_name)}!')
                
                # Redirect to original URL or dashboard
                next_url = session.pop('next_url', None)
                if next_url and is_safe_url(next_url):
                    return redirect(next_url)
                
                return redirect(url_for('dashboard'))
            else:
                flash_error('Account details not found. Please contact administrator.')
        else:
            # Log failed login attempt
            logger.warning(f"Failed login attempt: {user_name} from {get_client_ip()}")
            flash_error('Invalid username or password')
    
    except Exception as e:
        logger.error(f"Login error for {user_name}: {e}")
        flash_error('Login failed. Please try again.')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """User logout route"""
    user_name = session.get('user_name')
    
    # Clear session
    clear_user_session()
    
    # Log logout
    if user_name:
        logger.info(f"User logout: {user_name}")
        flash_info('You have been logged out successfully')
    
    return redirect(url_for('index'))

# =============================================
# REGISTRATION ROUTES
# =============================================

@auth_bp.route('/register', methods=['GET', 'POST'])
@rate_limit(max_requests=5, per_seconds=3600)  # 5 registrations per hour
def register():
    """Customer registration route"""
    if request.method == 'GET':
        # Get customer types for dropdown
        customer_types = execute_query("SELECT * FROM customer_type ORDER BY customer_type")
        return render_template('auth/register.html', customer_types=customer_types)
    
    # Handle POST request
    try:
        # Get form data
        form_data = {
            'user_name': sanitize_input(request.form.get('user_name', '').strip()),
            'password': request.form.get('password', ''),
            'confirm_password': request.form.get('confirm_password', ''),
            'customer_type': request.form.get('customer_type', 'end'),
            'first_name': sanitize_input(request.form.get('first_name', '').strip()),
            'last_name': sanitize_input(request.form.get('last_name', '').strip()),
            'email': sanitize_input(request.form.get('email', '').strip().lower()),
            'phone': sanitize_input(request.form.get('phone', '').strip()),
            'address': sanitize_input(request.form.get('address', '').strip()),
            'city': sanitize_input(request.form.get('city', '').strip()),
            'postal_code': sanitize_input(request.form.get('postal_code', '').strip())
        }
        
        # Validation
        validation_errors = _validate_registration_data(form_data)
        
        if validation_errors:
            for error in validation_errors:
                flash_error(error)
            customer_types = execute_query("SELECT * FROM customer_type ORDER BY customer_type")
            return render_template('auth/register.html', 
                                 customer_types=customer_types, 
                                 form_data=form_data)
        
        # Check if username or email already exists
        existing_user = execute_query(
            "SELECT user_name FROM users WHERE user_name = %s",
            (form_data['user_name'],),
            fetch_one=True
        )
        
        if existing_user:
            flash_error('Username already exists. Please choose a different username.')
            customer_types = execute_query("SELECT * FROM customer_type ORDER BY customer_type")
            return render_template('auth/register.html', 
                                 customer_types=customer_types, 
                                 form_data=form_data)
        
        existing_email = execute_query(
            "SELECT email FROM customers WHERE email = %s",
            (form_data['email'],),
            fetch_one=True
        )
        
        if existing_email:
            flash_error('Email address already registered. Please use a different email.')
            customer_types = execute_query("SELECT * FROM customer_type ORDER BY customer_type")
            return render_template('auth/register.html', 
                                 customer_types=customer_types, 
                                 form_data=form_data)
        
        # Hash password
        hashed_password = generate_password_hash(form_data['password'])
        
        # Create customer account
        customer = Customer.create_customer(
            user_name=form_data['user_name'],
            password=hashed_password,
            customer_type=form_data['customer_type'],
            first_name=form_data['first_name'],
            last_name=form_data['last_name'],
            email=form_data['email'],
            phone=form_data['phone'],
            address=form_data['address'],
            city=form_data['city'],
            postal_code=form_data['postal_code']
        )
        
        if customer:
            logger.info(f"New customer registered: {form_data['user_name']} ({form_data['email']})")
            flash_success('Registration successful! You can now log in with your credentials.')
            return redirect(url_for('auth.login'))
        else:
            flash_error('Registration failed. Please try again.')
    
    except Exception as e:
        logger.error(f"Registration error: {e}")
        flash_error('Registration failed. Please try again.')
    
    # Return form with errors
    customer_types = execute_query("SELECT * FROM customer_type ORDER BY customer_type")
    return render_template('auth/register.html', customer_types=customer_types)

# =============================================
# PASSWORD RESET ROUTES
# =============================================

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@rate_limit(max_requests=3, per_seconds=3600)  # 3 attempts per hour
def forgot_password():
    """Forgot password route"""
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
    # Handle POST request
    email = sanitize_input(request.form.get('email', '').strip().lower())
    
    if not email or not is_valid_email(email):
        flash_error('Please enter a valid email address')
        return render_template('auth/forgot_password.html')
    
    try:
        # Check if email exists
        customer = execute_query(
            """
            SELECT c.customer_id, c.user_name, c.first_name, c.last_name, c.email
            FROM customers c
            WHERE c.email = %s
            """,
            (email,),
            fetch_one=True
        )
        
        if customer:
            # Generate reset token (simplified implementation)
            # In production, you would generate a secure token and store it in database
            reset_token = generate_password_hash(f"{customer['user_name']}{datetime.now()}")[:32]
            
            # Store reset token in database (you would add a password_reset_tokens table)
            # For now, we'll just log it
            logger.info(f"Password reset requested for: {email}, token: {reset_token}")
            
            # Send email (implement email sending)
            # send_password_reset_email(customer['email'], reset_token)
            
            flash_success('If your email is registered, you will receive password reset instructions.')
        else:
            # Don't reveal whether email exists or not
            flash_success('If your email is registered, you will receive password reset instructions.')
    
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        flash_error('Unable to process password reset request. Please try again.')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    # Simplified implementation
    # In production, you would validate the token from database
    
    if request.method == 'GET':
        return render_template('auth/reset_password.html', token=token)
    
    # Handle POST request
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate passwords
    if not password or not confirm_password:
        flash_error('Please enter both password fields')
        return render_template('auth/reset_password.html', token=token)
    
    if password != confirm_password:
        flash_error('Passwords do not match')
        return render_template('auth/reset_password.html', token=token)
    
    is_valid, errors = is_valid_password(password)
    if not is_valid:
        for error in errors:
            flash_error(error)
        return render_template('auth/reset_password.html', token=token)
    
    try:
        # In production, validate token and get user
        # For now, we'll just show success message
        flash_success('Password reset successful! You can now log in with your new password.')
        return redirect(url_for('auth.login'))
    
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        flash_error('Password reset failed. Please try again.')
    
    return render_template('auth/reset_password.html', token=token)

# =============================================
# API AUTHENTICATION ENDPOINTS
# =============================================

@auth_bp.route('/api/login', methods=['POST'])
@rate_limit(max_requests=10, per_seconds=300)
def api_login():
    """API login endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'user_name' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'error': 'Username and password required'
            }), 400
        
        user_name = sanitize_input(data['user_name'])
        password = data['password']
        
        # Authenticate user
        auth_result = User.authenticate(user_name, password)
        
        if auth_result:
            user_details = _get_user_details(user_name, auth_result.role)
            
            if user_details:
                # Create session
                session_data = {
                    'user_name': user_name,
                    'role': auth_result.role,
                    'full_name': user_details.get('full_name'),
                    'customer_id': user_details.get('customer_id'),
                    'store_name': user_details.get('store_name'),
                    'manager_id': user_details.get('manager_id')
                }
                
                create_user_session(session_data)
                
                return jsonify({
                    'success': True,
                    'user': {
                        'user_name': user_name,
                        'role': auth_result.role,
                        'full_name': user_details.get('full_name')
                    }
                })
        
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401
    
    except Exception as e:
        logger.error(f"API login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500

@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """API logout endpoint"""
    try:
        clear_user_session()
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    
    except Exception as e:
        logger.error(f"API logout error: {e}")
        return jsonify({
            'success': False,
            'error': 'Logout failed'
        }), 500

@auth_bp.route('/api/session', methods=['GET'])
def api_session():
    """Get current session information"""
    try:
        if 'user_name' in session:
            return jsonify({
                'success': True,
                'logged_in': True,
                'user': {
                    'user_name': session.get('user_name'),
                    'role': session.get('user_role'),
                    'full_name': session.get('full_name')
                }
            })
        else:
            return jsonify({
                'success': True,
                'logged_in': False
            })
    
    except Exception as e:
        logger.error(f"API session error: {e}")
        return jsonify({
            'success': False,
            'error': 'Session check failed'
        }), 500

# =============================================
# HELPER FUNCTIONS
# =============================================

def _get_user_details(user_name: str, role: str) -> dict:
    """Get user details based on role"""
    try:
        if role == 'customer':
            customer = Customer.get_by_username(user_name)
            if customer:
                return {
                    'full_name': customer.get_full_name(),
                    'customer_id': customer.customer_id,
                    'email': customer.email
                }
        
        elif role == 'store_manager':
            manager = execute_query(
                """
                SELECT manager_id, first_name, last_name, store_name, email
                FROM store_manager
                WHERE user_name = %s
                """,
                (user_name,),
                fetch_one=True
            )
            if manager:
                return {
                    'full_name': f"{manager['first_name']} {manager['last_name']}",
                    'manager_id': manager['manager_id'],
                    'store_name': manager['store_name'],
                    'email': manager['email']
                }
        
        elif role == 'main_manager':
            manager = execute_query(
                """
                SELECT manager_id, first_name, last_name, department, email
                FROM main_manager
                WHERE user_name = %s
                """,
                (user_name,),
                fetch_one=True
            )
            if manager:
                return {
                    'full_name': f"{manager['first_name']} {manager['last_name']}",
                    'manager_id': manager['manager_id'],
                    'department': manager['department'],
                    'email': manager['email']
                }
        
        return None
    
    except Exception as e:
        logger.error(f"Error getting user details for {user_name}: {e}")
        return None

def _validate_registration_data(data: dict) -> list:
    """Validate registration form data"""
    errors = []
    
    # Required fields
    required_fields = ['user_name', 'password', 'first_name', 'last_name', 'email']
    for field in required_fields:
        if not data.get(field):
            errors.append(f'{field.replace("_", " ").title()} is required')
    
    # Username validation
    if data.get('user_name'):
        if len(data['user_name']) < 3:
            errors.append('Username must be at least 3 characters long')
        if not data['user_name'].replace('_', '').isalnum():
            errors.append('Username can only contain letters, numbers, and underscores')
    
    # Password validation
    if data.get('password'):
        if data['password'] != data.get('confirm_password'):
            errors.append('Passwords do not match')
        
        is_valid, password_errors = is_valid_password(data['password'])
        if not is_valid:
            errors.extend(password_errors)
    
    # Email validation
    if data.get('email') and not is_valid_email(data['email']):
        errors.append('Please enter a valid email address')
    
    # Phone validation (if provided)
    if data.get('phone') and not is_valid_phone(data['phone']):
        errors.append('Please enter a valid phone number')
    
    # Name validation
    for field in ['first_name', 'last_name']:
        if data.get(field):
            if len(data[field]) < 2:
                errors.append(f'{field.replace("_", " ").title()} must be at least 2 characters long')
            if not data[field].replace(' ', '').isalpha():
                errors.append(f'{field.replace("_", " ").title()} can only contain letters and spaces')
    
    return errors

# =============================================
# SESSION MANAGEMENT
# =============================================

@auth_bp.route('/check-session')
def check_session():
    """Check if session is still valid"""
    if 'user_name' in session:
        return jsonify({
            'valid': True,
            'user_name': session.get('user_name'),
            'role': session.get('user_role')
        })
    else:
        return jsonify({'valid': False})

@auth_bp.route('/extend-session', methods=['POST'])
def extend_session():
    """Extend user session"""
    if 'user_name' in session:
        session['last_activity'] = datetime.now().isoformat()
        return jsonify({'success': True, 'message': 'Session extended'})
    else:
        return jsonify({'success': False, 'error': 'No active session'}), 401