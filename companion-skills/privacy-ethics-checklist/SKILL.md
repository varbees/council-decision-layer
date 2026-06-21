---
name: privacy-ethics-checklist
description: Pre-build privacy and ethics gate. Load before shipping any feature that collects, stores, or processes user data.
version: 1.0.0
author: Hermes + Harsha Beesabathiba (Antharmaya Labs)
license: MIT
tags: [privacy, ethics, compliance, security, ddia, saif]
hermes:
  trigger_on:
    - "user data"
    - "tracking"
    - "analytics"
    - "privacy"
    - "personal data"
    - "collect email"
    - "collect phone"
    - "store photo"
    - "GDPR"
    - "DPDP"
    - "consent"
    - "data retention"
    - "third-party"
    - "API key"
    - "PII"
  related_skills:
    - council-decision-layer
---

# Privacy & Ethics Pre-Build Checklist

**Source:** DDIA Ch.14 + Google Secure AI Framework (SAIF)
**Use:** BEFORE writing code that touches user data. This is a gate, not a
retrospective review.

## Quick Gate (30 seconds)

Ask these three before anything else:

1. **Is this data truly necessary?** Yes → proceed. No → STOP, don't build this.
2. **What's the minimum viable data?** Collect less than you think you need.
3. **What happens if this leaks?** If the answer is "catastrophic" → find another way.

If you pass the quick gate, proceed to the full checklist.

---

## Full Checklist

### 🔒 Data Collection

- [ ] Is every field **necessary**? Can any field be removed?
- [ ] Are we collecting the **minimum** version? (hash instead of raw, count instead of list)
- [ ] Is collection **opt-in** or opt-out? Prefer opt-in.
- [ ] Is the purpose **clearly communicated** to the user?
- [ ] Are we collecting **third-party data** (guest emails, phone numbers)? Special rules apply.

### 🗑️ Data Retention

- [ ] What's the **auto-delete policy**? Default: 30 days for user content.
- [ ] Is auto-deletion **automatic** or manual? Prefer automatic.
- [ ] Does the user have a **self-service delete** mechanism?
- [ ] Are **backups** included in the deletion scope?
- [ ] Is retention **configurable** per-tenant for B2B?

### 🛡️ Data Security

- [ ] Is data **encrypted at rest**? (default for all new features)
- [ ] Is data **encrypted in transit**? (HTTPS, TLS)
- [ ] Are **access controls** in place? Who can read this data?
- [ ] Are **audit logs** enabled for all data access?
- [ ] Is the **attack surface** documented? What are the threat vectors?

### 📋 Compliance

- [ ] **DPDP-aligned**? (India's data protection law — mandatory)
- [ ] **Consent mechanism** in place? Recorded? Revocable?
- [ ] **Data processing agreement** needed? (if using third-party processors)
- [ ] **Cross-border data transfer**? If yes, where and why?
- [ ] **Data Protection Officer** or equivalent responsibility assigned? (solo founder = you)

### 🔁 Feedback Loop Audit

- [ ] Does this feature **make decisions about users**? (rankings, recommendations, filters)
- [ ] Could it create a **self-reinforcing feedback loop**? (popular → more visible → more popular)
- [ ] Are there **protected attributes** that could be used for discrimination?
- [ ] Can users **see why** a decision was made about them?
- [ ] Can users **contest** an automated decision?

### 🚦 Go/No-Go

- [ ] **All gates pass** → Proceed with build
- [ ] **Minor concerns only** → Proceed, file issues to address within 30 days
- [ ] **Major concerns** → Redesign to eliminate the concern before building

---

## Product-Specific Rules

### PhotoSelect

- Wedding photos = **deeply personal**. Encrypt at rest ALWAYS.
- Guest contact info = **third-party data** without direct consent. Minimize.
- Payment data = Razorpay handles PCI. Don't touch raw card data EVER.
- **Auto-delete** delivered photos after 90 days (configurable by studio).
- **No facial recognition** without explicit opt-in disclosure.

### Memory Bridge

- Conversation histories = **surveillance-capable**. Local only. NEVER upload.
- Agent-scanning = **user-controlled**. User picks which agents to scan.
- **Clear labeling**: "Memory Bridge knows what your agents have discussed."
- **Export/delete**: User can export their index or delete it entirely.

### Baggsy

- School fee data = **financial + child data** (dual sensitivity).
- Parent phone numbers = **sensitive**. No marketing use without consent.
- Fee history = **don't sell, don't share, don't analyze beyond the feature**.

---

## Post-Build Verification

After building, verify:

- [ ] **Data flow diagram** accurate? (what touches what)
- [ ] **Access control test**: Can an unauthorized user read this data?
- [ ] **Leak scenario test**: If this DB table leaked, what's exposed?
- [ ] **Deletion test**: Does auto-delete actually work?
- [ ] **Consent test**: Can a user revoke consent and have their data deleted?

---

## Related

- Load `council-decision-layer` pattern `ethics_triage` for structured Q&A
- See `council-decision-layer/patterns/ethics_triage.md` for the full framework
- Google SAIF: https://safety.google/cybersecurity-advancement/saif/
- DDIA Ch.14: `~/Desktop/Kleppmann M., Riccomini C. - Designing Data-Intensive Applications, 2nd Edition - 2026.pdf`

---

## Sharp Edges

- **This is a checklist, not legal advice.** For actual compliance (DPDP, GDPR),
  consult a lawyer.
- **The checklist is advisory.** It doesn't block deploys — it informs decisions.
  You can override any gate if you have good reason.
- **Auto-delete is easy to promise, hard to implement.** Backup systems, caches,
  and replicas all need to be included. Plan for this.
