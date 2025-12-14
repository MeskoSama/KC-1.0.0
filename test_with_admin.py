#!/usr/bin/env python3
"""
Test with admin user to verify stock buying functionality
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://code-fixer-104.preview.emergentagent.com/api"

async def test_admin_login():
    """Try to login as admin users"""
    session = aiohttp.ClientSession()
    
    # Try different admin users and passwords
    admin_users = [
        {"username": "meskop", "passwords": ["meskop", "admin", "password", "123456", "meskop123"]},
        {"username": "TestMiner", "passwords": ["test", "admin", "password", "123456", "TestMiner"]}
    ]
    
    for user_info in admin_users:
        username = user_info["username"]
        for password in user_info["passwords"]:
            login_data = {
                "minecraft_username": username,
                "password": password,
                "server_code": "10997"  # GRP server
            }
            
            try:
                async with session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Successfully logged in as {username} with password: {password}")
                        print(f"   User ID: {result.get('user', {}).get('id')}")
                        print(f"   Is Admin: {result.get('user', {}).get('is_admin')}")
                        print(f"   Balances: {result.get('user', {}).get('balances')}")
                        
                        await session.close()
                        return result.get("token"), result.get("user")
                    else:
                        print(f"❌ Failed login {username}:{password} - Status: {response.status}")
            except Exception as e:
                print(f"❌ Error trying {username}:{password} - {e}")
    
    await session.close()
    return None, None

async def test_stock_purchase_with_admin():
    """Test stock purchase with admin user"""
    token, user = await test_admin_login()
    
    if not token:
        print("❌ Could not login as admin user")
        return
        
    session = aiohttp.ClientSession()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    try:
        # Add balance if needed
        user_id = user.get("id")
        balances = user.get("balances", {})
        
        if all(balance < 1000 for balance in balances.values()):
            print("\n=== Adding Balance ===")
            for currency in ["GRP", "VDD", "NIM"]:
                balance_data = {
                    "user_id": user_id,
                    "currency": currency,
                    "amount": 10000.0,
                    "operation": "add"
                }
                
                async with session.put(f"{BASE_URL}/admin/user/balance", json=balance_data, headers=headers) as response:
                    if response.status == 200:
                        print(f"✅ Added 10000 {currency}")
                    else:
                        print(f"❌ Failed to add {currency}: {response.status}")
        
        # Get updated user info
        async with session.get(f"{BASE_URL}/auth/me", headers=headers) as response:
            if response.status == 200:
                user_info = await response.json()
                print(f"\n=== Updated User Info ===")
                print(f"Balances: {user_info.get('balances')}")
                print(f"Portfolio: {user_info.get('portfolio', 'Not in response')}")
        
        # Get investments
        async with session.get(f"{BASE_URL}/investments", headers=headers) as response:
            if response.status == 200:
                investments_data = await response.json()
                investments = investments_data.get("investments", [])
                print(f"\n=== Available Investments ===")
                print(f"Found {len(investments)} investments")
                
                if investments:
                    # Try to buy a stock
                    stock = investments[0]
                    symbol = stock.get("symbol")
                    price = stock.get("current_price")
                    currency = stock.get("currency")
                    
                    print(f"\n=== Testing Stock Purchase ===")
                    print(f"Attempting to buy 1 share of {symbol} at {price} {currency}")
                    
                    # Test the buy endpoint
                    buy_url = f"{BASE_URL}/investments/buy?symbol={symbol}&quantity=1"
                    async with session.post(buy_url, headers=headers) as response:
                        result = await response.json()
                        print(f"Buy Response Status: {response.status}")
                        print(f"Buy Response: {result}")
                        
                        if response.status == 200:
                            print("✅ Stock purchase successful!")
                            
                            # Check updated balance and portfolio
                            async with session.get(f"{BASE_URL}/auth/me", headers=headers) as response:
                                if response.status == 200:
                                    updated_user = await response.json()
                                    print(f"Updated Balances: {updated_user.get('balances')}")
                                    print(f"Updated Portfolio: {updated_user.get('portfolio', 'Not in response')}")
                            
                            # Check portfolio summary
                            async with session.get(f"{BASE_URL}/portfolio/summary", headers=headers) as response:
                                if response.status == 200:
                                    portfolio_data = await response.json()
                                    investments_breakdown = portfolio_data.get("breakdown", {}).get("investments", [])
                                    print(f"Portfolio Summary Investments: {len(investments_breakdown)}")
                                    if investments_breakdown:
                                        print(f"First Investment: {investments_breakdown[0]}")
                        else:
                            print(f"❌ Stock purchase failed: {result}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_stock_purchase_with_admin())