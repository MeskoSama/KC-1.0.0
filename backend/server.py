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

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'minecraft-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')

ADMIN_USERNAMES = ["TestMiner", "meskop"]

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

SERVER_CODES = {
    "10194": "NIM",
    "10997": "GRP",
    "20664": "VDD",
    "90154": "KKD"
}

RANK_PRICES = {
    "Germania Empire CITIZENSHIP": 3.00,
    "FIP": 1.00,
    "VIP": 3.00,
    "WIP": 7.50
}

BUILDING_TYPES = [
    "House", "Floor", "Complex", "Apartment", "Business",
    "Industrial", "Factory", "Park", "Agricultural Land", "Zoned Area"
]

BANKS = [
    "Bank of Cordoba (Lost Kingdom)",
    "Sakura Bank (Holy Empire)",
    "Bank of Germania (Federal Empire of Germania)",
    "VDD Ansbund Joint Banking"
]

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
    portfolio: Dict[str, float] = Field(default_factory=dict)
    total_spent: float = 0.0
    total_transactions: int = 0
    is_admin: bool = False
    selected_bank: Optional[str] = None
    hide_balance: bool = False
    can_use_real_money: bool = False
    created_at: str

class UserRegister(BaseModel):
    minecraft_username: str
    password: str
    server_code: str

class UserLogin(BaseModel):
    minecraft_username: str
    password: str
    server_code: str

class UserSettings(BaseModel):
    selected_bank: Optional[str] = None
    hide_balance: Optional[bool] = None

class MoneyTransfer(BaseModel):
    recipient_username: str
    amount: float
    currency: str

class InvestmentTransfer(BaseModel):
    recipient_username: str
    symbol: str
    quantity: float

class HouseSwapRequest(BaseModel):
    my_house_id: str
    their_house_id: str
    their_username: str

class StockPriceUpdate(BaseModel):
    symbol: str
    new_price: float

class ExchangeRateUpdate(BaseModel):
    rate_key: str
    new_rate: float

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

async def log_admin_action(admin_username: str, action: str, details: str):
    log_entry = {
        "id": str(uuid.uuid4()),
        "admin_username": admin_username,
        "action": action,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_logs.insert_one(log_entry)

async def get_exchange_rate(from_curr: str, to_curr: str) -> float:
    if from_curr == to_curr:
        return 1.0
    rates_doc = await db.exchange_rates.find_one({"id": "exchange_matrix"}, {"_id": 0})
    if not rates_doc:
        return 1.0
    rates = rates_doc.get("rates", {})
    rate_key = f"{from_curr}_TO_{to_curr}"
    return rates.get(rate_key, 1.0)

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
            "is_admin": is_admin,
            "hide_balance": user.hide_balance,
            "selected_bank": user.selected_bank,
            "portfolio": user.portfolio
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
            "is_admin": is_admin,
            "hide_balance": user.get("hide_balance", False),
            "selected_bank": user.get("selected_bank"),
            "portfolio": user.get("portfolio", {}),
            "can_use_real_money": user.get("can_use_real_money", False)
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
        "is_admin": current_user.get("is_admin", False),
        "hide_balance": current_user.get("hide_balance", False),
        "selected_bank": current_user.get("selected_bank"),
        "portfolio": current_user.get("portfolio", {}),
        "can_use_real_money": current_user.get("can_use_real_money", False)
    }

@api_router.put("/user/settings")
async def update_user_settings(settings: UserSettings, current_user: dict = Depends(get_current_user)):
    update_fields = {}
    if settings.selected_bank is not None:
        if settings.selected_bank not in BANKS and settings.selected_bank != "":
            raise HTTPException(status_code=400, detail="Invalid bank")
        update_fields["selected_bank"] = settings.selected_bank
    if settings.hide_balance is not None:
        update_fields["hide_balance"] = settings.hide_balance
    
    if update_fields:
        await db.users.update_one({"id": current_user["id"]}, {"$set": update_fields})
    
    return {"message": "Settings updated successfully"}

@api_router.get("/banks")
async def get_banks():
    return {"banks": BANKS}

@api_router.get("/building-types")
async def get_building_types():
    return {"types": BUILDING_TYPES}

# P2P Money Transfer
@api_router.post("/transfer/money")
async def transfer_money(transfer: MoneyTransfer, current_user: dict = Depends(get_current_user)):
    if transfer.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    # Find recipient
    recipient = await db.users.find_one({"minecraft_username": transfer.recipient_username}, {"_id": 0})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    if recipient["id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")
    
    # Check balance
    if current_user["balances"][transfer.currency] < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Get exchange rate for display
    sender_currency = current_user["currency_type"]
    rate = await get_exchange_rate(transfer.currency, sender_currency)
    
    # Transfer
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$inc": {f"balances.{transfer.currency}": -transfer.amount}}
    )
    
    await db.users.update_one(
        {"id": recipient["id"]},
        {"$inc": {f"balances.{transfer.currency}": transfer.amount}}
    )
    
    # Log transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "type": "money_transfer",
        "sender_id": current_user["id"],
        "sender_username": current_user["minecraft_username"],
        "recipient_id": recipient["id"],
        "recipient_username": recipient["minecraft_username"],
        "amount": transfer.amount,
        "currency": transfer.currency,
        "exchange_rate": rate,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.money_transfers.insert_one(transaction)
    
    return {
        "message": "Transfer successful",
        "sent": f"{transfer.amount} {transfer.currency}",
        "exchange_rate": f"1 {transfer.currency} = {rate:.5f} {sender_currency}"
    }

# Investment Transfer
@api_router.post("/transfer/investment")
async def transfer_investment(transfer: InvestmentTransfer, current_user: dict = Depends(get_current_user)):
    portfolio = current_user.get("portfolio", {})
    owned = portfolio.get(transfer.symbol, 0)
    
    if owned < transfer.quantity:
        raise HTTPException(status_code=400, detail="Insufficient shares")
    
    recipient = await db.users.find_one({"minecraft_username": transfer.recipient_username}, {"_id": 0})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    if recipient["id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")
    
    # Get investment
    investment = await db.investments.find_one({"symbol": transfer.symbol}, {"_id": 0})
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    # Calculate commission (0.01%)
    value = investment["current_price"] * transfer.quantity
    commission = value * 0.0001
    currency = investment["currency"]
    
    # Check balance for commission
    if current_user["balances"][currency] < commission:
        raise HTTPException(status_code=400, detail="Insufficient balance for commission")
    
    # Transfer
    await db.users.update_one(
        {"id": current_user["id"]},
        {
            "$inc": {
                f"portfolio.{transfer.symbol}": -transfer.quantity,
                f"balances.{currency}": -commission
            }
        }
    )
    
    await db.users.update_one(
        {"id": recipient["id"]},
        {"$inc": {f"portfolio.{transfer.symbol}": transfer.quantity}}
    )
    
    # Log
    transaction = {
        "id": str(uuid.uuid4()),
        "type": "investment_transfer",
        "sender_id": current_user["id"],
        "sender_username": current_user["minecraft_username"],
        "recipient_id": recipient["id"],
        "recipient_username": recipient["minecraft_username"],
        "symbol": transfer.symbol,
        "quantity": transfer.quantity,
        "value": value,
        "commission": commission,
        "currency": currency,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.investment_transactions.insert_one(transaction)
    
    return {"message": f"Transferred {transfer.quantity} shares of {transfer.symbol}", "commission": commission}

# Continue with remaining routes in next message due to length...
