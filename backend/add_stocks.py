#!/usr/bin/env python3
"""
Script to add new stocks to the Germania Empire Marketplace
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

# New stocks data
STOCKS = [
    # VDD Stocks
    {"symbol": "VDD-BERLIN-GOV", "name": "Berlin Goverment", "currency": "VDD", "current_price": 139.92},
    {"symbol": "VDD-ELCILIK", "name": "Elçilik", "currency": "VDD", "current_price": 2.88},
    {"symbol": "VDD-BERLINS", "name": "BerlinsBuilds", "currency": "VDD", "current_price": 7.05},
    {"symbol": "VDD-HAZINE", "name": "Berlin Konfederasyonu Hazine Bonosu", "currency": "VDD", "current_price": 0.10},
    
    # NIM Stocks
    {"symbol": "NIM-GOV-NE", "name": "Goverment of NE", "currency": "NIM", "current_price": 220.00},
    {"symbol": "NIM-FALCO", "name": "Falco", "currency": "NIM", "current_price": 215.50},
    {"symbol": "NIM-BIGPORT", "name": "BİGport", "currency": "NIM", "current_price": 46.85},
    {"symbol": "NIM-DELTA", "name": "Delta AirPort", "currency": "NIM", "current_price": 22.77},
    {"symbol": "NIM-ANKARA", "name": "Ankara City", "currency": "NIM", "current_price": 6.90},
    {"symbol": "NIM-PORTMETRO", "name": "PortMetro", "currency": "NIM", "current_price": 2.62},
    {"symbol": "NIM-SAKURA", "name": "SakuraBank", "currency": "NIM", "current_price": 28.60},
    {"symbol": "NIM-ARDAX", "name": "ArdaX Builds", "currency": "NIM", "current_price": 16.85},
    {"symbol": "NIM-MBUILDS", "name": "Mbuilds", "currency": "NIM", "current_price": 11.40},
    {"symbol": "NIM-HAZINE", "name": "Nazi İmparatorluğu Hazine Bonosu", "currency": "NIM", "current_price": 0.10},
    
    # KKD Stocks
    {"symbol": "KKD-GOV-ERENIUM", "name": "GOVERMENT OF ERENIUM", "currency": "KKD", "current_price": 86.00},
    {"symbol": "KKD-CORDOBA", "name": "Cordoba", "currency": "KKD", "current_price": 175.00},
    {"symbol": "KKD-CORDOBA-BANK", "name": "Cordoba Bank", "currency": "KKD", "current_price": 18.50},
    {"symbol": "KKD-FBUILD", "name": "F-Build", "currency": "KKD", "current_price": 8.50},
    {"symbol": "KKD-HAZINE", "name": "Kayıp Krallık Hazine Bonosu", "currency": "KKD", "current_price": 0.10},
    
    # GRP Stocks
    {"symbol": "GRP-GERMANIA-GOV", "name": "GERMANIA GOVERMENT", "currency": "GRP", "current_price": 368.35},
    {"symbol": "GRP-BOSO", "name": "Baweryan Organize Sanayi Odası BOSO", "currency": "GRP", "current_price": 192.50},
    {"symbol": "GRP-BAWERYAN", "name": "Baweryan City", "currency": "GRP", "current_price": 241.00},
    {"symbol": "GRP-GERMANIA-BANK", "name": "Germania Bankası", "currency": "GRP", "current_price": 200.00},
    {"symbol": "GRP-HAZINE", "name": "Germanıa Empıre Hazine Bonosu", "currency": "GRP", "current_price": 0.10},
]

async def add_stocks():
    """Add stocks to database"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🚀 Adding stocks to database...")
    print(f"Total stocks to add: {len(STOCKS)}\n")
    
    added_count = 0
    updated_count = 0
    
    for stock in STOCKS:
        # Check if stock already exists
        existing = await db.investments.find_one({"symbol": stock["symbol"]})
        
        if existing:
            # Update existing stock
            await db.investments.update_one(
                {"symbol": stock["symbol"]},
                {"$set": {
                    "name": stock["name"],
                    "current_price": stock["current_price"],
                    "currency": stock["currency"],
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }}
            )
            print(f"✏️  Updated: {stock['symbol']} - {stock['name']} ({stock['current_price']} {stock['currency']})")
            updated_count += 1
        else:
            # Add new stock
            investment_doc = {
                "id": str(uuid.uuid4()),
                "symbol": stock["symbol"],
                "name": stock["name"],
                "currency": stock["currency"],
                "current_price": stock["current_price"],
                "price_history": [
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "price": stock["current_price"],
                        "old_price": 0
                    }
                ],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            await db.investments.insert_one(investment_doc)
            print(f"✅ Added: {stock['symbol']} - {stock['name']} ({stock['current_price']} {stock['currency']})")
            added_count += 1
    
    print(f"\n✨ Complete!")
    print(f"   Added: {added_count} stocks")
    print(f"   Updated: {updated_count} stocks")
    print(f"   Total: {added_count + updated_count} stocks in database")
    
    # Show stocks by currency
    print("\n📊 Stocks by Currency:")
    for currency in ["VDD", "NIM", "KKD", "GRP"]:
        stocks_in_currency = [s for s in STOCKS if s["currency"] == currency]
        print(f"\n{currency}: {len(stocks_in_currency)} stocks")
        for stock in stocks_in_currency:
            print(f"   • {stock['name']}: {stock['current_price']} {currency}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_stocks())
