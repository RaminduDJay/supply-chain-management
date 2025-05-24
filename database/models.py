"""
Supply Chain Management System - Database Models
This module contains model classes and business logic for database operations.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, time
from dataclasses import dataclass, field
from decimal import Decimal
import bcrypt
import logging
from .connection import get_db, execute_query, execute_update, call_procedure, call_function

logger = logging.getLogger(__name__)

# =============================================
# BASE MODEL CLASS
# =============================================

class BaseModel:
    """Base class for all models with common functionality"""
    
    @classmethod
    def get_db(cls):
        """Get database instance"""
        return get_db()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model instance from dictionary"""
        return cls(**data)

# =============================================
# USER MANAGEMENT MODELS
# =============================================

@dataclass
class User(BaseModel):
    """User model for authentication"""
    user_name: str
    password: str = ""
    role: str = ""
    created_date: datetime = None
    last_login: datetime = None
    is_active: bool = True
    
    @classmethod
    def authenticate(cls, user_name: str, password: str) -> Optional['User']:
        """
        Authenticate user login
        
        Args:
            user_name: Username
            password: Plain text password
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        try:
            result = call_procedure('sp_authenticate_user', (user_name, password))
            
            if result and result[0]['status'] == 'Success':
                user_data = execute_query(
                    "SELECT * FROM users WHERE user_name = %s",
                    (user_name,),
                    fetch_one=True
                )
                return cls.from_dict(user_data) if user_data else None
            
            return None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    @classmethod
    def create_user(cls, user_name: str, password: str, role: str) -> bool:
        """
        Create a new user
        
        Args:
            user_name: Username
            password: Plain text password
            role: User role
            
        Returns:
            True if user created successfully
        """
        try:
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            execute_update(
                "INSERT INTO users (user_name, password, role) VALUES (%s, %s, %s)",
                (user_name, hashed_password, role)
            )
            return True
            
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return False
    
    def update_last_login(self):
        """Update user's last login timestamp"""
        try:
            execute_update(
                "UPDATE users SET last_login = NOW() WHERE user_name = %s",
                (self.user_name,)
            )
            self.last_login = datetime.now()
            
        except Exception as e:
            logger.error(f"Last login update error: {e}")

@dataclass
class Customer(BaseModel):
    """Customer model"""
    customer_id: int = None
    user_name: str = ""
    customer_type: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    postal_code: str = ""
    credit_limit: Decimal = Decimal('10000.00')
    current_balance: Decimal = Decimal('0.00')
    created_date: datetime = None
    
    @classmethod
    def create_customer(cls, user_name: str, password: str, customer_type: str,
                       first_name: str, last_name: str, email: str, **kwargs) -> Optional['Customer']:
        """
        Create a new customer account
        
        Args:
            user_name: Username
            password: Password
            customer_type: Type of customer (end, retail, wholesale)
            first_name: First name
            last_name: Last name
            email: Email address
            **kwargs: Additional customer details
            
        Returns:
            Customer instance if created successfully
        """
        try:
            result = call_procedure('sp_create_customer', (
                user_name, password, customer_type, first_name, last_name, email,
                kwargs.get('phone', ''), kwargs.get('address', ''),
                kwargs.get('city', ''), kwargs.get('postal_code', '')
            ))
            
            if result:
                customer_data = execute_query(
                    "SELECT * FROM customers WHERE user_name = %s",
                    (user_name,),
                    fetch_one=True
                )
                return cls.from_dict(customer_data) if customer_data else None
            
            return None
            
        except Exception as e:
            logger.error(f"Customer creation error: {e}")
            return None
    
    @classmethod
    def get_by_id(cls, customer_id: int) -> Optional['Customer']:
        """Get customer by ID"""
        try:
            customer_data = execute_query(
                "SELECT * FROM customers WHERE customer_id = %s",
                (customer_id,),
                fetch_one=True
            )
            return cls.from_dict(customer_data) if customer_data else None
            
        except Exception as e:
            logger.error(f"Customer retrieval error: {e}")
            return None
    
    @classmethod
    def get_by_username(cls, user_name: str) -> Optional['Customer']:
        """Get customer by username"""
        try:
            customer_data = execute_query(
                "SELECT * FROM customers WHERE user_name = %s",
                (user_name,),
                fetch_one=True
            )
            return cls.from_dict(customer_data) if customer_data else None
            
        except Exception as e:
            logger.error(f"Customer retrieval error: {e}")
            return None
    
    def get_full_name(self) -> str:
        """Get customer's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_discount_rate(self) -> Decimal:
        """Get customer's discount rate"""
        try:
            result = execute_query(
                "SELECT discount_rate FROM customer_type WHERE customer_type = %s",
                (self.customer_type,),
                fetch_one=True
            )
            return Decimal(str(result['discount_rate'])) if result else Decimal('0.00')
            
        except Exception as e:
            logger.error(f"Discount rate retrieval error: {e}")
            return Decimal('0.00')

# =============================================
# PRODUCT & INVENTORY MODELS
# =============================================

@dataclass
class Item(BaseModel):
    """Product item model"""
    item_id: int = None
    item_name: str = ""
    category: str = ""
    subcategory: str = ""
    description: str = ""
    price: Decimal = Decimal('0.00')
    weight: Decimal = Decimal('0.00')
    volume: Decimal = Decimal('0.00')
    fragile: bool = False
    hazardous: bool = False
    stock_threshold: int = 10
    is_active: bool = True
    created_date: datetime = None
    updated_date: datetime = None
    
    @classmethod
    def get_all_active(cls) -> List['Item']:
        """Get all active items"""
        try:
            items_data = execute_query(
                "SELECT * FROM items WHERE is_active = TRUE ORDER BY item_name"
            )
            return [cls.from_dict(item) for item in items_data]
            
        except Exception as e:
            logger.error(f"Items retrieval error: {e}")
            return []
    
    @classmethod
    def get_by_category(cls, category: str) -> List['Item']:
        """Get items by category"""
        try:
            items_data = execute_query(
                "SELECT * FROM items WHERE category = %s AND is_active = TRUE ORDER BY item_name",
                (category,)
            )
            return [cls.from_dict(item) for item in items_data]
            
        except Exception as e:
            logger.error(f"Items by category retrieval error: {e}")
            return []
    
    @classmethod
    def search(cls, search_term: str) -> List['Item']:
        """Search items by name or description"""
        try:
            search_pattern = f"%{search_term}%"
            items_data = execute_query(
                """
                SELECT * FROM items 
                WHERE (item_name LIKE %s OR description LIKE %s) 
                AND is_active = TRUE 
                ORDER BY item_name
                """,
                (search_pattern, search_pattern)
            )
            return [cls.from_dict(item) for item in items_data]
            
        except Exception as e:
            logger.error(f"Item search error: {e}")
            return []

@dataclass
class CartItem(BaseModel):
    """Shopping cart item model"""
    cart_id: int = None
    customer_id: int = None
    item_id: int = None
    quantity: int = 1
    added_date: datetime = None
    updated_date: datetime = None
    
    # Joined fields from items table
    item_name: str = ""
    price: Decimal = Decimal('0.00')
    weight: Decimal = Decimal('0.00')
    volume: Decimal = Decimal('0.00')
    
    @classmethod
    def add_to_cart(cls, customer_id: int, item_id: int, quantity: int = 1) -> bool:
        """Add item to cart"""
        try:
            call_procedure('sp_add_to_cart', (customer_id, item_id, quantity))
            return True
            
        except Exception as e:
            logger.error(f"Add to cart error: {e}")
            return False
    
    @classmethod
    def get_cart_contents(cls, customer_id: int) -> List['CartItem']:
        """Get cart contents for customer"""
        try:
            cart_data = call_procedure('sp_get_cart_summary', (customer_id,))
            return [cls.from_dict(item) for item in cart_data]
            
        except Exception as e:
            logger.error(f"Cart retrieval error: {e}")
            return []
    
    @classmethod
    def remove_from_cart(cls, customer_id: int, item_id: int) -> bool:
        """Remove item from cart"""
        try:
            execute_update(
                "DELETE FROM cart WHERE customer_id = %s AND item_id = %s",
                (customer_id, item_id)
            )
            return True
            
        except Exception as e:
            logger.error(f"Remove from cart error: {e}")
            return False
    
    @classmethod
    def clear_cart(cls, customer_id: int) -> bool:
        """Clear customer's cart"""
        try:
            execute_update(
                "DELETE FROM cart WHERE customer_id = %s",
                (customer_id,)
            )
            return True
            
        except Exception as e:
            logger.error(f"Clear cart error: {e}")
            return False
    
    def get_line_total(self) -> Decimal:
        """Calculate line total for cart item"""
        return self.price * Decimal(str(self.quantity))
    
    def get_total_weight(self) -> Decimal:
        """Calculate total weight for cart item"""
        return self.weight * Decimal(str(self.quantity))
    
    def get_total_volume(self) -> Decimal:
        """Calculate total volume for cart item"""
        return self.volume * Decimal(str(self.quantity))

# =============================================
# ORDER MANAGEMENT MODELS
# =============================================

@dataclass
class Order(BaseModel):
    """Order model"""
    order_id: int = None
    customer_id: int = None
    route_id: int = None
    order_date: datetime = None
    delivery_date: date = None
    requested_delivery_time: time = None
    status: str = "pending"
    total_items: int = 0
    total_weight: Decimal = Decimal('0.00')
    total_volume: Decimal = Decimal('0.00')
    subtotal: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    shipping_cost: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    payment_status: str = "pending"
    special_instructions: str = ""
    priority: str = "standard"
    created_date: datetime = None
    updated_date: datetime = None
    
    @classmethod
    def create_from_cart(cls, customer_id: int, route_id: int, delivery_date: date,
                        special_instructions: str = "") -> Optional['Order']:
        """Create order from customer's cart"""
        try:
            result = call_procedure('sp_create_order_from_cart', 
                                   (customer_id, route_id, delivery_date, special_instructions))
            
            if result and result[0].get('order_id'):
                order_id = result[0]['order_id']
                return cls.get_by_id(order_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Order creation error: {e}")
            return None
    
    @classmethod
    def get_by_id(cls, order_id: int) -> Optional['Order']:
        """Get order by ID"""
        try:
            order_data = execute_query(
                "SELECT * FROM order_table WHERE order_id = %s",
                (order_id,),
                fetch_one=True
            )
            return cls.from_dict(order_data) if order_data else None
            
        except Exception as e:
            logger.error(f"Order retrieval error: {e}")
            return None
    
    @classmethod
    def get_by_customer(cls, customer_id: int, limit: int = 50) -> List['Order']:
        """Get orders for customer"""
        try:
            orders_data = execute_query(
                """
                SELECT * FROM order_table 
                WHERE customer_id = %s 
                ORDER BY order_date DESC 
                LIMIT %s
                """,
                (customer_id, limit)
            )
            return [cls.from_dict(order) for order in orders_data]
            
        except Exception as e:
            logger.error(f"Customer orders retrieval error: {e}")
            return []
    
    @classmethod
    def get_by_status(cls, status: str, limit: int = 100) -> List['Order']:
        """Get orders by status"""
        try:
            orders_data = execute_query(
                """
                SELECT * FROM order_table 
                WHERE status = %s 
                ORDER BY order_date DESC 
                LIMIT %s
                """,
                (status, limit)
            )
            return [cls.from_dict(order) for order in orders_data]
            
        except Exception as e:
            logger.error(f"Orders by status retrieval error: {e}")
            return []
    
    def update_status(self, new_status: str, user_name: str = None) -> bool:
        """Update order status"""
        try:
            call_procedure('sp_update_order_status', (self.order_id, new_status, user_name))
            self.status = new_status
            return True
            
        except Exception as e:
            logger.error(f"Order status update error: {e}")
            return False
    
    def get_items(self) -> List[Dict[str, Any]]:
        """Get order items"""
        try:
            return execute_query(
                """
                SELECT oi.*, i.item_name, i.category
                FROM order_items oi
                INNER JOIN items i ON oi.item_id = i.item_id
                WHERE oi.order_id = %s
                ORDER BY oi.order_item_id
                """,
                (self.order_id,)
            )
            
        except Exception as e:
            logger.error(f"Order items retrieval error: {e}")
            return []

# =============================================
# TRANSPORTATION MODELS
# =============================================

@dataclass
class Train(BaseModel):
    """Train model"""
    train_id: int = None
    train_name: str = ""
    train_type: str = "standard"
    capacity: int = 0
    max_weight: Decimal = Decimal('0.00')
    max_volume: Decimal = Decimal('0.00')
    operational_cost_per_km: Decimal = Decimal('5.00')
    status: str = "active"
    purchase_date: date = None
    last_maintenance: date = None
    next_maintenance: date = None
    created_date: datetime = None
    
    @classmethod
    def get_active_trains(cls) -> List['Train']:
        """Get all active trains"""
        try:
            trains_data = execute_query(
                "SELECT * FROM train WHERE status = 'active' ORDER BY train_name"
            )
            return [cls.from_dict(train) for train in trains_data]
            
        except Exception as e:
            logger.error(f"Active trains retrieval error: {e}")
            return []
    
    def schedule_train(self, departure_date: date, departure_time: time, 
                      route_description: str) -> bool:
        """Schedule train for departure"""
        try:
            call_procedure('sp_schedule_train', 
                          (self.train_id, departure_date, departure_time, route_description))
            return True
            
        except Exception as e:
            logger.error(f"Train scheduling error: {e}")
            return False

@dataclass
class TrainSchedule(BaseModel):
    """Train schedule model"""
    train_session_id: int = None
    train_id: int = None
    departure_date: date = None
    departure_time: time = None
    route_description: str = ""
    total_capacity: int = 0
    available_capacity: int = 0
    total_weight_capacity: Decimal = Decimal('0.00')
    available_weight: Decimal = Decimal('0.00')
    total_volume_capacity: Decimal = Decimal('0.00')
    available_volume: Decimal = Decimal('0.00')
    status: str = "scheduled"
    
    @classmethod
    def get_available_schedules(cls, from_date: date = None) -> List['TrainSchedule']:
        """Get available train schedules"""
        try:
            if not from_date:
                from_date = date.today()
                
            schedules_data = execute_query(
                """
                SELECT ts.*, t.train_name
                FROM train_schedule ts
                INNER JOIN train t ON ts.train_id = t.train_id
                WHERE ts.departure_date >= %s 
                AND ts.status = 'scheduled'
                AND ts.available_capacity > 0
                ORDER BY ts.departure_date, ts.departure_time
                """,
                (from_date,)
            )
            return [cls.from_dict(schedule) for schedule in schedules_data]
            
        except Exception as e:
            logger.error(f"Available schedules retrieval error: {e}")
            return []
    
    def assign_order(self, order_id: int) -> bool:
        """Assign order to train schedule"""
        try:
            call_procedure('sp_assign_order_to_train', (order_id, self.train_session_id))
            return True
            
        except Exception as e:
            logger.error(f"Order assignment error: {e}")
            return False

@dataclass
class Truck(BaseModel):
    """Truck model"""
    truck_id: int = None
    store_name: str = ""
    license_plate: str = ""
    truck_model: str = ""
    capacity: int = 0
    max_weight: Decimal = Decimal('0.00')
    max_volume: Decimal = Decimal('0.00')
    fuel_type: str = "diesel"
    fuel_efficiency: Decimal = Decimal('8.0')
    operational_cost_per_km: Decimal = Decimal('2.50')
    status: str = "active"
    mileage: int = 0
    
    @classmethod
    def get_by_store(cls, store_name: str) -> List['Truck']:
        """Get trucks for a store"""
        try:
            trucks_data = execute_query(
                "SELECT * FROM truck WHERE store_name = %s AND status = 'active' ORDER BY license_plate",
                (store_name,)
            )
            return [cls.from_dict(truck) for truck in trucks_data]
            
        except Exception as e:
            logger.error(f"Store trucks retrieval error: {e}")
            return []

@dataclass
class Driver(BaseModel):
    """Driver model"""
    driver_id: int = None
    store_name: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    license_number: str = ""
    license_class: str = ""
    license_expiry: date = None
    hire_date: date = None
    hourly_rate: Decimal = Decimal('15.00')
    weekly_hours: Decimal = Decimal('0.00')
    max_weekly_hours: Decimal = Decimal('40.00')
    total_deliveries: int = 0
    rating: Decimal = Decimal('5.00')
    is_active: bool = True
    
    @classmethod
    def get_available_drivers(cls, store_name: str) -> List['Driver']:
        """Get available drivers for a store"""
        try:
            drivers_data = execute_query(
                """
                SELECT * FROM driver 
                WHERE store_name = %s 
                AND is_active = TRUE 
                AND weekly_hours < max_weekly_hours
                ORDER BY first_name, last_name
                """,
                (store_name,)
            )
            return [cls.from_dict(driver) for driver in drivers_data]
            
        except Exception as e:
            logger.error(f"Available drivers retrieval error: {e}")
            return []
    
    def get_full_name(self) -> str:
        """Get driver's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def can_work_hours(self, additional_hours: float) -> bool:
        """Check if driver can work additional hours"""
        return (self.weekly_hours + Decimal(str(additional_hours))) <= self.max_weekly_hours

# =============================================
# REPORTING MODELS
# =============================================

class ReportGenerator:
    """Report generation utilities"""
    
    @staticmethod
    def generate_sales_report(start_date: date, end_date: date, store_name: str = None) -> Dict[str, List]:
        """Generate sales report"""
        try:
            results = call_procedure('sp_generate_sales_report', (start_date, end_date, store_name))
            
            # Parse multiple result sets
            daily_sales = []
            top_products = []
            
            # First result set: daily sales
            for result in results[:len(results)//2]:
                daily_sales.append(result)
            
            # Second result set: top products
            for result in results[len(results)//2:]:
                top_products.append(result)
            
            return {
                'daily_sales': daily_sales,
                'top_products': top_products
            }
            
        except Exception as e:
            logger.error(f"Sales report generation error: {e}")
            return {'daily_sales': [], 'top_products': []}
    
    @staticmethod
    def generate_inventory_report(store_name: str = None) -> Dict[str, List]:
        """Generate inventory report"""
        try:
            results = call_procedure('sp_generate_inventory_report', (store_name,))
            return {'inventory_details': results}
            
        except Exception as e:
            logger.error(f"Inventory report generation error: {e}")
            return {'inventory_details': []}
    
    @staticmethod
    def generate_transport_report(start_date: date, end_date: date) -> Dict[str, List]:
        """Generate transportation report"""
        try:
            results = call_procedure('sp_generate_transport_report', (start_date, end_date))
            return {'transport_performance': results}
            
        except Exception as e:
            logger.error(f"Transport report generation error: {e}")
            return {'transport_performance': []}

# =============================================
# UTILITY FUNCTIONS
# =============================================

def get_order_summary_view(limit: int = 100) -> List[Dict[str, Any]]:
    """Get order summary from view"""
    try:
        return execute_query(
            "SELECT * FROM vw_order_summary ORDER BY order_date DESC LIMIT %s",
            (limit,)
        )
    except Exception as e:
        logger.error(f"Order summary view error: {e}")
        return []

def get_inventory_status_view(store_name: str = None) -> List[Dict[str, Any]]:
    """Get inventory status from view"""
    try:
        if store_name:
            return execute_query(
                "SELECT * FROM vw_inventory_status WHERE store_name = %s ORDER BY item_name",
                (store_name,)
            )
        else:
            return execute_query(
                "SELECT * FROM vw_inventory_status ORDER BY store_name, item_name"
            )
    except Exception as e:
        logger.error(f"Inventory status view error: {e}")
        return []

def get_transport_utilization_view() -> List[Dict[str, Any]]:
    """Get transport utilization from view"""
    try:
        return execute_query(
            "SELECT * FROM vw_transport_utilization ORDER BY departure_date DESC, utilization_percentage DESC"
        )
    except Exception as e:
        logger.error(f"Transport utilization view error: {e}")
        return []

def calculate_shipping_cost(route_id: int, weight: float, volume: float) -> Decimal:
    """Calculate shipping cost using database function"""
    try:
        result = call_function('fn_calculate_shipping_cost', (route_id, weight, volume))
        return Decimal(str(result)) if result else Decimal('10.00')
    except Exception as e:
        logger.error(f"Shipping cost calculation error: {e}")
        return Decimal('10.00')

def validate_status_transition(current_status: str, new_status: str) -> bool:
    """Validate order status transition using database function"""
    try:
        result = call_function('fn_validate_status_transition', (current_status, new_status))
        return bool(result) if result is not None else False
    except Exception as e:
        logger.error(f"Status transition validation error: {e}")
        return False