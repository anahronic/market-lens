# **DKP-PTL-REG-THREAT-001**

## **Deterministic Threat Model Specification**

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

---

# **1\. Scope**

This document defines the deterministic threat model for DKP-PTL-REG v0.6.

This specification:

* Enumerates admissible attack classes  
* Maps each attack class to existing mitigation mechanisms  
* Defines deterministic integrity disclosure rules  
* Prohibits non-deterministic mitigation mechanisms

This document does not introduce:

* New constants  
* New weight multipliers  
* External data sources  
* Manual moderation  
* Reputation systems  
* Machine learning components

All mitigation MUST be expressible using mechanisms already defined in:

* DATA-001  
* CONSTANTS-001  
* REFERENCE-001

---

# **2\. Threat Model Principles**

The registry assumes:

* Adversarial observation submission is possible.  
* Merchant-level manipulation is possible.  
* Subdomain proliferation is possible.  
* Coordinated synthetic bursts are possible.  
* Near-duplicate injection is possible.

The registry does not assume:

* Identity-level adversary tracking.  
* Persistent user tracking.  
* IP-based enforcement.  
* External fraud databases.

Mitigation is strictly statistical and deterministic.

---

# **3\. Attack Classes and Deterministic Mitigation**

---

## **A1. Data Poisoning**

### **Definition**

Injection of extreme or skewed price values intended to distort P\_ref.

### **Deterministic Mitigation**

* Preliminary weighted median (Step 9, DATA-001)  
* MAD\_pre computation (Step 12\)  
* z\_i filtering using z\_max (CONSTANTS-001)  
* Post-outlier renormalization (Step 13\)  
* ColdStart activation (Step 16\)

No additional dispersion constants permitted.

---

## **A2. Burst Amplification**

### **Definition**

Sudden spike in observation count for a domain or bucket.

### **Deterministic Mitigation**

* Stability windows (Step 4\)  
* burst\_threshold\_multiplier  
* early\_window\_multiplier  
* W\_burst penalty application  
* Downstream impact on W\_raw\_i  
* ColdStart if Σ w\_i falls below W\_min

All thresholds defined in CONSTANTS-001.

---

## **A3. Domain Farming**

### **Definition**

Use of multiple subdomains to bypass domain contribution cap.

### **Deterministic Mitigation**

* Root domain extraction via PSL (REFERENCE-001)  
* Domain aggregation (Step 6\)  
* domain\_contribution\_cap\_percent enforcement (Step 7\)  
* Normalization (Step 8\)

Subdomains MUST collapse to eTLD+1.

---

## **A4. Similarity Cluster Injection**

### **Definition**

Injection of near-identical observations differing slightly in time or encoding.

### **Deterministic Mitigation**

* Canonical normalization (REFERENCE-001)  
* Canonical JSON hashing  
* Feature vector construction (Step 10\)  
* Cosine similarity threshold  
* Union-find connected components  
* W\_similarity\_i \= 1 / n\_k  
* Single deterministic recompute (Step 11\)

No recursive recomputation allowed.

---

## **A5. Merchant Proliferation**

### **Definition**

Creation of multiple merchant\_id values to distribute weight.

### **Deterministic Mitigation**

* Domain-level cap (Step 7\)  
* Similarity clustering (Step 10\)  
* Diversity factor W\_diversity (Step 17\)

No identity persistence permitted.

---

# **4\. Integrity Status Disclosure**

The system MUST expose:

integrity\_status ∈ {  
NORMAL,  
BURST\_DETECTED,  
DOMAIN\_DOMINANCE,  
CLUSTER\_COLLAPSE,  
COLD\_START  
}

---

## **4.1 Deterministic Mapping Rules**

Mapping MUST follow strict precedence:

1. COLD\_START  
2. BURST\_DETECTED  
3. DOMAIN\_DOMINANCE  
4. CLUSTER\_COLLAPSE  
5. NORMAL

Only one status MUST be emitted.

---

### **COLD\_START**

Trigger:

cold\_start\_flag \= true  
(as defined in DATA-001 Step 16\)

---

### **BURST\_DETECTED**

Trigger:

For any domain j:

burst\_ratio\_j \> burst\_threshold\_effective

(as computed in Step 4\)

---

### **DOMAIN\_DOMINANCE**

Trigger:

There exists domain j such that:

D\_j\_raw \> domain\_contribution\_cap\_percent × Total\_raw

AND cap was applied in Step 7\.

---

### **CLUSTER\_COLLAPSE**

Define:

Total\_raw\_before\_similarity \= Σ W\_raw\_i (before Step 10\)

Total\_raw\_after\_similarity \= Σ W\_raw\_i (after similarity discount, before Step 11\)

Let:

Cluster\_weight\_loss \=  
Total\_raw\_before\_similarity − Total\_raw\_after\_similarity

Trigger if:

Cluster\_weight\_loss / Total\_raw\_before\_similarity \> 0.30

The 0.30 ratio is fixed in this specification and MUST NOT be externalized as a constant.

---

### **NORMAL**

Trigger:

None of the above conditions satisfied AND  
CS ≥ CS\_display\_threshold

---

# **5\. Deterministic Constraints**

Threat-001 MUST NOT:

* Introduce blacklists  
* Introduce IP heuristics  
* Modify weight formulas  
* Introduce external entropy  
* Introduce adaptive thresholds  
* Use floating precision outside IEEE 754

All integrity\_status triggers MUST be reproducible.

---

# **6\. Output Schema Extension**

All final outputs MUST include:

* integrity\_status  
* applied\_profile  
* protocol\_version  
* constants\_version  
* identity\_scope\_level  
* P\_ref  
* MAD  
* CS  
* N\_eff  
* cold\_start\_flag  
* insufficient\_data\_flag

integrity\_status MUST reflect the highest-precedence triggered condition.

---

# **7\. Deterministic Guarantee**

Given identical:

* Normalized input  
* PSL version  
* protocol\_version  
* constants\_version

All compliant implementations MUST produce identical:

* integrity\_status  
* Weight reductions  
* Cluster behavior  
* Domain cap enforcement  
* ColdStart activation

Any deviation invalidates conformance.

---

# **Final Statement**

DKP-PTL-REG-THREAT-001 v0.6 establishes:

* Closed deterministic attack surface  
* Strictly bounded mitigation space  
* Fully reproducible integrity disclosure  
* Zero external enforcement logic  
* No reputational expansion

Threat model is now formally locked for v0.6.

Источники  
