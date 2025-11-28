#!/usr/bin/env python3
"""
Script to set up the complete currency exchange rate matrix
All currency pairs with direct conversion rates
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

# Complete exchange rate matrix (as provided by user)
EXCHANGE_RATE_MATRIX = {
    # From GRP
    "GRP_TO_GRP": 1.0,
    "GRP_TO_NIM": 1.687,
    "GRP_TO_VDD": 2.366,
    "GRP_TO_KKD": 2.614,
    "GRP_TO_USD": 0.000245,
    
    # From NIM
    "NIM_TO_GRP": 0.592,
    "NIM_TO_NIM": 1.0,
    "NIM_TO_VDD": 1.403,
    "NIM_TO_KKD": 1.549,
    
    # From VDD
    "VDD_TO_GRP": 0.422,
    "VDD_TO_NIM": 0.713,
    "VDD_TO_VDD": 1.0,
    "VDD_TO_KKD": 1.104,
    
    # From KKD
    "KKD_TO_GRP": 0.382,
    "KKD_TO_NIM": 0.645,
    "KKD_TO_VDD": 0.905,
    "KKD_TO_KKD": 1.0
}

async def setup_exchange_matrix():
    """Set up the complete exchange rate matrix in database"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🌐 Setting up complete currency exchange matrix...")
    print("=" * 60)
    
    # Update the exchange_rates collection
    await db.exchange_rates.update_one(
        {"id": "exchange_matrix"},
        {
            "$set": {
                "rates": EXCHANGE_RATE_MATRIX,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "description": "Complete exchange rate matrix for all currency pairs"
            }
        },
        upsert=True
    )
    
    print("✅ Exchange rate matrix updated!\n")
    
    # Display the matrix
    currencies = ["GRP", "NIM", "VDD", "KKD"]
    
    print("📊 Exchange Rate Matrix:")
    print("-" * 60)
    
    for from_curr in currencies:
        print(f"\n💱 From {from_curr}:")
        for to_curr in currencies:
            if from_curr != to_curr:
                rate_key = f"{from_curr}_TO_{to_curr}"
                rate = EXCHANGE_RATE_MATRIX.get(rate_key, "N/A")
                print(f"   → {to_curr}: {rate}")
    
    print("\n" + "=" * 60)
    print(f"✨ Complete! Total exchange pairs: {len(EXCHANGE_RATE_MATRIX)}")
    
    # Also update currency_rates (for backward compatibility)
    old_format_rates = {
        "GRP_TO_NIM": EXCHANGE_RATE_MATRIX["GRP_TO_NIM"],
        "GRP_TO_VDD": EXCHANGE_RATE_MATRIX["GRP_TO_VDD"],
        "GRP_TO_KKD": EXCHANGE_RATE_MATRIX["GRP_TO_KKD"],
        "GRP_TO_USD": EXCHANGE_RATE_MATRIX["GRP_TO_USD"]
    }
    
    await db.currency_rates.update_one(
        {"id": "current_rates"},
        {
            "$set": {
                "rates": old_format_rates,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    print("✅ Legacy currency_rates also updated for backward compatibility")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(setup_exchange_matrix())
