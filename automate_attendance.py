import os
import sys
import json
import time
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service

# Configuration path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Config file not found at {CONFIG_FILE}")
        sys.exit(1)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def dismiss_any_popups(driver, timeout=5):
    """
    Attempts to find and click the OK dismiss button using multiple robust selectors.
    Returns True if successfully clicked, False if not found/timed out.
    """
    wait = WebDriverWait(driver, timeout)
    dismiss_selectors = [
        (By.CSS_SELECTOR, "button.dismissButton"),
        (By.XPATH, "//button[contains(@class, 'dismissButton') and text()='OK']"),
        (By.XPATH, "//button[contains(@class, 'dismissButton')]"),
        (By.CLASS_NAME, "dismissButton"),
        (By.XPATH, "//button[text()='OK']")
    ]
    for selector_type, selector_val in dismiss_selectors:
        try:
            dismiss_btn = wait.until(EC.element_to_be_clickable((selector_type, selector_val)))
            print(f"Dismiss button found via {selector_type}='{selector_val}'. Clicking OK...")
            dismiss_btn.click()
            return True
        except Exception:
            continue
    return False

def run_automation(action, headless):
    config = load_config()
    
    # Initialize Chrome options
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Enable Geolocation permission by default
    prefs = {
        "profile.default_content_setting_values.geolocation": 1  # 1 = Allow, 2 = Block
    }
    options.add_experimental_option("prefs", prefs)
    
    # Start WebDriver
    print("Starting Chrome WebDriver...")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    
    # Override Geolocation coordinates (e.g., matching local office or city)
    latitude = config.get("latitude", 13.0827)
    longitude = config.get("longitude", 80.2707)
    print(f"Setting Geolocation override: Latitude = {latitude}, Longitude = {longitude}")
    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": 100
    })
    
    try:
        # Step 1: Login
        print(f"Navigating to login page: {config['login_url']}")
        driver.get(config['login_url'])
        
        # Locate login elements
        username_selectors = [
            (By.NAME, "username"),
            (By.ID, "username"),
            (By.ID, "modlgn-username"),
            (By.CSS_SELECTOR, "input[type='text']")
        ]
        
        password_selectors = [
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.ID, "modlgn-passwd"),
            (By.CSS_SELECTOR, "input[type='password']")
        ]
        
        # Find username field
        username_el = None
        for selector_type, selector_val in username_selectors:
            try:
                username_el = wait.until(EC.presence_of_element_located((selector_type, selector_val)))
                break
            except Exception:
                continue
                
        if not username_el:
            raise NoSuchElementException("Could not locate username input field.")
            
        # Find password field
        password_el = None
        for selector_type, selector_val in password_selectors:
            try:
                password_el = driver.find_element(selector_type, selector_val)
                break
            except Exception:
                continue
                
        if not password_el:
            raise NoSuchElementException("Could not locate password input field.")
            
        print("Entering login credentials...")
        username_el.clear()
        username_el.send_keys(config['username'])
        password_el.clear()
        password_el.send_keys(config['password'])
        
        # Submit login form
        # Often there's a login button with type="submit" or value="Log in"
        login_button = None
        for selector in [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.CLASS_NAME, "login-btn"),
            (By.XPATH, "//button[contains(text(), 'Log in')]"),
            (By.XPATH, "//input[@value='Log in']")
        ]:
            try:
                login_button = driver.find_element(*selector)
                break
            except Exception:
                continue
                
        if login_button:
            print("Clicking login button...")
            login_button.click()
        else:
            print("Login button not found, submitting form by pressing Enter...")
            password_el.submit()
            
        # Wait for login redirect
        time.sleep(5)
        
        # Step 2: Navigate to attendance page
        print(f"Navigating to attendance page: {config['attendance_url']}")
        driver.get(config['attendance_url'])
        time.sleep(3)
        
        # Handle "Check In" flow
        if action in ["checkin", "auto"]:
            try:
                # Dismiss any popups that appear immediately upon loading the page
                print("Checking for any immediate popups on page load...")
                if dismiss_any_popups(driver, timeout=5):
                    print("Dismissed initial page-load popup.")
                    time.sleep(2)
                else:
                    print("No immediate page-load popup detected. Proceeding to Check In...")

                print("Checking for 'Check In' button...")
                # Look for Check In anchor link by ID or text
                checkin_btn = wait.until(EC.element_to_be_clickable((By.ID, "checkoutbutton")))
                print("Found Check In button. Clicking it...")
                checkin_btn.click()
                
                # Wait for pop-up dismiss button(s) in a loop (in case it appears multiple times)
                print("Waiting for popup dismiss button (OK)...")
                popup_count = 0
                while True:
                    if dismiss_any_popups(driver, timeout=5):
                        popup_count += 1
                        # Wait 5 seconds before checking for the next popup
                        time.sleep(5)
                    else:
                        if popup_count > 0:
                            print(f"Successfully dismissed all {popup_count} popups!")
                        else:
                            print("No popup dismiss button appeared.")
                        break
                
            except TimeoutException:
                print("Check In button or popup was not found / timed out.")
                if action == "checkin":
                    sys.exit(1)
        
        # Handle "Checkout" flow
        if action in ["checkout", "auto"]:
            try:
                print("Checking for 'Checkout' button...")
                # Look for the checkout submit input element
                checkout_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "finger_scan_checkout")))
                print("Found Checkout button. Clicking it...")
                checkout_btn.click()
                time.sleep(3)
                print("Successfully completed Checkout flow!")
                
            except TimeoutException:
                print("Checkout button was not found / timed out.")
                if action == "checkout":
                    sys.exit(1)
                    
        print("Automation run completed successfully.")
        
    except Exception as e:
        print(f"An error occurred during automation: {e}")
        # Take screenshot for debugging if error occurs
        screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_screenshot.png")
        try:
            driver.save_screenshot(screenshot_path)
            print(f"Error screenshot saved to {screenshot_path}")
        except Exception as se:
            print(f"Failed to save screenshot: {se}")
        sys.exit(1)
        
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate attendance check-in/checkout.")
    parser.add_argument(
        "--action", 
        choices=["checkin", "checkout", "auto"], 
        default="auto",
        help="Action to perform: 'checkin', 'checkout', or 'auto' (detect and click available buttons)"
    )
    parser.add_argument(
        "--headless", 
        action="store_true", 
        help="Run browser in headless (background) mode"
    )
    
    args = parser.parse_args()
    
    # Set default values for config template check
    config = load_config()
    if config['password'] == "YOUR_PASSWORD_HERE":
        print("Warning: Please edit config.json and replace 'YOUR_PASSWORD_HERE' with your actual password.")
        sys.exit(1)
        
    run_automation(args.action, args.headless)
