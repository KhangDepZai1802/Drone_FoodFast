from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio
import json
import math
import os
import time
import httpx

# ==========================================
# CONFIGURATION
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order_service:8000")

# Database setup
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# DATABASE MODELS
# ==========================================
class DeliveryTracking(Base):
    """Lịch sử vị trí drone theo thời gian thực"""
    __tablename__ = "delivery_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    drone_id = Column(Integer, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, default=50.0)  # meters
    speed = Column(Float, default=0.0)  # km/h
    battery_level = Column(Float)
    status = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)

class DeliveryRoute(Base):
    """Waypoints của tuyến đường"""
    __tablename__ = "delivery_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    drone_id = Column(Integer, nullable=False)
    waypoint_sequence = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    estimated_time = Column(Integer)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)

class GPSAccuracyLog(Base):
    """Độ chính xác GPS"""
    __tablename__ = "gps_accuracy_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy_meters = Column(Float, default=5.0)
    satellite_count = Column(Integer, default=8)
    timestamp = Column(DateTime, default=datetime.utcnow)

# ==========================================
# PYDANTIC MODELS
# ==========================================
class TrackingPoint(BaseModel):
    latitude: float
    longitude: float
    altitude: Optional[float] = 50.0
    speed: Optional[float] = 0.0
    battery_level: Optional[float] = None
    status: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class DeliveryTrackingResponse(BaseModel):
    id: int
    order_id: int
    drone_id: int
    latitude: float
    longitude: float
    altitude: float
    speed: float
    battery_level: Optional[float]
    status: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True

class RouteWaypoint(BaseModel):
    waypoint_sequence: int
    latitude: float
    longitude: float
    estimated_time: Optional[int]

class RouteResponse(BaseModel):
    order_id: int
    drone_id: int
    waypoints: List[RouteWaypoint]
    total_distance_km: float
    estimated_total_time: int

class GPSAccuracy(BaseModel):
    drone_id: int
    latitude: float
    longitude: float
    accuracy_meters: float
    satellite_count: int
    timestamp: datetime

    class Config:
        from_attributes = True

# ==========================================
# APP SETUP
# ==========================================
app = FastAPI(title="Delivery Tracking Service", version="1.0.0")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
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
            print("✓ Delivery Tracking database tables created")
            break
        except Exception as e:
            retry_count += 1
            print(f"Database connection failed: {e}")
            time.sleep(2)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{USER_SERVICE_URL}/verify-token",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response.json() if response.status_code == 200 else None
        except:
            return None

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine formula - tính khoảng cách GPS"""
    R = 6371  # Earth radius in km
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def calculate_bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Tính góc hướng (bearing) giữa 2 điểm"""
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lng = math.radians(lng2 - lng1)
    
    y = math.sin(delta_lng) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lng)
    bearing = math.atan2(y, x)
    return (math.degrees(bearing) + 360) % 360

def generate_waypoints(start_lat: float, start_lng: float, end_lat: float, end_lng: float, num_points: int = 10) -> List[dict]:
    """Tạo các waypoint dọc tuyến đường"""
    waypoints = []
    for i in range(num_points + 1):
        ratio = i / num_points
        lat = start_lat + (end_lat - start_lat) * ratio
        lng = start_lng + (end_lng - start_lng) * ratio
        waypoints.append({
            "sequence": i,
            "latitude": lat,
            "longitude": lng,
            "estimated_time": int((i / num_points) * 60)  # giả sử 60s tổng
        })
    return waypoints

# ==========================================
# WEBSOCKET CONNECTION MANAGER
# ==========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, order_id: int):
        await websocket.accept()
        if order_id not in self.active_connections:
            self.active_connections[order_id] = []
        self.active_connections[order_id].append(websocket)

    def disconnect(self, websocket: WebSocket, order_id: int):
        if order_id in self.active_connections:
            self.active_connections[order_id].remove(websocket)

    async def broadcast(self, order_id: int, message: dict):
        if order_id in self.active_connections:
            for connection in self.active_connections[order_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

# ==========================================
# ROUTES
# ==========================================

@app.get("/")
async def root():
    return {"service": "Delivery Tracking Service", "status": "running"}

# --- TRACKING ROUTES ---

@app.post("/tracking/start/{order_id}")
async def start_tracking(
    order_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Bắt đầu tracking cho 1 đơn hàng"""
    user = await verify_token(authorization)
    if not user:
        raise HTTPException(401, "Invalid token")
    
    # Get order info từ Order Service
    async with httpx.AsyncClient() as client:
        try:
            order_res = await client.get(
                f"{ORDER_SERVICE_URL}/orders/{order_id}",
                headers={"Authorization": authorization}
            )
            if order_res.status_code != 200:
                raise HTTPException(404, "Order not found")
            order = order_res.json()
        except:
            raise HTTPException(503, "Order service unavailable")
    
    if not order.get("drone_id"):
        raise HTTPException(400, "No drone assigned to this order")
    
    # Tạo route waypoints
    start_lat = order.get("restaurant_lat", 10.762622)
    start_lng = order.get("restaurant_lng", 106.660172)
    end_lat = order.get("delivery_lat", 10.775845)
    end_lng = order.get("delivery_lng", 106.701758)
    
    waypoints = generate_waypoints(start_lat, start_lng, end_lat, end_lng, num_points=15)
    
    # Lưu route
    for wp in waypoints:
        db_waypoint = DeliveryRoute(
            order_id=order_id,
            drone_id=order["drone_id"],
            waypoint_sequence=wp["sequence"],
            latitude=wp["latitude"],
            longitude=wp["longitude"],
            estimated_time=wp["estimated_time"]
        )
        db.add(db_waypoint)
    
    db.commit()
    
    # Tạo tracking point đầu tiên
    initial_tracking = DeliveryTracking(
        order_id=order_id,
        drone_id=order["drone_id"],
        latitude=start_lat,
        longitude=start_lng,
        altitude=0,
        speed=0,
        battery_level=order.get("battery_level", 100),
        status="taking_off"
    )
    db.add(initial_tracking)
    db.commit()
    
    return {
        "message": "Tracking started",
        "order_id": order_id,
        "drone_id": order["drone_id"],
        "total_waypoints": len(waypoints)
    }

@app.get("/tracking/{order_id}", response_model=List[DeliveryTrackingResponse])
async def get_tracking_history(order_id: int, db: Session = Depends(get_db)):
    """Lấy lịch sử tracking"""
    tracking = db.query(DeliveryTracking).filter(
        DeliveryTracking.order_id == order_id
    ).order_by(DeliveryTracking.timestamp).all()
    
    return tracking

@app.get("/tracking/latest/{order_id}")
async def get_latest_position(order_id: int, db: Session = Depends(get_db)):
    """Lấy vị trí hiện tại của drone"""
    latest = db.query(DeliveryTracking).filter(
        DeliveryTracking.order_id == order_id
    ).order_by(DeliveryTracking.timestamp.desc()).first()
    
    if not latest:
        raise HTTPException(404, "No tracking data found")
    
    return latest

@app.get("/route/{order_id}")
async def get_delivery_route(order_id: int, db: Session = Depends(get_db)):
    """Lấy tuyến đường đã lập sẵn"""
    waypoints = db.query(DeliveryRoute).filter(
        DeliveryRoute.order_id == order_id
    ).order_by(DeliveryRoute.waypoint_sequence).all()
    
    if not waypoints:
        raise HTTPException(404, "No route found")
    
    total_distance = 0
    for i in range(len(waypoints) - 1):
        dist = calculate_distance(
            waypoints[i].latitude, waypoints[i].longitude,
            waypoints[i+1].latitude, waypoints[i+1].longitude
        )
        total_distance += dist
    
    return {
        "order_id": order_id,
        "drone_id": waypoints[0].drone_id,
        "waypoints": [
            {
                "waypoint_sequence": wp.waypoint_sequence,
                "latitude": wp.latitude,
                "longitude": wp.longitude,
                "estimated_time": wp.estimated_time
            }
            for wp in waypoints
        ],
        "total_distance_km": round(total_distance, 2),
        "estimated_total_time": waypoints[-1].estimated_time if waypoints else 0
    }

@app.post("/tracking/update/{order_id}")
async def update_position(
    order_id: int,
    latitude: float,
    longitude: float,
    altitude: float = 50.0,
    speed: float = 30.0,
    battery_level: Optional[float] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Cập nhật vị trí drone (được gọi từ drone simulator hoặc GPS receiver)"""
    
    # Lấy order để biết drone_id
    async with httpx.AsyncClient() as client:
        try:
            order_res = await client.get(f"{ORDER_SERVICE_URL}/orders/{order_id}")
            if order_res.status_code != 200:
                raise HTTPException(404, "Order not found")
            order = order_res.json()
            drone_id = order.get("drone_id")
        except:
            raise HTTPException(503, "Order service unavailable")
    
    # Lưu tracking point
    tracking_point = DeliveryTracking(
        order_id=order_id,
        drone_id=drone_id,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        speed=speed,
        battery_level=battery_level,
        status=status
    )
    db.add(tracking_point)
    db.commit()
    db.refresh(tracking_point)
    
    # Broadcast qua WebSocket
    await manager.broadcast(order_id, {
        "type": "position_update",
        "order_id": order_id,
        "drone_id": drone_id,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "speed": speed,
        "battery_level": battery_level,
        "status": status,
        "timestamp": tracking_point.timestamp.isoformat()
    })
    
    return {"message": "Position updated", "tracking_id": tracking_point.id}

@app.post("/gps/log")
async def log_gps_accuracy(
    drone_id: int,
    latitude: float,
    longitude: float,
    accuracy_meters: float,
    satellite_count: int,
    db: Session = Depends(get_db)
):
    """Log độ chính xác GPS"""
    log_entry = GPSAccuracyLog(
        drone_id=drone_id,
        latitude=latitude,
        longitude=longitude,
        accuracy_meters=accuracy_meters,
        satellite_count=satellite_count
    )
    db.add(log_entry)
    db.commit()
    return {"message": "GPS accuracy logged"}

@app.get("/gps/accuracy/{drone_id}")
async def get_gps_accuracy(drone_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """Lấy lịch sử độ chính xác GPS"""
    logs = db.query(GPSAccuracyLog).filter(
        GPSAccuracyLog.drone_id == drone_id
    ).order_by(GPSAccuracyLog.timestamp.desc()).limit(limit).all()
    
    if not logs:
        return {"message": "No GPS logs", "average_accuracy": None}
    
    avg_accuracy = sum(log.accuracy_meters for log in logs) / len(logs)
    avg_satellites = sum(log.satellite_count for log in logs) / len(logs)
    
    return {
        "drone_id": drone_id,
        "recent_logs": logs,
        "average_accuracy_meters": round(avg_accuracy, 2),
        "average_satellite_count": round(avg_satellites, 1)
    }

# --- WEBSOCKET ENDPOINT ---

@app.websocket("/ws/tracking/{order_id}")
async def websocket_tracking(websocket: WebSocket, order_id: int):
    """WebSocket để nhận cập nhật real-time"""
    await manager.connect(websocket, order_id)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket, order_id)

# --- SIMULATION ENDPOINT (FOR TESTING) ---

@app.post("/simulation/start/{order_id}")
async def simulate_delivery(order_id: int, db: Session = Depends(get_db)):
    """Mô phỏng drone giao hàng (FOR TESTING)"""
    
    # Lấy route
    waypoints = db.query(DeliveryRoute).filter(
        DeliveryRoute.order_id == order_id
    ).order_by(DeliveryRoute.waypoint_sequence).all()
    
    if not waypoints:
        raise HTTPException(404, "Route not found. Call /tracking/start first")
    
    drone_id = waypoints[0].drone_id
    
    # Simulate drone movement
    asyncio.create_task(simulate_drone_movement(order_id, drone_id, waypoints, db))
    
    return {"message": "Simulation started", "order_id": order_id}

async def simulate_drone_movement(order_id: int, drone_id: int, waypoints: list, db: Session):
    """Background task: mô phỏng drone di chuyển"""
    battery = 100.0
    
    for i, waypoint in enumerate(waypoints):
        # Simulate movement
        tracking = DeliveryTracking(
            order_id=order_id,
            drone_id=drone_id,
            latitude=waypoint.latitude,
            longitude=waypoint.longitude,
            altitude=50 + (i % 10),  # vary altitude
            speed=25 + (i % 15),     # vary speed
            battery_level=battery,
            status="in_flight" if i < len(waypoints)-1 else "landing"
        )
        db.add(tracking)
        db.commit()
        
        # Broadcast
        await manager.broadcast(order_id, {
            "type": "position_update",
            "order_id": order_id,
            "drone_id": drone_id,
            "latitude": waypoint.latitude,
            "longitude": waypoint.longitude,
            "altitude": tracking.altitude,
            "speed": tracking.speed,
            "battery_level": battery,
            "status": tracking.status,
            "waypoint": i + 1,
            "total_waypoints": len(waypoints),
            "timestamp": tracking.timestamp.isoformat()
        })
        
        battery -= 0.5  # giảm pin
        await asyncio.sleep(2)  # 2s mỗi waypoint
    
    print(f"✅ Simulation completed for order {order_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)