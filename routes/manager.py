"""
Supply Chain Management System - Manager Routes
Routes for store manager and main manager functionality including dashboards,
inventory management, transportation scheduling, and staff management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from decimal import Decimal
from datetime import datetime, date, timedelta
import logging

# Import database models and utilities
from database.models import Order, Train, TrainSchedule, Truck, Driver, ReportGenerator
from database.connection import execute_query, execute_update, call_procedure, call_function
from utils.decorators import manager_required, store_manager_required, main_manager_required, audit_log, rate_limit
from utils.helpers import (
    get_current_user, get_user_store, is_store_manager, is_main_manager,
    format_currency, format_date, format_percentage, paginate_query,
    flash_success, flash_error, flash_warning, flash_info, sanitize_input
)

# Create blueprint
manager_bp = Blueprint('manager', __name__)
logger = logging.getLogger(__name__)

# =============================================
# DASHBOARD ROUTES
# =============================================

@manager_bp.route('/store-dashboard')
@store_manager_required
def store_dashboard():
    """Store manager dashboard"""
    try:
        user = get_current_user()
        store_name = user['store_name']
        
        if not store_name:
            flash_error('Store information not found')
            return redirect(url_for('auth.logout'))
        
        # Get store statistics
        stats = _get_store_stats(store_name)
        
        # Get pending orders for this store
        pending_orders = execute_query(
            """
            SELECT o.*, c.first_name, c.last_name, r.route_name
            FROM order_table o
            INNER JOIN customers c ON o.customer_id = c.customer_id
            INNER JOIN route r ON o.route_id = r.route_id
            WHERE r.store_name = %s AND o.status IN ('confirmed', 'at_warehouse')
            ORDER BY o.order_date ASC
            LIMIT 10
            """,
            (store_name,)
        )
        
        # Get today's truck schedules
        todays_trucks = execute_query(
            """
            SELECT ts.*, t.license_plate, d.first_name, d.last_name, r.route_name
            FROM truck_schedule ts
            INNER JOIN truck t ON ts.truck_id = t.truck_id
            INNER JOIN driver d ON ts.driver_id = d.driver_id
            INNER JOIN route r ON ts.route_id = r.route_id
            WHERE t.store_name = %s AND ts.scheduled_date = CURDATE()
            ORDER BY ts.start_time
            """,
            (store_name,)
        )
        
        # Get low stock items
        low_stock_items = execute_query(
            """
            SELECT i.item_name, inv.quantity_available, inv.reorder_point
            FROM inventory inv
            INNER JOIN items i ON inv.item_id = i.item_id
            WHERE inv.store_name = %s 
            AND inv.quantity_available <= inv.reorder_point
            ORDER BY (inv.quantity_available / inv.reorder_point) ASC
            LIMIT 10
            """,
            (store_name,)
        )
        
        return render_template('manager/store_dashboard.html',
                             store_name=store_name,
                             stats=stats,
                             pending_orders=pending_orders,
                             todays_trucks=todays_trucks,
                             low_stock_items=low_stock_items)
    
    except Exception as e:
        logger.error(f"Store dashboard error: {e}")
        flash_error('Error loading dashboard')
        return redirect(url_for('index'))

@manager_bp.route('/main-dashboard')
@main_manager_required
def main_dashboard():
    """Main manager dashboard"""
    try:
        # Get system-wide statistics
        stats = _get_system_stats()
        
        # Get recent orders across all stores
        recent_orders = execute_query(
            """
            SELECT o.*, c.first_name, c.last_name, r.route_name, s.store_name
            FROM order_table o
            INNER JOIN customers c ON o.customer_id = c.customer_id
            INNER JOIN route r ON o.route_id = r.route_id
            INNER JOIN store s ON r.store_name = s.store_name
            ORDER BY o.order_date DESC
            LIMIT 15
            """
        )
        
        # Get today's train schedules
        todays_trains = execute_query(
            """
            SELECT ts.*, t.train_name, t.train_type
            FROM train_schedule ts
            INNER JOIN train t ON ts.train_id = t.train_id
            WHERE ts.departure_date = CURDATE()
            ORDER BY ts.departure_time
            """
        )
        
        # Get store performance summary
        store_performance = execute_query(
            """
            SELECT 
                s.store_name,
                COUNT(DISTINCT o.order_id) as orders_today,
                COALESCE(SUM(o.total_amount), 0) as revenue_today,
                COUNT(DISTINCT ts.truck_session_id) as deliveries_scheduled
            FROM store s
            LEFT JOIN route r ON s.store_name = r.store_name
            LEFT JOIN order_table o ON r.route_id = o.route_id AND DATE(o.order_date) = CURDATE()
            LEFT JOIN truck_schedule ts ON ts.scheduled_date = CURDATE()
            LEFT JOIN truck t ON ts.truck_id = t.truck_id AND t.store_name = s.store_name
            GROUP BY s.store_name
            ORDER BY s.store_name
            """
        )
        
        return render_template('manager/main_dashboard.html',
                             stats=stats,
                             recent_orders=recent_orders,
                             todays_trains=todays_trains,
                             store_performance=store_performance)
    
    except Exception as e:
        logger.error(f"Main dashboard error: {e}")
        flash_error('Error loading dashboard')
        return redirect(url_for('index'))

# =============================================
# INVENTORY MANAGEMENT
# =============================================

@manager_bp.route('/inventory')
@manager_required
def inventory():
    """Inventory management page"""
    try:
        user = get_current_user()
        
        # Determine store filter based on user role
        if is_store_manager():
            store_filter = user['store_name']
        else:
            store_filter = request.args.get('store', '')
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = 20
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        stock_status = request.args.get('status', '')
        
        # Build inventory query
        query = """
        SELECT 
            inv.*, i.item_name, i.category, i.price,
            CASE 
                WHEN inv.quantity_available = 0 THEN 'out_of_stock'
                WHEN inv.quantity_available <= inv.reorder_point THEN 'low_stock'
                WHEN inv.quantity_available > inv.reorder_point * 3 THEN 'overstocked'
                ELSE 'normal'
            END as stock_status,
            (inv.quantity_available * inv.cost_per_unit) as inventory_value
        FROM inventory inv
        INNER JOIN items i ON inv.item_id = i.item_id
        WHERE i.is_active = TRUE
        """
        
        params = []
        
        # Add filters
        if store_filter:
            query += " AND inv.store_name = %s"
            params.append(store_filter)
        
        if search:
            search_term = f"%{search}%"
            query += " AND i.item_name LIKE %s"
            params.append(search_term)
        
        if category:
            query += " AND i.category = %s"
            params.append(category)
        
        if stock_status:
            if stock_status == 'low_stock':
                query += " AND inv.quantity_available <= inv.reorder_point"
            elif stock_status == 'out_of_stock':
                query += " AND inv.quantity_available = 0"
            elif stock_status == 'overstocked':
                query += " AND inv.quantity_available > inv.reorder_point * 3"
        
        query += " ORDER BY i.item_name"
        
        # Get results and paginate
        all_inventory = execute_query(query, params)
        pagination = paginate_query(all_inventory, page, per_page)
        
        # Get filter options
        if is_main_manager():
            stores = execute_query("SELECT store_name FROM store ORDER BY store_name")
        else:
            stores = []
        
        categories = execute_query(
            "SELECT DISTINCT category FROM items WHERE is_active = TRUE ORDER BY category"
        )
        
        return render_template('manager/inventory.html',
                             inventory=pagination['items'],
                             pagination=pagination,
                             stores=stores,
                             categories=categories,
                             current_store=store_filter,
                             current_search=search,
                             current_category=category,
                             current_status=stock_status)
    
    except Exception as e:
        logger.error(f"Inventory page error: {e}")
        flash_error('Error loading inventory')
        return redirect(url_for('manager.store_dashboard' if is_store_manager() else 'manager.main_dashboard'))

@manager_bp.route('/update-inventory', methods=['POST'])
@manager_required
@audit_log(action="UPDATE_INVENTORY", resource="INVENTORY")
def update_inventory():
    """Update inventory quantities"""
    try:
        store_name = sanitize_input(request.form.get('store_name', ''))
        item_id = int(request.form.get('item_id', 0))
        operation = request.form.get('operation', 'ADD')  # ADD, SUBTRACT, SET
        quantity = int(request.form.get('quantity', 0))
        
        # Validation
        if not store_name or item_id <= 0 or quantity < 0:
            flash_error('Invalid inventory update parameters')
            return redirect(request.referrer or url_for('manager.inventory'))
        
        # Check permissions
        user = get_current_user()
        if is_store_manager() and user['store_name'] != store_name:
            flash_error('You can only update inventory for your store')
            return redirect(url_for('manager.inventory'))
        
        if operation == 'SET':
            # Set absolute quantity
            result = execute_update(
                """
                UPDATE inventory 
                SET quantity_available = %s, updated_date = NOW()
                WHERE store_name = %s AND item_id = %s
                """,
                (quantity, store_name, item_id)
            )
        else:
            # Use stored procedure for ADD/SUBTRACT operations
            call_procedure('sp_update_inventory', (store_name, item_id, quantity, operation))
            result = 1
        
        if result > 0:
            flash_success('Inventory updated successfully')
        else:
            flash_error('Failed to update inventory')
        
        return redirect(request.referrer or url_for('manager.inventory'))
    
    except Exception as e:
        logger.error(f"Update inventory error: {e}")
        flash_error('Error updating inventory')
        return redirect(request.referrer or url_for('manager.inventory'))

# =============================================
# TRANSPORTATION MANAGEMENT
# =============================================

@manager_bp.route('/transportation')
@manager_required
def transportation():
    """Transportation management page"""
    try:
        user = get_current_user()
        
        # Get train schedules (main managers only)
        train_schedules = []
        if is_main_manager():
            train_schedules = execute_query(
                """
                SELECT ts.*, t.train_name, t.capacity,
                       (ts.total_capacity - ts.available_capacity) as used_capacity
                FROM train_schedule ts
                INNER JOIN train t ON ts.train_id = t.train_id
                WHERE ts.departure_date >= CURDATE()
                ORDER BY ts.departure_date, ts.departure_time
                LIMIT 20
                """
            )
        
        # Get truck schedules
        if is_store_manager():
            store_filter = user['store_name']
        else:
            store_filter = request.args.get('store', '')
        
        truck_query = """
        SELECT ts.*, t.license_plate, d.first_name, d.last_name, 
               r.route_name, s.store_name
        FROM truck_schedule ts
        INNER JOIN truck t ON ts.truck_id = t.truck_id
        INNER JOIN driver d ON ts.driver_id = d.driver_id
        INNER JOIN route r ON ts.route_id = r.route_id
        INNER JOIN store s ON t.store_name = s.store_name
        WHERE ts.scheduled_date >= CURDATE()
        """
        
        params = []
        if store_filter:
            truck_query += " AND s.store_name = %s"
            params.append(store_filter)
        
        truck_query += " ORDER BY ts.scheduled_date, ts.start_time LIMIT 20"
        
        truck_schedules = execute_query(truck_query, params)
        
        return render_template('manager/transportation.html',
                             train_schedules=train_schedules,
                             truck_schedules=truck_schedules,
                             current_store=store_filter)
    
    except Exception as e:
        logger.error(f"Transportation page error: {e}")
        flash_error('Error loading transportation')
        return redirect(url_for('manager.store_dashboard' if is_store_manager() else 'manager.main_dashboard'))

@manager_bp.route('/schedule-train', methods=['POST'])
@main_manager_required
@audit_log(action="SCHEDULE_TRAIN", resource="TRAIN")
def schedule_train():
    """Schedule a train"""
    try:
        train_id = int(request.form.get('train_id', 0))
        departure_date = request.form.get('departure_date', '')
        departure_time = request.form.get('departure_time', '')
        route_description = sanitize_input(request.form.get('route_description', ''))
        
        # Validation
        if train_id <= 0 or not departure_date or not departure_time:
            flash_error('Please fill in all required fields')
            return redirect(request.referrer or url_for('manager.transportation'))
        
        # Schedule train using stored procedure
        result = call_procedure('sp_schedule_train', 
                               (train_id, departure_date, departure_time, route_description))
        
        if result:
            flash_success('Train scheduled successfully')
        else:
            flash_error('Failed to schedule train')
        
        return redirect(url_for('manager.transportation'))
    
    except Exception as e:
        logger.error(f"Schedule train error: {e}")
        flash_error('Error scheduling train')
        return redirect(url_for('manager.transportation'))

@manager_bp.route('/schedule-truck', methods=['POST'])
@manager_required
@audit_log(action="SCHEDULE_TRUCK", resource="TRUCK")
def schedule_truck():
    """Schedule a truck"""
    try:
        truck_id = int(request.form.get('truck_id', 0))
        driver_id = int(request.form.get('driver_id', 0))
        driver_assistant_id = request.form.get('driver_assistant_id')
        route_id = int(request.form.get('route_id', 0))
        scheduled_date = request.form.get('scheduled_date', '')
        start_time = request.form.get('start_time', '')
        
        # Convert empty string to None for optional assistant
        if driver_assistant_id and driver_assistant_id.isdigit():
            driver_assistant_id = int(driver_assistant_id)
        else:
            driver_assistant_id = None
        
        # Validation
        if any(x <= 0 for x in [truck_id, driver_id, route_id]) or not scheduled_date or not start_time:
            flash_error('Please fill in all required fields')
            return redirect(request.referrer or url_for('manager.transportation'))
        
        # Check permissions for store managers
        user = get_current_user()
        if is_store_manager():
            # Verify truck belongs to manager's store
            truck_store = execute_query(
                "SELECT store_name FROM truck WHERE truck_id = %s",
                (truck_id,),
                fetch_one=True
            )
            
            if not truck_store or truck_store['store_name'] != user['store_name']:
                flash_error('You can only schedule trucks for your store')
                return redirect(url_for('manager.transportation'))
        
        # Schedule truck using stored procedure
        result = call_procedure('sp_schedule_truck', 
                               (truck_id, driver_id, driver_assistant_id, route_id, 
                                scheduled_date, start_time))
        
        if result:
            flash_success('Truck scheduled successfully')
        else:
            flash_error('Failed to schedule truck')
        
        return redirect(url_for('manager.transportation'))
    
    except Exception as e:
        logger.error(f"Schedule truck error: {e}")
        flash_error('Error scheduling truck')
        return redirect(url_for('manager.transportation'))

# =============================================
# ORDER MANAGEMENT
# =============================================

@manager_bp.route('/orders-management')
@manager_required
def orders_management():
    """Orders management page"""
    try:
        user = get_current_user()
        
        # Get filter parameters
        page = int(request.args.get('page', 1))
        per_page = 20
        status_filter = request.args.get('status', '')
        store_filter = request.args.get('store', '')
        
        # For store managers, filter by their store
        if is_store_manager():
            store_filter = user['store_name']
        
        # Build query
        query = """
        SELECT o.*, c.first_name, c.last_name, c.email,
               r.route_name, s.store_name
        FROM order_table o
        INNER JOIN customers c ON o.customer_id = c.customer_id
        INNER JOIN route r ON o.route_id = r.route_id
        INNER JOIN store s ON r.store_name = s.store_name
        WHERE 1=1
        """
        
        params = []
        
        if status_filter:
            query += " AND o.status = %s"
            params.append(status_filter)
        
        if store_filter:
            query += " AND s.store_name = %s"
            params.append(store_filter)
        
        query += " ORDER BY o.order_date DESC"
        
        # Get results and paginate
        all_orders = execute_query(query, params)
        pagination = paginate_query(all_orders, page, per_page)
        
        # Get filter options
        if is_main_manager():
            stores = execute_query("SELECT store_name FROM store ORDER BY store_name")
        else:
            stores = []
        
        order_statuses = [
            'pending', 'confirmed', 'assigned_train', 'in_transit_rail',
            'at_warehouse', 'assigned_truck', 'out_for_delivery', 'delivered',
            'cancelled', 'returned'
        ]
        
        return render_template('manager/orders_management.html',
                             orders=pagination['items'],
                             pagination=pagination,
                             stores=stores,
                             order_statuses=order_statuses,
                             current_status=status_filter,
                             current_store=store_filter)
    
    except Exception as e:
        logger.error(f"Orders management error: {e}")
        flash_error('Error loading orders')
        return redirect(url_for('manager.store_dashboard' if is_store_manager() else 'manager.main_dashboard'))

@manager_bp.route('/update-order-status', methods=['POST'])
@manager_required
@audit_log(action="UPDATE_ORDER_STATUS", resource="ORDER")
def update_order_status():
    """Update order status"""
    try:
        order_id = int(request.form.get('order_id', 0))
        new_status = request.form.get('new_status', '')
        
        if order_id <= 0 or not new_status:
            flash_error('Invalid order or status')
            return redirect(request.referrer or url_for('manager.orders_management'))
        
        # Get current user for audit
        user = get_current_user()
        user_name = user['user_name']
        
        # Update order status using stored procedure
        call_procedure('sp_update_order_status', (order_id, new_status, user_name))
        
        flash_success(f'Order #{order_id} status updated to {new_status}')
        return redirect(request.referrer or url_for('manager.orders_management'))
    
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        flash_error('Error updating order status')
        return redirect(request.referrer or url_for('manager.orders_management'))

@manager_bp.route('/assign-order-to-train', methods=['POST'])
@main_manager_required
@audit_log(action="ASSIGN_ORDER_TRAIN", resource="ORDER")
def assign_order_to_train():
    """Assign order to train"""
    try:
        order_id = int(request.form.get('order_id', 0))
        train_session_id = int(request.form.get('train_session_id', 0))
        
        if order_id <= 0 or train_session_id <= 0:
            flash_error('Invalid order or train session')
            return redirect(request.referrer or url_for('manager.orders_management'))
        
        # Assign order to train using stored procedure
        call_procedure('sp_assign_order_to_train', (order_id, train_session_id))
        
        flash_success(f'Order #{order_id} assigned to train successfully')
        return redirect(request.referrer or url_for('manager.orders_management'))
    
    except Exception as e:
        logger.error(f"Assign order to train error: {e}")
        flash_error('Error assigning order to train')
        return redirect(request.referrer or url_for('manager.orders_management'))

# =============================================
# STAFF MANAGEMENT
# =============================================

@manager_bp.route('/staff-management')
@manager_required
def staff_management():
    """Staff management page"""
    try:
        user = get_current_user()
        
        # For store managers, show only their store's staff
        if is_store_manager():
            store_filter = user['store_name']
        else:
            store_filter = request.args.get('store', '')
        
        # Get drivers
        driver_query = """
        SELECT d.*, 
               ROUND((d.weekly_hours / d.max_weekly_hours * 100), 1) as hour_utilization
        FROM driver d
        WHERE d.is_active = TRUE
        """
        
        driver_params = []
        if store_filter:
            driver_query += " AND d.store_name = %s"
            driver_params.append(store_filter)
        
        driver_query += " ORDER BY d.first_name, d.last_name"
        
        drivers = execute_query(driver_query, driver_params)
        
        # Get driver assistants
        assistant_query = """
        SELECT da.*,
               ROUND((da.weekly_hours / da.max_weekly_hours * 100), 1) as hour_utilization
        FROM driver_assistant da
        WHERE da.is_active = TRUE
        """
        
        assistant_params = []
        if store_filter:
            assistant_query += " AND da.store_name = %s"
            assistant_params.append(store_filter)
        
        assistant_query += " ORDER BY da.first_name, da.last_name"
        
        assistants = execute_query(assistant_query, assistant_params)
        
        # Get trucks
        truck_query = """
        SELECT t.*, COUNT(ts.truck_session_id) as scheduled_trips
        FROM truck t
        LEFT JOIN truck_schedule ts ON t.truck_id = ts.truck_id 
                                     AND ts.scheduled_date >= CURDATE()
        WHERE t.status = 'active'
        """
        
        truck_params = []
        if store_filter:
            truck_query += " AND t.store_name = %s"
            truck_params.append(store_filter)
        
        truck_query += " GROUP BY t.truck_id ORDER BY t.license_plate"
        
        trucks = execute_query(truck_query, truck_params)
        
        return render_template('manager/staff_management.html',
                             drivers=drivers,
                             assistants=assistants,
                             trucks=trucks,
                             current_store=store_filter)
    
    except Exception as e:
        logger.error(f"Staff management error: {e}")
        flash_error('Error loading staff management')
        return redirect(url_for('manager.store_dashboard' if is_store_manager() else 'manager.main_dashboard'))

# =============================================
# HELPER FUNCTIONS
# =============================================

def _get_store_stats(store_name: str) -> dict:
    """Get store-specific statistics"""
    try:
        # Today's orders
        todays_orders = execute_query(
            """
            SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as revenue
            FROM order_table o
            INNER JOIN route r ON o.route_id = r.route_id
            WHERE r.store_name = %s AND DATE(o.order_date) = CURDATE()
            """,
            (store_name,),
            fetch_one=True
        )
        
        # Pending orders
        pending_orders = execute_query(
            """
            SELECT COUNT(*) as count
            FROM order_table o
            INNER JOIN route r ON o.route_id = r.route_id
            WHERE r.store_name = %s AND o.status IN ('confirmed', 'at_warehouse')
            """,
            (store_name,),
            fetch_one=True
        )
        
        # Total inventory value
        inventory_value = execute_query(
            """
            SELECT COALESCE(SUM(quantity_available * cost_per_unit), 0) as value
            FROM inventory
            WHERE store_name = %s
            """,
            (store_name,),
            fetch_one=True
        )
        
        # Active trucks
        active_trucks = execute_query(
            """
            SELECT COUNT(*) as count
            FROM truck
            WHERE store_name = %s AND status = 'active'
            """,
            (store_name,),
            fetch_one=True
        )
        
        return {
            'todays_orders': todays_orders['count'] if todays_orders else 0,
            'todays_revenue': todays_orders['revenue'] if todays_orders else 0,
            'pending_orders': pending_orders['count'] if pending_orders else 0,
            'inventory_value': inventory_value['value'] if inventory_value else 0,
            'active_trucks': active_trucks['count'] if active_trucks else 0
        }
    
    except Exception as e:
        logger.error(f"Error getting store stats: {e}")
        return {
            'todays_orders': 0,
            'todays_revenue': 0,
            'pending_orders': 0,
            'inventory_value': 0,
            'active_trucks': 0
        }

def _get_system_stats() -> dict:
    """Get system-wide statistics"""
    try:
        # Total orders today
        todays_orders = execute_query(
            "SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as revenue FROM order_table WHERE DATE(order_date) = CURDATE()",
            fetch_one=True
        )
        
        # Active orders
        active_orders = execute_query(
            "SELECT COUNT(*) as count FROM order_table WHERE status NOT IN ('delivered', 'cancelled', 'returned')",
            fetch_one=True
        )
        
        # Total customers
        total_customers = execute_query(
            "SELECT COUNT(*) as count FROM customers",
            fetch_one=True
        )
        
        # Active trains
        active_trains = execute_query(
            "SELECT COUNT(*) as count FROM train WHERE status = 'active'",
            fetch_one=True
        )
        
        # Active trucks
        active_trucks = execute_query(
            "SELECT COUNT(*) as count FROM truck WHERE status = 'active'",
            fetch_one=True
        )
        
        return {
            'todays_orders': todays_orders['count'] if todays_orders else 0,
            'todays_revenue': todays_orders['revenue'] if todays_orders else 0,
            'active_orders': active_orders['count'] if active_orders else 0,
            'total_customers': total_customers['count'] if total_customers else 0,
            'active_trains': active_trains['count'] if active_trains else 0,
            'active_trucks': active_trucks['count'] if active_trucks else 0
        }
    
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {
            'todays_orders': 0,
            'todays_revenue': 0,
            'active_orders': 0,
            'total_customers': 0,
            'active_trains': 0,
            'active_trucks': 0
        }