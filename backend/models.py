from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid

# Exchange Rate Matrix - Every currency to every other
DEFAULT_EXCHANGE_MATRIX = {
    "NIM_TO_GRP": 0.592,
    "NIM_TO_VDD": 1.403,
    "NIM_TO_KKD": 1.549,
    "VDD_TO_GRP": 0.422,
    "VDD_TO_NIM": 0.713,
    "VDD_TO_KKD": 1.104,
    "KKD_TO_GRP": 0.382,
    "KKD_TO_NIM": 0.645,
    "KKD_TO_VDD": 0.905,
    "GRP_TO_NIM": 1.687,
    "GRP_TO_VDD": 2.366,
    "GRP_TO_KKD": 2.614,
    "GRP_TO_USD": 0.000245
}

# House/Building Types
BUILDING_TYPES = [
    "House",
    "Floor",
    "Complex",
    "Apartment",
    "Business",
    "Industrial",
    "Factory",
    "Park",
    "Agricultural Land",
    "Zoned Area"
]

# Banks
BANKS = [
    "Bank of Cordoba (Lost Kingdom)",
    "Sakura Bank (Holy Empire)",
    "Bank of Germania (Federal Empire of Germania)",
    "VDD Ansbund Joint Banking"
]

# Investment Stocks
INVESTMENTS = {
    "NIM": [
        {"name": "Government of N.E.", "symbol": "GOV_NE", "price": 220.00},
        {"name": "Falco", "symbol": "FALCO", "price": 215.50},
        {"name": "BIGport", "symbol": "BIGPORT", "price": 46.85},
        {"name": "Delta AirPort", "symbol": "DELTA_AP", "price": 22.77},
        {"name": "Ankara City", "symbol": "ANKARA", "price": 6.90},
        {"name": "PortMetro", "symbol": "PORTMETRO", "price": 2.62},
        {"name": "SakuraBank", "symbol": "SAKURA_BANK", "price": 28.60},
        {"name": "ArdaX Builds", "symbol": "ARDAX", "price": 16.85},
        {"name": "Mbuilds", "symbol": "MBUILDS", "price": 11.40},
        {"name": "Holy Imperial Treasury Bond", "symbol": "HOLY_BOND", "price": 0.10}
    ],
    "VDD": [
        {"name": "Berlin Government", "symbol": "BERLIN_GOV", "price": 139.92},
        {"name": "Embassy", "symbol": "EMBASSY", "price": 2.88},
        {"name": "BerlinsBuilds", "symbol": "BERLIN_BUILD", "price": 7.05},
        {"name": "Berlin Confederation Treasury Bond", "symbol": "BERLIN_BOND", "price": 0.10}
    ],
    "GRP": [
        {"name": "GERMANIA GOVERNMENT", "symbol": "GERMANIA_GOV", "price": 368.35},
        {"name": "Baweryan Organized Industrial Chamber BOSO", "symbol": "BOSO", "price": 192.50},
        {"name": "Baweryan City", "symbol": "BAWERYA", "price": 241.00},
        {"name": "Germania Bank", "symbol": "GERMANIA_BANK", "price": 200.00},
        {"name": "Germania Empire Treasury Bond", "symbol": "GERMANIA_BOND", "price": 0.10}
    ],
    "KKD": [
        {"name": "GOVERNMENT OF ERENIUM", "symbol": "ERENIUM_GOV", "price": 86.00},
        {"name": "Cordoba", "symbol": "CORDOBA", "price": 175.00},
        {"name": "Cordoba Bank", "symbol": "CORDOBA_BANK", "price": 18.50},
        {"name": "F-Build", "symbol": "F_BUILD", "price": 8.50},
        {"name": "Lost Kingdom Treasury Bond", "symbol": "LOST_BOND", "price": 0.10}
    ]
}

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
    portfolio: Dict[str, float] = Field(default_factory=dict)  # stock_symbol: quantity
    total_spent: float = 0.0
    total_transactions: int = 0
    is_admin: bool = False
    selected_bank: Optional[str] = None
    hide_balance: bool = False
    can_use_real_money: bool = False
    created_at: str

class House(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    location: str
    building_type: str = "House"  # House, Apartment, Factory, etc.
    price_currency: str = "NIM"  # Base currency for pricing
    price_amount: float = 0.0
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
    building_type: str
    owner_id: str
    owner_username: str
    previous_owner_id: Optional[str] = None
    previous_owner_username: Optional[str] = None
    purchase_price: float
    purchase_currency: str
    issued_date: str
    location: str

class Investment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    symbol: str
    name: str
    currency: str  # NIM, GRP, VDD, KKD
    current_price: float
    price_history: List[Dict] = Field(default_factory=list)  # [{timestamp, price}]
    last_updated: str

class InvestmentTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    username: str
    symbol: str
    transaction_type: str  # buy, sell, transfer
    quantity: float
    price_per_unit: float
    total_amount: float
    commission: float
    currency: str
    timestamp: str
    recipient_id: Optional[str] = None
    recipient_username: Optional[str] = None

class MoneyTransfer(BaseModel):
    sender_id: str
    recipient_username: str
    amount: float
    currency: str

class HouseSwap(BaseModel):
    my_house_id: str
    their_house_id: str
    their_username: str
