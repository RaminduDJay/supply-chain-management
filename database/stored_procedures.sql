-- =============================================
-- Supply Chain Management System - Stored Procedures
-- =============================================

USE supply_chain_db;

DELIMITER //

-- =============================================
-- 1. USER MANAGEMENT PROCEDURES
-- =============================================

-- Create new customer account
CREATE PROCEDURE sp_create_customer(
    IN p_user_name VARCHAR(50),
    IN p_password VARCHAR(255),
    IN p_customer_type VARCHAR(20),
    IN p_first_name VARCHAR(50),
    IN p_last_name VARCHAR(50),
    IN p_email VARCHAR(100),
    IN p_phone VARCHAR(20),
    IN p_address TEXT,
    IN p_city VARCHAR(50),
    IN p_postal_code VARCHAR(10)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Insert into users table
    INSERT INTO users (user_name, password, role) 
    VALUES (p_user_name, p_password, 'customer');
    
    -- Insert into customers table
    INSERT INTO customers (user_name, customer_type, first_name, last_name, email, phone, address, city, postal_code)
    VALUES (p_user_name, p_customer_type, p_first_name, p_last_name, p_email, p_phone, p_address, p_city, p_postal_code);
    
    COMMIT;
    
    SELECT 'Customer created successfully' as message, LAST_INSERT_ID() as customer_id;
END //

-- Authenticate user login
CREATE PROCEDURE sp_authenticate_user(
    IN p_user_name VARCHAR(50),
    IN p_password VARCHAR(255)
)
BEGIN
    DECLARE v_stored_password VARCHAR(255);
    DECLARE v_role VARCHAR(20);
    DECLARE v_is_active BOOLEAN;
    
    SELECT password, role, is_active 
    INTO v_stored_password, v_role, v_is_active
    FROM users 
    WHERE user_name = p_user_name;
    
    IF v_stored_password IS NULL THEN
        SELECT 'User not found' as status, NULL as role, NULL as user_name;
    ELSEIF NOT v_is_active THEN
        SELECT 'Account inactive' as status, NULL as role, NULL as user_name;
    ELSEIF v_stored_password = p_password THEN
        -- Update last login
        UPDATE users SET last_login = NOW() WHERE user_name = p_user_name;
        SELECT 'Success' as status, v_role as role, p_user_name as user_name;
    ELSE
        SELECT 'Invalid password' as status, NULL as role, NULL as user_name;
    END IF;
END //

-- =============================================
-- 2. PRODUCT & INVENTORY PROCEDURES
-- =============================================

-- Add item to cart
CREATE PROCEDURE sp_add_to_cart(
    IN p_customer_id INT,
    IN p_item_id INT,
    IN p_quantity INT
)
BEGIN
    DECLARE v_existing_qty INT DEFAULT 0;
    DECLARE v_item_exists INT DEFAULT 0;
    
    -- Check if item exists
    SELECT COUNT(*) INTO v_item_exists FROM items WHERE item_id = p_item_id AND is_active = TRUE;
    
    IF v_item_exists = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Item not found or inactive';
    END IF;
    
    -- Check if item already in cart
    SELECT quantity INTO v_existing_qty 
    FROM cart 
    WHERE customer_id = p_customer_id AND item_id = p_item_id;
    
    IF v_existing_qty > 0 THEN
        -- Update existing cart item
        UPDATE cart 
        SET quantity = quantity + p_quantity, updated_date = NOW()
        WHERE customer_id = p_customer_id AND item_id = p_item_id;
    ELSE
        -- Insert new cart item
        INSERT INTO cart (customer_id, item_id, quantity)
        VALUES (p_customer_id, p_item_id, p_quantity);
    END IF;
    
    SELECT 'Item added to cart successfully' as message;
END //

-- Get cart contents with totals
CREATE PROCEDURE sp_get_cart_summary(
    IN p_customer_id INT
)
BEGIN
    SELECT 
        c.cart_id,
        c.item_id,
        i.item_name,
        i.price,
        c.quantity,
        (i.price * c.quantity) as line_total,
        (i.weight * c.quantity) as total_weight,
        (i.volume * c.quantity) as total_volume,
        c.added_date
    FROM cart c
    INNER JOIN items i ON c.item_id = i.item_id
    WHERE c.customer_id = p_customer_id
    ORDER BY c.added_date DESC;
    
    -- Get cart totals
    SELECT 
        COUNT(*) as total_items,
        SUM(c.quantity) as total_quantity,
        SUM(i.price * c.quantity) as subtotal,
        SUM(i.weight * c.quantity) as total_weight,
        SUM(i.volume * c.quantity) as total_volume
    FROM cart c
    INNER JOIN items i ON c.item_id = i.item_id
    WHERE c.customer_id = p_customer_id;
END //

-- Update inventory levels
CREATE PROCEDURE sp_update_inventory(
    IN p_store_name VARCHAR(50),
    IN p_item_id INT,
    IN p_quantity_change INT,
    IN p_operation VARCHAR(10) -- 'ADD' or 'SUBTRACT' or 'RESERVE' or 'RELEASE'
)
BEGIN
    DECLARE v_current_available INT DEFAULT 0;
    DECLARE v_current_reserved INT DEFAULT 0;
    
    -- Get current quantities
    SELECT quantity_available, quantity_reserved
    INTO v_current_available, v_current_reserved
    FROM inventory
    WHERE store_name = p_store_name AND item_id = p_item_id;
    
    -- Handle different operations
    CASE p_operation
        WHEN 'ADD' THEN
            UPDATE inventory 
            SET quantity_available = quantity_available + p_quantity_change,
                updated_date = NOW()
            WHERE store_name = p_store_name AND item_id = p_item_id;
            
        WHEN 'SUBTRACT' THEN
            IF v_current_available < p_quantity_change THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient inventory';
            END IF;
            
            UPDATE inventory 
            SET quantity_available = quantity_available - p_quantity_change,
                updated_date = NOW()
            WHERE store_name = p_store_name AND item_id = p_item_id;
            
        WHEN 'RESERVE' THEN
            IF v_current_available < p_quantity_change THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient inventory to reserve';
            END IF;
            
            UPDATE inventory 
            SET quantity_available = quantity_available - p_quantity_change,
                quantity_reserved = quantity_reserved + p_quantity_change,
                updated_date = NOW()
            WHERE store_name = p_store_name AND item_id = p_item_id;
            
        WHEN 'RELEASE' THEN
            UPDATE inventory 
            SET quantity_available = quantity_available + p_quantity_change,
                quantity_reserved = quantity_reserved - p_quantity_change,
                updated_date = NOW()
            WHERE store_name = p_store_name AND item_id = p_item_id;
            
        ELSE
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid operation type';
    END CASE;
    
    SELECT 'Inventory updated successfully' as message;
END //

-- =============================================
-- 3. ORDER MANAGEMENT PROCEDURES
-- =============================================

-- Create order from cart
CREATE PROCEDURE sp_create_order_from_cart(
    IN p_customer_id INT,
    IN p_route_id INT,
    IN p_delivery_date DATE,
    IN p_special_instructions TEXT
)
BEGIN
    DECLARE v_order_id INT;
    DECLARE v_subtotal DECIMAL(12,2) DEFAULT 0;
    DECLARE v_discount_rate DECIMAL(5,2) DEFAULT 0;
    DECLARE v_discount_amount DECIMAL(10,2) DEFAULT 0;
    DECLARE v_total_weight DECIMAL(10,2) DEFAULT 0;
    DECLARE v_total_volume DECIMAL(10,2) DEFAULT 0;
    DECLARE v_total_items INT DEFAULT 0;
    DECLARE v_shipping_cost DECIMAL(10,2) DEFAULT 0;
    DECLARE v_total_amount DECIMAL(12,2) DEFAULT 0;
    DECLARE v_cart_count INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    -- Check if cart has items
    SELECT COUNT(*) INTO v_cart_count FROM cart WHERE customer_id = p_customer_id;
    
    IF v_cart_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cart is empty';
    END IF;
    
    -- Check delivery date (minimum 7 days from now)
    IF p_delivery_date < DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Minimum 7 days required for delivery';
    END IF;
    
    START TRANSACTION;
    
    -- Get customer discount rate
    SELECT ct.discount_rate INTO v_discount_rate
    FROM customers c
    INNER JOIN customer_type ct ON c.customer_type = ct.customer_type
    WHERE c.customer_id = p_customer_id;
    
    -- Calculate cart totals
    SELECT 
        SUM(c.quantity * i.price),
        SUM(c.quantity * i.weight),
        SUM(c.quantity * i.volume),
        SUM(c.quantity)
    INTO v_subtotal, v_total_weight, v_total_volume, v_total_items
    FROM cart c
    INNER JOIN items i ON c.item_id = i.item_id
    WHERE c.customer_id = p_customer_id;
    
    -- Calculate discount and shipping
    SET v_discount_amount = v_subtotal * (v_discount_rate / 100);
    SET v_shipping_cost = fn_calculate_shipping_cost(p_route_id, v_total_weight, v_total_volume);
    SET v_total_amount = v_subtotal - v_discount_amount + v_shipping_cost;
    
    -- Create order
    INSERT INTO order_table (
        customer_id, route_id, delivery_date, total_items, total_weight, total_volume,
        subtotal, discount_amount, shipping_cost, total_amount, special_instructions
    ) VALUES (
        p_customer_id, p_route_id, p_delivery_date, v_total_items, v_total_weight, v_total_volume,
        v_subtotal, v_discount_amount, v_shipping_cost, v_total_amount, p_special_instructions
    );
    
    SET v_order_id = LAST_INSERT_ID();
    
    -- Insert order items from cart
    INSERT INTO order_items (order_id, item_id, quantity, unit_price, discount_rate, line_total, weight_per_unit, volume_per_unit, total_weight, total_volume)
    SELECT 
        v_order_id,
        c.item_id,
        c.quantity,
        i.price,
        v_discount_rate,
        (c.quantity * i.price * (1 - v_discount_rate/100)),
        i.weight,
        i.volume,
        (c.quantity * i.weight),
        (c.quantity * i.volume)
    FROM cart c
    INNER JOIN items i ON c.item_id = i.item_id
    WHERE c.customer_id = p_customer_id;
    
    -- Clear cart
    DELETE FROM cart WHERE customer_id = p_customer_id;
    
    COMMIT;
    
    SELECT 'Order created successfully' as message, v_order_id as order_id, v_total_amount as total_amount;
END //

-- Update order status
CREATE PROCEDURE sp_update_order_status(
    IN p_order_id INT,
    IN p_new_status VARCHAR(50),
    IN p_user_name VARCHAR(50)
)
BEGIN
    DECLARE v_current_status VARCHAR(50);
    DECLARE v_valid_transition BOOLEAN DEFAULT FALSE;
    
    -- Get current status
    SELECT status INTO v_current_status FROM order_table WHERE order_id = p_order_id;
    
    IF v_current_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Order not found';
    END IF;
    
    -- Validate status transition
    SET v_valid_transition = fn_validate_status_transition(v_current_status, p_new_status);
    
    IF NOT v_valid_transition THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid status transition';
    END IF;
    
    -- Update order status
    UPDATE order_table 
    SET status = p_new_status, updated_date = NOW()
    WHERE order_id = p_order_id;
    
    -- Log the change
    INSERT INTO audit_log (table_name, operation, record_id, old_values, new_values, user_name)
    VALUES ('order_table', 'UPDATE', p_order_id, 
            JSON_OBJECT('status', v_current_status),
            JSON_OBJECT('status', p_new_status),
            p_user_name);
    
    SELECT 'Order status updated successfully' as message;
END //

-- =============================================
-- 4. TRANSPORTATION PROCEDURES
-- =============================================

-- Schedule train transport
CREATE PROCEDURE sp_schedule_train(
    IN p_train_id INT,
    IN p_departure_date DATE,
    IN p_departure_time TIME,
    IN p_route_description VARCHAR(255)
)
BEGIN
    DECLARE v_train_capacity INT;
    DECLARE v_train_max_weight DECIMAL(10,2);
    DECLARE v_train_max_volume DECIMAL(10,2);
    DECLARE v_train_status VARCHAR(20);
    
    -- Get train details
    SELECT capacity, max_weight, max_volume, status
    INTO v_train_capacity, v_train_max_weight, v_train_max_volume, v_train_status
    FROM train
    WHERE train_id = p_train_id;
    
    IF v_train_status != 'active' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Train is not active';
    END IF;
    
    -- Insert train schedule
    INSERT INTO train_schedule (
        train_id, departure_date, departure_time, route_description,
        total_capacity, available_capacity, total_weight_capacity, available_weight,
        total_volume_capacity, available_volume
    ) VALUES (
        p_train_id, p_departure_date, p_departure_time, p_route_description,
        v_train_capacity, v_train_capacity, v_train_max_weight, v_train_max_weight,
        v_train_max_volume, v_train_max_volume
    );
    
    SELECT 'Train scheduled successfully' as message, LAST_INSERT_ID() as train_session_id;
END //

-- Assign order to train
CREATE PROCEDURE sp_assign_order_to_train(
    IN p_order_id INT,
    IN p_train_session_id INT
)
BEGIN
    DECLARE v_order_weight DECIMAL(10,2);
    DECLARE v_order_volume DECIMAL(10,2);
    DECLARE v_order_items INT;
    DECLARE v_available_capacity INT;
    DECLARE v_available_weight DECIMAL(10,2);
    DECLARE v_available_volume DECIMAL(10,2);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Get order details
    SELECT total_weight, total_volume, total_items
    INTO v_order_weight, v_order_volume, v_order_items
    FROM order_table
    WHERE order_id = p_order_id AND status = 'confirmed';
    
    IF v_order_weight IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Order not found or not confirmed';
    END IF;
    
    -- Get train availability
    SELECT available_capacity, available_weight, available_volume
    INTO v_available_capacity, v_available_weight, v_available_volume
    FROM train_schedule
    WHERE train_session_id = p_train_session_id AND status = 'scheduled';
    
    IF v_available_capacity IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Train session not found or not available';
    END IF;
    
    -- Check capacity constraints
    IF v_available_capacity < v_order_items THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient train capacity';
    END IF;
    
    IF v_available_weight < v_order_weight THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient train weight capacity';
    END IF;
    
    IF v_available_volume < v_order_volume THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient train volume capacity';
    END IF;
    
    -- Create assignment
    INSERT INTO order_train_schedule (order_id, train_session_id, assigned_weight, assigned_volume, assigned_items)
    VALUES (p_order_id, p_train_session_id, v_order_weight, v_order_volume, v_order_items);
    
    -- Update train availability
    UPDATE train_schedule
    SET available_capacity = available_capacity - v_order_items,
        available_weight = available_weight - v_order_weight,
        available_volume = available_volume - v_order_volume
    WHERE train_session_id = p_train_session_id;
    
    -- Update order status
    UPDATE order_table
    SET status = 'assigned_train'
    WHERE order_id = p_order_id;
    
    COMMIT;
    
    SELECT 'Order assigned to train successfully' as message;
END //

-- Schedule truck delivery
CREATE PROCEDURE sp_schedule_truck(
    IN p_truck_id INT,
    IN p_driver_id INT,
    IN p_driver_assistant_id INT,
    IN p_route_id INT,
    IN p_scheduled_date DATE,
    IN p_start_time TIME
)
BEGIN
    DECLARE v_truck_capacity INT;
    DECLARE v_truck_max_weight DECIMAL(8,2);
    DECLARE v_truck_max_volume DECIMAL(8,2);
    DECLARE v_route_time TIME;
    DECLARE v_driver_hours DECIMAL(5,2);
    DECLARE v_assistant_hours DECIMAL(5,2);
    
    -- Get truck details
    SELECT capacity, max_weight, max_volume
    INTO v_truck_capacity, v_truck_max_weight, v_truck_max_volume
    FROM truck
    WHERE truck_id = p_truck_id AND status = 'active';
    
    IF v_truck_capacity IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Truck not found or inactive';
    END IF;
    
    -- Get route estimated time
    SELECT estimated_time INTO v_route_time FROM route WHERE route_id = p_route_id;
    
    -- Check driver working hours
    SELECT weekly_hours INTO v_driver_hours FROM driver WHERE driver_id = p_driver_id;
    IF v_driver_hours >= 40 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Driver has reached weekly hour limit';
    END IF;
    
    -- Check assistant working hours (if provided)
    IF p_driver_assistant_id IS NOT NULL THEN
        SELECT weekly_hours INTO v_assistant_hours FROM driver_assistant WHERE driver_assistant_id = p_driver_assistant_id;
        IF v_assistant_hours >= 60 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Driver assistant has reached weekly hour limit';
        END IF;
    END IF;
    
    -- Insert truck schedule
    INSERT INTO truck_schedule (
        truck_id, driver_id, driver_assistant_id, route_id, scheduled_date, start_time,
        estimated_end_time, total_capacity, available_capacity, total_weight_capacity, available_weight
    ) VALUES (
        p_truck_id, p_driver_id, p_driver_assistant_id, p_route_id, p_scheduled_date, p_start_time,
        ADDTIME(p_start_time, v_route_time), v_truck_capacity, v_truck_capacity, v_truck_max_weight, v_truck_max_weight
    );
    
    SELECT 'Truck scheduled successfully' as message, LAST_INSERT_ID() as truck_session_id;
END //

-- =============================================
-- 5. REPORTING PROCEDURES
-- =============================================

-- Generate sales report
CREATE PROCEDURE sp_generate_sales_report(
    IN p_start_date DATE,
    IN p_end_date DATE,
    IN p_store_name VARCHAR(50)
)
BEGIN
    -- Daily sales summary
    SELECT 
        DATE(o.order_date) as order_date,
        COUNT(o.order_id) as total_orders,
        SUM(o.total_amount) as total_revenue,
        AVG(o.total_amount) as avg_order_value,
        SUM(o.total_items) as total_items_sold
    FROM order_table o
    INNER JOIN route r ON o.route_id = r.route_id
    WHERE DATE(o.order_date) BETWEEN p_start_date AND p_end_date
    AND (p_store_name IS NULL OR r.store_name = p_store_name)
    AND o.status NOT IN ('cancelled', 'returned')
    GROUP BY DATE(o.order_date)
    ORDER BY order_date;
    
    -- Top selling products
    SELECT 
        i.item_name,
        SUM(oi.quantity) as total_quantity_sold,
        SUM(oi.line_total) as total_revenue,
        COUNT(DISTINCT oi.order_id) as orders_count
    FROM order_items oi
    INNER JOIN items i ON oi.item_id = i.item_id
    INNER JOIN order_table o ON oi.order_id = o.order_id
    INNER JOIN route r ON o.route_id = r.route_id
    WHERE DATE(o.order_date) BETWEEN p_start_date AND p_end_date
    AND (p_store_name IS NULL OR r.store_name = p_store_name)
    AND o.status NOT IN ('cancelled', 'returned')
    GROUP BY i.item_id, i.item_name
    ORDER BY total_revenue DESC
    LIMIT 10;
END //

-- Generate inventory report
CREATE PROCEDURE sp_generate_inventory_report(
    IN p_store_name VARCHAR(50)
)
BEGIN
    SELECT 
        s.store_name,
        i.item_name,
        i.category,
        inv.quantity_available,
        inv.quantity_reserved,
        (inv.quantity_available + inv.quantity_reserved) as total_quantity,
        inv.reorder_point,
        CASE 
            WHEN inv.quantity_available <= inv.reorder_point THEN 'Low Stock'
            WHEN inv.quantity_available = 0 THEN 'Out of Stock'
            ELSE 'Adequate'
        END as stock_status,
        inv.last_restocked,
        inv.cost_per_unit,
        (inv.quantity_available * inv.cost_per_unit) as inventory_value
    FROM inventory inv
    INNER JOIN store s ON inv.store_name = s.store_name
    INNER JOIN items i ON inv.item_id = i.item_id
    WHERE (p_store_name IS NULL OR inv.store_name = p_store_name)
    ORDER BY s.store_name, stock_status DESC, i.item_name;
    
    -- Summary by store
    SELECT 
        inv.store_name,
        COUNT(*) as total_items,
        SUM(inv.quantity_available) as total_available_items,
        SUM(inv.quantity_reserved) as total_reserved_items,
        SUM(inv.quantity_available * inv.cost_per_unit) as total_inventory_value,
        SUM(CASE WHEN inv.quantity_available <= inv.reorder_point THEN 1 ELSE 0 END) as low_stock_items
    FROM inventory inv
    WHERE (p_store_name IS NULL OR inv.store_name = p_store_name)
    GROUP BY inv.store_name
    ORDER BY inv.store_name;
END //

-- Generate transportation report
CREATE PROCEDURE sp_generate_transport_report(
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    -- Train utilization
    SELECT 
        t.train_name,
        COUNT(ts.train_session_id) as total_trips,
        AVG((ts.total_capacity - ts.available_capacity) / ts.total_capacity * 100) as avg_capacity_utilization,
        AVG((ts.total_weight_capacity - ts.available_weight) / ts.total_weight_capacity * 100) as avg_weight_utilization,
        SUM(ts.total_capacity - ts.available_capacity) as total_items_transported
    FROM train_schedule ts
    INNER JOIN train t ON ts.train_id = t.train_id
    WHERE ts.departure_date BETWEEN p_start_date AND p_end_date
    AND ts.status = 'completed'
    GROUP BY t.train_id, t.train_name
    ORDER BY avg_capacity_utilization DESC;
    
    -- Truck performance
    SELECT 
        tr.license_plate,
        CONCAT(d.first_name, ' ', d.last_name) as driver_name,
        COUNT(trs.truck_session_id) as total_deliveries,
        AVG((trs.total_capacity - trs.available_capacity) / trs.total_capacity * 100) as avg_utilization,
        SUM(trs.fuel_cost + trs.toll_cost + trs.maintenance_cost) as total_operating_cost
    FROM truck_schedule trs
    INNER JOIN truck tr ON trs.truck_id = tr.truck_id
    INNER JOIN driver d ON trs.driver_id = d.driver_id
    WHERE trs.scheduled_date BETWEEN p_start_date AND p_end_date
    AND trs.status = 'completed'
    GROUP BY tr.truck_id, tr.license_plate, d.driver_id, d.first_name, d.last_name
    ORDER BY total_deliveries DESC;
END //

-- =============================================
-- 6. MAINTENANCE PROCEDURES
-- =============================================

-- Update driver working hours
CREATE PROCEDURE sp_update_driver_hours(
    IN p_driver_id INT,
    IN p_hours_worked DECIMAL(5,2)
)
BEGIN
    DECLARE v_current_hours DECIMAL(5,2);
    DECLARE v_max_hours DECIMAL(5,2);
    
    SELECT weekly_hours, max_weekly_hours
    INTO v_current_hours, v_max_hours
    FROM driver
    WHERE driver_id = p_driver_id;
    
    IF (v_current_hours + p_hours_worked) > v_max_hours THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Would exceed maximum weekly hours';
    END IF;
    
    UPDATE driver
    SET weekly_hours = weekly_hours + p_hours_worked,
        total_deliveries = total_deliveries + 1
    WHERE driver_id = p_driver_id;
    
    SELECT 'Driver hours updated successfully' as message;
END //

-- Reset weekly hours (to be called weekly)
CREATE PROCEDURE sp_reset_weekly_hours()
BEGIN
    UPDATE driver SET weekly_hours = 0.00;
    UPDATE driver_assistant SET weekly_hours = 0.00;
    
    SELECT 'Weekly hours reset successfully' as message;
END //

-- Clean up old audit logs
CREATE PROCEDURE sp_cleanup_audit_logs(
    IN p_days_to_keep INT
)
BEGIN
    DELETE FROM audit_log 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL p_days_to_keep DAY);
    
    SELECT ROW_COUNT() as deleted_records, 'Old audit logs cleaned up' as message;
END //

DELIMITER ;

-- =============================================
-- END OF STORED PROCEDURES
-- =============================================