# Decision Log Database

**Location:** `~/.hermes/decisions/decision_log.db`
**Engine:** SQLite 3.35+ with WAL mode
**Schema version:** 1

## Tables

### decisions

Core table. One row per structured decision.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| timestamp | TEXT | ISO 8601 UTC, default now() |
| pattern | TEXT | Pattern name: tradeoff_matrix, failure_modes, end_to_end, ethics_triage, agentops_trajectory |
| pattern_source | TEXT | Book/source: "DDIA Ch.1", "DDIA Ch.9", etc. |
| session_id | TEXT | Hermes session ID (nullable — direct calls don't have one) |
| agent_model | TEXT | Model that made the decision (e.g., "deepseek-v4-pro") |
| questions_answers | TEXT | JSON array: `[{"q_id": "...", "question": "...", "answer": "..."}]` |
| summary | TEXT | Final decision/conclusion in natural language |
| outcome_verified | INTEGER | 0=unverified, 1=good, -1=bad |
| outcome_notes | TEXT | Free-text notes from review |
| outcome_checked_at | TEXT | When last reviewed |
| git_sha | TEXT | Git SHA at decision time (nullable) |
| project | TEXT | Project context (nullable) |
| tags | TEXT | JSON array of tag strings |

### decision_reviews

Review history. One row per review (can review a decision multiple times).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| decision_id | INTEGER FK | References decisions(id) |
| reviewed_at | TEXT | ISO 8601 UTC |
| outcome | TEXT | "good", "bad", "mixed", "unknown" |
| notes | TEXT | Free-text review notes |
| changed_mind | INTEGER | 0=no, 1=would decide differently now |

## Indexes

- `idx_decisions_pattern` — fast lookup by pattern type
- `idx_decisions_outcome` — fast lookup of unverified decisions
- `idx_decisions_timestamp` — chronological queries

## Query Examples

```sql
-- Decisions needing review (older than 14 days)
SELECT id, pattern, timestamp, summary
FROM decisions
WHERE outcome_verified = 0
  AND timestamp < datetime('now', '-14 days')
ORDER BY timestamp ASC;

-- Decision quality by pattern
SELECT pattern, 
       COUNT(*) as total,
       SUM(CASE WHEN outcome_verified = 1 THEN 1 ELSE 0 END) as good,
       SUM(CASE WHEN outcome_verified = -1 THEN 1 ELSE 0 END) as bad
FROM decisions
WHERE outcome_verified != 0
GROUP BY pattern;

-- Most recent decisions
SELECT id, timestamp, pattern, summary
FROM decisions
ORDER BY timestamp DESC
LIMIT 20;
```

## WAL Mode

The database uses WAL (Write-Ahead Logging) for:
- Concurrent reads during writes
- Better performance for mixed read/write workloads
- 64MB journal size limit (auto-checkpointed)

## Backup

The file is self-contained (single-file SQLite database). Back up with:
```bash
cp ~/.hermes/decisions/decision_log.db ~/backups/decision_log-$(date +%Y%m%d).db
```

## Migration Path to Memory Bridge (Module B)

When Memory Bridge Module B is implemented:
- The `decisions` table here gets a companion `structured_decisions` table in Memory Bridge
- Data can be linked via `session_id` (both systems reference Hermes session IDs)
- The question engine tool continues to write here; Memory Bridge reads from here
- No data migration needed — both systems coexist
