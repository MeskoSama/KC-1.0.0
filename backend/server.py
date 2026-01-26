from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
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
        },
        "government": {
            "leader_type": "Emperor",
            "leader_name": "Aurelius von Eisenhart",
            "government_system": "Consular Monarchy",
            "total_seats": 0,
            "council": [
                {"name": "Meskop", "role": "player", "age": 20},
                {"name": "Muzlupankek", "role": "player", "age": 18},
                {"name": "Aurelius von Eisenhart", "role": "MAI", "age": 102},
                {"name": "Rheinvald", "role": "Merchant", "age": 28},
                {"name": "Friedrich Von Kiel", "role": "Merchant", "age": 31},
                {"name": "Marcellin Kade", "role": "Merchant", "age": 25},
                {"name": "Umbrax", "role": "Monster", "age": 116},
                {"name": "Redfang", "role": "Piglin", "age": 420},
                {"name": "Velgoum Bremen", "role": "Villager", "age": 34},
                {"name": "Vilgrax Agras", "role": "Villager", "age": 42},
                {"name": "William Juleus", "role": "Villager", "age": 46},
                {"name": "Archi Mulam", "role": "Villager", "age": 44},
                {"name": "Fabr Jun", "role": "Villager", "age": 39},
                {"name": "Frobila", "role": "Pillager", "age": 30},
                {"name": "Gabriel", "role": "Pillager", "age": 32}
            ],
            "ministries": [
                {"name": "Alice Von Kiel", "position": "Minister of Economy", "age": 21},
                {"name": "Erick Frawn", "position": "Minister of Defense", "age": 46},
                {"name": "Erika Von Brasseum", "position": "Minister of Infrastructure and Design", "age": 37},
                {"name": "Mobel Grande", "position": "Minister of Health", "age": 52},
                {"name": "Klaus Tiran", "position": "Minister of Transportation", "age": 32},
                {"name": "Milim Vibanaus", "position": "Minister of Interior", "age": 60},
                {"name": "Wallius Faselleit", "position": "Minister of Foreign Affairs", "age": 58},
                {"name": "Rebellus Halm", "position": "Minister of Production and Revenue", "age": 43},
                {"name": "Jonathan Jobel", "position": "Minister of Measurement and Calculation", "age": 27},
                {"name": "Gramm Fajr", "position": "Minister of Guilds", "age": 41}
            ],
            "parties": []
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
        },
        "government": {
            "leader_type": "Party Leader and Emperor",
            "leader_name": "Meskop Von Brassenreich",
            "government_system": "National Democratic",
            "total_seats": 102,
            "council": [],
            "ministries": [],
            "parties": [
                {"name": "NSIP", "status": "Current ruling government", "leader_name": "Meskop Von Brassenreich", "leader_role": "Player", "leader_age": 21, "seats": 58},
                {"name": "SKNP", "status": "Active", "leader_name": "JewHunter", "leader_role": "Player", "leader_age": 26, "seats": 12},
                {"name": "TKNP", "status": "Active", "leader_name": "Alahamora", "leader_role": "Player", "leader_age": 22, "seats": 28},
                {"name": "PMNP", "status": "Active", "leader_name": "Fraudze", "leader_role": "Player", "leader_age": 21, "seats": 4}
            ]
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
        },
        "government": {
            "leader_type": "Sacred Leader",
            "leader_name": "wforestw",
            "government_system": "Socialism",
            "total_seats": 0,
            "council": [],
            "ministries": [],
            "parties": []
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
        },
        "government": {
            "leader_type": "Sacred Leader",
            "leader_name": "Muzlupankek",
            "government_system": "Populist Dictatorship",
            "total_seats": 0,
            "council": [],
            "ministries": [],
            "parties": []
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
        },
        "government": {
            "leader_type": "Prime Minister",
            "leader_name": "Egoslavin",
            "government_system": "Consular Monarchy",
            "total_seats": 0,
            "council": [
                {"name": "Meskop", "role": "player", "age": 20},
                {"name": "Egoslavin", "role": "player", "age": 18},
                {"name": "MiracLight20_09", "role": "player", "age": 18}
            ],
            "ministries": [
                {"name": "MiracLight20_09", "position": "Minister of Finance and Infrastructure", "age": 18}
            ],
            "parties": []
        }
    }
]

# New stocks to add
NEW_STOCKS = [
    # GRP Stocks
    {"symbol": "GRP-GERMANIA-GOV", "name": "GERMANIA GOVERNMENT", "currency": "GRP", "current_price": 351.19, "type": "stock"},
    {"symbol": "GRP-BOSO", "name": "Baweryen Organize Sanayi Odası BOSO", "currency": "GRP", "current_price": 195.73, "type": "stock"},
    {"symbol": "GRP-BAWERYAN", "name": "Baweryan City", "currency": "GRP", "current_price": 235.05, "type": "stock"},
    {"symbol": "GRP-GERMANIA-BANK", "name": "Germania Bankası", "currency": "GRP", "current_price": 200.74, "type": "stock"},
    {"symbol": "GRP-HAZINE", "name": "Germania Hazine Bonosu", "currency": "GRP", "current_price": 0.10, "type": "bond"},
    
    # NIM Stocks
    {"symbol": "NIM-GOV-NE", "name": "Government of NE", "currency": "NIM", "current_price": 241.49, "type": "stock"},
    {"symbol": "NIM-FALCO", "name": "Falco", "currency": "NIM", "current_price": 215.02, "type": "stock"},
    {"symbol": "NIM-BIGPORT", "name": "BIGPORT", "currency": "NIM", "current_price": 44.14, "type": "stock"},
    {"symbol": "NIM-DELTA", "name": "Delta Air Port", "currency": "NIM", "current_price": 22.03, "type": "stock"},
    {"symbol": "NIM-ANKARA", "name": "Ankara City", "currency": "NIM", "current_price": 5.57, "type": "stock"},
    {"symbol": "NIM-PORTMETRO", "name": "PortMetro", "currency": "NIM", "current_price": 2.18, "type": "stock"},
    {"symbol": "NIM-SAKURA", "name": "SakuraBank", "currency": "NIM", "current_price": 62.05, "type": "stock"},
    {"symbol": "NIM-ARDAX", "name": "ArdaX Builds", "currency": "NIM", "current_price": 14.12, "type": "stock"},
    {"symbol": "NIM-MBUILDS", "name": "Mbuilds", "currency": "NIM", "current_price": 22.21, "type": "stock"},
    {"symbol": "NIM-HAZINE", "name": "Nazi Imparatorluğu Hazine Bonosu", "currency": "NIM", "current_price": 0.10, "type": "bond"},
    {"symbol": "NIM-IMPERIAL-IND", "name": "Imperial Industry Office", "currency": "NIM", "current_price": 36.22, "type": "stock"},
    {"symbol": "NIM-IMPERIAL-TRADE", "name": "Imperial Trade Office", "currency": "NIM", "current_price": 2.55, "type": "stock"},
    
    # KKD Stocks
    {"symbol": "KKD-GOV-ERENIUM", "name": "GOVERMENT OF ERENIUM", "currency": "KKD", "current_price": 85.95, "type": "stock"},
    {"symbol": "KKD-CORDOBA", "name": "Cordoba", "currency": "KKD", "current_price": 183.56, "type": "stock"},
    {"symbol": "KKD-CORDOBA-BANK", "name": "Cordoba Bank", "currency": "KKD", "current_price": 23.70, "type": "stock"},
    {"symbol": "KKD-FBUILD", "name": "F-Build", "currency": "KKD", "current_price": 16.01, "type": "stock"},
    {"symbol": "KKD-HAZINE", "name": "Kayip Kredik Hazine Bonosu", "currency": "KKD", "current_price": 0.10, "type": "bond"},
    {"symbol": "KKD-IND-OFFICE", "name": "Lost Kingdom Industry Office", "currency": "KKD", "current_price": 23.55, "type": "stock"},
    {"symbol": "KKD-TRADE-OFFICE", "name": "Lost Kingdom Trade Office", "currency": "KKD", "current_price": 6.12, "type": "stock"},
    
    # VDD Stocks
    {"symbol": "VDD-BERLIN-GOV", "name": "Berlin Government", "currency": "VDD", "current_price": 105.95, "type": "stock"},
    {"symbol": "VDD-ELCIILIK", "name": "Elçilik", "currency": "VDD", "current_price": 3.41, "type": "stock"},
    {"symbol": "VDD-BERLINS", "name": "BerlinsBuilds", "currency": "VDD", "current_price": 7.42, "type": "stock"},
    {"symbol": "VDD-HAZINE", "name": "Berlin Konfederasyonu Hazine Bonosu", "currency": "VDD", "current_price": 0.10, "type": "bond"},
    {"symbol": "VDD-JOINT-BANK", "name": "Veltronia Joint Banking", "currency": "VDD", "current_price": 3.33, "type": "stock"},
    {"symbol": "VDD-TRADE-OFFICE", "name": "Veltronia Trade Office", "currency": "VDD", "current_price": 1.20, "type": "stock"},
    
    # EGD stocks
    {"symbol": "EGD-GOV", "name": "Egoslavia Government", "currency": "EGD", "current_price": 100.00, "type": "stock"},
    {"symbol": "EGD-MINISTRY", "name": "Egoslavia Ministry Office", "currency": "EGD", "current_price": 3.50, "type": "stock"},
    {"symbol": "EGD-SUMERBANK", "name": "SümerBank", "currency": "EGD", "current_price": 5.00, "type": "stock"},
    {"symbol": "EGD-MXBUILD", "name": "MX Build", "currency": "EGD", "current_price": 5.00, "type": "stock"},
    {"symbol": "EGD-EGBUILD", "name": "EG Build", "currency": "EGD", "current_price": 1.00, "type": "stock"},
    {"symbol": "EGD-HAZINE", "name": "Egoslavia Treasury Bond", "currency": "EGD", "current_price": 0.10, "type": "bond"}
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

# Country management models
class IncomeExpenseItem(BaseModel):
    name: str
    amount: float

class EconomicShare(BaseModel):
    bank_flow: float = 0
    trade: float = 0
    global_reserves: float = 0

class CountryCreate(BaseModel):
    id: str
    name: str
    currency: str
    independence_status: str = "independent country"
    treasury: float = 0
    color: str = "#9333ea"
    income: List[IncomeExpenseItem] = []
    expenses: List[IncomeExpenseItem] = []
    economic_share: EconomicShare = EconomicShare()

class CountryUpdate(BaseModel):
    name: Optional[str] = None
    currency: Optional[str] = None
    independence_status: Optional[str] = None
    treasury: Optional[float] = None
    color: Optional[str] = None

class CountryIncomeExpenseUpdate(BaseModel):
    country_id: str
    type: str  # "income" or "expenses"
    items: List[IncomeExpenseItem]

class CountryEconomicShareUpdate(BaseModel):
    country_id: str
    bank_flow: Optional[float] = None
    trade: Optional[float] = None
    global_reserves: Optional[float] = None

# Government & Leadership models
class CouncilMember(BaseModel):
    name: str
    role: str = ""  # e.g., "player", "MAI", "Merchant", "Monster", etc.
    age: int = 0

class Minister(BaseModel):
    name: str
    position: str  # e.g., "Minister of Economy"
    age: int = 0

class PoliticalParty(BaseModel):
    name: str
    status: str = "Active"  # "Current ruling government", "Active", "Inactive"
    leader_name: str = ""
    leader_role: str = ""  # e.g., "Player"
    leader_age: int = 0
    seats: int = 0  # Reichstag seats

class GovernmentInfo(BaseModel):
    leader_type: str = ""  # e.g., "Emperor", "Party Leader and Emperor", "Sacred Leader", "Prime Minister"
    leader_name: str = ""
    government_system: str = ""  # e.g., "Consular Monarchy", "National Democratic", "Socialism", etc.
    total_seats: int = 0  # For parliamentary systems
    council: List[CouncilMember] = []
    ministries: List[Minister] = []
    parties: List[PoliticalParty] = []

class GovernmentUpdate(BaseModel):
    leader_type: Optional[str] = None
    leader_name: Optional[str] = None
    government_system: Optional[str] = None
    total_seats: Optional[int] = None

class CouncilUpdate(BaseModel):
    council: List[CouncilMember]

class MinistriesUpdate(BaseModel):
    ministries: List[Minister]

class PartiesUpdate(BaseModel):
    parties: List[PoliticalParty]

# ============================================================================
# WORLD MAP MODELS
# ============================================================================

# World seed for Minecraft 1.21.1
WORLD_SEED = "8168667297865091855"

# State configurations with economic multipliers
MAP_STATES = {
    "germania": {"name": "Germania", "color": "#3A6EA5", "economic_multiplier": 1.0, "country_id": "germania"},
    "nazi_empire": {"name": "Nazi Empire", "color": "#8B0000", "economic_multiplier": 1.439, "country_id": "holy_empire"},
    "veltronia": {"name": "Veltronia Dominarex", "color": "#5A3D9A", "economic_multiplier": 2.386, "country_id": "veltronia"},
    "lost_kingdom": {"name": "Lost Kingdom", "color": "#C2A14D", "economic_multiplier": 2.269, "country_id": "lost_kingdom"},
    "egoslavia": {"name": "Egoslavia", "color": "#888888", "economic_multiplier": 1.2, "country_id": "egoslavia"}
}

# Ore prices per 100 block³
ORE_PRICES = {
    "lithium": {"name": "Lithium", "price": 506.5, "color": "#e879f9", "icon": "💎"},
    "iron": {"name": "Iron", "price": 10.0, "color": "#d4d4d4", "icon": "🔩"},
    "copper": {"name": "Copper", "price": 8.0, "color": "#f97316", "icon": "🟠"},
    "wood": {"name": "Wood (Odun)", "price": 0.1, "color": "#854d0e", "icon": "🪵"},
    "stone": {"name": "Stone", "price": 0.2, "color": "#71717a", "icon": "🪨"},
    "marble": {"name": "Marble", "price": 0.4, "color": "#f5f5f5", "icon": "⬜"},
    "building_stone": {"name": "Building Stones", "price": 0.4, "color": "#a1a1aa", "icon": "🧱"},
    "coal": {"name": "Coal", "price": 0.6, "color": "#27272a", "icon": "⚫"},
    "gold": {"name": "Gold", "price": 75.0, "color": "#fbbf24", "icon": "🥇"},
    "diamond": {"name": "Diamond", "price": 115.0, "color": "#22d3ee", "icon": "💠"},
    "uranium": {"name": "Uranium", "price": 17500.0, "color": "#22c55e", "icon": "☢️"},
    "plutonium": {"name": "Plutonium", "price": 95000.0, "color": "#a855f7", "icon": "⚛️"},
    "oil": {"name": "Oil", "price": 50.0, "color": "#18181b", "icon": "🛢️"}
}

# Marker types with emojis
MARKER_TYPES = {
    "city": {"name": "City", "icon": "🏠"},
    "capital": {"name": "Capital City", "icon": "⭐"},
    "army_camp": {"name": "Army Camp", "icon": "🛡️"},
    "port": {"name": "Port", "icon": "🚢"},
    "airport": {"name": "Airport", "icon": "✈️"},
    "battle": {"name": "War/Battle Area", "icon": "⚔️"},
    "village": {"name": "Village", "icon": "🏘️"},
    "temple": {"name": "Temple", "icon": "🏛️"},
    "stronghold": {"name": "Stronghold", "icon": "🏰"},
    "monument": {"name": "Ocean Monument", "icon": "🗿"},
    "mansion": {"name": "Woodland Mansion", "icon": "🏚️"},
    "outpost": {"name": "Pillager Outpost", "icon": "🗼"},
    "spawn": {"name": "World Spawn", "icon": "🌟"},
    "ore_deposit": {"name": "Ore Deposit", "icon": "⛏️"},
    "mine": {"name": "Mine", "icon": "⛏️"},
    "historical": {"name": "Historical Building", "icon": "🏛️"},
    "custom": {"name": "Custom", "icon": "📍"}
}

# Default territory data
DEFAULT_TERRITORIES = [
    {"state": "germania", "name": "Germania Mainland", "coordinates": [[1000, 1000], [5000, 1000], [5000, 5000], [1000, 5000]]},
    {"state": "nazi_empire", "name": "Nazi Empire Territory", "coordinates": [[5200, 1000], [9000, 1000], [9000, 5000], [5200, 5000]]},
    {"state": "veltronia", "name": "Veltronia Dominarex", "coordinates": [[1000, 5200], [5000, 5200], [5000, 9000], [1000, 9000]]},
    {"state": "lost_kingdom", "name": "Lost Kingdom Lands", "coordinates": [[5200, 5200], [9000, 5200], [9000, 9000], [5200, 9000]]},
    {"state": "egoslavia", "name": "Egoslavia Region", "coordinates": [[9500, 1000], [12000, 1000], [12000, 9000], [9500, 9000]]}
]

# Default markers
DEFAULT_MARKERS = [
    {"type": "capital", "name": "Germania Capital", "state": "germania", "coordinates": [3000, 3000]},
    {"type": "historical", "name": "Old Fortress", "state": "lost_kingdom", "coordinates": [6000, 6000]},
    {"type": "capital", "name": "Nazi Empire HQ", "state": "nazi_empire", "coordinates": [6000, 3000]},
    {"type": "capital", "name": "Veltronia Capital", "state": "veltronia", "coordinates": [3000, 6000]},
    {"type": "capital", "name": "Egoslavia Capital", "state": "egoslavia", "coordinates": [10000, 5000]}
]

# Default micro-regions with mineral data
DEFAULT_MICRO_REGIONS = [
    {
        "region_id": "GER-001",
        "state": "germania",
        "name": "Germania Central",
        "center": [2000, 2000],
        "area_km2": 1,
        "minerals": {
            "lithium": {"total": 100000, "available": 12000, "base_price": 506.5},
            "iron": {"total": 2000000, "available": 200000, "base_price": 10},
            "copper": {"total": 1200000, "available": 120000, "base_price": 8},
            "wood": {"total": 1600000, "available": 160000, "base_price": 0.1},
            "stone": {"total": 8020000, "available": 802000, "base_price": 0.2},
            "marble": {"total": 6700000, "available": 670000, "base_price": 0.4},
            "building_stone": {"total": 11000000, "available": 1100000, "base_price": 0.4},
            "coal": {"total": 15000000, "available": 1500000, "base_price": 0.6},
            "gold": {"total": 180000, "available": 18000, "base_price": 75},
            "diamond": {"total": 60000, "available": 6000, "base_price": 115},
            "uranium": {"total": 1800000, "available": 180000, "base_price": 17500},
            "plutonium": {"total": 70000, "available": 7000, "base_price": 95000},
            "oil": {"total": 1500000, "available": 150000, "base_price": 50}
        },
        "infrastructure_density": 0.7,
        "risk_factor": 1.05
    },
    {
        "region_id": "GER-002",
        "state": "germania",
        "name": "Germania East",
        "center": [4000, 3000],
        "area_km2": 1,
        "minerals": {
            "lithium": {"total": 90000, "available": 11000, "base_price": 506.5},
            "iron": {"total": 1800000, "available": 180000, "base_price": 10},
            "copper": {"total": 1100000, "available": 110000, "base_price": 8},
            "wood": {"total": 1500000, "available": 150000, "base_price": 0.1},
            "stone": {"total": 7500000, "available": 750000, "base_price": 0.2},
            "marble": {"total": 6000000, "available": 600000, "base_price": 0.4},
            "building_stone": {"total": 10000000, "available": 1000000, "base_price": 0.4},
            "coal": {"total": 14000000, "available": 1400000, "base_price": 0.6},
            "gold": {"total": 170000, "available": 17000, "base_price": 75},
            "diamond": {"total": 50000, "available": 5000, "base_price": 115},
            "uranium": {"total": 1700000, "available": 170000, "base_price": 17500},
            "plutonium": {"total": 60000, "available": 6000, "base_price": 95000},
            "oil": {"total": 1400000, "available": 140000, "base_price": 50}
        },
        "infrastructure_density": 0.65,
        "risk_factor": 1.05
    },
    {
        "region_id": "NAZ-001",
        "state": "nazi_empire",
        "name": "Nazi Empire Core",
        "center": [7000, 3000],
        "area_km2": 1,
        "minerals": {
            "lithium": {"total": 10000, "available": 1000, "base_price": 506.5},
            "iron": {"total": 1580000, "available": 158000, "base_price": 10},
            "copper": {"total": 2050000, "available": 205000, "base_price": 8},
            "wood": {"total": 7220000, "available": 722000, "base_price": 0.1},
            "stone": {"total": 2800000, "available": 280000, "base_price": 0.2},
            "marble": {"total": 700000, "available": 70000, "base_price": 0.4},
            "building_stone": {"total": 700000, "available": 70000, "base_price": 0.4},
            "coal": {"total": 9000000, "available": 900000, "base_price": 0.6},
            "gold": {"total": 130000, "available": 13000, "base_price": 75},
            "diamond": {"total": 37000, "available": 3700, "base_price": 115},
            "uranium": {"total": 10000000, "available": 1000000, "base_price": 17500},
            "plutonium": {"total": 9750, "available": 975, "base_price": 95000},
            "oil": {"total": 7900000, "available": 790000, "base_price": 50}
        },
        "infrastructure_density": 0.75,
        "risk_factor": 1.1
    },
    {
        "region_id": "VEL-001",
        "state": "veltronia",
        "name": "Veltronia Central",
        "center": [3000, 7000],
        "area_km2": 1,
        "minerals": {
            "lithium": {"total": 7500, "available": 750, "base_price": 506.5},
            "iron": {"total": 1966000, "available": 196600, "base_price": 10},
            "copper": {"total": 1705000, "available": 170500, "base_price": 8},
            "wood": {"total": 26000000, "available": 2600000, "base_price": 0.1},
            "stone": {"total": 22000000, "available": 2200000, "base_price": 0.2},
            "marble": {"total": 3200000, "available": 320000, "base_price": 0.4},
            "building_stone": {"total": 6240000, "available": 624000, "base_price": 0.4},
            "coal": {"total": 17000000, "available": 1700000, "base_price": 0.6},
            "gold": {"total": 111000, "available": 11100, "base_price": 75},
            "diamond": {"total": 21000, "available": 2100, "base_price": 115},
            "uranium": {"total": 190000, "available": 19000, "base_price": 17500},
            "plutonium": {"total": 9675, "available": 967, "base_price": 95000},
            "oil": {"total": 3790000, "available": 379000, "base_price": 50}
        },
        "infrastructure_density": 0.6,
        "risk_factor": 1.15
    },
    {
        "region_id": "LK-001",
        "state": "lost_kingdom",
        "name": "Lost Kingdom Heartland",
        "center": [7000, 7000],
        "area_km2": 1,
        "minerals": {
            "lithium": {"total": 4800, "available": 480, "base_price": 506.5},
            "iron": {"total": 800000, "available": 80000, "base_price": 10},
            "copper": {"total": 1270000, "available": 127000, "base_price": 8},
            "wood": {"total": 6000000, "available": 600000, "base_price": 0.1},
            "stone": {"total": 72000000, "available": 7200000, "base_price": 0.2},
            "marble": {"total": 98000000, "available": 9800000, "base_price": 0.4},
            "building_stone": {"total": 68000000, "available": 6800000, "base_price": 0.4},
            "coal": {"total": 58200000, "available": 5820000, "base_price": 0.6},
            "gold": {"total": 980000, "available": 98000, "base_price": 75},
            "diamond": {"total": 190000, "available": 19000, "base_price": 115},
            "uranium": {"total": 7530, "available": 753, "base_price": 17500},
            "plutonium": {"total": 3100, "available": 310, "base_price": 95000},
            "oil": {"total": 990000, "available": 99000, "base_price": 50}
        },
        "infrastructure_density": 0.55,
        "risk_factor": 1.2
    },
    {
        "region_id": "EGO-001",
        "state": "egoslavia",
        "name": "Egoslavia Main",
        "center": [10500, 5000],
        "area_km2": 1,
        "minerals": {
            "lithium": {"total": 50000, "available": 5000, "base_price": 506.5},
            "iron": {"total": 1000000, "available": 100000, "base_price": 10},
            "copper": {"total": 800000, "available": 80000, "base_price": 8},
            "wood": {"total": 2000000, "available": 200000, "base_price": 0.1},
            "stone": {"total": 5000000, "available": 500000, "base_price": 0.2},
            "marble": {"total": 3000000, "available": 300000, "base_price": 0.4},
            "building_stone": {"total": 4000000, "available": 400000, "base_price": 0.4},
            "coal": {"total": 8000000, "available": 800000, "base_price": 0.6},
            "gold": {"total": 100000, "available": 10000, "base_price": 75},
            "diamond": {"total": 30000, "available": 3000, "base_price": 115},
            "uranium": {"total": 500000, "available": 50000, "base_price": 17500},
            "plutonium": {"total": 20000, "available": 2000, "base_price": 95000},
            "oil": {"total": 1000000, "available": 100000, "base_price": 50}
        },
        "infrastructure_density": 0.5,
        "risk_factor": 1.1
    }
]

# Pydantic models for map
class MapCoordinate(BaseModel):
    x: int
    z: int

class TerritoryPolygon(BaseModel):
    points: List[MapCoordinate]  # List of x,z coordinates forming the polygon

class MapMarker(BaseModel):
    id: str = ""
    name: str
    marker_type: str  # Key from MARKER_TYPES
    x: int
    z: int
    description: Optional[str] = ""
    ore_type: Optional[str] = None  # For ore deposits
    ore_quantity: Optional[float] = None  # Blocks³ quantity

class Territory(BaseModel):
    id: str = ""
    name: str
    country_id: str  # Links to country
    color: str  # Hex color
    polygon: TerritoryPolygon
    markers: List[MapMarker] = []

class TerritoryCreate(BaseModel):
    name: str
    country_id: str
    color: str
    polygon: TerritoryPolygon

class TerritoryUpdate(BaseModel):
    name: Optional[str] = None
    country_id: Optional[str] = None
    color: Optional[str] = None
    polygon: Optional[TerritoryPolygon] = None

class MarkerCreate(BaseModel):
    name: str
    marker_type: str
    x: int
    z: int
    description: Optional[str] = ""
    ore_type: Optional[str] = None
    ore_quantity: Optional[float] = None

# Micro-region models
class MineralData(BaseModel):
    total: float
    available: float
    base_price: float

class MicroRegionCreate(BaseModel):
    region_id: str
    state: str
    name: str
    center: List[int]  # [x, z]
    area_km2: float = 1
    minerals: Dict[str, MineralData] = {}
    infrastructure_density: float = 0.5
    risk_factor: float = 1.0

class MicroRegionUpdate(BaseModel):
    name: Optional[str] = None
    minerals: Optional[Dict[str, Dict[str, float]]] = None
    infrastructure_density: Optional[float] = None
    risk_factor: Optional[float] = None

class OreUpdateRequest(BaseModel):
    ore_type: str
    total: Optional[float] = None
    available: Optional[float] = None
    base_price: Optional[float] = None

# ============================================================================
# BANKING SYSTEM CONFIGURATION
# ============================================================================

# All currencies in the system
CURRENCIES = ["GRP", "NIM", "VDD", "KKD", "EGD", "EP"]

# Bank configurations with home currency and card colors
BANKS = {
    "germania_bank": {
        "name": "Germania Bank",
        "home_currency": "GRP",
        "card_colors": {
            "credit": "#87CEEB",      # light blue
            "debit": "#0000FF",       # blue
            "government": "#000000",   # black
            "platinum": "#E5E4E2",    # platinum gray
            "gold": "#000000",        # black
            "investor": "#FFFFFF"      # white
        }
    },
    "sakura_bank": {
        "name": "Sakura Bank",
        "home_currency": "NIM",
        "card_colors": {
            "credit": "#FFB6C1",      # light red
            "debit": "#8B0000",       # dark red
            "government": "#000000",   # black
            "platinum": "#E5E4E2",    # platinum gray
            "gold": "#000000",        # black
            "investor": "#FFFFFF"      # white
        }
    },
    "veltronia_national_bank": {
        "name": "Veltronia National Bank",
        "home_currency": "VDD",
        "card_colors": {
            "credit": "#D2B48C",      # light brown
            "debit": "#8B4513",       # brown
            "government": "#000000",   # black
            "platinum": "#E5E4E2",    # platinum gray
            "gold": "#FFD700",        # yellow/gold
            "investor": "#FFFFFF"      # white
        }
    },
    "cordoba_bank": {
        "name": "Cordoba Bank",
        "home_currency": "KKD",
        "card_colors": {
            "credit": "#90EE90",      # light green
            "debit": "#228B22",       # green
            "government": "#000000",   # black
            "platinum": "#E5E4E2",    # platinum gray
            "gold": "#F4C430",        # saffron
            "investor": "#FFFFFF"      # white
        }
    },
    "sumerbank": {
        "name": "Sumerbank",
        "home_currency": "EGD",
        "card_colors": {
            "credit": "#DDA0DD",      # light purple
            "debit": "#800080",       # purple
            "government": "#000000",   # black
            "platinum": "#E5E4E2",    # platinum gray
            "gold": "#F4C430",        # saffron
            "investor": "#FFFFFF"      # white
        }
    }
}

# Card types
CARD_TYPES = ["credit", "debit", "government", "platinum", "gold", "investor"]

# Ranking colors for top 3
RANKING_COLORS = {
    "1": "#FFFF00",      # neon bright yellow
    "2": "#C0C0C0",      # neon bright light gray
    "3": "#B87333"       # neon bright copper
}

# Default sample accounts
DEFAULT_BANK_ACCOUNTS = [
    {
        "username": "bot1",
        "bank_accounts": [
            {
                "bank_id": "germania_bank",
                "cards": [
                    {
                        "card_type": "debit",
                        "balances": {"GRP": 500000, "NIM": 0, "VDD": 1000, "KKD": 0, "EGD": 0, "EP": 500},
                        "foreign_currencies_opened": ["VDD", "EP"]
                    },
                    {
                        "card_type": "credit",
                        "debt": {"GRP": 10000, "NIM": 0, "VDD": 0, "KKD": 0, "EGD": 0, "EP": 0}
                    }
                ]
            },
            {
                "bank_id": "sakura_bank",
                "cards": [
                    {
                        "card_type": "debit",
                        "balances": {"GRP": 0, "NIM": 250000, "VDD": 0, "KKD": 5000, "EGD": 0, "EP": 0},
                        "foreign_currencies_opened": ["GRP", "KKD"]
                    }
                ]
            }
        ]
    },
    {
        "username": "bot2",
        "bank_accounts": [
            {
                "bank_id": "cordoba_bank",
                "cards": [
                    {
                        "card_type": "debit",
                        "balances": {"GRP": 0, "NIM": 0, "VDD": 0, "KKD": 1000000, "EGD": 0, "EP": 0},
                        "foreign_currencies_opened": []
                    },
                    {
                        "card_type": "gold",
                        "balances": {"GRP": 100000, "NIM": 50000, "VDD": 0, "KKD": 200000, "EGD": 0, "EP": 10000},
                        "foreign_currencies_opened": ["GRP", "NIM", "EP"]
                    },
                    {
                        "card_type": "credit",
                        "debt": {"GRP": 0, "NIM": 5000, "VDD": 0, "KKD": 25000, "EGD": 0, "EP": 0}
                    }
                ]
            }
        ]
    },
    {
        "username": "bot3",
        "bank_accounts": [
            {
                "bank_id": "veltronia_national_bank",
                "cards": [
                    {
                        "card_type": "debit",
                        "balances": {"GRP": 0, "NIM": 0, "VDD": 750000, "KKD": 0, "EGD": 0, "EP": 0},
                        "foreign_currencies_opened": []
                    },
                    {
                        "card_type": "government",
                        "balances": {"GRP": 5000000, "NIM": 0, "VDD": 2000000, "KKD": 0, "EGD": 0, "EP": 0},
                        "foreign_currencies_opened": ["GRP"]
                    }
                ]
            },
            {
                "bank_id": "sumerbank",
                "cards": [
                    {
                        "card_type": "investor",
                        "balances": {"GRP": 0, "NIM": 0, "VDD": 0, "KKD": 0, "EGD": 100000, "EP": 50000},
                        "foreign_currencies_opened": ["EP"]
                    }
                ]
            }
        ]
    }
]

# Pydantic models for banking
class CardBalance(BaseModel):
    GRP: float = 0
    NIM: float = 0
    VDD: float = 0
    KKD: float = 0
    EGD: float = 0
    EP: float = 0

class CardCreate(BaseModel):
    card_type: str
    balances: Optional[Dict[str, float]] = None
    debt: Optional[Dict[str, float]] = None
    foreign_currencies_opened: List[str] = []

class CardUpdate(BaseModel):
    card_type: Optional[str] = None
    balances: Optional[Dict[str, float]] = None
    debt: Optional[Dict[str, float]] = None
    foreign_currencies_opened: Optional[List[str]] = None

class BankAccountCreate(BaseModel):
    bank_id: str
    cards: List[CardCreate] = []

class ServerAccountCreate(BaseModel):
    username: str
    bank_accounts: List[BankAccountCreate] = []

class ServerAccountUpdate(BaseModel):
    username: Optional[str] = None

class BalanceUpdateRequest(BaseModel):
    bank_id: str
    card_type: str
    currency: str
    amount: float
    operation: str = "set"  # set, add, subtract, reset

class ForeignCurrencyRequest(BaseModel):
    bank_id: str
    card_type: str
    currency: str
    open: bool  # True to open, False to close

class RankingColorsUpdate(BaseModel):
    rank_1: Optional[str] = None
    rank_2: Optional[str] = None
    rank_3: Optional[str] = None

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
    
    if user.get("server_code") != data.server_code:
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
        
        host_url = "https://world-map-helper.preview.emergentagent.com"
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


# ============================================================================
# COUNTRY MANAGEMENT ENDPOINTS
# ============================================================================

@api_router.get("/countries")
async def get_all_countries():
    """Get all countries with their data (public endpoint)"""
    countries = await db.countries.find({}, {"_id": 0}).to_list(100)
    
    # Calculate totals for each country
    for country in countries:
        total_income = sum(item.get("amount", 0) for item in country.get("income", []))
        total_expenses = sum(item.get("amount", 0) for item in country.get("expenses", []))
        country["total_income"] = total_income
        country["total_expenses"] = total_expenses
        country["weekly_net"] = total_income - total_expenses
    
    return {"countries": countries}

@api_router.get("/countries/{country_id}")
async def get_country(country_id: str):
    """Get a specific country's data"""
    country = await db.countries.find_one({"id": country_id}, {"_id": 0})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    total_income = sum(item.get("amount", 0) for item in country.get("income", []))
    total_expenses = sum(item.get("amount", 0) for item in country.get("expenses", []))
    country["total_income"] = total_income
    country["total_expenses"] = total_expenses
    country["weekly_net"] = total_income - total_expenses
    
    return country

@api_router.get("/countries/economic-shares/all")
async def get_all_economic_shares():
    """Get economic share data for all countries (for pie charts)"""
    countries = await db.countries.find({}, {"_id": 0, "id": 1, "name": 1, "color": 1, "economic_share": 1}).to_list(100)
    return {"countries": countries}

@api_router.post("/admin/countries")
async def create_country(data: CountryCreate, admin: dict = Depends(require_admin)):
    """Create a new country (admin only)"""
    existing = await db.countries.find_one({"id": data.id})
    if existing:
        raise HTTPException(status_code=400, detail="Country ID already exists")
    
    country_data = data.model_dump()
    country_data["created_at"] = datetime.now(timezone.utc).isoformat()
    country_data["last_treasury_update"] = datetime.now(timezone.utc).isoformat()
    country_data["treasury_history"] = []
    
    # Convert Pydantic models to dicts
    country_data["income"] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in country_data.get("income", [])]
    country_data["expenses"] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in country_data.get("expenses", [])]
    country_data["economic_share"] = country_data["economic_share"].model_dump() if hasattr(country_data["economic_share"], 'model_dump') else country_data["economic_share"]
    
    await db.countries.insert_one(country_data)
    
    await log_admin_action(
        admin["minecraft_username"],
        "Country created",
        f"{data.name} ({data.id}) - {data.currency}"
    )
    
    return {"message": "Country created successfully", "country_id": data.id}

@api_router.put("/admin/countries/{country_id}")
async def update_country(country_id: str, data: CountryUpdate, admin: dict = Depends(require_admin)):
    """Update country basic info (admin only)"""
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.countries.update_one(
        {"id": country_id},
        {"$set": update_data}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Country updated",
        f"{country_id}: {update_data}"
    )
    
    return {"message": "Country updated successfully"}

@api_router.put("/admin/countries/{country_id}/income-expenses")
async def update_country_income_expenses(country_id: str, data: CountryIncomeExpenseUpdate, admin: dict = Depends(require_admin)):
    """Update country income or expenses (admin only)"""
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    if data.type not in ["income", "expenses"]:
        raise HTTPException(status_code=400, detail="Type must be 'income' or 'expenses'")
    
    items = [item.model_dump() for item in data.items]
    
    await db.countries.update_one(
        {"id": country_id},
        {"$set": {data.type: items, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        f"Country {data.type} updated",
        f"{country_id}: {len(items)} items"
    )
    
    return {"message": f"Country {data.type} updated successfully"}

@api_router.post("/admin/countries/{country_id}/income-expenses/add")
async def add_income_expense_item(country_id: str, item_type: str, item: IncomeExpenseItem, admin: dict = Depends(require_admin)):
    """Add a new income or expense item to a country (admin only)"""
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    if item_type not in ["income", "expenses"]:
        raise HTTPException(status_code=400, detail="Type must be 'income' or 'expenses'")
    
    await db.countries.update_one(
        {"id": country_id},
        {
            "$push": {item_type: item.model_dump()},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        f"Added {item_type} item",
        f"{country_id}: {item.name} = {item.amount}"
    )
    
    return {"message": f"Added {item.name} to {item_type}"}

@api_router.put("/admin/countries/{country_id}/economic-share")
async def update_country_economic_share(country_id: str, data: CountryEconomicShareUpdate, admin: dict = Depends(require_admin)):
    """Update country economic share percentages (admin only)"""
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    current_share = country.get("economic_share", {})
    
    if data.bank_flow is not None:
        current_share["bank_flow"] = data.bank_flow
    if data.trade is not None:
        current_share["trade"] = data.trade
    if data.global_reserves is not None:
        current_share["global_reserves"] = data.global_reserves
    
    await db.countries.update_one(
        {"id": country_id},
        {"$set": {"economic_share": current_share, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Economic share updated",
        f"{country_id}: {current_share}"
    )
    
    return {"message": "Economic share updated successfully"}

@api_router.put("/admin/countries/{country_id}/color")
async def update_country_color(country_id: str, color: str, admin: dict = Depends(require_admin)):
    """Update country color for pie charts (admin only)"""
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    await db.countries.update_one(
        {"id": country_id},
        {"$set": {"color": color, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Country color updated",
        f"{country_id}: {color}"
    )
    
    return {"message": "Color updated successfully"}

@api_router.delete("/admin/countries/{country_id}")
async def delete_country(country_id: str, admin: dict = Depends(require_admin)):
    """Delete a country (admin only)"""
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    await db.countries.delete_one({"id": country_id})
    
    await log_admin_action(
        admin["minecraft_username"],
        "Country deleted",
        f"{country['name']} ({country_id})"
    )
    
    return {"message": "Country deleted successfully"}

@api_router.post("/admin/countries/treasury-update")
async def trigger_weekly_treasury_update(admin: dict = Depends(require_admin)):
    """Manually trigger weekly treasury update (admin only)"""
    result = await update_weekly_treasury()
    
    await log_admin_action(
        admin["minecraft_username"],
        "Treasury update triggered",
        result["message"]
    )
    
    return result

@api_router.get("/admin/countries/independence-statuses")
async def get_independence_statuses(admin: dict = Depends(require_admin)):
    """Get list of valid independence statuses"""
    return {"statuses": INDEPENDENCE_STATUSES}

@api_router.post("/admin/countries/initialize")
async def initialize_default_countries(admin: dict = Depends(require_admin)):
    """Initialize or reset countries to defaults (admin only)"""
    # Delete existing and re-insert
    await db.countries.delete_many({})
    
    for country_data in DEFAULT_COUNTRIES:
        country_copy = country_data.copy()
        country_copy["created_at"] = datetime.now(timezone.utc).isoformat()
        country_copy["last_treasury_update"] = datetime.now(timezone.utc).isoformat()
        country_copy["treasury_history"] = []
        await db.countries.insert_one(country_copy)
    
    await log_admin_action(
        admin["minecraft_username"],
        "Countries initialized",
        f"Created {len(DEFAULT_COUNTRIES)} default countries"
    )
    
    return {"message": f"Initialized {len(DEFAULT_COUNTRIES)} countries"}

@api_router.post("/admin/stocks/initialize-new")
async def initialize_new_stocks_endpoint(admin: dict = Depends(require_admin)):
    """Initialize new stocks (NIM, VDD, KKD, EGD) (admin only)"""
    added = 0
    for stock_data in NEW_STOCKS:
        existing = await db.investments.find_one({"symbol": stock_data["symbol"]})
        if not existing:
            stock = stock_data.copy()
            stock["id"] = str(uuid.uuid4())
            stock["created_at"] = datetime.now(timezone.utc).isoformat()
            stock["price_history"] = [{"timestamp": datetime.now(timezone.utc).isoformat(), "price": stock["current_price"]}]
            stock["disabled"] = False
            await db.investments.insert_one(stock)
            added += 1
    
    await log_admin_action(
        admin["minecraft_username"],
        "New stocks initialized",
        f"Added {added} new stocks"
    )
    
    return {"message": f"Added {added} new stocks", "total_new": len(NEW_STOCKS)}


# ============================================================================
# GOVERNMENT & LEADERSHIP ENDPOINTS
# ============================================================================

@api_router.get("/countries/{country_id}/government")
async def get_country_government(country_id: str):
    """Get government information for a specific country"""
    country = await db.countries.find_one({"id": country_id}, {"_id": 0})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    return {
        "country_id": country_id,
        "country_name": country.get("name"),
        "government": country.get("government", {
            "leader_type": "",
            "leader_name": "",
            "government_system": "",
            "total_seats": 0,
            "council": [],
            "ministries": [],
            "parties": []
        })
    }

@api_router.get("/countries/governments/all")
async def get_all_governments():
    """Get government information for all countries"""
    countries = await db.countries.find({}, {"_id": 0}).to_list(100)
    
    result = []
    for country in countries:
        result.append({
            "country_id": country.get("id"),
            "country_name": country.get("name"),
            "color": country.get("color"),
            "government": country.get("government", {
                "leader_type": "",
                "leader_name": "",
                "government_system": "",
                "total_seats": 0,
                "council": [],
                "ministries": [],
                "parties": []
            })
        })
    
    return {"countries": result}

@api_router.put("/admin/countries/{country_id}/government")
async def update_country_government(country_id: str, data: GovernmentUpdate, admin: dict = Depends(require_admin)):
    """Update government basic info (leader, system) for a country (admin only)"""
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    government = country.get("government", {})
    
    if data.leader_type is not None:
        government["leader_type"] = data.leader_type
    if data.leader_name is not None:
        government["leader_name"] = data.leader_name
    if data.government_system is not None:
        government["government_system"] = data.government_system
    if data.total_seats is not None:
        government["total_seats"] = data.total_seats
    
    await db.countries.update_one(
        {"id": country_id},
        {"$set": {"government": government, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Government updated",
        f"{country_id}: {data.model_dump(exclude_none=True)}"
    )
    
    return {"message": "Government info updated successfully"}

@api_router.put("/admin/countries/{country_id}/council")
async def update_country_council(country_id: str, data: CouncilUpdate, admin: dict = Depends(require_admin)):
    """Update council members for a country (admin only)"""
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    government = country.get("government", {})
    government["council"] = [member.model_dump() for member in data.council]
    
    await db.countries.update_one(
        {"id": country_id},
        {"$set": {"government": government, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Council updated",
        f"{country_id}: {len(data.council)} members"
    )
    
    return {"message": "Council updated successfully"}

@api_router.put("/admin/countries/{country_id}/ministries")
async def update_country_ministries(country_id: str, data: MinistriesUpdate, admin: dict = Depends(require_admin)):
    """Update ministries for a country (admin only)"""
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    government = country.get("government", {})
    government["ministries"] = [minister.model_dump() for minister in data.ministries]
    
    await db.countries.update_one(
        {"id": country_id},
        {"$set": {"government": government, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Ministries updated",
        f"{country_id}: {len(data.ministries)} ministries"
    )
    
    return {"message": "Ministries updated successfully"}

@api_router.put("/admin/countries/{country_id}/parties")
async def update_country_parties(country_id: str, data: PartiesUpdate, admin: dict = Depends(require_admin)):
    """Update political parties for a country (admin only)"""
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    government = country.get("government", {})
    government["parties"] = [party.model_dump() for party in data.parties]
    
    await db.countries.update_one(
        {"id": country_id},
        {"$set": {"government": government, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Parties updated",
        f"{country_id}: {len(data.parties)} parties"
    )
    
    return {"message": "Political parties updated successfully"}


# ============================================================================
# WORLD MAP ENDPOINTS
# ============================================================================

@api_router.get("/map/config")
async def get_map_config():
    """Get map configuration including seed, ore prices, marker types, and states"""
    return {
        "world_seed": WORLD_SEED,
        "ore_prices": ORE_PRICES,
        "marker_types": MARKER_TYPES,
        "states": MAP_STATES,
        "unit": "100_block3",
        "currency": "GRP"
    }

@api_router.get("/map/territories")
async def get_all_territories():
    """Get all territories with their markers"""
    territories = await db.territories.find({}, {"_id": 0}).to_list(1000)
    
    # Add country info to each territory
    for territory in territories:
        country = await db.countries.find_one({"id": territory.get("country_id")}, {"_id": 0, "name": 1, "color": 1})
        if country:
            territory["country_name"] = country.get("name")
            territory["country_color"] = country.get("color")
    
    return {"territories": territories}

@api_router.get("/map/territories/{territory_id}")
async def get_territory(territory_id: str):
    """Get a specific territory"""
    territory = await db.territories.find_one({"id": territory_id}, {"_id": 0})
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    return territory

@api_router.get("/map/markers")
async def get_all_markers():
    """Get all markers across all territories"""
    territories = await db.territories.find({}, {"_id": 0}).to_list(1000)
    
    all_markers = []
    for territory in territories:
        for marker in territory.get("markers", []):
            marker["territory_id"] = territory.get("id")
            marker["territory_name"] = territory.get("name")
            all_markers.append(marker)
    
    # Also get standalone markers (not in territories)
    standalone_markers = await db.map_markers.find({}, {"_id": 0}).to_list(1000)
    all_markers.extend(standalone_markers)
    
    return {"markers": all_markers}

@api_router.get("/map/countries-with-territories")
async def get_countries_with_territories():
    """Get all countries with their territories for the map"""
    countries = await db.countries.find({}, {"_id": 0, "id": 1, "name": 1, "color": 1}).to_list(100)
    territories = await db.territories.find({}, {"_id": 0}).to_list(1000)
    
    result = []
    for country in countries:
        country_territories = [t for t in territories if t.get("country_id") == country["id"]]
        result.append({
            "country_id": country["id"],
            "country_name": country["name"],
            "color": country["color"],
            "territories": country_territories
        })
    
    return {"countries": result}

@api_router.post("/admin/map/territories")
async def create_territory(data: TerritoryCreate, admin: dict = Depends(require_admin)):
    """Create a new territory (admin only)"""
    # Verify country exists
    country = await db.countries.find_one({"id": data.country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    territory_data = data.model_dump()
    territory_data["id"] = str(uuid.uuid4())
    territory_data["markers"] = []
    territory_data["created_at"] = datetime.now(timezone.utc).isoformat()
    
    # Convert polygon to dict
    territory_data["polygon"] = {
        "points": [{"x": p.x, "z": p.z} for p in data.polygon.points]
    }
    
    await db.territories.insert_one(territory_data)
    
    await log_admin_action(
        admin["minecraft_username"],
        "Territory created",
        f"{data.name} for {country['name']}"
    )
    
    return {"message": "Territory created", "territory_id": territory_data["id"]}

@api_router.put("/admin/map/territories/{territory_id}")
async def update_territory(territory_id: str, data: TerritoryUpdate, admin: dict = Depends(require_admin)):
    """Update a territory (admin only)"""
    territory = await db.territories.find_one({"id": territory_id})
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.country_id is not None:
        update_data["country_id"] = data.country_id
    if data.color is not None:
        update_data["color"] = data.color
    if data.polygon is not None:
        update_data["polygon"] = {
            "points": [{"x": p.x, "z": p.z} for p in data.polygon.points]
        }
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.territories.update_one(
        {"id": territory_id},
        {"$set": update_data}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Territory updated",
        f"{territory_id}"
    )
    
    return {"message": "Territory updated"}

@api_router.delete("/admin/map/territories/{territory_id}")
async def delete_territory(territory_id: str, admin: dict = Depends(require_admin)):
    """Delete a territory (admin only)"""
    territory = await db.territories.find_one({"id": territory_id})
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    await db.territories.delete_one({"id": territory_id})
    
    await log_admin_action(
        admin["minecraft_username"],
        "Territory deleted",
        f"{territory.get('name', territory_id)}"
    )
    
    return {"message": "Territory deleted"}

@api_router.post("/admin/map/territories/{territory_id}/markers")
async def add_marker_to_territory(territory_id: str, data: MarkerCreate, admin: dict = Depends(require_admin)):
    """Add a marker to a territory (admin only)"""
    territory = await db.territories.find_one({"id": territory_id})
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    marker_data = data.model_dump()
    marker_data["id"] = str(uuid.uuid4())
    
    await db.territories.update_one(
        {"id": territory_id},
        {"$push": {"markers": marker_data}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Marker added",
        f"{data.name} ({data.marker_type}) at {data.x}, {data.z}"
    )
    
    return {"message": "Marker added", "marker_id": marker_data["id"]}

@api_router.delete("/admin/map/territories/{territory_id}/markers/{marker_id}")
async def remove_marker_from_territory(territory_id: str, marker_id: str, admin: dict = Depends(require_admin)):
    """Remove a marker from a territory (admin only)"""
    territory = await db.territories.find_one({"id": territory_id})
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    await db.territories.update_one(
        {"id": territory_id},
        {"$pull": {"markers": {"id": marker_id}}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Marker removed",
        f"Marker {marker_id} from territory {territory_id}"
    )
    
    return {"message": "Marker removed"}

@api_router.post("/admin/map/markers")
async def create_standalone_marker(data: MarkerCreate, admin: dict = Depends(require_admin)):
    """Create a standalone marker not attached to any territory (admin only)"""
    marker_data = data.model_dump()
    marker_data["id"] = str(uuid.uuid4())
    marker_data["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.map_markers.insert_one(marker_data)
    
    await log_admin_action(
        admin["minecraft_username"],
        "Standalone marker created",
        f"{data.name} ({data.marker_type}) at {data.x}, {data.z}"
    )
    
    return {"message": "Marker created", "marker_id": marker_data["id"]}

@api_router.delete("/admin/map/markers/{marker_id}")
async def delete_standalone_marker(marker_id: str, admin: dict = Depends(require_admin)):
    """Delete a standalone marker (admin only)"""
    result = await db.map_markers.delete_one({"id": marker_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Marker not found")
    
    await log_admin_action(
        admin["minecraft_username"],
        "Standalone marker deleted",
        marker_id
    )
    
    return {"message": "Marker deleted"}

@api_router.get("/map/ore-deposits")
async def get_ore_deposits():
    """Get all ore deposit markers with their values"""
    territories = await db.territories.find({}, {"_id": 0}).to_list(1000)
    
    ore_deposits = []
    for territory in territories:
        for marker in territory.get("markers", []):
            if marker.get("ore_type") and marker.get("ore_quantity"):
                ore_info = ORE_PRICES.get(marker["ore_type"], {})
                deposit = {
                    **marker,
                    "territory_id": territory.get("id"),
                    "territory_name": territory.get("name"),
                    "ore_name": ore_info.get("name", marker["ore_type"]),
                    "ore_color": ore_info.get("color", "#888"),
                    "ore_icon": ore_info.get("icon", "⛏️"),
                    "price_per_100": ore_info.get("price", 0),
                    "total_value": ore_info.get("price", 0) * (marker.get("ore_quantity", 0) / 100)
                }
                ore_deposits.append(deposit)
    
    return {"ore_deposits": ore_deposits, "ore_prices": ORE_PRICES}

@api_router.get("/map/search")
async def search_map(query: str = "", x: Optional[int] = None, z: Optional[int] = None):
    """Search the map by name or coordinates"""
    results = []
    
    # Search territories by name
    if query:
        territories = await db.territories.find(
            {"$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"markers.name": {"$regex": query, "$options": "i"}}
            ]},
            {"_id": 0}
        ).to_list(100)
        
        for t in territories:
            results.append({
                "type": "territory",
                "id": t["id"],
                "name": t["name"],
                "polygon": t.get("polygon")
            })
            
            # Also add matching markers
            for m in t.get("markers", []):
                if query.lower() in m.get("name", "").lower():
                    results.append({
                        "type": "marker",
                        "id": m["id"],
                        "name": m["name"],
                        "marker_type": m.get("marker_type"),
                        "x": m["x"],
                        "z": m["z"]
                    })
    
    # Search by coordinates (find what's at/near this location)
    if x is not None and z is not None:
        territories = await db.territories.find({}, {"_id": 0}).to_list(1000)
        for t in territories:
            # Check if coordinate is within territory polygon (simple bounding box check)
            polygon = t.get("polygon", {}).get("points", [])
            if polygon:
                min_x = min(p["x"] for p in polygon)
                max_x = max(p["x"] for p in polygon)
                min_z = min(p["z"] for p in polygon)
                max_z = max(p["z"] for p in polygon)
                
                if min_x <= x <= max_x and min_z <= z <= max_z:
                    results.append({
                        "type": "territory",
                        "id": t["id"],
                        "name": t["name"],
                        "contains_point": True
                    })
            
            # Check markers near coordinates
            for m in t.get("markers", []):
                distance = ((m["x"] - x) ** 2 + (m["z"] - z) ** 2) ** 0.5
                if distance < 500:  # Within 500 blocks
                    results.append({
                        "type": "marker",
                        "id": m["id"],
                        "name": m["name"],
                        "marker_type": m.get("marker_type"),
                        "x": m["x"],
                        "z": m["z"],
                        "distance": round(distance)
                    })
    
    return {"results": results}


# ============================================================================
# MICRO-REGIONS AND MINERALS ENDPOINTS
# ============================================================================

@api_router.get("/map/micro-regions")
async def get_all_micro_regions():
    """Get all micro-regions with their mineral data"""
    regions = await db.micro_regions.find({}, {"_id": 0}).to_list(1000)
    
    # Calculate values with economic multipliers
    for region in regions:
        state = region.get("state")
        state_info = MAP_STATES.get(state, {"economic_multiplier": 1.0})
        multiplier = state_info.get("economic_multiplier", 1.0)
        
        total_value = 0
        available_value = 0
        
        for ore_type, mineral in region.get("minerals", {}).items():
            ore_info = ORE_PRICES.get(ore_type, {})
            base_price = mineral.get("base_price", ore_info.get("price", 0))
            adjusted_price = base_price * multiplier
            
            mineral["adjusted_price"] = adjusted_price
            mineral["total_value"] = (mineral.get("total", 0) / 100) * adjusted_price
            mineral["available_value"] = (mineral.get("available", 0) / 100) * adjusted_price
            mineral["availability_ratio"] = mineral.get("available", 0) / max(mineral.get("total", 1), 1)
            
            total_value += mineral["total_value"]
            available_value += mineral["available_value"]
        
        region["total_value_grp"] = total_value
        region["available_value_grp"] = available_value
        region["economic_multiplier"] = multiplier
        region["state_info"] = state_info
    
    return {"micro_regions": regions}

@api_router.get("/map/micro-regions/{region_id}")
async def get_micro_region(region_id: str):
    """Get a specific micro-region with detailed mineral data"""
    region = await db.micro_regions.find_one({"region_id": region_id}, {"_id": 0})
    if not region:
        raise HTTPException(status_code=404, detail="Micro-region not found")
    
    state = region.get("state")
    state_info = MAP_STATES.get(state, {"economic_multiplier": 1.0})
    multiplier = state_info.get("economic_multiplier", 1.0)
    
    mineral_details = []
    total_value = 0
    available_value = 0
    
    for ore_type, mineral in region.get("minerals", {}).items():
        ore_info = ORE_PRICES.get(ore_type, {})
        base_price = mineral.get("base_price", ore_info.get("price", 0))
        adjusted_price = base_price * multiplier
        
        detail = {
            "ore_type": ore_type,
            "name": ore_info.get("name", ore_type),
            "icon": ore_info.get("icon", "⛏️"),
            "color": ore_info.get("color", "#888"),
            "total": mineral.get("total", 0),
            "available": mineral.get("available", 0),
            "base_price": base_price,
            "adjusted_price": adjusted_price,
            "total_value_grp": (mineral.get("total", 0) / 100) * adjusted_price,
            "available_value_grp": (mineral.get("available", 0) / 100) * adjusted_price,
            "availability_ratio": mineral.get("available", 0) / max(mineral.get("total", 1), 1)
        }
        mineral_details.append(detail)
        total_value += detail["total_value_grp"]
        available_value += detail["available_value_grp"]
    
    # Sort by value
    mineral_details.sort(key=lambda x: x["available_value_grp"], reverse=True)
    
    return {
        **region,
        "mineral_details": mineral_details,
        "total_value_grp": total_value,
        "available_value_grp": available_value,
        "economic_multiplier": multiplier,
        "state_info": state_info
    }

@api_router.get("/map/distance")
async def calculate_distance(x1: int, z1: int, x2: int, z2: int):
    """Calculate distance between two points in blocks"""
    import math
    distance_blocks = math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)
    distance_km = distance_blocks / 1000  # 1000 blocks = 1 km in Minecraft RP
    
    return {
        "point1": {"x": x1, "z": z1},
        "point2": {"x": x2, "z": z2},
        "distance_blocks": round(distance_blocks, 2),
        "distance_km": round(distance_km, 3)
    }

@api_router.get("/map/states")
async def get_map_states():
    """Get all map states with their configurations"""
    return {"states": MAP_STATES}

@api_router.post("/admin/map/micro-regions")
async def create_micro_region(data: MicroRegionCreate, admin: dict = Depends(require_admin)):
    """Create a new micro-region (admin only)"""
    # Check if region_id already exists
    existing = await db.micro_regions.find_one({"region_id": data.region_id})
    if existing:
        raise HTTPException(status_code=400, detail="Region ID already exists")
    
    # Verify state exists
    if data.state not in MAP_STATES:
        raise HTTPException(status_code=400, detail=f"Invalid state. Valid states: {list(MAP_STATES.keys())}")
    
    region_data = data.model_dump()
    region_data["id"] = str(uuid.uuid4())
    region_data["created_at"] = datetime.now(timezone.utc).isoformat()
    
    # Convert minerals to proper format
    minerals_dict = {}
    for ore_type, mineral in region_data.get("minerals", {}).items():
        if hasattr(mineral, 'model_dump'):
            minerals_dict[ore_type] = mineral.model_dump()
        else:
            minerals_dict[ore_type] = mineral
    region_data["minerals"] = minerals_dict
    
    await db.micro_regions.insert_one(region_data)
    
    await log_admin_action(
        admin["minecraft_username"],
        "Micro-region created",
        f"{data.region_id} in {data.state}"
    )
    
    return {"message": "Micro-region created", "id": region_data["id"]}

@api_router.put("/admin/map/micro-regions/{region_id}")
async def update_micro_region(region_id: str, data: MicroRegionUpdate, admin: dict = Depends(require_admin)):
    """Update a micro-region (admin only)"""
    region = await db.micro_regions.find_one({"region_id": region_id})
    if not region:
        raise HTTPException(status_code=404, detail="Micro-region not found")
    
    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.infrastructure_density is not None:
        update_data["infrastructure_density"] = data.infrastructure_density
    if data.risk_factor is not None:
        update_data["risk_factor"] = data.risk_factor
    if data.minerals is not None:
        update_data["minerals"] = data.minerals
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.micro_regions.update_one(
        {"region_id": region_id},
        {"$set": update_data}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Micro-region updated",
        region_id
    )
    
    return {"message": "Micro-region updated"}

@api_router.put("/admin/map/micro-regions/{region_id}/ore")
async def update_micro_region_ore(region_id: str, data: OreUpdateRequest, admin: dict = Depends(require_admin)):
    """Update a specific ore in a micro-region (admin only)"""
    region = await db.micro_regions.find_one({"region_id": region_id})
    if not region:
        raise HTTPException(status_code=404, detail="Micro-region not found")
    
    minerals = region.get("minerals", {})
    ore = minerals.get(data.ore_type, {"total": 0, "available": 0, "base_price": 0})
    
    if data.total is not None:
        ore["total"] = data.total
    if data.available is not None:
        ore["available"] = data.available
    if data.base_price is not None:
        ore["base_price"] = data.base_price
    
    minerals[data.ore_type] = ore
    
    await db.micro_regions.update_one(
        {"region_id": region_id},
        {"$set": {"minerals": minerals, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Ore updated",
        f"{data.ore_type} in {region_id}"
    )
    
    return {"message": f"Ore {data.ore_type} updated in {region_id}"}

@api_router.delete("/admin/map/micro-regions/{region_id}")
async def delete_micro_region(region_id: str, admin: dict = Depends(require_admin)):
    """Delete a micro-region (admin only)"""
    result = await db.micro_regions.delete_one({"region_id": region_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Micro-region not found")
    
    await log_admin_action(
        admin["minecraft_username"],
        "Micro-region deleted",
        region_id
    )
    
    return {"message": "Micro-region deleted"}

@api_router.post("/admin/map/initialize-world-data")
async def initialize_world_data(admin: dict = Depends(require_admin)):
    """Initialize all world map data with default territories, markers, and micro-regions (admin only)"""
    initialized = {"territories": 0, "markers": 0, "micro_regions": 0}
    
    # Initialize territories
    for territory_data in DEFAULT_TERRITORIES:
        state = territory_data["state"]
        state_info = MAP_STATES.get(state, {})
        
        existing = await db.territories.find_one({"name": territory_data["name"]})
        if not existing:
            coords = territory_data["coordinates"]
            territory = {
                "id": str(uuid.uuid4()),
                "name": territory_data["name"],
                "country_id": state_info.get("country_id", state),
                "state": state,
                "color": state_info.get("color", "#888888"),
                "polygon": {
                    "points": [{"x": c[0], "z": c[1]} for c in coords]
                },
                "markers": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.territories.insert_one(territory)
            initialized["territories"] += 1
    
    # Initialize markers
    for marker_data in DEFAULT_MARKERS:
        existing = await db.map_markers.find_one({"name": marker_data["name"]})
        if not existing:
            marker = {
                "id": str(uuid.uuid4()),
                "name": marker_data["name"],
                "marker_type": marker_data["type"],
                "state": marker_data["state"],
                "x": marker_data["coordinates"][0],
                "z": marker_data["coordinates"][1],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.map_markers.insert_one(marker)
            initialized["markers"] += 1
    
    # Initialize micro-regions
    for region_data in DEFAULT_MICRO_REGIONS:
        existing = await db.micro_regions.find_one({"region_id": region_data["region_id"]})
        if not existing:
            region = {
                **region_data,
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.micro_regions.insert_one(region)
            initialized["micro_regions"] += 1
    
    await log_admin_action(
        admin["minecraft_username"],
        "World data initialized",
        f"Territories: {initialized['territories']}, Markers: {initialized['markers']}, Micro-regions: {initialized['micro_regions']}"
    )
    
    return {
        "message": "World data initialized",
        "initialized": initialized
    }

@api_router.put("/admin/map/ore-prices/{ore_type}")
async def update_ore_price(ore_type: str, price: float, admin: dict = Depends(require_admin)):
    """Update base price for an ore type (admin only) - affects all regions"""
    if ore_type not in ORE_PRICES:
        raise HTTPException(status_code=404, detail="Ore type not found")
    
    # Update in memory (temporary for this session)
    ORE_PRICES[ore_type]["price"] = price
    
    # Update in all micro-regions
    regions = await db.micro_regions.find({}).to_list(1000)
    updated_count = 0
    
    for region in regions:
        minerals = region.get("minerals", {})
        if ore_type in minerals:
            minerals[ore_type]["base_price"] = price
            await db.micro_regions.update_one(
                {"_id": region["_id"]},
                {"$set": {"minerals": minerals}}
            )
            updated_count += 1
    
    await log_admin_action(
        admin["minecraft_username"],
        "Ore price updated",
        f"{ore_type}: {price} GRP (updated in {updated_count} regions)"
    )
    
    return {"message": f"Ore price updated for {ore_type}", "new_price": price, "regions_updated": updated_count}


# ============================================================================
# SERVER BANK ACCOUNTS ENDPOINTS
# ============================================================================

def calculate_total_wealth(account: dict) -> float:
    """Calculate total wealth in GRP equivalent"""
    total = 0
    
    # These will be updated from DB if available
    exchange_rates = {
        "GRP": 1.0,
        "NIM": 0.62267,   # NIM_TO_GRP
        "VDD": 0.41909,   # VDD_TO_GRP
        "KKD": 0.43791,   # KKD_TO_GRP
        "EGD": 0.00847,   # EGD_TO_GRP
        "EP": 0.008888    # EP_TO_GRP
    }
    
    for bank_account in account.get("bank_accounts", []):
        for card in bank_account.get("cards", []):
            # Add balances (positive)
            balances = card.get("balances", {})
            for currency, amount in balances.items():
                if amount > 0:
                    total += amount * exchange_rates.get(currency, 0)
            
            # Subtract debt (negative)
            debt = card.get("debt", {})
            for currency, amount in debt.items():
                if amount > 0:
                    total -= amount * exchange_rates.get(currency, 0)
    
    return round(total, 2)

async def calculate_total_wealth_async(account: dict) -> float:
    """Calculate total wealth in GRP equivalent using DB exchange rates"""
    total = 0
    
    # Get exchange rates from database
    rates_doc = await db.exchange_rates.find_one({"id": "exchange_matrix"}, {"_id": 0})
    rates = rates_doc.get("rates", {}) if rates_doc else {}
    
    exchange_rates = {
        "GRP": 1.0,
        "NIM": rates.get("NIM_TO_GRP", 0.62267),
        "VDD": rates.get("VDD_TO_GRP", 0.41909),
        "KKD": rates.get("KKD_TO_GRP", 0.43791),
        "EGD": rates.get("EGD_TO_GRP", 0.00847),
        "EP": rates.get("EP_TO_GRP", 0.008888)
    }
    
    for bank_account in account.get("bank_accounts", []):
        for card in bank_account.get("cards", []):
            # Add balances (positive)
            balances = card.get("balances", {})
            for currency, amount in balances.items():
                if amount > 0:
                    total += amount * exchange_rates.get(currency, 0)
            
            # Subtract debt (negative)
            debt = card.get("debt", {})
            for currency, amount in debt.items():
                if amount > 0:
                    total -= amount * exchange_rates.get(currency, 0)
    
    return round(total, 2)

@api_router.get("/accounts/config")
async def get_accounts_config():
    """Get banking configuration"""
    # Get ranking colors from DB or use defaults
    config = await db.bank_config.find_one({"type": "ranking_colors"}, {"_id": 0})
    ranking_colors = config.get("colors", RANKING_COLORS) if config else RANKING_COLORS
    
    return {
        "banks": BANKS,
        "card_types": CARD_TYPES,
        "currencies": CURRENCIES,
        "ranking_colors": ranking_colors
    }

@api_router.get("/accounts")
async def get_all_accounts():
    """Get all server accounts with wealth ranking"""
    accounts = await db.server_accounts.find({}, {"_id": 0}).to_list(1000)
    
    # Calculate wealth for each account
    for account in accounts:
        account["total_wealth"] = calculate_total_wealth(account)
    
    # Sort by wealth (descending)
    accounts.sort(key=lambda x: x.get("total_wealth", 0), reverse=True)
    
    # Add rank
    for i, account in enumerate(accounts):
        account["rank"] = i + 1
    
    return {"accounts": accounts, "total_count": len(accounts)}

@api_router.get("/accounts/{account_id}")
async def get_account(account_id: str):
    """Get specific account details"""
    account = await db.server_accounts.find_one({"id": account_id}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account["total_wealth"] = calculate_total_wealth(account)
    return account

@api_router.get("/accounts/by-username/{username}")
async def get_account_by_username(username: str):
    """Get account by username"""
    account = await db.server_accounts.find_one(
        {"username": {"$regex": f"^{username}$", "$options": "i"}}, 
        {"_id": 0}
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account["total_wealth"] = calculate_total_wealth(account)
    return account

@api_router.post("/admin/accounts")
async def create_account(data: ServerAccountCreate, admin: dict = Depends(require_admin)):
    """Create a new server account (admin only)"""
    # Check if username exists
    existing = await db.server_accounts.find_one(
        {"username": {"$regex": f"^{data.username}$", "$options": "i"}}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    account_data = {
        "id": str(uuid.uuid4()),
        "username": data.username,
        "bank_accounts": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Process bank accounts
    for bank_acc in data.bank_accounts:
        if bank_acc.bank_id not in BANKS:
            raise HTTPException(status_code=400, detail=f"Invalid bank: {bank_acc.bank_id}")
        
        bank_data = {
            "bank_id": bank_acc.bank_id,
            "cards": []
        }
        
        for card in bank_acc.cards:
            if card.card_type not in CARD_TYPES:
                raise HTTPException(status_code=400, detail=f"Invalid card type: {card.card_type}")
            
            card_data = {
                "id": str(uuid.uuid4()),
                "card_type": card.card_type,
                "balances": card.balances or {c: 0 for c in CURRENCIES},
                "debt": card.debt or {c: 0 for c in CURRENCIES},
                "foreign_currencies_opened": card.foreign_currencies_opened or []
            }
            bank_data["cards"].append(card_data)
        
        account_data["bank_accounts"].append(bank_data)
    
    await db.server_accounts.insert_one(account_data)
    
    await log_admin_action(
        admin["minecraft_username"],
        "Account created",
        data.username
    )
    
    return {"message": "Account created", "id": account_data["id"]}

@api_router.put("/admin/accounts/{account_id}")
async def update_account(account_id: str, data: ServerAccountUpdate, admin: dict = Depends(require_admin)):
    """Update account basic info (admin only)"""
    account = await db.server_accounts.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.username is not None:
        # Check if new username exists
        existing = await db.server_accounts.find_one({
            "username": {"$regex": f"^{data.username}$", "$options": "i"},
            "id": {"$ne": account_id}
        })
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        update_data["username"] = data.username
    
    await db.server_accounts.update_one({"id": account_id}, {"$set": update_data})
    
    await log_admin_action(
        admin["minecraft_username"],
        "Account updated",
        f"{account['username']} -> {data.model_dump(exclude_none=True)}"
    )
    
    return {"message": "Account updated"}

@api_router.delete("/admin/accounts/{account_id}")
async def delete_account(account_id: str, admin: dict = Depends(require_admin)):
    """Delete an account (admin only)"""
    account = await db.server_accounts.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    await db.server_accounts.delete_one({"id": account_id})
    
    await log_admin_action(
        admin["minecraft_username"],
        "Account deleted",
        account["username"]
    )
    
    return {"message": "Account deleted"}

@api_router.post("/admin/accounts/{account_id}/bank")
async def add_bank_to_account(account_id: str, data: BankAccountCreate, admin: dict = Depends(require_admin)):
    """Add a bank account to user (admin only)"""
    account = await db.server_accounts.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if data.bank_id not in BANKS:
        raise HTTPException(status_code=400, detail=f"Invalid bank: {data.bank_id}")
    
    # Check if user already has this bank
    existing_banks = [ba["bank_id"] for ba in account.get("bank_accounts", [])]
    if data.bank_id in existing_banks:
        raise HTTPException(status_code=400, detail="User already has account at this bank")
    
    bank_data = {
        "bank_id": data.bank_id,
        "cards": []
    }
    
    for card in data.cards:
        if card.card_type not in CARD_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid card type: {card.card_type}")
        
        card_data = {
            "id": str(uuid.uuid4()),
            "card_type": card.card_type,
            "balances": card.balances or {c: 0 for c in CURRENCIES},
            "debt": card.debt or {c: 0 for c in CURRENCIES},
            "foreign_currencies_opened": card.foreign_currencies_opened or []
        }
        bank_data["cards"].append(card_data)
    
    await db.server_accounts.update_one(
        {"id": account_id},
        {"$push": {"bank_accounts": bank_data}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Bank added to account",
        f"{account['username']}: {BANKS[data.bank_id]['name']}"
    )
    
    return {"message": "Bank account added"}

@api_router.delete("/admin/accounts/{account_id}/bank/{bank_id}")
async def remove_bank_from_account(account_id: str, bank_id: str, admin: dict = Depends(require_admin)):
    """Remove a bank from user account (admin only)"""
    account = await db.server_accounts.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    await db.server_accounts.update_one(
        {"id": account_id},
        {"$pull": {"bank_accounts": {"bank_id": bank_id}}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Bank removed from account",
        f"{account['username']}: {bank_id}"
    )
    
    return {"message": "Bank account removed"}

@api_router.post("/admin/accounts/{account_id}/card")
async def add_card_to_account(account_id: str, bank_id: str, data: CardCreate, admin: dict = Depends(require_admin)):
    """Add a card to user's bank account (admin only)"""
    account = await db.server_accounts.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if data.card_type not in CARD_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid card type: {data.card_type}")
    
    # Find bank account
    bank_idx = None
    for i, ba in enumerate(account.get("bank_accounts", [])):
        if ba["bank_id"] == bank_id:
            bank_idx = i
            break
    
    if bank_idx is None:
        raise HTTPException(status_code=404, detail="User doesn't have account at this bank")
    
    card_data = {
        "id": str(uuid.uuid4()),
        "card_type": data.card_type,
        "balances": data.balances or {c: 0 for c in CURRENCIES},
        "debt": data.debt or {c: 0 for c in CURRENCIES},
        "foreign_currencies_opened": data.foreign_currencies_opened or []
    }
    
    await db.server_accounts.update_one(
        {"id": account_id},
        {"$push": {f"bank_accounts.{bank_idx}.cards": card_data}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Card added to account",
        f"{account['username']}: {data.card_type} at {bank_id}"
    )
    
    return {"message": "Card added", "card_id": card_data["id"]}

@api_router.delete("/admin/accounts/{account_id}/card/{bank_id}/{card_id}")
async def remove_card_from_account(account_id: str, bank_id: str, card_id: str, admin: dict = Depends(require_admin)):
    """Remove a card from user's bank account (admin only)"""
    account = await db.server_accounts.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Find bank account index
    bank_idx = None
    for i, ba in enumerate(account.get("bank_accounts", [])):
        if ba["bank_id"] == bank_id:
            bank_idx = i
            break
    
    if bank_idx is None:
        raise HTTPException(status_code=404, detail="User doesn't have account at this bank")
    
    await db.server_accounts.update_one(
        {"id": account_id},
        {"$pull": {f"bank_accounts.{bank_idx}.cards": {"id": card_id}}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Card removed from account",
        f"{account['username']}: {card_id} at {bank_id}"
    )
    
    return {"message": "Card removed"}

@api_router.put("/admin/accounts/{account_id}/balance")
async def update_card_balance(account_id: str, data: BalanceUpdateRequest, admin: dict = Depends(require_admin)):
    """Update balance on a specific card (admin only)"""
    account = await db.server_accounts.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if data.currency not in CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Invalid currency: {data.currency}")
    
    # Find bank and card
    bank_idx = None
    card_idx = None
    
    for i, ba in enumerate(account.get("bank_accounts", [])):
        if ba["bank_id"] == data.bank_id:
            bank_idx = i
            for j, card in enumerate(ba.get("cards", [])):
                if card["card_type"] == data.card_type:
                    card_idx = j
                    break
            break
    
    if bank_idx is None or card_idx is None:
        raise HTTPException(status_code=404, detail="Card not found")
    
    card = account["bank_accounts"][bank_idx]["cards"][card_idx]
    
    # Determine if updating balance or debt
    is_credit = data.card_type == "credit"
    field = "debt" if is_credit else "balances"
    
    current_value = card.get(field, {}).get(data.currency, 0)
    
    if data.operation == "set":
        new_value = data.amount
    elif data.operation == "add":
        new_value = current_value + data.amount
    elif data.operation == "subtract":
        new_value = current_value - data.amount
    elif data.operation == "reset":
        new_value = 0
    else:
        raise HTTPException(status_code=400, detail=f"Invalid operation: {data.operation}")
    
    # Don't allow negative balance (except for credit which tracks debt)
    if not is_credit and new_value < 0:
        new_value = 0
    
    await db.server_accounts.update_one(
        {"id": account_id},
        {"$set": {f"bank_accounts.{bank_idx}.cards.{card_idx}.{field}.{data.currency}": new_value}}
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Balance updated",
        f"{account['username']}: {data.card_type} at {data.bank_id} - {data.currency} {data.operation} {data.amount} -> {new_value}"
    )
    
    return {"message": "Balance updated", "new_value": new_value}

@api_router.put("/admin/accounts/{account_id}/foreign-currency")
async def toggle_foreign_currency(account_id: str, data: ForeignCurrencyRequest, admin: dict = Depends(require_admin)):
    """Open or close foreign currency account on a card (admin only)"""
    account = await db.server_accounts.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if data.currency not in CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Invalid currency: {data.currency}")
    
    # Find bank and card
    bank_idx = None
    card_idx = None
    
    for i, ba in enumerate(account.get("bank_accounts", [])):
        if ba["bank_id"] == data.bank_id:
            bank_idx = i
            for j, card in enumerate(ba.get("cards", [])):
                if card["card_type"] == data.card_type:
                    card_idx = j
                    break
            break
    
    if bank_idx is None or card_idx is None:
        raise HTTPException(status_code=404, detail="Card not found")
    
    card = account["bank_accounts"][bank_idx]["cards"][card_idx]
    current_opened = card.get("foreign_currencies_opened", [])
    
    if data.open:
        if data.currency not in current_opened:
            current_opened.append(data.currency)
    else:
        if data.currency in current_opened:
            current_opened.remove(data.currency)
    
    await db.server_accounts.update_one(
        {"id": account_id},
        {"$set": {f"bank_accounts.{bank_idx}.cards.{card_idx}.foreign_currencies_opened": current_opened}}
    )
    
    action = "opened" if data.open else "closed"
    await log_admin_action(
        admin["minecraft_username"],
        f"Foreign currency {action}",
        f"{account['username']}: {data.currency} on {data.card_type} at {data.bank_id}"
    )
    
    return {"message": f"Foreign currency account {action}"}

@api_router.put("/admin/accounts/config/ranking-colors")
async def update_ranking_colors(data: RankingColorsUpdate, admin: dict = Depends(require_admin)):
    """Update ranking colors for top 3 (admin only)"""
    colors = {}
    if data.rank_1:
        colors["1"] = data.rank_1
    if data.rank_2:
        colors["2"] = data.rank_2
    if data.rank_3:
        colors["3"] = data.rank_3
    
    await db.bank_config.update_one(
        {"type": "ranking_colors"},
        {"$set": {"colors": {**RANKING_COLORS, **colors}}},
        upsert=True
    )
    
    await log_admin_action(
        admin["minecraft_username"],
        "Ranking colors updated",
        str(colors)
    )
    
    return {"message": "Ranking colors updated"}

@api_router.post("/admin/accounts/initialize")
async def initialize_sample_accounts(admin: dict = Depends(require_admin)):
    """Initialize sample accounts for testing (admin only)"""
    initialized = 0
    
    for account_data in DEFAULT_BANK_ACCOUNTS:
        existing = await db.server_accounts.find_one(
            {"username": {"$regex": f"^{account_data['username']}$", "$options": "i"}}
        )
        if not existing:
            # Process bank accounts and add IDs to cards
            processed_accounts = []
            for bank_acc in account_data["bank_accounts"]:
                processed_bank = {
                    "bank_id": bank_acc["bank_id"],
                    "cards": []
                }
                for card in bank_acc["cards"]:
                    processed_card = {
                        "id": str(uuid.uuid4()),
                        "card_type": card["card_type"],
                        "balances": card.get("balances", {c: 0 for c in CURRENCIES}),
                        "debt": card.get("debt", {c: 0 for c in CURRENCIES}),
                        "foreign_currencies_opened": card.get("foreign_currencies_opened", [])
                    }
                    processed_bank["cards"].append(processed_card)
                processed_accounts.append(processed_bank)
            
            new_account = {
                "id": str(uuid.uuid4()),
                "username": account_data["username"],
                "bank_accounts": processed_accounts,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.server_accounts.insert_one(new_account)
            initialized += 1
    
    await log_admin_action(
        admin["minecraft_username"],
        "Sample accounts initialized",
        f"{initialized} accounts created"
    )
    
    return {"message": f"Initialized {initialized} sample accounts"}


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

async def weekly_treasury_scheduler():
    """Background task to update treasury weekly"""
    while True:
        # Wait for 1 week (604800 seconds)
        await asyncio.sleep(604800)
        try:
            result = await update_weekly_treasury()
            logger.info(f"Weekly treasury update: {result['message']}")
        except Exception as e:
            logger.error(f"Weekly treasury update failed: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await initialize_exchange_matrix()
    await initialize_currencies()
    await initialize_countries()
    await initialize_new_stocks()
    
    # Start weekly treasury scheduler in background
    asyncio.create_task(weekly_treasury_scheduler())
    
    logger.info("Database initialized with currencies, exchange rates, countries, and stocks")
    logger.info("Weekly treasury scheduler started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
