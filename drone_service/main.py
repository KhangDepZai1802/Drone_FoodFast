from fastapi import FastAPI, Depends, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import enum
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
# ENUMS
# ==========================================
class DroneDetailedStatus(str, enum.Enum):
    IDLE = "idle"                           # Rảnh rỗi tại trụ sở
    CHARGING = "charging"                   # Đang sạc pin
    ASSIGNED = "assigned"                   # Được giao nhiệm vụ
    GOING_TO_RESTAURANT = "going_to_restaurant"  # Đang bay đến nhà hàng
    PICKING_UP = "picking_up"               # Đang lấy hàng
    IN_DELIVERY = "in_delivery"             # Đang giao hàng cho khách
    RETURNING = "returning"                 # Đang quay về trụ sở
    MAINTENANCE = "maintenance"             # Đang bảo trì
    ERROR = "error"                         # Gặp sự cố

class MaintenanceType(str, enum.Enum):
    ROUTINE = "routine"                     # Bảo trì định kỳ
    REPAIR = "repair"                       # Sửa chữa
    BATTERY_REPLACEMENT = "battery_replacement"
    MOTOR_CHECK = "motor_check"
    SOFTWARE_UPDATE = "software_update"

# ==========================================
# DATABASE MODELS
# ==========================================
class DroneStatusHistory(Base):
    """Lịch sử thay đổi trạng thái chi tiết"""
    __tablename__ = "drone_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, nullable=False, index=True)
    status = Column(String(50), nullable=False)
    previous_status = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    battery_level = Column(Float)
    reason = Column(Text)
    changed_by = Column(Integer)  # User ID
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)

class DroneMaintenance(Base):
    """Lịch bảo trì drone"""
    __tablename__ = "drone_maintenance"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, nullable=False, index=True)
    maintenance_type = Column(String(50), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    completed_date = Column(DateTime)
    technician_id = Column(Integer)
    notes = Column(Text)
    cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class DronePerformance(Base):
    """Chỉ số hiệu suất drone"""
    __tablename__ = "drone_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, nullable=False, unique=True, index=True)
    total_deliveries = Column(Integer, default=0)
    total_distance_km = Column(Float, default=0.0)
    total_flight_time_minutes = Column(Integer, default=0)
    average_speed = Column(Float, default=0.0)
    success_rate = Column(Float, default=100.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

class DroneBatteryLog(Base):
    """Log sức khỏe pin"""
    __tablename__ = "drone_battery_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, nullable=False, index=True)
    battery_level = Column(Float, nullable=False)
    voltage = Column(Float)
    temperature = Column(Float)
    health_percentage = Column(Float)
    charge_cycles = Column(Integer)
    logged_at = Column(DateTime, default=datetime.utcnow)

class DroneAlert(Base):
    """Cảnh báo sự cố"""
    __tablename__ = "drone_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # low_battery, gps_error, motor_failure
    severity = Column(String(20))  # low, medium, high, critical
    message = Column(Text)
    is_resolved = Column(Integer, default=0)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==========================================
# PYDANTIC MODELS
# ==========================================
class StatusChange(BaseModel):
    status: DroneDetailedStatus
    reason: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class StatusHistoryResponse(BaseModel):
    id: int
    drone_id: int
    status: str
    previous_status: Optional[str]
    battery_level: Optional[float]
    reason: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True

class MaintenanceCreate(BaseModel):
    drone_id: int
    maintenance_type: MaintenanceType
    scheduled_date: datetime
    notes: Optional[str] = None

class MaintenanceResponse(BaseModel):
    id: int
    drone_id: int
    maintenance_type: str
    scheduled_date: datetime
    completed_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PerformanceResponse(BaseModel):
    drone_id: int
    total_deliveries: int
    total_distance_km: float
    total_flight_time_minutes: int
    average_speed: float
    success_rate: float
    last_updated: datetime

    class Config:
        from_attributes = True

class BatteryLogResponse(BaseModel):
    id: int
    drone_id: int
    battery_level: float
    voltage: Optional[float]
    temperature: Optional[float]
    health_percentage: Optional[float]
    logged_at: datetime

    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    id: int
    drone_id: int
    alert_type: str
    severity: str
    message: Optional[str]
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DroneStatusSummary(BaseModel):
    drone_id: int
    drone_name: str
    current_status: str
    battery_level: float
    current_location: Optional[dict]
    last_update: datetime
    performance: Optional[dict]
    active_alerts: int

# ==========================================
# APP SETUP
# ==========================================
app = FastAPI(title="Drone Management Service", version="1.0.0")

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
            print("✓ Drone Management database tables created")
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

async def get_drone_from_order_service(drone_id: int):
    """Lấy thông tin drone từ Order Service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{ORDER_SERVICE_URL}/drones")
            if response.status_code == 200:
                drones = response.json()
                return next((d for d in drones if d["id"] == drone_id), None)
        except:
            pass
    return None

def check_battery_health(battery_logs: list) -> dict:
    """Phân tích sức khỏe pin"""
    if not battery_logs:
        return {"status": "unknown", "recommendation": "No data"}
    
    recent_logs = battery_logs[:10]
    avg_health = sum(log.health_percentage for log in recent_logs if log.health_percentage) / len(recent_logs)
    
    if avg_health >= 90:
        return {"status": "excellent", "health": avg_health, "recommendation": "No action needed"}
    elif avg_health >= 75:
        return {"status": "good", "health": avg_health, "recommendation": "Monitor regularly"}
    elif avg_health >= 60:
        return {"status": "fair", "health": avg_health, "recommendation": "Schedule replacement soon"}
    else:
        return {"status": "poor", "health": avg_health, "recommendation": "Replace immediately"}

# ==========================================
# ROUTES
# ==========================================

@app.get("/")
async def root():
    return {"service": "Drone Management Service", "status": "running"}

# --- STATUS MANAGEMENT ---

@app.post("/drones/{drone_id}/status")
async def update_drone_status(
    drone_id: int,
    status_change: StatusChange,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Cập nhật trạng thái drone (Admin/System)"""
    user = await verify_token(authorization)
    if not user or user.get("role") not in ["admin", "restaurant"]:
        raise HTTPException(403, "Admin access required")
    
    # Get current status
    latest = db.query(DroneStatusHistory).filter(
        DroneStatusHistory.drone_id == drone_id
    ).order_by(DroneStatusHistory.changed_at.desc()).first()
    
    previous_status = latest.status if latest else "unknown"
    
    # Get current drone info
    drone = await get_drone_from_order_service(drone_id)
    current_battery = drone.get("battery_level", 0) if drone else 0
    
    # Create history record
    history_record = DroneStatusHistory(
        drone_id=drone_id,
        status=status_change.status.value,
        previous_status=previous_status,
        latitude=status_change.latitude,
        longitude=status_change.longitude,
        battery_level=current_battery,
        reason=status_change.reason,
        changed_by=user.get("user_id")
    )
    db.add(history_record)
    
    # Update drone in Order Service
    async with httpx.AsyncClient() as client:
        try:
            await client.put(
                f"{ORDER_SERVICE_URL}/drones/{drone_id}",
                json={"status": status_change.status.value}
            )
        except:
            pass
    
    # Check if need alerts
    if status_change.status == DroneDetailedStatus.ERROR:
        alert = DroneAlert(
            drone_id=drone_id,
            alert_type="status_error",
            severity="high",
            message=f"Drone status changed to ERROR. Reason: {status_change.reason}"
        )
        db.add(alert)
    
    db.commit()
    
    return {"message": "Status updated", "previous_status": previous_status, "new_status": status_change.status.value}

@app.get("/drones/{drone_id}/status-history", response_model=List[StatusHistoryResponse])
async def get_status_history(
    drone_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Xem lịch sử thay đổi trạng thái"""
    history = db.query(DroneStatusHistory).filter(
        DroneStatusHistory.drone_id == drone_id
    ).order_by(DroneStatusHistory.changed_at.desc()).limit(limit).all()
    
    return history

@app.get("/drones/status/summary")
async def get_all_drones_status(db: Session = Depends(get_db)):
    """Tổng quan trạng thái tất cả drone (Admin Dashboard)"""
    
    # Get all drones from Order Service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{ORDER_SERVICE_URL}/drones")
            drones = response.json() if response.status_code == 200 else []
        except:
            drones = []
    
    summaries = []
    for drone in drones:
        drone_id = drone["id"]
        
        # Get latest status
        latest_status = db.query(DroneStatusHistory).filter(
            DroneStatusHistory.drone_id == drone_id
        ).order_by(DroneStatusHistory.changed_at.desc()).first()
        
        # Get performance
        performance = db.query(DronePerformance).filter(
            DronePerformance.drone_id == drone_id
        ).first()
        
        # Count active alerts
        active_alerts = db.query(DroneAlert).filter(
            DroneAlert.drone_id == drone_id,
            DroneAlert.is_resolved == 0
        ).count()
        
        summaries.append({
            "drone_id": drone_id,
            "drone_name": drone["name"],
            "current_status": latest_status.status if latest_status else "unknown",
            "battery_level": drone["battery_level"],
            "current_location": {
                "lat": drone.get("current_lat"),
                "lng": drone.get("current_lng")
            } if drone.get("current_lat") else None,
            "last_update": latest_status.changed_at if latest_status else None,
            "performance": {
                "total_deliveries": performance.total_deliveries,
                "success_rate": performance.success_rate
            } if performance else None,
            "active_alerts": active_alerts
        })
    
    return summaries

# --- MAINTENANCE ---

@app.post("/maintenance", response_model=MaintenanceResponse)
async def schedule_maintenance(
    maintenance: MaintenanceCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Lên lịch bảo trì (Admin)"""
    user = await verify_token(authorization)
    if not user or user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    
    db_maintenance = DroneMaintenance(**maintenance.dict())
    db.add(db_maintenance)
    db.commit()
    db.refresh(db_maintenance)
    
    # Update drone status to maintenance if scheduled soon
    if maintenance.scheduled_date <= datetime.utcnow() + timedelta(hours=24):
        status_change = DroneStatusHistory(
            drone_id=maintenance.drone_id,
            status=DroneDetailedStatus.MAINTENANCE.value,
            reason=f"Scheduled maintenance: {maintenance.maintenance_type}",
            changed_by=user.get("user_id")
        )
        db.add(status_change)
        db.commit()
    
    return db_maintenance

@app.get("/maintenance/{drone_id}", response_model=List[MaintenanceResponse])
async def get_maintenance_history(drone_id: int, db: Session = Depends(get_db)):
    """Lịch sử bảo trì của drone"""
    maintenance = db.query(DroneMaintenance).filter(
        DroneMaintenance.drone_id == drone_id
    ).order_by(DroneMaintenance.scheduled_date.desc()).all()
    
    return maintenance

@app.put("/maintenance/{maintenance_id}/complete")
async def complete_maintenance(
    maintenance_id: int,
    notes: Optional[str] = None,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Đánh dấu bảo trì hoàn thành"""
    user = await verify_token(authorization)
    if not user or user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    
    maintenance = db.query(DroneMaintenance).filter(
        DroneMaintenance.id == maintenance_id
    ).first()
    
    if not maintenance:
        raise HTTPException(404, "Maintenance record not found")
    
    maintenance.completed_date = datetime.utcnow()
    if notes:
        maintenance.notes = notes
    maintenance.technician_id = user.get("user_id")
    
    # Update drone status back to idle
    status_change = DroneStatusHistory(
        drone_id=maintenance.drone_id,
        status=DroneDetailedStatus.IDLE.value,
        reason="Maintenance completed",
        changed_by=user.get("user_id")
    )
    db.add(status_change)
    
    db.commit()
    
    return {"message": "Maintenance completed"}

# --- PERFORMANCE ---

@app.get("/performance/{drone_id}", response_model=PerformanceResponse)
async def get_drone_performance(drone_id: int, db: Session = Depends(get_db)):
    """Xem hiệu suất drone"""
    performance = db.query(DronePerformance).filter(
        DronePerformance.drone_id == drone_id
    ).first()
    
    if not performance:
        # Create initial record
        performance = DronePerformance(drone_id=drone_id)
        db.add(performance)
        db.commit()
        db.refresh(performance)
    
    return performance

@app.post("/performance/{drone_id}/update")
async def update_performance(
    drone_id: int,
    deliveries_completed: int = 0,
    distance_km: float = 0.0,
    flight_time_minutes: int = 0,
    success: bool = True,
    db: Session = Depends(get_db)
):
    """Cập nhật chỉ số hiệu suất (được gọi tự động sau mỗi chuyến bay)"""
    performance = db.query(DronePerformance).filter(
        DronePerformance.drone_id == drone_id
    ).first()
    
    if not performance:
        performance = DronePerformance(drone_id=drone_id)
        db.add(performance)
    
    performance.total_deliveries += deliveries_completed
    performance.total_distance_km += distance_km
    performance.total_flight_time_minutes += flight_time_minutes
    
    if performance.total_flight_time_minutes > 0:
        performance.average_speed = (performance.total_distance_km / performance.total_flight_time_minutes) * 60
    
    # Calculate success rate
    if deliveries_completed > 0:
        total = performance.total_deliveries
        successes = int(total * performance.success_rate / 100)
        if success:
            successes += 1
        performance.success_rate = (successes / total) * 100
    
    performance.last_updated = datetime.utcnow()
    db.commit()
    
    return {"message": "Performance updated", "performance": performance}

# --- BATTERY ---

@app.post("/battery/log")
async def log_battery_status(
    drone_id: int,
    battery_level: float,
    voltage: Optional[float] = None,
    temperature: Optional[float] = None,
    health_percentage: Optional[float] = None,
    charge_cycles: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Log trạng thái pin (được gọi định kỳ từ drone)"""
    log_entry = DroneBatteryLog(
        drone_id=drone_id,
        battery_level=battery_level,
        voltage=voltage,
        temperature=temperature,
        health_percentage=health_percentage,
        charge_cycles=charge_cycles
    )
    db.add(log_entry)
    
    # Check if need alert
    if battery_level < 20:
        alert = DroneAlert(
            drone_id=drone_id,
            alert_type="low_battery",
            severity="high" if battery_level < 10 else "medium",
            message=f"Battery level critically low: {battery_level}%"
        )
        db.add(alert)
    
    if health_percentage and health_percentage < 60:
        alert = DroneAlert(
            drone_id=drone_id,
            alert_type="battery_health",
            severity="high",
            message=f"Battery health degraded: {health_percentage}%"
        )
        db.add(alert)
    
    db.commit()
    
    return {"message": "Battery status logged"}

@app.get("/battery/{drone_id}/health")
async def get_battery_health(drone_id: int, db: Session = Depends(get_db)):
    """Phân tích sức khỏe pin"""
    logs = db.query(DroneBatteryLog).filter(
        DroneBatteryLog.drone_id == drone_id
    ).order_by(DroneBatteryLog.logged_at.desc()).limit(50).all()
    
    analysis = check_battery_health(logs)
    
    return {
        "drone_id": drone_id,
        "recent_logs": logs[:10],
        "health_analysis": analysis
    }

# --- ALERTS ---

@app.get("/alerts", response_model=List[AlertResponse])
async def get_all_alerts(
    resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Xem tất cả cảnh báo (Admin)"""
    query = db.query(DroneAlert)
    
    if resolved is not None:
        query = query.filter(DroneAlert.is_resolved == (1 if resolved else 0))
    
    if severity:
        query = query.filter(DroneAlert.severity == severity)
    
    alerts = query.order_by(DroneAlert.created_at.desc()).limit(100).all()
    
    return alerts

@app.get("/alerts/{drone_id}", response_model=List[AlertResponse])
async def get_drone_alerts(drone_id: int, db: Session = Depends(get_db)):
    """Cảnh báo của 1 drone"""
    alerts = db.query(DroneAlert).filter(
        DroneAlert.drone_id == drone_id
    ).order_by(DroneAlert.created_at.desc()).all()
    
    return alerts

@app.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Đánh dấu cảnh báo đã xử lý"""
    user = await verify_token(authorization)
    if not user or user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    
    alert = db.query(DroneAlert).filter(DroneAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    
    alert.is_resolved = 1
    alert.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Alert resolved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)