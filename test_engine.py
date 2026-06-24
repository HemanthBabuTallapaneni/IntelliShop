import unittest
import json
import sqlite3
from app import app, init_db, generate_jwt, verify_jwt, DB_PATH

class TestOrchestrationEngine(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Ensure database is initialised
        init_db()
        cls.client = app.test_client()
        
    def setUp(self):
        # Setup session variables or headers if needed
        self.client = app.test_client()
        self.shopper_token = generate_jwt(1, "shopper1", "shopper")
        self.seller_token = generate_jwt(4, "seller1", "seller")
        self.admin_token = generate_jwt(5, "admin1", "admin")

    def test_jwt_generation_and_verification(self):
        """Test the multi-role security token system."""
        token = generate_jwt(99, "test_user", "shopper")
        payload = verify_jwt(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["username"], "test_user")
        self.assertEqual(payload["role"], "shopper")
        
        # Test signature tampering detection
        parts = token.split('.')
        tampered_token = f"{parts[0]}.{parts[1]}.invalid_signature"
        self.assertIsNone(verify_jwt(tampered_token))

    def test_shopper_dashboard_access(self):
        """Test page access constraints based on roles."""
        # Anonymous user should redirect to login
        response = self.client.get("/shopper")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)
        
        # Authorized shopper should load successfully
        with self.client.session_transaction() as sess:
            sess["jwt_token"] = self.shopper_token
            
        response = self.client.get("/shopper")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Product Catalog", response.data)
        self.assertIn(b"AI Recommender Matrix Feed", response.data)

    def test_seller_dashboard_guard(self):
        """Test route guard blocks shoppers from accessing the merchant dashboard."""
        with self.client.session_transaction() as sess:
            sess["jwt_token"] = self.shopper_token
            
        response = self.client.get("/seller")
        # Should return access denied/unauthorized page
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Access Denied", response.data)

        # Authorized seller should load dashboard
        with self.client.session_transaction() as sess:
            sess["jwt_token"] = self.seller_token
            
        response = self.client.get("/seller")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Merchant BI & Inventory Pipeline", response.data)

    def test_product_details_and_similarities(self):
        """Test details API return schema and Cosine similarity logic."""
        with self.client.session_transaction() as sess:
            sess["jwt_token"] = self.shopper_token
            
        response = self.client.get("/shopper/product/1")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn("id", data)
        self.assertIn("name", data)
        self.assertIn("price", data)
        self.assertIn("inventory", data)
        self.assertIn("similar_products", data)
        self.assertIn("attributes", data)
        
        # Similar products should contain up to 4 items with similarity score
        similar = data["similar_products"]
        self.assertTrue(len(similar) <= 4)
        if len(similar) > 0:
            self.assertIn("similarity", similar[0])
            self.assertIn("image_url", similar[0])

    def test_search_indexing_and_filtering(self):
        """Test sub-second attribute mapping queries."""
        with self.client.session_transaction() as sess:
            sess["jwt_token"] = self.shopper_token
            
        # Test query text search
        response = self.client.get("/shopper?query=Nike")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nike", response.data)
        
        # Test color filter
        response = self.client.get("/shopper?color=Red")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Color: Red", response.data)

    def test_checkout_inventory_mutation(self):
        """Test the live inventory mutation pipeline upon checkout."""
        # 1. Fetch initial stock level of product 1
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("SELECT inventory FROM products WHERE id = 1")
        initial_stock = cursor.fetchone()[0]
        db.close()
        
        # Skip test if item is out of stock (initial seed can vary, but product 1 should have stock)
        if initial_stock <= 0:
            # restock for test
            db = sqlite3.connect(DB_PATH)
            db.cursor().execute("UPDATE products SET inventory = 10 WHERE id = 1")
            db.commit()
            db.close()
            initial_stock = 10

        # 2. Add product 1 to cart
        with self.client.session_transaction() as sess:
            sess["jwt_token"] = self.shopper_token
            sess["cart"] = {"1": 1} # add 1 unit of product 1
            
        # 3. Execute checkout POST
        response = self.client.post("/shopper/checkout")
        self.assertEqual(response.status_code, 302) # should redirect back to dashboard
        
        # 4. Verify stock mutated instantly in SQLite
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("SELECT inventory FROM products WHERE id = 1")
        final_stock = cursor.fetchone()[0]
        db.close()
        
        self.assertEqual(final_stock, initial_stock - 1)

if __name__ == "__main__":
    unittest.main()
