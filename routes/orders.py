"""
Supply Chain Management System - Orders Routes
Routes for order-specific functionality including order tracking, status updates,
and order management operations.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from decimal import Decimal
from datetime import datetime, date, timedelta
import logging

# Import database models and utilities
from database.models import Order, Customer
from database.connection import execute_query, execute_update, call_procedure, call_function
from utils.decorators import login_required, customer_required, manager_required, api_response, rate_limit, audit_log
from utils.helpers import (
    get_current_user, is_customer, is_manager, format_currency, format_date,
    sanitize_input, paginate_query, flash_success, flash_error, flash_warning, flash_info
)

# Create blueprint
orders_bp = Blueprint('orders', __name__)
logger = logging.getLogger(__name__)

# =============================================
# ORDER TRACKING ROUTES
# =============================================

@orders_bp.route('/track/<int:order_id>')
@login_required
def track_order(order_id):
    """Track order status and location"""
    try:
        user = get_current_user()
        
        # Build query based on user role
        if is_customer():
            # Customers can only track their own orders
            order_query = """
            SELECT o.*, c.first_name, c.last_name, r.route_name, 
                   r.destination_city, s.store_name
            FROM order_table o
            INNER JOIN customers c ON o.customer_id = c.customer_id
            INNER JOIN route r ON o.route_id = r.route_id
            INNER JOIN store s ON r.store_name = s.store_name
            WHERE o.order_id = %s AND o.customer_id = %s
            """
            params = (order_id, user['customer_id'])
        else:
            # Managers can track any order
            order_query = """
            SELECT o.*, c.first_name, c.last_name, r.route_name, 
                   r.destination_city, s.store_name
            FROM order_table o
            INNER JOIN customers c ON o.customer_id = c.customer_id
            INNER JOIN route r ON o.route_id = r.route_id
            INNER JOIN store s ON r.store_name = s.store_name
            WHERE o.order_id = %s
            """
            params = (order_id,)
        
        order = execute_query(order_query, params, fetch_one=True)
        
        if not order:
            flash_error('Order not found')
            return redirect(url_for('customer.orders' if is_customer() else 'manager.orders_management'))
        
        # Get order items
        order_items = execute_query(
            """
            SELECT oi.*, i.item_name, i.category
            FROM order_items oi
            INNER JOIN items i ON oi.item_id = i.item_id
            WHERE oi.order_id = %s
            ORDER BY oi.order_item_id
            """,
            (order_id,)
        )
        
        # Get tracking timeline
        tracking_timeline = _get_tracking_timeline(order_id)
        
        # Get transportation details
        transport_details = _get_transport_details(order_id)
        
        return render_template('orders/track_order.html',
                             order=order,
                             order_items=order_items,
                             tracking_timeline=tracking_timeline,
                             transport_details=transport_details)
    
    except Exception as e:
        logger.error(f"Track order error: {e}")
        flash_error('Error loading order tracking information')
        return redirect(url_for('customer.orders' if is_customer() else 'manager.orders_management'))

@orders_bp.route('/status/<int:order_id>')
@login_required
def order_status(order_id):
    """Get order status information (AJAX endpoint)"""
    try:
        user = get_current_user()
        
        # Check permissions
        if is_customer():
            order = execute_query(
                "SELECT * FROM order_table WHERE order_id = %s AND customer_id = %s",
                (order_id, user['customer_id']),
                fetch_one=True
            )
        else:
            order = execute_query(
                "SELECT * FROM order_table WHERE order_id = %s",
                (order_id,),
                fetch_one=True
            )
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Get current status and estimated delivery
        status_info = {
            'order_id': order['order_id'],
            'status': order['status'],
            'delivery_date': order['delivery_date'].isoformat() if order['delivery_date'] else None,
            'total_amount': float(order['total_amount']),
            'payment_status': order['payment_status']
        }
        
        # Get latest tracking update
        latest_update = execute_query(
            """
            SELECT operation, timestamp 
            FROM audit_log 
            WHERE table_name = 'order_table' AND record_id = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
            """,
            (str(order_id),),
            fetch_one=True
        )
        
        if latest_update:
            status_info['last_updated'] = latest_update['timestamp'].isoformat()
        
        return jsonify(status_info)
    
    except Exception as e:
        logger.error(f"Order status error: {e}")
        return jsonify({'error': 'Error retrieving order status'}), 500

# =============================================
# ORDER SEARCH ROUTES
# =============================================

@orders_bp.route('/search')
@login_required
def search_orders():
    """Search orders"""
    try:
        user = get_current_user()
        
        # Get search parameters
        query = sanitize_input(request.args.get('q', ''))
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        page = int(request.args.get('page', 1))
        per_page = 20
        
        if not query and not status and not date_from:
            flash_info('Please enter search criteria')
            return redirect(url_for('customer.orders' if is_customer() else 'manager.orders_management'))
        
        # Build search query
        search_query = """
        SELECT o.*, c.first_name, c.last_name, r.route_name, s.store_name
        FROM order_table o
        INNER JOIN customers c ON o.customer_id = c.customer_id
        INNER JOIN route r ON o.route_id = r.route_id
        INNER JOIN store s ON r.store_name = s.store_name
        WHERE 1=1
        """
        
        params = []
        
        # Add customer filter for customer users
        if is_customer():
            search_query += " AND o.customer_id = %s"
            params.append(user['customer_id'])
        
        # Add search filters
        if query:
            search_query += """ AND (
                o.order_id LIKE %s OR
                c.first_name LIKE %s OR
                c.last_name LIKE %s OR
                c.email LIKE %s OR
                r.route_name LIKE %s
            )"""
            search_term = f"%{query}%"
            params.extend([search_term] * 5)
        
        if status:
            search_query += " AND o.status = %s"
            params.append(status)
        
        if date_from:
            search_query += " AND o.order_date >= %s"
            params.append(date_from)
        
        if date_to:
            search_query += " AND o.order_date <= %s"
            params.append(f"{date_to} 23:59:59")
        
        search_query += " ORDER BY o.order_date DESC"
        
        # Execute search and paginate
        all_results = execute_query(search_query, params)
        pagination = paginate_query(all_results, page, per_page)
        
        return render_template('orders/search_results.html',
                             orders=pagination['items'],
                             pagination=pagination,
                             search_query=query,
                             search_status=status,
                             search_date_from=date_from,
                             search_date_to=date_to)
    
    except Exception as e:
        logger.error(f"Search orders error: {e}")
        flash_error('Error searching orders')
        return redirect(url_for('customer.orders' if is_customer() else 'manager.orders_management'))

# =============================================
# ORDER MANAGEMENT ROUTES (MANAGERS ONLY)
# =============================================

@orders_bp.route('/bulk-update', methods=['POST'])
@manager_required
@audit_log(action="BULK_UPDATE_ORDERS", resource="ORDER")
def bulk_update_orders():
    """Bulk update order statuses"""
    try:
        order_ids = request.form.getlist('order_ids')
        new_status = request.form.get('new_status', '')
        
        if not order_ids or not new_status:
            flash_error('Please select orders and specify status')
            return redirect(request.referrer or url_for('manager.orders_management'))
        
        # Validate order IDs
        try:
            order_ids = [int(oid) for oid in order_ids if oid.isdigit()]
        except ValueError:
            flash_error('Invalid order IDs')
            return redirect(request.referrer or url_for('manager.orders_management'))
        
        if not order_ids:
            flash_error('No valid orders selected')
            return redirect(request.referrer or url_for('manager.orders_management'))
        
        # Update each order
        user = get_current_user()
        user_name = user['user_name']
        updated_count = 0
        
        for order_id in order_ids:
            try:
                call_procedure('sp_update_order_status', (order_id, new_status, user_name))
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating order {order_id}: {e}")
        
        flash_success(f'Updated {updated_count} orders to {new_status}')
        return redirect(request.referrer or url_for('manager.orders_management'))
    
    except Exception as e:
        logger.error(f"Bulk update orders error: {e}")
        flash_error('Error updating orders')
        return redirect(request.referrer or url_for('manager.orders_management'))

@orders_bp.route('/cancel/<int:order_id>', methods=['POST'])
@login_required
@audit_log(action="CANCEL_ORDER", resource="ORDER")
def cancel_order(order_id):
    """Cancel an order"""
    try:
        user = get_current_user()
        
        # Check permissions
        if is_customer():
            # Customers can only cancel their own orders
            order = execute_query(
                "SELECT * FROM order_table WHERE order_id = %s AND customer_id = %s",
                (order_id, user['customer_id']),
                fetch_one=True
            )
        else:
            # Managers can cancel any order
            order = execute_query(
                "SELECT * FROM order_table WHERE order_id = %s",
                (order_id,),
                fetch_one=True
            )
        
        if not order:
            flash_error('Order not found')
            return redirect(request.referrer or url_for('customer.orders'))
        
        # Check if order can be cancelled
        if order['status'] in ['delivered', 'cancelled', 'returned']:
            flash_error('Order cannot be cancelled')
            return redirect(request.referrer or url_for('customer.orders'))
        
        # Cancel order
        call_procedure('sp_update_order_status', (order_id, 'cancelled', user['user_name']))
        
        flash_success(f'Order #{order_id} has been cancelled')
        return redirect(request.referrer or url_for('customer.orders'))
    
    except Exception as e:
        logger.error(f"Cancel order error: {e}")
        flash_error('Error cancelling order')
        return redirect(request.referrer or url_for('customer.orders'))

# =============================================
# ORDER EXPORT ROUTES
# =============================================

@orders_bp.route('/export')
@manager_required
def export_orders():
    """Export orders to CSV"""
    try:
        # Get filter parameters
        status = request.args.get('status', '')
        store = request.args.get('store', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Build export query
        export_query = """
        SELECT 
            o.order_id,
            o.order_date,
            o.delivery_date,
            o.status,
            o.total_amount,
            o.payment_status,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            c.email as customer_email,
            r.route_name,
            r.destination_city,
            s.store_name
        FROM order_table o
        INNER JOIN customers c ON o.customer_id = c.customer_id
        INNER JOIN route r ON o.route_id = r.route_id
        INNER JOIN store s ON r.store_name = s.store_name
        WHERE 1=1
        """
        
        params = []
        
        if status:
            export_query += " AND o.status = %s"
            params.append(status)
        
        if store:
            export_query += " AND s.store_name = %s"
            params.append(store)
        
        if date_from:
            export_query += " AND o.order_date >= %s"
            params.append(date_from)
        
        if date_to:
            export_query += " AND o.order_date <= %s"
            params.append(f"{date_to} 23:59:59")
        
        export_query += " ORDER BY o.order_date DESC"
        
        # Get data
        orders_data = execute_query(export_query, params)
        
        if not orders_data:
            flash_warning('No orders found for export')
            return redirect(request.referrer or url_for('manager.orders_management'))
        
        # Generate CSV content
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Order ID', 'Order Date', 'Delivery Date', 'Status', 'Total Amount',
            'Payment Status', 'Customer Name', 'Customer Email', 'Route',
            'Destination City', 'Store'
        ])
        
        # Write data
        for order in orders_data:
            writer.writerow([
                order['order_id'],
                order['order_date'].strftime('%Y-%m-%d') if order['order_date'] else '',
                order['delivery_date'].strftime('%Y-%m-%d') if order['delivery_date'] else '',
                order['status'],
                float(order['total_amount']),
                order['payment_status'],
                order['customer_name'],
                order['customer_email'],
                order['route_name'],
                order['destination_city'],
                order['store_name']
            ])
        
        # Create response
        from flask import Response
        
        output.seek(0)
        filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
    
    except Exception as e:
        logger.error(f"Export orders error: {e}")
        flash_error('Error exporting orders')
        return redirect(request.referrer or url_for('manager.orders_management'))

# =============================================
# API ENDPOINTS
# =============================================

@orders_bp.route('/api/orders')
@login_required
@api_response
def api_get_orders():
    """Get orders via API"""
    try:
        user = get_current_user()
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status', '')
        
        # Build query based on user role
        if is_customer():
            query = """
            SELECT o.*, r.route_name, s.store_name
            FROM order_table o
            INNER JOIN route r ON o.route_id = r.route_id
            INNER JOIN store s ON r.store_name = s.store_name
            WHERE o.customer_id = %s
            """
            params = [user['customer_id']]
        else:
            query = """
            SELECT o.*, c.first_name, c.last_name, r.route_name, s.store_name
            FROM order_table o
            INNER JOIN customers c ON o.customer_id = c.customer_id
            INNER JOIN route r ON o.route_id = r.route_id
            INNER JOIN store s ON r.store_name = s.store_name
            WHERE 1=1
            """
            params = []
        
        if status:
            query += " AND o.status = %s"
            params.append(status)
        
        query += " ORDER BY o.order_date DESC"
        
        # Get all orders and paginate
        all_orders = execute_query(query, params)
        pagination = paginate_query(all_orders, page, per_page)
        
        # Convert to JSON-serializable format
        orders_data = []
        for order in pagination['items']:
            order_dict = dict(order)
            # Convert date objects to strings
            if order_dict.get('order_date'):
                order_dict['order_date'] = order_dict['order_date'].isoformat()
            if order_dict.get('delivery_date'):
                order_dict['delivery_date'] = order_dict['delivery_date'].isoformat()
            if order_dict.get('created_date'):
                order_dict['created_date'] = order_dict['created_date'].isoformat()
            if order_dict.get('updated_date'):
                order_dict['updated_date'] = order_dict['updated_date'].isoformat()
            
            # Convert Decimal to float
            for key, value in order_dict.items():
                if isinstance(value, Decimal):
                    order_dict[key] = float(value)
            
            orders_data.append(order_dict)
        
        return {
            'orders': orders_data,
            'pagination': {
                'page': pagination['page'],
                'pages': pagination['pages'],
                'per_page': pagination['per_page'],
                'total': pagination['total'],
                'has_prev': pagination['has_prev'],
                'has_next': pagination['has_next']
            }
        }
    
    except Exception as e:
        logger.error(f"API get orders error: {e}")
        return {'error': 'Error retrieving orders'}, 500

@orders_bp.route('/api/order/<int:order_id>')
@login_required
@api_response
def api_get_order(order_id):
    """Get single order via API"""
    try:
        user = get_current_user()
        
        # Check permissions
        if is_customer():
            order = execute_query(
                """
                SELECT o.*, r.route_name, r.destination_city, s.store_name
                FROM order_table o
                INNER JOIN route r ON o.route_id = r.route_id
                INNER JOIN store s ON r.store_name = s.store_name
                WHERE o.order_id = %s AND o.customer_id = %s
                """,
                (order_id, user['customer_id']),
                fetch_one=True
            )
        else:
            order = execute_query(
                """
                SELECT o.*, c.first_name, c.last_name, c.email,
                       r.route_name, r.destination_city, s.store_name
                FROM order_table o
                INNER JOIN customers c ON o.customer_id = c.customer_id
                INNER JOIN route r ON o.route_id = r.route_id
                INNER JOIN store s ON r.store_name = s.store_name
                WHERE o.order_id = %s
                """,
                (order_id,),
                fetch_one=True
            )
        
        if not order:
            return {'error': 'Order not found'}, 404
        
        # Get order items
        order_items = execute_query(
            """
            SELECT oi.*, i.item_name, i.category
            FROM order_items oi
            INNER JOIN items i ON oi.item_id = i.item_id
            WHERE oi.order_id = %s
            """,
            (order_id,)
        )
        
        # Convert to JSON-serializable format
        order_dict = dict(order)
        for key, value in order_dict.items():
            if isinstance(value, (date, datetime)):
                order_dict[key] = value.isoformat()
            elif isinstance(value, Decimal):
                order_dict[key] = float(value)
        
        items_data = []
        for item in order_items:
            item_dict = dict(item)
            for key, value in item_dict.items():
                if isinstance(value, Decimal):
                    item_dict[key] = float(value)
            items_data.append(item_dict)
        
        return {
            'order': order_dict,
            'items': items_data
        }
    
    except Exception as e:
        logger.error(f"API get order error: {e}")
        return {'error': 'Error retrieving order'}, 500

# =============================================
# HELPER FUNCTIONS
# =============================================

def _get_tracking_timeline(order_id: int) -> list:
    """Get order tracking timeline"""
    try:
        # Get status changes from audit log
        status_changes = execute_query(
            """
            SELECT 
                JSON_UNQUOTE(JSON_EXTRACT(new_values, '$.status')) as status,
                timestamp
            FROM audit_log
            WHERE table_name = 'order_table' 
            AND record_id = %s 
            AND operation = 'UPDATE'
            AND JSON_EXTRACT(new_values, '$.status') IS NOT NULL
            ORDER BY timestamp ASC
            """,
            (str(order_id),)
        )
        
        # Add initial order creation
        order_created = execute_query(
            "SELECT order_date FROM order_table WHERE order_id = %s",
            (order_id,),
            fetch_one=True
        )
        
        timeline = []
        
        if order_created:
            timeline.append({
                'status': 'pending',
                'timestamp': order_created['order_date'],
                'description': 'Order placed'
            })
        
        # Add status changes
        status_descriptions = {
            'confirmed': 'Order confirmed',
            'assigned_train': 'Assigned to train transport',
            'in_transit_rail': 'In transit by rail',
            'at_warehouse': 'Arrived at destination warehouse',
            'assigned_truck': 'Assigned to truck for delivery',
            'out_for_delivery': 'Out for delivery',
            'delivered': 'Order delivered',
            'cancelled': 'Order cancelled',
            'returned': 'Order returned'
        }
        
        for change in status_changes:
            timeline.append({
                'status': change['status'],
                'timestamp': change['timestamp'],
                'description': status_descriptions.get(change['status'], change['status'].title())
            })
        
        return timeline
    
    except Exception as e:
        logger.error(f"Error getting tracking timeline: {e}")
        return []

def _get_transport_details(order_id: int) -> dict:
    """Get transportation details for order"""
    try:
        # Get train assignment
        train_assignment = execute_query(
            """
            SELECT ots.*, ts.departure_date, ts.departure_time, 
                   t.train_name, t.train_type
            FROM order_train_schedule ots
            INNER JOIN train_schedule ts ON ots.train_session_id = ts.train_session_id
            INNER JOIN train t ON ts.train_id = t.train_id
            WHERE ots.order_id = %s
            """,
            (order_id,),
            fetch_one=True
        )
        
        # Get truck assignment
        truck_assignment = execute_query(
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
            'train': train_assignment,
            'truck': truck_assignment
        }
    
    except Exception as e:
        logger.error(f"Error getting transport details: {e}")
        return {
            'train': None,
            'truck': None
        }