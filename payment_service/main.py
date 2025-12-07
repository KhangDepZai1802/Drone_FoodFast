from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import time
import httpx
import uuid
import random

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order_service:8000") # [MỚI] Thêm URL Order Service

# Database setup
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# MODELS
# ==========================================
class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")
    transaction_id = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PaymentCreate(BaseModel):
    order_id: int
    amount: float
    payment_method: str

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    amount: float
    payment_method: str
    status: str
    transaction_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PaymentStatusUpdate(BaseModel):
    status: str

# ==========================================
# APP SETUP
# ==========================================
app = FastAPI(title="Payment Service", version="1.0.0")

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
            print("✓ Payment database tables created successfully")
            break
        except Exception as e:
            retry_count += 1
            print(f"Database connection failed (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(2)

# ==========================================
# HELPERS
# ==========================================
async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{USER_SERVICE_URL}/verify-token",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=401, detail="Invalid token")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="User service unavailable")
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=401, detail="Authentication failed")

def process_payment_simulation(payment_method: str, amount: float) -> dict:
    """Simulate payment processing"""
    # Trong thực tế sẽ gọi API Stripe/PayPal/Momo ở đây
    time.sleep(0.5)
    success = random.random() < 0.95 # 95% thành công
    
    if success:
        return {
            "success": True,
            "transaction_id": f"TXN-{uuid.uuid4().hex[:12].upper()}",
            "message": "Payment processed successfully"
        }
    else:
        return {
            "success": False,
            "transaction_id": None,
            "message": "Payment failed"
        }

# ==========================================
# ROUTES
# ==========================================
@app.get("/")
async def root():
    return {"service": "Payment Service", "status": "running"}

@app.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment: PaymentCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Create and process payment"""
    user = await verify_token(authorization)
    
    # Check duplicate
    existing = db.query(Payment).filter(Payment.order_id == payment.order_id).first()
    db_payment = None
    if existing:
        # Nếu đã hoàn thành, báo lỗi
        if existing.status == "completed":
            raise HTTPException(status_code=400, detail="Payment already exists for this order")

        # Nếu có record trước đó chưa hoàn thành (failed/processing), cập nhật lại và tiếp tục xử lý
        existing.amount = payment.amount
        existing.payment_method = payment.payment_method
        existing.status = "processing"
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        db_payment = existing
    else:
        # Tạo record payment mới
        db_payment = Payment(
            order_id=payment.order_id,
            user_id=user["user_id"],
            amount=payment.amount,
            payment_method=payment.payment_method,
            status="processing"
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
    
    # Xử lý thanh toán (Giả lập)
    result = process_payment_simulation(payment.payment_method, payment.amount)
    
    if result["success"]:
        db_payment.status = "completed"
        db_payment.transaction_id = result["transaction_id"]
        
        # [QUAN TRỌNG] Gọi Order Service để cập nhật trạng thái đơn hàng
        # Forward token của user để Order Service xác thực quyền sở hữu
        try:
            async with httpx.AsyncClient() as client:
                await client.put(
                    f"{ORDER_SERVICE_URL}/orders/{payment.order_id}/status",
                    json={"status": "confirmed"}, # Chuyển sang CONFIRMED
                    headers={"Authorization": authorization}
                )
        except Exception as e:
            print(f"⚠️ Failed to update order status: {e}")
            # Có thể cần cơ chế retry hoặc log để xử lý sau
            
    else:
        db_payment.status = "failed"
    
    db_payment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_payment)
    
    return db_payment

@app.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    authorization: str = Header(None),
    order_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    user = await verify_token(authorization)
    
    query = db.query(Payment)
    if user["role"] != "admin":
        query = query.filter(Payment.user_id == user["user_id"])
    
    if order_id:
        query = query.filter(Payment.order_id == order_id)
    
    payments = query.order_by(Payment.created_at.desc()).all()
    return payments

@app.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = await verify_token(authorization)
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    # Check quyền xem
    if user["role"] != "admin" and payment.user_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return payment

@app.get("/payments/order/{order_id}", response_model=PaymentResponse)
async def get_payment_by_order(
    order_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = await verify_token(authorization)
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    if user["role"] != "admin" and payment.user_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return payment

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)