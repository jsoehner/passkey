import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_passkey_demo():
    print("Initializing headless Chrome browser...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(15)
    
    try:
        # Step 1: Enable WebAuthn and register a Virtual Authenticator
        print("Configuring WebAuthn Virtual Authenticator via CDP...")
        driver.execute_cdp_cmd("WebAuthn.enable", {})
        
        # Simulates an internal resident-key authenticator with user verification pre-authorized
        auth_config = {
            "options": {
                "protocol": "ctap2",
                "transport": "internal",
                "hasUserVerification": True,
                "isUserVerified": True,
                "hasResidentKey": True,
                "automaticPresenceSimulation": True
            }
        }
        authenticator_id = driver.execute_cdp_cmd("WebAuthn.addVirtualAuthenticator", auth_config)
        print(f"Virtual Authenticator initialized. ID: {authenticator_id['authenticatorId']}")

        # Step 2: Open demo site
        demo_url = "https://webauthn.io"
        print(f"Loading {demo_url}...")
        driver.get(demo_url)
        
        # Step 3: Input Username
        username = f"testuser_{int(time.time())}"
        print(f"Registering username: {username}...")
        
        # Wait for input box to load
        input_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "input-email"))
        )
        input_element.clear()
        input_element.send_keys(username)
        
        # Step 4: Click register button
        register_button = driver.find_element(By.ID, "register-button")
        register_button.click()
        print("Registration request submitted. Waiting for virtual authenticator response...")
        
        # Step 5: Check verification alert
        # Webauthn.io displays a green alert banner or prompts for authentication on success
        success_banner = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-success, #login-button, button[id='login-button']"))
        )
        
        print("\n🎉 Success! The passkey was registered and stored in the virtual authenticator.")
        print(f"Banners/Status Text: {success_banner.text.strip()}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Cleaning up browser session.")
        driver.quit()

if __name__ == "__main__":
    run_passkey_demo()
