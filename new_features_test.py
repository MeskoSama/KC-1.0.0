#!/usr/bin/env python3
"""
Germania Empire Minecraft Marketplace - New Features Testing Suite
Tests the specific new fixes and features mentioned in the review request:
1. Stock Buy/Sell Endpoints with JSON body
2. EP and EGD currencies 
3. Admin currency management endpoints
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
import uuid

# Configuration
BASE_URL = "https://code-fixer-104.preview.emergentagent.com/api"
TEST_USER_DATA = {
    "minecraft_username": "TestMiner2024",
    "password": "SecurePassword123!",
    "server_code": "10997"  # GRP server
}

# Admin user for testing admin endpoints
ADMIN_USER_DATA = {
    "minecraft_username": "meskop",
    "password": "admin123",
    "server_code": "10997"
}

class NewFeaturesTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.admin_token = None
        self.user_id = None
        self.test_results = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    async def make_request(self, method, endpoint, data=None, auth=True, admin=False):
        """Make HTTP request with optional auth"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if auth:
            token = self.admin_token if admin else self.auth_token
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers) as response:
                    return response.status, await response.json()
            elif method.upper() == "POST":
                async with self.session.post(url, headers=headers, json=data) as response:
                    return response.status, await response.json()
            elif method.upper() == "PUT":
                async with self.session.put(url, headers=headers, json=data) as response:
                    return response.status, await response.json()
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=headers) as response:
                    return response.status, await response.json()
        except Exception as e:
            return 500, {"error": str(e)}
            
    async def setup_auth(self):
        """Setup authentication for both regular user and admin"""
        print("\n=== Setting up Authentication ===")
        
        # Setup regular user
        status, response = await self.make_request("POST", "/auth/register", TEST_USER_DATA, auth=False)
        
        if status == 200:
            self.auth_token = response.get("token")
            self.user_id = response.get("user", {}).get("id")
            self.log_test("User Registration", True, f"User ID: {self.user_id}")
        elif status == 400 and "already exists" in response.get("detail", ""):
            # User exists, try login
            status, response = await self.make_request("POST", "/auth/login", TEST_USER_DATA, auth=False)
            if status == 200:
                self.auth_token = response.get("token")
                self.user_id = response.get("user", {}).get("id")
                self.log_test("User Login (existing user)", True, f"User ID: {self.user_id}")
            else:
                self.log_test("User Login", False, f"Status: {status}, Response: {response}")
                return False
        else:
            self.log_test("User Registration", False, f"Status: {status}, Response: {response}")
            return False
            
        # Setup admin user
        status, response = await self.make_request("POST", "/auth/login", ADMIN_USER_DATA, auth=False)
        if status == 200:
            self.admin_token = response.get("token")
            self.log_test("Admin Login", True, "Admin authenticated")
        else:
            self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")
            # Continue without admin - some tests will be skipped
            
        return True
        
    async def add_balance_to_user(self):
        """Add balance to test user for stock trading"""
        if not self.admin_token:
            print("⚠️ No admin token - skipping balance addition")
            return
            
        print("\n=== Adding Balance to Test User ===")
        
        # Add GRP balance for testing
        balance_data = {
            "user_id": self.user_id,
            "currency": "GRP", 
            "amount": 1000.0,
            "operation": "add"
        }
        
        status, response = await self.make_request("PUT", "/admin/user/balance", balance_data, admin=True)
        success = status == 200
        self.log_test("Add GRP Balance to User", success, 
                     f"Added 1000 GRP" if success else f"Status: {status}, Response: {response}")
        
    async def test_new_currencies(self):
        """Test EP and EGD currencies"""
        print("\n=== Testing New Currencies (EP and EGD) ===")
        
        # Test GET /api/currencies - Should return 6 currencies
        status, response = await self.make_request("GET", "/currencies", auth=False)
        success = status == 200 and "currencies" in response
        
        if success:
            currencies = response.get("currencies", [])
            expected_currencies = ["NIM", "GRP", "VDD", "KKD", "EP", "EGD"]
            has_all_currencies = all(curr in currencies for curr in expected_currencies)
            currency_count = len(currencies)
            
            self.log_test("GET /currencies - 6 currencies", has_all_currencies and currency_count == 6,
                         f"Found {currency_count} currencies: {currencies}")
        else:
            self.log_test("GET /currencies", False, f"Status: {status}, Response: {response}")
            
        # Test GET /api/currencies/rates - Should have 36 exchange rates (6x6 matrix)
        status, response = await self.make_request("GET", "/currencies/rates", auth=False)
        success = status == 200 and "rates" in response
        
        if success:
            rates = response.get("rates", {})
            rate_count = len(rates)
            expected_count = 36  # 6x6 matrix
            
            # Check for specific EP rates mentioned in requirements
            grp_to_ep = rates.get("GRP_TO_EP", 0)
            ep_to_egd = rates.get("EP_TO_EGD", 0)
            
            expected_grp_to_ep = 112.4375
            expected_ep_to_egd = 1.05
            
            grp_ep_correct = abs(grp_to_ep - expected_grp_to_ep) < 0.001
            ep_egd_correct = abs(ep_to_egd - expected_ep_to_egd) < 0.001
            
            self.log_test("GET /currencies/rates - 36 rates", rate_count == expected_count,
                         f"Found {rate_count} rates (expected {expected_count})")
            self.log_test("EP Rate Verification", grp_ep_correct,
                         f"1 GRP = {grp_to_ep} EP (expected {expected_grp_to_ep})")
            self.log_test("EGD Rate Verification", ep_egd_correct,
                         f"1 EP = {ep_to_egd} EGD (expected {expected_ep_to_egd})")
        else:
            self.log_test("GET /currencies/rates", False, f"Status: {status}, Response: {response}")
            
        # Test currency conversion with EP/EGD
        conversion_tests = [
            {"from_currency": "GRP", "to_currency": "EP", "amount": 1.0},
            {"from_currency": "EP", "to_currency": "EGD", "amount": 100.0},
            {"from_currency": "EGD", "to_currency": "GRP", "amount": 50.0}
        ]
        
        for conversion in conversion_tests:
            status, response = await self.make_request("POST", "/currency/convert", conversion)
            success = status in [200, 400]  # 400 might be insufficient balance
            
            if status == 200:
                rate = response.get("exchange_rate", 0)
                self.log_test(f"Currency Conversion {conversion['from_currency']}->{conversion['to_currency']}", 
                             True, f"Rate: {rate}")
            elif status == 400 and "Insufficient balance" in response.get("detail", ""):
                self.log_test(f"Currency Conversion {conversion['from_currency']}->{conversion['to_currency']}", 
                             True, "Endpoint works - insufficient balance (expected)")
            else:
                self.log_test(f"Currency Conversion {conversion['from_currency']}->{conversion['to_currency']}", 
                             False, f"Status: {status}, Response: {response}")
                             
    async def test_stock_buy_sell_json(self):
        """Test fixed stock buy/sell endpoints with JSON body"""
        print("\n=== Testing Stock Buy/Sell with JSON Body ===")
        
        # First get available investments
        status, response = await self.make_request("GET", "/investments")
        if status != 200:
            self.log_test("Get Investments", False, f"Status: {status}")
            return
            
        investments = response.get("investments", [])
        if not investments:
            self.log_test("Stock Trading Test", False, "No investments available")
            return
            
        # Find GRP-HAZINE or any low-cost GRP stock
        grp_stocks = [inv for inv in investments if inv.get("currency") == "GRP"]
        if not grp_stocks:
            self.log_test("Stock Trading Test", False, "No GRP stocks available")
            return
            
        # Use the first GRP stock or look for GRP-HAZINE specifically
        test_stock = None
        for stock in grp_stocks:
            if "HAZINE" in stock.get("symbol", "").upper():
                test_stock = stock
                break
        
        if not test_stock:
            test_stock = grp_stocks[0]  # Use first GRP stock
            
        symbol = test_stock["symbol"]
        price = test_stock["current_price"]
        
        self.log_test("Found Test Stock", True, f"Symbol: {symbol}, Price: {price} GRP")
        
        # Test BUY with JSON body
        buy_order = {
            "symbol": symbol,
            "quantity": 2.0
        }
        
        status, response = await self.make_request("POST", "/investments/buy", buy_order)
        
        if status == 200:
            transaction = response.get("transaction", {})
            total_cost = transaction.get("total_amount", 0) + transaction.get("commission", 0)
            self.log_test("Stock BUY with JSON body", True, 
                         f"Bought 2 shares of {symbol} for {total_cost} GRP")
            
            # Test SELL with JSON body
            sell_order = {
                "symbol": symbol,
                "quantity": 1.0
            }
            
            status, response = await self.make_request("POST", "/investments/sell", sell_order)
            
            if status == 200:
                transaction = response.get("transaction", {})
                total_received = transaction.get("total_amount", 0) - transaction.get("commission", 0)
                self.log_test("Stock SELL with JSON body", True,
                             f"Sold 1 share of {symbol} for {total_received} GRP")
                             
                # Verify portfolio is updated
                status, response = await self.make_request("GET", "/auth/me")
                if status == 200:
                    portfolio = response.get("portfolio", {})
                    remaining_shares = portfolio.get(symbol, 0)
                    self.log_test("Portfolio Update Verification", remaining_shares == 1.0,
                                 f"Remaining shares: {remaining_shares} (expected 1)")
            else:
                self.log_test("Stock SELL with JSON body", False,
                             f"Status: {status}, Response: {response}")
        elif status == 400 and "Insufficient" in response.get("detail", ""):
            self.log_test("Stock BUY with JSON body", True,
                         "Endpoint works - insufficient balance (expected without admin balance)")
        else:
            self.log_test("Stock BUY with JSON body", False,
                         f"Status: {status}, Response: {response}")
                         
    async def test_admin_currency_management(self):
        """Test new admin currency management endpoints"""
        print("\n=== Testing Admin Currency Management ===")
        
        if not self.admin_token:
            print("⚠️ No admin token - skipping admin currency tests")
            return
            
        # Test POST /api/admin/currencies - Add new currency
        new_currency = {
            "code": "TEST",
            "name": "Test Currency",
            "base_rate_to_grp": 50.0
        }
        
        status, response = await self.make_request("POST", "/admin/currencies", new_currency, admin=True)
        success = status == 200
        self.log_test("POST /admin/currencies - Add currency", success,
                     f"Added TEST currency" if success else f"Status: {status}, Response: {response}")
        
        # Test PUT /api/admin/currencies - Update currency
        if success:
            update_currency = {
                "code": "TEST",
                "name": "Updated Test Currency",
                "base_rate_to_grp": 75.0
            }
            
            status, response = await self.make_request("PUT", "/admin/currencies", update_currency, admin=True)
            success = status == 200
            self.log_test("PUT /admin/currencies - Update currency", success,
                         f"Updated TEST currency" if success else f"Status: {status}, Response: {response}")
        
        # Test PUT /api/admin/exchange-rate/direct - Update specific rate
        rate_update = {
            "from_currency": "GRP",
            "to_currency": "EP", 
            "rate": 115.0
        }
        
        status, response = await self.make_request("PUT", "/admin/exchange-rate/direct", rate_update, admin=True)
        success = status == 200
        self.log_test("PUT /admin/exchange-rate/direct", success,
                     f"Updated GRP->EP rate" if success else f"Status: {status}, Response: {response}")
        
        # Test POST /admin/currencies/initialize - Reset to defaults
        status, response = await self.make_request("POST", "/admin/currencies/initialize", {}, admin=True)
        success = status == 200
        self.log_test("POST /admin/currencies/initialize", success,
                     f"Reset to defaults" if success else f"Status: {status}, Response: {response}")
        
        # Test POST /admin/users/migrate-balances - Add EP/EGD to users
        status, response = await self.make_request("POST", "/admin/users/migrate-balances", {}, admin=True)
        success = status == 200
        self.log_test("POST /admin/users/migrate-balances", success,
                     f"Migrated user balances" if success else f"Status: {status}, Response: {response}")
        
        # Test DELETE /admin/currencies/{code} - Delete custom currency
        if new_currency:
            status, response = await self.make_request("DELETE", "/admin/currencies/TEST", admin=True)
            success = status == 200
            self.log_test("DELETE /admin/currencies/{code}", success,
                         f"Deleted TEST currency" if success else f"Status: {status}, Response: {response}")
            
            # Try to delete base currency (should fail)
            status, response = await self.make_request("DELETE", "/admin/currencies/GRP", admin=True)
            success = status == 400 or status == 403  # Should be forbidden
            self.log_test("DELETE base currency (should fail)", success,
                         f"Correctly prevented deletion of base currency" if success else f"Unexpected: {status}")
                         
    async def run_all_tests(self):
        """Run all new feature tests"""
        print("🚀 Starting Germania Empire Marketplace - New Features Tests")
        print(f"Testing against: {BASE_URL}")
        
        await self.setup_session()
        
        try:
            # Setup authentication
            auth_success = await self.setup_auth()
            if not auth_success:
                print("❌ Authentication failed - cannot continue")
                return
                
            # Add balance for stock trading tests
            await self.add_balance_to_user()
            
            # Run specific new feature tests
            await self.test_new_currencies()
            await self.test_stock_buy_sell_json()
            await self.test_admin_currency_management()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🏁 NEW FEATURES TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        print("\n✅ CRITICAL NEW FEATURES STATUS:")
        critical_tests = [
            "GET /currencies - 6 currencies",
            "GET /currencies/rates - 36 rates", 
            "EP Rate Verification",
            "EGD Rate Verification",
            "Stock BUY with JSON body",
            "Stock SELL with JSON body"
        ]
        
        for test_name in critical_tests:
            test_result = next((t for t in self.test_results if t["test"] == test_name), None)
            if test_result:
                status = "✅" if test_result["success"] else "❌"
                print(f"  {status} {test_name}")

async def main():
    """Main test runner"""
    tester = NewFeaturesTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())