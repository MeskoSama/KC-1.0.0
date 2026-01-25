#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://world-map-helper.preview.emergentagent.com/api"
ADMIN_USERNAME = "meskop"
ADMIN_PASSWORD = "12345678"

class ServerAccountsAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
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
            # First register admin if not exists (will fail if exists, that's ok)
            register_data = {
                "minecraft_username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
                "server_code": "10997"  # GRP server code
            }
            
            register_response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
            
            # Now login
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

    def get_headers(self, auth_required=False):
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if auth_required and self.admin_token:
            headers["Authorization"] = f"Bearer {self.admin_token}"
        return headers

    def test_accounts_config(self):
        """Test GET /api/accounts/config"""
        try:
            response = self.session.get(f"{BASE_URL}/accounts/config")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["banks", "card_types", "currencies", "ranking_colors"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "GET /api/accounts/config", 
                        False, 
                        error=f"Missing fields: {missing_fields}"
                    )
                    return False
                
                # Check banks
                banks = data.get("banks", {})
                expected_banks = ["germania_bank", "sakura_bank", "veltronia_national_bank", "cordoba_bank", "sumerbank"]
                actual_banks = list(banks.keys())
                
                if not all(bank in actual_banks for bank in expected_banks):
                    self.log_test(
                        "GET /api/accounts/config", 
                        False, 
                        error=f"Expected banks {expected_banks}, got {actual_banks}"
                    )
                    return False
                
                # Check each bank has home_currency
                for bank_id, bank_info in banks.items():
                    if "home_currency" not in bank_info:
                        self.log_test(
                            "GET /api/accounts/config", 
                            False, 
                            error=f"Bank {bank_id} missing home_currency"
                        )
                        return False
                
                # Check card types
                card_types = data.get("card_types", [])
                expected_card_types = ["credit", "debit", "government", "platinum", "gold", "investor"]
                if not all(ct in card_types for ct in expected_card_types):
                    self.log_test(
                        "GET /api/accounts/config", 
                        False, 
                        error=f"Missing card types. Expected: {expected_card_types}, Got: {card_types}"
                    )
                    return False
                
                # Check currencies
                currencies = data.get("currencies", [])
                expected_currencies = ["GRP", "NIM", "VDD", "KKD", "EGD", "EP"]
                if not all(curr in currencies for curr in expected_currencies):
                    self.log_test(
                        "GET /api/accounts/config", 
                        False, 
                        error=f"Missing currencies. Expected: {expected_currencies}, Got: {currencies}"
                    )
                    return False
                
                # Check ranking colors
                ranking_colors = data.get("ranking_colors", {})
                expected_ranks = ["1", "2", "3"]
                if not all(rank in ranking_colors for rank in expected_ranks):
                    self.log_test(
                        "GET /api/accounts/config", 
                        False, 
                        error=f"Missing ranking colors for ranks: {expected_ranks}"
                    )
                    return False
                
                self.log_test(
                    "GET /api/accounts/config", 
                    True, 
                    f"Config returned with {len(banks)} banks, {len(card_types)} card types, {len(currencies)} currencies"
                )
                return True
                
            else:
                self.log_test(
                    "GET /api/accounts/config", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("GET /api/accounts/config", False, error=str(e))
            return False

    def test_accounts_empty_initially(self):
        """Test GET /api/accounts returns empty initially"""
        try:
            response = self.session.get(f"{BASE_URL}/accounts")
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get("accounts", [])
                total_count = data.get("total_count", 0)
                
                self.log_test(
                    "GET /api/accounts (initial)", 
                    True, 
                    f"Found {len(accounts)} accounts, total_count: {total_count}"
                )
                return len(accounts)
                
            else:
                self.log_test(
                    "GET /api/accounts (initial)", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return -1
                
        except Exception as e:
            self.log_test("GET /api/accounts (initial)", False, error=str(e))
            return -1

    def test_initialize_sample_accounts(self):
        """Test POST /api/admin/accounts/initialize"""
        try:
            headers = self.get_headers(auth_required=True)
            response = self.session.post(f"{BASE_URL}/admin/accounts/initialize", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                
                self.log_test(
                    "POST /api/admin/accounts/initialize", 
                    True, 
                    f"Response: {message}"
                )
                return True
                
            elif response.status_code == 403:
                self.log_test(
                    "POST /api/admin/accounts/initialize", 
                    False, 
                    error="Admin authentication failed - user may not have admin privileges"
                )
                return False
                
            else:
                self.log_test(
                    "POST /api/admin/accounts/initialize", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("POST /api/admin/accounts/initialize", False, error=str(e))
            return False

    def test_accounts_after_initialization(self):
        """Test GET /api/accounts after initialization"""
        try:
            response = self.session.get(f"{BASE_URL}/accounts")
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get("accounts", [])
                total_count = data.get("total_count", 0)
                
                # Check for expected accounts (bot1, bot2, bot3)
                expected_usernames = ["bot1", "bot2", "bot3"]
                found_usernames = [acc.get("username") for acc in accounts]
                
                missing_accounts = [name for name in expected_usernames if name not in found_usernames]
                
                if missing_accounts:
                    self.log_test(
                        "GET /api/accounts (after init)", 
                        False, 
                        error=f"Missing expected accounts: {missing_accounts}. Found: {found_usernames}"
                    )
                    return False
                
                # Check wealth ranking
                for i, account in enumerate(accounts):
                    expected_rank = i + 1
                    actual_rank = account.get("rank")
                    
                    if actual_rank != expected_rank:
                        self.log_test(
                            "GET /api/accounts (after init)", 
                            False, 
                            error=f"Account {account.get('username')} has rank {actual_rank}, expected {expected_rank}"
                        )
                        return False
                    
                    # Check total_wealth is calculated
                    if "total_wealth" not in account:
                        self.log_test(
                            "GET /api/accounts (after init)", 
                            False, 
                            error=f"Account {account.get('username')} missing total_wealth"
                        )
                        return False
                
                self.log_test(
                    "GET /api/accounts (after init)", 
                    True, 
                    f"Found {len(accounts)} accounts with proper wealth ranking. Accounts: {found_usernames}"
                )
                return accounts
                
            else:
                self.log_test(
                    "GET /api/accounts (after init)", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_test("GET /api/accounts (after init)", False, error=str(e))
            return []

    def test_get_specific_account(self, accounts):
        """Test GET /api/accounts/{account_id}"""
        if not accounts:
            self.log_test("GET /api/accounts/{id}", False, error="No accounts available for testing")
            return False
            
        try:
            # Test with first account
            account = accounts[0]
            account_id = account.get("id")
            username = account.get("username")
            
            response = self.session.get(f"{BASE_URL}/accounts/{account_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["id", "username", "bank_accounts", "total_wealth"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "GET /api/accounts/{id}", 
                        False, 
                        error=f"Missing fields: {missing_fields}"
                    )
                    return False
                
                # Check bank accounts structure
                bank_accounts = data.get("bank_accounts", [])
                if not bank_accounts:
                    self.log_test(
                        "GET /api/accounts/{id}", 
                        False, 
                        error="No bank accounts found"
                    )
                    return False
                
                # Check bank account structure
                for bank_acc in bank_accounts:
                    if "bank_id" not in bank_acc or "cards" not in bank_acc:
                        self.log_test(
                            "GET /api/accounts/{id}", 
                            False, 
                            error="Invalid bank account structure"
                        )
                        return False
                    
                    # Check cards structure
                    for card in bank_acc.get("cards", []):
                        required_card_fields = ["id", "card_type"]
                        missing_card_fields = [field for field in required_card_fields if field not in card]
                        if missing_card_fields:
                            self.log_test(
                                "GET /api/accounts/{id}", 
                                False, 
                                error=f"Card missing fields: {missing_card_fields}"
                            )
                            return False
                
                self.log_test(
                    "GET /api/accounts/{id}", 
                    True, 
                    f"Account {username} details retrieved with {len(bank_accounts)} bank accounts"
                )
                return True
                
            elif response.status_code == 404:
                self.log_test(
                    "GET /api/accounts/{id}", 
                    False, 
                    error="Account not found"
                )
                return False
                
            else:
                self.log_test(
                    "GET /api/accounts/{id}", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("GET /api/accounts/{id}", False, error=str(e))
            return False

    def test_create_new_account(self):
        """Test POST /api/admin/accounts"""
        try:
            headers = self.get_headers(auth_required=True)
            
            # Create test account data
            account_data = {
                "username": "test_account_" + str(int(datetime.now().timestamp())),
                "bank_accounts": [
                    {
                        "bank_id": "germania_bank",
                        "cards": [
                            {
                                "card_type": "debit",
                                "balances": {"GRP": 1000, "NIM": 0, "VDD": 0, "KKD": 0, "EGD": 0, "EP": 0},
                                "foreign_currencies_opened": []
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.post(f"{BASE_URL}/admin/accounts", json=account_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                account_id = data.get("account_id")
                
                if account_id:
                    self.log_test(
                        "POST /api/admin/accounts", 
                        True, 
                        f"Created account {account_data['username']} with ID {account_id}"
                    )
                    return account_id
                else:
                    self.log_test(
                        "POST /api/admin/accounts", 
                        False, 
                        error="No account_id returned"
                    )
                    return None
                    
            elif response.status_code == 403:
                self.log_test(
                    "POST /api/admin/accounts", 
                    False, 
                    error="Admin authentication failed"
                )
                return None
                
            else:
                self.log_test(
                    "POST /api/admin/accounts", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("POST /api/admin/accounts", False, error=str(e))
            return None

    def test_add_bank_to_account(self, account_id):
        """Test POST /api/admin/accounts/{id}/bank"""
        if not account_id:
            self.log_test("POST /api/admin/accounts/{id}/bank", False, error="No account ID provided")
            return False
            
        try:
            headers = self.get_headers(auth_required=True)
            
            # Add sakura_bank to the account
            bank_data = {
                "bank_id": "sakura_bank",
                "cards": [
                    {
                        "card_type": "credit",
                        "debt": {"GRP": 0, "NIM": 500, "VDD": 0, "KKD": 0, "EGD": 0, "EP": 0},
                        "foreign_currencies_opened": ["NIM"]
                    }
                ]
            }
            
            response = self.session.post(f"{BASE_URL}/admin/accounts/{account_id}/bank", json=bank_data, headers=headers)
            
            if response.status_code == 200:
                self.log_test(
                    "POST /api/admin/accounts/{id}/bank", 
                    True, 
                    f"Added {bank_data['bank_id']} to account {account_id}"
                )
                return True
                
            elif response.status_code == 404:
                self.log_test(
                    "POST /api/admin/accounts/{id}/bank", 
                    False, 
                    error="Account not found"
                )
                return False
                
            elif response.status_code == 403:
                self.log_test(
                    "POST /api/admin/accounts/{id}/bank", 
                    False, 
                    error="Admin authentication failed"
                )
                return False
                
            else:
                self.log_test(
                    "POST /api/admin/accounts/{id}/bank", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("POST /api/admin/accounts/{id}/bank", False, error=str(e))
            return False

    def test_update_card_balance(self, account_id):
        """Test PUT /api/admin/accounts/{id}/balance"""
        if not account_id:
            self.log_test("PUT /api/admin/accounts/{id}/balance", False, error="No account ID provided")
            return False
            
        try:
            headers = self.get_headers(auth_required=True)
            
            # Update balance for germania_bank debit card
            balance_data = {
                "bank_id": "germania_bank",
                "card_type": "debit",
                "currency": "GRP",
                "amount": 2500,
                "operation": "set"
            }
            
            response = self.session.put(f"{BASE_URL}/admin/accounts/{account_id}/balance", json=balance_data, headers=headers)
            
            if response.status_code == 200:
                self.log_test(
                    "PUT /api/admin/accounts/{id}/balance", 
                    True, 
                    f"Updated {balance_data['currency']} balance to {balance_data['amount']} for account {account_id}"
                )
                return True
                
            elif response.status_code == 404:
                self.log_test(
                    "PUT /api/admin/accounts/{id}/balance", 
                    False, 
                    error="Account, bank, or card not found"
                )
                return False
                
            elif response.status_code == 403:
                self.log_test(
                    "PUT /api/admin/accounts/{id}/balance", 
                    False, 
                    error="Admin authentication failed"
                )
                return False
                
            else:
                self.log_test(
                    "PUT /api/admin/accounts/{id}/balance", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("PUT /api/admin/accounts/{id}/balance", False, error=str(e))
            return False

    def run_all_tests(self):
        """Run all Server Accounts API tests"""
        print("🏦 SERVER ACCOUNTS API TESTING")
        print("=" * 50)
        print()
        
        # Step 1: Authenticate as admin
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return self.generate_summary()
        
        # Step 2: Test accounts config
        self.test_accounts_config()
        
        # Step 3: Test accounts list (initially empty or existing)
        initial_count = self.test_accounts_empty_initially()
        
        # Step 4: Initialize sample accounts
        if self.test_initialize_sample_accounts():
            # Step 5: Test accounts after initialization
            accounts = self.test_accounts_after_initialization()
            
            # Step 6: Test getting specific account
            self.test_get_specific_account(accounts)
        
        # Step 7: Test creating new account
        new_account_id = self.test_create_new_account()
        
        # Step 8: Test adding bank to account
        if new_account_id:
            self.test_add_bank_to_account(new_account_id)
            
            # Step 9: Test updating card balance
            self.test_update_card_balance(new_account_id)
        
        return self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 50)
        print("🏦 SERVER ACCOUNTS API TEST SUMMARY")
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
        
        # Check if config endpoint works
        config_test = next((r for r in self.test_results if "config" in r["test"]), None)
        if config_test and config_test["success"]:
            print("  ✅ Banking configuration endpoint working")
        else:
            print("  ❌ Banking configuration endpoint failed")
        
        # Check if initialization works
        init_test = next((r for r in self.test_results if "initialize" in r["test"]), None)
        if init_test and init_test["success"]:
            print("  ✅ Sample accounts initialization working")
        else:
            print("  ❌ Sample accounts initialization failed")
        
        # Check if accounts listing works
        accounts_test = next((r for r in self.test_results if "after init" in r["test"]), None)
        if accounts_test and accounts_test["success"]:
            print("  ✅ Accounts listing with wealth ranking working")
        else:
            print("  ❌ Accounts listing with wealth ranking failed")
        
        # Check if CRUD operations work
        create_test = next((r for r in self.test_results if "POST /api/admin/accounts" in r["test"] and "initialize" not in r["test"]), None)
        if create_test and create_test["success"]:
            print("  ✅ Account creation working")
        else:
            print("  ❌ Account creation failed")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0,
            "all_passed": failed_tests == 0
        }

def main():
    """Main function"""
    tester = ServerAccountsAPITester()
    summary = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if summary["all_passed"] else 1)

if __name__ == "__main__":
    main()