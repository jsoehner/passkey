#!/usr/bin/env python3
"""
unified_audit.py
Unified audit script: Passkey Capability, Passkey Creation Test, and PQC Support.
Usage: python3 unified_audit.py
"""

import sys
import subprocess
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TARGETS = [
    "https://www.google.com"
]

# --- Proxy Logic ---
def check_reachability(host, port, timeout=2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def get_proxy_config():
    if check_reachability("webproxy.bns", 8080):
        return "http://webproxy.bns:8080"
    elif check_reachability("127.0.0.1", 9000):
        return "http://127.0.0.1:9000"
    return None

PROXY = get_proxy_config()

# --- Audit Functions ---

def test_passkey_creation(driver):
    """
    Attempts to run navigator.credentials.create on the loaded page.
    Assumes a virtual authenticator is already configured on the driver.
    """
    try:
        # Check standard capability first
        is_cap = driver.execute_script("return typeof navigator.credentials !== 'undefined' && typeof navigator.credentials.create === 'function';")
        if not is_cap:
            return "Blocked: No navigator.credentials.create API"
            
        script = """
        // Trigger a synchronous check of credential generation to see if it immediately throws or goes to promise
        try {
            var promise = navigator.credentials.create({
                publicKey: {
                    challenge: new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]),
                    rp: { name: "Audit Test", id: window.location.hostname },
                    user: {
                        id: new Uint8Array([1]),
                        name: "test@example.com",
                        displayName: "Test User"
                    },
                    pubKeyCredParams: [{ type: "public-key", alg: -7 }],
                    timeout: 1000
                }
            });
            return { status: "initiated", message: "Call succeeded, promise returned" };
        } catch (e) {
            return { status: "error", message: e.message, name: e.name };
        }
        """
        result = driver.execute_script(script)
        if result.get("status") == "initiated":
            return "Passkey API call initiated successfully"
        else:
            return f"Blocked: {result.get('name')} - {result.get('message')}"
    except Exception as e:
        return f"Script Error: {e}"

def check_webauthn(driver, url):
    try:
        driver.get(url)
        return driver.execute_script("return !!window.PublicKeyCredential;")
    except Exception:
        return False

def check_pqc_exchange(url):
    try:
        hostname = url.replace('https://', '')
        env = {"https_proxy": PROXY} if PROXY else {}
        proxy_flag = f"-proxy {PROXY.replace('http://', '')}" if PROXY else ""
        
        cmd = f"openssl s_client -connect {hostname}:443 -tls1_3 {proxy_flag} < /dev/null"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
        return "X25519MLKEM768" in result.stdout
    except Exception:
        return False

def run_audit():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    if PROXY:
        options.add_argument(f"--proxy-server={PROXY}")
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(15)
    driver.implicitly_wait(5)
    
    # Initialize virtual authenticator once globally for the driver lifecycle
    try:
        driver.execute_cdp_cmd("WebAuthn.enable", {})
        driver.execute_cdp_cmd("WebAuthn.addVirtualAuthenticator", {
            "options": {
                "protocol": "ctap2",
                "transport": "internal",
                "hasUserVerification": True,
                "isUserVerified": True,
                "hasResidentKey": True,
                "automaticPresenceSimulation": True
            }
        })
    except Exception as e:
        print(f"Failed to initialize virtual WebAuthn: {e}")
    
    print(f"{'Target':<39} | {'Passkey Cap':<12} | {'Creation Test':<30} | {'PQC':<5}")
    print("-" * 95)
    
    for target in TARGETS:
        try:
            has_passkey = check_webauthn(driver, target)
            can_create = test_passkey_creation(driver) if has_passkey else "N/A (No Cap)"
            has_pqc = check_pqc_exchange(target)
            
            print(f"{target:<39} | {str(has_passkey):<12} | {str(can_create):<30} | {str(has_pqc):<5}")
        except Exception as e:
            print(f"{target:<39} | Error: {e}")
            
    driver.quit()

if __name__ == "__main__":
    run_audit()
