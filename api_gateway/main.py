from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import os

# ==========================================
# CONFIGURATION
# ==========================================
SERVICE_URLS = {
    "user": os.getenv("USER_SERVICE_URL", "http://user_service:8000"),
    "product": os.getenv("PRODUCT_SERVICE_URL", "http://product_service:8000"),
    "order": os.getenv("ORDER_SERVICE_URL", "http://order_service:8000"),
    "payment": os.getenv("PAYMENT_SERVICE_URL", "http://payment_service:8000"),
}

# ==========================================
# APP SETUP
# ==========================================
app = FastAPI(
    title="API Gateway",
    description="Central gateway for DroneFood",
    version="1.0.0"
)

# CORS - Allow frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# ROUTING LOGIC
# ==========================================

def get_service_url(path: str) -> str:
    """
    Xác định service dựa trên path
    
    CRITICAL ROUTES (No /api prefix):
    - /token → User Service
    - /register → User Service  
    - /verify-token → User Service
    
    STANDARD ROUTES:
    - /api/users/* → User Service
    - /api/products/* → Product Service
    - /api/orders/* → Order Service
    - /api/payments/* → Payment Service
    """
    
    # [CRITICAL] Special auth routes
    if path in ["/token", "/register", "/verify-token"]:
        print(f"🔑 Auth route detected: {path} → User Service")
        return SERVICE_URLS["user"]
    
    # Static files
    if path.startswith("/api/products/static"):
        return SERVICE_URLS["product"]
    
    # Standard API routes
    if path.startswith("/api/users"):
        return SERVICE_URLS["user"]
    elif path.startswith("/api/products"):
        return SERVICE_URLS["product"]
    elif path.startswith("/api/orders"):
        return SERVICE_URLS["order"]
    elif path.startswith("/api/payments"):
        return SERVICE_URLS["payment"]
    else:
        raise HTTPException(status_code=404, detail=f"No service found for path: {path}")

def strip_api_prefix(path: str) -> str:
    """
    Chuyển đổi path từ Gateway → Service
    
    Examples:
    - /token → /token (giữ nguyên)
    - /register → /register (giữ nguyên)
    - /api/users/restaurants → /restaurants
    - /api/products/static/images/x.jpg → /static/images/x.jpg
    """
    
    # Special routes: keep as-is
    if path in ["/token", "/register", "/verify-token"]:
        return path
    
    # Static files: strip /api/products
    if path.startswith("/api/products/static"):
        return path.replace("/api/products", "", 1)
    
    # Standard routes: strip /api/{service}
    if path.startswith("/api/users"):
        stripped = path.replace("/api/users", "", 1)
        return stripped if stripped else "/"
    elif path.startswith("/api/products"):
        stripped = path.replace("/api/products", "", 1)
        return stripped if stripped else "/"
    elif path.startswith("/api/orders"):
        stripped = path.replace("/api/orders", "", 1)
        return stripped if stripped else "/"
    elif path.startswith("/api/payments"):
        stripped = path.replace("/api/payments", "", 1)
        return stripped if stripped else "/"
    
    return path

# ==========================================
# PROXY ENDPOINT
# ==========================================

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    """Forward requests to appropriate service"""
    
    full_path = f"/{path}"
    
    # DEBUG logging
    print("=" * 60)
    print(f"📥 GATEWAY REQUEST:")
    print(f"   Method: {request.method}")
    print(f"   Path: {full_path}")
    print(f"   Headers: {dict(request.headers)}")
    print(f"   Query: {dict(request.query_params)}")
    
    # 1. Determine service
    try:
        service_url = get_service_url(full_path)
        print(f"✅ Service: {service_url}")
    except HTTPException as e:
        print(f"❌ No service found for: {full_path}")
        return JSONResponse(
            status_code=e.status_code,
            content={"error": str(e.detail)}
        )
    
    # 2. Build target URL
    target_path = strip_api_prefix(full_path)
    target_url = f"{service_url}{target_path}"
    print(f"🎯 Target URL: {target_url}")
    
    # 3. Copy headers (exclude host, content-length)
    headers = {
        key: value for key, value in request.headers.items() 
        if key.lower() not in ["host", "content-length"]
    }
    
    # 4. Get query params
    query_params = dict(request.query_params)
    
    # 5. Get body
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
        print(f"📦 Body: {body.decode('utf-8') if body else 'None'}")
    
    # 6. Forward request
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=query_params,
                content=body,
            )
            
            print(f"📤 Response Status: {response.status_code}")
            print("=" * 60)
            
            # Return response
            return StreamingResponse(
                response.iter_bytes(),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
            
        except httpx.RequestError as e:
            print(f"❌ Request error: {e}")
            print("=" * 60)
            return JSONResponse(
                status_code=503,
                content={"error": f"Service unavailable: {str(e)}"}
            )

# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/")
async def root():
    return {
        "service": "API Gateway",
        "status": "running",
        "routes": {
            "auth": {
                "/token": "POST - Login (OAuth2 form)",
                "/register": "POST - Register",
                "/verify-token": "GET - Verify token"
            },
            "api": {
                "/api/users/*": "User Service",
                "/api/products/*": "Product Service",
                "/api/orders/*": "Order Service",
                "/api/payments/*": "Payment Service"
            }
        }
    }

@app.get("/health")
async def health_check():
    """Check service health"""
    status = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in SERVICE_URLS.items():
            try:
                response = await client.get(f"{url}/")
                status[name] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                status[name] = "unreachable"
    
    return {
        "gateway": "healthy",
        "services": status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)