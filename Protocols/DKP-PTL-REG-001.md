# **DKP-PTL-REG-001**

## **Pricing Transparency Registry Protocol**

Version 0.6  
 Status: Draft – Deterministic Measurement Standard

---

# **1\. Purpose**

This protocol defines a deterministic, evidence-bound infrastructure for observing and contextualizing publicly available market prices.

The registry:

* Measures contextual price deviation  
* Computes reference prices  
* Quantifies transparency signals  
* Preserves statistical robustness  
* Operates without moral judgement

The registry does not:

* Provide purchasing advice  
* Accuse fraud  
* Issue enforcement actions  
* Override evidence with philosophical criteria

The registry is a measurement layer only.

---

# **2\. Core Invariants**

## **2.1 Observation-Only Principle**

All outputs must derive exclusively from:

* Publicly observable prices  
* Merchant-submitted structured data  
* User-submitted documented observations  
* Logged inquiry outcomes

No speculative inference is permitted.

---

## **2.2 Determinism Requirement**

All metrics must be reproducible from:

* Versioned formulas  
* Versioned constants  
* Versioned schemas

Any change affecting output requires version increment.

---

## **2.3 Evidence Hash Model**

For every observation, the registry must store:

* source\_url  
* timestamp  
* region  
* currency  
* product identity layer  
* observation context vector  
* evidence\_hash

The registry must not store:

* Raw HTML  
* Page snapshots  
* Copyrighted content

Only cryptographic hashes of minimal relevant fragments are permitted.

External archive links are allowed but not stored internally.

---

## **2.4 Explicit Uncertainty Disclosure**

All outputs must display:

* Effective sample size  
* Confidence Score  
* Coverage status  
* Context bucket (OCV)  
* Identity completeness

The system must explicitly indicate when coverage is insufficient.

All outputs MUST include:

\- applied\_profile ∈ {BASE, HARDENED}

\- protocol\_version

\- constants\_version

---

## **2.5 Non-Defamation Constraint**

The registry must not display:

* Fraud claims  
* “Scam” indicators  
* Normative directives  
* Reputational scoring

Only measurable metrics are allowed.

---

## **2.6 Privacy Constraint**

The registry must not store:

* Personal identity  
* Personal email  
* Device fingerprinting beyond entropy-level signals  
* Private correspondence

Only organization-level data may be published.

---

## **2.7 Scope Boundary**

The registry:

* Does not enforce policy  
* Does not apply sanctions  
* Does not override evidence  
* Does not implement justice functions

It is strictly a measurement system.

---

# **3\. System Architecture**

Client (Extension or API Consumer)  
 ↕  
 Registry API  
 ↕  
 Deterministic Calculation Engine  
 ↕  
 Hash-Based Evidence Store  
 ↕  
 Governance & Version Registry

The registry must remain client-agnostic.

---

# **4\. Product Identity Layer (PIL)**

Each observation must include structured product identity attributes:

* brand  
* model  
* sku (if available)  
* condition  
* bundle\_flag  
* warranty\_type (optional)  
* region\_variant (optional)  
* storage\_or\_size (optional)  
* release\_year (optional)

Identity completeness score c\_i ∈ \[0,1\] must be computed deterministically.

If identity is incomplete:

* Weight must be reduced  
* Comparison must remain within compatible identity scope  
  ---

  ## **4.1 Identity Fallback Mechanism**

If insufficient coverage exists under strict identity:

The system may relax identity granularity hierarchically:

1. Ignore cosmetic attributes  
2. Ignore accessory differences  
3. Ignore packaging variants

Such fallback must be flagged as Reduced Identity Scope.

---

# **5\. Observation Context Vector (OCV)**

Each observation must include:

* region  
* currency  
* device\_type  
* logged\_in\_state  
* session\_state

Comparisons are permitted only within identical OCV buckets.

---

# **6\. Data Structures**

## **6.1 MerchantRecord**

merchant\_id  
legal\_name  
domain  
country  
verification\_status  
record\_status  
transparency\_index  
last\_contact\_attempt

---

## **6.2 OfferRecord**

offer\_id  
merchant\_id or domain\_root  
product\_identity\_layer  
observed\_price  
price\_type  
currency  
region  
observation\_context\_vector  
timestamp  
capture\_method  
evidence\_hash  
confidence\_score

---

# **7\. Formal Metrics**

Let O be observations with identical PIL and OCV.

Each observation i has:

* price p\_i \> 0  
* weight w\_i  
* age a\_i  
* identity completeness c\_i

  clamp01(x) \= min(1, max(0, x))  
  ---

  ## **7.1 Observation Weight**

w\_i \= clamp01(  
  W\_source ×  
  W\_time ×  
  W\_identity ×  
  W\_consensus ×  
  W\_domain\_cap ×  
  W\_burst\_penalty  
 )  
W\_diversity ∈ \[0,1\] is defined in DKP-PTL-REG-DATA-001.

If not triggered, W\_diversity \= 1.0.

In v0.6, any weight component not explicitly defined in

DKP-PTL-REG-DATA-001 defaults to 1.0.

---

## **7.2 Temporal Decay**

W\_time \= 2^(−age / T\_half)

Observations older than max\_age\_cutoff may be excluded.

---

## **7.3 Reference Price (Weighted Median)**

Sort observations by (price ascending, timestamp ascending, evidence\_hash ascending).

Let total weight W \= Σ w\_i.

P\_ref is the smallest price where cumulative weight ≥ 0.5W.

If W \< W\_min (as defined in DKP-PTL-REG-CONSTANTS-001) → ColdStartState.

---

## **7.4 Price Position Index**

PPI \= (P\_offer − P\_ref) / P\_ref

Undefined during ColdStartState.

---

## **7.5 Effective Sample Size**

The effective sample size is defined as:

N\_eff \= (Σ w\_i)^2 / Σ (w\_i^2)

Where w\_i are final observation weights after application of

all weight components, caps, clustering, and exclusions.

Weights are not renormalized unless explicitly specified in DATA document.  
Minimum effective sample size threshold (N\_eff\_min) is defined in DKP-PTL-REG-CONSTANTS-001.

---

## **7.6 Confidence Score**

W\_recency \= Σ w\_i

W\_recency is not normalized and reflects absolute effective market coverage.

CS \= clamp01(

  (1 − exp(−k\_n × N\_eff)) ×

  W\_recency ×

  W\_diversity

)

exp(x) denotes the natural exponential function e^x.

Recency attenuation is fully embedded in w\_i via W\_time.

No additional temporal multiplier is applied at Confidence Score stage.

---

## **7.7 Transparency Index**

TI ∈ \[0,1\], derived from:

* Public pricing availability  
* Merchant verification  
* Structured submissions  
* Inquiry logging  
  ---

  # **8\. Statistical Robustness Layer**

  ## **8.1 Median Absolute Deviation (MAD)**

MAD \= median(|p\_i − P\_ref|)

MAD is computed over observations that remain after outlier exclusion.

MAD is unweighted in v0.6.

---

## **8.2 Bundle Handling**

bundle\_only observations must not enter standalone reference sets.

derived\_base observations must be flagged and downweighted.

---

# **9\. Sybil & Manipulation Resistance Layer**

The registry must detect anomalous patterns without identity storage.

---

## **9.1 Domain / Merchant Contribution Cap**

For each PIL+OCV bucket:

No single merchant or domain\_root may contribute more than

domain\_contribution\_cap\_percent

(as defined in DKP-PTL-REG-CONSTANTS-001)

of total weight.

Multiple pages under same domain count as a single capped contributor.

---

## **9.2 Burst Detection**

If observation rate for a given domain or bucket exceeds historical baseline beyond threshold:

* W\_burst\_penalty must reduce influence  
* Integrity flag may be raised  
  ---

  ## **9.3 Diversity Collapse Detection**

If weight concentration across domains exceeds threshold:

* W\_diversity ∈ \[0,1\] must decrease and directly scales CS.  
  ---

  ## **9.4 Similarity Cluster Penalty**

If high proportion of observations share nearly identical evidence patterns:

* Apply cluster penalty  
* Reduce cumulative weight of cluster  
  ---

  ## **9.5 Merchant Registry Integrity**

To prevent fake merchant proliferation:

Merchant verification may require:

* Domain validation  
* DNS proof  
* Legal registry lookup

Unverified domains remain limited in influence.

---

# **10\. Cold Start Model**

* If W \< W\_min or N\_eff \< N\_eff\_min  
* (as defined in DKP-PTL-REG-CONSTANTS-001):  
* P\_ref undefined  
* PPI undefined  
* CS \= 0  
* Status \= Insufficient Market Coverage  
  ---

  # **11\. Governance Layer**

The governance layer must provide:

* Versioned constants registry  
* Public methodology  
* Public test vectors  
* Deterministic reference implementation  
* Documented dispute workflow

No manual override of metric outputs is permitted.

---

# **12\. Non-Commercial Constraint**

The registry must:

* Remain open source  
* Not sell ranking  
* Not allow paid removal  
* Not use registry outputs for targeted advertising

Funding may occur via:

* Donations  
* Crowdfunding  
* Structurally separate merchandise  
  ---

  # **13\. Structural Separation**

Registry infrastructure must remain legally and functionally separate from:

* Merchandise  
* Books  
* Advocacy

Algorithmic outputs must not be influenced by commercial operations.

---

# **14\. Store Compliance**

Client applications must:

* Operate in passive mode by default  
* Request minimal permissions  
* Avoid aggressive scraping  
* Allow user opt-out  
* Publish privacy policy  
  ---

  # **15\. Security**

* Encrypted communication  
* Token-based claim links  
* No default credentials  
* Public audit capability  
* Reproducible builds  
  ---

  # **Summary**

Version 0.6 establishes:

* Deterministic statistical measurement  
* Identity-independent Sybil resistance  
* Domain-level contribution caps  
* Burst and cluster anomaly detection  
* Hash-only evidence storage  
* Cold-start protection  
* Strict neutrality

The registry is a reproducible price measurement protocol.  
It is not an enforcement or reputational system.