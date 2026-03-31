# Protocol Compliance and Official Implementation Policy

---

## Purpose

Market Lens is a deterministic, protocol-driven system. Public forks, modified implementations, or research variants may diverge from the official protocol behavior. This document defines what qualifies as an official, compliant, or unofficial implementation.

---

## Official Implementation

An implementation may be presented as **"Official Market Lens"** only if all of the following are true:

1. It is explicitly authorized by the author (Igor Opolinsky)
2. It follows the published protocol specifications and reference behavior without undocumented deviations
3. It preserves deterministic and reproducible behavior as defined by the project
4. It does not misrepresent modified behavior as original behavior
5. It passes all official conformance tests without modification

Unauthorized use of "Official Market Lens" branding is prohibited.

---

## Unofficial and Modified Implementations

Forks, adaptations, wrappers, research branches, or derivative systems are permitted for non-commercial use under the license terms.

However, such implementations:

- **Must not** be described as "Official Market Lens" unless explicitly authorized
- **Must not** imply endorsement, affiliation, or certification by the author
- **Must** clearly indicate their modified or derivative status when distributed publicly

---

## Required Notice for Public Derivatives

Any public derivative that modifies protocol behavior, extraction logic, or output semantics must include a clear notice stating:

1. That it is a modified version
2. That it is not the official implementation
3. That results may differ from the reference implementation

### Suggested Notice

Derivatives may use or adapt the following text:

> This project is a modified derivative of Market Lens and is not the official Market Lens implementation. Behavior and outputs may differ from the reference version.

---

## Relationship to License

This document clarifies protocol and identity integrity expectations. It must be read together with:

- [LICENSE](LICENSE) — Full license terms
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) — Commercial licensing information

Compliance with protocol integrity expectations does not override or replace license terms.

---

## Misrepresentation Prohibition

It is prohibited to present modified, partially compliant, or behaviorally divergent implementations as equivalent to the official Market Lens system.

Any claim of equivalence, compatibility, compliance parity, or result parity must be demonstrably supported by passing the official conformance tests without modification.

---

## Contact

For questions about official implementation status or authorization:

**Igor Opolinsky**  
licensing-contact@example.com
