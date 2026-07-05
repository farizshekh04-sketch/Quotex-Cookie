# ============================================================
# QUOTEX COOKIE EXTRACTOR - Python + Selenium
# ============================================================

import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import os

# ============================================================
# CONFIGURATION
# ============================================================

class QuotexCookieExtractor:
    def __init__(self, headless=False):
        """Initialize the cookie extractor"""
        self.driver = None
        self.headless = headless
        self.cookies_file = "quotex_cookies.json"
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Disable automation flag
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Execute script to hide automation
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return self.driver
    
    def login_quotex(self, email, password):
        """
        Login to Quotex
        """
        try:
            print("🌐 Navigating to Quotex...")
            self.driver.get("https://market-qx.trade/en/sign-in")
            
            # Wait for login page to load
            wait = WebDriverWait(self.driver, 20)
            
            # Find and fill email
            print("📧 Entering email...")
            email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']")))
            email_input.clear()
            email_input.send_keys(email)
            
            # Find and fill password
            print("🔑 Entering password...")
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_input.clear()
            password_input.send_keys(password)
            
            # Click login button
            print("🔄 Clicking login button...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            if "trade" in self.driver.current_url or "dashboard" in self.driver.current_url:
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed. Please check credentials.")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def extract_cookies(self):
        """
        Extract all cookies from current session
        """
        try:
            cookies = self.driver.get_cookies()
            
            # Convert to dictionary format
            cookie_dict = {}
            for cookie in cookies:
                cookie_dict[cookie['name']] = cookie['value']
            
            return cookie_dict
            
        except Exception as e:
            print(f"❌ Error extracting cookies: {e}")
            return {}
    
    def save_cookies(self, cookies, filename=None):
        """
        Save cookies to file
        """
        if filename is None:
            filename = self.cookies_file
            
        data = {
            'timestamp': datetime.now().isoformat(),
            'url': self.driver.current_url,
            'cookies': cookies,
            'count': len(cookies)
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Cookies saved to {filename}")
        return filename
    
    def load_cookies(self, filename=None):
        """
        Load cookies from file
        """
        if filename is None:
            filename = self.cookies_file
            
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            return data.get('cookies', {})
        except FileNotFoundError:
            print(f"❌ File {filename} not found")
            return {}
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {filename}")
            return {}
    
    def add_cookies_to_session(self, cookies):
        """
        Add cookies to current session
        """
        try:
            for name, value in cookies.items():
                self.driver.add_cookie({'name': name, 'value': value})
            print(f"✅ Added {len(cookies)} cookies to session")
            return True
        except Exception as e:
            print(f"❌ Error adding cookies: {e}")
            return False
    
    def display_cookies(self, cookies):
        """
        Display cookies in a readable format
        """
        print("\n" + "="*60)
        print("🍪 QUOTEX COOKIES")
        print("="*60)
        print(f"📊 Total: {len(cookies)} cookies found")
        print("-"*60)
        
        for idx, (name, value) in enumerate(cookies.items(), 1):
            # Check if it's a JWT token
            is_jwt = value.count('.') == 2 and len(value) > 50
            
            # Truncate long values
            display_value = value
            if len(value) > 100:
                display_value = value[:100] + "..."
            
            print(f"{idx:2}. {name}")
            print(f"   Value: {display_value}")
            if is_jwt:
                print(f"   🔐 JWT Token detected")
            print("-"*60)
    
    def decode_jwt(self, token):
        """
        Decode JWT token (simple decode without verification)
        """
        try:
            import base64
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode payload
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
            
        except Exception as e:
            return f"Error decoding: {e}"
    
    def auto_extract(self, email=None, password=None, wait_time=10):
        """
        Automated extraction process
        """
        if email and password:
            if not self.login_quotex(email, password):
                return None
        
        print("⏳ Waiting for page to load...")
        time.sleep(wait_time)
        
        cookies = self.extract_cookies()
        if cookies:
            self.display_cookies(cookies)
            filename = self.save_cookies(cookies)
            return cookies
        else:
            print("❌ No cookies found")
            return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("🔒 Browser closed")

# ============================================================
# COOKIE INJECTOR - Use saved cookies to login
# ============================================================

class QuotexCookieInjector:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver
    
    def inject_cookies(self, cookies_file="quotex_cookies.json"):
        """
        Inject cookies to login automatically
        """
        try:
            # Load cookies
            with open(cookies_file, 'r') as f:
                data = json.load(f)
                cookies = data.get('cookies', {})
            
            if not cookies:
                print("❌ No cookies found in file")
                return False
            
            # Navigate to Quotex
            print("🌐 Navigating to Quotex...")
            self.driver.get("https://quotex.io/en/trade")
            time.sleep(3)
            
            # Add cookies
            for name, value in cookies.items():
                self.driver.add_cookie({'name': name, 'value': value})
            
            # Refresh page
            self.driver.refresh()
            time.sleep(3)
            
            print(f"✅ Injected {len(cookies)} cookies")
            return True
            
        except Exception as e:
            print(f"❌ Error injecting cookies: {e}")
            return False

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    print("="*60)
    print("🍪 QUOTEX COOKIE EXTRACTOR")
    print("="*60)
    
    # Choose mode
    print("\nSelect mode:")
    print("1. Extract cookies (login required)")
    print("2. Inject cookies (use saved cookies)")
    print("3. View saved cookies")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        # Extract mode
        email = input("Enter your Quotex email: ").strip()
        password = input("Enter your Quotex password: ").strip()
        
        extractor = QuotexCookieExtractor(headless=False)
        try:
            extractor.setup_driver()
            cookies = extractor.auto_extract(email, password, wait_time=10)
            
            if cookies:
                print("\n✅ Extraction complete!")
                
                # Ask if user wants to decode JWT
                decode = input("\nDecode JWT tokens? (y/n): ").strip().lower()
                if decode == 'y':
                    for name, value in cookies.items():
                        if value.count('.') == 2:
                            print(f"\n🔐 Decoding {name}:")
                            decoded = extractor.decode_jwt(value)
                            print(json.dumps(decoded, indent=2))
        finally:
            extractor.close()
            
    elif choice == "2":
        # Inject mode
        injector = QuotexCookieInjector()
        try:
            injector.setup_driver()
            injector.inject_cookies()
            input("\nPress Enter to close browser...")
        finally:
            injector.driver.quit()
            
    elif choice == "3":
        # View saved cookies
        try:
            with open("quotex_cookies.json", 'r') as f:
                data = json.load(f)
                
            print("\n" + "="*60)
            print("📋 SAVED COOKIES")
            print("="*60)
            print(f"📅 Extracted: {data.get('timestamp', 'Unknown')}")
            print(f"🌐 URL: {data.get('url', 'Unknown')}")
            print(f"📊 Count: {data.get('count', 0)}")
            print("-"*60)
            
            cookies = data.get('cookies', {})
            for idx, (name, value) in enumerate(cookies.items(), 1):
                display = value[:50] + "..." if len(value) > 50 else value
                print(f"{idx:2}. {name}: {display}")
                
        except FileNotFoundError:
            print("❌ No saved cookies found. Run extraction first.")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    else:
        print("❌ Invalid choice")

# ============================================================
# COMMAND LINE USAGE
# ============================================================

if __name__ == "__main__":
    main()