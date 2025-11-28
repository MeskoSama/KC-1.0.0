#!/usr/bin/env python3
"""
Fix user portfolio field to ensure it's properly initialized
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/app/backend/.env')

async def fix_user_portfolio():
    """Fix user portfolio fields"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("Fixing user portfolio fields...")
    
    # Find all users
    users = await db.users.find({}).to_list(1000)
    print(f"Found {len(users)} users")
    
    for user in users:
        user_id = user.get("id")
        username = user.get("minecraft_username")
        
        # Check if user has portfolio field
        if "portfolio" not in user:
            print(f"Adding portfolio field to user {username}")
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"portfolio": {}}}
            )
        else:
            # Check if portfolio has any invalid data
            portfolio = user.get("portfolio", {})
            if portfolio and not isinstance(portfolio, dict):
                print(f"Fixing invalid portfolio for user {username}")
                await db.users.update_one(
                    {"id": user_id},
                    {"$set": {"portfolio": {}}}
                )
            elif portfolio:
                # Ensure all portfolio values are numbers
                fixed_portfolio = {}
                needs_fix = False
                for symbol, quantity in portfolio.items():
                    if isinstance(quantity, (int, float)):
                        fixed_portfolio[symbol] = quantity
                    else:
                        print(f"Fixing invalid quantity for {symbol} in user {username}")
                        fixed_portfolio[symbol] = 0.0
                        needs_fix = True
                
                if needs_fix:
                    await db.users.update_one(
                        {"id": user_id},
                        {"$set": {"portfolio": fixed_portfolio}}
                    )
    
    print("Portfolio fix complete!")
    
    # Also check investments collection for ObjectId issues
    investments = await db.investments.find({}).to_list(1000)
    print(f"Found {len(investments)} investments")
    
    for investment in investments:
        # Check if there are any ObjectId fields that shouldn't be there
        if "_id" in investment:
            symbol = investment.get("symbol")
            print(f"Investment {symbol} has _id field, this might cause issues")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(fix_user_portfolio())