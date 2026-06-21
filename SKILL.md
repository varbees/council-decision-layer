---
name: council-decision-layer
description: Structured decision-making using DDIA & AgentOps frameworks. Load when facing architecture, strategy, or prioritization decisions.
version: 1.0.0
author: Hermes + Harsha Beesabathiba (Antharmaya Labs)
license: MIT
tags: [decision-making, architecture, strategy, agentops, ddia]
hermes:
  trigger_on:
    - "architecture decision"
    - "which approach"
    - "trade-off"
    - "tradeoff"
    - "pros and cons"
    - "should we use"
    - "should we build"
    - "should we deploy"
    - "should we migrate"
    - "should we switch"
    - "what's the best way"
    - "cloud vs self-host"
    - "monolith vs microservice"
    - "before we deploy"
    - "is this safe to ship"
  tools:
    - council-decision-layer/tools/question_engine.py
---

# Council Decision Layer

When I (Hermes) face a decision that has real consequences — architecture, strategy, prioritization, privacy, deployment risk — I load this skill and invoke the question engine to structure the decision-making process.

## When to Use

| Decision type | Pattern to use | Trigger phrases |
|--------------|----------------|-----------------|
| Architecture choice (cloud vs self-host, monolith vs microservice) | `tradeoff_matrix` | "which approach", "cloud vs", "what stack" |
| Pre-deployment risk assessment | `failure_modes` | "before we deploy", "what could break", "blast radius" |
| Data pipeline / Memory Bridge changes | `end_to_end` | "data flow", "consistency", "pipeline" |
| Any user-data or tracking feature | `ethics_triage` | "user data", "tracking", "privacy", "analytics" |
| Multi-step agent task planning | `agentops_trajectory` | "agent should do X", "delegate to", "multi-step task" |

## How It Works

1. I detect a decision point (via trigger phrases above)
2. I load the relevant pattern
3. I present 3-5 structured questions to Harsha
4. Harsha answers (can skip or defer)
5. I log the Q&A + decision to `~/.hermes/decisions/decision_log.db`
6. Future sessions can search and review past decisions

## Available Patterns

| Pattern | Source | Questions | Use Case |
|---------|--------|-----------|----------|
| `tradeoff_matrix` | DDIA Ch.1 | 5 | Architecture choices — make trade-offs explicit |
| `failure_modes` | DDIA Ch.9 | 5 | Pre-deployment risk — what could break? |
| `end_to_end` | DDIA Ch.13 | 4 | Data pipelines — verify correctness end-to-end |
| `ethics_triage` | DDIA Ch.14 + SAIF | 5 | Privacy impact — before collecting user data |
| `agentops_trajectory` | Google Agent Guide §3 | 5 | Agent task planning — evaluate reasoning path |

## Tool Actions

```python
# Invoke via Hermes tool system or direct Python
question_engine_tool(action="list_patterns")
question_engine_tool(action="ask", pattern_name="tradeoff_matrix")
question_engine_tool(action="log", pattern_name="failure_modes", questions_answers=[...], summary="...")
question_engine_tool(action="review", decision_id=12, outcome="good", notes="...")
question_engine_tool(action="pending", days_old=14)
question_engine_tool(action="search", query="photoselect deployment")
```

## Database

- Location: `~/.hermes/decisions/decision_log.db`
- Tables: `decisions` (pattern, Q&A, summary, outcome), `decision_reviews` (post-hoc evaluation)
- Schema is auto-created on first use

## Context

These patterns are derived from two books available on Harsha's system:
- **Designing Data-Intensive Applications, 2nd Edition** (Kleppmann/Riccomini, 2026)
- **Google Startup Technical Guide: AI Agents** (Google Cloud, 2026)

See `references/source_mapping.md` for exact chapter-to-pattern mapping.

---

## Using the Question Engine

### Interactive flow

When I detect a decision, I'll say something like:

> This looks like an architecture decision. Let me use the **Trade-Off Matrix** (DDIA Ch.1):
>
> 1. What are the options you're choosing between?
> 2. What dimensions matter? (cost, latency, ops burden, etc.)
> 3. For each dimension, which option wins?
> 4. What constraints are non-negotiable?
> 5. Based on the trade-offs, what's your decision?
>
> Answer each, or reply "skip" to skip. Reply "done" when finished and I'll log the decision.

### After logging

The decision is stored with:
- Which pattern was used
- All Q&A pairs
- Summary of the final decision
- Session ID for traceability
- Timestamp

### Review cycle

Weekly (or on-demand), I check for decisions older than 14 days that haven't been outcome-verified and ask:

> You decided X on [date] using the Trade-Off Matrix. Did it work out? (good / bad / mixed)

This closes the feedback loop.

---

## Extending

To add a new pattern:

1. Define it in `question_engine.py` → `PATTERNS` dict
2. Add a reference file in `patterns/`
3. Add trigger phrases to this SKILL.md's `trigger_on` list
4. Map it in `references/source_mapping.md`

Patterns are portable — share them as markdown files between installations.

---

## Related Skills

- `privacy-ethics-checklist` — Module D: pre-build privacy gate (loads ethics_triage pattern)
- `memory-bridge` (future) — Module B: stores structured decisions in Memory Bridge

---

## Sharp Edges

- **No LLM in the tool itself** — the question engine is deterministic. I (the agent) do the reasoning about WHICH pattern to use. The tool just presents questions and logs answers.
- **The quality depends on the LLM choosing the right pattern** — if I pick `tradeoff_matrix` when I should pick `ethics_triage`, the wrong questions get asked. Future improvement: a pattern-suggestion classifier.
- **No enforcement** — the tool logs decisions but doesn't block bad ones. It's an advisory framework, not a permission system.
