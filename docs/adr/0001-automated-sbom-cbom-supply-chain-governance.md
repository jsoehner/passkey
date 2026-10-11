# ADR-0001: Automated SBOM and CBOM Supply Chain Governance Pipeline

## Metadata

| Field | Value |
|---|---|
| ADR ID | ADR-0001 |
| Status | Accepted |
| Created Date | 2026-10-11 |
| Decision Date | 2026-10-11 |
| Effective Date | 2026-10-11 |
| Architecture Domain | Security / Supply Chain Governance / Cryptography / DevOps |
| Scope | Software & Cryptographic Supply Chain Security (Repository & CI/CD) |
| Decision Owner | Lead DevSecOps Architect |
| Named Decision Maker | DevSecOps Engineering & Security Architecture Team |
| Approval Authority | Architecture Review Board (ARB) / Security Governance Committee |
| Approval Evidence ID | ARB-2026-10-SEC-006 |
| APM Code(s) | SEC-SUPPLYCHAIN-01 |
| NIRA Reference(s) | NIRA-SEC-2026-043 |
| Tags | sbom, cbom, cyclonedx, spdx, supply-chain, pqc, fido2, webauthn, passkey, x25519mlkem768, ast-analysis, devsecops |

---

## Business and Architecture Context

### Problem Statement

The `passkey` repository implements automated workflows and cryptographic verification harnesses for the FIDO2 / WebAuthn passkey lifecycle—orchestrating browser capability detection, Chrome DevTools Protocol (CDP) virtual authenticators, public key credential challenges, and attestation evaluations. Furthermore, the repository features diagnostic tools (`unified_audit.py`) that evaluate relying parties for both WebAuthn capabilities and Post-Quantum Cryptography (PQC) hybrid key exchange protocols (e.g., `X25519MLKEM768`).

Modern cybersecurity and software supply chain mandates—such as Executive Order 14028, NIST SP 800-218 (Secure Software Development Framework - SSDF), NIST SP 800-63B (Digital Identity Guidelines), and NIST IR 8547 (PQC Transition Guidance)—require verifiable software inventories via Software Bills of Materials (SBOMs) and comprehensive cryptographic asset catalogs via Cryptographic Bills of Materials (CBOMs).

Without an automated, continuous SBOM and CBOM pipeline embedded directly into continuous integration (CI):
1. **Supply Chain Blind Spots:** Upstream dependencies (e.g., Selenium, HTTP clients, browser driver packages) and CI action dependencies risk untracked vulnerabilities and integrity drift.
2. **Cryptographic Opacity:** Cryptographic algorithms (such as ECDSA P-256, Ed25519, RSA-2048, and hybrid PQC key exchange mechanisms like `X25519MLKEM768`) lack formal, machine-readable cataloging and automated discovery.
3. **PQC Transition Gap:** As organizations migrate toward post-quantum standards (NIST FIPS 203, 204, 205), distinguishing quantum-resilient implementations from quantum-vulnerable public key algorithms (e.g., classical ECDSA/RSA passkey credentials) requires automated, reproducible auditing.
4. **Attestation Deficit:** External auditors and downstream consumers lack machine-readable, standards-compliant CycloneDX and SPDX attestations verifying the repository's supply chain hygiene.

### Current Situation

Prior to this decision, the `passkey` repository maintained functional and interactive passkey demonstrations, but:
1. No automated CI workflow existed to generate, validate, and publish SBOMs or CBOMs upon branch commits or release tags.
2. Cryptographic scanning was not integrated into repository testing or AST call-site analysis.
3. There were no build gates to catch schema non-conformance or empty supply chain inventories.
4. Cryptographic auditing and PQC migration readiness were not continuously reported to project documentation.

### Decision Drivers

- **Cryptographic Visibility & FIDO/PQC Governance:** Automated cataloging of both WebAuthn signature algorithms (e.g., ES256, RS256, EdDSA) and network transport crypto (e.g., TLS 1.3 `X25519MLKEM768`) across source code.
- **Regulatory & Compliance Alignment:** Direct conformance with EO 14028, NTIA minimum SBOM elements, NIST SSDF, and CycloneDX v1.5–1.7 / SPDX v2.3 standards.
- **Continuous Quality & Gate Enforcement:** Automated test gates in CI ensuring schema validity, non-empty components, and verified cryptographic metadata.
- **Dual-Engine Interoperability:** Support for both SPDX (v2.3) and CycloneDX (v1.7) formats to enable seamless integration with modern DevSecOps scanners and policy engines.
- **Parity Between Local & CI Workflows:** Developer-friendly CLI scripts mirroring CI execution for fast local validation.

---

## Assumptions

- The repository codebase consists of Python automation and verification scripts interfacing with browser environments and network endpoints.
- Build environments support Python 3.11+ and GitHub Actions runner environments executing Node 24 compliant actions.
- Post-Quantum Cryptography transition will require continuous visibility across software dependencies, network cipher suites, and credential algorithms over the multi-year migration window.

---

## Constraints

- CI workflows must execute within standard GitHub-hosted runner environments without introducing excessive build latency (< 2-3 minutes).
- Tooling must execute locally via standard Python and Bash scripts without requiring proprietary commercial SaaS dependencies.
- All GitHub Actions must use immutable SHA-pinned references and comply with Node 24 runtime standards.

---

## Alternatives Considered

| Option | Advantages | Disadvantages / Risks | Disposition |
|---|---|---|---|
| **Option 1: Status Quo (Ad-hoc Manual Reviews)** | Zero CI runtime overhead; no workflow maintenance. | High operational and compliance risk; inventory quickly becomes obsolete; zero automated detection of cryptographic regressions. | **Rejected** |
| **Option 2: Standalone SBOM-Only Scanning (Syft Only)** | Simple pipeline; fast CycloneDX/SPDX generation. | Lacks cryptographic asset identification; fails to inspect FIDO/PQC primitives or provide CBOM inventories. | **Rejected** |
| **Option 3: cbomkit-Only Scanner** | Captures cryptographic assets in CycloneDX format. | Omits SPDX SBOM generation required by enterprise procurement standards; lacks custom AST call-site analysis. | **Rejected** |
| **Option 4: Integrated Dual-Engine SBOM/CBOM + AST Analysis + Automated CI Harness (Selected)** | Comprehensive coverage: dual-engine SBOM (CycloneDX & SPDX via Anchore/Syft) and CBOM (cbomkit); semantic AST cryptographic scanning (`scan_crypto_ast.py`); automated validation harness (`test_boms.sh`); automated PQC readiness reporting (`analyze_cbom.py`); identical local execution scripts. | Slight increase in CI workflow duration (~60-90s); requires Python 3.11 runtime setup in CI runner; produces artifacts requiring retention policies. | **Selected** |

---

## Decision

### Selected Option

Adopt **Option 4: Integrated Dual-Engine SBOM/CBOM + AST Analysis + Automated CI Harness** across the repository.

Specifically:
1. **GitHub Actions Workflow (`.github/workflows/sbom-cbom.yml`):**
   - Configured with Node 24 pinned actions (`actions/checkout@v7.0.1`, `anchore/sbom-action@v0.24.2`, `cbomkit/cbomkit-action@v2.3.0`, `actions/setup-python@v5.6.0`, `actions/upload-artifact@v4.6.2`).
   - Generates both CycloneDX JSON (`oss/sbom.cyclonedx.json`) and SPDX JSON (`oss/sbom.spdx.json`) SBOMs via Anchore / Syft.
   - Generates CycloneDX CBOM (`oss/cbom.json`) via `cbomkit`.
   - Executes semantic AST cryptographic analysis via `scripts/scan_crypto_ast.py`.
   - Executes validation and test harness via `scripts/test_boms.sh`.
   - Assesses Post-Quantum Cryptography (PQC) readiness and outputs dashboard summaries via `scripts/analyze_cbom.py`.
   - Automatically maintains `docs/security/CRYPTOGRAPHIC_AUDIT.md` and archives BOM artifacts.
2. **Local Tooling Suite (`scripts/`):**
   - `scripts/generate_boms.sh`: Portable CLI script for local generation across source trees or Docker images.
   - `scripts/test_boms.sh`: Strict verification harness testing syntax, CycloneDX schema conformance, and component counts.
   - `scripts/scan_crypto_ast.py`: Python AST walker identifying cryptographic call-sites, key generation, and cipher instantiations.
   - `scripts/analyze_cbom.py`: PQC readiness analysis, algorithm categorization, and Markdown/JSON report generator.
   - `scripts/attach_oci_bom.sh` & `scripts/fetch_oci_cbom.py`: OCI artifact publishing and retrieval utilities.

### Rationale

This multi-tiered architecture provides defense-in-depth supply chain and cryptographic visibility. For a repository demonstrating FIDO2 passkeys and evaluating post-quantum hybrid key exchange (`X25519MLKEM768`), uniting package-level SBOM inventories with cryptographic CBOM asset tracking and AST call-site analysis bridges the gap between third-party dependency vulnerabilities and application cryptographic posture. Automated testing in CI ensures corrupt, incomplete, or drifting BOMs fail fast prior to release.

---

## Consequences

### Benefits

- **Continuous Compliance:** Instant audit readiness for modern SBOM/CBOM standards across both SPDX and CycloneDX specifications.
- **PQC Migration Visibility:** Continuous visibility into quantum-vulnerable algorithms (ECDSA, RSA) alongside quantum-safe primitives (`X25519MLKEM768`, ML-DSA, ML-KEM) across dependencies and source code.
- **Automated Verification:** The `test_boms.sh` harness prevents empty or schema-invalid BOMs from being published.
- **Dual Developer & CI Experience:** Developers can run identical verification locally prior to pushing code.

### Trade-offs and Negative Consequences

- **CI Pipeline Latency:** Adds approximately 60-90 seconds to workflow execution time.
- **Maintenance Overhead:** Periodic updates to tool action SHAs and known algorithm catalogs (`known_cbom_catalog.json`) are required as cryptographic standards evolve.
- **Artifact Storage:** Retention of BOM artifacts in GitHub Actions consumes artifact storage quota (mitigated with 90-day retention policy).

### New Constraints

- Repository CI runners must provide Python 3.11+ runtime for AST and analysis scripts.
- GitHub Actions token permissions must grant `contents: write` for automated cryptographic audit report synchronization on `main` branch pushes.

### Follow-on Decisions and Activities

- Configure pull request checks to fail if high-risk deprecated algorithms (e.g., MD5 for digital signatures, DES, RC4) are newly introduced in source call-sites.
- Establish an automated schedule for nightly container image baseline scans (`scripts/generate_boms.sh -t docker`).
- Integrate OCI cosign / notation attestation signing for generated BOM artifacts in release workflows.

---

## Security, Privacy, and Risk Considerations

- **Integrity & Authenticity:** All workflow dependencies use immutable SHA-256 commit pins to mitigate supply chain tampering of actions.
- **Confidentiality:** Scans inspect public dependencies and cryptographic declarations; no secret keys, private keys, or credentials are embedded in generated BOM artifacts.
- **Supply Chain Traceability:** BOMs link directly to commit SHAs and repository metadata.

---

## Technical Debt Assessment

- **Catalog Maintenance:** The static cryptographic catalog in `scripts/known_cbom_catalog.json` must be reviewed annually against NIST PQC standardization updates.

---

## Review and Lifecycle

- **Review Schedule:** Annual or upon major NIST PQC milestone release.
- **Supersedes:** None (Initial baseline governance record).
- **Superseded By:** None.
