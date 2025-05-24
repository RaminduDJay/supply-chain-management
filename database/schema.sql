-- =============================================
-- Supply Chain Management System - Database Schema
-- =============================================

-- Drop database if exists and create new one
DROP DATABASE IF EXISTS supply_chain_db;
CREATE DATABASE supply_chain_db;
USE supply_chain_db;

-- =============================================
-- 1. USER MANAGEMENT TABLES
-- =============================================

-- Users table (base authentication)
CREATE TABLE users (
    user_name VARCHAR(50) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    role ENUM('customer', 'store_manager', 'main_manager') NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_role (role)
);

-- Customer types for discount management
CREATE TABLE customer_type (
    customer_type VARCHAR(20) PRIMARY KEY,
    discount_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    min_order_qty INT NOT NULL DEFAULT 1,
    description TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Customer details
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(50) UNIQUE NOT NULL,
    customer_type VARCHAR(20) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(50),
    postal_code VARCHAR(10),
    credit_limit DECIMAL(12,2) DEFAULT 10000.00,
    current_balance DECIMAL(12,2) DEFAULT 0.00,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_name) REFERENCES users(user_name) ON DELETE CASCADE,
    FOREIGN KEY (customer_type) REFERENCES customer_type(customer_type),
    INDEX idx_customer_type (customer_type),
    INDEX idx_email (email)
);

-- Store locations
CREATE TABLE store (
    store_name VARCHAR(50) PRIMARY KEY,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50),
    postal_code VARCHAR(10),
    phone VARCHAR(20),
    email VARCHAR(100),
    capacity INT NOT NULL DEFAULT 1000,
    current_inventory_count INT DEFAULT 0,
    manager_count INT DEFAULT 0,
    operating_hours VARCHAR(100) DEFAULT '08:00-18:00',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_city (city)
);

-- Store managers
CREATE TABLE store_manager (
    manager_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(50) UNIQUE NOT NULL,
    store_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    hire_date DATE NOT NULL,
    salary DECIMAL(10,2),
    department VARCHAR(50) DEFAULT 'Operations',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_name) REFERENCES users(user_name) ON DELETE CASCADE,
    FOREIGN KEY (store_name) REFERENCES store(store_name),
    INDEX idx_store (store_name)
);

-- Main managers (headquarters)
CREATE TABLE main_manager (
    manager_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    department VARCHAR(50) NOT NULL,
    hire_date DATE NOT NULL,
    salary DECIMAL(10,2),
    authority_level ENUM('senior', 'executive', 'director') DEFAULT 'senior',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_name) REFERENCES users(user_name) ON DELETE CASCADE,
    INDEX idx_department (department)
);

-- =============================================
-- 2. PRODUCT & INVENTORY TABLES
-- =============================================

-- Product catalog
CREATE TABLE items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    subcategory VARCHAR(50),
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    weight DECIMAL(8,2) NOT NULL COMMENT 'Weight in kg',
    volume DECIMAL(8,2) NOT NULL COMMENT 'Volume in cubic meters',
    fragile BOOLEAN DEFAULT FALSE,
    hazardous BOOLEAN DEFAULT FALSE,
    stock_threshold INT DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_name (item_name),
    INDEX idx_price (price)
);

-- Store inventory tracking
CREATE TABLE inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    store_name VARCHAR(50) NOT NULL,
    item_id INT NOT NULL,
    quantity_available INT NOT NULL DEFAULT 0,
    quantity_reserved INT NOT NULL DEFAULT 0,
    reorder_point INT DEFAULT 10,
    max_stock_level INT DEFAULT 1000,
    last_restocked DATETIME,
    cost_per_unit DECIMAL(10,2),
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (store_name) REFERENCES store(store_name),
    FOREIGN KEY (item_id) REFERENCES items(item_id),
    UNIQUE KEY unique_store_item (store_name, item_id),
    INDEX idx_quantity (quantity_available),
    INDEX idx_store_item (store_name, item_id)
);

-- Shopping cart
CREATE TABLE cart (
    cart_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(item_id),
    UNIQUE KEY unique_customer_item (customer_id, item_id),
    INDEX idx_customer (customer_id),
    INDEX idx_item (item_id)
);

-- =============================================
-- 3. LOCATION & ROUTING TABLES
-- =============================================

-- Delivery routes
CREATE TABLE route (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    store_name VARCHAR(50) NOT NULL,
    route_name VARCHAR(100) NOT NULL,
    destination_address VARCHAR(255) NOT NULL,
    destination_city VARCHAR(50) NOT NULL,
    destination_state VARCHAR(50),
    distance DECIMAL(8,2) NOT NULL COMMENT 'Distance in kilometers',
    estimated_time TIME NOT NULL COMMENT 'Estimated travel time',
    base_cost DECIMAL(10,2) NOT NULL,
    route_type ENUM('local', 'regional', 'express') DEFAULT 'local',
    is_active BOOLEAN DEFAULT TRUE,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_name) REFERENCES store(store_name),
    INDEX idx_store (store_name),
    INDEX idx_destination (destination_city),
    INDEX idx_distance (distance)
);

-- =============================================
-- 4. TRANSPORTATION TABLES
-- =============================================

-- Train fleet
CREATE TABLE train (
    train_id INT AUTO_INCREMENT PRIMARY KEY,
    train_name VARCHAR(50) NOT NULL,
    train_type ENUM('freight', 'express', 'standard') DEFAULT 'standard',
    capacity INT NOT NULL COMMENT 'Maximum items capacity',
    max_weight DECIMAL(10,2) NOT NULL COMMENT 'Maximum weight in tons',
    max_volume DECIMAL(10,2) NOT NULL COMMENT 'Maximum volume in cubic meters',
    operational_cost_per_km DECIMAL(8,2) DEFAULT 5.00,
    status ENUM('active', 'maintenance', 'retired') DEFAULT 'active',
    purchase_date DATE,
    last_maintenance DATE,
    next_maintenance DATE,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_capacity (capacity)
);

-- Train scheduling
CREATE TABLE train_schedule (
    train_session_id INT AUTO_INCREMENT PRIMARY KEY,
    train_id INT NOT NULL,
    departure_date DATE NOT NULL,
    departure_time TIME NOT NULL,
    estimated_arrival_time TIME,
    route_description VARCHAR(255),
    total_capacity INT NOT NULL,
    available_capacity INT NOT NULL,
    total_weight_capacity DECIMAL(10,2) NOT NULL,
    available_weight DECIMAL(10,2) NOT NULL,
    total_volume_capacity DECIMAL(10,2) NOT NULL,
    available_volume DECIMAL(10,2) NOT NULL,
    status ENUM('scheduled', 'in_progress', 'completed', 'cancelled') DEFAULT 'scheduled',
    actual_departure_time DATETIME,
    actual_arrival_time DATETIME,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (train_id) REFERENCES train(train_id),
    INDEX idx_departure_date (departure_date),
    INDEX idx_status (status),
    INDEX idx_available_capacity (available_capacity)
);

-- Train arrival stations (weak entity)
CREATE TABLE arrival_station (
    arrival_id INT AUTO_INCREMENT PRIMARY KEY,
    train_session_id INT NOT NULL,
    station_name VARCHAR(50) NOT NULL,
    arrival_time TIME NOT NULL,
    departure_time TIME,
    platform_number VARCHAR(10),
    station_city VARCHAR(50),
    is_final_destination BOOLEAN DEFAULT FALSE,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (train_session_id) REFERENCES train_schedule(train_session_id) ON DELETE CASCADE,
    UNIQUE KEY unique_session_station (train_session_id, station_name),
    INDEX idx_session (train_session_id),
    INDEX idx_station (station_name)
);

-- Truck fleet
CREATE TABLE truck (
    truck_id INT AUTO_INCREMENT PRIMARY KEY,
    store_name VARCHAR(50) NOT NULL,
    license_plate VARCHAR(20) UNIQUE NOT NULL,
    truck_model VARCHAR(50),
    capacity INT NOT NULL COMMENT 'Maximum items capacity',
    max_weight DECIMAL(8,2) NOT NULL COMMENT 'Maximum weight in kg',
    max_volume DECIMAL(8,2) NOT NULL COMMENT 'Maximum volume in cubic meters',
    fuel_type ENUM('diesel', 'petrol', 'electric', 'hybrid') DEFAULT 'diesel',
    fuel_efficiency DECIMAL(5,2) COMMENT 'km per liter',
    operational_cost_per_km DECIMAL(6,2) DEFAULT 2.50,
    status ENUM('active', 'maintenance', 'retired') DEFAULT 'active',
    purchase_date DATE,
    last_maintenance DATE,
    next_maintenance DATE,
    mileage INT DEFAULT 0,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_name) REFERENCES store(store_name),
    INDEX idx_store (store_name),
    INDEX idx_status (status),
    INDEX idx_license (license_plate)
);

-- =============================================
-- 5. HUMAN RESOURCES TABLES
-- =============================================

-- Drivers
CREATE TABLE driver (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    store_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    license_number VARCHAR(50) UNIQUE NOT NULL,
    license_class VARCHAR(10) NOT NULL,
    license_expiry DATE NOT NULL,
    hire_date DATE NOT NULL,
    hourly_rate DECIMAL(6,2) DEFAULT 15.00,
    weekly_hours DECIMAL(5,2) DEFAULT 0.00,
    max_weekly_hours DECIMAL(5,2) DEFAULT 40.00,
    total_deliveries INT DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 5.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_name) REFERENCES store(store_name),
    INDEX idx_store (store_name),
    INDEX idx_license (license_number),
    INDEX idx_active (is_active)
);

-- Driver assistants
CREATE TABLE driver_assistant (
    driver_assistant_id INT AUTO_INCREMENT PRIMARY KEY,
    store_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    hire_date DATE NOT NULL,
    hourly_rate DECIMAL(6,2) DEFAULT 12.00,
    weekly_hours DECIMAL(5,2) DEFAULT 0.00,
    max_weekly_hours DECIMAL(5,2) DEFAULT 60.00,
    certification VARCHAR(100),
    total_assists INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_name) REFERENCES store(store_name),
    INDEX idx_store (store_name),
    INDEX idx_active (is_active)
);

-- Truck scheduling
CREATE TABLE truck_schedule (
    truck_session_id INT AUTO_INCREMENT PRIMARY KEY,
    truck_id INT NOT NULL,
    driver_id INT NOT NULL,
    driver_assistant_id INT,
    route_id INT NOT NULL,
    scheduled_date DATE NOT NULL,
    start_time TIME NOT NULL,
    estimated_end_time TIME NOT NULL,
    actual_start_time DATETIME,
    actual_end_time DATETIME,
    total_capacity INT NOT NULL,
    available_capacity INT NOT NULL,
    total_weight_capacity DECIMAL(8,2) NOT NULL,
    available_weight DECIMAL(8,2) NOT NULL,
    fuel_cost DECIMAL(8,2) DEFAULT 0.00,
    toll_cost DECIMAL(8,2) DEFAULT 0.00,
    maintenance_cost DECIMAL(8,2) DEFAULT 0.00,
    status ENUM('scheduled', 'in_progress', 'completed', 'cancelled') DEFAULT 'scheduled',
    notes TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (truck_id) REFERENCES truck(truck_id),
    FOREIGN KEY (driver_id) REFERENCES driver(driver_id),
    FOREIGN KEY (driver_assistant_id) REFERENCES driver_assistant(driver_assistant_id),
    FOREIGN KEY (route_id) REFERENCES route(route_id),
    INDEX idx_truck (truck_id),
    INDEX idx_driver (driver_id),
    INDEX idx_date (scheduled_date),
    INDEX idx_status (status)
);

-- =============================================
-- 6. ORDER MANAGEMENT TABLES
-- =============================================

-- Main orders table
CREATE TABLE order_table (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    route_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    delivery_date DATE NOT NULL,
    requested_delivery_time TIME,
    status ENUM('pending', 'confirmed', 'assigned_train', 'in_transit_rail', 'at_warehouse', 'assigned_truck', 'out_for_delivery', 'delivered', 'cancelled', 'returned') DEFAULT 'pending',
    total_items INT NOT NULL DEFAULT 0,
    total_weight DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_volume DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    shipping_cost DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending',
    special_instructions TEXT,
    priority ENUM('standard', 'high', 'urgent') DEFAULT 'standard',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (route_id) REFERENCES route(route_id),
    INDEX idx_customer (customer_id),
    INDEX idx_status (status),
    INDEX idx_delivery_date (delivery_date),
    INDEX idx_order_date (order_date)
);

-- Order items detail
CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    discount_rate DECIMAL(5,2) DEFAULT 0.00,
    line_total DECIMAL(12,2) NOT NULL,
    weight_per_unit DECIMAL(8,2) NOT NULL,
    volume_per_unit DECIMAL(8,2) NOT NULL,
    total_weight DECIMAL(10,2) NOT NULL,
    total_volume DECIMAL(10,2) NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES order_table(order_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(item_id),
    UNIQUE KEY unique_order_item (order_id, item_id),
    INDEX idx_order (order_id),
    INDEX idx_item (item_id)
);

-- =============================================
-- 7. ASSIGNMENT/JUNCTION TABLES
-- =============================================

-- Order to train assignment
CREATE TABLE order_train_schedule (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    train_session_id INT NOT NULL,
    assigned_weight DECIMAL(10,2) NOT NULL,
    assigned_volume DECIMAL(10,2) NOT NULL,
    assigned_items INT NOT NULL,
    loading_status ENUM('pending', 'loading', 'loaded', 'in_transit', 'unloading', 'unloaded') DEFAULT 'pending',
    loading_time DATETIME,
    unloading_time DATETIME,
    assignment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (order_id) REFERENCES order_table(order_id) ON DELETE CASCADE,
    FOREIGN KEY (train_session_id) REFERENCES train_schedule(train_session_id),
    UNIQUE KEY unique_order_train (order_id, train_session_id),
    INDEX idx_order (order_id),
    INDEX idx_train_session (train_session_id),
    INDEX idx_status (loading_status)
);

-- Order to truck assignment
CREATE TABLE order_truck_schedule (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    truck_session_id INT NOT NULL,
    assigned_weight DECIMAL(10,2) NOT NULL,
    assigned_volume DECIMAL(10,2) NOT NULL,
    assigned_items INT NOT NULL,
    pickup_time DATETIME,
    delivery_time DATETIME,
    delivery_status ENUM('pending', 'picked_up', 'out_for_delivery', 'delivered', 'failed_delivery', 'returned') DEFAULT 'pending',
    delivery_attempts INT DEFAULT 0,
    recipient_name VARCHAR(100),
    delivery_notes TEXT,
    assignment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES order_table(order_id) ON DELETE CASCADE,
    FOREIGN KEY (truck_session_id) REFERENCES truck_schedule(truck_session_id),
    UNIQUE KEY unique_order_truck (order_id, truck_session_id),
    INDEX idx_order (order_id),
    INDEX idx_truck_session (truck_session_id),
    INDEX idx_delivery_status (delivery_status)
);

-- =============================================
-- 8. AUDIT AND LOGGING TABLES
-- =============================================

-- System audit log
CREATE TABLE audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    record_id VARCHAR(50) NOT NULL,
    old_values JSON,
    new_values JSON,
    user_name VARCHAR(50),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    INDEX idx_table (table_name),
    INDEX idx_user (user_name),
    INDEX idx_timestamp (timestamp)
);

-- Performance metrics
CREATE TABLE performance_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(20),
    category VARCHAR(50),
    recorded_date DATE NOT NULL,
    recorded_time TIME NOT NULL,
    additional_data JSON,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name_date (metric_name, recorded_date),
    INDEX idx_category (category)
);

-- =============================================
-- INDEXES FOR OPTIMIZATION
-- =============================================

-- Additional composite indexes for common queries
CREATE INDEX idx_order_customer_status ON order_table(customer_id, status);
CREATE INDEX idx_order_delivery_date_status ON order_table(delivery_date, status);
CREATE INDEX idx_train_schedule_date_capacity ON train_schedule(departure_date, available_capacity);
CREATE INDEX idx_truck_schedule_date_status ON truck_schedule(scheduled_date, status);
CREATE INDEX idx_inventory_store_quantity ON inventory(store_name, quantity_available);
CREATE INDEX idx_driver_store_active ON driver(store_name, is_active);
CREATE INDEX idx_customer_type_email ON customers(customer_type, email);

-- =============================================
-- END OF SCHEMA CREATION
-- =============================================

-- Set proper SQL modes and configurations
SET SQL_MODE = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- Enable event scheduler for automated tasks
SET GLOBAL event_scheduler = ON;

COMMIT;

-- Display creation summary
SELECT 'Database schema created successfully!' as Status,
       COUNT(*) as Total_Tables 
FROM information_schema.tables 
WHERE table_schema = 'supply_chain_db';