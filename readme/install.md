# 🚀 Hướng dẫn cài đặt chi tiết

## Bước 1: Cài đặt Docker Desktop

### Windows 10/11

1. **Kiểm tra yêu cầu hệ thống:**
   - Windows 10 64-bit: Pro, Enterprise, hoặc Education (Build 19041 trở lên)
   - Windows 11 64-bit
   - Bật Hyper-V và Containers Windows features
   - Bật WSL 2

2. **Tải Docker Desktop:**
   - Truy cập: https://www.docker.com/products/docker-desktop
   - Click "Download for Windows"
   - File tải về: ~500MB

3. **Cài đặt:**
   - Chạy file `Docker Desktop Installer.exe`
   - Chọn "Use WSL 2 instead of Hyper-V"
   - Click "Ok" và đợi cài đặt
   - Khởi động lại máy nếu được yêu cầu

4. **Khởi động Docker Desktop:**
   - Mở Docker Desktop từ Start Menu
   - Đợi icon Docker ở system tray (góc dưới phải) chuyển sang màu xanh
   - Khi thấy "Docker Desktop is running" là ok

5. **Verify Installation:**
   ```cmd
   docker --version
   docker-compose --version
   ```

## Bước 2: Tạo thư mục project

```cmd
# Tạo thư mục chính
mkdir drone-delivery
cd drone-delivery

# Tạo các thư mục con
mkdir user_service
mkdir product_service
mkdir order_service
mkdir payment_service
mkdir frontend
mkdir nginx
```

## Bước 3: Copy code vào các file

### 3.1. Root Directory Files

Tạo các files sau ở thư mục `drone-delivery/`:

**File: `.env`**
```env
DB_SERVER=sqlserver
DB_PORT=1433
DB_NAME=DroneDeliveryDB
DB_USER=sa
DB_PASSWORD=YourStrong@Passw0rd

JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-12345678
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

USER_SERVICE_URL=http://user_service:8000
PRODUCT_SERVICE_URL=http://product_service:8000
ORDER_SERVICE_URL=http://order_service:8000
PAYMENT_SERVICE_URL=http://payment_service:8000

ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=*
```

**File: `docker-compose.yml`**
- Copy từ artifact `docker-compose.yml`

**File: `.gitignore`**
- Copy từ artifact `.gitignore`

**File: `setup.bat`**
- Copy từ artifact `setup.bat`

**File: `start.bat`**
- Copy từ artifact `start.bat`

**File: `stop.bat`**
- Copy từ artifact `stop.bat`

**File: `test-api.bat`**
- Copy từ artifact `test-api.bat`

### 3.2. User Service Files

Trong thư mục `user_service/`:

**File: `main.py`**
- Copy từ artifact `user_service/main.py`

**File: `requirements.txt`**
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pyodbc==5.0.1
passlib==1.7.4
bcrypt==4.1.1
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
pydantic[email]==2.5.0
httpx==0.25.2
```

**File: `Dockerfile`**
- Copy từ artifact `user_service/Dockerfile`

### 3.3. Product Service Files

Trong thư mục `product_service/`:

**File: `main.py`**
- Copy từ artifact `product_service/main.py`

**File: `requirements.txt`**
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pyodbc==5.0.1
pydantic==2.5.0
httpx==0.25.2
```

**File: `Dockerfile`**
- Copy từ artifact `product_service/Dockerfile`

### 3.4. Order Service Files

Trong thư mục `order_service/`:

**File: `main.py`**
- Copy từ artifact `order_service/main.py`

**File: `requirements.txt`**
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pyodbc==5.0.1
pydantic==2.5.0
httpx==0.25.2
```

**File: `Dockerfile`**
- Copy từ artifact `order_service/Dockerfile`

### 3.5. Payment Service Files

Trong thư mục `payment_service/`:

**File: `main.py`**
- Copy từ artifact `payment_service/main.py`

**File: `requirements.txt`**
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pyodbc==5.0.1
pydantic==2.5.0
httpx==0.25.2
```

**File: `Dockerfile`**
- Copy từ artifact `payment_service/Dockerfile`

### 3.6. Frontend Files

Trong thư mục `frontend/`:

**File: `index.html`**
- Copy từ artifact `frontend/index.html`

**File: `style.css`**
- Copy từ artifact `frontend/style.css`

**File: `app.js`**
- Copy từ artifact `frontend/app.js`

**File: `Dockerfile`**
```dockerfile
FROM nginx:alpine

COPY index.html /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 3.7. Nginx Files

Trong thư mục `nginx/`:

**File: `nginx.conf`**
- Copy từ artifact `nginx/nginx.conf`

**File: `Dockerfile`**
- Copy từ artifact `nginx/Dockerfile`

## Bước 4: Verify cấu trúc

Cấu trúc thư mục phải như sau:

```
drone-delivery/
├── .env
├── .gitignore
├── docker-compose.yml
├── setup.bat
├── start.bat
├── stop.bat
├── test-api.bat
├── user_service/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── product_service/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── order_service/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── payment_service/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── Dockerfile
└── nginx/
    ├── nginx.conf
    └── Dockerfile
```

## Bước 5: Build và khởi động

### Tự động (Khuyến nghị)

```cmd
setup.bat
```

Script sẽ tự động:
1. ✅ Check Docker
2. ✅ Verify files
3. ✅ Build images
4. ✅ Start services
5. ✅ Show URLs

### Thủ công

```cmd
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Bước 6: Đợi services khởi động

Sau khi chạy `docker-compose up`, đợi khoảng **2-3 phút** để:
- SQL Server khởi động
- Database tables được tạo
- Tất cả services ready

**Kiểm tra status:**
```cmd
docker-compose ps
```

Tất cả services phải có status `Up (healthy)`.

## Bước 7: Tạo dữ liệu mẫu

```cmd
test-api.bat
```

Script sẽ tạo:
- ✅ Customer account
- ✅ Restaurant account  
- ✅ Sample products
- ✅ Sample drones

## Bước 8: Truy cập ứng dụng

### Frontend
```
http://localhost:3000
```

### API Documentation
- User Service: http://localhost:8001/docs
- Product Service: http://localhost:8002/docs
- Order Service: http://localhost:8003/docs
- Payment Service: http://localhost:8004/docs

## Bước 9: Đăng nhập và test

### Tài khoản mẫu

**Customer:**
- Username: `customer1`
- Password: `123456`

**Restaurant:**
- Username: `restaurant1`
- Password: `123456`

### Test flow đầy đủ

1. **Đăng nhập** với customer1
2. **Xem nhà hàng** → Click "Nhà hàng" menu
3. **Chọn nhà hàng** → Click "Xem thực đơn"
4. **Thêm món** vào giỏ hàng
5. **Thanh toán** → Nhập địa chỉ
6. **Xem đơn hàng** → Theo dõi status
7. **Xem drone** → Kiểm tra drone đang giao

## Troubleshooting

### Lỗi: Port already in use

**Giải pháp:**
```cmd
# Stop các container cũ
docker-compose down

# Hoặc thay đổi port trong docker-compose.yml
ports:
  - "8101:8000"  # Thay vì 8001:8000
```

### Lỗi: SQL Server không khởi động

**Giải pháp:**
```cmd
# Xem logs
docker-compose logs sqlserver

# Xóa và tạo lại
docker-compose down -v
docker-compose up -d sqlserver

# Đợi 1 phút rồi start các service khác
docker-compose up -d
```

### Lỗi: Service không healthy

**Giải pháp:**
```cmd
# Check logs của service
docker-compose logs user_service

# Restart service
docker-compose restart user_service

# Nếu vẫn lỗi, rebuild
docker-compose up --build user_service
```

### Lỗi: Frontend không kết nối được backend

**Nguyên nhân:** Services chưa ready hoặc CORS issue

**Giải pháp:**
1. Đợi thêm 1-2 phút
2. Check tất cả services: `docker-compose ps`
3. Test API trực tiếp: http://localhost:8001/docs
4. Check browser console (F12) xem lỗi gì

### Lỗi: Docker Desktop không khởi động

**Giải pháp:**
1. Restart Docker Desktop
2. Nếu vẫn lỗi, restart máy
3. Check Windows services → Docker Desktop Service phải Running
4. Cài lại Docker Desktop nếu cần

## Commands hữu ích

### Xem logs realtime
```cmd
docker-compose logs -f
docker-compose logs -f user_service
```

### Stop tất cả
```cmd
docker-compose down
```

### Restart một service
```cmd
docker-compose restart user_service
```

### Xem resource usage
```cmd
docker stats
```

### Connect vào container
```cmd
docker exec -it user_service bash
```

### Xóa tất cả và bắt đầu lại
```cmd
docker-compose down -v --rmi all
docker-compose up --build -d
```

### Export/Import database

**Export:**
```cmd
docker exec drone_delivery_db /opt/mssql-tools/bin/sqlcmd ^
  -S localhost -U sa -P YourStrong@Passw0rd ^
  -Q "BACKUP DATABASE DroneDeliveryDB TO DISK='/var/opt/mssql/backup.bak'"

docker cp drone_delivery_db:/var/opt/mssql/backup.bak ./backup.bak
```

**Import:**
```cmd
docker cp backup.bak drone_delivery_db:/var/opt/mssql/
docker exec drone_delivery_db /opt/mssql-tools/bin/sqlcmd ^
  -S localhost -U sa -P YourStrong@Passw0rd ^
  -Q "RESTORE DATABASE DroneDeliveryDB FROM DISK='/var/opt/mssql/backup.bak' WITH REPLACE"
```

## Performance Tuning

### Tăng memory cho Docker
1. Mở Docker Desktop
2. Settings → Resources
3. Tăng Memory lên 4GB
4. Tăng CPUs lên 4
5. Apply & Restart

### Tối ưu build time
```cmd
# Build parallel
docker-compose build --parallel

# Cache layers
docker-compose build --no-cache (chỉ khi cần)
```

## Production Deployment

### Sử dụng production config
```cmd
docker-compose -f docker-compose.yml up -d
```

### Thay đổi passwords
1. Edit `.env`
2. Thay đổi `DB_PASSWORD` và `JWT_SECRET_KEY`
3. Rebuild: `docker-compose up --build -d`

### Enable HTTPS
1. Get SSL certificates
2. Update nginx.conf với SSL config
3. Thay port 80 → 443

### Monitoring
- Add Prometheus
- Add Grafana
- Setup alerts

## Next Steps

Sau khi cài đặt thành công:

1. ✅ **Học cách sử dụng:** Xem QUICKSTART.md
2. ✅ **Đọc documentation:** Xem README.md
3. ✅ **Test API:** Dùng Swagger UI
4. ✅ **Customize:** Thay đổi code theo nhu cầu
5. ✅ **Deploy:** Production deployment guide

## Support

Nếu gặp vấn đề:
1. Check logs: `docker-compose logs -f`
2. Verify structure: Đối chiếu với PROJECT_STRUCTURE.md
3. Check Docker Desktop is running
4. Restart Docker Desktop
5. Clean và rebuild: `docker-compose down -v && docker-compose up --build`

---

**Chúc bạn cài đặt thành công! 🎉**

Có vấn đề gì cứ hỏi nhé!