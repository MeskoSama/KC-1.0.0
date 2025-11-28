#!/usr/bin/env python3
"""
Script to add portfolio field to all users who don't have it
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def fix_user_portfolios():
    """Add portfolio field to users who don't have it"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔧 Fixing user portfolio fields...")
    print("=" * 60)
    
    # Get all users
    users = await db.users.find({}, {"_id": 0, "id": 1, "minecraft_username": 1, "portfolio": 1}).to_list(1000)
    
    print(f"Found {len(users)} users\n")
    
    fixed_count = 0
    already_good = 0
    
    for user in users:
        username = user.get("minecraft_username", "Unknown")
        user_id = user.get("id")
        
        if "portfolio" not in user or user.get("portfolio") is None:
            # Add empty portfolio
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"portfolio": {}}}
            )
            print(f"✅ Added portfolio to: {username}")
            fixed_count += 1
        else:
            print(f"✓  Already has portfolio: {username}")
            already_good += 1
    
    print("\n" + "=" * 60)
    print(f"✨ Complete!")
    print(f"   Fixed: {fixed_count} users")
    print(f"   Already OK: {already_good} users")
    print(f"   Total: {len(users)} users")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_user_portfolios())
