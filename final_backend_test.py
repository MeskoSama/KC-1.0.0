#!/usr/bin/env python3
"""
Final Germania Empire Marketplace Backend Testing Suite
Focused testing of new improvements without admin requirements
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
    "minecraft_username": f"TestUser{uuid.uuid4().hex[:8]}",
    "password": "SecurePassword123!",
    "server_code": "10997"  # GRP server
}

class FinalBackendTester:
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
            
    def log_test(self, test_name, success, details="", critical=False):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        critical_marker = " [CRITICAL]" if critical else ""
        print(f"{status} {test_name}{critical_marker}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "critical": critical
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
        except Exception as e:
            return 500, {"error": str(e)}
            
    async def test_authentication_flow(self):
        """Test complete authentication flow"""
        print("\n=== Testing Authentication Flow ===")
        
        # Test registration
        status, response = await self.make_request("POST", "/auth/register", TEST_USER_DATA, auth=False)
        
        if status == 200:
            self.auth_token = response.get("token")
            self.user_id = response.get("user", {}).get("id")
            self.log_test("User Registration", True, f"User ID: {self.user_id}", critical=True)
        else:
            self.log_test("User Registration", False, f"Status: {status}, Response: {response}", critical=True)
            return False
            
        # Test /auth/me endpoint
        status, response = await self.make_request("GET", "/auth/me")
        success = status == 200 and "username" in response
        self.log_test("Get Current User (/auth/me)", success, 
                     f"Username: {response.get('username', 'N/A')}" if success else f"Status: {status}", 
                     critical=True)
        
        return True
        
    async def test_get_exchange_rate_implementation(self):
        """Test the get_exchange_rate function implementation"""
        print("\n=== Testing Exchange Rate Function Implementation ===")
        
        # Get currency rates to understand the system
        status, response = await self.make_request("GET", "/marketplace/currency-rates", auth=False)
        if status != 200:
            self.log_test("Get Currency Rates", False, f"Status: {status}", critical=True)
            return
            
        rates = response.get("rates", {})
        self.log_test("Get Currency Rates", True, f"Available rates: {list(rates.keys())}", critical=True)
        
        # Test that GRP is base currency (all rates should be GRP_TO_X format)
        grp_base_correct = all(rate_key.startswith("GRP_TO_") for rate_key in rates.keys() if rate_key != "GRP_TO_USD")
        self.log_test("GRP as Base Currency", grp_base_correct, 
                     f"Rate keys: {list(rates.keys())}", critical=True)
        
        # Verify expected currency rates exist
        expected_rates = ["GRP_TO_NIM", "GRP_TO_VDD", "GRP_TO_KKD", "GRP_TO_USD"]
        has_all_rates = all(rate in rates for rate in expected_rates)
        self.log_test("All Required Exchange Rates Present", has_all_rates,
                     f"Missing: {[r for r in expected_rates if r not in rates]}", critical=True)
                     
    async def test_transaction_history_endpoint(self):
        """Test new /api/transactions/history endpoint"""
        print("\n=== Testing Transaction History Endpoint ===")
        
        # Test without auth (should fail with 401 or 403)
        status, response = await self.make_request("GET", "/transactions/history", auth=False)
        auth_protected = status in [401, 403]
        self.log_test("Transaction History - Auth Protection", auth_protected, 
                     f"Status: {status} (expected 401/403)", critical=True)
        
        # Test with valid token
        status, response = await self.make_request("GET", "/transactions/history")
        success = status == 200 and "transactions" in response
        transaction_count = len(response.get("transactions", []))
        self.log_test("Transaction History - With Auth", success,
                     f"Status: {status}, Transactions: {transaction_count}", critical=True)
        
        if success:
            # Verify response structure
            required_fields = ["transactions", "total", "limit", "skip"]
            has_structure = all(field in response for field in required_fields)
            self.log_test("Transaction History Response Structure", has_structure,
                         f"Fields: {list(response.keys())}")
            
            # Test filtering parameters
            filter_types = ["payment", "investment", "property", "bounty_create", "bounty_complete"]
            for filter_type in filter_types:
                status, filtered_response = await self.make_request("GET", f"/transactions/history?transaction_type={filter_type}")
                filter_works = status == 200 and "transactions" in filtered_response
                self.log_test(f"Transaction Filter - {filter_type}", filter_works,
                             f"Count: {len(filtered_response.get('transactions', []))}")
            
            # Test pagination
            status, paginated_response = await self.make_request("GET", "/transactions/history?skip=0&limit=5")
            pagination_works = status == 200 and len(paginated_response.get("transactions", [])) <= 5
            self.log_test("Transaction History Pagination", pagination_works,
                         f"Returned: {len(paginated_response.get('transactions', []))} (max 5)")
                         
    async def test_activity_feed_endpoint(self):
        """Test new /api/activity/feed endpoint"""
        print("\n=== Testing Activity Feed Endpoint ===")
        
        # Test basic functionality (no auth required)
        status, response = await self.make_request("GET", "/activity/feed", auth=False)
        success = status == 200 and "activities" in response
        activity_count = len(response.get("activities", []))
        self.log_test("Activity Feed - Basic Access", success,
                     f"Status: {status}, Activities: {activity_count}", critical=True)
        
        if success:
            # Verify response structure
            required_fields = ["activities", "total"]
            has_structure = all(field in response for field in required_fields)
            self.log_test("Activity Feed Response Structure", has_structure,
                         f"Fields: {list(response.keys())}")
            
            # Verify activity structure if activities exist
            activities = response.get("activities", [])
            if activities:
                first_activity = activities[0]
                required_activity_fields = ["type", "message", "timestamp", "icon"]
                activity_structure_valid = all(field in first_activity for field in required_activity_fields)
                self.log_test("Activity Structure Validation", activity_structure_valid,
                             f"Activity fields: {list(first_activity.keys())}")
            
            # Test pagination
            status, paginated_response = await self.make_request("GET", "/activity/feed?skip=0&limit=3", auth=False)
            pagination_works = status == 200 and len(paginated_response.get("activities", [])) <= 3
            self.log_test("Activity Feed Pagination", pagination_works,
                         f"Returned: {len(paginated_response.get('activities', []))} (max 3)")
                         
    async def test_portfolio_summary_endpoint(self):
        """Test new /api/portfolio/summary endpoint"""
        print("\n=== Testing Portfolio Summary Endpoint ===")
        
        # Test without auth (should fail with 401 or 403)
        status, response = await self.make_request("GET", "/portfolio/summary", auth=False)
        auth_protected = status in [401, 403]
        self.log_test("Portfolio Summary - Auth Protection", auth_protected,
                     f"Status: {status} (expected 401/403)", critical=True)
        
        # Test with valid token
        status, response = await self.make_request("GET", "/portfolio/summary")
        success = status == 200 and "net_worth" in response
        self.log_test("Portfolio Summary - With Auth", success,
                     f"Status: {status}", critical=True)
        
        if success:
            # Verify net_worth structure
            net_worth = response.get("net_worth", {})
            required_net_worth_fields = ["total_grp", "total_usd", "currency_value", "investments_value", "properties_value"]
            has_net_worth_structure = all(field in net_worth for field in required_net_worth_fields)
            self.log_test("Portfolio Net Worth Structure", has_net_worth_structure,
                         f"Net worth GRP: {net_worth.get('total_grp', 0)}, USD: ${net_worth.get('total_usd', 0):.6f}")
            
            # Verify breakdown structure
            breakdown = response.get("breakdown", {})
            required_breakdown_fields = ["currencies", "investments", "properties"]
            has_breakdown_structure = all(field in breakdown for field in required_breakdown_fields)
            self.log_test("Portfolio Breakdown Structure", has_breakdown_structure,
                         f"Breakdown sections: {list(breakdown.keys())}")
            
            # Verify stats structure
            stats = response.get("stats", {})
            required_stats_fields = ["total_spent", "total_transactions", "owned_ranks", "owned_houses", "active_investments"]
            has_stats_structure = all(field in stats for field in required_stats_fields)
            self.log_test("Portfolio Stats Structure", has_stats_structure,
                         f"Stats: {stats}")
                         
    async def test_existing_marketplace_functionality(self):
        """Test that existing marketplace endpoints still work"""
        print("\n=== Testing Existing Marketplace Functionality ===")
        
        # Test currency rates
        status, response = await self.make_request("GET", "/marketplace/currency-rates", auth=False)
        success = status == 200 and "rates" in response
        self.log_test("Marketplace Currency Rates", success, f"Status: {status}")
        
        # Test rank prices
        status, response = await self.make_request("GET", "/marketplace/rank-prices", auth=False)
        success = status == 200 and "ranks" in response
        self.log_test("Marketplace Rank Prices", success, f"Status: {status}")
        
        # Test houses endpoint
        status, response = await self.make_request("GET", "/houses", auth=False)
        success = status == 200 and "houses" in response
        houses_count = len(response.get("houses", []))
        self.log_test("Houses Listing Endpoint", success, f"Status: {status}, Houses: {houses_count}")
        
        # Test bounties endpoint
        status, response = await self.make_request("GET", "/bounties", auth=False)
        success = status == 200 and "bounties" in response
        bounties_count = len(response.get("bounties", []))
        self.log_test("Bounties Listing Endpoint", success, f"Status: {status}, Bounties: {bounties_count}")
        
        # Test investments endpoint
        status, response = await self.make_request("GET", "/investments")
        success = status == 200 and "investments" in response
        self.log_test("Investments Listing Endpoint", success, f"Status: {status}")
        
    async def test_house_purchase_endpoint_structure(self):
        """Test house purchase endpoint structure (without actually purchasing)"""
        print("\n=== Testing House Purchase Endpoint Structure ===")
        
        # Get available houses
        status, response = await self.make_request("GET", "/houses", auth=False)
        if status != 200:
            self.log_test("House Purchase Test Setup", False, "Cannot get houses list")
            return
            
        houses = response.get("houses", [])
        available_houses = [h for h in houses if h.get("status") == "available"]
        
        if not available_houses:
            self.log_test("House Purchase Endpoint Test", True, "No available houses (expected for new system)")
            return
            
        # Test the endpoint exists and responds properly (even if purchase fails)
        house_id = available_houses[0].get("id")
        status, response = await self.make_request("POST", f"/houses/{house_id}/buy?payment_type=currency&payment_currency=GRP")
        
        # We expect either success, insufficient balance, or house not available
        endpoint_works = status in [200, 400, 404]
        expected_errors = ["Insufficient balance", "House not available", "House not found"]
        error_is_expected = any(error in response.get("detail", "") for error in expected_errors)
        
        success = endpoint_works and (status == 200 or error_is_expected)
        self.log_test("House Purchase Endpoint Structure", success,
                     f"Status: {status}, Response indicates endpoint works correctly")
                     
    async def run_final_tests(self):
        """Run all final tests"""
        print("🚀 Starting Final Germania Empire Marketplace Backend Tests")
        print(f"Testing against: {BASE_URL}")
        print(f"Test user: {TEST_USER_DATA['minecraft_username']}")
        
        await self.setup_session()
        
        try:
            # Setup authentication
            auth_success = await self.test_authentication_flow()
            if not auth_success:
                print("❌ Authentication failed - cannot continue with authenticated tests")
                return
                
            # Run all tests focusing on new improvements
            await self.test_get_exchange_rate_implementation()
            await self.test_transaction_history_endpoint()
            await self.test_activity_feed_endpoint()
            await self.test_portfolio_summary_endpoint()
            await self.test_existing_marketplace_functionality()
            await self.test_house_purchase_endpoint_structure()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("🏁 FINAL BACKEND TEST SUMMARY - Germania Empire Marketplace")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        critical_tests = [r for r in self.test_results if r.get("critical", False)]
        critical_passed = sum(1 for r in critical_tests if r["success"])
        critical_total = len(critical_tests)
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"\n🔥 CRITICAL FUNCTIONALITY:")
        print(f"   Critical Tests: {critical_total}")
        print(f"   Critical Passed: {critical_passed}")
        print(f"   Critical Success Rate: {(critical_passed/critical_total)*100:.1f}%")
        
        # Show critical test results
        print(f"\n✅ CRITICAL TEST RESULTS:")
        for test in critical_tests:
            status = "✅" if test["success"] else "❌"
            print(f"   {status} {test['test']}")
        
        # Show failed tests
        failed_test_results = [result for result in self.test_results if not result["success"]]
        if failed_test_results:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_test_results:
                print(f"   - {test['test']}: {test['details']}")
        
        # Final assessment
        print(f"\n🎯 NEW FEATURES ASSESSMENT:")
        new_features = [
            ("Exchange Rate Function", "Get Currency Rates"),
            ("Transaction History API", "Transaction History - With Auth"),
            ("Activity Feed API", "Activity Feed - Basic Access"),
            ("Portfolio Summary API", "Portfolio Summary - With Auth")
        ]
        
        for feature_name, test_name in new_features:
            test_result = next((t for t in self.test_results if t["test"] == test_name), None)
            if test_result:
                status = "✅ WORKING" if test_result["success"] else "❌ FAILED"
                print(f"   {status} {feature_name}")
        
        # Overall system health
        system_healthy = critical_passed == critical_total and passed_tests >= (total_tests * 0.8)
        health_status = "🟢 HEALTHY" if system_healthy else "🟡 NEEDS ATTENTION" if passed_tests >= (total_tests * 0.6) else "🔴 CRITICAL ISSUES"
        print(f"\n🏥 SYSTEM HEALTH: {health_status}")

async def main():
    """Main test runner"""
    tester = FinalBackendTester()
    await tester.run_final_tests()

if __name__ == "__main__":
    asyncio.run(main())