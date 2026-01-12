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
    "90154": "KKD",
    "10101": "EP",
    "90234": "EGD"
}

# All available currencies in the system
ALL_CURRENCIES = ["NIM", "GRP", "VDD", "KKD", "EP", "EGD"]

# Currency display names
CURRENCY_NAMES = {
    "NIM": "NIM",
    "GRP": "GRP", 
    "VDD": "VDD",
    "KKD": "KKD",
    "EP": "EP",  # Evrensel Para (Universal Money)
    "EGD": "EGD"  # Egoslavya Dinar
}

# Currency exchange rates (base: GRP) - UPDATED RATES
# 1 GRP = X other currency
DEFAULT_CURRENCY_RATES = {
    "GRP_TO_NIM": 1.6060,
    "GRP_TO_VDD": 2.3861,
    "GRP_TO_KKD": 2.2836,
    "GRP_TO_EP": 112.5055,
    "GRP_TO_EGD": 118.1307,
    "GRP_TO_USD": 0.000245
}

# Full exchange rate matrix - all currency pairs (UPDATED)
# These rates are: 1 FROM_CURRENCY = X TO_CURRENCY
DEFAULT_EXCHANGE_MATRIX = {
    # GRP conversions
    "GRP_TO_GRP": 1.0,
    "GRP_TO_NIM": 1.6060,
    "GRP_TO_VDD": 2.3861,
    "GRP_TO_KKD": 2.2836,
    "GRP_TO_EP": 112.5055,
    "GRP_TO_EGD": 118.1307,
    # NIM conversions (1 NIM = X)
    "NIM_TO_GRP": 0.62267,  # 1/1.6060
    "NIM_TO_NIM": 1.0,
    "NIM_TO_VDD": 1.48576,  # 2.3861/1.6060
    "NIM_TO_KKD": 1.42191,  # 2.2836/1.6060
    "NIM_TO_EP": 70.0532,   # 112.5055/1.6060
    "NIM_TO_EGD": 73.5560,  # 118.1307/1.6060
    # VDD conversions (1 VDD = X)
    "VDD_TO_GRP": 0.41909,  # 1/2.3861
    "VDD_TO_NIM": 0.67306,  # 1.6060/2.3861
    "VDD_TO_VDD": 1.0,
    "VDD_TO_KKD": 0.95704,  # 2.2836/2.3861
    "VDD_TO_EP": 47.1469,   # 112.5055/2.3861
    "VDD_TO_EGD": 49.5064,  # 118.1307/2.3861
    # KKD conversions (1 KKD = X)
    "KKD_TO_GRP": 0.43791,  # 1/2.2836
    "KKD_TO_NIM": 0.70335,  # 1.6060/2.2836
    "KKD_TO_VDD": 1.04488,  # 2.3861/2.2836
    "KKD_TO_KKD": 1.0,
    "KKD_TO_EP": 49.2658,   # 112.5055/2.2836
    "KKD_TO_EGD": 51.7295,  # 118.1307/2.2836
    # EP conversions (1 EP = X)
    "EP_TO_GRP": 0.00889,   # 1/112.5055
    "EP_TO_NIM": 0.01428,   # 1.6060/112.5055
    "EP_TO_VDD": 0.02121,   # 2.3861/112.5055
    "EP_TO_KKD": 0.02030,   # 2.2836/112.5055
    "EP_TO_EP": 1.0,
    "EP_TO_EGD": 1.05000,   # 118.1307/112.5055
    # EGD conversions (1 EGD = X)
    "EGD_TO_GRP": 0.00847,  # 1/118.1307
    "EGD_TO_NIM": 0.01360,  # 1.6060/118.1307
    "EGD_TO_VDD": 0.02020,  # 2.3861/118.1307
    "EGD_TO_KKD": 0.01933,  # 2.2836/118.1307
    "EGD_TO_EP": 0.95238,   # 1/1.05
    "EGD_TO_EGD": 1.0
}

# Independence status types
INDEPENDENCE_STATUSES = [
    "non-independent settlement",
    "independent settlement",
    "independent area",
    "independent region",
    "independent country"
]

# Default country data
DEFAULT_COUNTRIES = [
    {
        "id": "germania",
        "name": "Germania Empire",
        "currency": "GRP",
        "independence_status": "independent country",
        "treasury": 101270250000,
        "color": "#9333ea",  # Purple
        "income": [
            {"name": "Factory Income", "amount": 37550000},
            {"name": "Industrial Income", "amount": 7500000},
            {"name": "Tax Income", "amount": 5500000},
            {"name": "Customs Income", "amount": 1250000},
            {"name": "Trade Income", "amount": 10750000},
            {"name": "Business Income", "amount": 2245000},
            {"name": "Guild Income", "amount": 680000},
            {"name": "Infrastructure Income", "amount": 6650000}
        ],
        "expenses": [
            {"name": "Consumption Expenses", "amount": 1125000},
            {"name": "Infrastructure Maintenance", "amount": 3500000},
            {"name": "Salaries and Energy Expenses", "amount": 2200000},
            {"name": "Ministries and Council Expenses", "amount": 5000000},
            {"name": "Government Expenses", "amount": 12000000},
            {"name": "Artificial Intelligence Usage", "amount": 8000000}
        ],
        "economic_share": {
            "bank_flow": 18.37,
            "trade": 39.55,
            "global_reserves": 73.72
        }
    },
    {
        "id": "holy_empire",
        "name": "Holy Empire",
        "currency": "NIM",
        "independence_status": "independent country",
        "treasury": 46042452298,
        "color": "#ef4444",  # Red
        "income": [
            {"name": "Factory Income", "amount": 16630000},
            {"name": "Industrial Income", "amount": 6600000},
            {"name": "Tax Income", "amount": 6500000},
            {"name": "Customs Income", "amount": 1350000},
            {"name": "Trade Income", "amount": 10575000},
            {"name": "Business Income", "amount": 2950000},
            {"name": "Guild Income", "amount": 800000},
            {"name": "Infrastructure Income", "amount": 11000000}
        ],
        "expenses": [
            {"name": "Consumption Expenses", "amount": 1000000},
            {"name": "Infrastructure Maintenance", "amount": 4000000},
            {"name": "Salaries and Energy Expenses", "amount": 1850000},
            {"name": "Ministries and Council Expenses", "amount": 4000000},
            {"name": "Government Expenses", "amount": 6000000},
            {"name": "Artificial Intelligence Usage", "amount": 4000000}
        ],
        "economic_share": {
            "bank_flow": 53.03,
            "trade": 21.95,
            "global_reserves": 19.86
        }
    },
    {
        "id": "lost_kingdom",
        "name": "Lost Kingdom",
        "currency": "KKD",
        "independence_status": "independent country",
        "treasury": 20433225616,
        "color": "#f59e0b",  # Amber
        "income": [
            {"name": "Factory Income", "amount": 25370000},
            {"name": "Industrial Income", "amount": 0},
            {"name": "Tax Income", "amount": 3000000},
            {"name": "Customs Income", "amount": 3150000},
            {"name": "Trade Income", "amount": 19500000},
            {"name": "Business Income", "amount": 2500000},
            {"name": "Guild Income", "amount": 750000},
            {"name": "Infrastructure Income", "amount": 7000000}
        ],
        "expenses": [
            {"name": "Consumption Expenses", "amount": 4500000},
            {"name": "Infrastructure Maintenance", "amount": 5500000},
            {"name": "Salaries and Energy Expenses", "amount": 5000000},
            {"name": "Ministries and Council Expenses", "amount": 5000000},
            {"name": "Government Expenses", "amount": 12000000},
            {"name": "Artificial Intelligence Usage", "amount": 8000000}
        ],
        "economic_share": {
            "bank_flow": 28.60,
            "trade": 37.60,
            "global_reserves": 5.69
        }
    },
    {
        "id": "veltronia",
        "name": "Veltronia Dominarex",
        "currency": "VDD",
        "independence_status": "independent country",
        "treasury": 2358949410,
        "color": "#22c55e",  # Green
        "income": [
            {"name": "Factory Income", "amount": 0},
            {"name": "Industrial Income", "amount": 880000},
            {"name": "Tax Income", "amount": 500000},
            {"name": "Customs Income", "amount": 150000},
            {"name": "Trade Income", "amount": 7100000},
            {"name": "Business Income", "amount": 0},
            {"name": "Guild Income", "amount": 0},
            {"name": "Infrastructure Income", "amount": 350000}
        ],
        "expenses": [
            {"name": "Consumption Expenses", "amount": 1000000},
            {"name": "Infrastructure Maintenance", "amount": 500000},
            {"name": "Salaries and Energy Expenses", "amount": 1200000},
            {"name": "Ministries and Council Expenses", "amount": 1000000},
            {"name": "Government Expenses", "amount": 4000000},
            {"name": "Artificial Intelligence Usage", "amount": 0}
        ],
        "economic_share": {
            "bank_flow": 0,
            "trade": 0.90,
            "global_reserves": 0.73
        }
    },
    {
        "id": "egoslavia",
        "name": "Egoslavia",
        "currency": "EGD",
        "independence_status": "non-independent settlement",
        "treasury": 200000000,
        "color": "#3b82f6",  # Blue
        "income": [
            {"name": "Factory Income", "amount": 0},
            {"name": "Industrial Income", "amount": 0},
            {"name": "Tax Income", "amount": 0},
            {"name": "Customs Income", "amount": 0},
            {"name": "Trade Income", "amount": 0},
            {"name": "Business Income", "amount": 0},
            {"name": "Guild Income", "amount": 0},
            {"name": "Infrastructure Income", "amount": 0}
        ],
        "expenses": [
            {"name": "Consumption Expenses", "amount": 0},
            {"name": "Infrastructure Maintenance", "amount": 0},
            {"name": "Salaries and Energy Expenses", "amount": 0},
            {"name": "Ministries and Council Expenses", "amount": 0},
            {"name": "Government Expenses", "amount": 0},
            {"name": "Artificial Intelligence Usage", "amount": 0}
        ],
        "economic_share": {
            "bank_flow": 0,
            "trade": 0,
            "global_reserves": 0
        }
    }
]

# New stocks to add
NEW_STOCKS = [
    # NIM stocks
    {"symbol": "NIM-IMPERIAL-IND", "name": "Imperial Industry Office", "currency": "NIM", "current_price": 10.00},
    {"symbol": "NIM-IMPERIAL-TRADE", "name": "Imperial Trade Office", "currency": "NIM", "current_price": 2.55},
    # VDD stocks
    {"symbol": "VDD-JOINT-BANK", "name": "Veltronia Joint Banking", "currency": "VDD", "current_price": 3.33},
    {"symbol": "VDD-TRADE-OFFICE", "name": "Veltronia Trade Office", "currency": "VDD", "current_price": 1.20},
    # KKD stocks
    {"symbol": "KKD-IND-OFFICE", "name": "Lost Kingdom Industry Office", "currency": "KKD", "current_price": 23.50},
    {"symbol": "KKD-TRADE-OFFICE", "name": "Lost Kingdom Trade Office", "currency": "KKD", "current_price": 4.52},
    # EGD stocks
    {"symbol": "EGD-GOV", "name": "Egoslavia Government", "currency": "EGD", "current_price": 100.00},
    {"symbol": "EGD-MINISTRY", "name": "Egoslavia Ministry Office", "currency": "EGD", "current_price": 3.50},
    {"symbol": "EGD-SUMERBANK", "name": "SümerBank", "currency": "EGD", "current_price": 5.00},
    {"symbol": "EGD-MXBUILD", "name": "MX Build", "currency": "EGD", "current_price": 5.00},
    {"symbol": "EGD-EGBUILD", "name": "EG Build", "currency": "EGD", "current_price": 1.00},
    {"symbol": "EGD-HAZINE", "name": "Egoslavia Treasury Bond", "currency": "EGD", "current_price": 0.10}
]

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

async def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """
    Get direct exchange rate from one currency to another using the exchange matrix
    Returns the multiplier to convert from_currency to to_currency
    """
    if from_currency == to_currency:
        return 1.0
    
    # Get exchange rate matrix
    rates_doc = await db.exchange_rates.find_one({"id": "exchange_matrix"}, {"_id": 0})
    if not rates_doc:
        # Fallback to default matrix
        rate_key = f"{from_currency}_TO_{to_currency}"
        return DEFAULT_EXCHANGE_MATRIX.get(rate_key, 1.0)
    
    # Use direct conversion from matrix
    rate_key = f"{from_currency}_TO_{to_currency}"
    exchange_rates = rates_doc.get("rates", {})
    
    return exchange_rates.get(rate_key, DEFAULT_EXCHANGE_MATRIX.get(rate_key, 1.0))

async def get_available_currencies():
    """Get list of all available currencies from database"""
    currencies_doc = await db.currencies.find_one({"id": "currency_list"}, {"_id": 0})
    if currencies_doc:
        return currencies_doc.get("currencies", ALL_CURRENCIES)
    return ALL_CURRENCIES

async def get_currency_info():
    """Get all currency information including names"""
    currencies_doc = await db.currencies.find_one({"id": "currency_list"}, {"_id": 0})
    if currencies_doc:
        return {
            "currencies": currencies_doc.get("currencies", ALL_CURRENCIES),
            "names": currencies_doc.get("names", CURRENCY_NAMES)
        }
    return {
        "currencies": ALL_CURRENCIES,
        "names": CURRENCY_NAMES
    }

async def initialize_exchange_matrix():
    """Initialize exchange rate matrix in database if not exists"""
    existing = await db.exchange_rates.find_one({"id": "exchange_matrix"})
    if not existing:
        await db.exchange_rates.insert_one({
            "id": "exchange_matrix",
            "rates": DEFAULT_EXCHANGE_MATRIX,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
async def initialize_currencies():
    """Initialize currencies in database if not exists"""
    existing = await db.currencies.find_one({"id": "currency_list"})
    if not existing:
        await db.currencies.insert_one({
            "id": "currency_list",
            "currencies": ALL_CURRENCIES,
            "names": CURRENCY_NAMES,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

async def initialize_countries():
    """Initialize countries in database if not exists"""
    for country_data in DEFAULT_COUNTRIES:
        existing = await db.countries.find_one({"id": country_data["id"]})
        if not existing:
            country_data["created_at"] = datetime.now(timezone.utc).isoformat()
            country_data["last_treasury_update"] = datetime.now(timezone.utc).isoformat()
            await db.countries.insert_one(country_data)

async def initialize_new_stocks():
    """Initialize new stocks in database if not exists"""
    for stock_data in NEW_STOCKS:
        existing = await db.investments.find_one({"symbol": stock_data["symbol"]})
        if not existing:
            stock_data["id"] = str(uuid.uuid4())
            stock_data["created_at"] = datetime.now(timezone.utc).isoformat()
            stock_data["price_history"] = [{"timestamp": datetime.now(timezone.utc).isoformat(), "price": stock_data["current_price"]}]
            stock_data["disabled"] = False
            await db.investments.insert_one(stock_data)

async def update_weekly_treasury():
    """Update all country treasuries based on weekly net income"""
    countries = await db.countries.find({}).to_list(100)
    
    for country in countries:
        total_income = sum(item.get("amount", 0) for item in country.get("income", []))
        total_expenses = sum(item.get("amount", 0) for item in country.get("expenses", []))
        weekly_net = total_income - total_expenses
        
        new_treasury = country.get("treasury", 0) + weekly_net
        
        await db.countries.update_one(
            {"id": country["id"]},
            {
                "$set": {
                    "treasury": new_treasury,
                    "last_treasury_update": datetime.now(timezone.utc).isoformat()
                },
                "$push": {
                    "treasury_history": {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "previous": country.get("treasury", 0),
                        "change": weekly_net,
                        "new_balance": new_treasury
                    }
                }
            }
        )
    
    return {"message": f"Updated treasury for {len(countries)} countries"}


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
    balances: Dict[str, float] = Field(default_factory=lambda: {"NIM": 0, "GRP": 0, "VDD": 0, "KKD": 0, "EP": 0, "EGD": 0})
    owned_ranks: List[str] = Field(default_factory=list)
    owned_houses: List[str] = Field(default_factory=list)
    total_spent: float = 0.0
    total_transactions: int = 0
    is_admin: bool = False  # DEPRECATED: Use 'role' field instead
    role: str = "user"  # user, admin, superadmin
    banned: bool = False
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

# Admin operation models
class UserRoleUpdate(BaseModel):
    user_id: str
    new_role: str  # user, admin, superadmin

class UserBanUpdate(BaseModel):
    user_id: str
    banned: bool

class UserCurrencyUpdate(BaseModel):
    user_id: str
    new_currency_type: str


# Admin investment management models
class StockCreate(BaseModel):
    symbol: str
    name: str
    currency: str
    current_price: float

class StockNameUpdate(BaseModel):
    symbol: str
    new_name: str

class StockPriceUpdate(BaseModel):
    symbol: str
    new_price: float

class StockCurrencyUpdate(BaseModel):
    symbol: str
    new_currency: str

class StockStatusUpdate(BaseModel):
    symbol: str
    disabled: bool

# Investment order model for buy/sell
class InvestmentOrder(BaseModel):
    symbol: str
    quantity: float

# Currency management models
class CurrencyCreate(BaseModel):
    code: str  # e.g., "EP", "EGD"
    name: str  # e.g., "Evrensel Para", "Egoslavya Dinar"
    base_rate_to_grp: float  # How many of this currency = 1 GRP

class CurrencyUpdate(BaseModel):
    code: str
    name: Optional[str] = None
    base_rate_to_grp: Optional[float] = None

class ExchangeRateUpdate(BaseModel):
    from_currency: str
    to_currency: str
    rate: float

# Utility Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, username: str, role: str = "user") -> str:
    """Create JWT token with user role"""
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user (any role)"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Check if user is banned
        if user.get("banned", False):
            raise HTTPException(status_code=403, detail="Account banned")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# New role-based dependencies
async def require_user(user: dict = Depends(get_current_user)):
    """Require authenticated user (any role)"""
    return user

async def require_admin(user: dict = Depends(get_current_user)):
    """Require admin or superadmin role"""
    role = user.get("role", "user")
    if role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_superadmin(user: dict = Depends(get_current_user)):
    """Require superadmin role only"""
    role = user.get("role", "user")
    if role != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return user

# DEPRECATED: Keep for backward compatibility during transition
async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """DEPRECATED: Use require_admin instead"""
    return await require_admin(await get_current_user(credentials))

# Auth Routes
@api_router.post("/auth/register")
async def register(data: UserRegister):
    if data.server_code not in SERVER_CODES:
        raise HTTPException(status_code=400, detail="Invalid server code")
    
    existing = await db.users.find_one({"minecraft_username": data.minecraft_username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    currency_type = SERVER_CODES[data.server_code]
    
    user = User(
        minecraft_username=data.minecraft_username,
        password_hash=hash_password(data.password),
        server_code=data.server_code,
        currency_type=currency_type,
        role="user",  # All new users start as regular users
        banned=False,
        is_admin=False,  # Keep for backward compatibility
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    await db.users.insert_one(user.model_dump())
    token = create_jwt_token(user.id, user.minecraft_username, user.role)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.minecraft_username,
            "currency_type": user.currency_type,
            "balances": user.balances,
            "role": user.role,
            "is_admin": False  # For backward compatibility
        }
    }

@api_router.post("/auth/login")
async def login(data: UserLogin):
    user = await db.users.find_one({"minecraft_username": data.minecraft_username}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if user is banned
    if user.get("banned", False):
        raise HTTPException(status_code=403, detail="Account has been banned")
    
    if user["server_code"] != data.server_code:
        raise HTTPException(status_code=401, detail="Invalid server code")
    
    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    role = user.get("role", "user")
    token = create_jwt_token(user["id"], user["minecraft_username"], role)
    
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
            "role": role,
            "is_admin": role in ["admin", "superadmin"]  # For backward compatibility
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["minecraft_username"],
        "currency_type": current_user["currency_type"],
        "balances": current_user["balances"],
        "portfolio": current_user.get("portfolio", {}),
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
    
    # Get available currencies dynamically
    available = await get_available_currencies()
    if update.currency not in available:
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
    # Get all available currencies from database or use defaults
    available_currencies = await get_available_currencies()
    
    if conversion.from_currency not in available_currencies:
        raise HTTPException(status_code=400, detail="Invalid source currency")
    if conversion.to_currency not in available_currencies:
        raise HTTPException(status_code=400, detail="Invalid target currency")
    if conversion.from_currency == conversion.to_currency:
        raise HTTPException(status_code=400, detail="Cannot convert to same currency")
    if conversion.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Check balance
    user_balance = current_user.get("balances", {}).get(conversion.from_currency, 0)
    if user_balance < conversion.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Get exchange rate directly from matrix
    rate = await get_exchange_rate(conversion.from_currency, conversion.to_currency)
    target_amount = conversion.amount * rate
    
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
        "exchange_rate": rate
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
        
        host_url = "https://code-fixer-104.preview.emergentagent.com"
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

# Investment Routes
@api_router.get("/investments")
async def get_investments(current_user: dict = Depends(get_current_user)):
    # Exclude disabled stocks for regular users
    query = {"disabled": {"$ne": True}}
    investments = await db.investments.find(query, {"_id": 0}).to_list(1000)
    return {"investments": investments}

@api_router.get("/exchange-rates")
async def get_exchange_rates_matrix():
    rates_doc = await db.exchange_rates.find_one({"id": "exchange_matrix"}, {"_id": 0})
    if rates_doc:
        return {"rates": rates_doc.get("rates", {})}
    return {"rates": {}}

@api_router.post("/investments/buy")
async def buy_investment(order: InvestmentOrder, current_user: dict = Depends(get_current_user)):
    symbol = order.symbol
    quantity = order.quantity
    
    # Validate quantity
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    
    # Get investment
    investment = await db.investments.find_one({"symbol": symbol}, {"_id": 0})
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    # Check if stock is disabled
    if investment.get("disabled", False):
        raise HTTPException(status_code=403, detail="This stock is currently disabled")
    
    currency = investment["currency"]
    price = investment["current_price"]
    total = price * quantity
    commission = total * 0.00001  # 0.001%
    final_amount = total + commission
    
    # Check balance - ensure currency exists in user balances
    user_balance = current_user.get("balances", {}).get(currency, 0)
    if user_balance < final_amount:
        raise HTTPException(status_code=400, detail=f"Insufficient {currency} balance. Need {final_amount:.2f}, have {user_balance:.2f}")
    
    # Update user balance and portfolio
    await db.users.update_one(
        {"id": current_user["id"]},
        {
            "$inc": {
                f"balances.{currency}": -final_amount,
                f"portfolio.{symbol}": quantity,
                "total_transactions": 1
            }
        }
    )
    
    # Record transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "username": current_user["minecraft_username"],
        "symbol": symbol,
        "transaction_type": "buy",
        "quantity": quantity,
        "price_per_unit": price,
        "total_amount": total,
        "commission": commission,
        "currency": currency,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.investment_transactions.insert_one(transaction.copy())
    
    return {"message": "Purchase successful", "transaction": transaction}

@api_router.post("/investments/sell")
async def sell_investment(order: InvestmentOrder, current_user: dict = Depends(get_current_user)):
    symbol = order.symbol
    quantity = order.quantity
    
    # Validate quantity
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    
    # Check if user owns this stock
    portfolio = current_user.get("portfolio", {})
    owned = portfolio.get(symbol, 0)
    
    if owned < quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient shares. Own {owned}, trying to sell {quantity}")
    
    # Get investment
    investment = await db.investments.find_one({"symbol": symbol}, {"_id": 0})
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    currency = investment["currency"]
    price = investment["current_price"]
    total = price * quantity
    commission = total * 0.00001  # 0.001%
    final_amount = total - commission
    
    # Update user balance and portfolio
    await db.users.update_one(
        {"id": current_user["id"]},
        {
            "$inc": {
                f"balances.{currency}": final_amount,
                f"portfolio.{symbol}": -quantity,
                "total_transactions": 1
            }
        }
    )
    
    # Record transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "username": current_user["minecraft_username"],
        "symbol": symbol,
        "transaction_type": "sell",
        "quantity": quantity,
        "price_per_unit": price,
        "total_amount": total,
        "commission": commission,
        "currency": currency,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.investment_transactions.insert_one(transaction.copy())
    
    return {"message": "Sale successful", "transaction": transaction}

# Admin Investment Management
@api_router.put("/admin/investment/price")
async def admin_update_stock_price(update: dict, current_user: dict = Depends(get_admin_user)):
    symbol = update.get("symbol")
    new_price = update.get("new_price")
    
    if not symbol or new_price is None or new_price < 0:
        raise HTTPException(status_code=400, detail="Invalid data")
    
    investment = await db.investments.find_one({"symbol": symbol}, {"_id": 0})
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    old_price = investment["current_price"]
    
    # Update price and add to history
    await db.investments.update_one(
        {"symbol": symbol},
        {
            "$set": {
                "current_price": new_price,
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "$push": {
                "price_history": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "price": new_price,
                    "old_price": old_price
                }
            }
        }
    )
    
    await log_admin_action(
        current_user["minecraft_username"],
        "UPDATE_STOCK_PRICE",
        f"Symbol: {symbol}, Old: {old_price}, New: {new_price}"
    )
    
    return {"message": "Stock price updated", "symbol": symbol, "new_price": new_price}

@api_router.put("/admin/exchange-rate")
async def admin_update_exchange_rate(update: dict, current_user: dict = Depends(get_admin_user)):
    rate_key = update.get("rate_key")
    new_rate = update.get("new_rate")
    
    if not rate_key or new_rate is None or new_rate <= 0:
        raise HTTPException(status_code=400, detail="Invalid data")
    
    # Get current rates
    rates_doc = await db.exchange_rates.find_one({"id": "exchange_matrix"}, {"_id": 0})
    if not rates_doc:
        raise HTTPException(status_code=404, detail="Exchange rates not found")
    
    rates = rates_doc.get("rates", {})
    old_rate = rates.get(rate_key, 0)
    rates[rate_key] = new_rate
    
    await db.exchange_rates.update_one(
        {"id": "exchange_matrix"},
        {"$set": {"rates": rates}}
    )
    
    await log_admin_action(
        current_user["minecraft_username"],
        "UPDATE_EXCHANGE_RATE",
        f"Rate: {rate_key}, Old: {old_rate}, New: {new_rate}"
    )
    
    return {"message": "Exchange rate updated", "rate_key": rate_key, "new_rate": new_rate}

@api_router.put("/admin/user/real-money-access")
async def admin_toggle_real_money_access(user_id: str, enable: bool, current_user: dict = Depends(get_admin_user)):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"can_use_real_money": enable}}
    )
    
    await log_admin_action(
        current_user["minecraft_username"],
        "TOGGLE_REAL_MONEY_ACCESS",
        f"User: {user['minecraft_username']}, Enabled: {enable}"
    )
    
    return {"message": f"Real money access {'enabled' if enable else 'disabled'} for {user['minecraft_username']}"}

@api_router.post("/admin/transaction/refund")
async def admin_refund_transaction(transaction_id: str, current_user: dict = Depends(get_admin_user)):
    # Find payment transaction
    payment = await db.payment_transactions.find_one({"id": transaction_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if payment.get("refunded", False):
        raise HTTPException(status_code=400, detail="Already refunded")
    
    # Refund logic - deduct the items/currency that were given
    metadata = payment.get("metadata", {})
    user_id = payment["user_id"]
    
    if metadata.get("package_type") == "currency":
        currency = metadata["currency_type"]
        quantity = float(metadata["quantity"])
        
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {f"balances.{currency}": -quantity}}
        )
    elif metadata.get("package_type") == "rank":
        rank = metadata["package_id"]
        await db.users.update_one(
            {"id": user_id},
            {"$pull": {"owned_ranks": rank}}
        )
    
    # Mark as refunded
    await db.payment_transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "refunded": True,
            "refunded_at": datetime.now(timezone.utc).isoformat(),
            "refunded_by": current_user["minecraft_username"]
        }}
    )
    
    await log_admin_action(
        current_user["minecraft_username"],
        "REFUND_TRANSACTION",
        f"Transaction ID: {transaction_id}, Amount: ${payment['amount']}"
    )
    
    return {"message": "Transaction refunded successfully"}

# House Building Type Routes
@api_router.get("/houses/building-types")
async def get_building_types():
    return {"types": [
        "House", "Floor", "Complex", "Apartment", "Business",
        "Industrial", "Factory", "Park", "Agricultural Land", "Zoned Area"
    ]}

@api_router.post("/houses/list-with-type")
async def list_house_with_type(house_data: dict, current_user: dict = Depends(get_current_user)):
    required_fields = ["name", "description", "location", "building_type", "price_currency", "price_amount"]
    for field in required_fields:
        if field not in house_data:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")
    
    house = {
        "id": str(uuid.uuid4()),
        "name": house_data["name"],
        "description": house_data["description"],
        "location": house_data["location"],
        "building_type": house_data["building_type"],
        "price_currency": house_data["price_currency"],
        "price_amount": float(house_data["price_amount"]),
        "owner_id": current_user["id"],
        "owner_username": current_user["minecraft_username"],
        "images": house_data.get("images", []),
        "status": "pending",
        "listed_at": datetime.now(timezone.utc).isoformat(),
        "admin_approved": False
    }
    
    await db.houses.insert_one(house)
    return {"message": "House listed successfully. Waiting for admin approval.", "house_id": house["id"]}

@api_router.post("/houses/buy-with-currency")
async def buy_house_with_any_currency(house_id: str, payment_currency: str, current_user: dict = Depends(get_current_user)):
    house = await db.houses.find_one({"id": house_id}, {"_id": 0})
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    if house["status"] != "available":
        raise HTTPException(status_code=400, detail="House not available")
    
    # Convert price to payment currency
    house_currency = house["price_currency"]
    house_price = house["price_amount"]
    
    if payment_currency == house_currency:
        final_price = house_price
    else:
        rate = await get_exchange_rate(house_currency, payment_currency)
        final_price = house_price * rate
    
    # Check balance
    if current_user["balances"][payment_currency] < final_price:
        raise HTTPException(status_code=400, detail=f"Insufficient {payment_currency} balance")
    
    # Create title deed
    title_deed = {
        "id": str(uuid.uuid4()),
        "house_id": house_id,
        "house_name": house["name"],
        "building_type": house.get("building_type", "House"),
        "owner_id": current_user["id"],
        "owner_username": current_user["minecraft_username"],
        "previous_owner_id": house.get("owner_id"),
        "previous_owner_username": house.get("owner_username"),
        "purchase_price": final_price,
        "purchase_currency": payment_currency,
        "issued_date": datetime.now(timezone.utc).isoformat(),
        "location": house["location"]
    }
    
    await db.title_deeds.insert_one(title_deed)
    
    # Update user and house
    await db.users.update_one(
        {"id": current_user["id"]},
        {
            "$inc": {f"balances.{payment_currency}": -final_price, "total_transactions": 1},
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
                "title_deed_id": title_deed["id"]
            }
        }
    )
    
    return {
        "message": "House purchased successfully! Title deed issued.",
        "title_deed_id": title_deed["id"],
        "paid": f"{final_price:.2f} {payment_currency}"
    }

@api_router.post("/houses/swap")
async def swap_houses(swap_data: dict, current_user: dict = Depends(get_current_user)):
    my_house_id = swap_data.get("my_house_id")
    their_house_id = swap_data.get("their_house_id")
    
    # Get both houses
    my_house = await db.houses.find_one({"id": my_house_id}, {"_id": 0})
    their_house = await db.houses.find_one({"id": their_house_id}, {"_id": 0})
    
    if not my_house or not their_house:
        raise HTTPException(status_code=404, detail="House not found")
    
    # Verify ownership
    if my_house["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You don't own this house")
    
    # Calculate price difference
    my_price = my_house["price_amount"]
    their_price = their_house["price_amount"]
    currency = my_house["price_currency"]
    
    # Convert their price if different currency
    if their_house["price_currency"] != currency:
        rate = await get_exchange_rate(their_house["price_currency"], currency)
        their_price_converted = their_price * rate
    else:
        their_price_converted = their_price
    
    price_difference = abs(my_price - their_price_converted)
    
    # Determine who pays
    if my_price < their_price_converted:
        # Current user pays difference
        if current_user["balances"][currency] < price_difference:
            raise HTTPException(status_code=400, detail="Insufficient balance to cover price difference")
        
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {f"balances.{currency}": -price_difference}}
        )
        
        await db.users.update_one(
            {"id": their_house["owner_id"]},
            {"$inc": {f"balances.{currency}": price_difference}}
        )
    elif my_price > their_price_converted:
        # Other user pays difference (credited to current user)
        other_user = await db.users.find_one({"id": their_house["owner_id"]}, {"_id": 0})
        if other_user["balances"][currency] < price_difference:
            raise HTTPException(status_code=400, detail="Other user has insufficient balance")
        
        await db.users.update_one(
            {"id": their_house["owner_id"]},
            {"$inc": {f"balances.{currency}": -price_difference}}
        )
        
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {f"balances.{currency}": price_difference}}
        )
    
    # Swap ownership
    await db.houses.update_one(
        {"id": my_house_id},
        {"$set": {"owner_id": their_house["owner_id"], "owner_username": their_house["owner_username"]}}
    )
    
    await db.houses.update_one(
        {"id": their_house_id},
        {"$set": {"owner_id": current_user["id"], "owner_username": current_user["minecraft_username"]}}
    )
    
    # Update user house lists
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$pull": {"owned_houses": my_house_id}, "$push": {"owned_houses": their_house_id}}
    )
    
    await db.users.update_one(
        {"id": their_house["owner_id"]},
        {"$pull": {"owned_houses": their_house_id}, "$push": {"owned_houses": my_house_id}}
    )
    
    return {
        "message": "Houses swapped successfully",
        "price_difference": f"{price_difference:.2f} {currency}",
        "paid_by": "you" if my_price < their_price_converted else "them" if my_price > their_price_converted else "none"
    }

@api_router.get("/admin/investment-history/{symbol}")
async def get_investment_price_history(symbol: str, current_user: dict = Depends(get_current_user)):
    investment = await db.investments.find_one({"symbol": symbol}, {"_id": 0})
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    return {
        "symbol": symbol,
        "name": investment["name"],
        "current_price": investment["current_price"],
        "currency": investment["currency"],
        "price_history": investment.get("price_history", [])
    }


# Transaction History & Activity Feed Routes
@api_router.get("/transactions/history")
async def get_transaction_history(
    current_user: dict = Depends(get_current_user),
    transaction_type: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
):
    """Get user's transaction history across all activities"""
    user_id = current_user["id"]
    
    # Collect all transactions
    all_transactions = []
    
    # Payment transactions
    payment_txns = await db.payment_transactions.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for txn in payment_txns:
        all_transactions.append({
            "id": txn.get("id"),
            "type": "payment",
            "action": f"Purchased {txn.get('metadata', {}).get('package_type', 'item')}",
            "amount": txn.get("amount", 0),
            "currency": "USD",
            "status": txn.get("payment_status", "pending"),
            "timestamp": txn.get("created_at"),
            "details": txn.get("metadata", {})
        })
    
    # Investment transactions
    investment_txns = await db.investment_transactions.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(1000)
    
    for txn in investment_txns:
        action = "Bought" if txn.get("transaction_type") == "buy" else "Sold"
        all_transactions.append({
            "id": txn.get("id"),
            "type": "investment",
            "action": f"{action} {txn.get('quantity')} shares of {txn.get('symbol')}",
            "amount": txn.get("total_amount", 0),
            "currency": txn.get("currency", "GRP"),
            "status": "completed",
            "timestamp": txn.get("timestamp"),
            "details": {
                "symbol": txn.get("symbol"),
                "quantity": txn.get("quantity"),
                "price_per_unit": txn.get("price_per_unit"),
                "commission": txn.get("commission")
            }
        })
    
    # House purchases (from title deeds)
    title_deeds = await db.title_deeds.find(
        {"owner_id": user_id},
        {"_id": 0}
    ).sort("issued_date", -1).to_list(1000)
    
    for deed in title_deeds:
        all_transactions.append({
            "id": deed.get("id"),
            "type": "property",
            "action": f"Purchased {deed.get('house_name')}",
            "amount": deed.get("purchase_price", 0),
            "currency": deed.get("purchase_currency", "GRP"),
            "status": "completed",
            "timestamp": deed.get("issued_date"),
            "details": {
                "house_name": deed.get("house_name"),
                "location": deed.get("location"),
                "previous_owner": deed.get("previous_owner_username")
            }
        })
    
    # Bounties created
    bounties_created = await db.bounties.find(
        {"creator_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for bounty in bounties_created:
        all_transactions.append({
            "id": bounty.get("id"),
            "type": "bounty_create",
            "action": f"Created bounty: {bounty.get('title')}",
            "amount": -bounty.get("reward_amount", 0),
            "currency": bounty.get("reward_currency", "GRP"),
            "status": bounty.get("status", "active"),
            "timestamp": bounty.get("created_at"),
            "details": {
                "title": bounty.get("title"),
                "bounty_type": bounty.get("bounty_type"),
                "target": bounty.get("target_player")
            }
        })
    
    # Bounties completed
    bounties_completed = await db.bounties.find(
        {"completed_by": user_id},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(1000)
    
    for bounty in bounties_completed:
        all_transactions.append({
            "id": bounty.get("id"),
            "type": "bounty_complete",
            "action": f"Completed bounty: {bounty.get('title')}",
            "amount": bounty.get("reward_amount", 0),
            "currency": bounty.get("reward_currency", "GRP"),
            "status": "completed",
            "timestamp": bounty.get("completed_at"),
            "details": {
                "title": bounty.get("title"),
                "creator": bounty.get("creator_username")
            }
        })
    
    # Sort all transactions by timestamp
    all_transactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Filter by type if specified
    if transaction_type:
        all_transactions = [t for t in all_transactions if t["type"] == transaction_type]
    
    # Apply pagination
    total = len(all_transactions)
    paginated = all_transactions[skip:skip + limit]
    
    return {
        "transactions": paginated,
        "total": total,
        "limit": limit,
        "skip": skip
    }

@api_router.get("/activity/feed")
async def get_activity_feed(limit: int = 20, skip: int = 0):
    """Get recent activity across the platform"""
    activities = []
    
    # Recent house sales
    recent_houses = await db.houses.find(
        {"status": "sold"},
        {"_id": 0}
    ).sort("sold_at", -1).limit(10).to_list(10)
    
    for house in recent_houses:
        activities.append({
            "type": "house_sale",
            "message": f"{house.get('owner_username')} purchased {house.get('name')}",
            "timestamp": house.get("sold_at"),
            "icon": "home"
        })
    
    # Recent bounties
    recent_bounties = await db.bounties.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    for bounty in recent_bounties:
        if bounty.get("status") == "completed":
            activities.append({
                "type": "bounty_completed",
                "message": f"{bounty.get('completed_by_username')} completed bounty: {bounty.get('title')}",
                "timestamp": bounty.get("completed_at"),
                "icon": "target"
            })
        else:
            activities.append({
                "type": "bounty_created",
                "message": f"{bounty.get('creator_username')} created bounty: {bounty.get('title')}",
                "timestamp": bounty.get("created_at"),
                "icon": "target"
            })
    
    # Recent user registrations
    recent_users = await db.users.find(
        {},
        {"_id": 0, "minecraft_username": 1, "created_at": 1, "currency_type": 1}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    for user in recent_users:
        activities.append({
            "type": "user_joined",
            "message": f"{user.get('minecraft_username')} joined {user.get('currency_type')} server",
            "timestamp": user.get("created_at"),
            "icon": "user"
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Apply pagination
    total = len(activities)
    paginated = activities[skip:skip + limit]
    
    return {
        "activities": paginated,
        "total": total
    }

@api_router.get("/portfolio/summary")
async def get_portfolio_summary(current_user: dict = Depends(get_current_user)):
    """Get comprehensive portfolio summary with calculated values"""
    user_id = current_user["id"]
    
    # Calculate total currency value in GRP
    rates = await get_currency_rates()
    total_currency_value = 0.0
    currency_breakdown = {}
    
    for currency, balance in current_user["balances"].items():
        if balance > 0:
            # Convert to GRP
            if currency == "GRP":
                grp_value = balance
            else:
                rate_key = f"GRP_TO_{currency}"
                grp_value = balance / rates[rate_key]
            
            total_currency_value += grp_value
            currency_breakdown[currency] = {
                "balance": balance,
                "grp_value": grp_value
            }
    
    # Calculate investment portfolio value
    portfolio = current_user.get("portfolio", {})
    investments_value = 0.0
    investment_breakdown = []
    
    for symbol, quantity in portfolio.items():
        if quantity > 0:
            investment = await db.investments.find_one({"symbol": symbol}, {"_id": 0})
            if investment:
                current_price = investment["current_price"]
                currency = investment["currency"]
                total_value = current_price * quantity
                
                # Convert to GRP
                if currency == "GRP":
                    grp_value = total_value
                else:
                    rate_key = f"GRP_TO_{currency}"
                    grp_value = total_value / rates[rate_key]
                
                investments_value += grp_value
                investment_breakdown.append({
                    "symbol": symbol,
                    "name": investment["name"],
                    "quantity": quantity,
                    "current_price": current_price,
                    "currency": currency,
                    "total_value": total_value,
                    "grp_value": grp_value
                })
    
    # Calculate property value
    owned_houses = current_user.get("owned_houses", [])
    properties_value = 0.0
    property_breakdown = []
    
    for house_id in owned_houses:
        house = await db.houses.find_one({"id": house_id}, {"_id": 0})
        if house:
            # Get original purchase price from title deed
            title_deed = await db.title_deeds.find_one(
                {"house_id": house_id, "owner_id": user_id},
                {"_id": 0}
            )
            
            if title_deed:
                price = title_deed["purchase_price"]
                currency = title_deed["purchase_currency"]
                
                # Convert to GRP
                if currency == "GRP":
                    grp_value = price
                else:
                    rate_key = f"GRP_TO_{currency}"
                    grp_value = price / rates[rate_key]
                
                properties_value += grp_value
                property_breakdown.append({
                    "id": house_id,
                    "name": house["name"],
                    "location": house.get("location"),
                    "purchase_price": price,
                    "currency": currency,
                    "grp_value": grp_value,
                    "building_type": house.get("building_type", "House")
                })
    
    # Total net worth in GRP
    total_net_worth = total_currency_value + investments_value + properties_value
    
    # Convert total to USD for reference
    usd_value = total_net_worth * rates["GRP_TO_USD"]
    
    return {
        "net_worth": {
            "total_grp": total_net_worth,
            "total_usd": usd_value,
            "currency_value": total_currency_value,
            "investments_value": investments_value,
            "properties_value": properties_value
        },
        "breakdown": {
            "currencies": currency_breakdown,
            "investments": investment_breakdown,
            "properties": property_breakdown
        },
        "stats": {
            "total_spent": current_user.get("total_spent", 0),
            "total_transactions": current_user.get("total_transactions", 0),
            "owned_ranks": len(current_user.get("owned_ranks", [])),
            "owned_houses": len(owned_houses),
            "active_investments": len([q for q in portfolio.values() if q > 0])
        }
    }


# Price History & Charts Routes
@api_router.get("/stocks/{symbol}/history")
async def get_stock_price_history(
    symbol: str,
    days: Optional[int] = 90,
    current_user: dict = Depends(get_current_user)
):
    """Get historical price data for a specific stock"""
    investment = await db.investments.find_one({"symbol": symbol}, {"_id": 0})
    if not investment:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    price_history = investment.get("price_history", [])
    
    # Limit to requested days
    if days and len(price_history) > days:
        price_history = price_history[-days:]
    
    return {
        "symbol": symbol,
        "name": investment["name"],
        "currency": investment["currency"],
        "current_price": investment["current_price"],
        "history": price_history
    }

@api_router.get("/currency/history")
async def get_currency_exchange_history(
    days: Optional[int] = 90,
    current_user: dict = Depends(get_current_user)
):
    """Get historical exchange rate data"""
    # Fetch from exchange_rate_history collection
    history = await db.exchange_rate_history.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(days).to_list(days or 90)
    
    # Reverse to get chronological order
    history.reverse()
    
    return {
        "history": history,
        "current_rates": await get_currency_rates()
    }

@api_router.get("/market/overview")
async def get_market_overview(current_user: dict = Depends(get_current_user)):
    """Get overall market statistics and top movers"""
    investments = await db.investments.find({}, {"_id": 0}).to_list(1000)
    
    top_gainers = []
    top_losers = []
    
    for inv in investments:
        history = inv.get("price_history", [])
        if len(history) >= 2:
            start_price = history[0]["price"]
            current_price = inv["current_price"]
            change_pct = ((current_price - start_price) / start_price) * 100
            
            inv_data = {
                "symbol": inv["symbol"],
                "name": inv["name"],
                "currency": inv["currency"],
                "current_price": current_price,
                "change_percent": round(change_pct, 2)
            }
            
            if change_pct > 0:
                top_gainers.append(inv_data)
            else:
                top_losers.append(inv_data)
    
    # Sort and get top 5
    top_gainers = sorted(top_gainers, key=lambda x: x["change_percent"], reverse=True)[:5]
    top_losers = sorted(top_losers, key=lambda x: x["change_percent"])[:5]
    
    return {
        "total_stocks": len(investments),
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "currencies": ["NIM", "GRP", "VDD", "KKD"]
    }




# ============================================================================
# NEW ADMIN USER MANAGEMENT ENDPOINTS
# ============================================================================

@api_router.post("/admin/users/ban")
async def ban_user(data: UserBanUpdate, admin: dict = Depends(require_admin)):
    """Ban or unban a user (admin/superadmin only)"""
    target_user = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent banning superadmins
    if target_user.get("role") == "superadmin":
        raise HTTPException(status_code=403, detail="Cannot ban a superadmin")
    
    # Regular admins can't ban other admins (only superadmins can)
    if admin.get("role") == "admin" and target_user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Only superadmins can ban admins")
    
    await db.users.update_one(
        {"id": data.user_id},
        {"$set": {"banned": data.banned}}
    )
    
    action = "banned" if data.banned else "unbanned"
    await log_admin_action(
        admin["minecraft_username"],
        f"User {action}",
        f"User {target_user['minecraft_username']} (ID: {data.user_id})"
    )
    
    return {
        "message": f"User successfully {action}",
        "user_id": data.user_id,
        "banned": data.banned
    }

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_superadmin)):
    """Delete a user permanently (superadmin only)"""
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting superadmins (even by other superadmins)
    if target_user.get("role") == "superadmin":
        raise HTTPException(status_code=403, detail="Cannot delete a superadmin")
    
    # Delete user
    await db.users.delete_one({"id": user_id})
    
    await log_admin_action(
        admin["minecraft_username"],
        "User deleted",
        f"User {target_user['minecraft_username']} (ID: {user_id}) permanently deleted"
    )
    
    return {
        "message": "User deleted successfully",
        "user_id": user_id
    }

@api_router.put("/admin/users/role")
async def change_user_role(data: UserRoleUpdate, admin: dict = Depends(require_superadmin)):
    """Change user role (superadmin only)"""
    if data.new_role not in ["user", "admin", "superadmin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be: user, admin, or superadmin")
    
    target_user = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update role
    await db.users.update_one(
        {"id": data.user_id},
        {"$set": {"role": data.new_role}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Role changed",
        f"User {target_user['minecraft_username']} role changed to {data.new_role}"
    )
    
    return {
        "message": "User role updated successfully",
        "user_id": data.user_id,
        "new_role": data.new_role
    }

@api_router.put("/admin/users/currency")
async def change_user_currency(data: UserCurrencyUpdate, admin: dict = Depends(require_admin)):
    """Change user's primary currency (admin/superadmin only)"""
    if data.new_currency_type not in ["NIM", "GRP", "VDD", "KKD"]:
        raise HTTPException(status_code=400, detail="Invalid currency type")
    
    target_user = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": data.user_id},
        {"$set": {"currency_type": data.new_currency_type}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Currency changed",
        f"User {target_user['minecraft_username']} currency changed to {data.new_currency_type}"
    )
    
    return {
        "message": "User currency updated successfully",
        "user_id": data.user_id,
        "new_currency_type": data.new_currency_type
    }

@api_router.get("/admin/users/list")
async def list_all_users(admin: dict = Depends(require_admin), skip: int = 0, limit: int = 50):
    """List all users with pagination (admin/superadmin only)"""
    users = await db.users.find(
        {},
        {"_id": 0, "password_hash": 0}  # Exclude sensitive data
    ).skip(skip).limit(limit).to_list(limit)
    
    total = await db.users.count_documents({})
    
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@api_router.get("/admin/logs")
async def get_admin_logs(admin: dict = Depends(require_admin), limit: int = 100):
    """Get recent admin action logs (admin/superadmin only)"""
    logs = await db.admin_logs.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {
        "logs": logs,
        "total": len(logs)
    }



# ============================================================================
# ADMIN INVESTMENT MANAGEMENT ENDPOINTS
# ============================================================================

@api_router.post("/admin/investment/create")
async def create_stock(data: StockCreate, admin: dict = Depends(require_admin)):
    """Create a new stock (admin/superadmin only)"""
    # Check if stock already exists
    existing = await db.investments.find_one({"symbol": data.symbol})
    if existing:
        raise HTTPException(status_code=400, detail="Stock symbol already exists")
    
    # Validate currency
    if data.currency not in ["NIM", "GRP", "VDD", "KKD"]:
        raise HTTPException(status_code=400, detail="Invalid currency")
    
    # Create investment document
    investment = {
        "id": str(uuid.uuid4()),
        "symbol": data.symbol,
        "name": data.name,
        "currency": data.currency,
        "current_price": data.current_price,
        "price_history": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "price": data.current_price,
                "old_price": 0,
                "change": 0
            }
        ],
        "disabled": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    await db.investments.insert_one(investment)
    
    await log_admin_action(
        admin["minecraft_username"],
        "Stock created",
        f"Created {data.symbol}: {data.name} at {data.current_price} {data.currency}"
    )
    
    return {
        "message": "Stock created successfully",
        "stock": {
            "id": investment["id"],
            "symbol": data.symbol,
            "name": data.name,
            "currency": data.currency,
            "current_price": data.current_price
        }
    }

@api_router.put("/admin/investment/name")
async def update_stock_name(data: StockNameUpdate, admin: dict = Depends(require_admin)):
    """Update stock name (admin/superadmin only)"""
    investment = await db.investments.find_one({"symbol": data.symbol}, {"_id": 0})
    if not investment:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    old_name = investment["name"]
    
    await db.investments.update_one(
        {"symbol": data.symbol},
        {
            "$set": {
                "name": data.new_name,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Stock name updated",
        f"{data.symbol}: '{old_name}' → '{data.new_name}'"
    )
    
    return {
        "message": "Stock name updated successfully",
        "symbol": data.symbol,
        "old_name": old_name,
        "new_name": data.new_name
    }

@api_router.put("/admin/investment/price")
async def update_stock_price(data: StockPriceUpdate, admin: dict = Depends(require_admin)):
    """Update stock price and add to price_history (admin/superadmin only)"""
    investment = await db.investments.find_one({"symbol": data.symbol}, {"_id": 0})
    if not investment:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    old_price = investment["current_price"]
    price_change = ((data.new_price - old_price) / old_price) * 100 if old_price > 0 else 0
    
    # Create price history entry
    price_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "price": data.new_price,
        "old_price": old_price,
        "change": round(price_change, 2)
    }
    
    # Update investment
    await db.investments.update_one(
        {"symbol": data.symbol},
        {
            "$set": {
                "current_price": data.new_price,
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "$push": {"price_history": price_entry}
        }
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Stock price updated",
        f"{data.symbol}: {old_price} → {data.new_price} ({price_change:+.2f}%)"
    )
    
    return {
        "message": "Stock price updated successfully",
        "symbol": data.symbol,
        "old_price": old_price,
        "new_price": data.new_price,
        "change_percent": round(price_change, 2)
    }

@api_router.put("/admin/investment/currency")
async def update_stock_currency(data: StockCurrencyUpdate, admin: dict = Depends(require_admin)):
    """Change stock currency (admin/superadmin only)"""
    # Get available currencies dynamically
    available = await get_available_currencies()
    if data.new_currency not in available:
        raise HTTPException(status_code=400, detail="Invalid currency")
    
    investment = await db.investments.find_one({"symbol": data.symbol}, {"_id": 0})
    if not investment:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    old_currency = investment["currency"]
    
    await db.investments.update_one(
        {"symbol": data.symbol},
        {
            "$set": {
                "currency": data.new_currency,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Stock currency updated",
        f"{data.symbol}: {old_currency} → {data.new_currency}"
    )
    
    return {
        "message": "Stock currency updated successfully",
        "symbol": data.symbol,
        "old_currency": old_currency,
        "new_currency": data.new_currency
    }

@api_router.put("/admin/investment/status")
async def update_stock_status(data: StockStatusUpdate, admin: dict = Depends(require_admin)):
    """Enable or disable stock (soft delete) (admin/superadmin only)"""
    investment = await db.investments.find_one({"symbol": data.symbol}, {"_id": 0})
    if not investment:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    await db.investments.update_one(
        {"symbol": data.symbol},
        {
            "$set": {
                "disabled": data.disabled,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    status_text = "disabled" if data.disabled else "enabled"
    
    await log_admin_action(
        admin["minecraft_username"],
        f"Stock {status_text}",
        f"{data.symbol}: {investment['name']}"
    )
    
    return {
        "message": f"Stock {status_text} successfully",
        "symbol": data.symbol,
        "disabled": data.disabled
    }

@api_router.get("/admin/investment/list")
async def list_all_stocks(admin: dict = Depends(require_admin), include_disabled: bool = False):
    """List all stocks with optional disabled filter (admin/superadmin only)"""
    query = {} if include_disabled else {"disabled": {"$ne": True}}
    
    stocks = await db.investments.find(query, {"_id": 0}).to_list(1000)
    
    return {
        "stocks": stocks,
        "total": len(stocks)
    }


# ============================================================================
# CURRENCY MANAGEMENT ENDPOINTS
# ============================================================================

@api_router.get("/currencies")
async def get_currencies():
    """Get all available currencies with their display names (public endpoint)"""
    info = await get_currency_info()
    return info

@api_router.get("/currencies/rates")
async def get_all_exchange_rates():
    """Get complete exchange rate matrix (public endpoint)"""
    rates_doc = await db.exchange_rates.find_one({"id": "exchange_matrix"}, {"_id": 0})
    if rates_doc:
        return {"rates": rates_doc.get("rates", DEFAULT_EXCHANGE_MATRIX)}
    return {"rates": DEFAULT_EXCHANGE_MATRIX}

@api_router.post("/admin/currencies")
async def add_currency(data: CurrencyCreate, admin: dict = Depends(require_admin)):
    """Add a new currency to the system (admin only)"""
    # Get current currencies
    currencies_doc = await db.currencies.find_one({"id": "currency_list"})
    
    if currencies_doc:
        currencies = currencies_doc.get("currencies", [])
        names = currencies_doc.get("names", {})
    else:
        currencies = list(ALL_CURRENCIES)
        names = dict(CURRENCY_NAMES)
    
    # Check if currency already exists
    if data.code.upper() in currencies:
        raise HTTPException(status_code=400, detail="Currency already exists")
    
    # Add new currency
    new_code = data.code.upper()
    currencies.append(new_code)
    names[new_code] = data.name
    
    # Update currencies collection
    await db.currencies.update_one(
        {"id": "currency_list"},
        {
            "$set": {
                "currencies": currencies,
                "names": names,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Add exchange rates for new currency
    rates_doc = await db.exchange_rates.find_one({"id": "exchange_matrix"})
    if rates_doc:
        rates = rates_doc.get("rates", {})
    else:
        rates = dict(DEFAULT_EXCHANGE_MATRIX)
    
    # Calculate rates based on GRP base rate
    for existing_currency in currencies:
        if existing_currency == new_code:
            rates[f"{new_code}_TO_{new_code}"] = 1.0
        else:
            # Get GRP rate for existing currency
            grp_to_existing = rates.get(f"GRP_TO_{existing_currency}", 1.0)
            
            # New currency to existing: (1/base_rate_to_grp) * grp_to_existing
            new_to_existing = (1.0 / data.base_rate_to_grp) * grp_to_existing
            rates[f"{new_code}_TO_{existing_currency}"] = new_to_existing
            
            # Existing to new currency: inverse
            existing_to_new = 1.0 / new_to_existing if new_to_existing != 0 else 0
            rates[f"{existing_currency}_TO_{new_code}"] = existing_to_new
    
    # Add GRP to new currency rate
    rates[f"GRP_TO_{new_code}"] = data.base_rate_to_grp
    rates[f"{new_code}_TO_GRP"] = 1.0 / data.base_rate_to_grp if data.base_rate_to_grp != 0 else 0
    
    # Update exchange rates
    await db.exchange_rates.update_one(
        {"id": "exchange_matrix"},
        {"$set": {"rates": rates, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Currency added",
        f"Code: {new_code}, Name: {data.name}, GRP Rate: {data.base_rate_to_grp}"
    )
    
    return {
        "message": "Currency added successfully",
        "currency": {
            "code": new_code,
            "name": data.name,
            "base_rate_to_grp": data.base_rate_to_grp
        }
    }

@api_router.put("/admin/currencies")
async def update_currency(data: CurrencyUpdate, admin: dict = Depends(require_admin)):
    """Update currency name or rate (admin only)"""
    currencies_doc = await db.currencies.find_one({"id": "currency_list"})
    
    if not currencies_doc:
        raise HTTPException(status_code=404, detail="Currency system not initialized")
    
    currencies = currencies_doc.get("currencies", [])
    names = currencies_doc.get("names", {})
    
    if data.code not in currencies:
        raise HTTPException(status_code=404, detail="Currency not found")
    
    # Update name if provided
    if data.name is not None:
        old_name = names.get(data.code, data.code)
        names[data.code] = data.name
        await db.currencies.update_one(
            {"id": "currency_list"},
            {"$set": {"names": names, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        await log_admin_action(
            admin["minecraft_username"],
            "Currency name updated",
            f"{data.code}: '{old_name}' → '{data.name}'"
        )
    
    # Update rate if provided
    if data.base_rate_to_grp is not None:
        rates_doc = await db.exchange_rates.find_one({"id": "exchange_matrix"})
        rates = rates_doc.get("rates", {}) if rates_doc else dict(DEFAULT_EXCHANGE_MATRIX)
        
        old_rate = rates.get(f"GRP_TO_{data.code}", 1.0)
        
        # Update all rates involving this currency
        for currency in currencies:
            if currency == data.code:
                continue
            
            # Get GRP rate for other currency
            grp_to_other = rates.get(f"GRP_TO_{currency}", 1.0)
            
            # Update data.code to other
            new_to_other = (1.0 / data.base_rate_to_grp) * grp_to_other if data.base_rate_to_grp != 0 else 0
            rates[f"{data.code}_TO_{currency}"] = new_to_other
            
            # Update other to data.code
            rates[f"{currency}_TO_{data.code}"] = 1.0 / new_to_other if new_to_other != 0 else 0
        
        rates[f"GRP_TO_{data.code}"] = data.base_rate_to_grp
        rates[f"{data.code}_TO_GRP"] = 1.0 / data.base_rate_to_grp if data.base_rate_to_grp != 0 else 0
        
        await db.exchange_rates.update_one(
            {"id": "exchange_matrix"},
            {"$set": {"rates": rates, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        
        await log_admin_action(
            admin["minecraft_username"],
            "Currency rate updated",
            f"{data.code}: GRP rate {old_rate} → {data.base_rate_to_grp}"
        )
    
    return {"message": "Currency updated successfully", "code": data.code}

@api_router.put("/admin/exchange-rate/direct")
async def update_direct_exchange_rate(data: ExchangeRateUpdate, admin: dict = Depends(require_admin)):
    """Update a specific exchange rate directly (admin only)"""
    currencies = await get_available_currencies()
    
    if data.from_currency not in currencies or data.to_currency not in currencies:
        raise HTTPException(status_code=400, detail="Invalid currency")
    
    if data.rate <= 0:
        raise HTTPException(status_code=400, detail="Rate must be positive")
    
    rates_doc = await db.exchange_rates.find_one({"id": "exchange_matrix"})
    rates = rates_doc.get("rates", {}) if rates_doc else dict(DEFAULT_EXCHANGE_MATRIX)
    
    rate_key = f"{data.from_currency}_TO_{data.to_currency}"
    old_rate = rates.get(rate_key, 0)
    rates[rate_key] = data.rate
    
    # Also update inverse rate
    inverse_key = f"{data.to_currency}_TO_{data.from_currency}"
    rates[inverse_key] = 1.0 / data.rate
    
    await db.exchange_rates.update_one(
        {"id": "exchange_matrix"},
        {"$set": {"rates": rates, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Exchange rate updated",
        f"{rate_key}: {old_rate} → {data.rate}"
    )
    
    return {
        "message": "Exchange rate updated",
        "rate_key": rate_key,
        "old_rate": old_rate,
        "new_rate": data.rate
    }

@api_router.delete("/admin/currencies/{currency_code}")
async def delete_currency(currency_code: str, admin: dict = Depends(require_admin)):
    """Remove a currency from the system (admin only) - only works for non-base currencies"""
    base_currencies = ["NIM", "GRP", "VDD", "KKD"]  # These cannot be deleted
    
    if currency_code.upper() in base_currencies:
        raise HTTPException(status_code=400, detail="Cannot delete base currencies")
    
    currencies_doc = await db.currencies.find_one({"id": "currency_list"})
    if not currencies_doc:
        raise HTTPException(status_code=404, detail="Currency system not initialized")
    
    currencies = currencies_doc.get("currencies", [])
    names = currencies_doc.get("names", {})
    
    if currency_code.upper() not in currencies:
        raise HTTPException(status_code=404, detail="Currency not found")
    
    # Remove currency
    currencies.remove(currency_code.upper())
    if currency_code.upper() in names:
        del names[currency_code.upper()]
    
    await db.currencies.update_one(
        {"id": "currency_list"},
        {"$set": {"currencies": currencies, "names": names, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Remove exchange rates involving this currency
    rates_doc = await db.exchange_rates.find_one({"id": "exchange_matrix"})
    if rates_doc:
        rates = rates_doc.get("rates", {})
        keys_to_remove = [k for k in rates.keys() if currency_code.upper() in k]
        for key in keys_to_remove:
            del rates[key]
        
        await db.exchange_rates.update_one(
            {"id": "exchange_matrix"},
            {"$set": {"rates": rates, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Currency deleted",
        f"Code: {currency_code.upper()}"
    )
    
    return {"message": "Currency deleted successfully", "code": currency_code.upper()}

@api_router.post("/admin/currencies/initialize")
async def initialize_currency_system(admin: dict = Depends(require_admin)):
    """Initialize or reset the currency system with defaults (admin only)"""
    # Initialize currencies
    await db.currencies.update_one(
        {"id": "currency_list"},
        {
            "$set": {
                "currencies": ALL_CURRENCIES,
                "names": CURRENCY_NAMES,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Initialize exchange matrix
    await db.exchange_rates.update_one(
        {"id": "exchange_matrix"},
        {
            "$set": {
                "rates": DEFAULT_EXCHANGE_MATRIX,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Currency system initialized",
        f"Currencies: {ALL_CURRENCIES}"
    )
    
    return {
        "message": "Currency system initialized",
        "currencies": ALL_CURRENCIES,
        "rates_count": len(DEFAULT_EXCHANGE_MATRIX)
    }

# Add new balances (EP, EGD) to existing users
@api_router.post("/admin/users/migrate-balances")
async def migrate_user_balances(admin: dict = Depends(require_admin)):
    """Add new currency balances (EP, EGD) to all existing users"""
    result = await db.users.update_many(
        {},
        {
            "$set": {
                "balances.EP": 0,
                "balances.EGD": 0
            }
        }
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "User balances migrated",
        f"Updated {result.modified_count} users with EP and EGD balances"
    )
    
    return {
        "message": "User balances migrated successfully",
        "users_updated": result.modified_count
    }


# Include the router in the main app
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

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await initialize_exchange_matrix()
    await initialize_currencies()
    logger.info("Database initialized with currencies and exchange rates")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
