# Question Engine — Hermes Tool

import json
import sqlite3
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DECISIONS_DIR = Path(os.path.expanduser("~/.hermes/decisions"))
DB_PATH = DECISIONS_DIR / "decision_log.db"

# ─── Pattern Definitions ───────────────────────────────────────────

PATTERNS = {
    "tradeoff_matrix": {
        "name": "Trade-Off Matrix",
        "source": "DDIA Ch.1",
        "description": "Evaluate architecture choices by making trade-offs explicit",
        "questions": [
            {
                "id": "options",
                "text": "What are the options you're choosing between? List them.",
                "type": "open",
                "hint": "e.g., Cloud Run vs self-hosted VPS, monolith vs microservices"
            },
            {
                "id": "dimensions",
                "text": "What dimensions matter? Pick the top 3-5 that differentiate these options.",
                "type": "open",
                "hint": "e.g., cost, latency, operational burden, scalability ceiling, vendor lock-in"
            },
            {
                "id": "ranking",
                "text": "For each dimension, rank the options. Which wins on cost? Which wins on latency?",
                "type": "open",
                "hint": "Be specific — 'Cloud Run wins on ops burden, VPS wins on cost at scale'"
            },
            {
                "id": "constraints",
                "text": "What constraints are non-negotiable? (budget cap, data locality, latency SLA, team size)",
                "type": "open",
                "hint": "These disqualify options outright"
            },
            {
                "id": "decision",
                "text": "Based on the trade-offs above, what's your decision?",
                "type": "open",
                "hint": "State it as: 'We're going with X because Y, accepting Z as the cost'"
            }
        ]
    },
    "failure_modes": {
        "name": "Failure Mode Enumeration",
        "source": "DDIA Ch.9",
        "description": "Systematically identify what could go wrong before it does",
        "questions": [
            {
                "id": "component",
                "text": "What component or system are we evaluating?",
                "type": "open",
                "hint": "Be specific — 'PhotoSelect payment webhook handler' not 'the backend'"
            },
            {
                "id": "network",
                "text": "What happens if the network is slow, unreliable, or down?",
                "type": "open",
                "hint": "Timeouts, retries, partial failures, split-brain scenarios"
            },
            {
                "id": "clock",
                "text": "What happens if clocks are wrong? (NTP drift, timezone bugs, leap seconds)",
                "type": "open",
                "hint": "Ordering guarantees, TTL expirations, scheduled jobs firing at wrong times"
            },
            {
                "id": "process_pause",
                "text": "What happens if the process pauses? (GC pause, container freeze, OS scheduler)", 
                "type": "open",
                "hint": "Lease expirations, heartbeat timeouts, in-flight operations timing out"
            },
            {
                "id": "blast_radius",
                "text": "What's the blast radius? If this fails, what else breaks?",
                "type": "open",
                "hint": "Cascading failures, dependency chains, single points of failure"
            }
        ]
    },
    "end_to_end": {
        "name": "End-to-End Correctness",
        "source": "DDIA Ch.13",
        "description": "Verify correctness across the full data pipeline, not just individual components",
        "questions": [
            {
                "id": "data_flow",
                "text": "What's the full path of data through the system? List every hop.",
                "type": "open",
                "hint": "User → browser → API → queue → worker → DB → cache → what else?"
            },
            {
                "id": "consistency",
                "text": "Where could data become inconsistent? At which hop could writes be lost or duplicated?",
                "type": "open",
                "hint": "Exactly-once vs at-least-once, idempotency keys, transaction boundaries"
            },
            {
                "id": "constraints",
                "text": "What constraints must hold? (uniqueness, referential integrity, business rules)",
                "type": "open",
                "hint": "At DB layer (foreign keys, unique indexes) AND at app layer (domain invariants)"
            },
            {
                "id": "verification",
                "text": "How will you verify correctness? What's the trust-but-verify mechanism?",
                "type": "open",
                "hint": "Reconciliation jobs, integrity checks, audit logs, canary writes"
            }
        ]
    },
    "ethics_triage": {
        "name": "Privacy & Ethics Impact Triage",
        "source": "DDIA Ch.14 + Google SAIF",
        "description": "Evaluate privacy and ethical implications before building",
        "questions": [
            {
                "id": "necessity",
                "text": "Is this data truly necessary? What happens if you DON'T collect it?",
                "type": "open",
                "hint": "'Data you don't have is data that can't be leaked' — DDIA Ch.14"
            },
            {
                "id": "minimization",
                "text": "What's the minimum viable data? Can you collect less and still deliver the feature?",
                "type": "open",
                "hint": "Hash instead of store, aggregate instead of individual, sample instead of full"
            },
            {
                "id": "retention",
                "text": "How long do you keep it? What's the auto-delete policy?",
                "type": "open",
                "hint": "Default: 30 days. Longer requires explicit justification."
            },
            {
                "id": "leak_scenario",
                "text": "What happens if this data leaks? Walk through the worst-case scenario.",
                "type": "open",
                "hint": "Who gets harmed? What's the regulatory exposure? What's the reputational damage?"
            },
            {
                "id": "feedback_loop",
                "text": "Could this create a feedback loop that harms users? (recommendation bias, filter bubbles, unfair ranking)",
                "type": "open",
                "hint": "DDIA Ch.14: algorithms that amplify existing biases or create self-reinforcing loops"
            }
        ]
    },
    "agentops_trajectory": {
        "name": "AgentOps Trajectory Check",
        "source": "Google Agent Guide §3",
        "description": "Evaluate agent reasoning path before deploying a multi-step task",
        "questions": [
            {
                "id": "goal",
                "text": "What's the specific goal the agent is trying to achieve?",
                "type": "open",
                "hint": "Be precise — 'Deploy PhotoSelect staging with green health check' not 'deploy stuff'"
            },
            {
                "id": "steps",
                "text": "What are the Reason → Act → Observe steps you expect the agent to take?",
                "type": "open",
                "hint": "L1: Reason about goal → L2: Act (tool call) → L3: Observe result → L4: Reason about next step"
            },
            {
                "id": "failure_points",
                "text": "At which step is the agent most likely to fail? E.g., tool returns wrong format, ambiguous observation, etc.",
                "type": "open",
                "hint": "Tool Selection errors, Parameter Generation errors, Observation misinterpretation"
            },
            {
                "id": "guardrails",
                "text": "What guardrails should be in place? (max steps, timeout, human approval gates)",
                "type": "open",
                "hint": "AgentOps: input validation, output filtering, step limits, approval for destructive actions"
            },
            {
                "id": "evaluation",
                "text": "How will you know the agent did the right thing? What does success look like?",
                "type": "open",
                "hint": "Layer 3 eval: semantic correctness, factual grounding, completeness of response"
            }
        ]
    }
}


# ─── Database ──────────────────────────────────────────────────────

def _get_db() -> sqlite3.Connection:
    """Get or create the decision log database."""
    DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
    DECISIONS_DIR.chmod(0o700)
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    _ensure_schema(db)
    DB_PATH.chmod(0o600)
    return db


def _ensure_schema(db: sqlite3.Connection):
    """Create tables if they don't exist."""
    db.executescript("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            pattern TEXT NOT NULL,
            pattern_source TEXT,
            session_id TEXT,
            agent_model TEXT,
            -- Store all Q&A pairs as JSON
            questions_answers TEXT NOT NULL,  -- JSON: [{"q_id": "...", "question": "...", "answer": "..."}]
            summary TEXT,                     -- final decision/conclusion
            -- Outcome tracking
            outcome_verified INTEGER DEFAULT 0,
            outcome_notes TEXT,
            outcome_checked_at TEXT,
            -- Metadata
            git_sha TEXT,
            project TEXT,
            tags TEXT                         -- JSON array of strings
        );

        CREATE TABLE IF NOT EXISTS decision_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id INTEGER NOT NULL REFERENCES decisions(id),
            reviewed_at TEXT NOT NULL DEFAULT (datetime('now')),
            outcome TEXT NOT NULL,            -- 'good', 'bad', 'mixed', 'unknown'
            notes TEXT,
            changed_mind INTEGER DEFAULT 0   -- 1 = would decide differently now
        );

        CREATE INDEX IF NOT EXISTS idx_decisions_pattern ON decisions(pattern);
        CREATE INDEX IF NOT EXISTS idx_decisions_outcome ON decisions(outcome_verified);
        CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp);
    """)


# ─── Core Logic ────────────────────────────────────────────────────

def get_pattern(pattern_name: str) -> dict | None:
    """Return a pattern definition by name."""
    return PATTERNS.get(pattern_name)


def list_patterns() -> list[dict]:
    """Return all available patterns with metadata."""
    return [
        {
            "name": key,
            "display_name": p["name"],
            "source": p["source"],
            "description": p["description"],
            "question_count": len(p["questions"])
        }
        for key, p in PATTERNS.items()
    ]


def ask_questions(pattern_name: str) -> dict:
    """Get the structured questions for a pattern."""
    pattern = get_pattern(pattern_name)
    if not pattern:
        return {"error": f"Unknown pattern '{pattern_name}'. Available: {list(PATTERNS.keys())}"}
    
    return {
        "pattern": pattern_name,
        "display_name": pattern["name"],
        "source": pattern["source"],
        "description": pattern["description"],
        "questions": pattern["questions"],
        "instruction": (
            "Answer each question. Reply 'skip' to skip a question. "
            "Reply 'done' after answering all questions to log the decision."
        )
    }


def log_decision(
    pattern_name: str,
    questions_answers: list[dict],
    summary: str = "",
    session_id: str = "",
    agent_model: str = "",
    git_sha: str = "",
    project: str = "",
    tags: list[str] | None = None,
) -> dict:
    """Log a decision with its Q&A to the database."""
    pattern = get_pattern(pattern_name)
    db = _get_db()
    
    cursor = db.execute(
        """INSERT INTO decisions 
           (pattern, pattern_source, session_id, agent_model, questions_answers, summary, git_sha, project, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            pattern_name,
            pattern["source"] if pattern else "unknown",
            session_id,
            agent_model,
            json.dumps(questions_answers),
            summary,
            git_sha,
            project,
            json.dumps(tags or [])
        )
    )
    db.commit()
    decision_id = cursor.lastrowid
    
    return {
        "decision_id": decision_id,
        "pattern": pattern_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stored_at": str(DB_PATH)
    }


def review_decision(decision_id: int, outcome: str, notes: str = "", changed_mind: bool = False) -> dict:
    """Record a review of a past decision."""
    db = _get_db()
    
    # Verify decision exists
    decision = db.execute("SELECT id, outcome_verified FROM decisions WHERE id = ?", (decision_id,)).fetchone()
    if not decision:
        return {"error": f"Decision {decision_id} not found"}
    
    db.execute(
        """INSERT INTO decision_reviews (decision_id, outcome, notes, changed_mind)
           VALUES (?, ?, ?, ?)""",
        (decision_id, outcome, notes, 1 if changed_mind else 0)
    )
    
    # Update outcome_verified on the decision
    # 0=unverified, 1=good, 2=mixed, -1=bad  (DISTINCT from 0=unverified)
    outcome_map = {"good": 1, "bad": -1, "mixed": 2, "unknown": 0}
    outcome_code = outcome_map.get(outcome, 0)
    db.execute(
        "UPDATE decisions SET outcome_verified = ?, outcome_notes = ?, outcome_checked_at = datetime('now') WHERE id = ?",
        (outcome_code, notes, decision_id)
    )
    db.commit()
    
    return {"decision_id": decision_id, "outcome": outcome, "reviewed": True}


def get_pending_reviews(days_old: int = 14) -> list[dict]:
    """Get decisions that haven't been outcome-verified and are older than N days."""
    db = _get_db()
    rows = db.execute(
        """SELECT id, pattern, timestamp, summary 
           FROM decisions 
           WHERE outcome_verified = 0 
             AND timestamp < datetime('now', ?) 
           ORDER BY timestamp ASC""",
        (f'-{days_old} days',)
    ).fetchall()
    return [dict(r) for r in rows]


def get_decisions_by_pattern(pattern_name: str, limit: int = 20) -> list[dict]:
    """Get recent decisions using a specific pattern."""
    db = _get_db()
    rows = db.execute(
        "SELECT id, timestamp, summary, outcome_verified FROM decisions WHERE pattern = ? ORDER BY timestamp DESC LIMIT ?",
        (pattern_name, limit)
    ).fetchall()
    return [dict(r) for r in rows]


def _escape_like(value: str) -> str:
    """Escape LIKE special characters to prevent wildcard injection."""
    value = value.replace("\\", "\\\\")
    value = value.replace("%", "\\%")
    value = value.replace("_", "\\_")
    return value


def search_decisions(query: str, limit: int = 10) -> list[dict]:
    """Full-text search over decision summaries and Q&A."""
    if not query or not query.strip():
        return []
    db = _get_db()
    escaped = _escape_like(query.strip())
    rows = db.execute(
        """SELECT id, timestamp, pattern, summary 
           FROM decisions 
           WHERE summary LIKE ? ESCAPE '\\' OR questions_answers LIKE ? ESCAPE '\\'
           ORDER BY timestamp DESC LIMIT ?""",
        (f'%{escaped}%', f'%{escaped}%', limit)
    ).fetchall()
    return [dict(r) for r in rows]


# ─── Hermes Tool Registration ──────────────────────────────────────

def check_requirements() -> bool:
    """Validate that the environment meets minimum requirements."""
    if sys.version_info < (3, 11):
        return False
    try:
        _get_db()
        return True
    except Exception:
        return False


def question_engine_tool(action: str, **kwargs) -> str:
    """Hermes tool: question engine for structured decision-making.
    
    Actions:
      - list_patterns: Return all available decision patterns
      - ask: Get questions for a pattern (requires pattern_name)
      - log: Record a decision (requires pattern_name, questions_answers)
      - review: Review a past decision (requires decision_id, outcome)
      - pending: List decisions awaiting outcome review
      - search: Search past decisions (requires query)
    
    Args:
        action: The action to perform
        **kwargs: Action-specific parameters
    """
    try:
        if action == "list_patterns":
            patterns = list_patterns()
            return json.dumps({"patterns": patterns})
        
        elif action == "ask":
            pattern_name = kwargs.get("pattern_name", "")
            if not pattern_name:
                # Return pattern list with hint
                return json.dumps({
                    "error": "pattern_name required",
                    "available_patterns": [p["name"] for p in list_patterns()]
                })
            result = ask_questions(pattern_name)
            return json.dumps(result)
        
        elif action == "log":
            pattern_name = kwargs.get("pattern_name", "")
            questions_answers = kwargs.get("questions_answers", [])
            summary = kwargs.get("summary", "")
            session_id = kwargs.get("session_id", "")
            agent_model = kwargs.get("agent_model", "")
            
            if isinstance(questions_answers, str):
                questions_answers = json.loads(questions_answers)
            
            result = log_decision(
                pattern_name=pattern_name,
                questions_answers=questions_answers,
                summary=summary,
                session_id=session_id,
                agent_model=agent_model,
                project=kwargs.get("project", ""),
                tags=kwargs.get("tags", [])
            )
            return json.dumps(result)
        
        elif action == "review":
            decision_id = kwargs.get("decision_id", 0)
            outcome = kwargs.get("outcome", "")
            notes = kwargs.get("notes", "")
            changed_mind = kwargs.get("changed_mind", False)
            result = review_decision(int(decision_id), outcome, notes, bool(changed_mind))
            return json.dumps(result)
        
        elif action == "pending":
            days = int(kwargs.get("days_old", 14))
            pending = get_pending_reviews(days)
            return json.dumps({"pending_count": len(pending), "decisions": pending})
        
        elif action == "search":
            query = kwargs.get("query", "")
            limit = int(kwargs.get("limit", 10))
            results = search_decisions(query, limit)
            return json.dumps({"query": query, "count": len(results), "results": results})
        
        else:
            return json.dumps({
                "error": f"Unknown action '{action}'",
                "valid_actions": ["list_patterns", "ask", "log", "review", "pending", "search"]
            })
    
    except Exception as e:
        return json.dumps({"error": str(e)})


# Register with Hermes tool system
try:
    from tools.registry import registry
    registry.register(
        name="question_engine",
        toolset="council",
        schema={
            "name": "question_engine",
            "description": "Structured decision-making engine. Use when making architecture, strategy, or prioritization decisions. Actions: list_patterns, ask, log, review, pending, search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action: list_patterns, ask (needs pattern_name), log (needs pattern_name+questions_answers), review (needs decision_id+outcome), pending, search (needs query)",
                        "enum": ["list_patterns", "ask", "log", "review", "pending", "search"]
                    },
                    "pattern_name": {
                        "type": "string",
                        "description": "Pattern name for ask/log actions. Available: tradeoff_matrix, failure_modes, end_to_end, ethics_triage, agentops_trajectory"
                    },
                    "questions_answers": {
                        "type": "string",
                        "description": "JSON array of Q&A objects for log action: [{'q_id': '...', 'question': '...', 'answer': '...'}]"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Summary of the final decision (for log action)"
                    },
                    "decision_id": {
                        "type": "integer",
                        "description": "Decision ID for review action"
                    },
                    "outcome": {
                        "type": "string",
                        "description": "One of: good, bad, mixed, unknown (for review action)",
                        "enum": ["good", "bad", "mixed", "unknown"]
                    },
                    "notes": {
                        "type": "string",
                        "description": "Free-text notes for review"
                    },
                    "changed_mind": {
                        "type": "boolean",
                        "description": "Would you decide differently now? (for review action)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search term (for search action)"
                    },
                    "project": {
                        "type": "string",
                        "description": "Project name for context (e.g., 'photoselect', 'memory-bridge')"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorization"
                    },
                    "days_old": {
                        "type": "integer",
                        "description": "Days threshold for pending reviews (default: 14)"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Hermes session ID for traceability"
                    },
                    "agent_model": {
                        "type": "string",
                        "description": "Model that made the decision"
                    }
                },
                "required": ["action"]
            }
        },
        handler=lambda args, **kw: question_engine_tool(
            action=args.get("action", ""),
            pattern_name=args.get("pattern_name", ""),
            questions_answers=args.get("questions_answers", []),
            summary=args.get("summary", ""),
            decision_id=args.get("decision_id", 0),
            outcome=args.get("outcome", ""),
            notes=args.get("notes", ""),
            changed_mind=args.get("changed_mind", False),
            query=args.get("query", ""),
            limit=args.get("limit", 10),
            project=args.get("project", ""),
            tags=args.get("tags", []),
            days_old=args.get("days_old", 14),
            session_id=kw.get("task_id", args.get("session_id", "")),
            agent_model=args.get("agent_model", "")
        ),
        check_fn=check_requirements,
    )
except ImportError:
    # Not running inside Hermes — tool registration skipped
    # (useful for testing outside the agent loop)
    pass
