**DKP-PTL-REG-CONSTANTS-001**

Deterministic Constants Registry  
Version 0.6  
Status: Draft – Dual-Profile Parameter Lock Specification  
Aligned with DKP-PTL-REG-001 v0.6 and DKP-PTL-REG-DATA-001 v0.6

---

## **1\. Purpose**

This document defines all numerical constants used by:

* DKP-PTL-REG-001 v0.6  
* DKP-PTL-REG-DATA-001 v0.6

This document contains numerical parameters only.

All computational procedures, algorithms, and state transitions are defined exclusively in companion specifications.

This document defines two deterministic parameter profiles:

* BASE  
* HARDENED

All constants within a profile form an atomic deterministic set.

---

## **2\. Deterministic Requirements**

All implementations MUST:

* Use IEEE 754 double precision arithmetic  
* Use rounding mode: round half to even  
* Round all externally exposed metrics to 6 decimal places before storage or comparison

Any deviation invalidates conformance.

All time constants in this document are expressed in seconds.

---

## **3\. Profile Selection and Determinism**

### **3.1 Deterministic Profile Selection**

The system MUST NOT switch profiles dynamically based on internal discretion.

Profile selection MUST be either:

* Fixed system-wide by configuration, or  
* Deterministically mapped by product category or OCV via a published immutable mapping table

If mapping rules overlap, conflict resolution MUST follow this deterministic order:

1. Most specific rule  
2. Highest priority rule as defined in the mapping table  
3. Explicit fallback to BASE if no rule matches

The mapping table MUST be:

* Versioned  
* Published  
* Immutable per constants\_version

---

### **3.2 Mandatory Output Flag**

All Registry outputs MUST include:

applied\_profile ∈ {BASE, HARDENED}

---

### **3.3 Profile Atomicity**

Within each profile:

* Constants form an atomic set  
* Changing any constant requires:  
  * protocol\_version increment  
  * constants\_version increment  
  * republication of the full profile  
  * regeneration of official deterministic test vectors

No partial modification is permitted.

---

## **4\. Coverage Threshold Constants**

N\_eff\_min:

BASE: 3.0  
HARDENED: 3.5

ColdStart triggering logic is defined in:

* DKP-PTL-REG-001 v0.6  
* DKP-PTL-REG-DATA-001 v0.6

---

## **5\. Minimum Weight Threshold**

W\_min:

BASE: 1.0  
HARDENED: 1.5

ColdStart MUST be triggered when:

Σ w\_i \< W\_min

Defined in:

* DKP-PTL-REG-DATA-001

---

## **6\. Confidence Curve Constant**

k\_n:

BASE: 0.22  
HARDENED: 0.22

The Confidence Score formula is defined in:

* DKP-PTL-REG-001 v0.6  
* DKP-PTL-REG-DATA-001 v0.6

---

## **7\. Temporal Decay Constants (seconds)**

T\_half\_default:

BASE: 1209600  
HARDENED: 1209600

(14 days)

max\_age\_cutoff:

BASE: 7776000  
HARDENED: 7776000

(90 days)

Constraint:

max\_age\_cutoff \> T\_half\_default

Temporal weighting logic is defined in:

* DKP-PTL-REG-DATA-001

---

## **8\. Domain Contribution Constraint**

domain\_contribution\_cap\_percent:

BASE: 0.30  
HARDENED: 0.30

Constraint:

0 \< domain\_contribution\_cap\_percent ≤ 1

Domain cap algorithm is defined in:

* DKP-PTL-REG-DATA-001

---

## **9\. Similarity Threshold**

cluster\_similarity\_threshold:

BASE: 0.92  
HARDENED: 0.92

Constraint:

0 ≤ cluster\_similarity\_threshold ≤ 1

Similarity computation and clustering logic are defined in:

* DKP-PTL-REG-DATA-001  
* DKP-PTL-REG-THREAT-001

---

## **10\. Burst Detection Constants**

burst\_threshold\_multiplier:

BASE: 4.0  
HARDENED: 4.0

early\_window\_multiplier:

BASE: 2.0  
HARDENED: 2.0

stability\_window\_duration\_seconds:

BASE: 86400  
HARDENED: 86400

(24 hours)

Constraint:

stability\_window\_duration\_seconds \> 0

Burst detection algorithm is defined in:

* DKP-PTL-REG-DATA-001  
* DKP-PTL-REG-THREAT-001

---

## **11\. Outlier Control Constants**

z\_max:

BASE: 6.0  
HARDENED: 4.5

Constraint:

z\_max \> 0

Outlier detection logic is defined in:

* DKP-PTL-REG-DATA-001

Note:

dispersion\_threshold constant is intentionally removed in this version.  
Any dispersion-related logic MUST be fully defined in DATA-001 if introduced in future versions.

---

## **12\. Display Threshold**

CS\_display\_threshold:

BASE: 0.15  
HARDENED: 0.25

Constraint:

0 ≤ CS\_display\_threshold ≤ 1

Display logic is defined in:

* DKP-PTL-REG-DATA-001

---

## **13\. Scope Boundary**

This document does NOT define:

* ColdStart procedures  
* Effective sample size computation  
* Confidence Score formula  
* Similarity calculations  
* Burst detection logic  
* Weight normalization logic  
* Domain aggregation logic  
* Profile mapping table contents

All such procedures are defined exclusively in companion specifications.

---

## **14\. Version Governance Rule**

Any modification of any constant in this document requires:

* protocol\_version increment  
* constants\_version increment  
* public changelog publication  
* regeneration of official deterministic test vectors

No silent modification is permitted.

---

## **Final Statement**

Version 0.6 establishes a fully deterministic dual-profile constants registry with:

* Explicit unit specification  
* Atomic profile integrity  
* Cross-document consistency  
* Elimination of unused constants  
* Strict version governance

This document is numerically complete and synchronized with DKP-PTL-REG-001 v0.6 and DKP-PTL-REG-DATA-001 v0.6.

