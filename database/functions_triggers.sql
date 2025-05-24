-- =============================================
-- Supply Chain Management System - Functions and Triggers
-- =============================================

USE supply_chain_db;

DELIMITER //

-- =============================================
-- CUSTOM FUNCTIONS
-- =============================================

-- Calculate shipping cost based on route, weight, and volume
CREATE FUNCTION fn_calculate_shipping_cost(
    p_route_id INT,
    p_weight DECIMAL(10,2),
    p_volume DECIMAL(10,2)
) RETURNS DECIMAL(10,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_base_cost DECIMAL(10,2) DEFAULT 0;
    DECLARE v_distance DECIMAL(8,2) DEFAULT 0;
    DECLARE v_route_type VARCHAR(20);
    DECLARE v_weight_factor DECIMAL(5,2) DEFAULT 1.5;
    DECLARE v_volume_factor DECIMAL(5,2) DEFAULT 2.0;
    DECLARE v_type_multiplier DECIMAL(3,2) DEFAULT 1.0;
    DECLARE v_final_cost DECIMAL(10,2);
    
    -- Get route details
    SELECT base_cost, distance, route_type
    INTO v_base_cost, v_distance, v_route_type
    FROM route
    WHERE route_id = p_route_id;
    
    -- Set multiplier based on route type
    CASE v_route_type
        WHEN 'express' THEN SET v_type_multiplier = 1.5;
        WHEN 'regional' THEN SET v_type_multiplier = 1.2;
        ELSE SET v_type_multiplier = 1.0;
    END CASE;
    
    -- Calculate final cost
    SET v_final_cost = (v_base_cost + (p_weight * v_weight_factor) + (p_volume * v_volume_factor)) * v_type_multiplier;
    
    -- Minimum shipping cost
    IF v_final_cost < 10.00 THEN
        SET v_final_cost = 10.00;
    END IF;
    
    RETURN v_final_cost;
END //

-- Calculate customer discount based on type and order value
CREATE FUNCTION fn_calculate_customer_discount(
    p_customer_id INT,
    p_order_value DECIMAL(12,2)
) RETURNS DECIMAL(10,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_discount_rate DECIMAL(5,2) DEFAULT 0;
    DECLARE v_discount_amount DECIMAL(10,2) DEFAULT 0;
    DECLARE v_customer_type VARCHAR(20);
    
    -- Get customer discount rate
    SELECT ct.discount_rate, ct.customer_type
    INTO v_discount_rate, v_customer_type
    FROM customers c
    INNER JOIN customer_type ct ON c.customer_type = ct.customer_type
    WHERE c.customer_id = p_customer_id;
    
    -- Calculate discount
    SET v_discount_amount = p_order_value * (v_discount_rate / 100);
    
    -- Additional volume discount for wholesale customers
    IF v_customer_type = 'wholesale' AND p_order_value > 5000 THEN
        SET v_discount_amount = v_discount_amount + (p_order_value * 0.02); -- Additional 2%
    END IF;
    
    RETURN v_discount_amount;
END //

-- Validate order status transition
CREATE FUNCTION fn_validate_status_transition(
    p_current_status VARCHAR(50),
    p_new_status VARCHAR(50)
) RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_valid BOOLEAN DEFAULT FALSE;
    
    -- Define valid transitions
    CASE p_current_status
        WHEN 'pending' THEN
            IF p_new_status IN ('confirmed', 'cancelled') THEN
                SET v_valid = TRUE;
            END IF;
        WHEN 'confirmed' THEN
            IF p_new_status IN ('assigned_train', 'cancelled') THEN
                SET v_valid = TRUE;
            END IF;
        WHEN 'assigned_train' THEN
            IF p_new_status IN ('in_transit_rail', 'cancelled') THEN
                SET v_valid = TRUE;
            END IF;
        WHEN 'in_transit_rail' THEN
            IF p_new_status IN ('at_warehouse', 'cancelled') THEN
                SET v_valid = TRUE;
            END IF;
        WHEN 'at_warehouse' THEN
            IF p_new_status IN ('assigned_truck', 'cancelled') THEN
                SET v_valid = TRUE;
            END IF;
        WHEN 'assigned_truck' THEN
            IF p_new_status IN ('out_for_delivery', 'cancelled') THEN
                SET v_valid = TRUE;
            END IF;
        WHEN 'out_for_delivery' THEN
            IF p_new_status IN ('delivered', 'returned') THEN
                SET v_valid = TRUE;
            END IF;
        ELSE
            SET v_valid = FALSE;
    END CASE;
    
    RETURN v_valid;
END //

-- Calculate train capacity utilization percentage
CREATE FUNCTION fn_train_utilization(
    p_train_session_id INT
) RETURNS DECIMAL(5,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_total_capacity INT;
    DECLARE v_available_capacity INT;
    DECLARE v_utilization DECIMAL(5,2);
    
    SELECT total_capacity, available_capacity
    INTO v_total_capacity, v_available_capacity
    FROM train_schedule
    WHERE train_session_id = p_train_session_id;
    
    IF v_total_capacity > 0 THEN
        SET v_utilization = ((v_total_capacity - v_available_capacity) / v_total_capacity) * 100;
    ELSE
        SET v_utilization = 0;
    END IF;
    
    RETURN v_utilization;
END //

-- Get next available train for route
CREATE FUNCTION fn_get_next_available_train(
    p_departure_date DATE,
    p_required_capacity INT,
    p_required_weight DECIMAL(10,2)
) RETURNS INT
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_train_session_id INT DEFAULT NULL;
    
    SELECT train_session_id
    INTO v_train_session_id
    FROM train_schedule
    WHERE departure_date >= p_departure_date
    AND available_capacity >= p_required_capacity
    AND available_weight >= p_required_weight
    AND status = 'scheduled'
    ORDER BY departure_date ASC, departure_time ASC
    LIMIT 1;
    
    RETURN v_train_session_id;
END //

-- Check if driver can work (within hour limits)
CREATE FUNCTION fn_can_driver_work(
    p_driver_id INT,
    p_additional_hours DECIMAL(5,2)
) RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_current_hours DECIMAL(5,2);
    DECLARE v_max_hours DECIMAL(5,2);
    
    SELECT weekly_hours, max_weekly_hours
    INTO v_current_hours, v_max_hours
    FROM driver
    WHERE driver_id = p_driver_id AND is_active = TRUE;
    
    IF (v_current_hours + p_additional_hours) <= v_max_hours THEN
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END //

-- =============================================
-- TRIGGERS
-- =============================================

-- Trigger: Update order totals when order items change
CREATE TRIGGER tr_update_order_totals_after_insert
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE order_table
    SET total_items = (
            SELECT SUM(quantity) FROM order_items WHERE order_id = NEW.order_id
        ),
        total_weight = (
            SELECT SUM(total_weight) FROM order_items WHERE order_id = NEW.order_id
        ),
        total_volume = (
            SELECT SUM(total_volume) FROM order_items WHERE order_id = NEW.order_id
        ),
        subtotal = (
            SELECT SUM(line_total) FROM order_items WHERE order_id = NEW.order_id
        ),
        updated_date = NOW()
    WHERE order_id = NEW.order_id;
END //

CREATE TRIGGER tr_update_order_totals_after_update
AFTER UPDATE ON order_items
FOR EACH ROW
BEGIN
    UPDATE order_table
    SET total_items = (
            SELECT SUM(quantity) FROM order_items WHERE order_id = NEW.order_id
        ),
        total_weight = (
            SELECT SUM(total_weight) FROM order_items WHERE order_id = NEW.order_id
        ),
        total_volume = (
            SELECT SUM(total_volume) FROM order_items WHERE order_id = NEW.order_id
        ),
        subtotal = (
            SELECT SUM(line_total) FROM order_items WHERE order_id = NEW.order_id
        ),
        updated_date = NOW()
    WHERE order_id = NEW.order_id;
END //

-- Trigger: Validate capacity before train assignment
CREATE TRIGGER tr_validate_train_capacity_before_insert
BEFORE INSERT ON order_train_schedule
FOR EACH ROW
BEGIN
    DECLARE v_available_capacity INT;
    DECLARE v_available_weight DECIMAL(10,2);
    DECLARE v_available_volume DECIMAL(10,2);
    
    SELECT available_capacity, available_weight, available_volume
    INTO v_available_capacity, v_available_weight, v_available_volume
    FROM train_schedule
    WHERE train_session_id = NEW.train_session_id;
    
    IF v_available_capacity < NEW.assigned_items THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient train capacity';
    END IF;
    
    IF v_available_weight < NEW.assigned_weight THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient train weight capacity';
    END IF;
    
    IF v_available_volume < NEW.assigned_volume THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient train volume capacity';
    END IF;
END //

-- Trigger: Validate capacity before truck assignment
CREATE TRIGGER tr_validate_truck_capacity_before_insert
BEFORE INSERT ON order_truck_schedule
FOR EACH ROW
BEGIN
    DECLARE v_available_capacity INT;
    DECLARE v_available_weight DECIMAL(8,2);
    
    SELECT available_capacity, available_weight
    INTO v_available_capacity, v_available_weight
    FROM truck_schedule
    WHERE truck_session_id = NEW.truck_session_id;
    
    IF v_available_capacity < NEW.assigned_items THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient truck capacity';
    END IF;
    
    IF v_available_weight < NEW.assigned_weight THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient truck weight capacity';
    END IF;
END //

-- Trigger: Validate driver working hours before truck scheduling
CREATE TRIGGER tr_validate_driver_hours_before_insert
BEFORE INSERT ON truck_schedule
FOR EACH ROW
BEGIN
    DECLARE v_driver_hours DECIMAL(5,2);
    DECLARE v_max_driver_hours DECIMAL(5,2);
    DECLARE v_assistant_hours DECIMAL(5,2);
    DECLARE v_max_assistant_hours DECIMAL(5,2);
    DECLARE v_estimated_hours DECIMAL(5,2);
    
    -- Calculate estimated hours for this trip
    SELECT HOUR(TIMEDIFF(NEW.estimated_end_time, NEW.start_time)) + 
           (MINUTE(TIMEDIFF(NEW.estimated_end_time, NEW.start_time)) / 60)
    INTO v_estimated_hours;
    
    -- Check driver hours
    SELECT weekly_hours, max_weekly_hours
    INTO v_driver_hours, v_max_driver_hours
    FROM driver
    WHERE driver_id = NEW.driver_id;
    
    IF (v_driver_hours + v_estimated_hours) > v_max_driver_hours THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Driver would exceed maximum weekly hours';
    END IF;
    
    -- Check assistant hours if assigned
    IF NEW.driver_assistant_id IS NOT NULL THEN
        SELECT weekly_hours, max_weekly_hours
        INTO v_assistant_hours, v_max_assistant_hours
        FROM driver_assistant
        WHERE driver_assistant_id = NEW.driver_assistant_id;
        
        IF (v_assistant_hours + v_estimated_hours) > v_max_assistant_hours THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Driver assistant would exceed maximum weekly hours';
        END IF;
    END IF;
END //

-- Trigger: Update inventory when order is confirmed
CREATE TRIGGER tr_reserve_inventory_after_order_confirm
AFTER UPDATE ON order_table
FOR EACH ROW
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_item_id INT;
    DECLARE v_quantity INT;
    DECLARE v_store_name VARCHAR(50);
    
    DECLARE item_cursor CURSOR FOR
        SELECT oi.item_id, oi.quantity
        FROM order_items oi
        WHERE oi.order_id = NEW.order_id;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    -- Only process when status changes to confirmed
    IF OLD.status != 'confirmed' AND NEW.status = 'confirmed' THEN
        -- Get store name from route
        SELECT store_name INTO v_store_name
        FROM route
        WHERE route_id = NEW.route_id;
        
        OPEN item_cursor;
        read_loop: LOOP
            FETCH item_cursor INTO v_item_id, v_quantity;
            IF done THEN
                LEAVE read_loop;
            END IF;
            
            -- Reserve inventory
            UPDATE inventory
            SET quantity_available = quantity_available - v_quantity,
                quantity_reserved = quantity_reserved + v_quantity,
                updated_date = NOW()
            WHERE store_name = v_store_name AND item_id = v_item_id;
            
            -- Check if update was successful
            IF ROW_COUNT() = 0 THEN
                SIGNAL SQLSTATE '45000' 
                SET MESSAGE_TEXT = CONCAT('Insufficient inventory for item ID: ', v_item_id);
            END IF;
        END LOOP;
        CLOSE item_cursor;
    END IF;
    
    -- Release inventory when order is cancelled
    IF OLD.status NOT IN ('cancelled', 'returned') AND NEW.status IN ('cancelled', 'returned') THEN
        -- Get store name from route
        SELECT store_name INTO v_store_name
        FROM route
        WHERE route_id = NEW.route_id;
        
        SET done = FALSE;
        OPEN item_cursor;
        release_loop: LOOP
            FETCH item_cursor INTO v_item_id, v_quantity;
            IF done THEN
                LEAVE release_loop;
            END IF;
            
            -- Release reserved inventory
            UPDATE inventory
            SET quantity_available = quantity_available + v_quantity,
                quantity_reserved = quantity_reserved - v_quantity,
                updated_date = NOW()
            WHERE store_name = v_store_name AND item_id = v_item_id;
        END LOOP;
        CLOSE item_cursor;
    END IF;
END //

-- Trigger: Update store inventory count
CREATE TRIGGER tr_update_store_inventory_count_after_insert
AFTER INSERT ON inventory
FOR EACH ROW
BEGIN
    UPDATE store
    SET current_inventory_count = (
        SELECT SUM(quantity_available + quantity_reserved)
        FROM inventory
        WHERE store_name = NEW.store_name
    )
    WHERE store_name = NEW.store_name;
END //

CREATE TRIGGER tr_update_store_inventory_count_after_update
AFTER UPDATE ON inventory
FOR EACH ROW
BEGIN
    UPDATE store
    SET current_inventory_count = (
        SELECT SUM(quantity_available + quantity_reserved)
        FROM inventory
        WHERE store_name = NEW.store_name
    )
    WHERE store_name = NEW.store_name;
END //

-- Trigger: Log user activity
CREATE TRIGGER tr_log_user_login
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    IF OLD.last_login IS NULL OR NEW.last_login != OLD.last_login THEN
        INSERT INTO audit_log (table_name, operation, record_id, new_values, user_name)
        VALUES ('users', 'UPDATE', NEW.user_name, 
                JSON_OBJECT('last_login', NEW.last_login), 
                NEW.user_name);
    END IF;
END //

-- Trigger: Validate delivery date
CREATE TRIGGER tr_validate_delivery_date_before_insert
BEFORE INSERT ON order_table
FOR EACH ROW
BEGIN
    IF NEW.delivery_date < DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Delivery date must be at least 7 days from today';
    END IF;
END //

CREATE TRIGGER tr_validate_delivery_date_before_update
BEFORE UPDATE ON order_table
FOR EACH ROW
BEGIN
    IF NEW.delivery_date != OLD.delivery_date AND NEW.delivery_date < DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Delivery date must be at least 7 days from today';
    END IF;
END //

-- Trigger: Update driver total deliveries and hours
CREATE TRIGGER tr_update_driver_stats_after_completion
AFTER UPDATE ON truck_schedule
FOR EACH ROW
BEGIN
    DECLARE v_actual_hours DECIMAL(5,2);
    
    -- Only process when status changes to completed
    IF OLD.status != 'completed' AND NEW.status = 'completed' THEN
        -- Calculate actual hours worked
        IF NEW.actual_start_time IS NOT NULL AND NEW.actual_end_time IS NOT NULL THEN
            SELECT HOUR(TIMEDIFF(NEW.actual_end_time, NEW.actual_start_time)) + 
                   (MINUTE(TIMEDIFF(NEW.actual_end_time, NEW.actual_start_time)) / 60)
            INTO v_actual_hours;
            
            -- Update driver stats
            UPDATE driver
            SET weekly_hours = weekly_hours + v_actual_hours,
                total_deliveries = total_deliveries + 1
            WHERE driver_id = NEW.driver_id;
            
            -- Update assistant stats if present
            IF NEW.driver_assistant_id IS NOT NULL THEN
                UPDATE driver_assistant
                SET weekly_hours = weekly_hours + v_actual_hours,
                    total_assists = total_assists + 1
                WHERE driver_assistant_id = NEW.driver_assistant_id;
            END IF;
        END IF;
    END IF;
END //

-- Trigger: Prevent deletion of orders with active assignments
CREATE TRIGGER tr_prevent_order_deletion
BEFORE DELETE ON order_table
FOR EACH ROW
BEGIN
    DECLARE v_train_assignments INT DEFAULT 0;
    DECLARE v_truck_assignments INT DEFAULT 0;
    
    SELECT COUNT(*) INTO v_train_assignments
    FROM order_train_schedule
    WHERE order_id = OLD.order_id;
    
    SELECT COUNT(*) INTO v_truck_assignments
    FROM order_truck_schedule
    WHERE order_id = OLD.order_id;
    
    IF v_train_assignments > 0 OR v_truck_assignments > 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Cannot delete order with active transport assignments';
    END IF;
END //

-- Trigger: Auto-assign orders to available trains
CREATE TRIGGER tr_auto_assign_to_train
AFTER UPDATE ON order_table
FOR EACH ROW
BEGIN
    DECLARE v_train_session_id INT;
    
    -- Only process when status changes to confirmed
    IF OLD.status != 'confirmed' AND NEW.status = 'confirmed' THEN
        -- Find next available train
        SET v_train_session_id = fn_get_next_available_train(
            NEW.delivery_date,
            NEW.total_items,
            NEW.total_weight
        );
        
        -- If train found, create assignment
        IF v_train_session_id IS NOT NULL THEN
            INSERT INTO order_train_schedule (
                order_id, train_session_id, assigned_weight, assigned_volume, assigned_items
            ) VALUES (
                NEW.order_id, v_train_session_id, NEW.total_weight, NEW.total_volume, NEW.total_items
            );
            
            -- Update order status
            UPDATE order_table
            SET status = 'assigned_train'
            WHERE order_id = NEW.order_id;
        END IF;
    END IF;
END //

-- Trigger: Performance metrics collection
CREATE TRIGGER tr_collect_performance_metrics
AFTER INSERT ON order_table
FOR EACH ROW
BEGIN
    -- Record order metrics
    INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, category, recorded_date, recorded_time)
    VALUES 
    ('orders_created', 1, 'count', 'orders', CURDATE(), CURTIME()),
    ('order_value', NEW.total_amount, 'currency', 'revenue', CURDATE(), CURTIME()),
    ('order_weight', NEW.total_weight, 'kg', 'logistics', CURDATE(), CURTIME()),
    ('order_items', NEW.total_items, 'count', 'inventory', CURDATE(), CURTIME());
END //

DELIMITER ;

-- =============================================
-- VIEWS FOR REPORTING
-- =============================================

-- Order summary view
CREATE VIEW vw_order_summary AS
SELECT 
    o.order_id,
    o.order_date,
    o.delivery_date,
    o.status,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    c.email as customer_email,
    ct.customer_type,
    r.store_name,
    r.destination_city,
    o.total_items,
    o.total_weight,
    o.total_amount,
    o.payment_status,
    DATEDIFF(o.delivery_date, o.order_date) as days_to_delivery
FROM order_table o
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN customer_type ct ON c.customer_type = ct.customer_type
INNER JOIN route r ON o.route_id = r.route_id;

-- Inventory status view
CREATE VIEW vw_inventory_status AS
SELECT 
    i.store_name,
    it.item_name,
    it.category,
    i.quantity_available,
    i.quantity_reserved,
    (i.quantity_available + i.quantity_reserved) as total_quantity,
    i.reorder_point,
    CASE 
        WHEN i.quantity_available = 0 THEN 'Out of Stock'
        WHEN i.quantity_available <= i.reorder_point THEN 'Low Stock'
        WHEN i.quantity_available > i.reorder_point * 3 THEN 'Overstocked'
        ELSE 'Normal'
    END as stock_status,
    (i.quantity_available * i.cost_per_unit) as inventory_value
FROM inventory i
INNER JOIN items it ON i.item_id = it.item_id
WHERE it.is_active = TRUE;

-- Transportation utilization view
CREATE VIEW vw_transport_utilization AS
SELECT 
    'Train' as transport_type,
    t.train_name as vehicle_name,
    ts.departure_date,
    ts.total_capacity,
    ts.available_capacity,
    (ts.total_capacity - ts.available_capacity) as used_capacity,
    ROUND(((ts.total_capacity - ts.available_capacity) / ts.total_capacity * 100), 2) as utilization_percentage,
    ts.status
FROM train_schedule ts
INNER JOIN train t ON ts.train_id = t.train_id

UNION ALL

SELECT 
    'Truck' as transport_type,
    tr.license_plate as vehicle_name,
    trs.scheduled_date as departure_date,
    trs.total_capacity,
    trs.available_capacity,
    (trs.total_capacity - trs.available_capacity) as used_capacity,
    ROUND(((trs.total_capacity - trs.available_capacity) / trs.total_capacity * 100), 2) as utilization_percentage,
    trs.status
FROM truck_schedule trs
INNER JOIN truck tr ON trs.truck_id = tr.truck_id;

-- Driver performance view
CREATE VIEW vw_driver_performance AS
SELECT 
    d.driver_id,
    CONCAT(d.first_name, ' ', d.last_name) as driver_name,
    d.store_name,
    d.total_deliveries,
    d.weekly_hours,
    d.max_weekly_hours,
    ROUND((d.weekly_hours / d.max_weekly_hours * 100), 2) as hour_utilization_percentage,
    d.rating,
    COUNT(ts.truck_session_id) as scheduled_deliveries,
    AVG(CASE WHEN ts.status = 'completed' THEN 
        TIMESTAMPDIFF(MINUTE, ts.actual_start_time, ts.actual_end_time) 
        ELSE NULL END) as avg_delivery_time_minutes
FROM driver d
LEFT JOIN truck_schedule ts ON d.driver_id = ts.driver_id
WHERE d.is_active = TRUE
GROUP BY d.driver_id, d.first_name, d.last_name, d.store_name, d.total_deliveries, 
         d.weekly_hours, d.max_weekly_hours, d.rating;

-- Sales performance view
CREATE VIEW vw_sales_performance AS
SELECT 
    DATE(o.order_date) as sale_date,
    r.store_name,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as avg_order_value,
    SUM(o.total_items) as total_items_sold,
    SUM(o.total_weight) as total_weight_shipped
FROM order_table o
INNER JOIN route r ON o.route_id = r.route_id
WHERE o.status NOT IN ('cancelled', 'returned')
GROUP BY DATE(o.order_date), r.store_name
ORDER BY sale_date DESC, r.store_name;

-- =============================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =============================================

-- Additional indexes for complex queries
CREATE INDEX idx_order_date_status ON order_table(order_date, status);
CREATE INDEX idx_delivery_date_status ON order_table(delivery_date, status);
CREATE INDEX idx_train_schedule_departure ON train_schedule(departure_date, departure_time);
CREATE INDEX idx_truck_schedule_date ON truck_schedule(scheduled_date, start_time);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_performance_metrics_date ON performance_metrics(recorded_date, metric_name);

-- =============================================
-- END OF FUNCTIONS, TRIGGERS, AND VIEWS
-- =============================================

SELECT 'Database functions, triggers, and views created successfully!' as Status;