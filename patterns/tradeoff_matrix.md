# Trade-Off Matrix — DDIA Chapter 1

**Source:** Designing Data-Intensive Applications, 2nd Edition, Chapter 1
**When:** Architecture and infrastructure decisions

## The Principle

Every architecture decision is a trade-off. There is no "best" — only the
option that best fits your constraints. Making trade-offs explicit prevents
analysis paralysis and post-hoc rationalization.

## The Framework

### Step 1: List your options
Be specific. "Cloud Run" not "the cloud." "Self-hosted Hetzner VPS" not
"our own server." Include the null option: "do nothing, keep current setup."

### Step 2: Pick your dimensions
What actually matters? Common dimensions:
- **Cost** — per-request, per-month, at-scale
- **Latency** — cold start, p50/p99, geographic
- **Operational burden** — who maintains it? What's the pager load?
- **Scalability ceiling** — at what point does it break?
- **Vendor lock-in** — how hard to migrate away?
- **Security surface** — attack vectors, compliance burden
- **Developer experience** — local dev loop, debugging, onboarding

### Step 3: Rank each option on each dimension
Don't overthink this. It's a comparative exercise, not a precision one.
Use: ++ (strong win), + (win), = (neutral), - (loss), -- (strong loss).

### Step 4: Identify knockout constraints
Some constraints disqualify options outright:
- "Must be under ₹500/mo" → kills most managed services
- "Must work in India with <50ms latency" → kills US-only cloud
- "Must be maintainable by 1 person" → kills complex distributed setups
- "Must comply with DPDP" → kills non-India data centers

### Step 5: State the decision with the trade-off acknowledged
Format: "We're going with X because Y, accepting Z as the cost."

Example: "We're going with Cloud Run for PhotoSelect backend because it has
zero ops burden for a solo founder, accepting ~2x higher per-request cost
compared to a VPS at our current zero-revenue stage."

## Anti-Patterns

- **Optimizing prematurely:** Picking the "scalable" option when you have 0 users
- **Ignoring the null option:** Not asking "what if we just don't build this?"
- **Vendor seduction:** Picking the shiny new thing over the boring thing that works
- **Paralysis by dimensions:** Adding 15 dimensions when 3 actually matter

## DDIA Quotable

> "There is no single right answer — there are only trade-offs. Understanding
> the trade-offs is the essence of good architecture." — DDIA Ch.1
