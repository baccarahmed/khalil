import requests
import unittest
import uuid
import time
from datetime import datetime

# Base URL from frontend .env
BASE_URL = "https://aa23fa79-3f16-4319-b81a-556b8621341d.preview.emergentagent.com/api"

class FoodDeliveryAPITest(unittest.TestCase):
    def setUp(self):
        # Generate unique identifiers for test data
        self.test_id = str(uuid.uuid4())[:8]
        self.customer_email = f"customer_{self.test_id}@test.com"
        self.driver_email = f"driver_{self.test_id}@test.com"
        self.restaurant_email = f"restaurant_{self.test_id}@test.com"
        self.admin_email = f"admin_{self.test_id}@test.com"
        
        # Store tokens and IDs
        self.tokens = {}
        self.user_ids = {}
        self.restaurant_id = None
        self.menu_item_id = None
        self.order_id = None

    def test_01_register_users(self):
        """Test user registration for all user types"""
        print("\n🔍 Testing user registration for all user types...")
        
        # Register customer
        customer_data = {
            "email": self.customer_email,
            "name": "Test Customer",
            "phone": "1234567890",
            "user_type": "customer",
            "address": "123 Customer St",
            "location": {"lat": 40.7128, "lng": -74.0060}
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=customer_data)
        self.assertEqual(response.status_code, 200, f"Customer registration failed: {response.text}")
        data = response.json()
        self.tokens["customer"] = data["token"]
        self.user_ids["customer"] = data["user"]["id"]
        print(f"✅ Customer registered successfully with ID: {self.user_ids['customer']}")
        
        # Register driver
        driver_data = {
            "email": self.driver_email,
            "name": "Test Driver",
            "phone": "1234567891",
            "user_type": "driver",
            "location": {"lat": 40.7128, "lng": -74.0060}
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=driver_data)
        self.assertEqual(response.status_code, 200, f"Driver registration failed: {response.text}")
        data = response.json()
        self.tokens["driver"] = data["token"]
        self.user_ids["driver"] = data["user"]["id"]
        print(f"✅ Driver registered successfully with ID: {self.user_ids['driver']}")
        
        # Register restaurant owner
        restaurant_data = {
            "email": self.restaurant_email,
            "name": "Test Restaurant Owner",
            "phone": "1234567892",
            "user_type": "restaurant"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=restaurant_data)
        self.assertEqual(response.status_code, 200, f"Restaurant owner registration failed: {response.text}")
        data = response.json()
        self.tokens["restaurant"] = data["token"]
        self.user_ids["restaurant"] = data["user"]["id"]
        print(f"✅ Restaurant owner registered successfully with ID: {self.user_ids['restaurant']}")
        
        # Register admin
        admin_data = {
            "email": self.admin_email,
            "name": "Test Admin",
            "phone": "1234567893",
            "user_type": "admin"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=admin_data)
        self.assertEqual(response.status_code, 200, f"Admin registration failed: {response.text}")
        data = response.json()
        self.tokens["admin"] = data["token"]
        self.user_ids["admin"] = data["user"]["id"]
        print(f"✅ Admin registered successfully with ID: {self.user_ids['admin']}")

    def test_02_login_users(self):
        """Test login functionality for all user types"""
        print("\n🔍 Testing login functionality for all user types...")
        
        # Login as customer
        login_data = {
            "email": self.customer_email,
            "user_type": "customer"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200, f"Customer login failed: {response.text}")
        print("✅ Customer login successful")
        
        # Login as driver
        login_data = {
            "email": self.driver_email,
            "user_type": "driver"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200, f"Driver login failed: {response.text}")
        print("✅ Driver login successful")
        
        # Login as restaurant owner
        login_data = {
            "email": self.restaurant_email,
            "user_type": "restaurant"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200, f"Restaurant owner login failed: {response.text}")
        print("✅ Restaurant owner login successful")
        
        # Login as admin
        login_data = {
            "email": self.admin_email,
            "user_type": "admin"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200, f"Admin login failed: {response.text}")
        print("✅ Admin login successful")

    def test_03_create_restaurant(self):
        """Test restaurant creation"""
        print("\n🔍 Testing restaurant creation...")
        
        restaurant_data = {
            "name": f"Test Restaurant {self.test_id}",
            "description": "A test restaurant for API testing",
            "address": "123 Test St, Test City",
            "location": {"lat": 40.7128, "lng": -74.0060},
            "cuisine_type": "Test Cuisine",
            "phone": "1234567890",
            "delivery_fee": 3.99,
            "min_order": 15.0,
            "estimated_delivery_time": 30
        }
        
        headers = {"Authorization": f"Bearer {self.tokens['restaurant']}"}
        response = requests.post(f"{BASE_URL}/restaurants", json=restaurant_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Restaurant creation failed: {response.text}")
        data = response.json()
        self.restaurant_id = data["id"]
        print(f"✅ Restaurant created successfully with ID: {self.restaurant_id}")

    def test_04_get_restaurants(self):
        """Test getting all restaurants"""
        print("\n🔍 Testing get all restaurants...")
        
        response = requests.get(f"{BASE_URL}/restaurants")
        self.assertEqual(response.status_code, 200, f"Get restaurants failed: {response.text}")
        restaurants = response.json()
        self.assertIsInstance(restaurants, list, "Response should be a list of restaurants")
        print(f"✅ Retrieved {len(restaurants)} restaurants successfully")

    def test_05_get_restaurant(self):
        """Test getting a specific restaurant"""
        print("\n🔍 Testing get specific restaurant...")
        
        if not self.restaurant_id:
            self.skipTest("Restaurant ID not available")
        
        response = requests.get(f"{BASE_URL}/restaurants/{self.restaurant_id}")
        self.assertEqual(response.status_code, 200, f"Get restaurant failed: {response.text}")
        restaurant = response.json()
        self.assertEqual(restaurant["id"], self.restaurant_id, "Restaurant ID mismatch")
        print(f"✅ Retrieved restaurant {self.restaurant_id} successfully")

    def test_06_add_menu_item(self):
        """Test adding a menu item to a restaurant"""
        print("\n🔍 Testing add menu item...")
        
        if not self.restaurant_id:
            self.skipTest("Restaurant ID not available")
        
        menu_item_data = {
            "name": f"Test Item {self.test_id}",
            "description": "A delicious test item",
            "price": 12.99,
            "category": "Test Category",
            "preparation_time": 15
        }
        
        headers = {"Authorization": f"Bearer {self.tokens['restaurant']}"}
        response = requests.post(f"{BASE_URL}/restaurants/{self.restaurant_id}/menu", json=menu_item_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Add menu item failed: {response.text}")
        data = response.json()
        self.menu_item_id = data["id"]
        print(f"✅ Menu item added successfully with ID: {self.menu_item_id}")

    def test_07_get_menu(self):
        """Test getting a restaurant's menu"""
        print("\n🔍 Testing get restaurant menu...")
        
        if not self.restaurant_id:
            self.skipTest("Restaurant ID not available")
        
        response = requests.get(f"{BASE_URL}/restaurants/{self.restaurant_id}/menu")
        self.assertEqual(response.status_code, 200, f"Get menu failed: {response.text}")
        menu = response.json()
        self.assertIsInstance(menu, list, "Response should be a list of menu items")
        print(f"✅ Retrieved {len(menu)} menu items successfully")

    def test_08_create_order(self):
        """Test creating an order"""
        print("\n🔍 Testing create order...")
        
        if not self.restaurant_id or not self.menu_item_id:
            self.skipTest("Restaurant ID or Menu Item ID not available")
        
        order_data = {
            "restaurant_id": self.restaurant_id,
            "items": [
                {
                    "menu_item_id": self.menu_item_id,
                    "quantity": 2,
                    "special_instructions": "Extra spicy"
                }
            ],
            "delivery_address": "456 Customer St, Test City",
            "delivery_location": {"lat": 40.7129, "lng": -74.0061},
            "special_instructions": "Leave at door"
        }
        
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        response = requests.post(f"{BASE_URL}/orders", json=order_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Create order failed: {response.text}")
        data = response.json()
        self.order_id = data["order"]["id"]
        print(f"✅ Order created successfully with ID: {self.order_id}")
        print(f"✅ Payment intent created with client_secret: {data['client_secret'][:20]}...")

    def test_09_get_orders(self):
        """Test getting orders for different user types"""
        print("\n🔍 Testing get orders for different user types...")
        
        # Customer orders
        headers = {"Authorization": f"Bearer {self.tokens['customer']}"}
        response = requests.get(f"{BASE_URL}/orders", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get customer orders failed: {response.text}")
        customer_orders = response.json()
        print(f"✅ Retrieved {len(customer_orders)} customer orders successfully")
        
        # Restaurant orders
        headers = {"Authorization": f"Bearer {self.tokens['restaurant']}"}
        response = requests.get(f"{BASE_URL}/orders", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get restaurant orders failed: {response.text}")
        restaurant_orders = response.json()
        print(f"✅ Retrieved {len(restaurant_orders)} restaurant orders successfully")
        
        # Driver orders
        headers = {"Authorization": f"Bearer {self.tokens['driver']}"}
        response = requests.get(f"{BASE_URL}/orders", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get driver orders failed: {response.text}")
        driver_orders = response.json()
        print(f"✅ Retrieved {len(driver_orders)} driver orders successfully")
        
        # Admin orders
        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        response = requests.get(f"{BASE_URL}/orders", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get admin orders failed: {response.text}")
        admin_orders = response.json()
        print(f"✅ Retrieved {len(admin_orders)} admin orders successfully")

    def test_10_update_order_status(self):
        """Test updating order status"""
        print("\n🔍 Testing update order status...")
        
        if not self.order_id:
            self.skipTest("Order ID not available")
        
        # Restaurant confirms order
        headers = {"Authorization": f"Bearer {self.tokens['restaurant']}"}
        response = requests.put(f"{BASE_URL}/orders/{self.order_id}/status?status=confirmed", headers=headers)
        self.assertEqual(response.status_code, 200, f"Update order status to confirmed failed: {response.text}")
        print("✅ Order status updated to confirmed successfully")
        
        # Restaurant prepares order
        response = requests.put(f"{BASE_URL}/orders/{self.order_id}/status?status=preparing", headers=headers)
        self.assertEqual(response.status_code, 200, f"Update order status to preparing failed: {response.text}")
        print("✅ Order status updated to preparing successfully")
        
        # Restaurant marks order as ready
        response = requests.put(f"{BASE_URL}/orders/{self.order_id}/status?status=ready", headers=headers)
        self.assertEqual(response.status_code, 200, f"Update order status to ready failed: {response.text}")
        print("✅ Order status updated to ready successfully")

    def test_11_assign_driver(self):
        """Test assigning a driver to an order"""
        print("\n🔍 Testing assign driver to order...")
        
        if not self.order_id:
            self.skipTest("Order ID not available")
        
        headers = {"Authorization": f"Bearer {self.tokens['driver']}"}
        response = requests.post(f"{BASE_URL}/orders/{self.order_id}/assign-driver", headers=headers)
        self.assertEqual(response.status_code, 200, f"Assign driver failed: {response.text}")
        print("✅ Driver assigned to order successfully")

    def test_12_driver_update_order_status(self):
        """Test driver updating order status"""
        print("\n🔍 Testing driver update order status...")
        
        if not self.order_id:
            self.skipTest("Order ID not available")
        
        # Driver picks up order
        headers = {"Authorization": f"Bearer {self.tokens['driver']}"}
        response = requests.put(f"{BASE_URL}/orders/{self.order_id}/status?status=picked_up", headers=headers)
        self.assertEqual(response.status_code, 200, f"Update order status to picked_up failed: {response.text}")
        print("✅ Order status updated to picked_up successfully")
        
        # Driver delivers order
        response = requests.put(f"{BASE_URL}/orders/{self.order_id}/status?status=delivered", headers=headers)
        self.assertEqual(response.status_code, 200, f"Update order status to delivered failed: {response.text}")
        print("✅ Order status updated to delivered successfully")

    def test_13_update_driver_location(self):
        """Test updating driver location"""
        print("\n🔍 Testing update driver location...")
        
        location_data = {"lat": 40.7130, "lng": -74.0062}
        headers = {"Authorization": f"Bearer {self.tokens['driver']}"}
        response = requests.post(f"{BASE_URL}/drivers/location", json=location_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Update driver location failed: {response.text}")
        print("✅ Driver location updated successfully")

    def test_14_admin_analytics(self):
        """Test admin analytics endpoint"""
        print("\n🔍 Testing admin analytics...")
        
        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        response = requests.get(f"{BASE_URL}/analytics", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get analytics failed: {response.text}")
        analytics = response.json()
        self.assertIn("total_orders", analytics, "Analytics should include total_orders")
        self.assertIn("total_users", analytics, "Analytics should include total_users")
        self.assertIn("total_restaurants", analytics, "Analytics should include total_restaurants")
        self.assertIn("total_revenue", analytics, "Analytics should include total_revenue")
        print("✅ Admin analytics retrieved successfully")

if __name__ == "__main__":
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add tests in order
    test_suite.addTest(FoodDeliveryAPITest('test_01_register_users'))
    test_suite.addTest(FoodDeliveryAPITest('test_02_login_users'))
    test_suite.addTest(FoodDeliveryAPITest('test_03_create_restaurant'))
    test_suite.addTest(FoodDeliveryAPITest('test_04_get_restaurants'))
    test_suite.addTest(FoodDeliveryAPITest('test_05_get_restaurant'))
    test_suite.addTest(FoodDeliveryAPITest('test_06_add_menu_item'))
    test_suite.addTest(FoodDeliveryAPITest('test_07_get_menu'))
    test_suite.addTest(FoodDeliveryAPITest('test_08_create_order'))
    test_suite.addTest(FoodDeliveryAPITest('test_09_get_orders'))
    test_suite.addTest(FoodDeliveryAPITest('test_10_update_order_status'))
    test_suite.addTest(FoodDeliveryAPITest('test_11_assign_driver'))
    test_suite.addTest(FoodDeliveryAPITest('test_12_driver_update_order_status'))
    test_suite.addTest(FoodDeliveryAPITest('test_13_update_driver_location'))
    test_suite.addTest(FoodDeliveryAPITest('test_14_admin_analytics'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
