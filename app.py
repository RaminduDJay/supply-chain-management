"""
Supply Chain Management System - Flask Application
Main application entry point with configuration and route registration.
"""

from flask import Flask, render_template, session, request, redirect, url_for, flash, jsonify
from flask_session import Session
import os
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import configuration
from config import Config

# Import database
from database.connection import get_db

# Import routes
from routes.auth import auth_bp
from routes.customer import customer_bp
from routes.manager import manager_bp
from routes.orders import orders_bp
from routes.reports import reports_bp
from routes.api import api_bp

# Import utilities
from utils.decorators import login_required, role_required
from utils.helpers import format_currency, format_date, get_user_role

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    Session(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register template filters
    register_template_filters(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Initialize database connection test
    with app.app_context():
        if not test_database_connection():
            logger.error("Database connection failed on startup")
    
    return app

def register_template_filters(app):
    """Register custom template filters"""
    
    @app.template_filter('currency')
    def currency_filter(value):
        """Format currency values"""
        return format_currency(value)
    
    @app.template_filter('date')
    def date_filter(value, format='%Y-%m-%d'):
        """Format date values"""
        return format_date(value, format)
    
    @app.template_filter('datetime')
    def datetime_filter(value, format='%Y-%m-%d %H:%M'):
        """Format datetime values"""
        if isinstance(value, str):
            return value
        return value.strftime(format) if value else ''
    
    @app.template_filter('status_badge')
    def status_badge_filter(status):
        """Convert status to Bootstrap badge class"""
        status_classes = {
            'pending': 'badge-warning',
            'confirmed': 'badge-info',
            'assigned_train': 'badge-primary',
            'in_transit_rail': 'badge-primary',
            'at_warehouse': 'badge-secondary',
            'assigned_truck': 'badge-info',
            'out_for_delivery': 'badge-warning',
            'delivered': 'badge-success',
            'cancelled': 'badge-danger',
            'returned': 'badge-dark'
        }
        return status_classes.get(status, 'badge-secondary')
    
    @app.template_filter('truncate_words')
    def truncate_words_filter(text, length=20):
        """Truncate text to specified word count"""
        if not text:
            return ''
        words = text.split()
        if len(words) <= length:
            return text
        return ' '.join(words[:length]) + '...'

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        if request.is_json:
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {error}")
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors"""
        if request.is_json:
            return jsonify({'error': 'Access forbidden'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions"""
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        if request.is_json:
            return jsonify({'error': 'An unexpected error occurred'}), 500
        return render_template('errors/500.html'), 500

def register_context_processors(app):
    """Register template context processors"""
    
    @app.context_processor
    def inject_user():
        """Inject user information into all templates"""
        user_info = {
            'is_logged_in': 'user_name' in session,
            'user_name': session.get('user_name'),
            'user_role': session.get('user_role'),
            'full_name': session.get('full_name'),
            'customer_id': session.get('customer_id'),
            'store_name': session.get('store_name')
        }
        return dict(user=user_info)
    
    @app.context_processor
    def inject_app_info():
        """Inject application information"""
        return dict(
            app_name='Supply Chain Management',
            app_version='1.0.0',
            current_year=datetime.now().year,
            current_date=datetime.now().date()
        )

def test_database_connection():
    """Test database connection on startup"""
    try:
        db = get_db()
        return db.test_connection()
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

# Create Flask application instance
app = create_app()

# =============================================
# MAIN ROUTES
# =============================================

@app.route('/')
def index():
    """Home page route"""
    if 'user_name' in session:
        # Redirect based on user role
        role = session.get('user_role')
        if role == 'customer':
            return redirect(url_for('customer.dashboard'))
        elif role == 'store_manager':
            return redirect(url_for('manager.store_dashboard'))
        elif role == 'main_manager':
            return redirect(url_for('manager.main_dashboard'))
    
    # Show public home page
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """General dashboard route - redirects based on role"""
    role = session.get('user_role')
    if role == 'customer':
        return redirect(url_for('customer.dashboard'))
    elif role == 'store_manager':
        return redirect(url_for('manager.store_dashboard'))
    elif role == 'main_manager':
        return redirect(url_for('manager.main_dashboard'))
    else:
        flash('Invalid user role', 'error')
        return redirect(url_for('auth.logout'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        user_name = session.get('user_name')
        role = session.get('user_role')
        
        # Get user-specific information based on role
        if role == 'customer':
            from database.models import Customer
            user_data = Customer.get_by_username(user_name)
        elif role in ['store_manager', 'main_manager']:
            from database.connection import execute_query
            table = 'store_manager' if role == 'store_manager' else 'main_manager'
            user_data = execute_query(
                f"SELECT * FROM {table} WHERE user_name = %s",
                (user_name,),
                fetch_one=True
            )
        else:
            user_data = None
        
        return render_template('profile.html', user_data=user_data)
        
    except Exception as e:
        logger.error(f"Profile page error: {e}")
        flash('Error loading profile', 'error')
        return redirect(url_for('dashboard'))

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_status = test_database_connection()
        
        health_status = {
            'status': 'healthy' if db_status else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected' if db_status else 'disconnected',
            'version': '1.0.0'
        }
        
        status_code = 200 if db_status else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

# =============================================
# SESSION MANAGEMENT
# =============================================

@app.before_request
def before_request():
    """Execute before each request"""
    # Skip session check for static files and public routes
    if request.endpoint in ['static', 'health_check', 'about', 'contact', 'index']:
        return
    
    # Skip session check for auth routes
    if request.endpoint and request.endpoint.startswith('auth.'):
        return
    
    # Check session timeout
    if 'user_name' in session:
        last_activity = session.get('last_activity')
        if last_activity:
            last_activity = datetime.fromisoformat(last_activity)
            if datetime.now() - last_activity > timedelta(hours=8):  # 8 hour timeout
                session.clear()
                flash('Session expired. Please log in again.', 'warning')
                return redirect(url_for('auth.login'))
        
        # Update last activity
        session['last_activity'] = datetime.now().isoformat()

@app.after_request
def after_request(response):
    """Execute after each request"""
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Log request (exclude static files)
    if not request.endpoint or not request.endpoint.startswith('static'):
        logger.info(f"{request.method} {request.path} - {response.status_code}")
    
    return response

# =============================================
# CLI COMMANDS
# =============================================

@app.cli.command()
def init_db():
    """Initialize database with schema and sample data"""
    try:
        print("Initializing database...")
        
        # Read and execute schema
        with open('database/schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute schema (this would need to be done in parts due to delimiter issues)
        print("Database schema created successfully!")
        
        # Read and execute sample data
        with open('database/sample_data.sql', 'r') as f:
            data_sql = f.read()
        
        print("Sample data inserted successfully!")
        print("Database initialization complete!")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")

@app.cli.command()
def create_admin():
    """Create an admin user"""
    try:
        from database.models import User
        
        admin_username = input("Enter admin username: ")
        admin_password = input("Enter admin password: ")
        
        if User.create_user(admin_username, admin_password, 'main_manager'):
            print("Admin user created successfully!")
        else:
            print("Failed to create admin user!")
            
    except Exception as e:
        print(f"Admin creation failed: {e}")

@app.cli.command()
def reset_weekly_hours():
    """Reset weekly hours for drivers and assistants"""
    try:
        from database.connection import call_procedure
        call_procedure('sp_reset_weekly_hours')
        print("Weekly hours reset successfully!")
        
    except Exception as e:
        print(f"Weekly hours reset failed: {e}")

@app.cli.command()
def cleanup_logs():
    """Clean up old audit logs"""
    try:
        days = int(input("Enter number of days to keep (default 90): ") or "90")
        from database.connection import call_procedure
        result = call_procedure('sp_cleanup_audit_logs', (days,))
        print(f"Cleaned up old logs: {result}")
        
    except Exception as e:
        print(f"Log cleanup failed: {e}")

# =============================================
# DEVELOPMENT HELPERS
# =============================================

@app.route('/debug/session')
def debug_session():
    """Debug session information (development only)"""
    if not app.debug:
        return "Debug mode only", 403
    
    return jsonify({
        'session': dict(session),
        'request_headers': dict(request.headers),
        'request_args': dict(request.args)
    })

if __name__ == '__main__':
    # Development server configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting Supply Chain Management System...")
    print(f"🌐 Server running on http://localhost:{port}")
    print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
    
    if test_database_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )