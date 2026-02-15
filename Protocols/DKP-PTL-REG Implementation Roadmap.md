Верно. Никаких «если». Никаких размытых формулировок. Ни одного условного документа.

Ниже — строгий, детерминированный Roadmap, полностью на английском, без комментариев и без альтернативных веток.

---

# **DKP-PTL-REG Implementation Roadmap**

Strict Standard Track (A) — v0.6 Architecture Locked

Strategic Principle  
The standard is published first.  
The implementation is published second.

Normative Architecture (Frozen Set):

* DKP-PTL-REG-001 v0.6  
* DKP-PTL-REG-DATA-001 v0.6  
* DKP-PTL-REG-CONSTANTS-001 v0.6  
* DKP-PTL-REG-THREAT-001  
* DKP-PTL-REG-GOV-001  
* DKP-PTL-REG-REFERENCE-001

No additional documents are normative.

---

## **PHASE 0 — Architecture Freeze**

Objective  
Lock v0.6 as the canonical deterministic architecture.

Actions

* Set protocol\_version \= 0.6.0  
* Set constants\_version \= 0.6.0  
* Freeze all invariants in DKP-PTL-REG-001  
* Freeze 18-step deterministic pipeline in DATA-001  
* Freeze dual-profile structure in CONSTANTS-001  
* Freeze ColdStart semantics  
* Freeze Sybil-resistance mechanisms  
* Freeze hash-only evidence model

Any change to formulas, thresholds, invariants, or state transitions requires version increment.

---

## **PHASE 1 — Deterministic Input Boundary**

Objective  
Define canonical input normalization before DATA-001 execution.

Actions

Create deterministic input specification inside REFERENCE-001:

* domain\_id canonicalization (UTF-8 lowercase, trimmed)  
* merchant\_id canonicalization  
* missing field definition (absent OR empty string)  
* root-domain extraction rules  
* timestamp validation (UTC only)  
* SHA256 hashing rules  
* Evidence hash generation rules  
* Rejection conditions

Input boundary must not alter weighting logic defined in DATA-001.

---

## **PHASE 2 — Engine Formal Validation**

Objective  
Verify that DATA-001 is executable, deterministic, and complete.

Validation Blocks

2.1 Processing Order

* All 18 steps executed exactly once  
* No recursion  
* No implicit recomputation  
* ColdStart short-circuit enforcement

2.2 Domain Cap

* Aggregation correctness  
* Cap enforcement  
* Deterministic redistribution  
* Zero-weight behavior

2.3 Similarity Clustering

* Feature vector construction  
* Missing hash behavior  
* L2 normalization edge cases  
* Deterministic union-find  
* Single recompute enforcement

2.4 Outlier Filtering

* MAD\_pre computation  
* z\_i calculation  
* z\_max enforcement  
* Post-filter renormalization  
* ColdStart after filtering

2.5 Confidence Score

* N\_eff correctness  
* k\_n curve behavior  
* W\_recency aggregation  
* Diversity calculation  
* clamp01 enforcement  
* Display threshold logic

Phase 2 completion requires reproducible identical output for identical input.

---

## **PHASE 3 — Synthetic Stress Testing**

Objective  
Prove numerical stability and attack resistance.

Mandatory datasets

* Uniform competitive market  
* Single dominant domain  
* Coordinated burst attack  
* Sybil amplification  
* Extreme outlier injection  
* Low coverage scenario  
* All identical prices  
* Missing merchant\_id cases  
* Missing domain\_id cases  
* Zero-MAD scenario

Validation criteria

* Stable P\_ref  
* Stable MAD  
* Deterministic N\_eff  
* Correct ColdStart activation  
* Correct domain cap behavior  
* Correct burst suppression  
* No non-deterministic divergence

Phase 3 is incomplete without full reproducibility validation.

---

## **PHASE 4 — Threat Model Specification**

Objective  
Create DKP-PTL-REG-THREAT-001.

Define attacks

* Data poisoning  
* Burst amplification  
* Domain farming  
* Similarity cluster injection  
* Merchant registry abuse

For each attack define

* Detection rule  
* Deterministic mitigation  
* Weight impact  
* ColdStart boundary behavior

Threat specification must not introduce new constants outside CONSTANTS-001.

---

## **PHASE 5 — Governance Layer**

Objective  
Create DKP-PTL-REG-GOV-001.

Define

* Version bump rules  
* Constants modification procedure  
* Profile mapping governance  
* Test vector publication rules  
* Public changelog structure  
* Dispute workflow  
* Appeal mechanism

Governance must not override metric outputs.

---

## **PHASE 6 — Reference Implementation**

Objective  
Create DKP-PTL-REG-REFERENCE-001 and executable engine.

Implement

* Standalone deterministic calculation engine  
* CLI interface  
* JSON input schema  
* JSON output schema  
* Official deterministic test vectors  
* Reproducibility documentation  
* CI deterministic verification

Engine must produce identical outputs across compliant environments.

---

## **PHASE 7 — Legal and Compliance Layer**

Prepare

* Privacy Policy  
* Terms of Use  
* Liability limitation  
* Hash-only evidence statement  
* Data removal procedure  
* Jurisdiction declaration  
* Minimal permission specification

No legal text may modify computational behavior.

---

## **PHASE 8 — Client Layer**

Objective  
Develop extension or API client.

Constraints

* Thin client architecture  
* Passive mode by default  
* No HTML storage  
* No local metric computation  
* Use reference engine exclusively  
* Minimal permissions  
* Display applied\_profile

Client must not influence computation logic.

---

## **PHASE 9 — Closed Deterministic Audit**

Verify

* Cross-document consistency  
* Profile atomicity  
* ColdStart behavior  
* Domain cap enforcement  
* Similarity determinism  
* Burst suppression  
* Reproducibility  
* Legal consistency

Audit must include hash verification of published documents.

---

## **PHASE 10 — Public Release**

Publish

* DKP-PTL-REG-001 v0.6  
* DKP-PTL-REG-DATA-001 v0.6  
* DKP-PTL-REG-CONSTANTS-001 v0.6  
* DKP-PTL-REG-THREAT-001  
* DKP-PTL-REG-GOV-001  
* DKP-PTL-REG-REFERENCE-001  
* Deterministic test vectors  
* Open-source repository  
* Methodology documentation

Release is valid only if deterministic reproducibility is independently verifiable.

---

This roadmap is fully synchronized with v0.6 architecture.  
No optional branches.  
No undefined documents.  
No conditional dependencies.

