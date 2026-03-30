# Data Dispute Policy

**Document ID:** ML-LEGAL-DISPUTE-001  
**Version:** 1.0  
**Status:** Freeze  
**Effective Date:** 2026-03-31  

---

## 1. Purpose

This policy defines the process for disputing or requesting correction of Market Lens observation data.

---

## 2. What Can Be Disputed

Disputes may be submitted for:

- **Observation data errors:** Incorrect price extraction, timestamp errors
- **Normalization errors:** Misapplied currency conversion, unit normalization failures
- **Product identity mapping errors:** Incorrect brand/model/SKU linkage, wrong condition classification
- **Missing context:** Relevant data sources not observed, incomplete coverage affecting metrics

---

## 3. What Cannot Be Requested

The following are **not available** through the dispute process:

- **Manual override of metrics:** P_ref, CS (Coverage Score), integrity_status, or other computed values cannot be manually adjusted
- **Discretionary rewriting:** Outputs cannot be altered based on preference or negotiation
- **Suppression of valid observations:** Correctly captured data will not be removed because it is unfavorable
- **Retroactive data deletion:** Historical observations remain part of the versioned audit trail

---

## 4. Deterministic Correction Path

Valid disputes trigger **recomputation through normal pipelines**. This means:

1. The disputed data point is flagged for review
2. If an error is confirmed, source data is re-extracted or corrected
3. The corrected input is processed through standard normalization
4. New outputs replace erroneous outputs in subsequent versions
5. Historical versions remain available for audit (immutability per GOV-001)

No human override of deterministic logic is applied. Corrections flow through the same pipeline as original observations.

---

## 5. Submission Format

Dispute submissions must include:

| Field | Required | Description |
|-------|----------|-------------|
| `dispute_type` | Yes | One of: `observation_error`, `normalization_error`, `identity_mapping_error`, `missing_context` |
| `affected_entity` | Yes | Product ID, observation ID, or metric identifier |
| `description` | Yes | Specific description of the alleged error |
| `evidence` | Yes | Supporting documentation (screenshots, source URLs, timestamps) |
| `expected_correction` | Optional | What the submitter believes the correct value should be |
| `contact` | Yes | Email or other contact method for response |

Submissions missing required fields will be returned without processing.

---

## 6. Review Flow

1. **Receipt:** Submission acknowledged within 5 business days
2. **Triage:** Submission classified by dispute type and severity
3. **Investigation:** Technical review of alleged error against source data and pipeline logic
4. **Determination:** One of:
   - `CONFIRMED`: Error verified, correction scheduled
   - `NOT_CONFIRMED`: No error found, rationale provided
   - `PARTIAL`: Some elements confirmed, others not
5. **Resolution:** If confirmed, recomputation triggered; updated outputs published in next release cycle

---

## 7. Expected Output

Upon resolution, the submitter receives:

- Determination status (`CONFIRMED`, `NOT_CONFIRMED`, `PARTIAL`)
- Explanation of findings
- If corrected: reference to updated data version
- If not corrected: technical rationale for determination

---

## 8. Governance Reference

This policy operates under DKP-PTL-REG-GOV-001 governance rules:

- No changes to frozen logic without version increment
- Historical data remains immutable
- All corrections flow through deterministic pipelines

---

## 9. Contact

Submit disputes to:

- **Email:** [dispute contact to be specified]
- **Subject line format:** `[ML-DISPUTE] <dispute_type> - <affected_entity>`

---

*End of Document*
