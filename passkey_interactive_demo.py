import sys
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def create_artifact_summary(stage_num, title, description, details, payload=None):
    """
    Saves an artifact file in the workspace directory under `passkey_artifacts/` for user inspection.
    """
    os.makedirs("passkey_artifacts", exist_ok=True)
    filename = f"passkey_artifacts/stage_{stage_num}_{title.lower().replace(' ', '_')}.json"
    
    artifact_data = {
        "stage": stage_num,
        "title": title,
        "description": description,
        "details": details,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "captured_payload": payload
    }
    
    with open(filename, "w") as f:
        json.dump(artifact_data, f, indent=4)
        
    print(f"\n--- [Stage {stage_num}] Generated Artifact: {filename} ---")
    print(f"Title: {title}")
    print(f"Description: {description}")
    if payload:
        print(f"Payload Data Highlight: {str(payload)[:160]}...")
    print("-" * 50)
    return filename

def run_interactive_demo():
    print("=" * 60)
    print("         INTERACTIVE PASSKEY WORKFLOW AUDIT DEMO          ")
    print("=" * 60)
    
    # -------------------------------------------------------------
    # STAGE 1: Check System/Browser Passkey API support (WebAuthn)
    # -------------------------------------------------------------
    print("\n[Stage 1] Verifying host browser capability...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    # Enable performance logging to capture WebSocket/network requests
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(15)
    
    try:
        driver.get("https://webauthn.io")
        has_webauthn = driver.execute_script("return !!window.PublicKeyCredential;")
        stage_1_details = {
            "browser": "Chrome Headless",
            "PublicKeyCredential_Declared": has_webauthn,
            "user_agent": driver.execute_script("return navigator.userAgent;")
        }
        create_artifact_summary(
            stage_num=1,
            title="Browser Capability Scan",
            description="Scans the browser context to verify if PublicKeyCredential API is exposed.",
            details=stage_1_details,
            payload={"PublicKeyCredential": has_webauthn}
        )
        
        if not has_webauthn:
            print("Aborting: WebAuthn is not supported by the browser engine.")
            return

        # -------------------------------------------------------------
        # STAGE 2: Add WebAuthn Virtual Authenticator (CDP Interception)
        # -------------------------------------------------------------
        print("\n[Stage 2] Activating DevTools Virtual Authenticator...")
        driver.execute_cdp_cmd("WebAuthn.enable", {})
        
        # We specify ctap2 protocol with internal transport (simulating TouchID/FaceID)
        auth_opts = {
            "protocol": "ctap2",
            "transport": "internal",
            "hasUserVerification": True,
            "isUserVerified": True,
            "hasResidentKey": True,
            "automaticPresenceSimulation": True
        }
        authenticator = driver.execute_cdp_cmd("WebAuthn.addVirtualAuthenticator", {"options": auth_opts})
        
        create_artifact_summary(
            stage_num=2,
            title="Virtual Authenticator Setup",
            description="Chrome DevTools Protocol (CDP) commands are sent to create an auto-responding FIDO2 authenticator.",
            details={
                "CDP_Command": "WebAuthn.addVirtualAuthenticator",
                "authenticator_options": auth_opts
            },
            payload=authenticator
        )

        # -------------------------------------------------------------
        # STAGE 3: Run Registration Protocol (Creation Challenge)
        # -------------------------------------------------------------
        print("\n[Stage 3] Initiating navigator.credentials.create Registration Challenge...")
        
        # Enable CDP Network tracing to capture response body
        driver.execute_cdp_cmd("Network.enable", {})
        
        # Open page
        demo_url = "https://webauthn.io"
        print(f"Loading {demo_url}...")
        driver.get(demo_url)
        
        # Input Username
        username = f"testuser_{int(time.time())}"
        print(f"Registering username: {username}...")
        
        # Wait for input box to load
        input_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "input-email"))
        )
        input_element.clear()
        input_element.send_keys(username)
        
        # Trigger the page register button click to initiate registration challenge
        register_btn = driver.find_element(By.ID, "register-button")
        register_btn.click()
        
        # Wait until registration is verified on the UI
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "login-button"))
        )
        
        # Settle time for network response packets to log
        time.sleep(3)
        
        # Parse Performance Logs to find the Network response received event for registration options
        creation_opts = None
        logs = driver.get_log("performance")
        for entry in logs:
            log_data = json.loads(entry["message"])["message"]
            if log_data.get("method") == "Network.responseReceived":
                resp_url = log_data.get("params", {}).get("response", {}).get("url", "")
                if "registration/options" in resp_url:
                    req_id = log_data.get("params", {}).get("requestId")
                    try:
                        # Extract response body using CDP command
                        body_data = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": req_id})
                        creation_opts = json.loads(body_data.get("body", "{}"))
                        break
                    except Exception as body_err:
                        creation_opts = {"error": f"Failed to retrieve body: {body_err}"}
        
        create_artifact_summary(
            stage_num=3,
            title="Credential Registration Challenge",
            description="Intercepted the PublicKeyCredentialCreationOptions generated by the Relying Party (RP).",
            details={
                "relying_party_domain": "webauthn.io",
                "registered_user": username
            },
            payload=creation_opts
        )

        # -------------------------------------------------------------
        # STAGE 4: Finalize & Store FIDO/Passkey Artifact
        # -------------------------------------------------------------
        print("\n[Stage 4] Verifying the generated Credential Artifact...")
        
        # Allow extra time for credential write to mock authenticator
        time.sleep(2)
        
        # Retrieve the active credentials registered under the virtual authenticator using CDP
        credentials = driver.execute_cdp_cmd("WebAuthn.getCredentials", {"authenticatorId": authenticator["authenticatorId"]})
        
        # Decode and structure the passkey artifact details
        passkey_artifacts = []
        for cred in credentials.get("credentials", []):
            passkey_artifacts.append({
                "credentialId_base64": cred.get("credentialId"),
                "isResidentKey": cred.get("isResidentKey"),
                "rpId": cred.get("rpId"),
                "userHandle_base64": cred.get("userHandle"),
                "signCount": cred.get("signCount")
            })
            
        create_artifact_summary(
            stage_num=4,
            title="Registered Passkey Artifact",
            description="The resulting FIDO credential artifact stored within the Authenticator containing the public key credentials.",
            details={
                "total_credentials_in_authenticator": len(passkey_artifacts)
            },
            payload=passkey_artifacts
        )
        
        print("\n" + "=" * 60)
        print("🎉 Interactive PassKey Demo completed successfully!")
        print("Artifacts saved. You can inspect the outputs in the 'passkey_artifacts/' directory.")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during interactive demo: {e}")
    finally:
        driver.quit()

def parse_saved_artifacts():
    print("\n" + "=" * 60)
    print("         PARSING GENERATED PASSKEY ARTIFACTS IN SEQUENCE          ")
    print("=" * 60)
    
    artifact_dir = "passkey_artifacts"
    if not os.path.exists(artifact_dir):
        print(f"Directory {artifact_dir} does not exist.")
        return
        
    stages = [
        ("stage_1_browser_capability_scan.json", 1),
        ("stage_2_virtual_authenticator_setup.json", 2),
        ("stage_3_credential_registration_challenge.json", 3),
        ("stage_4_registered_passkey_artifact.json", 4)
    ]
    
    for filename, stage_num in stages:
        filepath = os.path.join(artifact_dir, filename)
        if not os.path.exists(filepath):
            print(f"Missing file: {filepath}")
            continue
            
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            
            print(f"\n[Stage {data.get('stage')}] {data.get('title')}")
            print(f"Description: {data.get('description')}")
            print(f"Timestamp: {data.get('timestamp')}")
            
            payload = data.get("captured_payload")
            details = data.get("details", {})
            
            if stage_num == 1:
                print(f"  - Browser: {details.get('browser')}")
                print(f"  - PublicKeyCredential API Available: {details.get('PublicKeyCredential_Declared')}")
                print(f"  - User Agent: {details.get('user_agent')}")
            elif stage_num == 2:
                print(f"  - CDP Command: {details.get('CDP_Command')}")
                if details.get('authenticator_options'):
                    print(f"  - Authenticator Protocol: {details.get('authenticator_options', {}).get('protocol')}")
                    print(f"  - Authenticator Transport: {details.get('authenticator_options', {}).get('transport')}")
                if payload:
                    print(f"  - Authenticator ID: {payload.get('authenticatorId')}")
            elif stage_num == 3:
                if payload:
                    print(f"  - Relying Party Name: {payload.get('rp', {}).get('name')}")
                    print(f"  - Relying Party ID: {payload.get('rp', {}).get('id')}")
                    print(f"  - Registered Username: {payload.get('user', {}).get('name')}")
                    print(f"  - Challenge (Base64URL): {payload.get('challenge')}")
                    print(f"  - Supported Algorithms (COSE IDs): {[p.get('alg') for p in payload.get('pubKeyCredParams', [])]}")
            elif stage_num == 4:
                print(f"  - Total Credentials Registered: {details.get('total_credentials_in_authenticator')}")
                if isinstance(payload, list):
                    for idx, cred in enumerate(payload):
                        print(f"    Credential #{idx + 1}:")
                        print(f"      - Credential ID: {cred.get('credentialId_base64')}")
                        print(f"      - RP ID: {cred.get('rpId')}")
                        print(f"      - Sign Count: {cred.get('signCount')}")
            print("-" * 50)
        except Exception as e:
            print(f"Error parsing {filename}: {e}")

if __name__ == "__main__":
    run_interactive_demo()
    parse_saved_artifacts()
