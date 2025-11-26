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

# Admin users
ADMIN_USERNAMES = ["TestMiner", "meskop"]

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

# Currency exchange rates (base: GRP)
# 1 GRP = X other currency
DEFAULT_CURRENCY_RATES = {
    "GRP_TO_NIM": 1.68700,
    "GRP_TO_VDD": 2.36666,
    "GRP_TO_KKD": 2.61455,
    "GRP_TO_USD": 0.000245
}

# Rank prices
RANK_PRICES = {
    "Germania Empire CITIZENSHIP": 3.00,
    "FIP": 1.00,
    "VIP": 3.00,
    "WIP": 7.50
}

async def get_currency_rates():
    """Get currency rates from database or use defaults"""
    rates = await db.currency_rates.find_one({"id": "current_rates"}, {"_id": 0})
    if rates:
        return rates.get("rates", DEFAULT_CURRENCY_RATES)
    return DEFAULT_CURRENCY_RATES

async def update_currency_rates(new_rates: Dict[str, float]):
    """Update currency rates in database"""
    await db.currency_rates.update_one(
        {"id": "current_rates"},
        {"$set": {"rates": new_rates, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )

async def log_admin_action(admin_username: str, action: str, details: str):
    """Log admin actions"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "admin_username": admin_username,
        "action": action,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_logs.insert_one(log_entry)

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
    is_admin: bool = False
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
    status: str = "available"
    listed_at: str
    sold_at: Optional[str] = None
    admin_approved: bool = False
    title_deed_id: Optional[str] = None

class TitleDeed(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    house_id: str
    house_name: str
    owner_id: str
    owner_username: str
    previous_owner_id: Optional[str] = None
    previous_owner_username: Optional[str] = None
    purchase_price: float
    purchase_currency: str
    issued_date: str
    location: str

class CurrencyConversion(BaseModel):
    from_currency: str
    to_currency: str
    amount: float

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
    bounty_type: str
    title: str
    description: str
    reward_currency: str
    reward_amount: float
    target_player: Optional[str] = None
    creator_id: str
    creator_username: str
    status: str = "active"
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
    package_type: str
    package_id: str
    currency_type: Optional[str] = None
    quantity: Optional[float] = 1.0

class CurrencyRatesUpdate(BaseModel):
    GRP_TO_NIM: float
    GRP_TO_VDD: float
    GRP_TO_KKD: float
    GRP_TO_USD: float

class UserBalanceUpdate(BaseModel):
    user_id: str
    currency: str
    amount: float
    operation: str  # "add" or "set"

# Utility Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, username: str, is_admin: bool = False) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "is_admin": is_admin,
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

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = await get_current_user(credentials)
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# Auth Routes
@api_router.post("/auth/register")
async def register(data: UserRegister):
    if data.server_code not in SERVER_CODES:
        raise HTTPException(status_code=400, detail="Invalid server code")
    
    existing = await db.users.find_one({"minecraft_username": data.minecraft_username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    currency_type = SERVER_CODES[data.server_code]
    is_admin = data.minecraft_username in ADMIN_USERNAMES
    
    user = User(
        minecraft_username=data.minecraft_username,
        password_hash=hash_password(data.password),
        server_code=data.server_code,
        currency_type=currency_type,
        is_admin=is_admin,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    await db.users.insert_one(user.model_dump())
    token = create_jwt_token(user.id, user.minecraft_username, is_admin)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.minecraft_username,
            "currency_type": user.currency_type,
            "balances": user.balances,
            "is_admin": is_admin
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
    
    is_admin = user.get("is_admin", False) or data.minecraft_username in ADMIN_USERNAMES
    if is_admin and not user.get("is_admin", False):
        await db.users.update_one({"id": user["id"]}, {"$set": {"is_admin": True}})
    
    token = create_jwt_token(user["id"], user["minecraft_username"], is_admin)
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["minecraft_username"],
            "currency_type": user["currency_type"],
            "balances": user["balances"],
            "owned_ranks": user.get("owned_ranks", []),
            "owned_houses": user.get("owned_houses", []),
            "is_admin": is_admin
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
        "total_transactions": current_user.get("total_transactions", 0),
        "is_admin": current_user.get("is_admin", False)
    }

# Admin Routes
@api_router.get("/admin/stats")
async def get_admin_stats(current_user: dict = Depends(get_admin_user)):
    total_users = await db.users.count_documents({})
    total_transactions = await db.payment_transactions.count_documents({})
    total_bounties = await db.bounties.count_documents({})
    total_houses = await db.houses.count_documents({})
    pending_houses = await db.houses.count_documents({"admin_approved": False})
    
    # Total revenue
    payments = await db.payment_transactions.find({"payment_status": "paid"}, {"_id": 0, "amount": 1}).to_list(10000)
    total_revenue = sum(p.get("amount", 0) for p in payments)
    
    return {
        "total_users": total_users,
        "total_transactions": total_transactions,
        "total_bounties": total_bounties,
        "total_houses": total_houses,
        "pending_houses": pending_houses,
        "total_revenue": total_revenue
    }

@api_router.get("/admin/users")
async def get_all_users(current_user: dict = Depends(get_admin_user), skip: int = 0, limit: int = 50):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).skip(skip).limit(limit).to_list(limit)
    return {"users": users}

@api_router.put("/admin/user/balance")
async def update_user_balance(update: UserBalanceUpdate, current_user: dict = Depends(get_admin_user)):
    user = await db.users.find_one({"id": update.user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if update.currency not in ["NIM", "GRP", "VDD", "KKD"]:
        raise HTTPException(status_code=400, detail="Invalid currency")
    
    if update.operation == "add":
        await db.users.update_one(
            {"id": update.user_id},
            {"$inc": {f"balances.{update.currency}": update.amount}}
        )
    elif update.operation == "set":
        await db.users.update_one(
            {"id": update.user_id},
            {"$set": {f"balances.{update.currency}": update.amount}}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid operation")
    
    await log_admin_action(
        current_user["minecraft_username"],
        "UPDATE_USER_BALANCE",
        f"User: {user['minecraft_username']}, Currency: {update.currency}, Operation: {update.operation}, Amount: {update.amount}"
    )
    
    return {"message": "Balance updated successfully"}

@api_router.get("/admin/currency-rates")
async def get_admin_currency_rates(current_user: dict = Depends(get_admin_user)):
    rates = await get_currency_rates()
    return {"rates": rates}

@api_router.put("/admin/currency-rates")
async def update_admin_currency_rates(rates: CurrencyRatesUpdate, current_user: dict = Depends(get_admin_user)):
    new_rates = rates.model_dump()
    await update_currency_rates(new_rates)
    
    await log_admin_action(
        current_user["minecraft_username"],
        "UPDATE_CURRENCY_RATES",
        f"New rates: {new_rates}"
    )
    
    return {"message": "Currency rates updated successfully", "rates": new_rates}

@api_router.get("/admin/logs")
async def get_admin_logs(current_user: dict = Depends(get_admin_user), skip: int = 0, limit: int = 100):
    logs = await db.admin_logs.find({}, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    return {"logs": logs}

@api_router.get("/admin/transactions")
async def get_all_transactions(current_user: dict = Depends(get_admin_user), skip: int = 0, limit: int = 50):
    transactions = await db.payment_transactions.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"transactions": transactions}

# Currency Purchase Routes
@api_router.get("/marketplace/currency-rates")
async def get_marketplace_currency_rates():
    rates = await get_currency_rates()
    return {"rates": rates}

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
async def get_pending_houses(current_user: dict = Depends(get_admin_user)):
    houses = await db.houses.find({"admin_approved": False}, {"_id": 0}).to_list(1000)
    return {"houses": houses}

@api_router.post("/houses/{house_id}/approve")
async def approve_house(house_id: str, current_user: dict = Depends(get_admin_user)):
    result = await db.houses.update_one(
        {"id": house_id},
        {"$set": {"admin_approved": True, "status": "available"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="House not found")
    
    await log_admin_action(
        current_user["minecraft_username"],
        "APPROVE_HOUSE",
        f"House ID: {house_id}"
    )
    
    return {"message": "House approved"}

@api_router.delete("/houses/{house_id}")
async def delete_house(house_id: str, current_user: dict = Depends(get_admin_user)):
    result = await db.houses.delete_one({"id": house_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="House not found")
    
    await log_admin_action(
        current_user["minecraft_username"],
        "DELETE_HOUSE",
        f"House ID: {house_id}"
    )
    
    return {"message": "House deleted"}

@api_router.post("/houses/{house_id}/buy")
async def buy_house(house_id: str, payment_type: str, payment_currency: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    house = await db.houses.find_one({"id": house_id}, {"_id": 0})
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    if house["status"] != "available":
        raise HTTPException(status_code=400, detail="House not available")
    
    if payment_type == "currency":
        if not house.get("price_currency"):
            raise HTTPException(status_code=400, detail="Currency payment not available")
        
        # Allow payment with any currency
        if not payment_currency or payment_currency not in ["NIM", "GRP", "VDD", "KKD"]:
            payment_currency = current_user["currency_type"]
        
        required_amount = house["price_currency"].get(payment_currency, 0)
        
        if current_user["balances"][payment_currency] < required_amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Create title deed
        title_deed = TitleDeed(
            house_id=house_id,
            house_name=house["name"],
            owner_id=current_user["id"],
            owner_username=current_user["minecraft_username"],
            previous_owner_id=house.get("owner_id"),
            previous_owner_username=house.get("owner_username"),
            purchase_price=required_amount,
            purchase_currency=payment_currency,
            issued_date=datetime.now(timezone.utc).isoformat(),
            location=house["location"]
        )
        
        await db.title_deeds.insert_one(title_deed.model_dump())
        
        await db.users.update_one(
            {"id": current_user["id"]},
            {
                "$inc": {f"balances.{payment_currency}": -required_amount, "total_transactions": 1},
                "$push": {"owned_houses": house_id}
            }
        )
        
        await db.houses.update_one(
            {"id": house_id},
            {
                "$set": {
                    "status": "sold",
                    "sold_at": datetime.now(timezone.utc).isoformat(),
                    "owner_id": current_user["id"],
                    "owner_username": current_user["minecraft_username"],
                    "title_deed_id": title_deed.id
                }
            }
        )
        
        return {
            "message": "House purchased successfully! Title deed issued.",
            "title_deed_id": title_deed.id
        }
    
    return {"message": "USD payment requires Stripe checkout", "amount": house.get("price_usd", 0)}

# Bounty Routes  
@api_router.post("/bounties")
async def create_bounty(bounty_data: BountyCreate, current_user: dict = Depends(get_current_user)):
    if current_user["balances"][bounty_data.reward_currency] < bounty_data.reward_amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
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

@api_router.delete("/bounties/{bounty_id}")
async def delete_bounty(bounty_id: str, current_user: dict = Depends(get_admin_user)):
    result = await db.bounties.delete_one({"id": bounty_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bounty not found")
    
    await log_admin_action(
        current_user["minecraft_username"],
        "DELETE_BOUNTY",
        f"Bounty ID: {bounty_id}"
    )
    
    return {"message": "Bounty deleted"}

# Currency Conversion Routes
@api_router.post("/currency/convert")
async def convert_currency(conversion: CurrencyConversion, current_user: dict = Depends(get_current_user)):
    if conversion.from_currency not in ["NIM", "GRP", "VDD", "KKD"]:
        raise HTTPException(status_code=400, detail="Invalid source currency")
    if conversion.to_currency not in ["NIM", "GRP", "VDD", "KKD"]:
        raise HTTPException(status_code=400, detail="Invalid target currency")
    if conversion.from_currency == conversion.to_currency:
        raise HTTPException(status_code=400, detail="Cannot convert to same currency")
    if conversion.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Check balance
    if current_user["balances"][conversion.from_currency] < conversion.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Get exchange rates
    rates = await get_currency_rates()
    
    # Convert to GRP first, then to target currency
    grp_amount = conversion.amount
    if conversion.from_currency != "GRP":
        rate_key = f"GRP_TO_{conversion.from_currency}"
        grp_amount = conversion.amount / rates[rate_key]
    
    # Convert from GRP to target
    target_amount = grp_amount
    if conversion.to_currency != "GRP":
        rate_key = f"GRP_TO_{conversion.to_currency}"
        target_amount = grp_amount * rates[rate_key]
    
    # Update balances
    await db.users.update_one(
        {"id": current_user["id"]},
        {
            "$inc": {
                f"balances.{conversion.from_currency}": -conversion.amount,
                f"balances.{conversion.to_currency}": target_amount,
                "total_transactions": 1
            }
        }
    )
    
    return {
        "message": "Currency converted successfully",
        "from_amount": conversion.amount,
        "from_currency": conversion.from_currency,
        "to_amount": target_amount,
        "to_currency": conversion.to_currency,
        "exchange_rate": target_amount / conversion.amount
    }

@api_router.get("/title-deeds")
async def get_my_title_deeds(current_user: dict = Depends(get_current_user)):
    deeds = await db.title_deeds.find({"owner_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    return {"title_deeds": deeds}

@api_router.get("/title-deeds/{deed_id}")
async def get_title_deed(deed_id: str, current_user: dict = Depends(get_current_user)):
    deed = await db.title_deeds.find_one({"id": deed_id}, {"_id": 0})
    if not deed:
        raise HTTPException(status_code=404, detail="Title deed not found")
    if deed["owner_id"] != current_user["id"] and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized to view this title deed")
    return deed

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
        
        origin = request.headers.get("origin", host_url)
        success_url = f"{origin}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin}/marketplace"
        
        rates = await get_currency_rates()
        amount = 0.0
        metadata = {
            "user_id": current_user["id"],
            "username": current_user["minecraft_username"],
            "package_type": checkout_req.package_type,
            "package_id": checkout_req.package_id
        }
        
        if checkout_req.package_type == "currency":
            # Allow buying any currency, not just user's server currency
            if checkout_req.currency_type not in ["NIM", "GRP", "VDD", "KKD"]:
                raise HTTPException(status_code=400, detail="Invalid currency type")
            
            grp_amount = checkout_req.quantity
            if checkout_req.currency_type != "GRP":
                rate_key = f"GRP_TO_{checkout_req.currency_type}"
                grp_amount = checkout_req.quantity / rates[rate_key]
            
            amount = grp_amount * rates["GRP_TO_USD"]
            metadata["currency_type"] = checkout_req.currency_type
            metadata["quantity"] = str(checkout_req.quantity)
            metadata["user_server_currency"] = current_user["currency_type"]
            
        elif checkout_req.package_type == "rank":
            if checkout_req.package_id not in RANK_PRICES:
                raise HTTPException(status_code=400, detail="Invalid rank")
            amount = RANK_PRICES[checkout_req.package_id]
        
        checkout_request = CheckoutSessionRequest(
            amount=amount,
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            payment_methods=['card']
        )
        
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
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
        payment = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if payment["payment_status"] == "paid":
            return {
                "status": payment["status"],
                "payment_status": payment["payment_status"],
                "message": "Payment already processed"
            }
        
        host_url = "https://pixeltraders.preview.emergentagent.com"
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        checkout_status = await stripe_checkout.get_checkout_status(session_id)
        
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": checkout_status.status,
                "payment_status": checkout_status.payment_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
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

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
