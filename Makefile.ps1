# PowerShell Makefile for Drone Delivery System

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Drone Delivery System - Commands" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host "Usage: .\Makefile.ps1 <command>" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Green
    Write-Host "  build      - Build all Docker containers"
    Write-Host "  up         - Start all services"
    Write-Host "  down       - Stop all services"
    Write-Host "  restart    - Restart all services"
    Write-Host "  logs       - Show logs from all services"
    Write-Host "  clean      - Remove all containers and volumes"
    Write-Host "  ps         - Show running containers"
    Write-Host "  init       - Initialize with sample data"
    Write-Host ""
}

function Initialize-Data {
    Write-Host "Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host "`n=== INITIALIZING SAMPLE DATA ===" -ForegroundColor Cyan
    Write-Host ""
    
    # 1. Create customer account
    Write-Host "[1/4] Creating customer account..." -ForegroundColor Green
    $customer = @{
        email = "khach@gmail.com"
        username = "khach1"
        password = "123456"
        full_name = "Nguyen Van Khach"
        role = "customer"
        address = "123 Nguyen Hue, Q1, TP.HCM"
        phone = "0901234567"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8001/register" -Method Post -Body $customer -ContentType "application/json" -ErrorAction Stop
        Write-Host "SUCCESS: Customer created - khach1" -ForegroundColor Cyan
    }
    catch {
        Write-Host "INFO: Customer already exists or error occurred" -ForegroundColor Gray
    }
    
    # 2. Create 3 restaurants
    Write-Host "`n[2/4] Creating restaurants..." -ForegroundColor Green
    
    $restaurants = @(
        @{
            username = "res_pho"
            name = "Pho Ngon 24h"
            desc = "Pho bo truyen thong Ha Noi"
            items = @(
                @{name="Pho Bo Tai"; price=55000},
                @{name="Pho Ga"; price=45000},
                @{name="Pho Bo Vien"; price=50000}
            )
        },
        @{
            username = "res_pizza"
            name = "Pizza Italia"
            desc = "Pizza nuong cui chuan Y"
            items = @(
                @{name="Pizza Hai San"; price=120000},
                @{name="Pizza Pho Mai"; price=90000},
                @{name="Pizza Thap Cam"; price=110000}
            )
        },
        @{
            username = "res_burger"
            name = "Burger King VN"
            desc = "Burger bo My cao cap"
            items = @(
                @{name="Burger Bo Phomage"; price=65000},
                @{name="Burger Ga Sot Mayonnaise"; price=55000},
                @{name="Khoai Tay Chien Lon"; price=30000}
            )
        }
    )
    
    foreach ($restaurant in $restaurants) {
        $resData = @{
            email = "$($restaurant.username)@mail.com"
            username = $restaurant.username
            password = "123456"
            role = "restaurant"
            restaurant_name = $restaurant.name
            restaurant_description = $restaurant.desc
            full_name = "Manager"
        } | ConvertTo-Json
        
        try {
            $userResponse = Invoke-RestMethod -Uri "http://localhost:8001/register" -Method Post -Body $resData -ContentType "application/json" -ErrorAction Stop
            $resId = $userResponse.id
            
            Write-Host "SUCCESS: Restaurant created - $($restaurant.name) (ID: $resId)" -ForegroundColor Cyan
            
            # Create products for restaurant
            foreach ($item in $restaurant.items) {
                $prodData = @{
                    restaurant_id = $resId
                    name = $item.name
                    price = $item.price
                    description = "Mon ngon, tuoi ngon"
                    category = "Food"
                    preparation_time = 15
                    is_available = $true
                } | ConvertTo-Json
                
                try {
                    Invoke-RestMethod -Uri "http://localhost:8002/products" -Method Post -Body $prodData -ContentType "application/json" -ErrorAction Stop | Out-Null
                    Write-Host "  + Product added: $($item.name)" -ForegroundColor Gray
                }
                catch {
                    Write-Host "  WARNING: Failed to add product: $($item.name)" -ForegroundColor Yellow
                }
            }
        }
        catch {
            Write-Host "INFO: Restaurant $($restaurant.name) already exists" -ForegroundColor Gray
        }
    }
    
    # 3. Create additional drones
    Write-Host "`n[3/4] Creating drones..." -ForegroundColor Green
    $drones = @(
        @{name="Drone Delta"; model="DX-300"; payload=6.5},
        @{name="Drone Echo"; model="DX-400"; payload=8.0}
    )
    
    foreach ($drone in $drones) {
        $droneData = @{
            name = $drone.name
            model = $drone.model
            max_payload = $drone.payload
        } | ConvertTo-Json
        
        try {
            Invoke-RestMethod -Uri "http://localhost:8003/drones" -Method Post -Body $droneData -ContentType "application/json" -ErrorAction Stop | Out-Null
            Write-Host "SUCCESS: Drone created - $($drone.name)" -ForegroundColor Cyan
        }
        catch {
            Write-Host "INFO: Drone already exists" -ForegroundColor Gray
        }
    }
    
    # 4. Summary
    Write-Host "`n[4/4] Verification..." -ForegroundColor Green
    try {
        $restaurants = Invoke-RestMethod -Uri "http://localhost:8001/restaurants" -Method Get -ErrorAction Stop
        $products = Invoke-RestMethod -Uri "http://localhost:8002/products" -Method Get -ErrorAction Stop
        $drones = Invoke-RestMethod -Uri "http://localhost:8003/drones" -Method Get -ErrorAction Stop
        
        Write-Host "  Restaurants: $($restaurants.Count)" -ForegroundColor White
        Write-Host "  Products: $($products.Count)" -ForegroundColor White
        Write-Host "  Drones: $($drones.Count)" -ForegroundColor White
    }
    catch {
        Write-Host "  WARNING: Could not verify data" -ForegroundColor Yellow
    }
    
    Write-Host "`n=== INITIALIZATION COMPLETE ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "--- LOGIN CREDENTIALS ---" -ForegroundColor Yellow
    Write-Host "Customer:" -ForegroundColor White
    Write-Host "  Username: khach1" -ForegroundColor Cyan
    Write-Host "  Password: 123456" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Restaurants:" -ForegroundColor White
    Write-Host "  res_pho, res_pizza, res_burger" -ForegroundColor Cyan
    Write-Host "  Password: 123456" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Admin:" -ForegroundColor White
    Write-Host "  Username: admin" -ForegroundColor Cyan
    Write-Host "  Password: admin123" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Access at: http://localhost:3000" -ForegroundColor Magenta
    Write-Host ""
}

# Support functions
function Build-Services { 
    Write-Host "Building Docker images..." -ForegroundColor Yellow
    docker-compose build 
}

function Start-Services { 
    Write-Host "Starting services..." -ForegroundColor Yellow
    docker-compose up -d 
    Write-Host "Services started!" -ForegroundColor Green
}

function Stop-Services { 
    Write-Host "Stopping services..." -ForegroundColor Yellow
    docker-compose down 
    Write-Host "Services stopped!" -ForegroundColor Green
}

function Restart-Services { 
    Write-Host "Restarting services..." -ForegroundColor Yellow
    docker-compose restart 
}

function Show-Logs { 
    docker-compose logs -f 
}

function Show-Status { 
    docker-compose ps 
}

function Clean-All { 
    Write-Host "Cleaning up..." -ForegroundColor Red
    docker-compose down -v --rmi all 
    Write-Host "Cleanup complete!" -ForegroundColor Green
}

# Main Router
switch ($Command.ToLower()) {
    "build" { Build-Services }
    "up" { Start-Services }
    "down" { Stop-Services }
    "restart" { Restart-Services }
    "logs" { Show-Logs }
    "clean" { Clean-All }
    "ps" { Show-Status }
    "init" { Initialize-Data }
    "help" { Show-Help }
    default { Show-Help }
}