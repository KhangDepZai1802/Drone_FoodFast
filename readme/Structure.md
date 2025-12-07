# 📁 Cấu trúc Project hoàn chỉnh

## Cấu trúc thư mục

```
drone-delivery/
│
├── .env                          # Environment variables
├── .gitignore                    # Git ignore file
├── docker-compose.yml            # Docker Compose chính (Production)
├── docker-compose.dev.yml        # Docker Compose cho Development
├── init-db.sql                   # Database initialization script
├── README.md                     # Tài liệu chính
├── QUICKSTART.md                 # Hướng dẫn nhanh
├── PROJECT_STRUCTURE.md          # File này
│
├── setup.bat                     # Setup tự động (Windows)
├── start.bat                     # Khởi động nhanh
├── stop.bat                      # Dừng services
├── test-api.bat                  # Test APIs và tạo data mẫu
├── Makefile.ps1                  # PowerShell commands
│
├── user_service/                 # USER MICROSERVICE
│   ├── main.py                   # FastAPI app
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # Docker image definition
│
├── product_service/              # PRODUCT MICROSERVICE
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── order_service/                # ORDER MICROSERVICE
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── payment_service/              # PAYMENT MICROSERVICE
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                     # FRONTEND
│   ├── index.html               # Main HTML
│   ├── style.css                # Styles
│   ├── app.js                   # JavaScript logic
│   └── Dockerfile               # Nginx container
│
└── nginx/                        # API GATEWAY
    ├── nginx.conf               # Nginx configuration
    └── Dockerfile               # Nginx image

```

## Chi tiết từng file

### Root Level Files

#### `.env`
```env
# Database
DB_SERVER=sqlserver
DB_PASSWORD=YourStrong@Passw0rd

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Service URLs
USER_SERVICE_URL=http://user_service:8000
PRODUCT_SERVICE_URL=http://product_service:8000
ORDER_SERVICE_URL=http://order_service:8000
PAYMENT_SERVICE_URL=http://payment_service:8000
```

#### `docker-compose.yml`
- Định nghĩa 6 services: sqlserver, user, product, order, payment, frontend
- Network configuration
- Volume mapping
- Health checks
- Port mappings

#### `setup.bat`
- Check Docker installation
- Verify project structure
- Build all images
- Start services
- Show access URLs

### User Service

**Port:** 8001

**Chức năng:**
- Đăng ký user (customer, restaurant, admin)
- Đăng nhập (JWT token)
- Quản lý profile
- Authentication & Authorization

**Endpoints:**
- POST /register
- POST /token
- GET /users/me
- PUT /users/me
- GET /users/{id}
- GET /restaurants

**Database Tables:**
- users (id, email, username, password, role, etc.)

### Product Service

**Port:** 8002

**Chức năng:**
- CRUD products/món ăn
- Filter by restaurant, category
- Manage availability

**Endpoints:**
- GET /products
- POST /products
- GET /products/{id}
- PUT /products/{id}
- DELETE /products/{id}
- GET /products/restaurant/{id}

**Database Tables:**
- products (id, restaurant_id, name, price, etc.)

### Order Service

**Port:** 8003

**Chức năng:**
- Tạo đơn hàng
- Quản lý order items
- Assign drone tự động
- Update order status

**Endpoints:**
- GET /orders
- POST /orders
- GET /orders/{id}
- PUT /orders/{id}/status
- GET /drones
- POST /drones

**Database Tables:**
- orders (id, customer_id, restaurant_id, status, etc.)
- order_items (id, order_id, product_id, quantity, etc.)
- drones (id, name, status, battery_level, etc.)

### Payment Service

**Port:** 8004

**Chức năng:**
- Xử lý thanh toán
- Payment simulation
- Transaction history
- Refund processing

**Endpoints:**
- GET /payments
- POST /payments
- GET /payments/{id}
- GET /payments/order/{id}
- PUT /payments/{id}/status
- POST /payments/{id}/refund

**Database Tables:**
- payments (id, order_id, amount, method, status, etc.)

### Frontend

**Port:** 3000

**Technology:** HTML, CSS, Vanilla JavaScript

**Pages:**
- Home
- Login/Register
- Restaurants list
- Products/Menu
- Cart & Checkout
- Orders history
- Drones status

**Features:**
- Responsive design
- JWT authentication
- Real-time cart updates
- Order tracking

### Nginx API Gateway

**Port:** 80

**Chức năng:**
- Reverse proxy cho tất cả services
- Rate limiting
- CORS handling
- Load balancing ready

**Routes:**
- / → Frontend
- /api/users/* → User Service
- /api/products/* → Product Service
- /api/orders/* → Order Service
- /api/payments/* → Payment Service

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INT PRIMARY KEY IDENTITY(1,1),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    address VARCHAR(500),
    role VARCHAR(20) DEFAULT 'customer',
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    restaurant_name VARCHAR(255),
    restaurant_description VARCHAR(1000)
);
```

### Products Table
```sql
CREATE TABLE products (
    id INT PRIMARY KEY IDENTITY(1,1),
    restaurant_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price FLOAT NOT NULL,
    image_url VARCHAR(500),
    category VARCHAR(100),
    is_available BIT DEFAULT 1,
    preparation_time INT DEFAULT 15,
    created_at DATETIME DEFAULT GETDATE()
);
```

### Orders Table
```sql
CREATE TABLE orders (
    id INT PRIMARY KEY IDENTITY(1,1),
    customer_id INT NOT NULL,
    restaurant_id INT NOT NULL,
    total_amount FLOAT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    delivery_address VARCHAR(500) NOT NULL,
    delivery_lat FLOAT,
    delivery_lng FLOAT,
    drone_id INT,
    estimated_delivery_time INT,
    notes TEXT,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
```

### Order Items Table
```sql
CREATE TABLE order_items (
    id INT PRIMARY KEY IDENTITY(1,1),
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    price FLOAT NOT NULL
);
```

### Drones Table
```sql
CREATE TABLE drones (
    id INT PRIMARY KEY IDENTITY(1,1),
    name VARCHAR(100) NOT NULL,
    model VARCHAR(100),
    status VARCHAR(20) DEFAULT 'idle',
    battery_level FLOAT DEFAULT 100.0,
    max_payload FLOAT DEFAULT 5.0,
    current_lat FLOAT,
    current_lng FLOAT,
    created_at DATETIME DEFAULT GETDATE()
);
```

### Payments Table
```sql
CREATE TABLE payments (
    id INT PRIMARY KEY IDENTITY(1,1),
    order_id INT UNIQUE NOT NULL,
    user_id INT NOT NULL,
    amount FLOAT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    transaction_id VARCHAR(255) UNIQUE,
    payment_details VARCHAR(500),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
```

## Service Communication Flow

### Đặt hàng (Create Order):
```
Frontend → Order Service → User Service (verify token)
                        → Product Service (get product info)
                        → Payment Service (process payment)
                        → Drone Assignment
```

### Authentication Flow:
```
Frontend → User Service (login)
       ← JWT Token
       
Frontend → Any Service (with token)
       → User Service (verify token)
       ← User info
       ← Response
```

## Environment Variables

### User Service
```
DATABASE_URL=mssql+pyodbc://...
JWT_SECRET=...
JWT_ALGORITHM=HS256
SERVICE_NAME=user_service
```

### Product Service
```
DATABASE_URL=mssql+pyodbc://...
JWT_SECRET=...
USER_SERVICE_URL=http://user_service:8000
SERVICE_NAME=product_service
```

### Order Service
```
DATABASE_URL=mssql+pyodbc://...
JWT_SECRET=...
USER_SERVICE_URL=http://user_service:8000
PRODUCT_SERVICE_URL=http://product_service:8000
PAYMENT_SERVICE_URL=http://payment_service:8000
SERVICE_NAME=order_service
```

### Payment Service
```
DATABASE_URL=mssql+pyodbc://...
JWT_SECRET=...
USER_SERVICE_URL=http://user_service:8000
ORDER_SERVICE_URL=http://order_service:8000
SERVICE_NAME=payment_service
```

## Docker Networks

**Network Name:** `drone_network`

**Connected Services:**
- sqlserver (database)
- user_service
- product_service
- order_service
- payment_service
- frontend
- nginx (gateway)

All services can communicate using service names as hostnames.

## Docker Volumes

**Volume Name:** `sqlserver_data`

**Purpose:** Persist SQL Server database data

**Location:** Docker managed volume

## Port Mapping

| Service | Internal Port | External Port | Access URL |
|---------|--------------|---------------|------------|
| SQL Server | 1433 | 1433 | localhost:1433 |
| User Service | 8000 | 8001 | localhost:8001 |
| Product Service | 8000 | 8002 | localhost:8002 |
| Order Service | 8000 | 8003 | localhost:8003 |
| Payment Service | 8000 | 8004 | localhost:8004 |
| Frontend | 80 | 3000 | localhost:3000 |
| Nginx Gateway | 80 | 80 | localhost:80 |

## Health Checks

All services have health checks configured:

**Interval:** 30s  
**Timeout:** 10s  
**Retries:** 3  
**Start Period:** 40s

**Check Method:** HTTP GET to service root endpoint

## Security Features

### 1. JWT Authentication
- Token-based authentication
- 30 minutes expiration
- HS256 algorithm
- Secure token storage

### 2. Password Security
- Bcrypt hashing
- Salt rounds: 12
- Never stored in plain text

### 3. API Protection
- Bearer token required
- Token verification on each request
- Role-based access control

### 4. Database Security
- Encrypted connection (TLS)
- Strong SA password
- Connection pooling
- Parameterized queries (SQLAlchemy ORM)

### 5. CORS Configuration
- Configured for all services
- Allow credentials
- Specific origins in production

### 6. Rate Limiting (Nginx)
- API endpoints: 100 req/min
- Auth endpoints: 20 req/min
- Burst allowance configured

## Development vs Production

### Development (`docker-compose.dev.yml`)
- Hot reload enabled
- Debug mode on
- Exposed ports for debugging
- Volume mounting for code changes
- Simpler passwords

### Production (`docker-compose.yml`)
- Optimized builds
- Health checks enabled
- Restart policies
- Strong passwords
- Rate limiting
- API Gateway active

## Common Commands

### Start Everything
```bash
docker-compose up -d
```

### Build and Start
```bash
docker-compose up --build -d
```

### Stop Everything
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f
docker-compose logs -f user_service
```

### Restart Service
```bash
docker-compose restart user_service
```

### Check Status
```bash
docker-compose ps
```

### Clean Everything
```bash
docker-compose down -v --rmi all
```

### Access Database
```bash
docker exec -it drone_delivery_db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P YourStrong@Passw0rd
```

## Testing

### Manual API Testing
Use Swagger UI at each service:
- http://localhost:8001/docs
- http://localhost:8002/docs
- http://localhost:8003/docs
- http://localhost:8004/docs

### Automated Testing
Run `test-api.bat` to:
- Test all service endpoints
- Create sample users
- Create sample products
- Verify connectivity

## Monitoring

### View Container Stats
```bash
docker stats
```

### Check Health
```bash
docker inspect --format='{{.State.Health.Status}}' user_service
```

### Database Monitoring
Connect with SQL Server Management Studio or Azure Data Studio

## Troubleshooting

### Service won't start
1. Check logs: `docker-compose logs [service_name]`
2. Verify all files exist
3. Check port conflicts
4. Restart Docker Desktop

### Database connection error
1. Wait for database to be fully ready
2. Check SQL Server is healthy
3. Verify connection string
4. Restart database: `docker-compose restart sqlserver`

### Frontend can't connect to backend
1. Check all services are running
2. Verify CORS configuration
3. Check browser console for errors
4. Test API endpoints directly

## Performance Tips

1. **Build Cache**: Use `--build` only when code changes
2. **Resource Allocation**: Increase Docker Desktop memory to 4GB+
3. **Volume Performance**: Use named volumes for better performance
4. **Network Optimization**: Keep all services on same network
5. **Database Indexing**: Indexes already on foreign keys and frequently queried fields

---

**Note:** This is a complete microservices architecture suitable for a Software Engineering university project.