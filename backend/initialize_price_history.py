#!/usr/bin/env python3
"""
Script to initialize realistic price history for all stocks
Generates 90 days of historical price data with realistic movements
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone, timedelta
import random
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

def generate_price_history(base_price, days=90):
    """Generate realistic price history with trends and volatility"""
    history = []
    current_price = base_price
    
    # Random trend direction
    trend = random.choice([-1, 1])
    trend_strength = random.uniform(0.001, 0.003)  # 0.1% to 0.3% daily trend
    
    for i in range(days, 0, -1):
        timestamp = datetime.now(timezone.utc) - timedelta(days=i)
        
        # Add trend
        trend_change = trend * trend_strength * current_price
        
        # Add volatility (random daily fluctuation)
        volatility = random.uniform(-0.02, 0.02) * current_price  # ±2% daily volatility
        
        # Apply changes
        old_price = current_price
        current_price = max(current_price + trend_change + volatility, base_price * 0.5)  # Don't drop below 50%
        
        # Occasionally reverse trend (market correction)
        if random.random() < 0.05:  # 5% chance
            trend = -trend
        
        history.append({
            "timestamp": timestamp.isoformat(),
            "price": round(current_price, 2),
            "old_price": round(old_price, 2),
            "change": round(((current_price - old_price) / old_price) * 100, 2)
        })
    
    return history, current_price

async def initialize_price_history():
    """Initialize price history for all stocks"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🚀 Initializing price history for all stocks...")
    print("=" * 60)
    
    # Get all investments
    investments = await db.investments.find({}, {"_id": 0}).to_list(1000)
    
    print(f"Found {len(investments)} stocks\n")
    
    updated_count = 0
    
    for investment in investments:
        symbol = investment["symbol"]
        base_price = investment["current_price"]
        
        # Generate 90 days of history
        price_history, final_price = generate_price_history(base_price, days=90)
        
        # Update the investment with history and final price
        await db.investments.update_one(
            {"symbol": symbol},
            {
                "$set": {
                    "price_history": price_history,
                    "current_price": final_price,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Calculate change
        start_price = price_history[0]["price"]
        price_change = ((final_price - start_price) / start_price) * 100
        trend_emoji = "📈" if price_change > 0 else "📉"
        
        print(f"{trend_emoji} {symbol}")
        print(f"   Start: {start_price:.2f} → Current: {final_price:.2f}")
        print(f"   90-day change: {price_change:+.2f}%")
        print(f"   History points: {len(price_history)}")
        print()
        
        updated_count += 1
    
    print("=" * 60)
    print(f"✨ Complete! Updated {updated_count} stocks with 90-day price history")
    print(f"📊 Total data points: {updated_count * 90}")
    
    # Also initialize currency exchange rate history
    print("\n🌐 Initializing currency exchange rate history...")
    
    base_rates = {
        "GRP_TO_EP": 112.43700,
        "GRP_TO_NIM": 1.68700,
        "GRP_TO_VDD": 2.36666,
        "GRP_TO_KKD": 2.61455,
        "GRP_TO_USD": 0.000245
    }
    
    rate_history = []
    for i in range(90, 0, -1):
        timestamp = datetime.now(timezone.utc) - timedelta(days=i)
        
        day_rates = {}
        for rate_key, base_rate in base_rates.items():
            # Small fluctuations in exchange rates
            variation = random.uniform(-0.01, 0.01) * base_rate
            day_rates[rate_key] = round(base_rate + variation, 6)
        
        rate_history.append({
            "timestamp": timestamp.isoformat(),
            "rates": day_rates
        })
    
    # Store exchange rate history
    await db.exchange_rate_history.delete_many({})  # Clear old data
    await db.exchange_rate_history.insert_many(rate_history)
    
    print(f"✅ Added 90 days of exchange rate history")
    print(f"📊 Total rate snapshots: {len(rate_history)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(initialize_price_history())
