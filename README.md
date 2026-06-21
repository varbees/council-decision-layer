# 🧠 Council Decision Layer

**Structured decision-making for Hermes Agent.** Stop making ad-hoc architecture and strategy decisions. Use proven frameworks — all through a curl-installable Hermes skill.

```bash
curl -fsSL https://raw.githubusercontent.com/varbees/council-decision-layer/main/install.sh | bash
```

## What You Get

| Component | What It Does |
|-----------|-------------|
| **5 Decision Patterns** | Trade-off Matrix, Failure Mode Enumeration, End-to-End Correctness, Privacy Triage, AgentOps Trajectory |
| **Question Engine** | Deterministic Python tool — presents structured questions, logs answers to SQLite |
| **Decision Log** | Every decision recorded with rationale, pattern used, and outcome tracking |
| **Privacy Checklist** | Pre-build privacy/ethics gate (DPDP-aligned, DDIA Ch.14-based) |
| **85 Tests** | Component-tested, DB-isolated, SQL-injection hardened |

## Available Patterns

| Pattern | When to Use | Source |
|---------|------------|--------|
| `tradeoff_matrix` | Architecture choices (cloud vs self-host, monolith vs microservice) | DDIA Ch.1 |
| `failure_modes` | Pre-deployment risk assessment | DDIA Ch.9 |
| `end_to_end` | Data pipeline correctness verification | DDIA Ch.13 |
| `ethics_triage` | Before collecting/storing user data | DDIA Ch.14 + SAIF |
| `agentops_trajectory` | Multi-step agent task planning | Google Agent Guide §3 |

## Quick Start

```bash
# Install
curl -fsSL https://raw.githubusercontent.com/varbees/council-decision-layer/main/install.sh | bash

# Enable in Hermes
hermes skills config          # Enable council-decision-layer
hermes tools enable council   # Enable the council toolset
/reset                        # Start fresh session

# Or test directly
python3 -m pytest ~/.hermes/skills/council-decision-layer/tools/tests/ -v
```

## Architecture

```
~/.hermes/skills/council-decision-layer/
├── SKILL.md                  # Hermes skill manifest
├── patterns/                 # 5 decision framework references
│   ├── tradeoff_matrix.md
│   ├── failure_modes.md
│   ├── end_to_end.md
│   ├── ethics_triage.md
│   └── agentops_trajectory.md
├── tools/
│   ├── question_engine.py    # Core engine (stdlib only, no deps)
│   └── tests/
│       └── test_question_engine.py  # 85 tests
├── references/
│   └── source_mapping.md     # Book → pattern mapping
├── companion-skills/
│   └── privacy-ethics-checklist/  # Module D
├── install.sh                # curl-installable
└── docs/
    └── decision-log-schema.md
```

## Why This Exists

Most AI agent users make architecture and strategy decisions ad-hoc. When things go wrong, there's no record of WHY the decision was made. The Council Decision Layer fixes this: structured questioning → better decisions → logged rationale → outcome verification.

Built for solo founders running multi-agent councils. Powers the [Antharmaya Labs](https://antharmaya.com) agent ecosystem.

## Requirements

- Hermes Agent v0.16.0+
- Python 3.11+
- Zero external dependencies (stdlib only)
- Zero API keys (deterministic engine)

## License

MIT — built with 🧠 by [Antharmaya Labs](https://antharmaya.com).
