-- =============================================
-- Supply Chain Management System - Sample Data
-- =============================================

USE supply_chain_db;

-- Disable foreign key checks temporarily for data insertion
SET FOREIGN_KEY_CHECKS = 0;

-- =============================================
-- 1. USER MANAGEMENT DATA
-- =============================================

-- Insert customer types
INSERT INTO customer_type (customer_type, discount_rate, min_order_qty, description) VALUES
('end', 0.00, 1, 'End consumer with standard pricing'),
('retail', 5.00, 10, 'Retail customer with 5% discount'),
('wholesale', 15.00, 50, 'Wholesale customer with 15% discount');

-- Insert users
INSERT INTO users (user_name, password, role, created_date, is_active) VALUES
-- Customers
('john_doe', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewTHNGfC8z5U7X92', 'customer', '2024-01-15 10:00:00', TRUE),
('jane_smith', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewTHNGfC8z5U7X92', 'customer', '2024-01-16 11:30:00', TRUE),
('retailer_a', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewTHNGfC8z5U7X92', 'customer', '2024-01-20 09:15:00', TRUE),
('wholesale_b', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewTHNGfC8z5U7X92', 'customer', '2024-01-25 14:45:00', TRUE),
-- Store Managers
('sm_colombo', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewTHNGfC8z5U7X92', 'store_manager', '2024-01-01 08:00:00', TRUE),
('sm_kandy', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewTHNGfC8z5U7X92', 'store_manager', '2024-01-01 08:00:00', TRUE),
('sm_galle', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewTHNGfC8z5U7X92', 'store_manager', '2024-01-01 08:00:00', TRUE),
-- Main Managers
('mm_operations', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewTHNGfC8z5U7X92', 'main_manager', '2024-01-01 08:00:00', TRUE),
('mm_logistics', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewTHNGfC8z5U7X92', 'main_manager', '2024-01-01 08:00:00', TRUE);

-- Insert stores
INSERT INTO store (store_name, address, city, state, postal_code, phone, email, capacity, manager_count, operating_hours) VALUES
('Colombo Main', '123 Galle Road, Colombo 03', 'Colombo', 'Western', '00300', '+94-11-2345678', 'colombo@supplychain.lk', 2000, 1, '08:00-20:00'),
('Kandy Branch', '45 Peradeniya Road, Kandy', 'Kandy', 'Central', '20000', '+94-81-2234567', 'kandy@supplychain.lk', 1500, 1, '08:00-18:00'),
('Galle Branch', '78 Wakwella Road, Galle', 'Galle', 'Southern', '80000', '+94-91-2123456', 'galle@supplychain.lk', 1200, 1, '08:00-18:00'),
('Jaffna Branch', '12 Hospital Street, Jaffna', 'Jaffna', 'Northern', '40000', '+94-21-2345678', 'jaffna@supplychain.lk', 800, 1, '08:00-17:00');

-- Insert customers
INSERT INTO customers (user_name, customer_type, first_name, last_name, email, phone, address, city, postal_code, credit_limit) VALUES
('john_doe', 'end', 'John', 'Doe', 'john.doe@email.com', '+94-77-1234567', '12 Temple Road, Nugegoda', 'Nugegoda', '10250', 50000.00),
('jane_smith', 'end', 'Jane', 'Smith', 'jane.smith@email.com', '+94-76-9876543', '34 Flower Road, Colombo 07', 'Colombo', '00700', 75000.00),
('retailer_a', 'retail', 'Anil', 'Fernando', 'anil@retailstore.lk', '+94-11-2567890', '56 Main Street, Maharagama', 'Maharagama', '10280', 200000.00),
('wholesale_b', 'wholesale', 'Sunil', 'Perera', 'sunil@wholesale.lk', '+94-11-3456789', '89 Industrial Zone, Katunayake', 'Katunayake', '11450', 500000.00);

-- Insert store managers
INSERT INTO store_manager (user_name, store_name, first_name, last_name, email, phone, hire_date, salary, department) VALUES
('sm_colombo', 'Colombo Main', 'Priya', 'Jayawardena', 'priya.j@supplychain.lk', '+94-77-2345678', '2023-06-01', 85000.00, 'Operations'),
('sm_kandy', 'Kandy Branch', 'Rohan', 'Silva', 'rohan.s@supplychain.lk', '+94-77-3456789', '2023-07-15', 75000.00, 'Operations'),
('sm_galle', 'Galle Branch', 'Nimali', 'Wickramasinghe', 'nimali.w@supplychain.lk', '+94-77-4567890', '2023-08-01', 70000.00, 'Operations');

-- Insert main managers
INSERT INTO main_manager (user_name, first_name, last_name, email, phone, department, hire_date, salary, authority_level) VALUES
('mm_operations', 'Chamara', 'Bandara', 'chamara.b@supplychain.lk', '+94-77-5678901', 'Operations', '2022-01-15', 150000.00, 'senior'),
('mm_logistics', 'Sanduni', 'Rajapaksa', 'sanduni.r@supplychain.lk', '+94-77-6789012', 'Logistics', '2022-03-01', 160000.00, 'executive');

-- =============================================
-- 2. PRODUCT & INVENTORY DATA
-- =============================================

-- Insert items
INSERT INTO items (item_name, category, subcategory, description, price, weight, volume, fragile, hazardous, stock_threshold) VALUES
-- Electronics
('Samsung Galaxy S24', 'Electronics', 'Smartphones', 'Latest Samsung flagship smartphone', 145000.00, 0.2, 0.001, TRUE, FALSE, 20),
('Apple iPhone 15', 'Electronics', 'Smartphones', 'Apple iPhone 15 with advanced features', 185000.00, 0.18, 0.001, TRUE, FALSE, 15),
('Dell Laptop XPS 13', 'Electronics', 'Computers', 'Dell XPS 13 ultrabook laptop', 225000.00, 1.2, 0.003, TRUE, FALSE, 10),
('Sony WH-1000XM5', 'Electronics', 'Audio', 'Noise cancelling wireless headphones', 45000.00, 0.25, 0.002, TRUE, FALSE, 25),
('iPad Pro 12.9', 'Electronics', 'Tablets', 'Apple iPad Pro with M2 chip', 175000.00, 0.68, 0.002, TRUE, FALSE, 12),

-- Home & Kitchen
('Samsung Refrigerator', 'Home & Kitchen', 'Appliances', 'Double door refrigerator 350L', 95000.00, 65.0, 0.6, FALSE, FALSE, 5),
('LG Washing Machine', 'Home & Kitchen', 'Appliances', 'Front load washing machine 8kg', 75000.00, 68.0, 0.5, FALSE, FALSE, 8),
('Philips Air Fryer', 'Home & Kitchen', 'Small Appliances', 'Digital air fryer 4.1L capacity', 18500.00, 4.5, 0.03, FALSE, FALSE, 30),
('Tefal Cookware Set', 'Home & Kitchen', 'Cookware', 'Non-stick cookware set 7 pieces', 12000.00, 3.2, 0.02, FALSE, FALSE, 40),

-- Fashion & Clothing
('Nike Running Shoes', 'Fashion', 'Footwear', 'Professional running shoes', 15500.00, 0.8, 0.005, FALSE, FALSE, 50),
('Adidas T-Shirt', 'Fashion', 'Apparel', 'Premium cotton sports t-shirt', 3500.00, 0.2, 0.001, FALSE, FALSE, 100),
('Levis Jeans', 'Fashion', 'Apparel', 'Classic denim jeans', 8500.00, 0.5, 0.002, FALSE, FALSE, 75),

-- Books & Stationery
('Programming Books Set', 'Books', 'Education', 'Complete programming guide collection', 5500.00, 2.1, 0.008, FALSE, FALSE, 60),
('Office Stationery Kit', 'Stationery', 'Office Supplies', 'Complete office stationery package', 2800.00, 1.5, 0.006, FALSE, FALSE, 80),

-- Sports & Fitness
('Yoga Mat Premium', 'Sports', 'Fitness', 'Non-slip yoga mat with carrying strap', 4500.00, 1.2, 0.01, FALSE, FALSE, 45);

-- Insert inventory for each store
INSERT INTO inventory (store_name, item_id, quantity_available, quantity_reserved, reorder_point, max_stock_level, cost_per_unit) VALUES
-- Colombo Main Store
('Colombo Main', 1, 45, 5, 20, 100, 120000.00),
('Colombo Main', 2, 30, 2, 15, 80, 155000.00),
('Colombo Main', 3, 25, 3, 10, 50, 190000.00),
('Colombo Main', 4, 60, 8, 25, 150, 38000.00),
('Colombo Main', 5, 20, 2, 12, 60, 148000.00),
('Colombo Main', 6, 15, 1, 5, 30, 82000.00),
('Colombo Main', 7, 22, 2, 8, 40, 65000.00),
('Colombo Main', 8, 35, 5, 30, 80, 16000.00),
('Colombo Main', 9, 50, 10, 40, 120, 10500.00),
('Colombo Main', 10, 80, 12, 50, 200, 13000.00),
('Colombo Main', 11, 120, 15, 100, 300, 3000.00),
('Colombo Main', 12, 95, 18, 75, 250, 7200.00),
('Colombo Main', 13, 75, 10, 60, 180, 4800.00),
('Colombo Main', 14, 65, 8, 80, 150, 2400.00),
('Colombo Main', 15, 55, 7, 45, 120, 3800.00),

-- Kandy Branch Store
('Kandy Branch', 1, 25, 3, 20, 60, 120000.00),
('Kandy Branch', 2, 18, 1, 15, 45, 155000.00),
('Kandy Branch', 3, 12, 2, 10, 30, 190000.00),
('Kandy Branch', 4, 35, 4, 25, 80, 38000.00),
('Kandy Branch', 5, 10, 1, 12, 35, 148000.00),
('Kandy Branch', 6, 8, 0, 5, 20, 82000.00),
('Kandy Branch', 7, 12, 1, 8, 25, 65000.00),
('Kandy Branch', 8, 20, 2, 30, 50, 16000.00),
('Kandy Branch', 9, 28, 3, 40, 70, 10500.00),
('Kandy Branch', 10, 45, 5, 50, 100, 13000.00),
('Kandy Branch', 11, 70, 8, 100, 180, 3000.00),
('Kandy Branch', 12, 52, 6, 75, 130, 7200.00),
('Kandy Branch', 13, 42, 4, 60, 90, 4800.00),
('Kandy Branch', 14, 38, 3, 80, 85, 2400.00),
('Kandy Branch', 15, 32, 2, 45, 70, 3800.00),

-- Galle Branch Store
('Galle Branch', 1, 20, 2, 20, 50, 120000.00),
('Galle Branch', 2, 15, 1, 15, 40, 155000.00),
('Galle Branch', 3, 8, 1, 10, 25, 190000.00),
('Galle Branch', 4, 28, 3, 25, 65, 38000.00),
('Galle Branch', 5, 8, 0, 12, 30, 148000.00),
('Galle Branch', 6, 6, 0, 5, 18, 82000.00),
('Galle Branch', 7, 10, 1, 8, 22, 65000.00),
('Galle Branch', 8, 18, 2, 30, 45, 16000.00),
('Galle Branch', 9, 22, 2, 40, 60, 10500.00),
('Galle Branch', 10, 38, 4, 50, 85, 13000.00),
('Galle Branch', 11, 58, 6, 100, 150, 3000.00),
('Galle Branch', 12, 45, 5, 75, 110, 7200.00),
('Galle Branch', 13, 35, 3, 60, 80, 4800.00),
('Galle Branch', 14, 32, 2, 80, 75, 2400.00),
('Galle Branch', 15, 28, 2, 45, 65, 3800.00);

-- =============================================
-- 3. ROUTES DATA
-- =============================================

INSERT INTO route (store_name, route_name, destination_address, destination_city, destination_state, distance, estimated_time, base_cost, route_type) VALUES
-- Colombo Main Routes
('Colombo Main', 'Colombo-Nugegoda', 'Nugegoda Town Area', 'Nugegoda', 'Western', 12.5, '00:45:00', 350.00, 'local'),
('Colombo Main', 'Colombo-Maharagama', 'Maharagama Commercial Zone', 'Maharagama', 'Western', 18.3, '01:00:00', 450.00, 'local'),
('Colombo Main', 'Colombo-Katunayake', 'Katunayake Industrial Zone', 'Katunayake', 'Western', 35.2, '01:30:00', 850.00, 'regional'),
('Colombo Main', 'Colombo-Mount Lavinia', 'Mount Lavinia Beach Road', 'Mount Lavinia', 'Western', 15.8, '00:50:00', 420.00, 'local'),
('Colombo Main', 'Colombo-Kalutara', 'Kalutara Town Center', 'Kalutara', 'Western', 45.6, '02:00:00', 1200.00, 'regional'),

-- Kandy Branch Routes
('Kandy Branch', 'Kandy-Peradeniya', 'University of Peradeniya', 'Peradeniya', 'Central', 8.2, '00:30:00', 280.00, 'local'),
('Kandy Branch', 'Kandy-Matale', 'Matale Town Center', 'Matale', 'Central', 28.4, '01:15:00', 650.00, 'regional'),
('Kandy Branch', 'Kandy-Nuwara Eliya', 'Nuwara Eliya Main Street', 'Nuwara Eliya', 'Central', 48.7, '02:30:00', 1350.00, 'regional'),
('Kandy Branch', 'Kandy-Dambulla', 'Dambulla Commercial Area', 'Dambulla', 'Central', 72.1, '02:45:00', 1650.00, 'regional'),

-- Galle Branch Routes
('Galle Branch', 'Galle-Unawatuna', 'Unawatuna Beach Area', 'Unawatuna', 'Southern', 6.5, '00:25:00', 250.00, 'local'),
('Galle Branch', 'Galle-Matara', 'Matara Bus Station Area', 'Matara', 'Southern', 32.8, '01:20:00', 750.00, 'regional'),
('Galle Branch', 'Galle-Hikkaduwa', 'Hikkaduwa Beach Road', 'Hikkaduwa', 'Southern', 18.9, '00:55:00', 480.00, 'local'),
('Galle Branch', 'Galle-Tangalle', 'Tangalle Town Center', 'Tangalle', 'Southern', 58.3, '02:15:00', 1450.00, 'regional');

-- =============================================
-- 4. TRANSPORTATION DATA
-- =============================================

-- Insert trains
INSERT INTO train (train_name, train_type, capacity, max_weight, max_volume, operational_cost_per_km, status, purchase_date, last_maintenance, next_maintenance) VALUES
('Express Cargo 001', 'express', 500, 25.0, 80.0, 8.50, 'active', '2022-03-15', '2024-11-15', '2025-02-15'),
('Freight Master 002', 'freight', 800, 40.0, 120.0, 6.75, 'active', '2021-08-20', '2024-10-20', '2025-01-20'),
('Standard Trans 003', 'standard', 350, 18.0, 60.0, 5.25, 'active', '2023-01-10', '2024-12-10', '2025-03-10'),
('Heavy Haul 004', 'freight', 1000, 50.0, 150.0, 7.80, 'active', '2020-11-05', '2024-09-05', '2024-12-05'),
('Quick Line 005', 'express', 400, 20.0, 70.0, 9.20, 'maintenance', '2023-06-18', '2024-11-01', '2025-02-01');

-- Insert train schedules
INSERT INTO train_schedule (train_id, departure_date, departure_time, route_description, total_capacity, available_capacity, total_weight_capacity, available_weight, total_volume_capacity, available_volume, status) VALUES
-- Current week schedules
(1, '2024-12-02', '08:00:00', 'Colombo-Kandy-Galle Circuit', 500, 420, 25.0, 20.5, 80.0, 65.0, 'scheduled'),
(2, '2024-12-02', '14:00:00', 'Main Distribution Route', 800, 720, 40.0, 32.0, 120.0, 95.0, 'scheduled'),
(3, '2024-12-03', '10:00:00', 'Regional Express Route', 350, 300, 18.0, 15.0, 60.0, 48.0, 'scheduled'),
(1, '2024-12-03', '16:00:00', 'Evening Distribution', 500, 450, 25.0, 22.0, 80.0, 70.0, 'scheduled'),
(4, '2024-12-04', '09:00:00', 'Heavy Cargo Route', 1000, 850, 50.0, 40.0, 150.0, 115.0, 'scheduled'),

-- Next week schedules
(2, '2024-12-09', '08:30:00', 'Weekly Main Route', 800, 800, 40.0, 40.0, 120.0, 120.0, 'scheduled'),
(3, '2024-12-10', '11:00:00', 'Mid-week Express', 350, 350, 18.0, 18.0, 60.0, 60.0, 'scheduled'),
(1, '2024-12-11', '15:30:00', 'Priority Delivery Route', 500, 500, 25.0, 25.0, 80.0, 80.0, 'scheduled');

-- Insert arrival stations
INSERT INTO arrival_station (train_session_id, station_name, arrival_time, departure_time, platform_number, station_city, is_final_destination) VALUES
-- For train_session_id 1
(1, 'Colombo Central', '08:00:00', '08:15:00', 'A1', 'Colombo', FALSE),
(1, 'Kandy Railway Station', '10:30:00', '10:45:00', 'B2', 'Kandy', FALSE),
(1, 'Galle Railway Station', '13:15:00', NULL, 'C1', 'Galle', TRUE),

-- For train_session_id 2
(2, 'Colombo Central', '14:00:00', '14:20:00', 'A2', 'Colombo', FALSE),
(2, 'Kurunegala Junction', '16:45:00', '17:00:00', 'D1', 'Kurunegala', FALSE),
(2, 'Anuradhapura Station', '19:30:00', NULL, 'E1', 'Anuradhapura', TRUE);

-- Insert trucks
INSERT INTO truck (store_name, license_plate, truck_model, capacity, max_weight, max_volume, fuel_type, fuel_efficiency, operational_cost_per_km, status, purchase_date, last_maintenance, next_maintenance, mileage) VALUES
-- Colombo Main trucks
('Colombo Main', 'CAB-1234', 'Isuzu NPR', 150, 3500.00, 25.00, 'diesel', 8.5, 45.00, 'active', '2023-02-15', '2024-10-15', '2025-01-15', 45000),
('Colombo Main', 'CAB-5678', 'Mitsubishi Canter', 120, 2800.00, 20.00, 'diesel', 9.2, 42.00, 'active', '2023-05-20', '2024-11-20', '2025-02-20', 38000),
('Colombo Main', 'CAB-9012', 'Tata Ultra', 180, 4200.00, 30.00, 'diesel', 7.8, 48.00, 'active', '2022-11-10', '2024-09-10', '2024-12-10', 62000),

-- Kandy Branch trucks
('Kandy Branch', 'CAK-2345', 'Isuzu ELF', 100, 2500.00, 18.00, 'diesel', 10.5, 38.00, 'active', '2023-03-08', '2024-10-08', '2025-01-08', 32000),
('Kandy Branch', 'CAK-6789', 'Mitsubishi Fuso', 130, 3200.00, 22.00, 'diesel', 8.8, 43.00, 'active', '2023-07-12', '2024-12-12', '2025-03-12', 28000),

-- Galle Branch trucks
('Galle Branch', 'CAG-3456', 'Isuzu NPR', 140, 3300.00, 24.00, 'diesel', 8.9, 44.00, 'active', '2023-01-25', '2024-09-25', '2024-12-25', 41000),
('Galle Branch', 'CAG-7890', 'Tata Ace', 80, 1800.00, 12.00, 'diesel', 12.0, 35.00, 'active', '2023-09-05', '2024-11-05', '2025-02-05', 18000);

-- =============================================
-- 5. HUMAN RESOURCES DATA
-- =============================================

-- Insert drivers
INSERT INTO driver (store_name, first_name, last_name, email, phone, license_number, license_class, license_expiry, hire_date, hourly_rate, weekly_hours, max_weekly_hours, total_deliveries, rating) VALUES
-- Colombo Main drivers
('Colombo Main', 'Kamal', 'Perera', 'kamal.p@drivers.lk', '+94-77-1111111', 'DL001234567', 'HEAVY', '2026-03-15', '2023-01-15', 1800.00, 35.5, 40.00, 145, 4.8),
('Colombo Main', 'Nimal', 'Silva', 'nimal.s@drivers.lk', '+94-77-2222222', 'DL002345678', 'HEAVY', '2025-11-20', '2023-02-20', 1750.00, 38.0, 40.00, 128, 4.6),
('Colombo Main', 'Sunil', 'Fernando', 'sunil.f@drivers.lk', '+94-77-3333333', 'DL003456789', 'HEAVY', '2026-07-10', '2023-03-10', 1850.00, 32.5, 40.00, 162, 4.9),

-- Kandy Branch drivers
('Kandy Branch', 'Prasad', 'Wickramasinghe', 'prasad.w@drivers.lk', '+94-77-4444444', 'DL004567890', 'HEAVY', '2026-01-08', '2023-04-08', 1700.00, 36.0, 40.00, 89, 4.7),
('Kandy Branch', 'Chaminda', 'Rajapaksa', 'chaminda.r@drivers.lk', '+94-77-5555555', 'DL005678901', 'HEAVY', '2025-09-12', '2023-05-12', 1725.00, 34.5, 40.00, 96, 4.5),

-- Galle Branch drivers
('Galle Branch', 'Ruwan', 'Jayasuriya', 'ruwan.j@drivers.lk', '+94-77-6666666', 'DL006789012', 'HEAVY', '2026-05-25', '2023-06-25', 1680.00, 37.0, 40.00, 72, 4.4),
('Galle Branch', 'Asanka', 'Mendis', 'asanka.m@drivers.lk', '+94-77-7777777', 'DL007890123', 'LIGHT', '2025-12-05', '2023-07-05', 1600.00, 35.0, 40.00, 65, 4.6);

-- Insert driver assistants
INSERT INTO driver_assistant (store_name, first_name, last_name, email, phone, hire_date, hourly_rate, weekly_hours, max_weekly_hours, certification, total_assists) VALUES
-- Colombo Main assistants
('Colombo Main', 'Lasith', 'Kumara', 'lasith.k@assistants.lk', '+94-76-1111111', '2023-02-01', 1200.00, 45.0, 60.00, 'Cargo Handling', 145),
('Colombo Main', 'Dinesh', 'Pathirana', 'dinesh.p@assistants.lk', '+94-76-2222222', '2023-03-15', 1250.00, 42.5, 60.00, 'Safety & Security', 128),

-- Kandy Branch assistants
('Kandy Branch', 'Nuwan', 'Senanayake', 'nuwan.s@assistants.lk', '+94-76-3333333', '2023-04-20', 1180.00, 48.0, 60.00, 'Cargo Handling', 89),

-- Galle Branch assistants
('Galle Branch', 'Thilina', 'Bandara', 'thilina.b@assistants.lk', '+94-76-4444444', '2023-05-10', 1220.00, 44.5, 60.00, 'First Aid', 72);

-- Insert truck schedules
INSERT INTO truck_schedule (truck_id, driver_id, driver_assistant_id, route_id, scheduled_date, start_time, estimated_end_time, total_capacity, available_capacity, total_weight_capacity, available_weight, status) VALUES
-- Current week schedules
(1, 1, 1, 1, '2024-12-02', '09:00:00', '09:45:00', 150, 120, 3500.00, 2800.00, 'scheduled'),
(2, 2, 2, 2, '2024-12-02', '14:00:00', '15:00:00', 120, 100, 2800.00, 2300.00, 'scheduled'),
(3, 3, NULL, 3, '2024-12-03', '10:30:00', '12:00:00', 180, 150, 4200.00, 3500.00, 'scheduled'),
(4, 4, 3, 6, '2024-12-03', '08:00:00', '08:30:00', 100, 85, 2500.00, 2100.00, 'scheduled'),
(5, 5, NULL, 7, '2024-12-04', '11:00:00', '12:15:00', 130, 110, 3200.00, 2700.00, 'scheduled');

-- =============================================
-- 6. ORDER DATA
-- =============================================

-- Insert some sample orders
INSERT INTO order_table (customer_id, route_id, delivery_date, status, total_items, total_weight, total_volume, subtotal, discount_amount, shipping_cost, total_amount, payment_status, special_instructions) VALUES
(1, 1, '2024-12-15', 'confirmed', 3, 1.18, 0.007, 195500.00, 0.00, 420.00, 195920.00, 'paid', 'Handle with care - fragile items'),
(2, 2, '2024-12-18', 'confirmed', 2, 0.45, 0.003, 48500.00, 0.00, 480.00, 48980.00, 'paid', 'Deliver during office hours'),
(3, 3, '2024-12-20', 'pending', 5, 2.3, 0.015, 42500.00, 2125.00, 650.00, 41025.00, 'pending', 'Retail customer - bulk order'),
(4, 4, '2024-12-22', 'confirmed', 10, 8.5, 0.045, 185000.00, 27750.00, 1200.00, 158450.00, 'paid', 'Wholesale delivery - priority');

-- Insert order items
INSERT INTO order_items (order_id, item_id, quantity, unit_price, discount_rate, line_total, weight_per_unit, volume_per_unit, total_weight, total_volume) VALUES
-- Order 1 items (John Doe)
(1, 1, 1, 145000.00, 0.00, 145000.00, 0.2, 0.001, 0.2, 0.001),
(1, 4, 1, 45000.00, 0.00, 45000.00, 0.25, 0.002, 0.25, 0.002),
(1, 8, 1, 18500.00, 0.00, 18500.00, 4.5, 0.03, 4.5, 0.03),

-- Order 2 items (Jane Smith)
(2, 10, 2, 15500.00, 0.00, 31000.00, 0.8, 0.005, 1.6, 0.01),
(2, 11, 5, 3500.00, 0.00, 17500.00, 0.2, 0.001, 1.0, 0.005),

-- Order 3 items (Retailer A)
(3, 14, 10, 2800.00, 5.00, 26600.00, 1.5, 0.006, 15.0, 0.06),
(3, 15, 5, 4500.00, 5.00, 21375.00, 1.2, 0.01, 6.0, 0.05),

-- Order 4 items (Wholesale B)
(4, 6, 2, 95000.00, 15.00, 161500.00, 65.0, 0.6, 130.0, 1.2),
(4, 7, 1, 75000.00, 15.00, 63750.00, 68.0, 0.5, 68.0, 0.5);

-- Insert some cart items (current shopping carts)
INSERT INTO cart (customer_id, item_id, quantity, added_date) VALUES
(1, 12, 2, '2024-11-28 14:30:00'),
(1, 13, 1, '2024-11-29 10:15:00'),
(2, 3, 1, '2024-11-29 16:45:00'),
(2, 5, 1, '2024-11-30 09:20:00'),
(3, 9, 3, '2024-11-30 11:30:00'),
(3, 10, 5, '2024-11-30 11:35:00');

-- =============================================
-- 7. ASSIGNMENT DATA
-- =============================================

-- Insert order to train assignments
INSERT INTO order_train_schedule (order_id, train_session_id, assigned_weight, assigned_volume, assigned_items, loading_status, assignment_date) VALUES
(1, 1, 5.05, 0.033, 3, 'pending', '2024-11-30 10:00:00'),
(2, 1, 2.6, 0.015, 7, 'pending', '2024-11-30 10:15:00'),
(4, 2, 198.0, 1.7, 3, 'loaded', '2024-11-30 11:00:00');

-- Insert order to truck assignments
INSERT INTO order_truck_schedule (order_id, truck_session_id, assigned_weight, assigned_volume, assigned_items, delivery_status, assignment_date) VALUES
(1, 1, 5.05, 0.033, 3, 'pending', '2024-12-01 08:00:00'),
(2, 2, 2.6, 0.015, 7, 'pending', '2024-12-01 08:30:00');

-- =============================================
-- 8. AUDIT AND PERFORMANCE DATA
-- =============================================

-- Insert some audit log entries
INSERT INTO audit_log (table_name, operation, record_id, old_values, new_values, user_name, timestamp, ip_address) VALUES
('order_table', 'INSERT', '1', NULL, '{"customer_id": 1, "status": "pending"}', 'john_doe', '2024-11-25 10:30:00', '192.168.1.100'),
('order_table', 'UPDATE', '1', '{"status": "pending"}', '{"status": "confirmed"}', 'sm_colombo', '2024-11-25 14:15:00', '192.168.1.101'),
('users', 'UPDATE', 'john_doe', '{"last_login": null}', '{"last_login": "2024-11-30 09:00:00"}', 'john_doe', '2024-11-30 09:00:00', '192.168.1.100');

-- Insert performance metrics
INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, category, recorded_date, recorded_time) VALUES
('orders_created', 4, 'count', 'orders', '2024-11-30', '23:59:59'),
('total_revenue', 444375.00, 'LKR', 'revenue', '2024-11-30', '23:59:59'),
('avg_order_value', 111093.75, 'LKR', 'revenue', '2024-11-30', '23:59:59'),
('train_utilization', 75.5, 'percentage', 'logistics', '2024-11-30', '18:00:00'),
('truck_utilization', 68.2, 'percentage', 'logistics', '2024-11-30', '18:00:00'),
('inventory_turnover', 12.5, 'ratio', 'inventory', '2024-11-30', '23:59:59');

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- =============================================
-- 9. VERIFICATION QUERIES
-- =============================================

-- Verify data insertion
SELECT 'Data insertion completed successfully!' as Status;

-- Summary statistics
SELECT 
    'Database Summary' as Info,
    (SELECT COUNT(*) FROM users) as Total_Users,
    (SELECT COUNT(*) FROM customers) as Total_Customers,
    (SELECT COUNT(*) FROM items) as Total_Items,
    (SELECT COUNT(*) FROM order_table) as Total_Orders,
    (SELECT COUNT(*) FROM train) as Total_Trains,
    (SELECT COUNT(*) FROM truck) as Total_Trucks,
    (SELECT COUNT(*) FROM driver) as Total_Drivers;

-- Inventory summary by store
SELECT 
    store_name,
    COUNT(*) as items_count,
    SUM(quantity_available) as total_available,
    SUM(quantity_reserved) as total_reserved,
    ROUND(SUM(quantity_available * cost_per_unit), 2) as inventory_value
FROM inventory
GROUP BY store_name;

-- Order status summary
SELECT 
    status,
    COUNT(*) as order_count,
    ROUND(SUM(total_amount), 2) as total_value
FROM order_table
GROUP BY status
ORDER BY order_count DESC;

COMMIT;