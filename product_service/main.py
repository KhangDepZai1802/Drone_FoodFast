from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import shutil
import uuid
import httpx
import time

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL")
UPLOAD_DIR = "static/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Database setup
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# DATABASE MODELS
# ==========================================
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    image_url = Column(String(500))
    category = Column(String(100))
    is_available = Column(Integer, default=1)
    stock_quantity = Column(Integer, default=999)  # [Feature] Tồn kho
    weight = Column(Float, default=0.5)  # [Feature] Trọng lượng
    preparation_time = Column(Integer, default=15)
    options = Column(JSON)  # [Feature] Topping, size
    created_at = Column(DateTime, default=datetime.utcnow)

class RestaurantHours(Base):
    """Bảng giờ mở cửa nhà hàng"""
    __tablename__ = "restaurant_hours"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, nullable=False, unique=True, index=True)
    monday_open = Column(String(5))
    monday_close = Column(String(5))
    tuesday_open = Column(String(5))
    tuesday_close = Column(String(5))
    wednesday_open = Column(String(5))
    wednesday_close = Column(String(5))
    thursday_open = Column(String(5))
    thursday_close = Column(String(5))
    friday_open = Column(String(5))
    friday_close = Column(String(5))
    saturday_open = Column(String(5))
    saturday_close = Column(String(5))
    sunday_open = Column(String(5))
    sunday_close = Column(String(5))
    is_24h = Column(Integer, default=0)

# ==========================================
# PYDANTIC MODELS
# ==========================================
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_available: bool = True
    stock_quantity: int = 999
    weight: float = 0.5
    preparation_time: int = 15
    options: Optional[dict] = None

class ProductCreate(ProductBase):
    pass # restaurant_id sẽ lấy từ token

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_available: Optional[bool] = None
    stock_quantity: Optional[int] = None
    weight: Optional[float] = None
    preparation_time: Optional[int] = None
    options: Optional[dict] = None

class ProductResponse(ProductBase):
    id: int
    restaurant_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class RestaurantHoursCreate(BaseModel):
    restaurant_id: int
    monday_open: Optional[str] = "08:00"
    monday_close: Optional[str] = "22:00"
    tuesday_open: Optional[str] = "08:00"
    tuesday_close: Optional[str] = "22:00"
    wednesday_open: Optional[str] = "08:00"
    wednesday_close: Optional[str] = "22:00"
    thursday_open: Optional[str] = "08:00"
    thursday_close: Optional[str] = "22:00"
    friday_open: Optional[str] = "08:00"
    friday_close: Optional[str] = "22:00"
    saturday_open: Optional[str] = "08:00"
    saturday_close: Optional[str] = "22:00"
    sunday_open: Optional[str] = "08:00"
    sunday_close: Optional[str] = "22:00"
    is_24h: bool = False

# ==========================================
# APP SETUP
# ==========================================
app = FastAPI(title="Product Service", version="2.0.0")

# Cho phép chính xác địa chỉ Frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8003",  
    "http://127.0.0.1:8003",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Mount static files (Chỉ gọi 1 lần)
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Startup event
@app.on_event("startup")
async def startup_event():
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        try:
            Base.metadata.create_all(bind=engine)
            print("✓ Product database tables created successfully")
            break
        except Exception as e:
            retry_count += 1
            print(f"Database connection failed (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(2)

# ==========================================
# HELPERS & AUTH
# ==========================================
async def verify_token(token: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{USER_SERVICE_URL}/verify-token",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

async def get_current_user(authorization: str = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    user_data = await verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_data

def is_restaurant_open(hours: RestaurantHours) -> tuple[bool, str]:
    if hours.is_24h: return True, "Open 24/7"
    now = datetime.now()
    weekday = now.strftime("%A").lower()
    
    open_time_str = getattr(hours, f"{weekday}_open")
    close_time_str = getattr(hours, f"{weekday}_close")
    
    if not open_time_str or not close_time_str:
        return False, "Closed today"
    
    current_time = now.time()
    try:
        open_time = datetime.strptime(open_time_str, "%H:%M").time()
        close_time = datetime.strptime(close_time_str, "%H:%M").time()
        if open_time <= current_time <= close_time:
            return True, f"Open until {close_time_str}"
        return False, f"Opens at {open_time_str}"
    except:
        return True, "Time format error"

# ==========================================
# ROUTES
# ==========================================

@app.get("/")
async def root():
    return {"service": "Product Service", "status": "running", "version": "2.0.0"}

# 1. CREATE PRODUCT (Secure + Features)
@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    preparation_time: int = Form(15),
    is_available: bool = Form(True),
    stock_quantity: int = Form(999),
    weight: float = Form(0.5),
    image: Optional[UploadFile] = File(None),
    authorization: str = Header(None), # [Secure]
    db: Session = Depends(get_db)
):
    # Check quyền nhà hàng
    user = await get_current_user(authorization)
    if user["role"] != "restaurant":
        raise HTTPException(status_code=403, detail="Only restaurants can create products")

    # Xử lý ảnh
    image_path_db = None
    if image:
        try:
            file_extension = image.filename.split(".")[-1]
            file_name = f"{uuid.uuid4()}.{file_extension}"
            file_location = f"{UPLOAD_DIR}/{file_name}"
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            image_path_db = f"/static/images/{file_name}"
        except Exception as e:
            print(f"Error saving image: {e}")

    # Tạo món (Lấy restaurant_id từ Token)
    new_product = Product(
        name=name,
        price=price,
        restaurant_id=user["user_id"], # [Secure]
        description=description,
        category=category,
        preparation_time=preparation_time,
        is_available=1 if is_available else 0,
        stock_quantity=stock_quantity,
        weight=weight,
        image_url=image_path_db
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

# 2. LIST PRODUCTS
@app.get("/products", response_model=List[ProductResponse])
async def list_products(
    restaurant_id: Optional[int] = None,
    category: Optional[str] = None,
    available_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if restaurant_id:
        query = query.filter(Product.restaurant_id == restaurant_id)
    if category:
        query = query.filter(Product.category == category)
    if available_only:
        query = query.filter(Product.is_available == 1, Product.stock_quantity > 0)
    
    products = query.order_by(Product.id).offset(skip).limit(limit).all()
    return products

# 3. GET PRODUCT DETAIL
@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# 4. UPDATE PRODUCT (Secure)
@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    authorization: str = Header(None), # [Secure]
    db: Session = Depends(get_db)
):
    user = await get_current_user(authorization)
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check quyền sở hữu
    if product.restaurant_id != user["user_id"] and user["role"] != "admin":
        raise HTTPException(403, "Permission denied")
    
    for key, value in product_update.dict(exclude_unset=True).items():
        if key == "is_available":
            setattr(product, key, 1 if value else 0)
        else:
            setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

# 5. DELETE PRODUCT (Secure)
@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int, 
    authorization: str = Header(None), # [Secure]
    db: Session = Depends(get_db)
):
    user = await get_current_user(authorization)
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product: raise HTTPException(404, "Product not found")

    # Check quyền sở hữu
    if product.restaurant_id != user["user_id"] and user["role"] != "admin":
        raise HTTPException(403, "Permission denied")

    db.delete(product)
    db.commit()
    return None

# 6. STOCK MANAGEMENT (Internal use mainly)
@app.post("/products/{product_id}/decrease-stock")
async def decrease_stock(product_id: int, quantity: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stock_quantity < quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")
    
    product.stock_quantity -= quantity
    if product.stock_quantity == 0:
        product.is_available = 0
    
    db.commit()
    return {"message": "Stock decreased", "remaining": product.stock_quantity}

# 7. GET BY RESTAURANT
@app.get("/products/restaurant/{restaurant_id}", response_model=List[ProductResponse])
async def get_restaurant_products(restaurant_id: int, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.restaurant_id == restaurant_id).all()
    return products

# 8. HOURS MANAGEMENT
@app.post("/restaurant-hours")
async def set_restaurant_hours(
    hours: RestaurantHoursCreate, 
    authorization: str = Header(None), # [Secure]
    db: Session = Depends(get_db)
):
    user = await get_current_user(authorization)
    # Check ID: Nhà hàng chỉ được sửa giờ của chính mình
    if user["user_id"] != hours.restaurant_id:
        raise HTTPException(403, "Can only update your own hours")

    existing = db.query(RestaurantHours).filter(RestaurantHours.restaurant_id == hours.restaurant_id).first()
    
    if existing:
        for key, value in hours.dict().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_hours = RestaurantHours(**hours.dict())
        db.add(db_hours)
        db.commit()
        db.refresh(db_hours)
        return db_hours

@app.get("/restaurant-hours/{restaurant_id}")
async def get_restaurant_hours(restaurant_id: int, db: Session = Depends(get_db)):
    hours = db.query(RestaurantHours).filter(RestaurantHours.restaurant_id == restaurant_id).first()
    
    if not hours:
        return {"restaurant_id": restaurant_id, "is_open": True, "message": "Always Open", "hours": None}
    
    is_open, message = is_restaurant_open(hours)
    return {
        "restaurant_id": restaurant_id,
        "is_open": is_open,
        "message": message,
        "hours": hours
    }
# --- Thêm đoạn này vào product_service/main.py ---


# 6. GET BY RESTAURANT
@app.get("/products/restaurant/{restaurant_id}", response_model=List[ProductResponse])
async def get_restaurant_products(restaurant_id: int, db: Session = Depends(get_db)):
    """Lấy danh sách món ăn của một nhà hàng cụ thể"""
    products = db.query(Product).filter(Product.restaurant_id == restaurant_id).all()
    return products
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)