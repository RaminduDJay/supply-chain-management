#!/usr/bin/env python3
"""
Supply Chain Management System - Folder Structure Generator
Creates the complete project directory structure with all necessary files and folders.
"""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """Create the complete folder structure for the supply chain management system."""
    
    # Main project directory
    project_name = "supply_chain_management"
    
    # Define the complete directory structure
    directories = [
        # Root level
        project_name,
        
        # Database layer
        f"{project_name}/database",
        f"{project_name}/database/migrations",
        
        # Routes layer
        f"{project_name}/routes",
        
        # Services layer
        f"{project_name}/services",
        
        # Utils layer
        f"{project_name}/utils",
        
        # Static assets
        f"{project_name}/static",
        f"{project_name}/static/css",
        f"{project_name}/static/js",
        f"{project_name}/static/images",
        f"{project_name}/static/images/icons",
        f"{project_name}/static/images/charts",
        f"{project_name}/static/vendor",
        f"{project_name}/static/vendor/bootstrap",
        f"{project_name}/static/vendor/jquery",
        f"{project_name}/static/vendor/chartjs",
        
        # Templates
        f"{project_name}/templates",
        f"{project_name}/templates/auth",
        f"{project_name}/templates/customer",
        f"{project_name}/templates/manager",
        f"{project_name}/templates/reports",
        f"{project_name}/templates/components",
        f"{project_name}/templates/errors",
        
        # Tests
        f"{project_name}/tests",
        
        # Documentation
        f"{project_name}/docs",
        f"{project_name}/docs/screenshots",
        
        # Deployment
        f"{project_name}/deployment",
        f"{project_name}/deployment/docker",
        f"{project_name}/deployment/nginx",
        f"{project_name}/deployment/scripts",
    ]
    
    # Define files to create with their content
    files_content = {
        # Root files
        f"{project_name}/app.py": '''#!/usr/bin/env python3
"""
Supply Chain Management System - Main Flask Application
"""
from flask import Flask, render_template, redirect, url_for
from routes import auth, customer, manager, orders, reports, api
from database.connection import init_db
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Initialize database
init_db()

# Register blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(customer.bp)
app.register_blueprint(manager.bp)
app.register_blueprint(orders.bp)
app.register_blueprint(reports.bp)
app.register_blueprint(api.bp)

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
''',
        
        f"{project_name}/config.py": '''"""
Configuration settings for Supply Chain Management System
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Database configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'supply_chain_db')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    
    # Application settings
    ITEMS_PER_PAGE = 20
    MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB
    
    # Email settings (if needed)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
''',
        
        f"{project_name}/requirements.txt": '''Flask==2.3.3
Flask-Session==0.5.0
PyMySQL==1.1.0
python-dotenv==1.0.0
bcrypt==4.0.1
Werkzeug==2.3.7
Jinja2==3.1.2
requests==2.31.0
pandas==2.1.0
matplotlib==3.7.2
plotly==5.17.0
''',
        
        f"{project_name}/.env": '''# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=supply_chain_db
DB_PORT=3306

# Application Configuration
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
''',
        
        f"{project_name}/.gitignore": '''.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
.DS_Store
*.sqlite3
instance/
uploads/
logs/
''',
        
        f"{project_name}/README.md": '''# Supply Chain Management System

A comprehensive multi-modal supply chain management system built with Flask and MySQL.

## Features

- **Multi-Modal Transportation**: Rail and truck transport coordination
- **Role-Based Access Control**: Customer, Store Manager, and Main Manager roles
- **Real-Time Inventory Management**: Multi-warehouse stock tracking
- **Order Processing Pipeline**: Complete order lifecycle management
- **Advanced Reporting**: Financial, operational, and executive dashboards
- **Capacity Management**: Dynamic resource allocation and optimization

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure database settings in `.env`
4. Run database setup: `python database/schema.sql`
5. Start the application: `python app.py`

## Project Structure

See folder structure documentation for detailed organization.

## Usage

1. Access the application at `http://localhost:5000`
2. Register as a customer or login with manager credentials
3. Navigate through role-specific dashboards
4. Manage orders, inventory, and transportation

## Technology Stack

- **Backend**: Python Flask, SQLAlchemy
- **Database**: MySQL 8.0+
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Visualization**: Chart.js, Plotly
- **Authentication**: Session-based with password hashing
''',
        
        # Database files
        f"{project_name}/database/__init__.py": '',
        
        f"{project_name}/database/connection.py": '''"""
Database connection management for Supply Chain Management System
"""
import pymysql
from config import Config
import sys

class DatabaseConnection:
    """Singleton database connection manager"""
    _instance = None
    _connection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def get_connection(self):
        """Get database connection"""
        if self._connection is None or not self._connection.open:
            try:
                self._connection = pymysql.connect(
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME,
                    port=Config.DB_PORT,
                    charset='utf8mb4',
                    autocommit=False,
                    cursorclass=pymysql.cursors.DictCursor
                )
                print("Database connection established successfully")
            except Exception as e:
                print(f"Database connection failed: {e}")
                sys.exit(1)
        
        return self._connection
    
    def close_connection(self):
        """Close database connection"""
        if self._connection and self._connection.open:
            self._connection.close()
            print("Database connection closed")

def get_db():
    """Get database connection instance"""
    db = DatabaseConnection()
    return db.get_connection()

def init_db():
    """Initialize database connection"""
    print("Initializing database connection...")
    db = DatabaseConnection()
    connection = db.get_connection()
    return connection
''',
        
        f"{project_name}/database/models.py": '''"""
Database models and stored procedure calls
"""
from database.connection import get_db
import pymysql

class BaseModel:
    """Base model class with common database operations"""
    
    @staticmethod
    def execute_query(query, params=None, fetch=False):
        """Execute database query"""
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(query, params)
            if fetch:
                result = cursor.fetchall()
                return result
            else:
                db.commit()
                return cursor.rowcount
        except Exception as e:
            db.rollback()
            raise e
        finally:
            cursor.close()
    
    @staticmethod
    def call_procedure(proc_name, params=None):
        """Call stored procedure"""
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.callproc(proc_name, params)
            result = cursor.fetchall()
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            raise e
        finally:
            cursor.close()

class User(BaseModel):
    """User model for authentication"""
    
    @staticmethod
    def create_user(username, password_hash, role):
        """Create new user"""
        query = "INSERT INTO users (user_name, password, role) VALUES (%s, %s, %s)"
        return User.execute_query(query, (username, password_hash, role))
    
    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        query = "SELECT * FROM users WHERE user_name = %s"
        result = User.execute_query(query, (username,), fetch=True)
        return result[0] if result else None

class Customer(BaseModel):
    """Customer model"""
    
    @staticmethod
    def create_customer(user_name, customer_type, first_name, last_name, contact_info):
        """Create new customer"""
        return Customer.call_procedure('sp_create_customer', 
                                     (user_name, customer_type, first_name, last_name, contact_info))
    
    @staticmethod
    def get_customer_by_username(username):
        """Get customer details by username"""
        query = """
        SELECT c.*, ct.discount_rate, u.user_name 
        FROM customers c 
        JOIN customer_type ct ON c.customer_type = ct.customer_type
        JOIN users u ON c.user_name = u.user_name
        WHERE u.user_name = %s
        """
        result = Customer.execute_query(query, (username,), fetch=True)
        return result[0] if result else None

class Order(BaseModel):
    """Order model"""
    
    @staticmethod
    def create_order(customer_id, route_id, delivery_date):
        """Create new order"""
        return Order.call_procedure('sp_create_order', (customer_id, route_id, delivery_date))
    
    @staticmethod
    def get_customer_orders(customer_id):
        """Get orders for a customer"""
        query = """
        SELECT o.*, r.destination, r.distance 
        FROM order_table o 
        JOIN route r ON o.route_id = r.route_id 
        WHERE o.customer_id = %s 
        ORDER BY o.order_date DESC
        """
        return Order.execute_query(query, (customer_id,), fetch=True)

# Add more models as needed...
''',
        
        f"{project_name}/database/schema.sql": '''-- Your existing database schema goes here
-- This file should contain all your table definitions, 
-- stored procedures, functions, triggers, and views

-- Example placeholder - replace with your actual schema
USE supply_chain_db;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS customer_type;

-- Create tables
CREATE TABLE users (
    user_name VARCHAR(50) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    role ENUM('customer', 'store_manager', 'main_manager') NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer_type (
    customer_type VARCHAR(20) PRIMARY KEY,
    discount_rate DECIMAL(5,2) DEFAULT 0.00,
    min_order_qty INT DEFAULT 1
);

-- Insert sample data
INSERT INTO customer_type VALUES 
('end', 0.00, 1),
('retail', 5.00, 10),
('wholesale', 10.00, 50);

-- Add your complete schema here...
''',
        
        f"{project_name}/database/sample_data.sql": '''-- Sample data for testing
USE supply_chain_db;

-- Insert sample users
INSERT INTO users (user_name, password, role) VALUES 
('admin', '$2b$12$hash_here', 'main_manager'),
('store1_mgr', '$2b$12$hash_here', 'store_manager'),
('customer1', '$2b$12$hash_here', 'customer');

-- Add more sample data as needed...
''',
        
        # Routes
        f"{project_name}/routes/__init__.py": '',
        
        f"{project_name}/routes/auth.py": '''"""
Authentication routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services.auth_service import AuthService
from utils.decorators import require_logout

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
@require_logout
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = AuthService.authenticate_user(username, password)
        if user:
            session['user'] = user
            session['username'] = user['user_name']
            session['role'] = user['role']
            
            # Redirect based on role
            if user['role'] == 'customer':
                return redirect(url_for('customer.dashboard'))
            elif user['role'] == 'store_manager':
                return redirect(url_for('manager.store_dashboard'))
            elif user['role'] == 'main_manager':
                return redirect(url_for('manager.main_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
@require_logout
def register():
    """Customer registration"""
    if request.method == 'POST':
        # Handle registration logic
        pass
    
    return render_template('auth/register.html')

@bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))
''',
        
        # Services
        f"{project_name}/services/__init__.py": '',
        
        f"{project_name}/services/auth_service.py": '''"""
Authentication service
"""
import bcrypt
from database.models import User

class AuthService:
    """Authentication service class"""
    
    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def authenticate_user(username, password):
        """Authenticate user credentials"""
        try:
            user = User.get_user_by_username(username)
            if user and AuthService.verify_password(password, user['password']):
                # Remove password from returned user data
                user.pop('password', None)
                return user
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    @staticmethod
    def create_user(username, password, role):
        """Create new user account"""
        try:
            password_hash = AuthService.hash_password(password)
            return User.create_user(username, password_hash, role)
        except Exception as e:
            print(f"User creation error: {e}")
            return False
''',
        
        # Utils
        f"{project_name}/utils/__init__.py": '',
        
        f"{project_name}/utils/decorators.py": '''"""
Custom decorators for authentication and authorization
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def require_logout(f):
    """Decorator to require logout (for login/register pages)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' in session:
            role = session.get('role')
            if role == 'customer':
                return redirect(url_for('customer.dashboard'))
            elif role == 'store_manager':
                return redirect(url_for('manager.store_dashboard'))
            elif role == 'main_manager':
                return redirect(url_for('manager.main_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                flash('Access denied: insufficient permissions', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def manager_required(f):
    """Decorator to require manager role (store or main)"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        role = session.get('role')
        if role not in ['store_manager', 'main_manager']:
            flash('Access denied: manager access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
''',
        
        # Templates
        f"{project_name}/templates/base.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Supply Chain Management System{% endblock %}</title>
    <link href="{{ url_for('static', filename='vendor/bootstrap/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/main.css') }}" rel="stylesheet">
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% include 'components/navbar.html' %}
    
    <div class="container-fluid">
        <div class="row">
            {% if session.user %}
                {% include 'components/sidebar.html' %}
                <main class="col-md-9 ml-sm-auto col-lg-10 px-md-4">
            {% else %}
                <main class="col-12">
            {% endif %}
                
                {% include 'components/alerts.html' %}
                
                {% block content %}{% endblock %}
                
            </main>
        </div>
    </div>
    
    {% include 'components/footer.html' %}
    
    <script src="{{ url_for('static', filename='vendor/jquery/jquery.min.js') }}"></script>
    <script src="{{ url_for('static', filename='vendor/bootstrap/bootstrap.bundle.min.js') }}"></script>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
''',
        
        f"{project_name}/templates/index.html": '''{% extends "base.html" %}
{% block title %}Home - Supply Chain Management{% endblock %}

{% block content %}
<div class="jumbotron">
    <h1 class="display-4">Supply Chain Management System</h1>
    <p class="lead">Comprehensive multi-modal transportation and logistics management platform.</p>
    {% if not session.user %}
        <hr class="my-4">
        <p>Manage your supply chain operations efficiently with our integrated platform.</p>
        <a class="btn btn-primary btn-lg" href="{{ url_for('auth.login') }}" role="button">Login</a>
        <a class="btn btn-secondary btn-lg" href="{{ url_for('auth.register') }}" role="button">Register</a>
    {% else %}
        <hr class="my-4">
        <p>Welcome back, {{ session.username }}!</p>
        <a class="btn btn-primary btn-lg" href="#" role="button">Go to Dashboard</a>
    {% endif %}
</div>

<div class="row">
    <div class="col-md-4">
        <h3>Multi-Modal Transport</h3>
        <p>Coordinate rail and truck transportation for optimal delivery efficiency.</p>
    </div>
    <div class="col-md-4">
        <h3>Inventory Management</h3>
        <p>Real-time tracking across multiple warehouses with automated capacity management.</p>
    </div>
    <div class="col-md-4">
        <h3>Advanced Reporting</h3>
        <p>Comprehensive analytics and reporting for all stakeholders.</p>
    </div>
</div>
{% endblock %}
''',
        
        # Static files
        f"{project_name}/static/css/main.css": '''/* Main stylesheet for Supply Chain Management System */

:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --success-color: #28a745;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #17a2b8;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f8f9fa;
}

.navbar-brand {
    font-weight: bold;
}

.sidebar {
    position: fixed;
    top: 56px;
    bottom: 0;
    left: 0;
    z-index: 100;
    padding: 48px 0 0;
    box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1);
}

.sidebar-sticky {
    position: relative;
    top: 0;
    height: calc(100vh - 48px);
    padding-top: .5rem;
    overflow-x: hidden;
    overflow-y: auto;
}

.sidebar .nav-link {
    color: #333;
}

.sidebar .nav-link.active {
    color: var(--primary-color);
}

main {
    padding-top: 20px;
}

.card {
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    border: 1px solid rgba(0, 0, 0, 0.125);
}

.btn {
    border-radius: 0.375rem;
}

.table {
    background-color: white;
}

.footer {
    background-color: #f8f9fa;
    padding: 20px 0;
    margin-top: 50px;
    border-top: 1px solid #dee2e6;
}

/* Dashboard specific styles */
.dashboard-card {
    transition: transform 0.2s;
}

.dashboard-card:hover {
    transform: translateY(-2px);
}

.metric-card {
    background: linear-gradient(135deg, var(--primary-color), var(--info-color));
    color: white;
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
}

/* Form styles */
.form-control:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

/* Alert styles */
.alert {
    border-radius: 0.5rem;
}

/* Responsive design */
@media (max-width: 768px) {
    .sidebar {
        position: static;
        height: auto;
    }
    
    main {
        margin-left: 0;
    }
}
''',
        
        f"{project_name}/static/js/main.js": '''// Main JavaScript for Supply Chain Management System

$(document).ready(function() {
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-toggle="popover"]').popover();
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
    
    // Form validation
    $('.needs-validation').on('submit', function(event) {
        if (this.checkValidity() === false) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // AJAX setup
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", $('meta[name=csrf-token]').attr('content'));
            }
        }
    });
});

// Utility functions
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        </div>
    `;
    $('#alerts-container').append(alertHtml);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}
''',
        
        # Component templates
        f"{project_name}/templates/components/navbar.html": '''<nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
    <a class="navbar-brand" href="{{ url_for('index') }}">
        <img src="{{ url_for('static', filename='images/logo.png') }}" width="30" height="30" class="d-inline-block align-top" alt="Logo">
        Supply Chain MS
    </a>
    
    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
    </button>
    
    <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ml-auto">
            {% if session.user %}
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-toggle="dropdown">
                        {{ session.username }} ({{ session.role.replace('_', ' ').title() }})
                    </a>
                    <div class="dropdown-menu">
                        <a class="dropdown-item" href="#">Profile</a>
                        <a class="dropdown-item" href="#">Settings</a>
                        <div class="dropdown-divider"></div>
                        <a class="dropdown-item" href="{{ url_for('auth.logout') }}">Logout</a>
                    </div>
                </li>
            {% else %}
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('auth.login') }}">Login</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{{ url_for('auth.register') }}">Register</a>
                </li>
            {% endif %}
        </ul>
    </div>
</nav>
''',
        
        f"{project_name}/templates/components/alerts.html": '''<div id="alerts-container">
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="close" data-dismiss="alert">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
</div>
''',
        
        # Error templates
        f"{project_name}/templates/errors/404.html": '''{% extends "base.html" %}
{% block title %}Page Not Found{% endblock %}

{% block content %}
<div class="text-center">
    <h1 class="display-1">404</h1>
    <p class="fs-3"><span class="text-danger">Oops!</span> Page not found.</p>
    <p class="lead">The page you're looking for doesn't exist.</p>
    <a href="{{ url_for('index') }}" class="btn btn-primary">Go Home</a>
</div>
{% endblock %}
''',
        
        f"{project_name}/templates/errors/500.html": '''{% extends "base.html" %}
{% block title %}Server Error{% endblock %}

{% block content %}
<div class="text-center">
    <h1 class="display-1">500</h1>
    <p class="fs-3"><span class="text-danger">Oops!</span> Something went wrong.</p>
    <p class="lead">We're experiencing some technical difficulties. Please try again later.</p>
    <a href="{{ url_for('index') }}" class="btn btn-primary">Go Home</a>
</div>
{% endblock %}
''',
        
        f"{project_name}/templates/errors/403.html": '''{% extends "base.html" %}
{% block title %}Access Forbidden{% endblock %}

{% block content %}
<div class="text-center">
    <h1 class="display-1">403</h1>
    <p class="fs-3"><span class="text-danger">Access Denied!</span></p>
    <p class="lead">You don't have permission to access this resource.</p>
    <a href="{{ url_for('index') }}" class="btn btn-primary">Go Home</a>
</div>
{% endblock %}
''',
        
        # Auth templates
        f"{project_name}/templates/auth/login.html": '''{% extends "base.html" %}
{% block title %}Login{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-4">
        <div class="card">
            <div class="card-header">
                <h4 class="text-center">Login</h4>
            </div>
            <div class="card-body">
                <form method="POST" class="needs-validation" novalidate>
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                        <div class="invalid-feedback">Please enter your username.</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                        <div class="invalid-feedback">Please enter your password.</div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary btn-block">Login</button>
                </form>
                
                <hr>
                <div class="text-center">
                    <p>Don't have an account? <a href="{{ url_for('auth.register') }}">Register here</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''',
        
        f"{project_name}/templates/auth/register.html": '''{% extends "base.html" %}
{% block title %}Register{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8 col-lg-6">
        <div class="card">
            <div class="card-header">
                <h4 class="text-center">Customer Registration</h4>
            </div>
            <div class="card-body">
                <form method="POST" class="needs-validation" novalidate>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="username">Username</label>
                                <input type="text" class="form-control" id="username" name="username" required>
                                <div class="invalid-feedback">Please choose a username.</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="customer_type">Customer Type</label>
                                <select class="form-control" id="customer_type" name="customer_type" required>
                                    <option value="">Select Type</option>
                                    <option value="end">End Customer</option>
                                    <option value="retail">Retail</option>
                                    <option value="wholesale">Wholesale</option>
                                </select>
                                <div class="invalid-feedback">Please select customer type.</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="first_name">First Name</label>
                                <input type="text" class="form-control" id="first_name" name="first_name" required>
                                <div class="invalid-feedback">Please enter your first name.</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="last_name">Last Name</label>
                                <input type="text" class="form-control" id="last_name" name="last_name" required>
                                <div class="invalid-feedback">Please enter your last name.</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="contact_info">Contact Information</label>
                        <textarea class="form-control" id="contact_info" name="contact_info" rows="3" required></textarea>
                        <div class="invalid-feedback">Please enter your contact information.</div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="password">Password</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                                <div class="invalid-feedback">Please enter a password.</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="confirm_password">Confirm Password</label>
                                <input type="password" class="form-control" id="confirm_password" name="confirm_password" required>
                                <div class="invalid-feedback">Please confirm your password.</div>
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary btn-block">Register</button>
                </form>
                
                <hr>
                <div class="text-center">
                    <p>Already have an account? <a href="{{ url_for('auth.login') }}">Login here</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''',
        
        # More route files
        f"{project_name}/routes/customer.py": '''"""
Customer routes
"""
from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required

bp = Blueprint('customer', __name__, url_prefix='/customer')

@bp.route('/dashboard')
@role_required('customer')
def dashboard():
    """Customer dashboard"""
    return render_template('customer/dashboard.html')

@bp.route('/products')
@role_required('customer')
def products():
    """Browse products"""
    return render_template('customer/products.html')

@bp.route('/cart')
@role_required('customer')
def cart():
    """Shopping cart"""
    return render_template('customer/cart.html')

@bp.route('/orders')
@role_required('customer')
def orders():
    """Order history"""
    return render_template('customer/orders.html')

@bp.route('/profile')
@role_required('customer')
def profile():
    """Customer profile"""
    return render_template('customer/profile.html')
''',
        
        f"{project_name}/routes/manager.py": '''"""
Manager routes (Store and Main)
"""
from flask import Blueprint, render_template, session
from utils.decorators import login_required, manager_required, role_required

bp = Blueprint('manager', __name__, url_prefix='/manager')

@bp.route('/store-dashboard')
@role_required('store_manager')
def store_dashboard():
    """Store manager dashboard"""
    return render_template('manager/store_dashboard.html')

@bp.route('/main-dashboard')
@role_required('main_manager')
def main_dashboard():
    """Main manager dashboard"""
    return render_template('manager/main_dashboard.html')

@bp.route('/inventory')
@manager_required
def inventory():
    """Inventory management"""
    return render_template('manager/inventory.html')

@bp.route('/transportation')
@manager_required
def transportation():
    """Transportation management"""
    return render_template('manager/transportation.html')

@bp.route('/staff')
@manager_required
def staff_management():
    """Staff management"""
    return render_template('manager/staff_management.html')
''',
        
        f"{project_name}/routes/orders.py": '''"""
Order management routes
"""
from flask import Blueprint, render_template, request, jsonify
from utils.decorators import login_required
from services.order_service import OrderService

bp = Blueprint('orders', __name__, url_prefix='/orders')

@bp.route('/')
@login_required
def list_orders():
    """List orders based on user role"""
    return render_template('manager/orders_management.html')

@bp.route('/create', methods=['POST'])
@login_required
def create_order():
    """Create new order"""
    try:
        # Handle order creation logic
        return jsonify({'success': True, 'message': 'Order created successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/<int:order_id>')
@login_required
def order_details(order_id):
    """Order details"""
    return render_template('customer/order_details.html', order_id=order_id)
''',
        
        f"{project_name}/routes/reports.py": '''"""
Reporting routes
"""
from flask import Blueprint, render_template, request, jsonify
from utils.decorators import login_required, manager_required
from services.report_service import ReportService

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/sales')
@manager_required
def sales_report():
    """Sales report"""
    return render_template('reports/sales_report.html')

@bp.route('/inventory')
@manager_required
def inventory_report():
    """Inventory report"""
    return render_template('reports/inventory_report.html')

@bp.route('/transport')
@manager_required
def transport_report():
    """Transportation report"""
    return render_template('reports/transport_report.html')

@bp.route('/executive')
@manager_required
def executive_summary():
    """Executive summary"""
    return render_template('reports/executive_summary.html')

@bp.route('/api/sales-data')
@manager_required
def sales_data_api():
    """API endpoint for sales data"""
    try:
        # Get sales data from service
        data = ReportService.get_sales_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
''',
        
        f"{project_name}/routes/api.py": '''"""
API routes for AJAX calls
"""
from flask import Blueprint, request, jsonify, session
from utils.decorators import login_required
from services.order_service import OrderService
from services.inventory_service import InventoryService

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    """Get orders for current user"""
    try:
        if session.get('role') == 'customer':
            orders = OrderService.get_customer_orders(session.get('customer_id'))
        else:
            orders = OrderService.get_all_orders()
        return jsonify({'success': True, 'data': orders})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/inventory/check', methods=['POST'])
@login_required
def check_inventory():
    """Check inventory availability"""
    try:
        item_id = request.json.get('item_id')
        quantity = request.json.get('quantity')
        
        available = InventoryService.check_availability(item_id, quantity)
        return jsonify({'success': True, 'available': available})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """Add item to cart"""
    try:
        # Handle add to cart logic
        return jsonify({'success': True, 'message': 'Item added to cart'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
''',
        
        # Additional service files
        f"{project_name}/services/order_service.py": '''"""
Order processing service
"""
from database.models import Order, BaseModel

class OrderService:
    """Order service class"""
    
    @staticmethod
    def create_order(customer_id, route_id, delivery_date, items):
        """Create new order with items"""
        try:
            # Create order
            order_result = Order.create_order(customer_id, route_id, delivery_date)
            order_id = order_result[0]['order_id'] if order_result else None
            
            if order_id:
                # Add items to order
                for item in items:
                    OrderService.add_order_item(order_id, item['item_id'], 
                                              item['quantity'], item['unit_price'])
                
                return {'success': True, 'order_id': order_id}
            else:
                return {'success': False, 'error': 'Failed to create order'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def add_order_item(order_id, item_id, quantity, unit_price):
        """Add item to order"""
        query = "CALL sp_add_order_item(%s, %s, %s, %s)"
        return BaseModel.execute_query(query, (order_id, item_id, quantity, unit_price))
    
    @staticmethod
    def get_customer_orders(customer_id):
        """Get orders for specific customer"""
        return Order.get_customer_orders(customer_id)
    
    @staticmethod
    def get_order_details(order_id):
        """Get detailed order information"""
        query = """
        SELECT o.*, oi.item_id, oi.quantity, oi.unit_price, i.item_name
        FROM order_table o
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN items i ON oi.item_id = i.item_id
        WHERE o.order_id = %s
        """
        return BaseModel.execute_query(query, (order_id,), fetch=True)
    
    @staticmethod
    def update_order_status(order_id, status):
        """Update order status"""
        query = "UPDATE order_table SET status = %s WHERE order_id = %s"
        return BaseModel.execute_query(query, (status, order_id))
''',
        
        f"{project_name}/services/inventory_service.py": '''"""
Inventory management service
"""
from database.models import BaseModel

class InventoryService:
    """Inventory service class"""
    
    @staticmethod
    def check_availability(item_id, quantity, store_name=None):
        """Check if item is available in requested quantity"""
        try:
            if store_name:
                # Check specific store inventory
                result = BaseModel.call_procedure('sp_check_store_inventory', 
                                                (item_id, quantity, store_name))
            else:
                # Check system-wide inventory
                result = BaseModel.call_procedure('sp_check_inventory', 
                                                (item_id, quantity))
            
            return result[0]['available'] if result else False
            
        except Exception as e:
            print(f"Inventory check error: {e}")
            return False
    
    @staticmethod
    def get_inventory_report(store_name=None):
        """Get inventory report"""
        try:
            if store_name:
                query = """
                SELECT i.item_name, i.price, 
                       COALESCE(inv.quantity, 0) as quantity,
                       COALESCE(inv.reserved_quantity, 0) as reserved
                FROM items i
                LEFT JOIN inventory inv ON i.item_id = inv.item_id
                WHERE inv.store_name = %s OR inv.store_name IS NULL
                ORDER BY i.item_name
                """
                return BaseModel.execute_query(query, (store_name,), fetch=True)
            else:
                query = """
                SELECT i.item_name, i.price,
                       SUM(COALESCE(inv.quantity, 0)) as total_quantity,
                       SUM(COALESCE(inv.reserved_quantity, 0)) as total_reserved
                FROM items i
                LEFT JOIN inventory inv ON i.item_id = inv.item_id
                GROUP BY i.item_id, i.item_name, i.price
                ORDER BY i.item_name
                """
                return BaseModel.execute_query(query, fetch=True)
                
        except Exception as e:
            print(f"Inventory report error: {e}")
            return []
    
    @staticmethod
    def update_inventory(item_id, store_name, quantity):
        """Update inventory quantity"""
        try:
            return BaseModel.call_procedure('sp_update_inventory', 
                                          (item_id, store_name, quantity))
        except Exception as e:
            print(f"Inventory update error: {e}")
            return False
''',
        
        f"{project_name}/services/transport_service.py": '''"""
Transportation management service
"""
from database.models import BaseModel

class TransportService:
    """Transportation service class"""
    
    @staticmethod
    def schedule_train_transport(train_id, departure_date, departure_time):
        """Schedule train transport"""
        try:
            return BaseModel.call_procedure('sp_schedule_train', 
                                          (train_id, departure_date, departure_time))
        except Exception as e:
            print(f"Train scheduling error: {e}")
            return False
    
    @staticmethod
    def assign_order_to_train(order_id, train_session_id):
        """Assign order to train schedule"""
        try:
            return BaseModel.call_procedure('sp_assign_order_train', 
                                          (order_id, train_session_id))
        except Exception as e:
            print(f"Order assignment error: {e}")
            return False
    
    @staticmethod
    def schedule_truck_delivery(truck_id, driver_id, route_id, scheduled_date):
        """Schedule truck delivery"""
        try:
            return BaseModel.call_procedure('sp_schedule_truck', 
                                          (truck_id, driver_id, route_id, scheduled_date))
        except Exception as e:
            print(f"Truck scheduling error: {e}")
            return False
    
    @staticmethod
    def get_available_trains(departure_date):
        """Get available trains for specific date"""
        query = """
        SELECT t.train_id, t.train_name, t.capacity, ts.available_capacity
        FROM train t
        JOIN train_schedule ts ON t.train_id = ts.train_id
        WHERE ts.departure_date = %s AND ts.status = 'scheduled'
        AND ts.available_capacity > 0
        """
        return BaseModel.execute_query(query, (departure_date,), fetch=True)
    
    @staticmethod
    def get_available_trucks(store_name, scheduled_date):
        """Get available trucks for specific store and date"""
        query = """
        SELECT tr.truck_id, tr.license_plate, tr.capacity
        FROM truck tr
        WHERE tr.store_name = %s AND tr.status = 'active'
        AND tr.truck_id NOT IN (
            SELECT truck_id FROM truck_schedule 
            WHERE scheduled_date = %s
        )
        """
        return BaseModel.execute_query(query, (store_name, scheduled_date), fetch=True)
''',
        
        f"{project_name}/services/report_service.py": '''"""
Report generation service
"""
from database.models import BaseModel
import json
from datetime import datetime, timedelta

class ReportService:
    """Report service class"""
    
    @staticmethod
    def get_sales_report(start_date=None, end_date=None, store_name=None):
        """Generate sales report"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
                
            query = """
            SELECT DATE(o.order_date) as order_date,
                   COUNT(o.order_id) as total_orders,
                   SUM(o.total_amount) as total_revenue,
                   AVG(o.total_amount) as avg_order_value
            FROM order_table o
            WHERE o.order_date BETWEEN %s AND %s
            """
            params = [start_date, end_date]
            
            if store_name:
                query += " AND o.route_id IN (SELECT route_id FROM route WHERE store_name = %s)"
                params.append(store_name)
                
            query += " GROUP BY DATE(o.order_date) ORDER BY order_date"
            
            return BaseModel.execute_query(query, params, fetch=True)
            
        except Exception as e:
            print(f"Sales report error: {e}")
            return []
    
    @staticmethod
    def get_customer_analysis():
        """Get customer analysis report"""
        try:
            query = """
            SELECT ct.customer_type,
                   COUNT(c.customer_id) as customer_count,
                   COUNT(o.order_id) as total_orders,
                   SUM(o.total_amount) as total_revenue,
                   AVG(o.total_amount) as avg_order_value
            FROM customer_type ct
            LEFT JOIN customers c ON ct.customer_type = c.customer_type
            LEFT JOIN order_table o ON c.customer_id = o.customer_id
            GROUP BY ct.customer_type
            ORDER BY total_revenue DESC
            """
            return BaseModel.execute_query(query, fetch=True)
            
        except Exception as e:
            print(f"Customer analysis error: {e}")
            return []
    
    @staticmethod
    def get_transportation_metrics():
        """Get transportation performance metrics"""
        try:
            # Train metrics
            train_query = """
            SELECT 'Train Transport' as transport_type,
                   COUNT(ts.train_session_id) as total_sessions,
                   AVG(ts.available_capacity / t.capacity * 100) as avg_utilization,
                   COUNT(CASE WHEN ts.status = 'completed' THEN 1 END) as completed_sessions
            FROM train_schedule ts
            JOIN train t ON ts.train_id = t.train_id
            WHERE ts.departure_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            
            # Truck metrics
            truck_query = """
            SELECT 'Truck Delivery' as transport_type,
                   COUNT(ts.truck_session_id) as total_sessions,
                   AVG(tr.capacity) as avg_capacity,
                   COUNT(CASE WHEN ts.status = 'completed' THEN 1 END) as completed_sessions
            FROM truck_schedule ts
            JOIN truck tr ON ts.truck_id = tr.truck_id
            WHERE ts.scheduled_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            
            train_data = BaseModel.execute_query(train_query, fetch=True)
            truck_data = BaseModel.execute_query(truck_query, fetch=True)
            
            return {'train': train_data, 'truck': truck_data}
            
        except Exception as e:
            print(f"Transportation metrics error: {e}")
            return {'train': [], 'truck': []}
    
    @staticmethod
    def get_executive_summary():
        """Get executive summary dashboard data"""
        try:
            # Key metrics
            metrics_query = """
            SELECT 
                (SELECT COUNT(*) FROM order_table WHERE order_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)) as monthly_orders,
                (SELECT SUM(total_amount) FROM order_table WHERE order_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)) as monthly_revenue,
                (SELECT COUNT(*) FROM customers) as total_customers,
                (SELECT COUNT(*) FROM items) as total_products
            """
            
            metrics = BaseModel.execute_query(metrics_query, fetch=True)
            
            # Recent orders trend
            trend_query = """
            SELECT DATE(order_date) as date, COUNT(*) as orders, SUM(total_amount) as revenue
            FROM order_table 
            WHERE order_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(order_date)
            ORDER BY date
            """
            
            trends = BaseModel.execute_query(trend_query, fetch=True)
            
            return {
                'metrics': metrics[0] if metrics else {},
                'trends': trends
            }
            
        except Exception as e:
            print(f"Executive summary error: {e}")
            return {'metrics': {}, 'trends': []}
''',
        
        # Test files
        f"{project_name}/tests/__init__.py": '',
        
        f"{project_name}/tests/test_auth.py": '''"""
Authentication tests
"""
import unittest
from services.auth_service import AuthService

class TestAuthService(unittest.TestCase):
    """Test authentication service"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password"
        hashed = AuthService.hash_password(password)
        
        # Test correct password
        self.assertTrue(AuthService.verify_password(password, hashed))
        
        # Test incorrect password
        self.assertFalse(AuthService.verify_password("wrong_password", hashed))
    
    def test_user_creation(self):
        """Test user creation"""
        # This would require database setup
        pass

if __name__ == '__main__':
    unittest.main()
''',
        
        # Documentation files
        f"{project_name}/docs/installation.md": '''# Installation Guide

## Prerequisites
- Python 3.8+
- MySQL 8.0+
- Git

## Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd supply_chain_management
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   - Create MySQL database: `supply_chain_db`
   - Update `.env` file with your database credentials
   - Run database schema: `mysql -u root -p supply_chain_db < database/schema.sql`

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open browser to `http://localhost:5000`

## Troubleshooting

### Database Connection Issues
- Verify MySQL is running
- Check credentials in `.env` file
- Ensure database exists

### Permission Errors
- Check file permissions
- Verify virtual environment activation

### Module Import Errors
- Ensure all dependencies are installed
- Check Python path configuration
''',
        
        # Deployment files
        f"{project_name}/deployment/docker/Dockerfile": '''FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    default-libmysqlclient-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
''',
        
        f"{project_name}/deployment/docker/docker-compose.yml": '''version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DB_HOST=db
      - DB_USER=root
      - DB_PASSWORD=rootpassword
      - DB_NAME=supply_chain_db
    depends_on:
      - db
    volumes:
      - .:/app

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=supply_chain_db
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql

volumes:
  mysql_data:
''',
        
        f"{project_name}/deployment/scripts/deploy.sh": '''#!/bin/bash

# Deployment script for Supply Chain Management System

echo "Starting deployment..."

# Pull latest code
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run database migrations if needed
# python manage.py migrate

# Restart application (adjust for your server setup)
sudo systemctl restart supply_chain_app

echo "Deployment completed successfully!"
''',
    }
    
    print("Creating Supply Chain Management System folder structure...")
    print("=" * 60)
    print("\n🎉 PROJECT STRUCTURE CREATED SUCCESSFULLY!")
    print(f"\nProject created in: {os.path.abspath(project_name)}")
    
    print("\n📋 NEXT STEPS:")
    print("1. Navigate to project directory:")
    print(f"   cd {project_name}")
    
    print("\n2. Create virtual environment:")
    print("   python -m venv venv")
    print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    
    print("\n3. Install dependencies:")
    print("   pip install -r requirements.txt")
    
    print("\n4. Configure database:")
    print("   - Create MySQL database: 'supply_chain_db'")
    print("   - Update .env file with your database credentials")
    print("   - Run: mysql -u root -p supply_chain_db < database/schema.sql")
    
    print("\n5. Run the application:")
    print("   python app.py")
    
    print("\n6. Access your application:")
    print("   http://localhost:5000")
    
    print("\n📁 KEY DIRECTORIES CREATED:")
    print("├── database/          # Database models, schema, connections")
    print("├── routes/            # Flask route handlers")
    print("├── services/          # Business logic layer")
    print("├── templates/         # HTML templates")
    print("├── static/            # CSS, JS, images")
    print("├── utils/             # Helper functions and decorators")
    print("├── tests/             # Unit tests")
    print("├── docs/              # Documentation")
    print("└── deployment/        # Docker and deployment scripts")
    
    print("\n🔑 IMPORTANT FILES:")
    print("- app.py              # Main Flask application")
    print("- config.py           # Configuration settings")
    print("- requirements.txt    # Python dependencies")
    print("- .env               # Environment variables (update with your settings)")
    print("- database/schema.sql # Your database schema goes here")
    
    print("\n⚠️  REMEMBER TO:")
    print("- Update .env with your actual database credentials")
    print("- Replace database/schema.sql with your actual database schema")
    print("- Customize the templates and styling as needed")
    print("- Add your specific business logic to services")
    print("- Configure proper security measures for production")
    
    return True

def show_project_structure():
    """Display the project structure tree"""
    project_name = "supply_chain_management"
    
    structure = f"""
{project_name}/
│
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings  
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
├── .env                           # Environment variables
├── .gitignore                     # Git ignore file
│
├── database/
│   ├── __init__.py
│   ├── connection.py              # Database connection management
│   ├── models.py                  # Database models/classes
│   ├── schema.sql                 # Database schema
│   ├── sample_data.sql            # Sample data insertion
│   └── migrations/
│       └── initial_setup.sql
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                    # Authentication routes
│   ├── customer.py                # Customer-related routes
│   ├── manager.py                 # Manager routes
│   ├── orders.py                  # Order management routes
│   ├── reports.py                 # Reporting routes
│   └── api.py                     # API endpoints
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py            # Authentication logic
│   ├── order_service.py           # Order processing logic
│   ├── inventory_service.py       # Inventory management
│   ├── transport_service.py       # Transportation logic
│   └── report_service.py          # Report generation
│
├── utils/
│   ├── __init__.py
│   ├── decorators.py              # Custom decorators
│   ├── validators.py              # Input validation
│   ├── helpers.py                 # Utility functions
│   └── constants.py               # Application constants
│
├── static/
│   ├── css/
│   │   ├── main.css              # Main stylesheet
│   │   ├── dashboard.css         # Dashboard styles
│   │   ├── forms.css             # Form styles
│   │   └── reports.css           # Report styles
│   │
│   ├── js/
│   │   ├── main.js               # Main JavaScript
│   │   ├── dashboard.js          # Dashboard functionality
│   │   ├── charts.js             # Chart implementations
│   │   ├── forms.js              # Form validation
│   │   └── api.js                # AJAX API calls
│   │
│   ├── images/
│   │   ├── logo.png
│   │   ├── icons/
│   │   └── charts/
│   │
│   └── vendor/
│       ├── bootstrap/            # Bootstrap CSS/JS
│       ├── jquery/               # jQuery
│       └── chartjs/              # Chart.js
│
├── templates/
│   ├── base.html                 # Base template
│   ├── index.html                # Home page
│   │
│   ├── auth/
│   │   ├── login.html
│   │   ├── register.html
│   │   └── forgot_password.html
│   │
│   ├── customer/
│   │   ├── dashboard.html
│   │   ├── profile.html
│   │   ├── products.html
│   │   ├── cart.html
│   │   ├── orders.html
│   │   └── order_details.html
│   │
│   ├── manager/
│   │   ├── main_dashboard.html
│   │   ├── store_dashboard.html
│   │   ├── orders_management.html
│   │   ├── inventory.html
│   │   ├── transportation.html
│   │   ├── staff_management.html
│   │   └── settings.html
│   │
│   ├── reports/
│   │   ├── sales_report.html
│   │   ├── inventory_report.html
│   │   ├── transport_report.html
│   │   ├── customer_report.html
│   │   └── executive_summary.html
│   │
│   ├── components/
│   │   ├── navbar.html
│   │   ├── sidebar.html
│   │   ├── footer.html
│   │   ├── alerts.html
│   │   └── modals.html
│   │
│   └── errors/
│       ├── 404.html
│       ├── 500.html
│       └── 403.html
│
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_orders.py
│   ├── test_database.py
│   └── test_api.py
│
├── docs/
│   ├── installation.md
│   ├── api_documentation.md
│   ├── database_schema.md
│   ├── user_guide.md
│   └── screenshots/
│
└── deployment/
    ├── docker/
    │   ├── Dockerfile
    │   └── docker-compose.yml
    ├── nginx/
    │   └── nginx.conf
    └── scripts/
        ├── deploy.sh
        └── backup.sh
    """
    
    print("📁 PROJECT STRUCTURE:")
    print(structure)

def main():
    """Main function to run the folder structure generator"""
    print("🚀 Supply Chain Management System - Folder Structure Generator")
    print("=" * 70)
    
    try:
        # Show what will be created
        show_project_structure()
        
        # Ask for confirmation
        response = input("\n❓ Do you want to create this folder structure? (y/N): ").lower().strip()
        
        if response in ['y', 'yes']:
            success = create_directory_structure()
            if success:
                print("\n✅ All done! Your Supply Chain Management System is ready for development.")
            else:
                print("\n❌ Some errors occurred during creation. Please check the output above.")
        else:
            print("\n🛑 Operation cancelled by user.")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Operation cancelled by user (Ctrl+C).")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()