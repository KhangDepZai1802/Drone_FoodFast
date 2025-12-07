from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum as SQLEnum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import enum
import os
import time
import httpx
import math

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8000")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product_service:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment_service:8000")

# Database setup
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enums
class OrderStatus(str, enum.Enum):
    WAITING_CONFIRMATION = "waiting_confirmation"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    IN_DELIVERY = "in_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class DroneStatus(str, enum.Enum):
    IDLE = "idle"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    CHARGING = "charging"

# ============================================
# DATABASE MODELS
# ============================================
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    restaurant_id = Column(Integer, nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    total_weight = Column(Float, default=0)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.WAITING_CONFIRMATION)
    delivery_address = Column(String(500), nullable=False)
    delivery_lat = Column(Float, nullable=True)
    delivery_lng = Column(Float, nullable=True)
    restaurant_lat = Column(Float, nullable=True)
    restaurant_lng = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)
    drone_id = Column(Integer, nullable=True)
    estimated_delivery_time = Column(Integer, default=30)
    rejection_reason = Column(Text, nullable=True)
    # Keep a human-friendly status history in a separate table (linked by order_id)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    weight = Column(Float, default=0.5)


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    status = Column(String(50), nullable=False)
    changed_by = Column(Integer, nullable=True)
    role = Column(String(50), nullable=True)
    note = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)

class Drone(Base):
    __tablename__ = "drones"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100))
    status = Column(SQLEnum(DroneStatus), default=DroneStatus.IDLE)
    battery_level = Column(Float, default=100.0)
    max_payload = Column(Float, default=5.0)
    max_distance_km = Column(Float, default=15.0)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================
# PYDANTIC MODELS
# ============================================
class OrderItemCreate(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float
    weight: Optional[float] = 0.5

class OrderItemResponse(OrderItemCreate):
    id: int
    order_id: int
    class Config:
        from_attributes = True


class OrderStatusHistoryResponse(BaseModel):
    id: int
    order_id: int
    status: str
    changed_by: Optional[int]
    role: Optional[str]
    note: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    restaurant_id: int
    delivery_address: str
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None
    notes: Optional[str] = None
    items: List[OrderItemCreate]


class CheckoutItem(BaseModel):
    restaurant_id: int
    product_id: int
    product_name: str
    quantity: int
    price: float
    weight: Optional[float] = 0.5


class CheckoutRequest(BaseModel):
    items: List[CheckoutItem]
    delivery_address: str
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None
    notes: Optional[str] = None
    payment_method: Optional[str] = 'cod'

class OrderResponse(BaseModel):
    id: int
    user_id: int
    restaurant_id: int
    total_amount: float
    total_weight: float
    status: OrderStatus
    delivery_address: str
    delivery_lat: Optional[float]
    delivery_lng: Optional[float]
    distance_km: Optional[float]
    drone_id: Optional[int]
    estimated_delivery_time: Optional[int]
    rejection_reason: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    history: List[OrderStatusHistoryResponse] = []
    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderReject(BaseModel):
    reason: str

class DroneCreate(BaseModel):
    name: str
    model: Optional[str] = None
    max_payload: float = 5.0
    max_distance_km: float = 15.0

class DroneResponse(BaseModel):
    id: int
    name: str
    model: Optional[str]
    status: DroneStatus
    battery_level: float
    max_payload: float
    max_distance_km: float
    current_lat: Optional[float]
    current_lng: Optional[float]
    created_at: datetime
    class Config:
        from_attributes = True

# ============================================
# APP SETUP
# ============================================
app = FastAPI(title="Order Service", version="2.0.0")

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        try:
            Base.metadata.create_all(bind=engine)
            print("✓ Database tables created successfully")
            
            # Create sample drones
            db = SessionLocal()
            if db.query(Drone).count() == 0:
                sample_drones = [
                    Drone(name="Drone Alpha", model="DX-100", status=DroneStatus.IDLE, 
                          battery_level=100.0, max_payload=5.0, max_distance_km=15.0,
                          current_lat=10.762622, current_lng=106.660172),
                    Drone(name="Drone Beta", model="DX-200", status=DroneStatus.IDLE, 
                          battery_level=95.0, max_payload=7.0, max_distance_km=20.0,
                          current_lat=10.762622, current_lng=106.660172),
                ]
                db.add_all(sample_drones)
                db.commit()
                print("✓ Sample drones created")
            db.close()
            break
        except Exception as e:
            retry_count += 1
            print(f"Database connection failed: {e}")
            time.sleep(2)

# ============================================
# HELPER FUNCTIONS
# ============================================

async def verify_token(token: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{USER_SERVICE_URL}/verify-token",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            return response.json() if response.status_code == 200 else None
        except:
            return None

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    user_data = await verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_data

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371 
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat, delta_lng = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

async def check_and_decrease_stock(product_id: int, quantity: int) -> bool:
    """[QUAN TRỌNG] Gọi Product Service để trừ tồn kho"""
    async with httpx.AsyncClient() as client:
        try:
            # 1. Check availability
            res = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5.0)
            if res.status_code != 200: return False
            product = res.json()
            if not product['is_available'] or product['stock_quantity'] < quantity:
                return False
            
            # 2. Decrease stock
            # (Trong thực tế nên dùng distributed transaction hoặc saga, nhưng ở đây gọi trực tiếp cho đơn giản)
            res_decrease = await client.post(
                f"{PRODUCT_SERVICE_URL}/products/{product_id}/decrease-stock",
                params={"quantity": quantity},
                timeout=5.0
            )
            return res_decrease.status_code == 200
        except Exception as e:
            print(f"Error checking stock: {e}")
            return False

def find_suitable_drone(db: Session, weight: float, distance: float, restaurant_lat: float, restaurant_lng: float) -> Optional[Drone]:
    drones = db.query(Drone).filter(
        Drone.status == DroneStatus.IDLE,
        Drone.battery_level >= 20,
        Drone.max_payload >= weight,
        Drone.max_distance_km >= distance
    ).order_by(Drone.battery_level.desc()).all()
    
    if not drones: return None
    
    best_drone = None
    min_dist = float('inf')
    for drone in drones:
        if drone.current_lat and drone.current_lng:
            d = calculate_distance(drone.current_lat, drone.current_lng, restaurant_lat, restaurant_lng)
            if d < min_dist:
                min_dist = d
                best_drone = drone
    return best_drone or drones[0]

# ============================================
# ROUTES
# ============================================

@app.get("/")
async def root():
    return {"service": "Order Service", "status": "running"}

@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_current_user(authorization)
    if user["role"] != "customer":
        raise HTTPException(403, "Only customers can place orders")
    
    # 1. Validate & Decrease Stock
    for item in order.items:
        success = await check_and_decrease_stock(item.product_id, item.quantity)
        if not success:
            raise HTTPException(400, f"Product '{item.product_name}' is out of stock or unavailable")

    # 2. Calculate Total & Weight
    total = sum(item.price * item.quantity for item in order.items)
    total_weight = sum(item.weight * item.quantity for item in order.items)
    
    # 3. Get Restaurant Location
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{USER_SERVICE_URL}/restaurants/{order.restaurant_id}")
            restaurant = res.json() if res.status_code == 200 else {}
        except:
            restaurant = {}
            
    # Mặc định lấy HCM nếu lỗi
    r_lat = restaurant.get("latitude", 10.762622) 
    r_lng = restaurant.get("longitude", 106.660172)
    
    # 4. Calculate Distance
    dist_km = 0
    if order.delivery_lat and order.delivery_lng:
        dist_km = calculate_distance(r_lat, r_lng, order.delivery_lat, order.delivery_lng)
        if dist_km > 30:
            raise HTTPException(400, "Delivery distance exceeds 30km limit")

    # 5. Create Order
    db_order = Order(
        user_id=user["user_id"],
        restaurant_id=order.restaurant_id,
        total_amount=total,
        total_weight=total_weight,
        delivery_address=order.delivery_address,
        delivery_lat=order.delivery_lat,
        delivery_lng=order.delivery_lng,
        restaurant_lat=r_lat,
        restaurant_lng=r_lng,
        distance_km=dist_km,
        notes=order.notes,
        estimated_delivery_time=int(dist_km * 2 + 20),
        status=OrderStatus.WAITING_CONFIRMATION
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    for item in order.items:
        db_item = OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            price=item.price,
            weight=item.weight
        )
        db.add(db_item)
    db.commit()
    
    # Create initial history entry
    try:
        history = OrderStatusHistory(
            order_id=db_order.id,
            status=OrderStatus.WAITING_CONFIRMATION.value,
            changed_by=user['user_id'],
            role=user['role'],
            note='Order created',
            changed_at=datetime.utcnow()
        )
        db.add(history)
        db.commit()
    except Exception as e:
        print('Warning: could not write order history:', e)

    # Return full response
    items = db.query(OrderItem).filter(OrderItem.order_id == db_order.id).all()
    response = OrderResponse.from_orm(db_order)
    response.items = [OrderItemResponse.from_orm(item) for item in items]
    try:
        rows = db.query(OrderStatusHistory).filter(OrderStatusHistory.order_id == db_order.id).order_by(OrderStatusHistory.changed_at).all()
        response.history = [OrderStatusHistoryResponse.from_orm(r) for r in rows]
    except Exception:
        response.history = []
    return response


@app.post("/orders/checkout", status_code=status.HTTP_201_CREATED)
async def checkout_order(checkout: CheckoutRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    """Create multiple orders from a single checkout (split per restaurant).
    The endpoint groups items by restaurant_id and creates one Order per restaurant.
    If `payment_method` is provided and not 'cod', this endpoint attempts to create a payment for each order
    by calling the Payment Service using the caller's Authorization header.
    Returns: { orders: [OrderResponse], payments: [{order_id, status, payment_id?, error?}] }
    """
    user = await get_current_user(authorization)
    if user['role'] != 'customer':
        raise HTTPException(403, 'Only customers can checkout')

    items = checkout.items or []
    if not items:
        raise HTTPException(400, 'No items in checkout')

    # Pre-check availability for all products to avoid partial decreases
    async with httpx.AsyncClient() as client:
        for it in items:
            try:
                res = await client.get(f"{PRODUCT_SERVICE_URL}/products/{it.product_id}", timeout=5.0)
                if res.status_code != 200:
                    raise HTTPException(400, f'Product {it.product_id} unavailable')
                prod = res.json()
                if not prod.get('is_available') or prod.get('stock_quantity', 0) < it.quantity:
                    raise HTTPException(400, f"Product '{it.product_name}' is out of stock or unavailable")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(503, f'Product service unavailable: {e}')

    # Group items by restaurant
    groups = {}
    for it in items:
        groups.setdefault(it.restaurant_id, []).append(it)

    created_orders = []
    payment_results = []

    # Process each group as a separate order
    async with httpx.AsyncClient() as client:
        for restaurant_id, items_group in groups.items():
            # Build order totals
            total = sum(i.price * i.quantity for i in items_group)
            total_weight = sum(i.weight * i.quantity for i in items_group)

            # Fetch restaurant location (best-effort)
            try:
                rres = await client.get(f"{USER_SERVICE_URL}/restaurants/{restaurant_id}", timeout=5.0)
                restaurant = rres.json() if rres.status_code == 200 else {}
            except Exception:
                restaurant = {}

            r_lat = restaurant.get('latitude', 10.762622)
            r_lng = restaurant.get('longitude', 106.660172)
            dist_km = 0
            if checkout.delivery_lat and checkout.delivery_lng:
                dist_km = calculate_distance(r_lat, r_lng, checkout.delivery_lat, checkout.delivery_lng)
                if dist_km > 30:
                    raise HTTPException(400, 'Delivery distance exceeds 30km limit for one of the restaurants')

            # Create Order DB row
            db_order = Order(
                user_id=user['user_id'],
                restaurant_id=restaurant_id,
                total_amount=total,
                total_weight=total_weight,
                delivery_address=checkout.delivery_address,
                delivery_lat=checkout.delivery_lat,
                delivery_lng=checkout.delivery_lng,
                restaurant_lat=r_lat,
                restaurant_lng=r_lng,
                distance_km=dist_km,
                notes=checkout.notes,
                estimated_delivery_time=int(dist_km * 2 + 20),
                status=OrderStatus.WAITING_CONFIRMATION
            )
            db.add(db_order)
            db.commit()
            db.refresh(db_order)

            # Add items and decrease stock
            for it in items_group:
                # decrease stock (call product service)
                try:
                    await client.post(f"{PRODUCT_SERVICE_URL}/products/{it.product_id}/decrease-stock", params={'quantity': it.quantity}, timeout=5.0)
                except Exception:
                    # if decrease fails, continue but warn (in production would revert)
                    raise HTTPException(400, f'Failed to decrease stock for product {it.product_id}')

                db_item = OrderItem(
                    order_id=db_order.id,
                    product_id=it.product_id,
                    product_name=it.product_name,
                    quantity=it.quantity,
                    price=it.price,
                    weight=it.weight or 0.5
                )
                db.add(db_item)
            db.commit()

            # initial history entry
            try:
                history = OrderStatusHistory(
                    order_id=db_order.id,
                    status=OrderStatus.WAITING_CONFIRMATION.value,
                    changed_by=user['user_id'],
                    role=user['role'],
                    note='Order created (split checkout)',
                    changed_at=datetime.utcnow()
                )
                db.add(history)
                db.commit()
            except Exception:
                print('Warning: could not write order history during checkout')

            # Prepare response shape
            items_db = db.query(OrderItem).filter(OrderItem.order_id == db_order.id).all()
            resp = OrderResponse.from_orm(db_order)
            resp.items = [OrderItemResponse.from_orm(i) for i in items_db]
            try:
                rows = db.query(OrderStatusHistory).filter(OrderStatusHistory.order_id == db_order.id).order_by(OrderStatusHistory.changed_at).all()
                resp.history = [OrderStatusHistoryResponse.from_orm(r) for r in rows]
            except Exception:
                resp.history = []

            created_orders.append(resp)

            # If payment required, create payment record via Payment Service
            if checkout.payment_method and checkout.payment_method != 'cod':
                try:
                    pay_res = await client.post(
                        f"{PAYMENT_SERVICE_URL}/payments",
                        json={'order_id': db_order.id, 'amount': db_order.total_amount, 'payment_method': checkout.payment_method},
                        headers={'Authorization': authorization},
                        timeout=10.0
                    )
                    if pay_res.status_code in (200, 201):
                        payment_results.append({'order_id': db_order.id, 'status': 'created', 'payment': pay_res.json()})
                    else:
                        payment_results.append({'order_id': db_order.id, 'status': 'error', 'error': pay_res.text})
                except Exception as e:
                    payment_results.append({'order_id': db_order.id, 'status': 'error', 'error': str(e)})

    return {'orders': created_orders, 'payments': payment_results}

@app.post("/orders/{order_id}/accept", response_model=OrderResponse)
async def accept_order(order_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_current_user(authorization)
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order: raise HTTPException(404, "Order not found")
    if user["role"] == "restaurant" and order.restaurant_id != user["user_id"]:
        raise HTTPException(403, "Permission denied")
    
    order.status = OrderStatus.CONFIRMED
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)

    # Create a history entry for the restaurant acceptance
    try:
        history = OrderStatusHistory(
            order_id=order.id,
            status=OrderStatus.CONFIRMED.value,
            changed_by=user['user_id'],
            role=user['role'],
            note='Restaurant accepted order',
            changed_at=datetime.utcnow()
        )
        db.add(history)
        db.commit()
    except Exception as e:
        print('Warning: could not write order history on accept:', e)
    # Build full response
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    res = OrderResponse.from_orm(order)
    res.items = [OrderItemResponse.from_orm(item) for item in items]
    try:
        rows = db.query(OrderStatusHistory).filter(OrderStatusHistory.order_id == order.id).order_by(OrderStatusHistory.changed_at).all()
        res.history = [OrderStatusHistoryResponse.from_orm(r) for r in rows]
    except Exception:
        res.history = []
    return res

@app.post("/orders/{order_id}/reject", response_model=OrderResponse)
async def reject_order(order_id: int, reject_data: OrderReject, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_current_user(authorization)
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order: raise HTTPException(404, "Order not found")
    if user["role"] == "restaurant" and order.restaurant_id != user["user_id"]:
        raise HTTPException(403, "Permission denied")

    order.status = OrderStatus.REJECTED
    order.rejection_reason = reject_data.reason
    order.updated_at = datetime.utcnow()
    db.commit()
    # add history entry
    try:
        history = OrderStatusHistory(
            order_id=order.id,
            status=order.status.value,
            changed_by=user['user_id'],
            role=user['role'],
            note=f'Reason: {reject_data.reason}',
            changed_at=datetime.utcnow()
        )
        db.add(history)
        db.commit()
    except Exception as e:
        print('Warning: could not write reject history:', e)
    
    # [TODO] Logic hoàn tồn kho (tăng lại số lượng) nên được thêm vào đây
    # Gọi API: POST /products/{id}/increase-stock (nếu có)
    
    # Build full response
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    res = OrderResponse.from_orm(order)
    res.items = [OrderItemResponse.from_orm(item) for item in items]
    try:
        rows = db.query(OrderStatusHistory).filter(OrderStatusHistory.order_id == order.id).order_by(OrderStatusHistory.changed_at).all()
        res.history = [OrderStatusHistoryResponse.from_orm(r) for r in rows]
    except Exception:
        res.history = []
    return res

@app.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    skip: int = 0, limit: int = 100, 
    authorization: str = Header(None), 
    status: Optional[OrderStatus] = None, 
    db: Session = Depends(get_db)
):
    user = await get_current_user(authorization)
    query = db.query(Order)
    
    if user["role"] == "customer":
        query = query.filter(Order.user_id == user["user_id"])
    elif user["role"] == "restaurant":
        query = query.filter(Order.restaurant_id == user["user_id"])
        
    if status:
        query = query.filter(Order.status == status)
        
    orders = query.order_by(Order.id.desc()).offset(skip).limit(limit).all()
    
    # Populate items
    result = []
    for order in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        res = OrderResponse.from_orm(order)
        res.items = [OrderItemResponse.from_orm(item) for item in items]
        # attach history
        try:
            rows = db.query(OrderStatusHistory).filter(OrderStatusHistory.order_id == order.id).order_by(OrderStatusHistory.changed_at).all()
            res.history = [OrderStatusHistoryResponse.from_orm(r) for r in rows]
        except Exception:
            res.history = []
        result.append(res)
    return result

@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order: raise HTTPException(404, "Order not found")
    
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    res = OrderResponse.from_orm(order)
    res.items = [OrderItemResponse.from_orm(item) for item in items]
    try:
        rows = db.query(OrderStatusHistory).filter(OrderStatusHistory.order_id == order_id).order_by(OrderStatusHistory.changed_at).all()
        res.history = [OrderStatusHistoryResponse.from_orm(r) for r in rows]
    except Exception:
        res.history = []
    try:
        rows = db.query(OrderStatusHistory).filter(OrderStatusHistory.order_id == order_id).order_by(OrderStatusHistory.changed_at).all()
        res.history = [OrderStatusHistoryResponse.from_orm(r) for r in rows]
    except Exception:
        res.history = []
    return res

@app.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int, 
    status_update: OrderStatusUpdate, 
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = await get_current_user(authorization)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order: raise HTTPException(404, "Order not found")
    
    new_status = status_update.status

    # Permission checks
    if user['role'] == 'customer':
        if order.user_id != user['user_id']:
            raise HTTPException(403, 'Permission denied')
        if new_status != OrderStatus.CANCELLED:
            raise HTTPException(403, 'Customers can only cancel their own orders')
        if order.status not in [OrderStatus.WAITING_CONFIRMATION, OrderStatus.CONFIRMED]:
            raise HTTPException(400, 'Cannot cancel at this stage')

    if user['role'] == 'restaurant':
        if order.restaurant_id != user['user_id']:
            raise HTTPException(403, 'Permission denied')
        allowed = [OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.IN_DELIVERY, OrderStatus.DELIVERED, OrderStatus.REJECTED]
        if new_status not in allowed:
            raise HTTPException(403, 'Action not allowed for restaurant')

    # apply new status
    order.status = new_status
    order.updated_at = datetime.utcnow()
    
    # --- LOGIC DRONE ---
    if new_status == OrderStatus.READY and not order.drone_id:
        drone = find_suitable_drone(
            db, 
            order.total_weight, 
            order.distance_km or 5,
            order.restaurant_lat or 10.762, 
            order.restaurant_lng or 106.660
        )
        if drone:
            order.drone_id = drone.id
            drone.status = DroneStatus.IN_USE
            drone.current_lat = order.restaurant_lat # Drone bay đến quán
            drone.current_lng = order.restaurant_lng
            order.status = OrderStatus.IN_DELIVERY # Auto switch status
            
            # Trừ pin (giả lập 1km = 1% pin)
            dist = order.distance_km or 5
            drone.battery_level = max(0, drone.battery_level - dist)

    if new_status == OrderStatus.DELIVERED and order.drone_id:
        drone = db.query(Drone).filter(Drone.id == order.drone_id).first()
        if drone:
            drone.status = DroneStatus.IDLE
            drone.current_lat = order.delivery_lat # Drone ở vị trí khách
            drone.current_lng = order.delivery_lng
            
    # Write history entries for this status transition
    try:
        if new_status == OrderStatus.READY:
            # record READY
            h_ready = OrderStatusHistory(
                order_id=order.id,
                status=OrderStatus.READY.value,
                changed_by=user['user_id'],
                role=user['role'],
                note='Marked ready',
                changed_at=datetime.utcnow()
            )
            db.add(h_ready)
            db.commit()

            # if auto-assigned a drone and the status auto-switched to IN_DELIVERY, add IN_DELIVERY
            if order.status == OrderStatus.IN_DELIVERY:
                note = f'Drone assigned: #{order.drone_id}' if order.drone_id else 'Auto switched to in_delivery'
                h_in = OrderStatusHistory(
                    order_id=order.id,
                    status=OrderStatus.IN_DELIVERY.value,
                    changed_by=user['user_id'],
                    role=user['role'],
                    note=note,
                    changed_at=datetime.utcnow()
                )
                db.add(h_in)
                db.commit()
        else:
            h = OrderStatusHistory(
                order_id=order.id,
                status=order.status.value,
                changed_by=user['user_id'],
                role=user['role'],
                note='Status updated',
                changed_at=datetime.utcnow()
            )
            db.add(h)
            db.commit()
    except Exception as e:
        print('Warning: could not append update history:', e)

    db.commit()
    db.refresh(order)
    
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    res = OrderResponse.from_orm(order)
    res.items = [OrderItemResponse.from_orm(item) for item in items]
    return res

# Drones CRUD
@app.get("/drones", response_model=List[DroneResponse])
async def list_drones(db: Session = Depends(get_db)):
    return db.query(Drone).all()

@app.post("/drones", response_model=DroneResponse)
async def create_drone(drone: DroneCreate, db: Session = Depends(get_db)):
    db_drone = Drone(**drone.dict(), current_lat=10.762622, current_lng=106.660172)
    db.add(db_drone)
    db.commit()
    db.refresh(db_drone)
    return db_drone

@app.post("/drones/{drone_id}/charge")
async def charge_drone(drone_id: int, db: Session = Depends(get_db)):
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone: raise HTTPException(404, "Drone not found")
    drone.battery_level = 100.0
    drone.status = DroneStatus.IDLE
    db.commit()
    return {"message": "Charged"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)