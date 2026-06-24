import os
import time
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = "static/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def run_web_tests():
    with sync_playwright() as p:
        print("Launching headless Chromium browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        # 1. Test Login Page
        print("Navigating to Login Page...")
        page.goto("http://127.0.0.1:5000/login")
        page.wait_for_timeout(1000)
        login_img = os.path.join(SCREENSHOT_DIR, "login.png")
        page.screenshot(path=login_img)
        print(f"Login page screenshot saved to {login_img}")
        
        # 2. Test Shopper Dashboard & Login
        print("Logging in as shopper1...")
        page.click("text=@shopper1") # autofills
        page.click("button:has-text('Authenticate')")
        page.wait_for_url("**/shopper")
        page.wait_for_timeout(1000)
        
        shopper_img = os.path.join(SCREENSHOT_DIR, "shopper_dashboard.png")
        page.screenshot(path=shopper_img)
        print(f"Shopper dashboard screenshot saved to {shopper_img}")
        
        # 3. Test Product Details Modal
        print("Opening product details modal...")
        # Click on the first product card (using a class selector or title text)
        page.locator(".product-card").first.click()
        page.wait_for_selector("#productDetailsModal.show")
        page.wait_for_timeout(1500) # let transition finish and similar items load
        
        modal_img = os.path.join(SCREENSHOT_DIR, "product_modal.png")
        page.screenshot(path=modal_img)
        print(f"Product details modal screenshot saved to {modal_img}")
        
        # Close modal
        page.click("#productDetailsModal .btn-close")
        page.wait_for_timeout(500)
        
        # 4. Test Seller Dashboard (BI & charts)
        print("Logging out shopper...")
        page.goto("http://127.0.0.1:5000/logout")
        page.wait_for_url("**/login")
        
        print("Logging in as seller1...")
        page.click("text=@seller1")
        page.click("button:has-text('Authenticate')")
        page.wait_for_url("**/seller")
        page.wait_for_timeout(2500) # let Chart.js animations complete
        
        seller_img = os.path.join(SCREENSHOT_DIR, "seller_dashboard.png")
        page.screenshot(path=seller_img)
        print(f"Seller dashboard screenshot saved to {seller_img}")
        
        # 5. Test Admin Portal
        print("Logging out seller...")
        page.goto("http://127.0.0.1:5000/logout")
        page.wait_for_url("**/login")
        
        print("Logging in as admin1...")
        page.click("text=@admin1")
        page.click("button:has-text('Authenticate')")
        page.wait_for_url("**/admin")
        page.wait_for_timeout(1000)
        
        admin_img = os.path.join(SCREENSHOT_DIR, "admin_dashboard.png")
        page.screenshot(path=admin_img)
        print(f"Admin portal screenshot saved to {admin_img}")
        
        browser.close()
        print("Web testing sequence completed successfully. All page views verified.")

if __name__ == "__main__":
    run_web_tests()
