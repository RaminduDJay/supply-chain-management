"""
Supply Chain Management System - Customer Routes
Routes for customer-specific functionality including dashboard, products, cart, and orders.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from decimal import Decimal
from datetime import datetime, date, timedelta
import logging

# Import database models and utilities
from database.models import Customer, Item, CartItem, Order
from database.connection import execute_query, execute_update, call_procedure
from utils.decorators import customer_required, rate_limit, audit_log
from utils.helpers import (
    get_current_user, format_currency, format_date, format_weight, format_volume,
    sanitize_input, is_future_date, calculate_delivery_date, paginate_query,
    flash_success, flash_error, flash_warning, flash_info, get_pagination_info
)

# Create blueprint
customer_bp = Blueprint('customer', __name__)
logger = logging.getLogger(__name__)

# =============================================
# DASHBOARD ROUTES
# =============================================

@customer_bp.route('/dashboard')
@customer_required
def dashboard():
    """Customer dashboard"""
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        # Get customer details
        customer = Customer.get_by_id(customer_id)
        if not customer:
            flash_error('Customer account not found')
            return redirect(url_for('auth.logout'))
        
        # Get dashboard statistics
        stats = _get_customer_stats(customer_id)
        
        # Get recent orders
        recent_orders = Order.get_by_customer(customer_id, limit=5)
        
        # Get cart summary
        cart_items = CartItem.get_cart_contents(customer_id)
        cart_summary = _calculate_cart_summary(cart_items)
        
        # Get customer type info
        customer_type_info = execute_query(
            "SELECT * FROM customer_type WHERE customer_type = %s",
            (customer.customer_type,),
            fetch_one=True
        )
        
        return render_template('customer/dashboard.html',
                             customer=customer,
                             stats=stats,
                             recent_orders=recent_orders,
                             cart_summary=cart_summary,
                             customer_type_info=customer_type_info)
    
    except Exception as e:
        logger.error(f"Customer dashboard error: {e}")
        flash_error('Error loading dashboard')
        return redirect(url_for('index'))

# =============================================
# PRODUCT BROWSING ROUTES
# =============================================

@customer_bp.route('/products')
@customer_required
def products():
    """Browse products"""
    try:
        # Get filter parameters
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        sort_by = request.args.get('sort', 'name')
        page = int(request.args.get('page', 1))
        per_page = 12
        
        # Build query
        query = """
        SELECT i.*, 
               COALESCE(MIN(inv.quantity_available), 0) as min_stock,
               COUNT(inv.store_name) as stores_available
        FROM items i
        LEFT JOIN inventory inv ON i.item_id = inv.item_id AND inv.quantity_available > 0
        WHERE i.is_active = TRUE
        """
        
        params = []
        
        # Add filters
        if category:
            query += " AND i.category = %s"
            params.append(category)
        
        if search:
            search_term = f"%{search}%"
            query += " AND (i.item_name LIKE %s OR i.description LIKE %s)"
            params.extend([search_term, search_term])
        
        query += " GROUP BY i.item_id"
        
        # Add sorting
        sort_options = {
            'name': 'i.item_name ASC',
            'price_low': 'i.price ASC',
            'price_high': 'i.price DESC',
            'newest': 'i.created_date DESC'
        }
        
        if sort_by in sort_options:
            query += f" ORDER BY {sort_options[sort_by]}"
        else:
            query += " ORDER BY i.item_name ASC"
        
        # Get all results first for pagination
        all_items = execute_query(query, params)
        
        # Paginate results
        pagination = paginate_query(all_items, page, per_page)
        
        # Get categories for filter dropdown
        categories = execute_query(
            "SELECT DISTINCT category FROM items WHERE is_active = TRUE ORDER BY category"
        )
        
        return render_template('customer/products.html',
                             items=pagination['items'],
                             pagination=pagination,
                             categories=categories,
                             current_category=category,
                             current_search=search,
                             current_sort=sort_by)
    
    except Exception as e:
        logger.error(f"Products page error: {e}")
        flash_error('Error loading products')
        return redirect(url_for('customer.dashboard'))

@customer_bp.route('/product/<int:item_id>')
@customer_required
def product_detail(item_id):
    """Product detail page"""
    try:
        # Get product details
        product = execute_query(
            """
            SELECT i.*, 
                   COUNT(inv.store_name) as stores_available,
                   SUM(inv.quantity_available) as total_stock
            FROM items i
            LEFT JOIN inventory inv ON i.item_id = inv.item_id AND inv.quantity_available > 0
            WHERE i.item_id = %s AND i.is_active = TRUE
            GROUP BY i.item_id
            """,
            (item_id,),
            fetch_one=True
        )
        
        if not product:
            flash_error('Product not found')
            return redirect(url_for('customer.products'))
        
        # Get inventory by store
        inventory_by_store = execute_query(
            """
            SELECT s.store_name, s.city, inv.quantity_available
            FROM inventory inv
            INNER JOIN store s ON inv.store_name = s.store_name
            WHERE inv.item_id = %s AND inv.quantity_available > 0
            ORDER BY s.store_name
            """,
            (item_id,)
        )
        
        # Get related products (same category)
        related_products = execute_query(
            """
            SELECT i.*, COALESCE(MIN(inv.quantity_available), 0) as min_stock
            FROM items i
            LEFT JOIN inventory inv ON i.item_id = inv.item_id AND inv.quantity_available > 0
            WHERE i.category = %s AND i.item_id != %s AND i.is_active = TRUE
            GROUP BY i.item_id
            ORDER BY i.item_name
            LIMIT 4
            """,
            (product['category'], item_id)
        )
        
        return render_template('customer/product_detail.html',
                             product=product,
                             inventory_by_store=inventory_by_store,
                             related_products=related_products)
    
    except Exception as e:
        logger.error(f"Product detail error: {e}")
        flash_error('Error loading product details')
        return redirect(url_for('customer.products'))

# =============================================
# SHOPPING CART ROUTES
# =============================================

@customer_bp.route('/cart')
@customer_required
def cart():
    """Shopping cart page"""
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        # Get cart items
        cart_items = CartItem.get_cart_contents(customer_id)
        
        # Calculate cart summary
        cart_summary = _calculate_cart_summary(cart_items)
        
        # Get available routes for delivery
        routes = execute_query(
            """
            SELECT r.*, s.city as store_city
            FROM route r
            INNER JOIN store s ON r.store_name = s.store_name
            WHERE r.is_active = TRUE
            ORDER BY r.store_name, r.route_name
            """
        )
        
        return render_template('customer/cart.html',
                             cart_items=cart_items,
                             cart_summary=cart_summary,
                             routes=routes)
    
    except Exception as e:
        logger.error(f"Cart page error: {e}")
        flash_error('Error loading cart')
        return redirect(url_for('customer.dashboard'))

@customer_bp.route('/add-to-cart', methods=['POST'])
@customer_required
@rate_limit(max_requests=20, per_seconds=60)
@audit_log(action="ADD_TO_CART", resource="CART")
def add_to_cart():
    """Add item to cart"""
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        item_id = int(request.form.get('item_id', 0))
        quantity = int(request.form.get('quantity', 1))
        
        if item_id <= 0 or quantity <= 0:
            flash_error('Invalid item or quantity')
            return redirect(request.referrer or url_for('customer.products'))
        
        # Check if item exists and is active
        item = execute_query(
            "SELECT item_id, item_name FROM items WHERE item_id = %s AND is_active = TRUE",
            (item_id,),
            fetch_one=True
        )
        
        if not item:
            flash_error('Product not found or unavailable')
            return redirect(request.referrer or url_for('customer.products'))
        
        # Check available inventory
        total_available = execute_query(
            "SELECT SUM(quantity_available) as total FROM inventory WHERE item_id = %s",
            (item_id,),
            fetch_one=True
        )
        
        if not total_available or total_available['total'] < quantity:
            flash_error('Insufficient stock available')
            return redirect(request.referrer or url_for('customer.products'))
        
        # Add to cart
        if CartItem.add_to_cart(customer_id, item_id, quantity):
            flash_success(f'{item["item_name"]} added to cart')
        else:
            flash_error('Failed to add item to cart')
        
        return redirect(request.referrer or url_for('customer.cart'))
    
    except Exception as e:
        logger.error(f"Add to cart error: {e}")
        flash_error('Error adding item to cart')
        return redirect(request.referrer or url_for('customer.products'))

@customer_bp.route('/update-cart', methods=['POST'])
@customer_required
@audit_log(action="UPDATE_CART", resource="CART")
def update_cart():
    """Update cart item quantities"""
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        # Get form data
        updates = {}
        for key, value in request.form.items():
            if key.startswith('quantity_'):
                item_id = int(key.replace('quantity_', ''))
                quantity = int(value) if value.isdigit() and int(value) > 0 else 0
                updates[item_id] = quantity
        
        # Update cart items
        updated_count = 0
        for item_id, quantity in updates.items():
            if quantity == 0:
                # Remove item from cart
                if CartItem.remove_from_cart(customer_id, item_id):
                    updated_count += 1
            else:
                # Update quantity
                result = execute_update(
                    """
                    UPDATE cart 
                    SET quantity = %s, updated_date = NOW() 
                    WHERE customer_id = %s AND item_id = %s
                    """,
                    (quantity, customer_id, item_id)
                )
                if result > 0:
                    updated_count += 1
        
        if updated_count > 0:
            flash_success('Cart updated successfully')
        else:
            flash_warning('No changes made to cart')
        
        return redirect(url_for('customer.cart'))
    
    except Exception as e:
        logger.error(f"Update cart error: {e}")
        flash_error('Error updating cart')
        return redirect(url_for('customer.cart'))

@customer_bp.route('/remove-from-cart/<int:item_id>', methods=['POST'])
@customer_required
@audit_log(action="REMOVE_FROM_CART", resource="CART")
def remove_from_cart(item_id):
    """Remove item from cart"""
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        if CartItem.remove_from_cart(customer_id, item_id):
            flash_success('Item removed from cart')
        else:
            flash_error('Failed to remove item from cart')
        
        return redirect(url_for('customer.cart'))
    
    except Exception as e:
        logger.error(f"Remove from cart error: {e}")
        flash_error('Error removing item from cart')
        return redirect(url_for('customer.cart'))

@customer_bp.route('/clear-cart', methods=['POST'])
@customer_required
@audit_log(action="CLEAR_CART", resource="CART")
def clear_cart():
    """Clear entire cart"""
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        if CartItem.clear_cart(customer_id):
            flash_success('Cart cleared successfully')
        else:
            flash_error('Failed to clear cart')
        
        return redirect(url_for('customer.cart'))
    
    except Exception as e:
        logger.error(f"Clear cart error: {e}")
        flash_error('Error clearing cart')
        return redirect(url_for('customer.cart'))

# =============================================
# ORDER MANAGEMENT ROUTES
# =============================================

@customer_bp.route('/checkout', methods=['GET', 'POST'])
@customer_required
def checkout():
    """Order checkout"""
    if request.method == 'GET':
        return _render_checkout_page()
    
    # Handle POST request
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        # Get form data
        route_id = int(request.form.get('route_id', 0))
        delivery_date = request.form.get('delivery_date', '')
        special_instructions = sanitize_input(request.form.get('special_instructions', ''))
        
        # Validation
        if route_id <= 0:
            flash_error('Please select a delivery route')
            return _render_checkout_page()
        
        if not delivery_date or not is_future_date(delivery_date, days_ahead=7):
            flash_error('Delivery date must be at least 7 days from today')
            return _render_checkout_page()
        
        # Check if cart has items
        cart_items = CartItem.get_cart_contents(customer_id)
        if not cart_items:
            flash_error('Your cart is empty')
            return redirect(url_for('customer.cart'))
        
        # Create order from cart
        order = Order.create_from_cart(
            customer_id=customer_id,
            route_id=route_id,
            delivery_date=datetime.strptime(delivery_date, '%Y-%m-%d').date(),
            special_instructions=special_instructions
        )
        
        if order:
            flash_success(f'Order #{order.order_id} placed successfully!')
            return redirect(url_for('customer.order_detail', order_id=order.order_id))
        else:
            flash_error('Failed to create order. Please try again.')
            return _render_checkout_page()
    
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        flash_error('Error processing order')
        return _render_checkout_page()

@customer_bp.route('/orders')
@customer_required
def orders():
    """Customer orders list"""
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = 10
        status_filter = request.args.get('status', '')
        
        # Build query
        query = """
        SELECT o.*, r.route_name, r.destination_city, s.store_name
        FROM order_table o
        INNER JOIN route r ON o.route_id = r.route_id
        INNER JOIN store s ON r.store_name = s.store_name
        WHERE o.customer_id = %s
        """
        
        params = [customer_id]
        
        if status_filter:
            query += " AND o.status = %s"
            params.append(status_filter)
        
        query += " ORDER BY o.order_date DESC"
        
        # Get all results for pagination
        all_orders = execute_query(query, params)
        
        # Paginate results
        pagination = paginate_query(all_orders, page, per_page)
        
        # Get order statuses for filter
        order_statuses = execute_query(
            """
            SELECT DISTINCT status 
            FROM order_table 
            WHERE customer_id = %s 
            ORDER BY status
            """,
            (customer_id,)
        )
        
        return render_template('customer/orders.html',
                             orders=pagination['items'],
                             pagination=pagination,
                             order_statuses=order_statuses,
                             current_status=status_filter)
    
    except Exception as e:
        logger.error(f"Orders page error: {e}")
        flash_error('Error loading orders')
        return redirect(url_for('customer.dashboard'))

@customer_bp.route('/order/<int:order_id>')
@customer_required
def order_detail(order_id):
    """Order detail page"""
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        # Get order details
        order = execute_query(
            """
            SELECT o.*, r.route_name, r.destination_city, r.destination_address,
                   s.store_name, s.city as store_city, s.address as store_address
            FROM order_table o
            INNER JOIN route r ON o.route_id = r.route_id
            INNER JOIN store s ON r.store_name = s.store_name
            WHERE o.order_id = %s AND o.customer_id = %s
            """,
            (order_id, customer_id),
            fetch_one=True
        )
        
        if not order:
            flash_error('Order not found')
            return redirect(url_for('customer.orders'))
        
        # Get order items
        order_items = execute_query(
            """
            SELECT oi.*, i.item_name, i.category, i.description
            FROM order_items oi
            INNER JOIN items i ON oi.item_id = i.item_id
            WHERE oi.order_id = %s
            ORDER BY oi.order_item_id
            """,
            (order_id,)
        )
        
        # Get tracking information
        tracking_info = _get_order_tracking(order_id)
        
        return render_template('customer/order_detail.html',
                             order=order,
                             order_items=order_items,
                             tracking_info=tracking_info)
    
    except Exception as e:
        logger.error(f"Order detail error: {e}")
        flash_error('Error loading order details')
        return redirect(url_for('customer.orders'))

# =============================================
# PROFILE MANAGEMENT ROUTES
# =============================================

@customer_bp.route('/profile')
@customer_required
def profile():
    """Customer profile page"""
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        # Get customer details
        customer = Customer.get_by_id(customer_id)
        if not customer:
            flash_error('Customer account not found')
            return redirect(url_for('auth.logout'))
        
        # Get customer type information
        customer_type_info = execute_query(
            "SELECT * FROM customer_type WHERE customer_type = %s",
            (customer.customer_type,),
            fetch_one=True
        )
        
        return render_template('customer/profile.html',
                             customer=customer,
                             customer_type_info=customer_type_info)
    
    except Exception as e:
        logger.error(f"Profile page error: {e}")
        flash_error('Error loading profile')
        return redirect(url_for('customer.dashboard'))

@customer_bp.route('/update-profile', methods=['POST'])
@customer_required
@audit_log(action="UPDATE_PROFILE", resource="CUSTOMER")
def update_profile():
    """Update customer profile"""
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        # Get form data
        first_name = sanitize_input(request.form.get('first_name', '').strip())
        last_name = sanitize_input(request.form.get('last_name', '').strip())
        email = sanitize_input(request.form.get('email', '').strip().lower())
        phone = sanitize_input(request.form.get('phone', '').strip())
        address = sanitize_input(request.form.get('address', '').strip())
        city = sanitize_input(request.form.get('city', '').strip())
        postal_code = sanitize_input(request.form.get('postal_code', '').strip())
        
        # Validation
        if not first_name or not last_name or not email:
            flash_error('Name and email are required')
            return redirect(url_for('customer.profile'))
        
        # Update customer profile
        result = execute_update(
            """
            UPDATE customers 
            SET first_name = %s, last_name = %s, email = %s, phone = %s,
                address = %s, city = %s, postal_code = %s
            WHERE customer_id = %s
            """,
            (first_name, last_name, email, phone, address, city, postal_code, customer_id)
        )
        
        if result > 0:
            # Update session full name
            session['full_name'] = f"{first_name} {last_name}"
            flash_success('Profile updated successfully')
        else:
            flash_error('Failed to update profile')
        
        return redirect(url_for('customer.profile'))
    
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        flash_error('Error updating profile')
        return redirect(url_for('customer.profile'))

# =============================================
# HELPER FUNCTIONS
# =============================================

def _get_customer_stats(customer_id: int) -> dict:
    """Get customer dashboard statistics"""
    try:
        # Total orders
        total_orders = execute_query(
            "SELECT COUNT(*) as count FROM order_table WHERE customer_id = %s",
            (customer_id,),
            fetch_one=True
        )
        
        # Total spent
        total_spent = execute_query(
            """
            SELECT COALESCE(SUM(total_amount), 0) as total 
            FROM order_table 
            WHERE customer_id = %s AND status NOT IN ('cancelled', 'returned')
            """,
            (customer_id,),
            fetch_one=True
        )
        
        # Pending orders
        pending_orders = execute_query(
            """
            SELECT COUNT(*) as count 
            FROM order_table 
            WHERE customer_id = %s AND status NOT IN ('delivered', 'cancelled', 'returned')
            """,
            (customer_id,),
            fetch_one=True
        )
        
        # Cart items
        cart_items = execute_query(
            "SELECT COUNT(*) as count FROM cart WHERE customer_id = %s",
            (customer_id,),
            fetch_one=True
        )
        
        return {
            'total_orders': total_orders['count'] if total_orders else 0,
            'total_spent': total_spent['total'] if total_spent else 0,
            'pending_orders': pending_orders['count'] if pending_orders else 0,
            'cart_items': cart_items['count'] if cart_items else 0
        }
    
    except Exception as e:
        logger.error(f"Error getting customer stats: {e}")
        return {
            'total_orders': 0,
            'total_spent': 0,
            'pending_orders': 0,
            'cart_items': 0
        }

def _calculate_cart_summary(cart_items: list) -> dict:
    """Calculate cart summary totals"""
    try:
        if not cart_items:
            return {
                'total_items': 0,
                'total_quantity': 0,
                'subtotal': Decimal('0.00'),
                'total_weight': Decimal('0.00'),
                'total_volume': Decimal('0.00')
            }
        
        total_items = len(cart_items)
        total_quantity = sum(item.quantity for item in cart_items)
        subtotal = sum(item.get_line_total() for item in cart_items)
        total_weight = sum(item.get_total_weight() for item in cart_items)
        total_volume = sum(item.get_total_volume() for item in cart_items)
        
        return {
            'total_items': total_items,
            'total_quantity': total_quantity,
            'subtotal': subtotal,
            'total_weight': total_weight,
            'total_volume': total_volume
        }
    
    except Exception as e:
        logger.error(f"Error calculating cart summary: {e}")
        return {
            'total_items': 0,
            'total_quantity': 0,
            'subtotal': Decimal('0.00'),
            'total_weight': Decimal('0.00'),
            'total_volume': Decimal('0.00')
        }

def _render_checkout_page():
    """Render checkout page with required data"""
    try:
        user = get_current_user()
        customer_id = user['customer_id']
        
        # Get cart items
        cart_items = CartItem.get_cart_contents(customer_id)
        
        if not cart_items:
            flash_warning('Your cart is empty')
            return redirect(url_for('customer.cart'))
        
        # Calculate cart summary
        cart_summary = _calculate_cart_summary(cart_items)
        
        # Get customer details for discount calculation
        customer = Customer.get_by_id(customer_id)
        discount_rate = customer.get_discount_rate() if customer else Decimal('0.00')
        
        # Calculate potential discount
        discount_amount = cart_summary['subtotal'] * (discount_rate / 100)
        
        # Get available routes
        routes = execute_query(
            """
            SELECT r.*, s.city as store_city
            FROM route r
            INNER JOIN store s ON r.store_name = s.store_name
            WHERE r.is_active = TRUE
            ORDER BY r.store_name, r.route_name
            """
        )
        
        # Calculate minimum delivery date
        min_delivery_date = calculate_delivery_date(min_days=7)
        
        return render_template('customer/checkout.html',
                             cart_items=cart_items,
                             cart_summary=cart_summary,
                             discount_rate=discount_rate,
                             discount_amount=discount_amount,
                             routes=routes,
                             min_delivery_date=min_delivery_date)
    
    except Exception as e:
        logger.error(f"Checkout page error: {e}")
        flash_error('Error loading checkout page')
        return redirect(url_for('customer.cart'))

def _get_order_tracking(order_id: int) -> dict:
    """Get order tracking information"""
    try:
        # Get train assignment
        train_info = execute_query(
            """
            SELECT ots.*, ts.departure_date, ts.departure_time, t.train_name
            FROM order_train_schedule ots
            INNER JOIN train_schedule ts ON ots.train_session_id = ts.train_session_id
            INNER JOIN train t ON ts.train_id = t.train_id
            WHERE ots.order_id = %s
            """,
            (order_id,),
            fetch_one=True
        )
        
        # Get truck assignment
        truck_info = execute_query(
            """
            SELECT ots.*, trs.scheduled_date, trs.start_time, 
                   tr.license_plate, d.first_name, d.last_name
            FROM order_truck_schedule ots
            INNER JOIN truck_schedule trs ON ots.truck_session_id = trs.truck_session_id
            INNER JOIN truck tr ON trs.truck_id = tr.truck_id
            INNER JOIN driver d ON trs.driver_id = d.driver_id
            WHERE ots.order_id = %s
            """,
            (order_id,),
            fetch_one=True
        )
        
        return {
            'train_info': train_info,
            'truck_info': truck_info
        }
    
    except Exception as e:
        logger.error(f"Error getting order tracking: {e}")
        return {
            'train_info': None,
            'truck_info': None
        }