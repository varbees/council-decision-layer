# Privacy & Ethics Impact Triage — DDIA Chapter 14 + Google SAIF

**Source:** DDIA Ch.14 "Doing the Right Thing" + Google Secure AI Framework
**When:** Before shipping any feature that collects, stores, or processes user data

## The Principles

1. **Data is a toxic asset** — Data you don't have is data that can't be leaked,
   subpoenaed, or misused. Every byte you collect is a liability.

2. **Privacy is a decision right** — Users should control what they reveal,
   not have it extracted by default. Consent must be informed and revocable.

3. **Purpose limitation** — Data collected for X should not be used for Y
   without explicit re-consent. Feature creep via data repurposing is a
   privacy violation.

4. **Feedback loops can harm** — Algorithms that learn from user behavior
   can amplify biases, create filter bubbles, and discriminate at scale.

5. **Defense in depth** — Security is not a feature, it's a property of
   the architecture. Multiple layers of protection, not a single gate.

## The Framework

### Gate 1: Necessity
- Is this data **truly necessary** for the feature to function?
- What happens if we **don't** collect it? What's the degraded experience?
- Can we achieve the same outcome with less data?

### Gate 2: Minimization
- What's the **minimum viable data**?
- Can we hash instead of store? Aggregate instead of individual? Sample instead of full?
- Can we process client-side and never send raw data to the server?

### Gate 3: Retention
- What's the **auto-delete policy**? Default: 30 days.
- Does the user know how long their data is kept?
- Is there a self-service delete mechanism?

### Gate 4: Leak Impact
- **Worst-case scenario:** What if this data is breached?
- Who gets harmed? What's the regulatory exposure? What's the reputational damage?
- If the answer is "user trust is destroyed" — find a way to collect less.

### Gate 5: Feedback Loop Detection
- Could this data be used to make decisions about users that **amplify existing biases**?
- Does the algorithm create a **self-reinforcing loop** (popular→more visible→more popular)?
- Can users **see and contest** automated decisions about them?

## Specific to Our Products

### PhotoSelect
- Wedding photos = deeply personal, intimate data
- Guest email/phone collection = third-party data without direct consent
- Payment data = PCI scope (mitigated by Razorpay)
- **Rule:** Never store raw photos unencrypted. Never share guest data with
  studios beyond delivery. Auto-delete delivered photos after 90 days.

### Memory Bridge
- Conversation histories = surveillance-adjacent
- Cross-agent memory = powerful but potentially creepy
- **Rule:** All local. Never upload. User controls which agents are scanned.
  Clear labeling: "This is what YOUR agents know about you."

## Google SAIF Alignment

The Google Secure AI Framework adds technical controls:
- **Input guardrails:** Validate and sanitize all user input
- **Output guardrails:** Filter harmful/biased content before display
- **Audit trails:** Log every data access for compliance
- **Least privilege:** Tools and agents only access what they need

## DDIA Quotable

> "Data is a toxic asset. You want as little of it as possible, you want
> to get rid of it as quickly as you can, and you want to be very careful
> about what you do with it while you have it." — DDIA Ch.14
