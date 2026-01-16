#!/usr/bin/env python3
"""
Germania Empire Minecraft Marketplace Backend Testing Suite
Tests all backend functionality including new improvements
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
import uuid

# Configuration
BASE_URL = "https://world-map-helper.preview.emergentagent.com/api"
TEST_USER_DATA = {
    "minecraft_username": "TestMiner2024",
    "password": "SecurePassword123!",
    "server_code": "10997"  # GRP server
}

class BackendTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
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
        
    async def make_request(self, method, endpoint, data=None, auth=True):
        """Make HTTP request with optional auth"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if auth and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
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
            
    async def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n=== Testing Authentication Endpoints ===")
        
        # Test registration
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
            
        # Test /auth/me endpoint
        status, response = await self.make_request("GET", "/auth/me")
        success = status == 200 and "username" in response
        self.log_test("Get Current User (/auth/me)", success, 
                     f"Username: {response.get('username', 'N/A')}" if success else f"Status: {status}")
        
        return True
        
    async def test_get_exchange_rate_function(self):
        """Test the fixed get_exchange_rate function through currency conversion"""
        print("\n=== Testing Exchange Rate Function ===")
        
        # First, get current currency rates
        status, response = await self.make_request("GET", "/marketplace/currency-rates", auth=False)
        if status != 200:
            self.log_test("Get Currency Rates", False, f"Status: {status}")
            return
            
        rates = response.get("rates", {})
        self.log_test("Get Currency Rates", True, f"Rates: {rates}")
        
        # Test same currency conversion (should return 1.0 conceptually)
        # We'll test this through the conversion endpoint
        conversion_data = {
            "from_currency": "GRP",
            "to_currency": "NIM", 
            "amount": 100.0
        }
        
        status, response = await self.make_request("POST", "/currency/convert", conversion_data)
        if status == 200:
            exchange_rate = response.get("exchange_rate", 0)
            expected_rate = rates.get("GRP_TO_NIM", 0)
            rate_matches = abs(exchange_rate - expected_rate) < 0.001
            self.log_test("Currency Conversion GRP->NIM", rate_matches, 
                         f"Rate: {exchange_rate}, Expected: {expected_rate}")
        else:
            self.log_test("Currency Conversion Test", False, f"Status: {status}, Response: {response}")
            
    async def test_transaction_history_endpoint(self):
        """Test new /api/transactions/history endpoint"""
        print("\n=== Testing Transaction History Endpoint ===")
        
        # Test without auth (should fail 401)
        status, response = await self.make_request("GET", "/transactions/history", auth=False)
        success = status == 401
        self.log_test("Transaction History - No Auth", success, 
                     f"Status: {status} (expected 401)")
        
        # Test with valid token
        status, response = await self.make_request("GET", "/transactions/history")
        success = status == 200 and "transactions" in response
        self.log_test("Transaction History - With Auth", success,
                     f"Status: {status}, Transactions count: {len(response.get('transactions', []))}")
        
        if success:
            # Verify structure
            transactions = response.get("transactions", [])
            if transactions:
                first_txn = transactions[0]
                required_fields = ["id", "type", "action", "amount", "currency", "status", "timestamp", "details"]
                has_all_fields = all(field in first_txn for field in required_fields)
                self.log_test("Transaction Structure Validation", has_all_fields,
                             f"Fields present: {list(first_txn.keys())}")
            
            # Test filtering by transaction_type
            for txn_type in ["payment", "investment", "property", "bounty_create", "bounty_complete"]:
                status, response = await self.make_request("GET", f"/transactions/history?transaction_type={txn_type}")
                success = status == 200
                filtered_count = len(response.get("transactions", []))
                self.log_test(f"Transaction Filter - {txn_type}", success,
                             f"Count: {filtered_count}")
            
            # Test pagination
            status, response = await self.make_request("GET", "/transactions/history?skip=0&limit=5")
            success = status == 200 and len(response.get("transactions", [])) <= 5
            self.log_test("Transaction Pagination", success,
                         f"Returned: {len(response.get('transactions', []))} (max 5)")
                         
    async def test_activity_feed_endpoint(self):
        """Test new /api/activity/feed endpoint"""
        print("\n=== Testing Activity Feed Endpoint ===")
        
        # Test without params
        status, response = await self.make_request("GET", "/activity/feed", auth=False)
        success = status == 200 and "activities" in response
        self.log_test("Activity Feed - Basic", success,
                     f"Status: {status}, Activities count: {len(response.get('activities', []))}")
        
        if success:
            # Verify activity structure
            activities = response.get("activities", [])
            if activities:
                first_activity = activities[0]
                required_fields = ["type", "message", "timestamp", "icon"]
                has_all_fields = all(field in first_activity for field in required_fields)
                self.log_test("Activity Structure Validation", has_all_fields,
                             f"Fields: {list(first_activity.keys())}")
            
            # Test pagination
            status, response = await self.make_request("GET", "/activity/feed?skip=0&limit=3", auth=False)
            success = status == 200 and len(response.get("activities", [])) <= 3
            self.log_test("Activity Feed Pagination", success,
                         f"Returned: {len(response.get('activities', []))} (max 3)")
                         
    async def test_portfolio_summary_endpoint(self):
        """Test new /api/portfolio/summary endpoint"""
        print("\n=== Testing Portfolio Summary Endpoint ===")
        
        # Test without auth (should fail 401)
        status, response = await self.make_request("GET", "/portfolio/summary", auth=False)
        success = status == 401
        self.log_test("Portfolio Summary - No Auth", success,
                     f"Status: {status} (expected 401)")
        
        # Test with valid token
        status, response = await self.make_request("GET", "/portfolio/summary")
        success = status == 200 and "net_worth" in response
        self.log_test("Portfolio Summary - With Auth", success,
                     f"Status: {status}")
        
        if success:
            # Verify net_worth structure
            net_worth = response.get("net_worth", {})
            required_net_worth_fields = ["total_grp", "total_usd", "currency_value", "investments_value", "properties_value"]
            has_net_worth_fields = all(field in net_worth for field in required_net_worth_fields)
            self.log_test("Portfolio Net Worth Structure", has_net_worth_fields,
                         f"Net worth: {net_worth.get('total_grp', 0)} GRP")
            
            # Verify breakdown structure
            breakdown = response.get("breakdown", {})
            required_breakdown_fields = ["currencies", "investments", "properties"]
            has_breakdown_fields = all(field in breakdown for field in required_breakdown_fields)
            self.log_test("Portfolio Breakdown Structure", has_breakdown_fields,
                         f"Breakdown keys: {list(breakdown.keys())}")
            
            # Verify stats structure
            stats = response.get("stats", {})
            required_stats_fields = ["total_spent", "total_transactions", "owned_ranks", "owned_houses", "active_investments"]
            has_stats_fields = all(field in stats for field in required_stats_fields)
            self.log_test("Portfolio Stats Structure", has_stats_fields,
                         f"Stats: {stats}")
                         
    async def test_marketplace_endpoints(self):
        """Test existing marketplace endpoints still work"""
        print("\n=== Testing Existing Marketplace Endpoints ===")
        
        # Test currency rates
        status, response = await self.make_request("GET", "/marketplace/currency-rates", auth=False)
        success = status == 200 and "rates" in response
        self.log_test("Marketplace Currency Rates", success,
                     f"Status: {status}")
        
        # Test rank prices
        status, response = await self.make_request("GET", "/marketplace/rank-prices", auth=False)
        success = status == 200 and "ranks" in response
        self.log_test("Marketplace Rank Prices", success,
                     f"Status: {status}")
        
        # Test houses endpoint
        status, response = await self.make_request("GET", "/houses", auth=False)
        success = status == 200 and "houses" in response
        self.log_test("Houses Listing", success,
                     f"Status: {status}, Houses count: {len(response.get('houses', []))}")
        
        # Test bounties endpoint
        status, response = await self.make_request("GET", "/bounties", auth=False)
        success = status == 200 and "bounties" in response
        self.log_test("Bounties Listing", success,
                     f"Status: {status}, Bounties count: {len(response.get('bounties', []))}")
        
        # Test investments endpoint
        status, response = await self.make_request("GET", "/investments")
        success = status == 200 and "investments" in response
        self.log_test("Investments Listing", success,
                     f"Status: {status}")
                     
    async def test_house_purchase_with_conversion(self):
        """Test house purchase uses fixed get_exchange_rate function"""
        print("\n=== Testing House Purchase with Currency Conversion ===")
        
        # First, get available houses
        status, response = await self.make_request("GET", "/houses", auth=False)
        if status != 200:
            self.log_test("Get Houses for Purchase Test", False, f"Status: {status}")
            return
            
        houses = response.get("houses", [])
        available_houses = [h for h in houses if h.get("status") == "available"]
        
        if not available_houses:
            self.log_test("House Purchase Test", False, "No available houses to test purchase")
            return
            
        # Try to purchase a house (this will likely fail due to insufficient balance, but we can test the endpoint)
        house = available_houses[0]
        house_id = house.get("id")
        
        # Test the buy endpoint (should use the fixed exchange rate function)
        purchase_data = {
            "payment_type": "currency",
            "payment_currency": "GRP"
        }
        
        status, response = await self.make_request("POST", f"/houses/{house_id}/buy?payment_type=currency&payment_currency=GRP")
        
        # We expect either success or insufficient balance error (both indicate the endpoint works)
        success = status in [200, 400]
        if status == 400 and "Insufficient balance" in response.get("detail", ""):
            self.log_test("House Purchase Endpoint (Exchange Rate)", True, 
                         "Endpoint works - insufficient balance (expected)")
        elif status == 200:
            self.log_test("House Purchase Endpoint (Exchange Rate)", True,
                         "Purchase successful")
        else:
            self.log_test("House Purchase Endpoint (Exchange Rate)", False,
                         f"Status: {status}, Response: {response}")
                         
    async def create_test_data(self):
        """Create some test data for better testing"""
        print("\n=== Creating Test Data ===")
        
        # Try to create a bounty to generate transaction history
        bounty_data = {
            "bounty_type": "kill",
            "title": "Test Bounty for Testing",
            "description": "This is a test bounty created for testing purposes",
            "reward_currency": "GRP",
            "reward_amount": 10.0,
            "target_player": "TestTarget"
        }
        
        status, response = await self.make_request("POST", "/bounties", bounty_data)
        if status == 200:
            self.log_test("Create Test Bounty", True, f"Bounty ID: {response.get('bounty_id')}")
        elif status == 400 and "Insufficient balance" in response.get("detail", ""):
            self.log_test("Create Test Bounty", True, "Insufficient balance (expected for new user)")
        else:
            self.log_test("Create Test Bounty", False, f"Status: {status}, Response: {response}")
            
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Germania Empire Marketplace Backend Tests")
        print(f"Testing against: {BASE_URL}")
        
        await self.setup_session()
        
        try:
            # Setup authentication
            auth_success = await self.test_auth_endpoints()
            if not auth_success:
                print("❌ Authentication failed - cannot continue with authenticated tests")
                return
                
            # Create some test data
            await self.create_test_data()
            
            # Run all tests
            await self.test_get_exchange_rate_function()
            await self.test_transaction_history_endpoint()
            await self.test_activity_feed_endpoint()
            await self.test_portfolio_summary_endpoint()
            await self.test_marketplace_endpoints()
            await self.test_house_purchase_with_conversion()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🏁 TEST SUMMARY")
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
        
        print("\n✅ CRITICAL FUNCTIONALITY STATUS:")
        critical_tests = [
            "User Registration", "User Login (existing user)", "Get Current User (/auth/me)",
            "Transaction History - With Auth", "Portfolio Summary - With Auth",
            "Activity Feed - Basic", "Currency Conversion GRP->NIM"
        ]
        
        for test_name in critical_tests:
            test_result = next((t for t in self.test_results if t["test"] == test_name), None)
            if test_result:
                status = "✅" if test_result["success"] else "❌"
                print(f"  {status} {test_name}")

async def main():
    """Main test runner"""
    tester = BackendTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())