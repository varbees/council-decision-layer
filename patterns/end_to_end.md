# End-to-End Correctness — DDIA Chapter 13

**Source:** Designing Data-Intensive Applications, 2nd Edition, Chapter 13
**When:** Data pipeline changes, database schema changes, multi-service flows

## The Principle

Correctness must be verified end-to-end, not component-by-component. A
system is only as correct as its weakest link. Trust-but-verify: don't
assume each component did its job — check at the boundaries.

## The Framework

### 1. Map the full data flow
User → browser → CDN → API → queue → worker → database → cache → what else?
List EVERY hop. The gaps between hops are where correctness breaks.

### 2. Identify consistency boundaries
Where can data diverge? At each hop, ask:
- Could a write be lost? (crash before ack, buffer flush)
- Could a write be duplicated? (retry without idempotency)
- Could a read be stale? (cache, replica lag, async propagation)
- Could ordering be violated? (concurrent writes, queue reordering)

### 3. Define invariants
What MUST be true at every point? These are your constraints:
- **Uniqueness:** No two users with the same email
- **Referential integrity:** Every order belongs to a real user
- **Business rules:** Payment amount must match invoice amount
- **Temporal:** A photo can't be "delivered" before it's "uploaded"

### 4. Build verification mechanisms
Don't just assert correctness — prove it:
- **Reconciliation jobs:** Compare source-of-truth with derived stores
- **Integrity checks:** Checksums, hash chains, audit logs
- **Canary writes:** Write known values, verify they flow correctly
- **Constraint enforcement:** At DB layer (unique indexes, foreign keys) AND app layer

## Anti-Patterns

- **"The database handles it":** Only if you defined the constraints
- **"The queue is reliable":** Queues drop, duplicate, and reorder messages
- **"The tests pass":** Tests test what you thought of, not what actually happens
- **"It worked in staging":** Production has different data, load, and failure modes

## DDIA Quotable

> "The only way to know whether a system is correct is to check its outputs
> against what you expect. This means defining invariants and writing checks
> that verify those invariants hold." — DDIA Ch.13
