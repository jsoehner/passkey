# Passkey Workflow & FIDO Verification Demo

This directory contains an automated, interactive demonstration of the **FIDO2 / WebAuthn Passkey registration lifecycle** using Selenium and Chrome DevTools Protocol (CDP).

## Overview of Stages

The demonstration models the four critical security phases of a FIDO/Passkey registration:

1. **Stage 1: Browser Capability Scan**: Inspects if the client browser runtime declares support for the `PublicKeyCredential` API.
2. **Stage 2: Virtual Authenticator Setup**: Uses CDP to inject an automated virtual hardware authenticator (mocking TouchID/FaceID) to respond to credential challenges.
3. **Stage 3: Registration Interception**: Intercepts the cryptographic creation challenge (`PublicKeyCredentialCreationOptions`) sent by the Relying Party (RP).
4. **Stage 4: FIDO Credential Extraction**: Queries the local browser authenticator context to extract the resulting public key credential artifact.

---

## How to Install Dependencies

Make sure you have Chrome installed on your system. Then, install the required python packages:

```bash
pip install selenium
```

---

## Running the Demo

Run the interactive demo script directly using Python:

```bash
python3 passkey_interactive_demo.py
```

### Expected Output

During execution, the script will output real-time diagnostics:

```text
============================================================
         INTERACTIVE PASSKEY WORKFLOW AUDIT DEMO          
============================================================

[Stage 1] Verifying host browser capability...
--- [Stage 1] Generated Artifact: passkey_artifacts/stage_1_browser_capability_scan.json ---

[Stage 2] Activating DevTools Virtual Authenticator...
--- [Stage 2] Generated Artifact: passkey_artifacts/stage_2_virtual_authenticator_setup.json ---

[Stage 3] Initiating navigator.credentials.create Registration Challenge...
Loading https://webauthn.io...
Registering username: testuser_...
--- [Stage 3] Generated Artifact: passkey_artifacts/stage_3_credential_registration_challenge.json ---

[Stage 4] Verifying the generated Credential Artifact...
--- [Stage 4] Generated Artifact: passkey_artifacts/stage_4_registered_passkey_artifact.json ---
```

---

## Additional Scripts

This repository contains other utility scripts for testing and auditing:

### 1. Standard Passkey Demo ([passkey_demo.py](file:///Users/jsoehner/passkey/passkey_demo.py))
A simplified, automated version of the Selenium WebAuthn flow. It starts a headless Chrome browser, initializes a virtual authenticator via Chrome DevTools Protocol, registers a dummy user on [webauthn.io](https://webauthn.io), and verifies the registration banner. Unlike the interactive script, it does not save JSON artifacts to disk.

Run it using:
```bash
python3 passkey_demo.py
```

### 2. Unified Audit Script ([unified_audit.py](file:///Users/jsoehner/passkey/unified_audit.py))
Audits a list of target websites (configured in the script, defaulting to `https://www.google.com`) for WebAuthn APIs, credentials creation capability, and TLS 1.3 Post-Quantum Cryptography (PQC) hybrid key exchange support (`X25519MLKEM768`).

* **Passkey Cap**: Checks if the global `window.PublicKeyCredential` is available.
* **Creation Test**: Asserts whether `navigator.credentials.create` can be successfully called when a virtual authenticator is attached.
* **PQC**: Runs an `openssl s_client` connection command to identify if `X25519MLKEM768` was negotiated.

Run the audit using:
```bash
python3 unified_audit.py
```

---

## Inspecting Artifacts

After execution completes, you will find a newly created `passkey_artifacts/` directory containing JSON files for each stage:

* **[Stage 1 Scan](file:///Users/jsoehner/passkey/passkey_artifacts/stage_1_browser_capability_scan.json)**: Verifies `window.PublicKeyCredential` is defined.
* **[Stage 2 Setup](file:///Users/jsoehner/passkey/passkey_artifacts/stage_2_virtual_authenticator_setup.json)**: Contains the generated `authenticatorId` handler.
* **[Stage 3 Challenge](file:///Users/jsoehner/passkey/passkey_artifacts/stage_3_credential_registration_challenge.json)**: Inspects the raw relying party challenge, user parameters, and accepted cryptographic signature algorithms.
* **[Stage 4 Passkey](file:///Users/jsoehner/passkey/passkey_artifacts/stage_4_registered_passkey_artifact.json)**: The final generated public key credential object.

---

## Security Model: TPM vs. Software

In the FIDO/WebAuthn architecture, key storage security depends heavily on the type of authenticator used:

* **This Demonstration (Software-Based):** To run headlessly and automatically, this script uses **pure software emulation**. The virtual authenticator is created and held in Chrome's temporary heap memory. It does not utilize any physical hardware security modules.
* **Production Platforms (Hardware/TPM/Secure Enclaves):** Modern operating systems bind passkeys to hardware security modules:
  * **Windows Hello:** Generates and stores passkeys in a hardware **TPM (Trusted Platform Module)**.
  * **Apple Touch ID/Face ID (macOS/iOS):** Generates and stores keys inside the **Secure Enclave**.
  * **Android Keystore:** Stores keys in a hardware-backed **TEE (Trusted Execution Environment)** or dedicated **StrongBox** security chip.

---

## Demo "Tricks" (Automation Bypass)

Normally, FIDO2/WebAuthn is explicitly designed to **block programmatic automation** to prevent clickjacking and credential stealing. A real browser requires:
1. An active user gesture (e.g., clicking a button).
2. Physical interaction with a system-level biometric prompt (fingerprint, face scan) or physical security key.

To demonstrate this headlessly, the demo employs **Chrome DevTools Protocol (CDP) simulation tricks**:
* `WebAuthn.enable`: Overrides the browser's native OS-level credential prompt routing.
* `WebAuthn.addVirtualAuthenticator`: Injects a simulated software device with `"automaticPresenceSimulation": True` and `"isUserVerified": True`. This tricks Chrome into thinking a user physically touched a hardware authenticator and verified their identity, bypassing the biometric OS dialog.

---

## Real-world Passkey Creation Methods

Anyone can manually create, test, and observe passkey creation using public diagnostics apps like [webauthn.io](https://webauthn.io/).

### 1. Creating a Hardware-Backed (Device-Bound) Passkey
A hardware-backed passkey generates and binds the private key within a physical secure chip (e.g., physical YubiKey or built-in Touch ID/Windows Hello TPM).

#### Step-by-Step Instructions:
1. **Prepare Hardware:** Connect a physical FIDO2 USB key, or ensure you are using a device with configured biometrics (Touch ID, Face ID, Windows Hello).
2. **Navigate to the App:** Open a browser and go to [webauthn.io](https://webauthn.io/).
3. **Open Developer Tools (to inspect):** Press `F12` and select the **Application** tab. Scroll down to **WebAuthn** on the left menu. Make sure **"Enable virtual authenticator environment" is unchecked** so the browser reaches real hardware.
4. **Configure Registration Options:**
   * **Username:** Enter any unique name (e.g., `hardware_user_abc`).
   * **Authenticator Type:** Choose **Cross-Platform** (for external keys like YubiKey) or **Platform** (for built-in device biometrics).
   * **Resident Key:** Set to **Required** (stores the key directly on the hardware token).
   * **Attestation:** Set to **Direct** (requests the hardware module to supply its certified cryptographic signature chain).
5. **Trigger Registration:** Click **Register**.
6. **Complete System Verification:** Follow your OS/browser prompt to touch your security key or authenticate with your biometric reader.
7. **Observe Attestation:** Under the registration response, examine the `attestationObject`. FIDO hardware keys sign this payload with a manufacturer-embedded certificate, proving cryptographic creation inside a physical secure element.

---

### 2. Creating a Cloud-Synced (Software-Synced) Passkey
Cloud-synced passkeys trade device-isolation for multi-device recovery by synchronizing encrypted key material across your ecosystem devices.

#### Step-by-Step Instructions:
1. **Prepare Account:** Ensure you are logged into your primary ecosystem account (e.g., Google Account in Chrome, or Apple Account on Safari/macOS).
2. **Navigate to the App:** Open your browser and go to [webauthn.io](https://webauthn.io/).
3. **Configure Registration Options:**
   * **Username:** Enter a unique name (e.g., `synced_user_abc`).
   * **Authenticator Type:** Set to **Platform** (tells the browser to route to OS/browser native storage).
   * **Resident Key:** Set to **Preferred**.
   * **Attestation:** Set to **None** (attestation certificates are skipped to protect user privacy).
4. **Trigger Registration:** Click **Register**.
5. **Authorize Cloud Storage:**
   * A prompt will ask where you'd like to save the credential (e.g., "iCloud Keychain" or "Google Password Manager").
   * Approve using your system biometrics or passcode.
6. **Verify Sync Status:**
   * **On Chrome:** Go to `chrome://settings/passwords` and verify your passkey for `webauthn.io` is saved in the Google Password Manager cloud list.
   * **On macOS/iOS:** Go to **System Settings** > **Passwords** to view the entry saved under your iCloud Keychain.
   * *Note:* The private key is wrapped with end-to-end encryption based on your lock screen passcode before syncing, keeping it private from the cloud hosting provider.
