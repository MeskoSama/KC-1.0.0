from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Secret
JWT_SECRET = os.environ.get('JWT_SECRET', 'minecraft-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"

# Stripe
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# Server codes mapping
SERVER_CODES = {
    "10194": "NIM",
    "10997": "GRP",
    "20664": "VDD",
    "90154": "KKD"
}

# Currency purchase rates (USD to in-game currency)
CURRENCY_RATES = {
    "NIM": 4081.63,  # 10,000 NIM = $2.45
    "GRP": 4081.63,
    "VDD": 4081.63,
    "KKD": 4081.63
}

# Rank prices
RANK_PRICES = {
    "Germania Empire": 3.00,
    "FIP": 1.00,
    "VIP": 3.00,
    "WIP": 7.50
}

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    minecraft_username: str
    password_hash: str
    server_code: str
    currency_type: str
    balances: Dict[str, float] = Field(default_factory=lambda: {"NIM": 0, "GRP": 0, "VDD": 0, "KKD": 0})
    owned_ranks: List[str] = Field(default_factory=list)
    owned_houses: List[str] = Field(default_factory=list)
    total_spent: float = 0.0
    total_transactions: int = 0
    created_at: str

class UserRegister(BaseModel):
    minecraft_username: str
    password: str
    server_code: str

class UserLogin(BaseModel):
    minecraft_username: str
    password: str
    server_code: str

class House(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    location: str
    price_usd: Optional[float] = None
    price_currency: Optional[Dict[str, float]] = None
    owner_id: Optional[str] = None
    owner_username: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    status: str = "available"  # available, pending, sold, rented
    listed_at: str
    sold_at: Optional[str] = None
    admin_approved: bool = False

class HouseListing(BaseModel):
    name: str
    description: str
    location: str
    price_usd: Optional[float] = None
    price_currency: Optional[Dict[str, float]] = None
    images: List[str] = Field(default_factory=list)

class Bounty(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bounty_type: str  # "pvp" or "quest"
    title: str
    description: str
    reward_currency: str
    reward_amount: float
    target_player: Optional[str] = None  # For PvP bounties
    creator_id: str
    creator_username: str
    status: str = "active"  # active, completed, expired
    completed_by: Optional[str] = None
    completed_by_username: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

class BountyCreate(BaseModel):
    bounty_type: str
    title: str
    description: str
    reward_currency: str
    reward_amount: float
    target_player: Optional[str] = None

class CheckoutRequest(BaseModel):
    package_type: str  # "currency", "rank"
    package_id: str
    currency_type: Optional[str] = None  # For currency purchases
    quantity: Optional[float] = 1.0

# Utility Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# Auth Routes
@api_router.post("/auth/register")
async def register(data: UserRegister):
    # Validate server code
    if data.server_code not in SERVER_CODES:
        raise HTTPException(status_code=400, detail="Invalid server code")
    
    # Check if username already exists
    existing = await db.users.find_one({"minecraft_username": data.minecraft_username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    currency_type = SERVER_CODES[data.server_code]
    user = User(
        minecraft_username=data.minecraft_username,
        password_hash=hash_password(data.password),
        server_code=data.server_code,
        currency_type=currency_type,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    await db.users.insert_one(user.model_dump())
    token = create_jwt_token(user.id, user.minecraft_username)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.minecraft_username,
            "currency_type": user.currency_type,
            "balances": user.balances
        }
    }

@api_router.post("/auth/login")
async def login(data: UserLogin):
    user = await db.users.find_one({"minecraft_username": data.minecraft_username}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user["server_code"] != data.server_code:
        raise HTTPException(status_code=401, detail="Invalid server code")
    
    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user["id"], user["minecraft_username"])
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["minecraft_username"],
            "currency_type": user["currency_type"],
            "balances": user["balances"],
            "owned_ranks": user.get("owned_ranks", []),
            "owned_houses": user.get("owned_houses", [])
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["minecraft_username"],
        "currency_type": current_user["currency_type"],
        "balances": current_user["balances"],
        "owned_ranks": current_user.get("owned_ranks", []),
        "owned_houses": current_user.get("owned_houses", []),
        "total_spent": current_user.get("total_spent", 0),
        "total_transactions": current_user.get("total_transactions", 0)
    }

# Currency Purchase Routes
@api_router.get("/marketplace/currency-rates")
async def get_currency_rates():
    return {"rates": CURRENCY_RATES}

@api_router.get("/marketplace/rank-prices")
async def get_rank_prices():
    return {"ranks": RANK_PRICES}

# House Routes
@api_router.post("/houses/list")
async def list_house(house_data: HouseListing, current_user: dict = Depends(get_current_user)):
    house = House(
        **house_data.model_dump(),
        owner_id=current_user["id"],
        owner_username=current_user["minecraft_username"],
        listed_at=datetime.now(timezone.utc).isoformat(),
        status="pending",
        admin_approved=False
    )
    await db.houses.insert_one(house.model_dump())
    return {"message": "House listed successfully. Waiting for admin approval.", "house_id": house.id}

@api_router.get("/houses")
async def get_houses(status: Optional[str] = "available"):
    query = {}
    if status:
        query["status"] = status
    query["admin_approved"] = True
    houses = await db.houses.find(query, {"_id": 0}).to_list(1000)
    return {"houses": houses}

@api_router.get("/houses/pending")
async def get_pending_houses(current_user: dict = Depends(get_current_user)):
    # Simple admin check - you can enhance this
    houses = await db.houses.find({"admin_approved": False}, {"_id": 0}).to_list(1000)
    return {"houses": houses}

@api_router.post("/houses/{house_id}/approve")
async def approve_house(house_id: str, current_user: dict = Depends(get_current_user)):
    # Simple admin action - enhance with proper admin roles
    result = await db.houses.update_one(
        {"id": house_id},
        {"$set": {"admin_approved": True, "status": "available"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="House not found")
    return {"message": "House approved"}

@api_router.post("/houses/{house_id}/buy")
async def buy_house(house_id: str, payment_type: str, current_user: dict = Depends(get_current_user)):
    house = await db.houses.find_one({"id": house_id}, {"_id": 0})
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    if house["status"] != "available":
        raise HTTPException(status_code=400, detail="House not available")
    
    if payment_type == "currency":
        if not house.get("price_currency"):
            raise HTTPException(status_code=400, detail="Currency payment not available")
        
        user_currency = current_user["currency_type"]
        required_amount = house["price_currency"].get(user_currency, 0)
        
        if current_user["balances"][user_currency] < required_amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Deduct balance
        await db.users.update_one(
            {"id": current_user["id"]},
            {
                "$inc": {f"balances.{user_currency}": -required_amount, "total_transactions": 1},
                "$push": {"owned_houses": house_id}
            }
        )
        
        # Update house
        await db.houses.update_one(
            {"id": house_id},
            {"$set": {"status": "sold", "sold_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"message": "House purchased successfully with in-game currency"}
    
    # For USD payment, return checkout info (implement with Stripe)
    return {"message": "USD payment requires Stripe checkout", "amount": house.get("price_usd", 0)}

# Bounty Routes
@api_router.post("/bounties")
async def create_bounty(bounty_data: BountyCreate, current_user: dict = Depends(get_current_user)):
    # Check if user has enough balance
    user_currency = current_user["currency_type"]
    if current_user["balances"][bounty_data.reward_currency] < bounty_data.reward_amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Deduct reward from creator's balance
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$inc": {f"balances.{bounty_data.reward_currency}": -bounty_data.reward_amount}}
    )
    
    bounty = Bounty(
        **bounty_data.model_dump(),
        creator_id=current_user["id"],
        creator_username=current_user["minecraft_username"],
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    await db.bounties.insert_one(bounty.model_dump())
    return {"message": "Bounty created successfully", "bounty_id": bounty.id}

@api_router.get("/bounties")
async def get_bounties(bounty_type: Optional[str] = None, status: str = "active"):
    query = {"status": status}
    if bounty_type:
        query["bounty_type"] = bounty_type
    bounties = await db.bounties.find(query, {"_id": 0}).to_list(1000)
    return {"bounties": bounties}

@api_router.post("/bounties/{bounty_id}/complete")
async def complete_bounty(bounty_id: str, current_user: dict = Depends(get_current_user)):
    bounty = await db.bounties.find_one({"id": bounty_id}, {"_id": 0})
    if not bounty:
        raise HTTPException(status_code=404, detail="Bounty not found")
    
    if bounty["status"] != "active":
        raise HTTPException(status_code=400, detail="Bounty not active")
    
    # Award bounty
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$inc": {f"balances.{bounty['reward_currency']}": bounty["reward_amount"], "total_transactions": 1}}
    )
    
    await db.bounties.update_one(
        {"id": bounty_id},
        {
            "$set": {
                "status": "completed",
                "completed_by": current_user["id"],
                "completed_by_username": current_user["minecraft_username"],
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Bounty completed successfully"}

# Leaderboard Routes
@api_router.get("/leaderboard/richest")
async def get_richest_players(currency: str = "NIM", limit: int = 10):
    users = await db.users.find({}, {"_id": 0, "minecraft_username": 1, f"balances.{currency}": 1, "currency_type": 1}).to_list(1000)
    sorted_users = sorted(users, key=lambda x: x.get("balances", {}).get(currency, 0), reverse=True)[:limit]
    return {"leaderboard": sorted_users}

@api_router.get("/leaderboard/traders")
async def get_top_traders(limit: int = 10):
    users = await db.users.find(
        {},
        {"_id": 0, "minecraft_username": 1, "total_transactions": 1, "total_spent": 1}
    ).to_list(1000)
    sorted_users = sorted(users, key=lambda x: x.get("total_transactions", 0), reverse=True)[:limit]
    return {"leaderboard": sorted_users}

@api_router.get("/leaderboard/house-owners")
async def get_house_owners(limit: int = 10):
    users = await db.users.find(
        {"owned_houses": {"$exists": True, "$ne": []}},
        {"_id": 0, "minecraft_username": 1, "owned_houses": 1}
    ).to_list(1000)
    users_with_count = [{**u, "house_count": len(u.get("owned_houses", []))} for u in users]
    sorted_users = sorted(users_with_count, key=lambda x: x["house_count"], reverse=True)[:limit]
    return {"leaderboard": sorted_users}

# Stripe Payment Routes
@api_router.post("/checkout/session")
async def create_checkout_session(request: Request, checkout_req: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    try:
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        # Get origin from headers
        origin = request.headers.get("origin", host_url)
        success_url = f"{origin}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin}/marketplace"
        
        amount = 0.0
        metadata = {
            "user_id": current_user["id"],
            "username": current_user["minecraft_username"],
            "package_type": checkout_req.package_type,
            "package_id": checkout_req.package_id
        }
        
        if checkout_req.package_type == "currency":
            # Calculate amount based on currency rate
            if checkout_req.currency_type not in CURRENCY_RATES:
                raise HTTPException(status_code=400, detail="Invalid currency type")
            
            rate = CURRENCY_RATES[checkout_req.currency_type]
            amount = checkout_req.quantity / rate  # quantity in in-game currency to USD
            metadata["currency_type"] = checkout_req.currency_type
            metadata["quantity"] = str(checkout_req.quantity)
            
        elif checkout_req.package_type == "rank":
            if checkout_req.package_id not in RANK_PRICES:
                raise HTTPException(status_code=400, detail="Invalid rank")
            amount = RANK_PRICES[checkout_req.package_id]
        
        # Create checkout session
        checkout_request = CheckoutSessionRequest(
            amount=amount,
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )
        
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        payment_record = {
            "id": str(uuid.uuid4()),
            "session_id": session.session_id,
            "user_id": current_user["id"],
            "username": current_user["minecraft_username"],
            "amount": amount,
            "currency": "usd",
            "metadata": metadata,
            "payment_status": "pending",
            "status": "initiated",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payment_transactions.insert_one(payment_record)
        
        return {"url": session.url, "session_id": session.session_id}
        
    except Exception as e:
        logging.error(f"Checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, current_user: dict = Depends(get_current_user)):
    try:
        # First check if already processed
        payment = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if payment["payment_status"] == "paid":
            return {
                "status": payment["status"],
                "payment_status": payment["payment_status"],
                "message": "Payment already processed"
            }
        
        # Check with Stripe
        host_url = "https://pixeltraders.preview.emergentagent.com"  # Will be dynamic
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        checkout_status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update payment record
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": checkout_status.status,
                "payment_status": checkout_status.payment_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # If paid, process the purchase
        if checkout_status.payment_status == "paid":
            metadata = payment["metadata"]
            
            if metadata["package_type"] == "currency":
                currency_type = metadata["currency_type"]
                quantity = float(metadata["quantity"])
                
                await db.users.update_one(
                    {"id": payment["user_id"]},
                    {
                        "$inc": {
                            f"balances.{currency_type}": quantity,
                            "total_spent": payment["amount"],
                            "total_transactions": 1
                        }
                    }
                )
                
            elif metadata["package_type"] == "rank":
                rank_name = metadata["package_id"]
                await db.users.update_one(
                    {"id": payment["user_id"]},
                    {
                        "$addToSet": {"owned_ranks": rank_name},
                        "$inc": {"total_spent": payment["amount"], "total_transactions": 1}
                    }
                )
        
        return {
            "status": checkout_status.status,
            "payment_status": checkout_status.payment_status,
            "amount_total": checkout_status.amount_total,
            "currency": checkout_status.currency
        }
        
    except Exception as e:
        logging.error(f"Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Handle webhook event
        if webhook_response.payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {"$set": {
                    "payment_status": "paid",
                    "status": "complete",
                    "webhook_received_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return {"status": "success"}
        
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
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
