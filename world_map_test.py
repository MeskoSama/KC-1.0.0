#!/usr/bin/env python3
"""
World Map API Testing Suite
Tests all World Map endpoints as requested in the review
"""

import asyncio
import aiohttp
import json
import math
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://world-map-helper.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "minecraft_username": "meskop",
    "password": "12345678",
    "server_code": "10997"  # GRP server
}

class WorldMapTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
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
        
    async def make_request(self, method, endpoint, data=None, auth=True, params=None):
        """Make HTTP request with optional auth"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if auth and self.admin_token:
            headers["Authorization"] = f"Bearer {self.admin_token}"
            
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers, params=params) as response:
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
            
    async def admin_login(self):
        """Login as admin user"""
        print("\n=== Admin Authentication ===")
        
        status, response = await self.make_request("POST", "/auth/login", ADMIN_CREDENTIALS, auth=False)
        
        if status == 200:
            self.admin_token = response.get("token")
            user_role = response.get("user", {}).get("role", "user")
            is_admin = response.get("user", {}).get("is_admin", False)
            self.log_test("Admin Login", True, f"Role: {user_role}, Admin: {is_admin}")
            return True
        else:
            self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")
            return False
            
    async def test_map_config_endpoint(self):
        """Test GET /api/map/config endpoint"""
        print("\n=== Testing Map Config Endpoint ===")
        
        status, response = await self.make_request("GET", "/map/config", auth=False)
        success = status == 200
        
        if success:
            # Check required fields
            required_fields = ["world_seed", "ore_prices", "marker_types", "states", "unit", "currency"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                self.log_test("Map Config - Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Map Config - Structure", True, "All required fields present")
                
                # Check states have economic_multiplier
                states = response.get("states", {})
                states_with_multiplier = all("economic_multiplier" in state for state in states.values())
                self.log_test("Map Config - States Economic Multiplier", states_with_multiplier,
                             f"States count: {len(states)}")
                
                # Check ore prices structure
                ore_prices = response.get("ore_prices", {})
                self.log_test("Map Config - Ore Prices", len(ore_prices) > 0,
                             f"Ore types: {len(ore_prices)}")
                
                # Check marker types
                marker_types = response.get("marker_types", {})
                self.log_test("Map Config - Marker Types", len(marker_types) > 0,
                             f"Marker types: {len(marker_types)}")
        else:
            self.log_test("Map Config - Basic", False, f"Status: {status}, Response: {response}")
            
    async def test_map_states_endpoint(self):
        """Test GET /api/map/states endpoint"""
        print("\n=== Testing Map States Endpoint ===")
        
        status, response = await self.make_request("GET", "/map/states", auth=False)
        success = status == 200
        
        if success:
            states = response.get("states", {})
            state_count = len(states)
            
            # Should return 5 states
            expected_count = 5
            count_correct = state_count == expected_count
            self.log_test("Map States - Count", count_correct,
                         f"Expected: {expected_count}, Got: {state_count}")
            
            # Each state should have economic_multiplier
            states_with_multiplier = 0
            for state_id, state_data in states.items():
                if "economic_multiplier" in state_data:
                    states_with_multiplier += 1
                    
            all_have_multiplier = states_with_multiplier == state_count
            self.log_test("Map States - Economic Multipliers", all_have_multiplier,
                         f"States with multiplier: {states_with_multiplier}/{state_count}")
        else:
            self.log_test("Map States - Basic", False, f"Status: {status}, Response: {response}")
            
    async def test_map_distance_endpoint(self):
        """Test GET /api/map/distance endpoint"""
        print("\n=== Testing Map Distance Endpoint ===")
        
        # Test distance calculation
        params = {
            "x1": 1000,
            "z1": 1000,
            "x2": 5000,
            "z2": 5000
        }
        
        status, response = await self.make_request("GET", "/map/distance", auth=False, params=params)
        success = status == 200
        
        if success:
            distance_blocks = response.get("distance_blocks")
            distance_km = response.get("distance_km")
            
            if distance_blocks is not None and distance_km is not None:
                # Calculate expected distance: sqrt((5000-1000)^2 + (5000-1000)^2)
                expected_distance = math.sqrt((5000-1000)**2 + (5000-1000)**2)
                distance_correct = abs(distance_blocks - expected_distance) < 1.0  # Allow small floating point differences
                
                self.log_test("Map Distance - Calculation", distance_correct,
                             f"Expected: {expected_distance:.2f}, Got: {distance_blocks} blocks, {distance_km} km")
            else:
                self.log_test("Map Distance - Response Structure", False, 
                             f"Missing distance fields. Response: {response}")
        else:
            self.log_test("Map Distance - Basic", False, f"Status: {status}, Response: {response}")
            
    async def test_territories_endpoint_before_init(self):
        """Test GET /api/map/territories before initialization"""
        print("\n=== Testing Territories Endpoint (Before Init) ===")
        
        status, response = await self.make_request("GET", "/map/territories", auth=False)
        success = status == 200
        
        if success:
            territories = response.get("territories", [])
            self.log_test("Territories - Before Init", True,
                         f"Territories count: {len(territories)} (should be empty or existing)")
        else:
            self.log_test("Territories - Before Init", False, f"Status: {status}, Response: {response}")
            
        return response.get("territories", []) if success else []
        
    async def test_micro_regions_endpoint_before_init(self):
        """Test GET /api/map/micro-regions before initialization"""
        print("\n=== Testing Micro-Regions Endpoint (Before Init) ===")
        
        status, response = await self.make_request("GET", "/map/micro-regions", auth=False)
        success = status == 200
        
        if success:
            micro_regions = response.get("micro_regions", [])
            self.log_test("Micro-Regions - Before Init", True,
                         f"Micro-regions count: {len(micro_regions)} (should be empty or existing)")
        else:
            self.log_test("Micro-Regions - Before Init", False, f"Status: {status}, Response: {response}")
            
        return response.get("micro_regions", []) if success else []
        
    async def test_initialize_world_data(self):
        """Test POST /api/admin/map/initialize-world-data"""
        print("\n=== Testing Initialize World Data ===")
        
        # Test without auth (should fail)
        status, response = await self.make_request("POST", "/admin/map/initialize-world-data", auth=False)
        auth_required = status in [401, 403]
        self.log_test("Initialize World Data - Auth Required", auth_required,
                     f"Status: {status} (expected 401/403)")
        
        # Test with admin auth
        status, response = await self.make_request("POST", "/admin/map/initialize-world-data")
        success = status == 200
        
        if success:
            self.log_test("Initialize World Data - Admin Auth", True,
                         f"Response: {response.get('message', 'Success')}")
        else:
            self.log_test("Initialize World Data - Admin Auth", False,
                         f"Status: {status}, Response: {response}")
            
        return success
        
    async def test_territories_endpoint_after_init(self):
        """Test GET /api/map/territories after initialization"""
        print("\n=== Testing Territories Endpoint (After Init) ===")
        
        status, response = await self.make_request("GET", "/map/territories", auth=False)
        success = status == 200
        
        if success:
            territories = response.get("territories", [])
            territory_count = len(territories)
            
            # Should have 5 territories after initialization
            expected_count = 5
            count_correct = territory_count == expected_count
            self.log_test("Territories - After Init Count", count_correct,
                         f"Expected: {expected_count}, Got: {territory_count}")
            
            # Check territory structure
            if territories:
                first_territory = territories[0]
                required_fields = ["id", "name", "country_id", "color", "polygon"]
                has_required_fields = all(field in first_territory for field in required_fields)
                self.log_test("Territories - Structure", has_required_fields,
                             f"Fields: {list(first_territory.keys())}")
        else:
            self.log_test("Territories - After Init", False, f"Status: {status}, Response: {response}")
            
    async def test_micro_regions_endpoint_after_init(self):
        """Test GET /api/map/micro-regions after initialization"""
        print("\n=== Testing Micro-Regions Endpoint (After Init) ===")
        
        status, response = await self.make_request("GET", "/map/micro-regions", auth=False)
        success = status == 200
        
        if success:
            micro_regions = response.get("micro_regions", [])
            region_count = len(micro_regions)
            
            # Should have 6 micro-regions after initialization
            expected_count = 6
            count_correct = region_count == expected_count
            self.log_test("Micro-Regions - After Init Count", count_correct,
                         f"Expected: {expected_count}, Got: {region_count}")
            
            # Check micro-region structure and mineral data
            if micro_regions:
                first_region = micro_regions[0]
                required_fields = ["region_id", "state", "name", "center", "minerals"]
                has_required_fields = all(field in first_region for field in required_fields)
                self.log_test("Micro-Regions - Structure", has_required_fields,
                             f"Fields: {list(first_region.keys())}")
                
                # Check mineral data structure
                minerals = first_region.get("minerals", {})
                if minerals:
                    first_mineral = list(minerals.values())[0]
                    mineral_fields = ["total", "available", "base_price"]
                    has_mineral_fields = all(field in first_mineral for field in mineral_fields)
                    self.log_test("Micro-Regions - Mineral Data", has_mineral_fields,
                                 f"Mineral types: {len(minerals)}, Sample: {first_mineral}")
                else:
                    self.log_test("Micro-Regions - Mineral Data", False, "No mineral data found")
        else:
            self.log_test("Micro-Regions - After Init", False, f"Status: {status}, Response: {response}")
            
    async def run_all_tests(self):
        """Run all World Map tests"""
        print("🗺️ Starting World Map API Tests")
        print(f"Testing against: {BASE_URL}")
        
        await self.setup_session()
        
        try:
            # Admin authentication
            admin_success = await self.admin_login()
            if not admin_success:
                print("❌ Admin authentication failed - cannot test admin endpoints")
                
            # Test public endpoints
            await self.test_map_config_endpoint()
            await self.test_map_states_endpoint()
            await self.test_map_distance_endpoint()
            
            # Test endpoints before initialization
            territories_before = await self.test_territories_endpoint_before_init()
            micro_regions_before = await self.test_micro_regions_endpoint_before_init()
            
            # Test admin initialization (if admin auth succeeded)
            if admin_success:
                init_success = await self.test_initialize_world_data()
                
                # Test endpoints after initialization
                if init_success:
                    await self.test_territories_endpoint_after_init()
                    await self.test_micro_regions_endpoint_after_init()
                else:
                    print("⚠️ Initialization failed - skipping post-init tests")
            else:
                print("⚠️ Admin auth failed - skipping initialization and post-init tests")
                
        finally:
            await self.cleanup_session()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🏁 WORLD MAP API TEST SUMMARY")
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
        print("\n✅ CRITICAL WORLD MAP FUNCTIONALITY:")
        critical_tests = [
            "Map Config - Structure",
            "Map States - Count", 
            "Map Distance - Calculation",
            "Initialize World Data - Admin Auth",
            "Territories - After Init Count",
            "Micro-Regions - After Init Count"
        ]
        
        for test_name in critical_tests:
            test_result = next((t for t in self.test_results if t["test"] == test_name), None)
            if test_result:
                status = "✅" if test_result["success"] else "❌"
                print(f"  {status} {test_name}")
            else:
                print(f"  ⚪ {test_name} (not run)")

async def main():
    """Main test runner"""
    tester = WorldMapTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())