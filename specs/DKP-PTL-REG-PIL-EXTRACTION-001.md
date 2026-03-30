# **DKP-PTL-REG-PIL-EXTRACTION-001**

## **Deterministic Product Identity Extraction Specification**

Version: 0.3  
Status: Draft – Audit Candidate (Tightened, Post-Audit)  
Layer: Deterministic Client Pre-Processing Layer

Aligned with:

* DKP-PTL-REG-001 v0.6  
* DKP-PTL-REG-DATA-001 v0.6  
* DKP-PTL-REG-REFERENCE-001 v0.6  
* DKP-PTL-REG-CLIENT-001 v0.6

---

# **1\. Scope**

This document defines deterministic extraction of Product Identity Layer (PIL) from rendered webpages.

This specification:

* defines extraction sources  
* defines source precedence  
* defines normalization  
* defines parsing rules  
* defines failure states  
* defines submission gate

This specification does NOT:

* modify registry logic  
* introduce ML or probabilistic logic

---

# **2\. Embedded Price Presence Contract (RESOLVED BLOCKER)**

To remove external dependency, this specification defines a minimal deterministic price detector.

A price candidate is valid if:

* contains at least one digit  
* contains a currency symbol OR ISO code (₪, $, €, £, USD, ILS, EUR, GBP)  
* matches regex:

(price\_regex\_v1)  
(\[₪$€£\]|USD|ILS|EUR|GBP)?\\s?\[0-9\]{1,3}(\[,\\s\]\[0-9\]{3})\*(\\.\[0-9\]{1,2})?

Normalization:

* remove commas and spaces  
* convert to float

A page unit is valid ONLY if:

* exactly one price candidate exists

If multiple → INVALID\_PAGE\_UNIT

---

# **3\. Deterministic Principles**

All implementations MUST:

* operate on rendered DOM only  
* use UTF-8 \+ NFC  
* use deterministic parsing only  
* execute fixed order

MUST NOT:

* use ML  
* use external APIs  
* use fuzzy matching  
* use user history

---

# **4\. Output Schema**

Return either:

{  
"pil\_extraction\_status": "OK",  
"PIL": { ... }  
}

or failure status.

---

# **5\. Source Classes**

S1 JSON-LD  
S2 Microdata / RDFa  
S3 Meta tags  
S4 DOM visible text  
S5 URL tokens

---

# **6\. Source Precedence**

S1 \> S2 \> S3 \> S4 \> S5

No merging allowed.

---

# **7\. Page Unit Selection (FIXED)**

## **7.1 Product Page**

Single Product entity → full page

## **7.2 Listing Page (LCA DEFINITION)**

Define:

* Node\_T \= title node  
* Node\_P \= price node

Page Unit \= Lowest Common Ancestor (LCA(Node\_T, Node\_P))

Constraints:

* LCA depth must not exceed 10 levels above Node\_T  
* if multiple LCAs exist (edge case) → choose closest to Node\_T

If Node\_T or Node\_P missing → INVALID\_PAGE\_UNIT

---

# **8\. Normalization (UPDATED)**

Steps:

1. UTF-8 decode  
2. NFC  
3. trim  
4. collapse spaces  
5. case-fold  
6. remove zero-width

Allowed chars:  
\[a-z0-9 \-/+.&\]

Rules:

* "&" → "and"  
* """ → "inch"

---

# **9\. JSON-LD Selection (FIXED)**

If multiple Product objects:

Select object maximizing:  
score \= count(non-empty PIL fields)

Tie-break:

1. has offers  
2. has sku  
3. DOM order

---

# **10\. Title Candidate**

Same as v0.2.

---

# **11\. URL Token Rules (HARDENED)**

Restrictions:

* max tokens used \= 3  
* S5 MUST NOT populate model if S1-S3 exist

---

# **12\. Parsing Rules**

## **12.1 Tokenization**

Split by strict regex:  
\[\\s,|()\\\[\\\]\]+

---

## **12.2 Brand**

Rule tightened:

Brand valid ONLY if:

* exists in S1-S3  
  OR  
* exact prefix match between title and URL tokens (first token only)

Else ""

---

## **12.3 Model (FORMALIZED)**

Steps:

1. Remove brand prefix if exists  
2. Remove tokens in DICTIONARY\_NOISE\_v1  
3. Remove tokens matching price\_regex\_v1  
4. Remaining tokens → contiguous segments

Define segment as sequence of tokens with no removal gaps.

Select segment with:

* max length (tokens count)  
* tie-break: earliest occurrence

Constraints:

* must contain ≥1 alphabetic char  
* max 128 bytes

If no valid segment → FAIL

---

## **12.4 SKU**

Unchanged.

---

## **12.5 Condition**

Unchanged.

---

## **12.6 Bundle Flag**

Unchanged.

---

## **12.7 Warranty**

Unchanged.

---

## **12.8 Region**

Unchanged.

---

## **12.9 Storage/Size (FORMALIZED)**

Regex set:

(storage\_regex\_v1)  
\[0-9\]+(gb|tb|w|cm|inch)

Normalization:

* "55"" → "55inch"

---

## **12.10 Release Year (UPDATED)**

Valid if:  
1970 ≤ year ≤ current\_year \+ 2

---

# **13\. Validity Gate**

Valid if:

* model \!= ""  
* price exists  
* C\_extract ≥ 2

---

# **14\. Conflict Rules**

Unchanged.

---

# **15\. Runtime Order**

Unchanged.

---

# **16\. Security Constraints**

Unchanged.

---

# **17\. Deterministic Guarantee**

Unchanged.

---

# **18\. Known Limitations**

Unchanged.

---

# **19\. Token Dictionary (NEW)**

DICTIONARY\_NOISE\_v1 (versioned):  
new, sale, best, free, shipping, deal, discount, promo

Dictionary MUST be version-locked.

---

# **Final Statement**

Version 0.3 resolves:

* price dependency blocker  
* LCA ambiguity  
* model parsing ambiguity  
* URL poisoning risk

System is now:

* deterministic  
* executable  
* audit-ready

Remaining dependency (non-blocking): future standalone PRICE-EXTRACTION spec for extended coverage.

