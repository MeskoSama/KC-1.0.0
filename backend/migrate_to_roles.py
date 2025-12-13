#!/usr/bin/env python3
"""
Migration Script: Add role-based permissions to existing users
Run this ONCE before deploying the new code
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

# Hardcoded admin usernames (from old system)
OLD_ADMIN_USERNAMES = ["TestMiner", "meskop"]

async def migrate_users():
    """Add role and banned fields to all existing users"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔄 Starting user migration to role-based system...")
    print("=" * 60)
    
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    print(f"Found {len(users)} users\n")
    
    updated_count = 0
    admin_count = 0
    
    for user in users:
        username = user.get("minecraft_username", "Unknown")
        user_id = user.get("id")
        
        updates = {}
        
        # Add role field if missing
        if "role" not in user:
            # Check if user was previously an admin
            if username in OLD_ADMIN_USERNAMES or user.get("is_admin", False):
                updates["role"] = "admin"
                admin_count += 1
                print(f"👑 {username} → role: admin")
            else:
                updates["role"] = "user"
                print(f"👤 {username} → role: user")
        
        # Add banned field if missing
        if "banned" not in user:
            updates["banned"] = False
        
        # Apply updates
        if updates:
            await db.users.update_one(
                {"id": user_id},
                {"$set": updates}
            )
            updated_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Migration complete!")
    print(f"   Updated: {updated_count} users")
    print(f"   Admins: {admin_count}")
    print(f"   Regular users: {updated_count - admin_count}")
    print("\n⚠️  Note: The 'is_admin' field is now deprecated.")
    print("   It will be removed in the next cleanup phase.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_users())
