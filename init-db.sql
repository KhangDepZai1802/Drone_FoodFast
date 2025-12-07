/* SCRIPT KHỞI TẠO DATABASES VÀ DỮ LIỆU MẪU (REALISTIC DATA)
   HỆ THỐNG: DRONE DELIVERY MICROSERVICES
   Pass mặc định cho tất cả user: 123456
   Hash: $2b$12$49h7Uk7BWuTkmo/l7PWj0uJrLFVg86SoeT.X.QGEB8hj5GsS2/aVq
*/

USE master;
GO

-- ====================================================
-- 1. USER SERVICE (Database: UserDB)
-- ====================================================
IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = 'UserDB') BEGIN CREATE DATABASE UserDB; END
GO
USE UserDB;
GO

-- Reset Tables
IF OBJECT_ID('users', 'U') IS NOT NULL DROP TABLE users;

CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name NVARCHAR(255),
    phone VARCHAR(20),
    address NVARCHAR(500),
    role VARCHAR(20) DEFAULT 'customer',
    is_active INT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    -- Fields riêng cho Restaurant
    restaurant_name NVARCHAR(255),
    restaurant_description NVARCHAR(MAX),
    restaurant_image VARCHAR(500),
    city NVARCHAR(100),
    status VARCHAR(20) DEFAULT 'active'
);

-- SEED DATA: USERS & RESTAURANTS
INSERT INTO users (username, email, hashed_password, full_name, phone, address, role, restaurant_name, restaurant_description, restaurant_image, city) VALUES 
-- 1. Admin
('admin', 'admin@dronefood.com', '$2b$12$PxVVMg.DNaTcjj4XMk4Dd.Av5AMIAYs5R17mkOYNou/AuMLY2c87W', 'System Administrator', '0909000000', 'HQ DroneFood', 'admin', NULL, NULL, NULL, NULL),

-- 2. Restaurant: KFC
('kfc_vietnam', 'contact@kfc.com.vn', '$2b$12$PxVVMg.DNaTcjj4XMk4Dd.Av5AMIAYs5R17mkOYNou/AuMLY2c87W', 'KFC Manager', '19006886', N'Lê Lai, Quận 1', 'restaurant', 
 N'KFC Vietnam', N'Gà rán Kentucky trứ danh thế giới. Vị ngon trên từng ngón tay.', 
 'https://static.kfcvietnam.com.vn/images/content/home/carousel/3.jpg', N'Hồ Chí Minh'),

-- 3. Restaurant: Phúc Long
('phuclong', 'info@phuclong.com.vn', '$2b$12$PxVVMg.DNaTcjj4XMk4Dd.Av5AMIAYs5R17mkOYNou/AuMLY2c87W', 'Phuc Long Manager', '02862630377', N'42 Ngô Đức Kế, Quận 1', 'restaurant', 
 N'Phúc Long Tea & Coffee', N'Thương hiệu trà và cà phê thượng hạng từ năm 1968.', 
 'https://phuclong.com.vn/uploads/store/0530467772637255d642b58872658a2d.jpg', N'Hồ Chí Minh'),

-- 4. Restaurant: Pizza 4P's
('pizza4ps', 'booking@pizza4ps.com', '$2b$12$PxVVMg.DNaTcjj4XMk4Dd.Av5AMIAYs5R17mkOYNou/AuMLY2c87W', '4Ps Manager', '19006043', N'8 Thủ Khoa Huân, Quận 1', 'restaurant', 
 N'Pizza 4P''s', N'Pizza kiểu Nhật với phô mai tự làm. Mang lại sự an nhiên cho tâm hồn.', 
 'https://pizza4ps.com/wp-content/uploads/2021/08/Pizza-4Ps-Ben-Thanh-1.jpg', N'Hồ Chí Minh'),

-- 5. Restaurant: Cơm Tấm Cali
('comtamcali', 'lienhe@comtamcali.com', '$2b$12$PxVVMg.DNaTcjj4XMk4Dd.Av5AMIAYs5R17mkOYNou/AuMLY2c87W', 'Cali Manager', '02839252222', N'236 Lê Thánh Tôn, Quận 1', 'restaurant', 
 N'Cơm Tấm Cali', N'Hệ thống cơm tấm văn phòng sạch sẽ, ngon miệng, chuẩn vị Sài Gòn.', 
 'https://comtamcali.com/wp-content/uploads/2020/07/slide-1.jpg', N'Hồ Chí Minh'),

-- 6. Restaurant: Phở Hùng
('phohung', 'info@phohung.vn', '$2b$12$PxVVMg.DNaTcjj4XMk4Dd.Av5AMIAYs5R17mkOYNou/AuMLY2c87W', 'Pho Hung Owner', '02439363636', N'24 Láng Hạ, Đống Đa', 'restaurant', 
 N'Phở Hùng', N'Hương vị phở truyền thống Hà Nội, nước dùng đậm đà.', 
 'https://cdn.tgdd.vn/Files/2022/01/25/1412806/pho-hung-huong-vi-pho-truyen-thong-giua-long-sai-gon-202201250953187289.jpg', N'Hà Nội'),

-- 7. Customers
('khangdepzai', 'khang@gmail.com', '$2b$12$PxVVMg.DNaTcjj4XMk4Dd.Av5AMIAYs5R17mkOYNou/AuMLY2c87W', N'Lê Khang', '0987654321', N'Landmark 81, Bình Thạnh', 'customer', NULL, NULL, NULL, N'Hồ Chí Minh'),
('thanhhang', 'hang@gmail.com', '$2b$12$PxVVMg.DNaTcjj4XMk4Dd.Av5AMIAYs5R17mkOYNou/AuMLY2c87W', N'Phạm Thanh Hằng', '0912345678', N'Times City, Hai Bà Trưng', 'customer', NULL, NULL, NULL, N'Hà Nội'),
('elonmusk', 'elon@tesla.com', '$2b$12$PxVVMg.DNaTcjj4XMk4Dd.Av5AMIAYs5R17mkOYNou/AuMLY2c87W', N'Elon Musk', '0999999999', N'Bitexco Financial Tower', 'customer', NULL, NULL, NULL, N'Hồ Chí Minh');
GO

-- ====================================================
-- 2. PRODUCT SERVICE (Database: ProductDB)
-- ====================================================
IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = 'ProductDB') BEGIN CREATE DATABASE ProductDB; END
GO
USE ProductDB;
GO

IF OBJECT_ID('products', 'U') IS NOT NULL DROP TABLE products;
CREATE TABLE products (
    id INT IDENTITY(1,1) PRIMARY KEY,
    restaurant_id INT NOT NULL, 
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    price FLOAT NOT NULL,
    original_price FLOAT,
    image_url VARCHAR(500),
    category NVARCHAR(100),
    is_available INT DEFAULT 1,
    stock_quantity INT DEFAULT 100,
    weight FLOAT DEFAULT 0.5,
    preparation_time INT DEFAULT 15,
    options NVARCHAR(MAX), -- [FIX] Added for JSON options
    created_at DATETIME DEFAULT GETDATE()
);

-- SEED DATA: PRODUCTS
INSERT INTO products (restaurant_id, name, description, price, original_price, image_url, category, weight) VALUES 
-- KFC (ID: 2)
(2, N'Combo Gà Rán Cơ Bản', N'2 Miếng Gà Giòn Cay + 1 Khoai Tây Chiên (Vừa) + 1 Pepsi', 89000, 105000, 'https://static.kfcvietnam.com.vn/images/items/lg/Combo-Ga-Ran-A.jpg', N'Combo', 0.8),
(2, N'Gà Popcorn (Vừa)', N'Gà viên chiên giòn rụm, lắc phô mai.', 45000, 45000, 'https://static.kfcvietnam.com.vn/images/items/lg/Popcorn-Vua.jpg', N'Gà Rán', 0.3),
(2, N'Burger Zinger', N'Bánh mì kẹp phi lê gà giòn cay độc quyền.', 59000, 59000, 'https://static.kfcvietnam.com.vn/images/items/lg/Burger-Zinger.jpg', N'Burger', 0.4),
(2, N'Cơm Gà Giòn Cay', N'Cơm trắng ăn kèm đùi gà giòn cay và xốt.', 49000, 49000, 'https://static.kfcvietnam.com.vn/images/items/lg/Com-Ga-Gion-Cay.jpg', N'Cơm', 0.5),

-- Phúc Long (ID: 3)
(3, N'Trà Sữa Phúc Long', N'Vị trà đậm đà đặc trưng, kết hợp sữa béo ngậy.', 55000, 55000, 'https://phuclong.com.vn/uploads/dish/062d989359a686-trasuaphuclong.png', N'Trà Sữa', 0.5),
(3, N'Trà Đào Cam Sả', N'Best seller. Trà đen ủ lạnh với đào miếng giòn ngọt.', 60000, 60000, 'https://phuclong.com.vn/uploads/dish/64a6c406981881-tradaocamsa.png', N'Trà Trái Cây', 0.5),
(3, N'Cà Phê Sữa Đá', N'Cà phê phin truyền thống Việt Nam.', 45000, 45000, 'https://phuclong.com.vn/uploads/dish/d56545129995fd-caphesuada.png', N'Cà Phê', 0.4),

-- Pizza 4P's (ID: 4)
(4, N'Pizza 4 Cheese Honey', N'Pizza 4 loại phô mai kèm mật ong rừng. Món đặc trưng nhất.', 280000, 280000, 'https://delivery.pizza4ps.com/wp-content/uploads/2021/08/4-Cheese-Honey.jpg', N'Pizza', 0.6),
(4, N'Mỳ Cua Sốt Kem', N'Mỳ Ý sốt kem cà chua với thịt cua bể tươi.', 195000, 195000, 'https://delivery.pizza4ps.com/wp-content/uploads/2021/08/Crab-Tomato-Cream.jpg', N'Pasta', 0.5),
(4, N'Salad Burrata kèm Trái Cây', N'Phô mai Burrata tươi làm thủ công kèm trái cây nhiệt đới.', 165000, 165000, 'https://delivery.pizza4ps.com/wp-content/uploads/2021/08/Burrata-Fruit-Salad.jpg', N'Salad', 0.4),

-- Cơm Tấm Cali (ID: 5)
(5, N'Cơm Sườn Bì Chả', N'Dĩa cơm đầy đủ sườn nướng mật ong, bì thính, chả trứng.', 75000, 85000, 'https://comtamcali.com/wp-content/uploads/2016/06/suon-bi-cha.jpg', N'Cơm Tấm', 0.6),
(5, N'Cơm Ba Rọi Nướng', N'Ba rọi heo nướng muối ớt đậm đà.', 68000, 68000, 'https://comtamcali.com/wp-content/uploads/2016/06/ba-roi-nuong.jpg', N'Cơm Tấm', 0.6),
(5, N'Canh Khổ Qua Nhồi Thịt', N'Canh khổ qua thanh mát, giải nhiệt.', 25000, 25000, 'https://comtamcali.com/wp-content/uploads/2016/06/canh-kho-qua.jpg', N'Canh', 0.3),

-- Phở Hùng (ID: 6)
(6, N'Phở Đặc Biệt', N'Tô lớn: Tái, Nạm, Gầu, Gân, Bò Viên.', 95000, 95000, 'https://phohung.com.vn/wp-content/uploads/2020/08/pho-dac-biet.jpg', N'Phở', 0.8),
(6, N'Phở Tái Lăn', N'Thịt bò xào lăn thơm phức tỏi.', 85000, 85000, 'https://phohung.com.vn/wp-content/uploads/2020/08/pho-tai-lan.jpg', N'Phở', 0.8);
GO

-- ====================================================
-- 3. ORDER SERVICE (Database: OrderDB)
-- ====================================================
IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = 'OrderDB') BEGIN CREATE DATABASE OrderDB; END
GO
USE OrderDB;
GO

IF OBJECT_ID('order_items', 'U') IS NOT NULL DROP TABLE order_items;
IF OBJECT_ID('orders', 'U') IS NOT NULL DROP TABLE orders;
IF OBJECT_ID('drones', 'U') IS NOT NULL DROP TABLE drones;

CREATE TABLE drones (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    model VARCHAR(100),
    status VARCHAR(20) DEFAULT 'idle',
    battery_level FLOAT DEFAULT 100.0,
    max_payload FLOAT DEFAULT 5.0,
    max_distance_km FLOAT DEFAULT 15.0, -- [FIX] Added
    current_lat FLOAT,
    current_lng FLOAT,
    created_at DATETIME DEFAULT GETDATE()
);

CREATE TABLE orders (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    restaurant_id INT NOT NULL,
    total_amount FLOAT NOT NULL,
    total_weight FLOAT DEFAULT 0, -- [FIX] Added
    status VARCHAR(50) DEFAULT 'waiting_confirmation',
    delivery_address NVARCHAR(500) NOT NULL,
    delivery_lat FLOAT,
    delivery_lng FLOAT,
    restaurant_lat FLOAT,
    restaurant_lng FLOAT,
    distance_km FLOAT,
    drone_id INT,
    estimated_delivery_time INT DEFAULT 30,
    rejection_reason NVARCHAR(MAX), -- [FIX] Added
    notes NVARCHAR(MAX), -- [FIX] Added
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

CREATE TABLE order_items (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    product_name NVARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    price FLOAT NOT NULL,
    weight FLOAT DEFAULT 0.5, -- [FIX] Added
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- SEED DATA: DRONES
INSERT INTO drones (name, model, status, battery_level, current_lat, current_lng, max_payload, max_distance_km) VALUES 
(N'Falcon Heavy', 'DJI Matrice 600', 'idle', 100.0, 10.771595, 106.704758, 6.0, 20.0),
(N'Nimbus 2000', 'DJI Mavic 3', 'idle', 78.5, 10.775845, 106.701758, 2.5, 15.0),
(N'Firebolt', 'Custom FPV', 'charging', 12.0, 10.771595, 106.704758, 1.5, 10.0),
(N'Sky Walker', 'Amazon Prime Air Clone', 'maintenance', 0.0, 10.771595, 106.704758, 4.0, 25.0),
(N'Hawk Eye 1', 'DJI Phantom 4', 'idle', 92.0, 10.791595, 106.694758, 3.0, 18.0);

-- SEED DATA: ORDERS
INSERT INTO orders (user_id, restaurant_id, total_amount, total_weight, status, delivery_address, drone_id, created_at) VALUES 
(7, 2, 134000, 1.1, 'delivered', N'Landmark 81, Vinhomes Central Park', 1, DATEADD(hour, -2, GETDATE()));

INSERT INTO order_items (order_id, product_id, product_name, quantity, price, weight) VALUES 
(1, 1, N'Combo Gà Rán Cơ Bản', 1, 89000, 0.8),
(1, 2, N'Gà Popcorn (Vừa)', 1, 45000, 0.3);

INSERT INTO orders (user_id, restaurant_id, total_amount, total_weight, status, delivery_address, drone_id, created_at) VALUES 
(8, 3, 115000, 1.0, 'in_delivery', N'Bitexco Tower, Quận 1', 2, DATEADD(minute, -15, GETDATE()));

INSERT INTO order_items (order_id, product_id, product_name, quantity, price, weight) VALUES 
(2, 5, N'Trà Sữa Phúc Long', 1, 55000, 0.5),
(2, 6, N'Trà Đào Cam Sả', 1, 60000, 0.5);
GO

-- ====================================================
-- 4. PAYMENT SERVICE (Database: PaymentDB)
-- ====================================================
IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = 'PaymentDB') BEGIN CREATE DATABASE PaymentDB; END
GO
USE PaymentDB;
GO

IF OBJECT_ID('payments', 'U') IS NOT NULL DROP TABLE payments;
CREATE TABLE payments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL UNIQUE,
    user_id INT NOT NULL,
    amount FLOAT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    transaction_id VARCHAR(255) UNIQUE,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

-- SEED DATA: PAYMENTS
INSERT INTO payments (order_id, user_id, amount, payment_method, status, transaction_id, created_at) VALUES 
(1, 7, 134000, 'momo', 'completed', 'MOMO123456789', DATEADD(hour, -2, GETDATE())),
(2, 8, 115000, 'credit_card', 'completed', 'VISA987654321', DATEADD(minute, -15, GETDATE()));
GO