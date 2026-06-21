# Failure Mode Enumeration — DDIA Chapter 9

**Source:** Designing Data-Intensive Applications, 2nd Edition, Chapter 9
**When:** Pre-deployment risk assessment, "what could go wrong?"

## The Principle

Distributed systems fail in predictable ways. Enumerate failure modes
systematically before deploying, not after the incident. Most failures
fall into a small set of categories: network, clock, process pause, and
cascading effects.

## The Framework

### 1. Network Failures
Networks are unreliable. Packets get dropped, delayed, duplicated, reordered.
- What's your timeout? What happens on timeout? Retry? Fail?
- Is your system safe under partition (split-brain)?
- Are you assuming synchronous communication where it's actually async?

### 2. Clock Failures
Clocks drift. NTP fails silently. Leap seconds happen.
- What breaks if `clock_a > clock_b` when it shouldn't be?
- Are TTLs, leases, rate limits safe under clock skew?
- Does ordering depend on wall-clock timestamps? (It shouldn't.)

### 3. Process Pauses
Garbage collection, container freezes, OS scheduler preemption.
- What happens if your process is frozen for 10 seconds? 60 seconds?
- Do heartbeats/leases expire? Can another node take over prematurely?
- Are your timeouts shorter than your expected pause durations?

### 4. Cascading Failures
One thing breaks → downstream things break → more things break.
- What's the blast radius of each component?
- Do you have circuit breakers? Bulkheads? Retry budgets?
- Can a slow dependency take down the whole system?

### 5. Byzantine Faults
Nodes that lie, not just crash. Rare but real (bugs, compromises, corrupt data).
- What happens if a node returns garbage data?
- Are integrity checks in place (checksums, signatures, constraint validation)?
- Defense in depth: never trust a single node's answer.

## Checklist (Run Before Every Deployment)

- [ ] What's the worst-case failure of this change?
- [ ] What's the blast radius? Who/what else breaks?
- [ ] What's the rollback plan? How fast can we undo?
- [ ] Are there new single points of failure?
- [ ] Are timeouts and retries appropriate for the new path?
- [ ] Does this change assume something that isn't guaranteed?

## DDIA Quotable

> "It is important to think about what can go wrong, and to design systems
> that are resilient to those failure modes." — DDIA Ch.9
