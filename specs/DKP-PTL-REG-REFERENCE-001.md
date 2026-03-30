# **DKP-PTL-REG-REFERENCE-001**

## **Deterministic Input Boundary Specification**

Version: 0.6  
Status: Freeze Candidate  
Aligned with:

* DKP-PTL-REG-001 v0.6  
* DKP-PTL-REG-DATA-001 v0.6  
* DKP-PTL-REG-CONSTANTS-001 v0.6

---

# **1\. Scope**

This document defines the deterministic input normalization boundary required before execution of DATA-001 Step 1\.

This specification:

* Defines canonical string normalization  
* Defines domain canonicalization and root-domain extraction  
* Defines timestamp canonicalization  
* Defines evidence\_hash construction  
* Defines rejection conditions  
* Defines deterministic sorting behavior

This document does not modify computational logic defined in DATA-001.

---

# **2\. Global Determinism Requirements**

All implementations MUST:

* Use UTF-8 encoding  
* Use Unicode Normalization Form C (NFC)  
* Use IEEE 754 double precision  
* Use binary/byte-order sorting for all string comparisons  
* Use SHA256 for hashing  
* Use Unix epoch time (seconds precision)

Locale-dependent collation is strictly prohibited.

---

# **3\. Canonical String Normalization**

For all string fields:

1. Decode as UTF-8.  
2. Apply Unicode normalization: NFC.  
3. Trim leading and trailing ASCII whitespace:  
   * U+0020 (space)  
   * U+0009 (tab)  
   * U+000A (LF)  
   * U+000D (CR)  
4. Convert to lowercase using Unicode case-fold (locale-independent).

After normalization:

* Missing field \= field absent OR equals "".  
* Missing fields MUST be stored as "".

No other transformations are permitted.

---

# **4\. Domain Canonicalization**

## **4.1 Raw Domain Extraction**

Given source\_url:

1. Parse using RFC 3986\.  
2. Extract host component.  
3. Remove port.  
4. Apply string normalization (Section 3).

If host parsing fails → reject observation.

---

## **4.2 Root Domain Extraction**

Root domain MUST be computed using:

Public Suffix List version: PSL-2026-01-01  
(Exact byte snapshot must be version-pinned in repository.)

Algorithm:

1. Match host against PSL.  
2. Extract effective top-level domain \+ one label (eTLD+1).  
3. If no PSL match:  
   * Root domain \= full normalized host.

Examples:

* sub.shop.example.com → example.com  
* example.co.uk → example.co.uk  
* localhost → localhost

Root domain becomes domain\_id.

Subdomains MUST NOT be used for domain cap logic.

---

# **5\. Merchant ID Canonicalization**

merchant\_id MUST:

* Undergo full string normalization (Section 3).  
* If absent → set to "".  
* Max length: 256 bytes after UTF-8 encoding.  
* If exceeds limit → reject observation.

merchant\_id participates in:

* tie\_key\_i  
* similarity hashing  
* clustering

---

# **6\. Timestamp Canonicalization**

Input timestamps MUST be convertible to Unix epoch.

Procedure:

1. Parse ISO-8601 or numeric epoch.  
2. Convert to UTC.  
3. Convert to Unix epoch seconds.  
4. Apply floor(t).  
5. Store as integer.

If:

* Timestamp invalid  
* Timestamp not convertible  
* Timestamp \> current\_time\_utc \+ 5 seconds tolerance

→ reject observation.

Milliseconds MUST be discarded.

All downstream computations use integer seconds only.

---

# **7\. Binary Deterministic Sorting**

All string comparisons MUST:

* Compare UTF-8 encoded byte sequences  
* Use lexicographic byte-order  
* Disallow locale or Unicode collation rules

Tie-breaking in DATA-001 Step 9 MUST use:

Binary comparison of:

* domain\_id  
* merchant\_id  
* timestamp (integer)  
* price (double)

In exact declared order.

---

# **8\. Evidence Hash Construction**

evidence\_hash MUST be computed as:

SHA256(canonical\_payload)

Canonical payload MUST be constructed using deterministic JSON Canonicalization Scheme (JCS):

* UTF-8  
* Lexicographically sorted keys  
* No whitespace  
* No trailing zeros in numbers  
* No insignificant decimal expansion

Required fields in canonical JSON object:

{  
"domain\_id": "...",  
"merchant\_id": "...",  
"price": number,  
"currency": "...",  
"timestamp": integer,  
"region": "...",  
"product\_identity\_layer": {  
"brand": "...",  
"model": "...",  
"sku": "...",  
"condition": "...",  
"bundle\_flag": "...",  
"warranty\_type": "...",  
"region\_variant": "...",  
"storage\_or\_size": "...",  
"release\_year": "..."  
}  
}

All nested objects MUST also use sorted keys.

If any required field missing → reject observation.

No pipe-separated strings permitted.

JSON canonicalization is mandatory.

---

# **9\. Rejection Conditions**

Observation MUST be rejected if any of the following holds:

* price ≤ 0  
* price not finite  
* currency missing  
* region missing  
* OCV incomplete  
* domain parsing fails  
* timestamp invalid  
* timestamp \> future tolerance  
* merchant\_id length \> 256 bytes  
* product identity layer missing required fields  
* normalization error  
* UTF-8 decoding failure

Rejected observations MUST NOT enter DATA-001 pipeline.

---

# **10\. Output Extension**

All validated observations entering DATA-001 MUST include:

* normalized domain\_id  
* normalized merchant\_id  
* timestamp (integer seconds)  
* evidence\_hash (SHA256)  
* identity\_scope\_level (computed later)  
* applied\_profile (in final output)

---

# **11\. Deterministic Guarantees**

Given identical raw input and identical:

* PSL version  
* protocol\_version  
* constants\_version

All compliant implementations MUST produce:

* Identical domain\_id  
* Identical merchant\_id  
* Identical timestamp  
* Identical evidence\_hash  
* Identical sorting order  
* Identical downstream P\_ref  
* Identical MAD  
* Identical N\_eff  
* Identical CS

Any deviation invalidates conformance.

---

# **Final Statement**

Phase 1 Input Boundary is now formally defined with:

* NFC normalization  
* PSL-pinned root domain extraction  
* Second-precision timestamps  
* Binary sorting enforcement  
* Canonical JSON hashing  
* Strict rejection model

Executional Blocker is resolved at specification level.

Architecture remains deterministic and version-locked.

