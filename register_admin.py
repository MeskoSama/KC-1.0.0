#!/usr/bin/env python3
"""
Register admin user for testing
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://world-map-helper.preview.emergentagent.com/api"

async def register_admin():
    """Register admin user"""
    session = aiohttp.ClientSession()
    
    # Try to register TestMiner
    register_data = {
        "minecraft_username": "TestMiner",
        "password": "admin123",
        "server_code": "10997"  # GRP server
    }
    
    try:
        async with session.post(f"{BASE_URL}/auth/register", json=register_data) as response:
            result = await response.json()
            print(f"Register TestMiner Status: {response.status}")
            print(f"Register Response: {result}")
            
            if response.status == 200:
                token = result.get("token")
                user = result.get("user")
                print(f"✅ Successfully registered TestMiner")
                print(f"   Is Admin: {user.get('is_admin')}")
                print(f"   Balances: {user.get('balances')}")
                
                await session.close()
                return token, user
            elif "already exists" in result.get("detail", ""):
                print("User already exists, trying to login...")
                
                # Try to login
                login_data = {
                    "minecraft_username": "TestMiner",
                    "password": "admin123",
                    "server_code": "10997"
                }
                
                async with session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Successfully logged in as TestMiner")
                        await session.close()
                        return result.get("token"), result.get("user")
                    else:
                        print(f"❌ Login failed: {response.status}")
                        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    await session.close()
    return None, None

if __name__ == "__main__":
    asyncio.run(register_admin())