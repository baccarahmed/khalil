from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
import stripe
import asyncio
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Stripe configuration
stripe.api_key = os.environ['STRIPE_SECRET_KEY']

# JWT configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                self.disconnect(user_id)
    
    async def broadcast_to_drivers(self, message: dict):
        for user_id, connection in self.active_connections.items():
            if user_id.startswith("driver_"):
                try:
                    await connection.send_json(message)
                except:
                    self.disconnect(user_id)

manager = ConnectionManager()

# Enums
class UserType(str, Enum):
    CUSTOMER = "customer"
    DRIVER = "driver"
    RESTAURANT = "restaurant"
    ADMIN = "admin"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    phone: str
    user_type: UserType
    location: Optional[Dict[str, float]] = None  # {"lat": 0.0, "lng": 0.0}
    address: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    name: str
    phone: str
    user_type: UserType
    location: Optional[Dict[str, float]] = None
    address: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    user_type: UserType

class Restaurant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    address: str
    location: Dict[str, float]  # {"lat": 0.0, "lng": 0.0}
    cuisine_type: str
    owner_id: str
    phone: str
    image_url: Optional[str] = None
    rating: float = 0.0
    is_active: bool = True
    delivery_fee: float = 2.99
    min_order: float = 10.0
    estimated_delivery_time: int = 30  # minutes
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RestaurantCreate(BaseModel):
    name: str
    description: str
    address: str
    location: Dict[str, float]
    cuisine_type: str
    phone: str
    image_url: Optional[str] = None
    delivery_fee: float = 2.99
    min_order: float = 10.0
    estimated_delivery_time: int = 30

class MenuItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    restaurant_id: str
    name: str
    description: str
    price: float
    category: str
    image_url: Optional[str] = None
    is_available: bool = True
    preparation_time: int = 15  # minutes
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MenuItemCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    image_url: Optional[str] = None
    preparation_time: int = 15

class OrderItem(BaseModel):
    menu_item_id: str
    quantity: int
    special_instructions: Optional[str] = None

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    restaurant_id: str
    driver_id: Optional[str] = None
    items: List[OrderItem]
    subtotal: float
    delivery_fee: float
    tax: float
    total: float
    status: OrderStatus = OrderStatus.PENDING
    delivery_address: str
    delivery_location: Dict[str, float]
    payment_intent_id: Optional[str] = None
    estimated_delivery_time: datetime
    actual_delivery_time: Optional[datetime] = None
    special_instructions: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OrderCreate(BaseModel):
    restaurant_id: str
    items: List[OrderItem]
    delivery_address: str
    delivery_location: Dict[str, float]
    special_instructions: Optional[str] = None

class PaymentIntent(BaseModel):
    client_secret: str
    amount: int

# Utility functions
def create_jwt_token(user_data: dict):
    payload = {
        "user_id": user_data["id"],
        "user_type": user_data["user_type"],
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_jwt_token(credentials.credentials)
    user = await db.users.find_one({"id": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

def calculate_order_total(items: List[OrderItem], restaurant: Restaurant):
    subtotal = 0
    for item in items:
        # In real app, fetch menu item price from database
        subtotal += item.quantity * 12.99  # placeholder price
    
    delivery_fee = restaurant.delivery_fee
    tax = subtotal * 0.08  # 8% tax
    total = subtotal + delivery_fee + tax
    
    return subtotal, delivery_fee, tax, total

# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# Authentication endpoints
@api_router.post("/auth/register")
async def register_user(user: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email, "user_type": user.user_type})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_obj = User(**user.dict())
    await db.users.insert_one(user_obj.dict())
    
    token = create_jwt_token(user_obj.dict())
    return {"user": user_obj, "token": token}

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email, "user_type": login_data.user_type})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_obj = User(**user)
    token = create_jwt_token(user_obj.dict())
    return {"user": user_obj, "token": token}

# Restaurant endpoints
@api_router.post("/restaurants")
async def create_restaurant(restaurant: RestaurantCreate, current_user: User = Depends(get_current_user)):
    if current_user.user_type != UserType.RESTAURANT:
        raise HTTPException(status_code=403, detail="Only restaurant users can create restaurants")
    
    restaurant_obj = Restaurant(**restaurant.dict(), owner_id=current_user.id)
    await db.restaurants.insert_one(restaurant_obj.dict())
    return restaurant_obj

@api_router.get("/restaurants", response_model=List[Restaurant])
async def get_restaurants():
    restaurants = await db.restaurants.find({"is_active": True}).to_list(100)
    return [Restaurant(**restaurant) for restaurant in restaurants]

@api_router.get("/restaurants/{restaurant_id}")
async def get_restaurant(restaurant_id: str):
    restaurant = await db.restaurants.find_one({"id": restaurant_id})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return Restaurant(**restaurant)

# Menu endpoints
@api_router.post("/restaurants/{restaurant_id}/menu")
async def add_menu_item(restaurant_id: str, item: MenuItemCreate, current_user: User = security):
    if current_user.user_type != UserType.RESTAURANT:
        raise HTTPException(status_code=403, detail="Only restaurant users can add menu items")
    
    restaurant = await db.restaurants.find_one({"id": restaurant_id, "owner_id": current_user.id})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found or not owned by user")
    
    item_obj = MenuItem(**item.dict(), restaurant_id=restaurant_id)
    await db.menu_items.insert_one(item_obj.dict())
    return item_obj

@api_router.get("/restaurants/{restaurant_id}/menu", response_model=List[MenuItem])
async def get_menu(restaurant_id: str):
    menu_items = await db.menu_items.find({"restaurant_id": restaurant_id, "is_available": True}).to_list(100)
    return [MenuItem(**item) for item in menu_items]

# Order endpoints
@api_router.post("/orders")
async def create_order(order: OrderCreate, current_user: User = security):
    if current_user.user_type != UserType.CUSTOMER:
        raise HTTPException(status_code=403, detail="Only customers can create orders")
    
    restaurant = await db.restaurants.find_one({"id": order.restaurant_id})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    restaurant_obj = Restaurant(**restaurant)
    subtotal, delivery_fee, tax, total = calculate_order_total(order.items, restaurant_obj)
    
    # Create Stripe Payment Intent
    payment_intent = stripe.PaymentIntent.create(
        amount=int(total * 100),  # Convert to cents
        currency='usd',
        metadata={'customer_id': current_user.id, 'restaurant_id': order.restaurant_id}
    )
    
    estimated_delivery_time = datetime.utcnow() + timedelta(minutes=restaurant_obj.estimated_delivery_time)
    
    order_obj = Order(
        **order.dict(),
        customer_id=current_user.id,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        tax=tax,
        total=total,
        payment_intent_id=payment_intent.id,
        estimated_delivery_time=estimated_delivery_time
    )
    
    await db.orders.insert_one(order_obj.dict())
    
    # Broadcast to available drivers
    await manager.broadcast_to_drivers({
        "type": "new_order",
        "order": order_obj.dict()
    })
    
    return {
        "order": order_obj,
        "client_secret": payment_intent.client_secret
    }

@api_router.get("/orders", response_model=List[Order])
async def get_orders(current_user: User = security):
    if current_user.user_type == UserType.CUSTOMER:
        orders = await db.orders.find({"customer_id": current_user.id}).to_list(100)
    elif current_user.user_type == UserType.DRIVER:
        orders = await db.orders.find({"driver_id": current_user.id}).to_list(100)
    elif current_user.user_type == UserType.RESTAURANT:
        restaurants = await db.restaurants.find({"owner_id": current_user.id}).to_list(10)
        restaurant_ids = [r["id"] for r in restaurants]
        orders = await db.orders.find({"restaurant_id": {"$in": restaurant_ids}}).to_list(100)
    else:
        orders = await db.orders.find().to_list(100)
    
    return [Order(**order) for order in orders]

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: OrderStatus, current_user: User = security):
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check permissions based on user type and status
    if current_user.user_type == UserType.RESTAURANT and status in [OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY]:
        pass
    elif current_user.user_type == UserType.DRIVER and status in [OrderStatus.PICKED_UP, OrderStatus.DELIVERED]:
        pass
    else:
        raise HTTPException(status_code=403, detail="Not authorized to update this status")
    
    update_data = {"status": status, "updated_at": datetime.utcnow()}
    if status == OrderStatus.DELIVERED:
        update_data["actual_delivery_time"] = datetime.utcnow()
    
    await db.orders.update_one({"id": order_id}, {"$set": update_data})
    
    # Send real-time updates
    await manager.send_personal_message({
        "type": "order_status_update",
        "order_id": order_id,
        "status": status
    }, order["customer_id"])
    
    if order.get("driver_id"):
        await manager.send_personal_message({
            "type": "order_status_update",
            "order_id": order_id,
            "status": status
        }, order["driver_id"])
    
    return {"message": "Order status updated"}

@api_router.post("/orders/{order_id}/assign-driver")
async def assign_driver(order_id: str, current_user: User = security):
    if current_user.user_type != UserType.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can accept orders")
    
    order = await db.orders.find_one({"id": order_id, "driver_id": None})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or already assigned")
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {"driver_id": current_user.id, "status": OrderStatus.CONFIRMED, "updated_at": datetime.utcnow()}}
    )
    
    # Notify customer
    await manager.send_personal_message({
        "type": "driver_assigned",
        "order_id": order_id,
        "driver": current_user.dict()
    }, order["customer_id"])
    
    return {"message": "Driver assigned to order"}

# Driver location update
@api_router.post("/drivers/location")
async def update_driver_location(location: Dict[str, float], current_user: User = security):
    if current_user.user_type != UserType.DRIVER:
        raise HTTPException(status_code=403, detail="Only drivers can update location")
    
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"location": location}}
    )
    
    # Get active orders for this driver
    orders = await db.orders.find({"driver_id": current_user.id, "status": {"$in": [OrderStatus.PICKED_UP]}}).to_list(10)
    
    # Send location updates to customers with active orders
    for order in orders:
        await manager.send_personal_message({
            "type": "driver_location_update",
            "order_id": order["id"],
            "location": location
        }, order["customer_id"])
    
    return {"message": "Location updated"}

# Analytics endpoint
@api_router.get("/analytics")
async def get_analytics(current_user: User = security):
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_orders = await db.orders.count_documents({})
    total_users = await db.users.count_documents({})
    total_restaurants = await db.restaurants.count_documents({})
    
    # Revenue calculation
    completed_orders = await db.orders.find({"status": OrderStatus.DELIVERED}).to_list(1000)
    total_revenue = sum(order.get("total", 0) for order in completed_orders)
    
    return {
        "total_orders": total_orders,
        "total_users": total_users,
        "total_restaurants": total_restaurants,
        "total_revenue": total_revenue,
        "completed_orders": len(completed_orders)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
