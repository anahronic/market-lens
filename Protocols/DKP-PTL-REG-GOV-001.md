# **DKP-PTL-REG-GOV-001**

## **Deterministic Governance & Version Control Specification**

Version: 0.6  
Status: Freeze Candidate  
Aligned with:

* DKP-PTL-REG-001 v0.6  
   DKP-PTL-REG-001  
* DKP-PTL-REG-DATA-001 v0.6  
   DKP-PTL-REG-DATA-001  
* DKP-PTL-REG-CONSTANTS-001 v0.6  
   DKP-PTL-REG-CONSTANTS-001\_  
* DKP-PTL-REG-REFERENCE-001 v0.6  
* DKP-PTL-REG-THREAT-001 v0.6

---

# **1\. Scope**

This document defines:

* Version lifecycle rules  
* Constants modification governance  
* Artifact immutability requirements  
* Dispute and recomputation workflow  
* Build reproducibility requirements  
* Activation control mechanisms

This document does not:

* Modify metric outputs  
* Introduce override mechanisms  
* Introduce administrative exception logic  
* Introduce discretionary interpretation

All governance operations MUST preserve deterministic reproducibility.

---

# **2\. Version Semantics**

## **2.1 Version Format**

Version format:

vX.Y

Where:

* X \= major version (architectural break)  
* Y \= monotonic integer increment

No PATCH level exists.

Any change affecting:

* Algorithms  
* Constants  
* Normalization rules  
* Threat triggers  
* Sorting logic  
* Output schema  
* PSL snapshot  
* Canonical hashing logic

MUST increment version.

Example:

v0.6 → v0.7 → v0.8 → v1.0

Version numbers MUST be strictly increasing.

Re-use of version identifiers is prohibited.

---

# **3\. Dual Version Coupling**

Each release MUST declare:

* protocol\_version  
* constants\_version

Rule:

Any modification to CONSTANTS-001 requires:

* protocol\_version increment  
* constants\_version increment

Constants and protocol are atomically coupled.

No constant may change independently.

---

# **4\. Immutable Artifact Registry**

Each published version MUST include:

* SHA256 hash of:  
  * DKP-PTL-REG-001  
  * DKP-PTL-REG-DATA-001  
  * DKP-PTL-REG-CONSTANTS-001  
  * DKP-PTL-REG-REFERENCE-001  
  * DKP-PTL-REG-THREAT-001  
  * DKP-PTL-REG-GOV-001  
* SHA256 hash of PSL snapshot  
* SHA256 hash of Reference Engine binary  
* SHA256 hash of official test vector archive

These hashes MUST be published in:

Artifact\_Registry\_vX.Y.json

Once published, artifact registry entries MUST NOT be altered.

If correction required → new version required.

---

# **5\. Build Reproducibility**

Reference Engine MUST:

* Be buildable from published source  
* Produce identical binary hash when built in declared environment  
* Declare:  
  * Compiler version  
  * OS target  
  * Dependency versions

Binary hash MUST match hash declared in Artifact Registry.

If mismatch → release invalid.

---

# **6\. Official Deterministic Test Vectors**

Each version MUST publish:

* Canonical input datasets  
* Expected normalized input boundary outputs  
* Expected:  
  * P\_ref  
  * MAD  
  * N\_eff  
  * CS  
  * integrity\_status  
  * cold\_start\_flag  
  * insufficient\_data\_flag

Test vectors MUST include:

* Uniform market case  
* Burst attack case  
* Domain dominance case  
* Cluster injection case  
* ColdStart case  
* Zero-MAD case

Test vectors MUST be version-bound.

---

# **7\. Cooling-Off Period**

Any new version introducing:

* Constant changes  
* Threat logic change  
* Input boundary change

MUST observe:

Minimum activation delay \= 7 DTI-days

DTI-day defined per DKP time layer.

During cooling-off:

* Version published  
* Test vectors published  
* Artifact registry published  
* Public review permitted

Activation before cooling-off expiry is prohibited.

---

# **8\. Dispute & Recalculation Model**

## **8.1 Non-Override Rule**

Governance MUST NOT:

* Modify P\_ref manually  
* Modify CS manually  
* Override integrity\_status  
* Suppress outputs

All outputs remain purely algorithmic.

---

## **8.2 Evidence Resubmission**

Dispute MAY submit:

* New observations  
* Corrected normalized data  
* Missing product identity attributes

All submissions MUST pass REFERENCE-001 validation.

Accepted data enters global observation pool.

No special weighting granted.

---

## **8.3 Forced Recomputation**

Upon valid dispute submission:

* Entire affected PIL+OCV bucket MUST be recomputed.  
* Recalculation MUST use current protocol\_version and constants\_version.

Recomputation MUST NOT alter historical versioned outputs.

Historical outputs remain archived with their version tags.

---

# **9\. Version Activation**

Each version MUST declare:

* activation\_timestamp (UTC)  
* previous\_version  
* migration\_notes (if applicable)

Multiple versions MAY coexist historically.

Live system MUST expose active\_version.

All outputs MUST include protocol\_version and constants\_version.

---

# **10\. Deactivation Rules**

A version MAY be deprecated only by:

* Publishing new version  
* Declaring deprecation\_notice

Deprecated versions remain reproducible and auditable.

Removal of historical artifacts is prohibited.

---

# **11\. Governance Authority Constraints**

Governance body MUST NOT:

* Introduce emergency override  
* Introduce secret constants  
* Introduce unpublished PSL updates  
* Introduce runtime profile switching without version increment

All governance actions MUST be logged and versioned.

---

# **12\. Deterministic Auditability Guarantee**

Given:

* Version identifier  
* Artifact registry  
* PSL snapshot  
* Test vectors

Any third party MUST be able to reproduce:

* Binary hash  
* All metric outputs  
* integrity\_status  
* ColdStart behavior

Failure to reproduce invalidates version.

---

# **Final Statement**

DKP-PTL-REG-GOV-001 v0.6 establishes:

* Strict monotonic version control  
* Atomic constant-protocol coupling  
* Immutable artifact registry  
* Deterministic dispute workflow  
* Cooling-off safeguard  
* Zero manual override principle  
* Full third-party reproducibility

Governance layer is now formally bounded and deterministic.

Frozen Set governance is structurally complete for v0.6.

