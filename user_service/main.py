from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import bcrypt 
from typing import Optional, List
import os
import time
# 👇👇👇 BẠN ĐANG THIẾU DÒNG QUAN TRỌNG NÀY 👇👇👇
from pydantic import BaseModel, EmailStr
# ==========================================
# CONFIGURATION
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET", "secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Database setup
engine = create_engine(DATABASE_URL, echo=False)  # [FIX] Tắt echo để clean logs
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# [CRITICAL] Password hashing - PHẢI dùng bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================================
# DATABASE MODELS
# ==========================================
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(20))
    address = Column(String(500))
    role = Column(String(20), default="customer")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Restaurant fields
    restaurant_name = Column(String(255))
    restaurant_description = Column(Text)
    restaurant_image = Column(String(500))
    city = Column(String(100))
    status = Column(String(20), default="active")

# ==========================================
# PYDANTIC MODELS
# ==========================================
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class RestaurantCreate(UserRegister):
    restaurant_name: str
    restaurant_description: Optional[str] = None
    city: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    role: str
    is_active: bool
    restaurant_name: Optional[str] = None
    restaurant_description: Optional[str] = None
    restaurant_image: Optional[str] = None
    city: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# ==========================================
# APP SETUP
# ==========================================
app = FastAPI(title="User Service", version="1.0.0")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
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

# Helper functions
def verify_password(plain_password, hashed_password):
    """Verify password trực tiếp bằng bcrypt (Bỏ qua passlib)"""
    try:
        # Chuyển đổi sang bytes vì bcrypt yêu cầu bytes
        password_bytes = plain_password.encode('utf-8')
        
        # hashed_password từ DB có thể đang là string, cần encode
        hash_bytes = hashed_password.encode('utf-8')

        # Dùng trực tiếp bcrypt để check
        is_correct = bcrypt.checkpw(password_bytes, hash_bytes)
        print(f"🔍 bcrypt check result: {is_correct}")
        return is_correct
        
    except Exception as e:
        print(f"❌ LỖI CODE VERIFY: {e}")
        return False

def get_password_hash(password):
    """Hash password với bcrypt"""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    [FIX CRITICAL] KHÔNG tạo admin tự động
    Vì init-db.sql đã tạo sẵn với hash cố định
    """
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        try:
            Base.metadata.create_all(bind=engine)
            print("=" * 60)
            print("✅ USER SERVICE STARTED")
            print("=" * 60)
            
            # [FIX] Không tạo admin nữa, dùng data từ init-db.sql
            db = SessionLocal()
            user_count = db.query(User).count()
            admin = db.query(User).filter(User.username == "admin").first()
            
            print(f"📊 Total users in DB: {user_count}")
            if admin:
                print(f"👤 Admin exists: {admin.username} (role: {admin.role})")
            
            # [DEBUG] List all users
            users = db.query(User).all()
            print(f"\n📋 User list:")
            for u in users[:5]:  # Chỉ show 5 users đầu
                print(f"   - {u.username} ({u.role})")
            
            db.close()
            print("=" * 60)
            break
        except Exception as e:
            retry_count += 1
            print(f"❌ Database connection failed (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(2)

# ==========================================
# ROUTES
# ==========================================

@app.get("/")
async def root():
    return {"service": "User Service", "status": "running", "version": "1.0.0"}

# --- AUTH ---

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Đăng ký KHÁCH HÀNG"""
    print(f"📝 Register request: {user_data.username}")
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        address=user_data.address,
        role="customer",
        is_active=1
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print(f"✅ User registered: {db_user.username}")
    return db_user

@app.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    [CRITICAL] Login endpoint
    - OAuth2PasswordRequestForm: application/x-www-form-urlencoded
    - Returns JWT token + user info
    """
    print("=" * 60)
    print(f"🔐 LOGIN ATTEMPT")
    print(f"   Username: {form_data.username}")
    print(f"   Password: {'*' * len(form_data.password)}")
    
    # 1. Find user
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user:
        print(f"❌ User not found: {form_data.username}")
        print("=" * 60)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ User found: {user.username}")
    print(f"   Role: {user.role}")
    print(f"   Active: {user.is_active}")
    print(f"   Hash in DB: {user.hashed_password[:30]}...")
    
    # [DEBUG] In ra password để test (CHỈ DÙNG KHI DEBUG)
    print(f"   Password nhập vào: {form_data.password}")
    
    # 2. Verify password
    print(f"🔍 Verifying password...")
    password_valid = verify_password(form_data.password, user.hashed_password)
    
    print(f"   bcrypt.checkpw result: {password_valid}")
    
    if not password_valid:
        print(f"❌ Wrong password")
        print(f"   Expected hash: {user.hashed_password}")
        print(f"   Password given: {form_data.password}")
        
        # [DEBUG] Test hash bằng tay
        import bcrypt
        try:
            manual_check = bcrypt.checkpw(
                form_data.password.encode('utf-8'), 
                user.hashed_password.encode('utf-8')
            )
            print(f"   Manual bcrypt check: {manual_check}")
        except Exception as e:
            print(f"   Manual check error: {e}")
        
        print("=" * 60)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ Password correct!")
    
    # 3. Check active
    if not user.is_active:
        print(f"❌ User inactive")
        print("=" * 60)
        raise HTTPException(status_code=400, detail="User account is inactive")
    
    # 4. Create token
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        }
    )
    
    print(f"✅ Token created: {access_token[:30]}...")
    print(f"✅ LOGIN SUCCESS for {user.username}")
    print("=" * 60)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": user
    }

@app.get("/verify-token")
async def verify_user_token(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Verify token (Internal)"""
    user_id = token_data.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name
    }

# --- ADMIN ---

@app.post("/admin/create-restaurant", response_model=UserResponse)
async def create_restaurant_account(
    user_data: RestaurantCreate, 
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin tạo Restaurant"""
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_restaurant = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role="restaurant",
        restaurant_name=user_data.restaurant_name,
        restaurant_description=user_data.restaurant_description,
        city=user_data.city,
        is_active=1
    )
    db.add(new_restaurant)
    db.commit()
    db.refresh(new_restaurant)
    return new_restaurant

@app.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = None,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin xem User list"""
    if token_data.get("role") != "admin":
         raise HTTPException(status_code=403, detail="Admin access required")
         
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()

# --- PUBLIC ---

@app.get("/restaurants", response_model=List[UserResponse])
async def list_restaurants(db: Session = Depends(get_db)):
    """Public: Xem danh sách nhà hàng"""
    restaurants = db.query(User).filter(
        User.role == "restaurant", 
        User.is_active == 1
    ).all()
    print(f"📋 Restaurants found: {len(restaurants)}")
    return restaurants

@app.get("/restaurants/{restaurant_id}", response_model=UserResponse)
async def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """Public: Chi tiết nhà hàng"""
    restaurant = db.query(User).filter(
        User.id == restaurant_id, 
        User.role == "restaurant"
    ).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant

# --- PROFILE ---

@app.get("/users/me", response_model=UserResponse)
async def get_my_profile(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/me", response_model=UserResponse)
async def update_profile(
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if full_name: user.full_name = full_name
    if phone: user.phone = phone
    if address: user.address = address
    db.commit()
    db.refresh(user)
    return user


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)