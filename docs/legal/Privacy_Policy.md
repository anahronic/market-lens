# Privacy Policy

**Document ID:** ML-LEGAL-PRIVACY-001  
**Version:** 1.0  
**Status:** Freeze  
**Effective Date:** 2026-03-31  

---

## 1. Scope

This Privacy Policy applies to the Market Lens system ("System"), a deterministic price observation and measurement platform. It describes what data the System collects, processes, and retains.

---

## 2. Data Collection

### 2.1 Data Collected

The System collects and processes:

- **Observation metadata:** Timestamps, source URLs, page structure signals
- **Normalized price data:** Extracted price values in canonical form
- **Product identity linkage data:** Brand, model, SKU, condition, and other PIL (Product Identity Linkage) fields
- **Evidence hashes:** SHA256 cryptographic hashes of observed content for auditability

### 2.2 Evidence Hash

An `evidence_hash` is a one-way cryptographic fingerprint computed from observed content. It enables verification that a specific observation occurred without storing the original content. The hash cannot be reversed to reconstruct the source material.

### 2.3 Data NOT Collected

The System does **not** collect, store, or process:

- Raw HTML page content or page snapshots
- Copyrighted product descriptions or images
- Personal user data (names, emails, addresses, payment information)
- User browsing history or behavioral profiles
- Cookies or tracking identifiers for user profiling purposes

---

## 3. Purpose Limitation

The System is a **measurement layer** designed for:

- Price observation and normalization
- Market coverage analysis
- Product identity resolution

The System is **not designed for**:

- User profiling or behavioral tracking
- Personal data processing
- Storing proprietary commercial content

---

## 4. Data Retention

- **Observation metadata:** Retained as part of versioned audit trail
- **Normalized data:** Retained indefinitely for historical analysis
- **Evidence hashes:** Retained indefinitely for verification purposes
- **Raw source content:** Not retained

Retention periods may be adjusted per operational requirements. Historical data remains versioned and immutable once frozen.

---

## 5. Data Security

- All data at rest is stored in access-controlled environments
- Cryptographic hashing ensures data integrity
- No personal authentication data is processed by the observation pipeline
- Access to production data is restricted to authorized operators

---

## 6. Cookies and Telemetry

The System does not use cookies for user tracking. If operational telemetry is collected (e.g., error logs, performance metrics), it does not include personally identifiable information.

---

## 7. User Rights

Where applicable law grants data subject rights, requests may be submitted through the contact path specified below. Note that the System does not process personal data as its primary function; requests will be evaluated based on what data, if any, is attributable to an individual.

---

## 8. Contact

For privacy inquiries or data requests:

- **Email:** [privacy contact to be specified]
- **Response time:** Within 30 days of receipt

---

## 9. Jurisdiction

This policy is intended to comply with applicable data protection regulations. Specific jurisdictional requirements will be addressed in supplementary notices as needed.

---

## 10. Changes to This Policy

Updates to this Privacy Policy will be published through versioned documentation. The `Version` field in the document header indicates the current revision.

---

*End of Document*
