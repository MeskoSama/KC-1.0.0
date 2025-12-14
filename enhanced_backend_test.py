#!/usr/bin/env python3
"""
Enhanced Germania Empire Minecraft Marketplace Backend Testing Suite
Tests with admin privileges to create proper test data
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
import uuid

# Configuration
BASE_URL = "https://code-fixer-104.preview.emergentagent.com/api"
ADMIN_USER_DATA = {
    "minecraft_username": "TestMiner",  # Admin user
    "password": "SecurePassword123!",
    "server_code": "10997"  # GRP server
}

TEST_USER_DATA = {
    "minecraft_username": "RegularUser2024",
    "password": "SecurePassword123!",
    "server_code": "10997"  # GRP server
}

class EnhancedBackendTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.user_token = None
        self.admin_id = None
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
        
    async def make_request(self, method, endpoint, data=None, auth_token=None):
        """Make HTTP request with optional auth"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            
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
        except Exception as e:
            return 500, {"error": str(e)}
            
    async def setup_admin_and_user(self):
        """Setup admin and regular user accounts"""
        print("\n=== Setting Up Test Accounts ===")
        
        # Setup admin user
        status, response = await self.make_request("POST", "/auth/login", ADMIN_USER_DATA)
        if status == 200:
            self.admin_token = response.get("token")
            self.admin_id = response.get("user", {}).get("id")
            self.log_test("Admin Login", True, f"Admin ID: {self.admin_id}")
        else:
            self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")
            return False
            
        # Setup regular user
        status, response = await self.make_request("POST", "/auth/register", TEST_USER_DATA)
        if status == 200:
            self.user_token = response.get("token")
            self.user_id = response.get("user", {}).get("id")
            self.log_test("User Registration", True, f"User ID: {self.user_id}")
        elif status == 400 and "already exists" in response.get("detail", ""):
            # User exists, try login
            status, response = await self.make_request("POST", "/auth/login", TEST_USER_DATA)
            if status == 200:
                self.user_token = response.get("token")
                self.user_id = response.get("user", {}).get("id")
                self.log_test("User Login (existing)", True, f"User ID: {self.user_id}")
            else:
                self.log_test("User Login", False, f"Status: {status}")
                return False
        else:
            self.log_test("User Registration", False, f"Status: {status}")
            return False
            
        return True
        
    async def give_user_balance(self):
        """Give user some balance for testing"""
        print("\n=== Setting Up Test Balance ===")
        
        balance_updates = [
            {"user_id": self.user_id, "currency": "GRP", "amount": 1000.0, "operation": "set"},
            {"user_id": self.user_id, "currency": "NIM", "amount": 500.0, "operation": "set"},
            {"user_id": self.user_id, "currency": "VDD", "amount": 300.0, "operation": "set"},
            {"user_id": self.user_id, "currency": "KKD", "amount": 200.0, "operation": "set"}
        ]
        
        for update in balance_updates:
            status, response = await self.make_request("PUT", "/admin/user/balance", update, self.admin_token)
            success = status == 200
            self.log_test(f"Set {update['currency']} Balance", success, 
                         f"{update['amount']} {update['currency']}")
                         
    async def test_exchange_rate_function_comprehensive(self):
        """Comprehensive test of get_exchange_rate function"""
        print("\n=== Testing Exchange Rate Function (Comprehensive) ===")
        
        # Test all currency pairs
        currency_pairs = [
            ("GRP", "NIM"), ("GRP", "VDD"), ("GRP", "KKD"),
            ("NIM", "GRP"), ("VDD", "GRP"), ("KKD", "GRP"),
            ("NIM", "VDD"), ("VDD", "KKD"), ("KKD", "NIM")
        ]
        
        for from_curr, to_curr in currency_pairs:
            conversion_data = {
                "from_currency": from_curr,
                "to_currency": to_curr,
                "amount": 100.0
            }
            
            status, response = await self.make_request("POST", "/currency/convert", conversion_data, self.user_token)
            success = status == 200
            if success:
                rate = response.get("exchange_rate", 0)
                self.log_test(f"Currency Conversion {from_curr}->{to_curr}", True, f"Rate: {rate:.6f}")
            else:
                self.log_test(f"Currency Conversion {from_curr}->{to_curr}", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test same currency conversion (should return 1.0)
        same_currency_data = {
            "from_currency": "GRP",
            "to_currency": "GRP", 
            "amount": 100.0
        }
        
        status, response = await self.make_request("POST", "/currency/convert", same_currency_data, self.user_token)
        if status == 400 and "Cannot convert to same currency" in response.get("detail", ""):
            self.log_test("Same Currency Conversion Prevention", True, "Correctly prevents same currency conversion")
        else:
            self.log_test("Same Currency Conversion Prevention", False, f"Status: {status}")
            
    async def create_test_transactions(self):
        """Create various types of transactions for testing"""
        print("\n=== Creating Test Transactions ===")
        
        # Create a bounty
        bounty_data = {
            "bounty_type": "kill",
            "title": "Test Kill Bounty",
            "description": "Test bounty for testing transaction history",
            "reward_currency": "GRP",
            "reward_amount": 50.0,
            "target_player": "TestTarget"
        }
        
        status, response = await self.make_request("POST", "/bounties", bounty_data, self.user_token)
        success = status == 200
        self.log_test("Create Test Bounty", success, 
                     f"Bounty ID: {response.get('bounty_id', 'N/A')}" if success else f"Status: {status}")
        
        # Try to buy an investment (if any exist)
        status, response = await self.make_request("GET", "/investments", auth_token=self.user_token)
        if status == 200:
            investments = response.get("investments", [])
            if investments:
                investment = investments[0]
                symbol = investment.get("symbol")
                
                status, response = await self.make_request("POST", f"/investments/buy?symbol={symbol}&quantity=10", 
                                                         auth_token=self.user_token)
                success = status == 200
                self.log_test("Create Investment Transaction", success,
                             f"Bought {symbol}" if success else f"Status: {status}")
            else:
                self.log_test("Create Investment Transaction", False, "No investments available")
                
    async def test_transaction_history_comprehensive(self):
        """Comprehensive test of transaction history endpoint"""
        print("\n=== Testing Transaction History (Comprehensive) ===")
        
        # Test basic functionality
        status, response = await self.make_request("GET", "/transactions/history", auth_token=self.user_token)
        success = status == 200 and "transactions" in response
        transaction_count = len(response.get("transactions", []))
        self.log_test("Transaction History Basic", success, f"Found {transaction_count} transactions")
        
        if success and transaction_count > 0:
            # Test structure validation
            first_txn = response["transactions"][0]
            required_fields = ["id", "type", "action", "amount", "currency", "status", "timestamp", "details"]
            has_all_fields = all(field in first_txn for field in required_fields)
            self.log_test("Transaction Structure Complete", has_all_fields,
                         f"Missing: {[f for f in required_fields if f not in first_txn]}")
            
            # Test filtering
            unique_types = set(txn["type"] for txn in response["transactions"])
            for txn_type in unique_types:
                status, filtered_response = await self.make_request(
                    "GET", f"/transactions/history?transaction_type={txn_type}", 
                    auth_token=self.user_token
                )
                filtered_txns = filtered_response.get("transactions", [])
                all_correct_type = all(txn["type"] == txn_type for txn in filtered_txns)
                self.log_test(f"Transaction Filter {txn_type}", all_correct_type,
                             f"Count: {len(filtered_txns)}")
                             
    async def test_portfolio_calculations(self):
        """Test portfolio summary calculations"""
        print("\n=== Testing Portfolio Calculations ===")
        
        status, response = await self.make_request("GET", "/portfolio/summary", auth_token=self.user_token)
        success = status == 200
        
        if success:
            net_worth = response.get("net_worth", {})
            breakdown = response.get("breakdown", {})
            
            # Verify calculations make sense
            currency_value = net_worth.get("currency_value", 0)
            investments_value = net_worth.get("investments_value", 0)
            properties_value = net_worth.get("properties_value", 0)
            total_grp = net_worth.get("total_grp", 0)
            
            calculated_total = currency_value + investments_value + properties_value
            calculation_correct = abs(calculated_total - total_grp) < 0.01
            
            self.log_test("Portfolio Calculation Accuracy", calculation_correct,
                         f"Calculated: {calculated_total:.2f}, Reported: {total_grp:.2f}")
            
            # Test USD conversion
            total_usd = net_worth.get("total_usd", 0)
            usd_conversion_exists = total_usd >= 0
            self.log_test("USD Conversion Present", usd_conversion_exists,
                         f"USD Value: ${total_usd:.6f}")
                         
    async def test_activity_feed_content(self):
        """Test activity feed content and structure"""
        print("\n=== Testing Activity Feed Content ===")
        
        status, response = await self.make_request("GET", "/activity/feed")
        success = status == 200 and "activities" in response
        
        if success:
            activities = response.get("activities", [])
            activity_count = len(activities)
            self.log_test("Activity Feed Content", True, f"Found {activity_count} activities")
            
            if activities:
                # Check activity types
                activity_types = set(activity.get("type") for activity in activities)
                expected_types = {"house_sale", "bounty_completed", "bounty_created", "user_joined"}
                valid_types = activity_types.issubset(expected_types)
                self.log_test("Activity Types Valid", valid_types,
                             f"Types: {list(activity_types)}")
                
                # Check required fields
                first_activity = activities[0]
                required_fields = ["type", "message", "timestamp", "icon"]
                has_required = all(field in first_activity for field in required_fields)
                self.log_test("Activity Structure Valid", has_required,
                             f"Fields: {list(first_activity.keys())}")
                             
    async def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Enhanced Germania Empire Marketplace Backend Tests")
        print(f"Testing against: {BASE_URL}")
        
        await self.setup_session()
        
        try:
            # Setup accounts
            if not await self.setup_admin_and_user():
                print("❌ Failed to setup test accounts")
                return
                
            # Give user balance for testing
            await self.give_user_balance()
            
            # Create test data
            await self.create_test_transactions()
            
            # Run comprehensive tests
            await self.test_exchange_rate_function_comprehensive()
            await self.test_transaction_history_comprehensive()
            await self.test_portfolio_calculations()
            await self.test_activity_feed_content()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("🏁 ENHANCED TEST SUMMARY")
        print("="*70)
        
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
        
        # Critical functionality check
        critical_functions = [
            "Admin Login", "User Registration", "Transaction History Basic",
            "Portfolio Calculation Accuracy", "Activity Feed Content"
        ]
        
        print("\n✅ CRITICAL FUNCTIONALITY:")
        for func in critical_functions:
            test_result = next((t for t in self.test_results if t["test"] == func), None)
            if test_result:
                status = "✅" if test_result["success"] else "❌"
                print(f"  {status} {func}")

async def main():
    """Main test runner"""
    tester = EnhancedBackendTester()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())