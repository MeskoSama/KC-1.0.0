#!/usr/bin/env python3
"""
Final Stock Market Test with Admin User
Tests all stock buying functionality thoroughly
"""

import asyncio
import aiohttp
import json

BASE_URL = "https://world-map-helper.preview.emergentagent.com/api"

class FinalStockTester:
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
        except Exception as e:
            return 500, {"error": str(e)}
            
    async def setup_admin_user(self):
        """Setup admin user with balance"""
        print("\n=== Setting Up Admin User ===")
        
        # Login as TestMiner
        login_data = {
            "minecraft_username": "TestMiner",
            "password": "admin123",
            "server_code": "10997"
        }
        
        status, response = await self.make_request("POST", "/auth/login", login_data, auth=False)
        
        if status == 200:
            self.auth_token = response.get("token")
            self.user_id = response.get("user", {}).get("id")
            user_data = response.get("user", {})
            self.log_test("Login as TestMiner", True, f"User ID: {self.user_id}")
            
            # Add balance for testing
            await self.add_balance_for_testing()
            return True
        else:
            self.log_test("Login as TestMiner", False, f"Status: {status}, Response: {response}")
            return False
            
    async def add_balance_for_testing(self):
        """Add balance for testing"""
        print("\n=== Adding Balance for Testing ===")
        
        currencies = ["GRP", "VDD", "NIM", "KKD"]
        for currency in currencies:
            balance_data = {
                "user_id": self.user_id,
                "currency": currency,
                "amount": 50000.0,
                "operation": "add"
            }
            
            status, response = await self.make_request("PUT", "/admin/user/balance", balance_data)
            if status == 200:
                self.log_test(f"Add {currency} Balance", True, f"Added 50000 {currency}")
            else:
                self.log_test(f"Add {currency} Balance", False, f"Status: {status}")
                
    async def test_investment_listing(self):
        """Test GET /api/investments"""
        print("\n=== Testing Investment Listing ===")
        
        status, response = await self.make_request("GET", "/investments")
        
        if status == 200:
            investments = response.get("investments", [])
            self.log_test("GET /api/investments", True, f"Found {len(investments)} investments")
            
            # Verify 24 stocks
            if len(investments) >= 24:
                self.log_test("Stock Count (≥24)", True, f"Found {len(investments)} stocks")
            else:
                self.log_test("Stock Count (≥24)", False, f"Found {len(investments)} stocks")
            
            # Verify structure
            if investments:
                stock = investments[0]
                required_fields = ["symbol", "name", "current_price", "currency"]
                has_all_fields = all(field in stock for field in required_fields)
                self.log_test("Stock Structure", has_all_fields, f"Fields: {list(stock.keys())}")
                
                # Check for target stocks
                target_stocks = ["VDD-BERLIN-GOV", "NIM-GOV-NE", "GRP-GERMANIA-GOV"]
                found_stocks = [s.get("symbol") for s in investments if s.get("symbol") in target_stocks]
                self.log_test("Target Stocks Available", len(found_stocks) > 0, f"Found: {found_stocks}")
                
            return investments
        else:
            self.log_test("GET /api/investments", False, f"Status: {status}")
            return []
            
    async def test_buying_success_cases(self, investments):
        """Test successful stock purchases"""
        print("\n=== Testing Stock Buying (Success Cases) ===")
        
        if not investments:
            self.log_test("Stock Buying Tests", False, "No investments available")
            return
            
        # Test buying VDD-BERLIN-GOV
        vdd_stock = next((s for s in investments if s.get("symbol") == "VDD-BERLIN-GOV"), None)
        if vdd_stock:
            await self.buy_stock_test(vdd_stock, 1, "VDD-BERLIN-GOV (1 share)")
            
        # Test buying NIM-GOV-NE
        nim_stock = next((s for s in investments if s.get("symbol") == "NIM-GOV-NE"), None)
        if nim_stock:
            await self.buy_stock_test(nim_stock, 1, "NIM-GOV-NE (1 share)")
            
        # Test buying GRP-GERMANIA-GOV
        grp_stock = next((s for s in investments if s.get("symbol") == "GRP-GERMANIA-GOV"), None)
        if grp_stock:
            await self.buy_stock_test(grp_stock, 1, "GRP-GERMANIA-GOV (1 share)")
            
    async def buy_stock_test(self, stock, quantity, test_name):
        """Test buying a specific stock"""
        symbol = stock.get("symbol")
        price = stock.get("current_price")
        currency = stock.get("currency")
        
        # Get current balance
        status, user_response = await self.make_request("GET", "/auth/me")
        if status != 200:
            self.log_test(f"Buy {test_name}", False, "Could not get user balance")
            return False
            
        initial_balance = user_response.get("balances", {}).get(currency, 0)
        
        # Make the purchase
        endpoint = f"/investments/buy?symbol={symbol}&quantity={quantity}"
        status, response = await self.make_request("POST", endpoint, None)
        
        if status == 200:
            transaction = response.get("transaction", {})
            total_amount = transaction.get("total_amount", 0)
            commission = transaction.get("commission", 0)
            final_amount = total_amount + commission
            
            self.log_test(f"Buy {test_name}", True, 
                         f"Total: {total_amount} + Commission: {commission} = {final_amount} {currency}")
            
            # Verify balance deduction
            status, updated_user = await self.make_request("GET", "/auth/me")
            if status == 200:
                new_balance = updated_user.get("balances", {}).get(currency, 0)
                expected_balance = initial_balance - final_amount
                balance_correct = abs(new_balance - expected_balance) < 0.01
                
                self.log_test(f"Balance Deduction - {symbol}", balance_correct,
                             f"Initial: {initial_balance}, New: {new_balance}, Expected: {expected_balance}")
            
            # Verify transaction details
            expected_total = price * quantity
            commission_rate = commission / total_amount if total_amount > 0 else 0
            
            self.log_test(f"Transaction Details - {symbol}", 
                         abs(total_amount - expected_total) < 0.01 and commission > 0,
                         f"Price: {price}, Quantity: {quantity}, Total: {total_amount}, Commission Rate: {commission_rate:.6f}")
            
            return True
        else:
            self.log_test(f"Buy {test_name}", False, f"Status: {status}, Response: {response}")
            return False
            
    async def test_buying_error_cases(self, investments):
        """Test error cases for stock buying"""
        print("\n=== Testing Stock Buying (Error Cases) ===")
        
        if not investments:
            return
            
        # Test insufficient balance
        expensive_stock = max(investments, key=lambda x: x.get("current_price", 0))
        symbol = expensive_stock.get("symbol")
        endpoint = f"/investments/buy?symbol={symbol}&quantity=1000000"
        
        status, response = await self.make_request("POST", endpoint, None)
        
        if status == 400 and "Insufficient balance" in response.get("detail", ""):
            self.log_test("Insufficient Balance Error", True, "Correctly rejected expensive purchase")
        else:
            self.log_test("Insufficient Balance Error", False, f"Status: {status}, Response: {response}")
        
        # Test non-existent stock
        endpoint = "/investments/buy?symbol=NONEXISTENT-STOCK&quantity=1"
        status, response = await self.make_request("POST", endpoint, None)
        
        if status == 404:
            self.log_test("Non-existent Stock Error", True, "Correctly rejected non-existent stock")
        else:
            self.log_test("Non-existent Stock Error", False, f"Status: {status}, Response: {response}")
        
        # Test invalid quantities
        stock = investments[0]
        symbol = stock.get("symbol")
        
        # Negative quantity
        endpoint = f"/investments/buy?symbol={symbol}&quantity=-1"
        status, response = await self.make_request("POST", endpoint, None)
        
        if status == 400:
            self.log_test("Negative Quantity Error", True, "Correctly rejected negative quantity")
        else:
            self.log_test("Negative Quantity Error", False, f"Status: {status}, Response: {response}")
        
        # Zero quantity
        endpoint = f"/investments/buy?symbol={symbol}&quantity=0"
        status, response = await self.make_request("POST", endpoint, None)
        
        if status == 400:
            self.log_test("Zero Quantity Error", True, "Correctly rejected zero quantity")
        else:
            self.log_test("Zero Quantity Error", False, f"Status: {status}, Response: {response}")
            
    async def test_portfolio_view(self):
        """Test portfolio view after purchases"""
        print("\n=== Testing Portfolio View ===")
        
        # Test /auth/me
        status, response = await self.make_request("GET", "/auth/me")
        
        if status == 200:
            portfolio = response.get("portfolio", {})
            has_portfolio_field = "portfolio" in response
            
            if has_portfolio_field:
                self.log_test("Portfolio Field in /auth/me", True, f"Portfolio: {portfolio}")
                
                if portfolio:
                    total_shares = sum(portfolio.values())
                    self.log_test("Portfolio Contains Stocks", total_shares > 0,
                                 f"Total shares: {total_shares}")
                else:
                    self.log_test("Portfolio Contains Stocks", False, "Portfolio is empty")
            else:
                self.log_test("Portfolio Field in /auth/me", False, "Portfolio field missing")
        
        # Test /portfolio/summary
        status, response = await self.make_request("GET", "/portfolio/summary")
        
        if status == 200:
            breakdown = response.get("breakdown", {})
            investments_list = breakdown.get("investments", [])
            
            self.log_test("Portfolio Summary Endpoint", True, f"Found {len(investments_list)} investments")
            
            if investments_list:
                total_value = sum(inv.get("total_value", 0) for inv in investments_list)
                self.log_test("Portfolio Has Value", total_value > 0, f"Total value: {total_value}")
                
                # Verify investment structure
                first_inv = investments_list[0]
                required_fields = ["symbol", "name", "quantity", "current_price", "currency", "total_value"]
                has_required_fields = all(field in first_inv for field in required_fields)
                self.log_test("Investment Structure", has_required_fields, f"Fields: {list(first_inv.keys())}")
        else:
            self.log_test("Portfolio Summary Endpoint", False, f"Status: {status}")
            
    async def test_transaction_history(self):
        """Test transaction history"""
        print("\n=== Testing Transaction History ===")
        
        status, response = await self.make_request("GET", "/transactions/history")
        
        if status == 200:
            transactions = response.get("transactions", [])
            self.log_test("Get Transaction History", True, f"Found {len(transactions)} transactions")
            
            # Look for investment transactions
            investment_txns = [t for t in transactions if t.get("type") == "investment"]
            self.log_test("Investment Transactions Recorded", len(investment_txns) > 0,
                         f"Found {len(investment_txns)} investment transactions")
            
            if investment_txns:
                txn = investment_txns[0]
                details = txn.get("details", {})
                required_fields = ["symbol", "quantity", "price_per_unit", "commission"]
                has_required_fields = all(field in details for field in required_fields)
                
                self.log_test("Transaction Structure", has_required_fields, f"Details: {details}")
        else:
            self.log_test("Get Transaction History", False, f"Status: {status}")
            
    async def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Stock Market Test")
        print(f"Testing against: {BASE_URL}")
        
        await self.setup_session()
        
        try:
            # Setup
            if not await self.setup_admin_user():
                print("❌ Admin setup failed - cannot continue")
                return
                
            # Run tests
            investments = await self.test_investment_listing()
            await self.test_buying_success_cases(investments)
            await self.test_buying_error_cases(investments)
            await self.test_portfolio_view()
            await self.test_transaction_history()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🏁 COMPREHENSIVE STOCK MARKET TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        # Show critical functionality status
        print("\n✅ CRITICAL STOCK MARKET FUNCTIONALITY:")
        critical_tests = [
            "GET /api/investments",
            "Stock Count (≥24)", 
            "Target Stocks Available",
            "Buy VDD-BERLIN-GOV (1 share)",
            "Buy NIM-GOV-NE (1 share)",
            "Buy GRP-GERMANIA-GOV (1 share)",
            "Portfolio Summary Endpoint",
            "Investment Transactions Recorded"
        ]
        
        for test_name in critical_tests:
            test_result = next((t for t in self.test_results if t["test"] == test_name), None)
            if test_result:
                status = "✅" if test_result["success"] else "❌"
                print(f"  {status} {test_name}")

async def main():
    """Main test runner"""
    tester = FinalStockTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())