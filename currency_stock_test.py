#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://world-map-helper.preview.emergentagent.com/api"
ADMIN_USERNAME = "meskop"
ADMIN_PASSWORD = "12345678"

class CurrencyStockTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.user_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def authenticate_admin(self):
        """Authenticate as admin user"""
        try:
            login_data = {
                "minecraft_username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
                "server_code": "10997"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                user_info = data.get("user", {})
                is_admin = user_info.get("is_admin", False) or user_info.get("role") in ["admin", "superadmin"]
                
                self.log_test(
                    "Admin Authentication", 
                    True, 
                    f"Logged in as {ADMIN_USERNAME}, Admin status: {is_admin}"
                )
                return True
            else:
                self.log_test(
                    "Admin Authentication", 
                    False, 
                    error=f"Login failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, error=str(e))
            return False

    def create_test_user(self):
        """Create and authenticate test user"""
        try:
            # Create test user
            user_data = {
                "minecraft_username": f"TestUser_{int(datetime.now().timestamp())}",
                "password": "TestPassword123",
                "server_code": "10997"  # GRP server
            }
            
            # Register
            response = self.session.post(f"{BASE_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get("token")
                user_info = data.get("user", {})
                
                self.log_test(
                    "Test User Creation", 
                    True, 
                    f"Created user {user_info.get('username')} with ID {user_info.get('id')}"
                )
                return user_info
            else:
                self.log_test(
                    "Test User Creation", 
                    False, 
                    error=f"Registration failed: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Test User Creation", False, error=str(e))
            return None

    def get_headers(self, admin=False):
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if admin and self.admin_token:
            headers["Authorization"] = f"Bearer {self.admin_token}"
        elif not admin and self.user_token:
            headers["Authorization"] = f"Bearer {self.user_token}"
        return headers

    def test_currency_endpoints(self):
        """Test currency management endpoints"""
        try:
            # Test GET /api/currencies (public)
            response = self.session.get(f"{BASE_URL}/currencies")
            
            if response.status_code == 200:
                data = response.json()
                currencies = data.get("currencies", [])
                expected_currencies = ["NIM", "GRP", "VDD", "KKD", "EP", "EGD"]
                
                if all(curr in currencies for curr in expected_currencies):
                    self.log_test(
                        "GET /api/currencies", 
                        True, 
                        f"Found all expected currencies: {currencies}"
                    )
                else:
                    self.log_test(
                        "GET /api/currencies", 
                        False, 
                        error=f"Missing currencies. Expected: {expected_currencies}, Got: {currencies}"
                    )
                    return False
            else:
                self.log_test(
                    "GET /api/currencies", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Test GET /api/currencies/rates (public)
            response = self.session.get(f"{BASE_URL}/currencies/rates")
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                
                # Check for key exchange rates
                key_rates = ["GRP_TO_NIM", "GRP_TO_VDD", "GRP_TO_KKD", "GRP_TO_EP", "GRP_TO_EGD"]
                missing_rates = [rate for rate in key_rates if rate not in rates]
                
                if not missing_rates:
                    self.log_test(
                        "GET /api/currencies/rates", 
                        True, 
                        f"Found {len(rates)} exchange rates including EP and EGD"
                    )
                else:
                    self.log_test(
                        "GET /api/currencies/rates", 
                        False, 
                        error=f"Missing exchange rates: {missing_rates}"
                    )
                    return False
            else:
                self.log_test(
                    "GET /api/currencies/rates", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Currency Endpoints Test", False, error=str(e))
            return False

    def test_admin_currency_endpoints(self):
        """Test admin currency management endpoints"""
        try:
            headers = self.get_headers(admin=True)
            
            # Test POST /api/admin/currencies/initialize
            response = self.session.post(f"{BASE_URL}/admin/currencies/initialize", headers=headers)
            
            if response.status_code == 200:
                self.log_test(
                    "POST /api/admin/currencies/initialize", 
                    True, 
                    "Currency initialization successful"
                )
            else:
                self.log_test(
                    "POST /api/admin/currencies/initialize", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Test PUT /api/admin/exchange-rate/direct
            rate_update = {
                "from_currency": "GRP",
                "to_currency": "EP",
                "rate": 112.5055
            }
            
            response = self.session.put(f"{BASE_URL}/admin/exchange-rate/direct", json=rate_update, headers=headers)
            
            if response.status_code == 200:
                self.log_test(
                    "PUT /api/admin/exchange-rate/direct", 
                    True, 
                    f"Updated {rate_update['from_currency']} to {rate_update['to_currency']} rate"
                )
            else:
                self.log_test(
                    "PUT /api/admin/exchange-rate/direct", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Admin Currency Endpoints Test", False, error=str(e))
            return False

    def test_stock_endpoints(self):
        """Test stock buy/sell endpoints with JSON body"""
        try:
            headers = self.get_headers(admin=False)
            
            # First, get available investments
            response = self.session.get(f"{BASE_URL}/investments")
            
            if response.status_code != 200:
                self.log_test(
                    "GET /api/investments", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            investments = response.json()
            if not investments:
                self.log_test(
                    "Stock Endpoints Test", 
                    False, 
                    error="No investments available for testing"
                )
                return False
            
            # Find a stock to test with
            test_stock = investments[0]
            stock_symbol = test_stock.get("symbol")
            stock_price = test_stock.get("current_price", 0)
            
            self.log_test(
                "GET /api/investments", 
                True, 
                f"Found {len(investments)} investments, testing with {stock_symbol}"
            )
            
            # Test buy endpoint with JSON body (should fail due to insufficient balance, but endpoint should work)
            buy_order = {
                "symbol": stock_symbol,
                "quantity": 1
            }
            
            response = self.session.post(f"{BASE_URL}/investments/buy", json=buy_order, headers=headers)
            
            # We expect this to fail due to insufficient balance, but the endpoint should accept JSON
            if response.status_code == 400:
                response_data = response.json()
                if "insufficient" in response_data.get("detail", "").lower():
                    self.log_test(
                        "POST /api/investments/buy (JSON body)", 
                        True, 
                        "Endpoint accepts JSON body correctly (insufficient balance expected)"
                    )
                else:
                    self.log_test(
                        "POST /api/investments/buy (JSON body)", 
                        False, 
                        error=f"Unexpected error: {response_data.get('detail')}"
                    )
                    return False
            elif response.status_code == 200:
                self.log_test(
                    "POST /api/investments/buy (JSON body)", 
                    True, 
                    "Stock purchase successful"
                )
            else:
                self.log_test(
                    "POST /api/investments/buy (JSON body)", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Stock Endpoints Test", False, error=str(e))
            return False

    def test_user_balance_migration(self):
        """Test user balance migration for EP/EGD currencies"""
        try:
            headers = self.get_headers(admin=True)
            
            # Test POST /api/admin/users/migrate-balances
            response = self.session.post(f"{BASE_URL}/admin/users/migrate-balances", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "POST /api/admin/users/migrate-balances", 
                    True, 
                    f"Migration response: {data.get('message', 'Success')}"
                )
                return True
            else:
                self.log_test(
                    "POST /api/admin/users/migrate-balances", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("User Balance Migration Test", False, error=str(e))
            return False

    def run_all_tests(self):
        """Run all currency and stock tests"""
        print("💰 CURRENCY & STOCK API TESTING")
        print("=" * 50)
        print()
        
        # Step 1: Authenticate as admin
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return self.generate_summary()
        
        # Step 2: Create test user
        test_user = self.create_test_user()
        if not test_user:
            print("❌ Cannot proceed without test user")
            return self.generate_summary()
        
        # Step 3: Test currency endpoints
        self.test_currency_endpoints()
        
        # Step 4: Test admin currency endpoints
        self.test_admin_currency_endpoints()
        
        # Step 5: Test stock endpoints
        self.test_stock_endpoints()
        
        # Step 6: Test user balance migration
        self.test_user_balance_migration()
        
        return self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 50)
        print("💰 CURRENCY & STOCK API TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['error']}")
            print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        
        # Check currency endpoints
        currency_test = next((r for r in self.test_results if "GET /api/currencies" in r["test"]), None)
        if currency_test and currency_test["success"]:
            print("  ✅ Currency listing endpoints working (EP and EGD included)")
        else:
            print("  ❌ Currency listing endpoints failed")
        
        # Check stock endpoints
        stock_test = next((r for r in self.test_results if "investments/buy" in r["test"]), None)
        if stock_test and stock_test["success"]:
            print("  ✅ Stock buy/sell endpoints accept JSON body correctly")
        else:
            print("  ❌ Stock buy/sell endpoints failed")
        
        # Check admin endpoints
        admin_test = next((r for r in self.test_results if "admin/currencies" in r["test"]), None)
        if admin_test and admin_test["success"]:
            print("  ✅ Admin currency management working")
        else:
            print("  ❌ Admin currency management failed")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0,
            "all_passed": failed_tests == 0
        }

def main():
    """Main function"""
    tester = CurrencyStockTester()
    summary = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if summary["all_passed"] else 1)

if __name__ == "__main__":
    main()