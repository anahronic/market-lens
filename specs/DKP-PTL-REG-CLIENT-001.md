# **DKP-PTL-REG-CLIENT-001**

## **Deterministic Client Interpretation Specification**

Version: 0.6  
 Status: Freeze    
 Layer: Non-Normative Client Layer

Aligned with:

* DKP-PTL-REG-001 v0.6

* DKP-PTL-REG-DATA-001 v0.6

* DKP-PTL-REG-CONSTANTS-001 v0.6

* DKP-PTL-REG-THREAT-001 v0.6

---

# **1\. Scope**

This specification defines deterministic mapping rules from registry output metrics to client-visible signals.

The client layer:

* Interprets registry outputs

* Classifies price deviation

* Maps signals to visual representation

* Provides access to registry data

This specification does NOT:

* Modify computation logic

* Introduce weights

* Override registry outputs

* Perform inference or estimation

All behavior MUST be deterministic and reproducible.

---

# **2\. Input Requirements**

Client MUST consume registry output fields:

* P\_ref

* CS

* N\_eff

* MAD

* integrity\_status

* cold\_start\_flag

* insufficient\_data\_flag

* identity\_scope\_level

* applied\_profile

* protocol\_version

* constants\_version

* region

* currency

Client MUST obtain from page context:

* P\_offer

* P\_offer.currency

* P\_offer.region

---

## **2.1 Offer Context Validation**

If:

P\_offer.currency ≠ registry.currency  
OR  
P\_offer.region ≠ registry.region

→

SIGNAL \= NO\_DATA

Constraints:

* No currency conversion permitted

* No region inference permitted

---

## **2.2 MAD Usage Constraint**

MAD is included for schema completeness.

Client MUST:

* NOT use MAD in classification

* NOT derive thresholds from MAD

* MAY display MAD in extended UI (optional)

MAD has zero influence on SIGNAL.

---

# **3\. Signal State Space**

SIGNAL ∈ {  
   BELOW\_MARKET,  
   SLIGHTLY\_BELOW,  
   NEAR\_MARKET,  
   SLIGHTLY\_ABOVE,  
   ABOVE\_MARKET,  
   NO\_DATA  
}

Signal space is finite and deterministic.

---

# **4\. Threshold Definitions**

T\_near \= 0.05  
T\_low  \= 0.15  
T\_high \= 0.15

Constraints:

* T\_near ≥ 0

* T\_low \> T\_near

* T\_high \> T\_near

Thresholds are:

* immutable within version

* independent of engine constants

---

# **5\. Classification Logic**

All calculations MUST use IEEE 754 double precision.  
 No rounding permitted before classification.

---

## **5.1 Cold Start Override**

If:

cold\_start\_flag \= true  
OR  
P\_ref \= null

→

SIGNAL \= NO\_DATA  
---

## **5.2 Confidence Gate**

If:

CS \< CS\_display\_threshold

→

SIGNAL \= NO\_DATA

Where:

CS\_display\_threshold is selected from CONSTANTS-001  
using applied\_profile from registry output.  
---

## **5.3 Missing Offer Price**

If:

P\_offer is undefined

→

SIGNAL \= NO\_DATA  
---

## **5.4 PPI Calculation**

PPI \= (P\_offer − P\_ref) / P\_ref  
---

## **5.5 Deterministic Classification**

### **BELOW\_MARKET**

PPI ≤ −T\_low  
---

### **SLIGHTLY\_BELOW**

−T\_low \< PPI \< −T\_near  
---

### **NEAR\_MARKET (symmetric zone)**

−T\_near ≤ PPI ≤ T\_near  
---

### **SLIGHTLY\_ABOVE**

T\_near \< PPI \< T\_high  
---

### **ABOVE\_MARKET**

PPI ≥ T\_high  
---

## **5.6 Boundary Rule**

Boundary handling is symmetric:

* PPI \= −T\_near → NEAR\_MARKET

* PPI \= \+T\_near → NEAR\_MARKET

No asymmetry permitted.

---

# **6\. Color Mapping**

BELOW\_MARKET     → GOLD  
SLIGHTLY\_BELOW   → LIGHT\_GOLD  
NEAR\_MARKET      → GREEN  
SLIGHTLY\_ABOVE   → ORANGE  
ABOVE\_MARKET     → RED  
NO\_DATA          → GRAY

Hex:

GOLD        \= \#C9A227  
LIGHT\_GOLD  \= \#E6C65C  
GREEN       \= \#2ECC71  
ORANGE      \= \#F39C12  
RED         \= \#E74C3C  
GRAY        \= \#95A5A6  
---

# **7\. Integrity Status Overlay**

Integrity does NOT affect SIGNAL.

NORMAL → no overlay

BURST\_DETECTED → warning flag

DOMAIN\_DOMINANCE → dominance flag

CLUSTER\_COLLAPSE → clustering warning

COLD\_START → handled via NO\_DATA  
---

# **8\. Identity Scope Disclosure**

If:

identity\_scope\_level \> 0

→

Display:

"Reduced Identity Scope"  
---

# **9\. Tooltip Specification**

Client MUST display:

Reference Price: P\_ref  
Offer Price: P\_offer  
Deviation: PPI (%)  
Confidence Score: CS  
Effective Sample Size: N\_eff  
MAD: MAD  
Integrity Status: integrity\_status  
Profile: applied\_profile

Formatting:

* numeric precision: 6 decimal places

* percentage: explicit sign

---

# **10\. Click Behavior**

Open:

/market-lens?product\_id=...\&region=...\&currency=...

Client MUST NOT compute additional metrics.

---

# **11\. Deterministic Constraints**

Client MUST:

* be stateless

* not cache beyond session

* not smooth values

* not interpolate

* not personalize

---

## **11.1 Temporal Stability**

Client MUST:

* use registry values as-is

* not re-fetch within same render cycle

Temporal stability is guaranteed by registry TTL.

---

# **12\. Versioning**

client\_version \= 0.3  
protocol\_version  
constants\_version  
---

# **13\. Failure Modes**

## **API Failure**

SIGNAL \= NO\_DATA  
---

## **Partial Response**

If any required field missing:

SIGNAL \= NO\_DATA  
---

## **Invalid Values**

If:

P\_ref ≤ 0  
OR  
CS \< 0  
OR  
CS \> 1

→

SIGNAL \= NO\_DATA  
---

# **14\. Non-Override Rule**

Client MUST NOT:

* provide purchase advice

* label fraud

* rank merchants

* suggest best deals

---

# **Final Statement**

DKP-PTL-REG-CLIENT-001 v0.6 establishes:

* fully deterministic UI mapping

* complete schema alignment with DATA-001

* profile-consistent confidence gating

* symmetric classification boundaries

* strict separation from computation

The client layer is:

* bounded

* reproducible

* audit-compatible

