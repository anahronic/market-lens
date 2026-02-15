# **DKP-PTL-REG-DATA-001**

Deterministic Data Processing Specification  
Version: 0.6  
Status: Freeze Candidate  
Aligned with:

* DKP-PTL-REG-001 v0.6  
* DKP-PTL-REG-CONSTANTS-001 v0.6

# ---

 **0\. Auxiliary Functions**

clamp01(x) \= min(1, max(0, x))

Initial State:

cold\_start\_flag \= false

insufficient\_data\_flag \= false

P\_ref \= null

MAD \= null

CS \= 0

N\_eff \= 0  
---

**Identity Scope Resolution (Pre-Processing Phase)**

This phase MUST execute exactly once before Step 1\.

Let O\_all be the full candidate observation set after external input validation.

O\_all MUST include only observations that share identical:

* \- Observation Context Vector (OCV)  
* \- region  
* \- currency


No recursion permitted.  
 No backtracking permitted.  
 This phase does not modify weights.

---

## **A. Deterministic Identity Levels**

Level 0:

Match all identity fields exactly.  
Missing fields MUST be treated as empty string "" after normalization.  
Two observations match at a level only if all compared fields are equal after this rule.

Level 1:

Ignore bundle\_flag.

Level 2:

Ignore bundle\_flag and warranty\_type.

No other attributes may be relaxed.

Attribute relaxation order is fixed and immutable.

---

## **B. Resolution Algorithm**

All O\_L MUST be constructed as subsets of O\_all.

Set:

    selected \= false

    identity\_scope\_level \= null

    O \= empty set

For each level L in {0,1,2}:

    Construct O\_L as subset of O\_all under identity level L.

    If |O\_L| ≥ 2:

        identity\_scope\_level \= L

        O \= O\_L for Steps 1–18

        selected \= true

        Break.

If selected \= false:

    O \= empty set for Steps 1–18

    identity\_scope\_level \= null

If identity\_scope\_level \> 0:

    Reduced Identity Scope MUST be reported.

---

## **C. Deterministic Constraints**

* Resolution must execute exactly once.

* Selected identity scope must remain fixed for entire pipeline execution.

* No re-evaluation allowed after Step 1\.

* No additional constants permitted.

* No weighting adjustments permitted in this phase.

---

## **D. Output Schema Extension**

All outputs MUST include:

* identity\_scope\_level

identity\_scope\_level MUST be present.

If no level selected, identity\_scope\_level \= null.

This does not modify applied\_profile logic.

---

# **1\. Deterministic Processing Order**

The following 18 steps MUST be executed exactly once and in the specified order.

No step may be skipped.  
No implicit recomputation is allowed.  
No recursion is allowed.

---

# **2\. Temporal Validation**

For each observation i:

age\_i \= current\_time\_utc − t\_i

If:

age\_i \< 0 → discard observation

age\_i \> max\_age\_cutoff → discard observation

window\_index \= floor(unix\_seconds(t\_i) / stability\_window\_duration\_seconds)

Unix epoch origin \= 1970-01-01T00:00:00Z

---

# **3\. Temporal Weight**

For remaining observations:

W\_time\_i \= 2^(−age\_i / T\_half\_default)

---

# **4\. Burst Detection**

For each domain j:

Define fixed, non-overlapping stability windows aligned to UTC epoch boundaries.

Compute:

N\_recent\_j

N\_baseline\_j \= median(counts in last 7 windows)

If baseline windows \< 3:

burst\_threshold\_effective \= early\_window\_multiplier

Else:

burst\_threshold\_effective \= burst\_threshold\_multiplier

If N\_baseline\_j \= 0:

Use global baseline

Compute:

burst\_ratio\_j \= N\_recent\_j / max(N\_baseline\_j, 1\)

If:

burst\_ratio\_j \> burst\_threshold\_effective:

    W\_burst\_j \= 1 / burst\_ratio\_j

Else:

    W\_burst\_j \= 1

---

# **5\. Raw Observation Weight**

For each observation i:

W\_raw\_i \= W\_time\_i × W\_burst\_j

---

# **6\. Domain Aggregation**

Domains j considered in Steps 6–8 are those with at least one remaining observation.

For each domain j:

D\_j\_raw \= Σ W\_raw\_i  (over observations in domain j)

Let:

Total\_raw \= Σ D\_j\_raw

---

# **7\. Domain Cap**

For each domain j:

D\_j\_capped \= min(D\_j\_raw, domain\_contribution\_cap\_percent × Total\_raw)

Let:

Total\_capped \= Σ D\_j\_capped

If Total\_capped \= 0:

    Set:

        P\_ref \= null

        MAD \= null

        N\_eff \= 0

        CS \= 0

        cold\_start\_flag \= true

        insufficient\_data\_flag \= true

If cold\_start\_flag \= true, Steps 8–18 MUST be no-op and MUST preserve previously set state variables.

---

# **8\. Domain Normalization and Observation Weights**

For each domain j:

    D\_j \= D\_j\_capped / Total\_capped

For each observation i in domain j:

    If D\_j\_raw \= 0:

        w\_i \= 0

    Else:

        w\_i \= W\_raw\_i × (D\_j / D\_j\_raw)

---

# **9\. Preliminary Reference Price**

Sort tuples:

(p\_i, tie\_key\_i, w\_i)

Ascending by:

1. p\_i  
2. tie\_key\_i (lexicographic)

Where:

tie\_key\_i \=

(

  domain\_id\_utf8\_lowercase,

  merchant\_id\_utf8\_lowercase,

  t\_i,

  p\_i

)

Compute weighted median:

Find smallest k such that cumulative Σ w\_i ≥ 0.5

P\_ref\_pre \= p\_k

---

# **10\. Similarity Groups**

Two observations may be considered for clustering if and only if they share:

domain\_id OR merchant\_id

Similarity is computed only within deterministic groups.

Feature vector:

Since p\_i \> 0 (per Protocol), P\_ref\_pre \> 0 and division is well-defined.

normalized\_price\_i \= p\_i / P\_ref\_pre

normalized\_time\_i  \= age\_i / max\_age\_cutoff

domain\_hash\_i      \= SHA256(domain\_id)\[0:64bits\] normalized to \[0,1\]

merchant\_hash\_i    \= SHA256(merchant\_id)\[0:64bits\] normalized to \[0,1\]

Definition: "missing" means the field is absent OR equals "" after UTF-8 lowercase normalization.

If merchant\_id is missing:

    merchant\_hash\_i \= 0

If domain\_id is missing:

    domain\_hash\_i \= 0

Vector:

feature\_vector\_i \=

\[

 normalized\_price\_i,

 normalized\_time\_i,

 domain\_hash\_i,

 merchant\_hash\_i

\]

If ||feature\_vector\_i||\_2 \= 0:

    feature\_vector\_i remains unnormalized

Else:

    feature\_vector\_i \= feature\_vector\_i / ||feature\_vector\_i||\_2

Cosine similarity:

S\_ij \= dot(feature\_vector\_i, feature\_vector\_j)

If:

S\_ij ≥ similarity\_threshold

→ same cluster.

For cluster k of size n\_k:

W\_similarity\_i \= 1 / n\_k

Update:

W\_raw\_i \= W\_raw\_i × W\_similarity\_i

Clusters are defined as connected components under relation

S\_ij \>= similarity\_threshold.

Connected components MUST be computed deterministically using

union-find over observations sorted by (p\_i ascending, tie\_key\_i ascending).

Domain aggregation is not updated until Step 11\.

---

# **11\. Single Deterministic Recompute**

Repeat:

* Step 6  
* Step 7  
* Step 8  
* Step 9

Exactly once.

No further repetitions allowed.

---

# **12\. Outlier Filtering**

Compute:

MAD\_pre \= median(|p\_i − P\_ref\_pre|)

If:

MAD\_pre \= 0:

    For all i: z\_i \= 0

Else:

    z\_i \= |p\_i − P\_ref\_pre| / MAD\_pre

If:

z\_i \> z\_max → discard observation

---

# **13\. Post-Outlier Renormalization**

Recompute:

* Domain aggregation  
* Domain cap  
* Domain normalization

As defined in Steps 6–8.

If Σ w\_i \= 0:

    Set:

        P\_ref \= null

        MAD \= null

        N\_eff \= 0

        CS \= 0

        cold\_start\_flag \= true

        insufficient\_data\_flag \= true

D\_j values after Step 13 are the final normalized domain weights used in subsequent computations.  
If cold\_start\_flag \= true, Steps 14–18 MUST be no-op and MUST preserve previously set state variables.

---

# **14\. Final Reference Price**

Recompute weighted median as defined in Step 9\.

P\_ref \= final weighted median

Compute final MAD:

MAD \= median(|p\_i − P\_ref|)

over remaining observations after Step 13\.  
MAD is unweighted in v0.6.

---

# **15\. Effective Sample Size**

Using final observation weights w\_i produced by Step 13:

N\_eff \= (Σ w\_i)^2 / Σ (w\_i^2)

---

# **16\. ColdStart Check**

If Σ w\_i \< W\_min OR N\_eff \< N\_eff\_min:

    Set:

        P\_ref \= null  
        MAD \= null

        CS \= 0

        cold\_start\_flag \= true

        insufficient\_data\_flag \= true

If cold\_start\_flag \= true, Steps 17–18 MUST be no-op and MUST preserve previously set state variables.

---

# **17\. Confidence Score**

Core:

CS\_core \= 1 − exp(−k\_n × N\_eff)

Recency:

W\_recency \= Σ w\_i

Diversity:

W\_diversity \= 1 − max(D\_j)

Final:

CS \= clamp01(

    CS\_core × W\_recency × W\_diversity

)

---

# **18\. Display Rule**

If:

CS \< CS\_display\_threshold:

    Output: Low Confidence

Else:

    Output: Market Reference Price \= P\_ref

---

# **Determinism Requirements**

All computations MUST:

* Use IEEE 754 double precision  
* Use round half to even  
* Round all externally exposed metrics to 6 decimal places  
* Use stable sorting with deterministic tie-breaking  
* Produce identical output for identical input

Output Schema Requirements

All outputs MUST include:

\- applied\_profile  
\- protocol\_version  
\- constants\_version  
\- identity\_scope\_level  
\- P\_ref  
\- MAD  
\- CS  
\- N\_eff  
\- cold\_start\_flag  
\- insufficient\_data\_flag

