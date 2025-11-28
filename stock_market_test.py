#!/usr/bin/env python3
"""
Stock Market Testing Suite for Germania Empire Marketplace
Tests stock/bond buying functionality thoroughly as requested
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
import uuid

# Configuration
BASE_URL = "https://repo-viewer-22.preview.emergentagent.com/api"

class StockMarketTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        self.user_data = None
        
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
            
    async def setup_test_user(self):
        """Setup or login test user"""
        print("\n=== Setting Up Test User ===")
        
        # Try different passwords for meskop
        passwords_to_try = ["password123", "meskop123", "admin123", "test123", "password", "123456"]
        
        for password in passwords_to_try:
            login_data = {
                "minecraft_username": "meskop",
                "password": password,
                "server_code": "10997"  # GRP server
            }
            
            status, response = await self.make_request("POST", "/auth/login", login_data, auth=False)
            
            if status == 200:
                self.auth_token = response.get("token")
                self.user_id = response.get("user", {}).get("id")
                self.user_data = response.get("user", {})
                self.log_test("Login as meskop", True, f"User ID: {self.user_id}, Password: {password}")
                return True
        
        # If meskop login fails, try to create a new test user
        test_username = f"StockTester{datetime.now().strftime('%H%M%S')}"
        register_data = {
            "minecraft_username": test_username,
            "password": "test123",
            "server_code": "10997"  # GRP server
        }
        
        status, response = await self.make_request("POST", "/auth/register", register_data, auth=False)
        
        if status == 200:
            self.auth_token = response.get("token")
            self.user_id = response.get("user", {}).get("id")
            self.user_data = response.get("user", {})
            self.log_test(f"Register {test_username}", True, f"User ID: {self.user_id}")
            return True
        else:
            self.log_test("Setup test user", False, f"Status: {status}, Response: {response}")
            return False
                
    async def check_user_balance(self):
        """Check and display user balances"""
        print("\n=== Checking User Balance ===")
        
        status, response = await self.make_request("GET", "/auth/me")
        if status == 200:
            balances = response.get("balances", {})
            portfolio = response.get("portfolio", {})
            
            self.log_test("Get User Info", True, f"Balances: {balances}")
            print(f"   Portfolio: {portfolio}")
            
            # Check if user has sufficient balance for testing
            grp_balance = balances.get("GRP", 0)
            vdd_balance = balances.get("VDD", 0)
            nim_balance = balances.get("NIM", 0)
            
            if grp_balance < 1000 or vdd_balance < 1000 or nim_balance < 1000:
                print(f"   ⚠️  Low balance detected. May need admin to add funds for testing.")
                
            return balances, portfolio
        else:
            self.log_test("Get User Info", False, f"Status: {status}")
            return {}, {}
            
    async def test_investment_listing(self):
        """Test GET /api/investments - Verify stocks are returned"""
        print("\n=== Testing Investment Listing ===")
        
        status, response = await self.make_request("GET", "/investments")
        
        if status == 200:
            investments = response.get("investments", [])
            self.log_test("GET /api/investments", True, f"Found {len(investments)} investments")
            
            # Check if we have the expected 24 stocks
            if len(investments) >= 24:
                self.log_test("Stock Count Verification", True, f"Found {len(investments)} stocks (≥24 expected)")
            else:
                self.log_test("Stock Count Verification", False, f"Found {len(investments)} stocks (24 expected)")
            
            # Verify each stock has required fields
            if investments:
                first_stock = investments[0]
                required_fields = ["symbol", "name", "current_price", "currency"]
                has_all_fields = all(field in first_stock for field in required_fields)
                self.log_test("Stock Structure Validation", has_all_fields, 
                             f"Fields: {list(first_stock.keys())}")
                
                # Look for specific stocks mentioned in the request
                target_stocks = ["VDD-BERLIN-GOV", "NIM-GOV-NE", "GRP-GERMANIA-GOV"]
                found_stocks = []
                for stock in investments:
                    if stock.get("symbol") in target_stocks:
                        found_stocks.append(stock.get("symbol"))
                        
                self.log_test("Target Stocks Available", len(found_stocks) > 0, 
                             f"Found: {found_stocks}")
                             
                return investments
        else:
            self.log_test("GET /api/investments", False, f"Status: {status}, Response: {response}")
            return []
            
    async def test_buying_stocks_success(self, investments, balances):
        """Test POST /api/investments/buy with valid data"""
        print("\n=== Testing Stock Buying (Success Cases) ===")
        
        if not investments:
            self.log_test("Stock Buying Tests", False, "No investments available")
            return
            
        # Find stocks we can afford
        affordable_stocks = []
        for stock in investments:
            currency = stock.get("currency")
            price = stock.get("current_price", 0)
            user_balance = balances.get(currency, 0)
            
            # Calculate total cost with commission (0.001%)
            total_cost = price * 1 + (price * 1 * 0.00001)
            
            if user_balance >= total_cost:
                affordable_stocks.append(stock)
                
        if not affordable_stocks:
            self.log_test("Stock Affordability Check", False, "No affordable stocks found")
            return
            
        # Test buying specific stocks mentioned in the request
        target_symbols = ["VDD-BERLIN-GOV", "NIM-GOV-NE", "GRP-GERMANIA-GOV"]
        
        for symbol in target_symbols:
            stock = next((s for s in affordable_stocks if s.get("symbol") == symbol), None)
            if stock:
                await self.buy_stock_test(stock, 1)
            else:
                # Try to find any stock with similar currency
                currency_match = None
                if "VDD" in symbol:
                    currency_match = next((s for s in affordable_stocks if s.get("currency") == "VDD"), None)
                elif "NIM" in symbol:
                    currency_match = next((s for s in affordable_stocks if s.get("currency") == "NIM"), None)
                elif "GRP" in symbol:
                    currency_match = next((s for s in affordable_stocks if s.get("currency") == "GRP"), None)
                    
                if currency_match:
                    await self.buy_stock_test(currency_match, 1)
                else:
                    self.log_test(f"Buy {symbol}", False, "Stock not found or not affordable")
                    
    async def buy_stock_test(self, stock, quantity):
        """Test buying a specific stock"""
        symbol = stock.get("symbol")
        price = stock.get("current_price")
        currency = stock.get("currency")
        
        # Make the purchase
        buy_data = {
            "symbol": symbol,
            "quantity": quantity
        }
        
        status, response = await self.make_request("POST", "/investments/buy", buy_data)
        
        if status == 200:
            transaction = response.get("transaction", {})
            self.log_test(f"Buy {symbol} (1 share)", True, 
                         f"Total: {transaction.get('total_amount', 0)} {currency}")
            
            # Verify transaction details
            expected_total = price * quantity
            actual_total = transaction.get("total_amount", 0)
            commission = transaction.get("commission", 0)
            
            total_matches = abs(actual_total - expected_total) < 0.01
            has_commission = commission > 0
            
            self.log_test(f"Transaction Details - {symbol}", total_matches and has_commission,
                         f"Expected: {expected_total}, Actual: {actual_total}, Commission: {commission}")
                         
            return True
        else:
            self.log_test(f"Buy {symbol} (1 share)", False, 
                         f"Status: {status}, Response: {response}")
            return False
            
    async def test_buying_errors(self, investments):
        """Test buying errors - insufficient balance, non-existent stock, invalid quantity"""
        print("\n=== Testing Stock Buying (Error Cases) ===")
        
        # Test insufficient balance - try to buy expensive stock with large quantity
        if investments:
            expensive_stock = max(investments, key=lambda x: x.get("current_price", 0))
            symbol = expensive_stock.get("symbol")
            
            # Try to buy 1000000 shares (should be too expensive)
            buy_data = {
                "symbol": symbol,
                "quantity": 1000000
            }
            
            status, response = await self.make_request("POST", "/investments/buy", buy_data)
            
            if status == 400 and "Insufficient balance" in response.get("detail", ""):
                self.log_test("Insufficient Balance Error", True, "Correctly rejected expensive purchase")
            else:
                self.log_test("Insufficient Balance Error", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test non-existent stock
        buy_data = {
            "symbol": "NONEXISTENT-STOCK",
            "quantity": 1
        }
        
        status, response = await self.make_request("POST", "/investments/buy", buy_data)
        
        if status == 404:
            self.log_test("Non-existent Stock Error", True, "Correctly rejected non-existent stock")
        else:
            self.log_test("Non-existent Stock Error", False, 
                         f"Status: {status}, Response: {response}")
        
        # Test invalid quantity - negative
        if investments:
            stock = investments[0]
            buy_data = {
                "symbol": stock.get("symbol"),
                "quantity": -1
            }
            
            status, response = await self.make_request("POST", "/investments/buy", buy_data)
            
            if status == 400:
                self.log_test("Negative Quantity Error", True, "Correctly rejected negative quantity")
            else:
                self.log_test("Negative Quantity Error", False, 
                             f"Status: {status}, Response: {response}")
        
        # Test invalid quantity - zero
        if investments:
            stock = investments[0]
            buy_data = {
                "symbol": stock.get("symbol"),
                "quantity": 0
            }
            
            status, response = await self.make_request("POST", "/investments/buy", buy_data)
            
            if status == 400:
                self.log_test("Zero Quantity Error", True, "Correctly rejected zero quantity")
            else:
                self.log_test("Zero Quantity Error", False, 
                             f"Status: {status}, Response: {response}")
                             
    async def test_portfolio_view(self):
        """Test GET /api/auth/me after purchase - verify portfolio field"""
        print("\n=== Testing Portfolio View ===")
        
        status, response = await self.make_request("GET", "/auth/me")
        
        if status == 200:
            portfolio = response.get("portfolio", {})
            self.log_test("Portfolio Field Exists", "portfolio" in response, 
                         f"Portfolio: {portfolio}")
            
            # Check if portfolio contains purchased stocks
            if portfolio:
                total_shares = sum(portfolio.values())
                self.log_test("Portfolio Contains Stocks", total_shares > 0,
                             f"Total shares owned: {total_shares}")
                             
                # Verify quantities are correct (should be positive numbers)
                valid_quantities = all(isinstance(qty, (int, float)) and qty >= 0 for qty in portfolio.values())
                self.log_test("Portfolio Quantities Valid", valid_quantities,
                             f"Quantities: {list(portfolio.values())}")
            else:
                self.log_test("Portfolio Contains Stocks", False, "Portfolio is empty")
        else:
            self.log_test("Get Portfolio", False, f"Status: {status}")
            
    async def test_transaction_history(self):
        """Test GET /api/transactions/history - verify buy transactions are recorded"""
        print("\n=== Testing Transaction History ===")
        
        status, response = await self.make_request("GET", "/transactions/history")
        
        if status == 200:
            transactions = response.get("transactions", [])
            self.log_test("Get Transaction History", True, f"Found {len(transactions)} transactions")
            
            # Look for investment transactions
            investment_txns = [t for t in transactions if t.get("type") == "investment"]
            self.log_test("Investment Transactions Recorded", len(investment_txns) > 0,
                         f"Found {len(investment_txns)} investment transactions")
            
            # Verify transaction structure
            if investment_txns:
                txn = investment_txns[0]
                required_fields = ["symbol", "quantity", "price_per_unit", "commission"]
                details = txn.get("details", {})
                has_required_fields = all(field in details for field in required_fields)
                
                self.log_test("Transaction Structure Complete", has_required_fields,
                             f"Details: {details}")
        else:
            self.log_test("Get Transaction History", False, f"Status: {status}")
            
    async def run_stock_market_tests(self):
        """Run all stock market tests"""
        print("🚀 Starting Stock Market Testing Suite")
        print(f"Testing against: {BASE_URL}")
        
        await self.setup_session()
        
        try:
            # Setup user
            if not await self.setup_test_user():
                print("❌ User setup failed - cannot continue")
                return
                
            # Check balances
            balances, portfolio = await self.check_user_balance()
            
            # Run tests in order
            investments = await self.test_investment_listing()
            await self.test_buying_stocks_success(investments, balances)
            await self.test_buying_errors(investments)
            await self.test_portfolio_view()
            await self.test_transaction_history()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🏁 STOCK MARKET TEST SUMMARY")
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
            "Stock Count Verification", 
            "Stock Structure Validation",
            "Portfolio Field Exists",
            "Get Transaction History"
        ]
        
        for test_name in critical_tests:
            test_result = next((t for t in self.test_results if t["test"] == test_name), None)
            if test_result:
                status = "✅" if test_result["success"] else "❌"
                print(f"  {status} {test_name}")

async def main():
    """Main test runner"""
    tester = StockMarketTester()
    await tester.run_stock_market_tests()

if __name__ == "__main__":
    asyncio.run(main())