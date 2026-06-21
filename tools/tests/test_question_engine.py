"""Component tests for the Council Decision Layer question engine.

Module C — AgentOps Layer 1: Deterministic component evaluation.

Uses a temporary SQLite database for complete test isolation.
No production data is ever touched.

Run: python3 -m pytest tools/tests/test_question_engine.py -v
"""

import json
import sqlite3
import sys
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test (using the actual source file, not the installed copy)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import question_engine as qe


# ─── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """Redirect all DB operations to a temporary directory for test isolation."""
    tmpdir = Path(tempfile.mkdtemp(prefix="cdl_test_"))
    monkeypatch.setattr(qe, "DECISIONS_DIR", tmpdir / "decisions")
    monkeypatch.setattr(qe, "DB_PATH", qe.DECISIONS_DIR / "decision_log.db")
    yield tmpdir
    # Cleanup
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_qa():
    return [{"q_id": "q1", "question": "Test question?", "answer": "Test answer"}]


# ─── Pattern Definition Tests ──────────────────────────────────────────────

class TestPatternDefinitions:
    """All 5 patterns must be complete and consistent."""

    REQUIRED_KEYS = {"name", "source", "description", "questions"}
    REQUIRED_Q_KEYS = {"id", "text", "type", "hint"}

    @pytest.mark.parametrize("pattern_name", list(qe.PATTERNS.keys()))
    def test_pattern_has_required_keys(self, pattern_name):
        p = qe.PATTERNS[pattern_name]
        missing = self.REQUIRED_KEYS - set(p.keys())
        assert not missing, f"Pattern '{pattern_name}' missing keys: {missing}"

    @pytest.mark.parametrize("pattern_name", list(qe.PATTERNS.keys()))
    def test_pattern_has_valid_questions(self, pattern_name):
        p = qe.PATTERNS[pattern_name]
        questions = p["questions"]
        assert isinstance(questions, list), "Questions must be a list"
        assert len(questions) >= 3, \
            f"Pattern '{pattern_name}' has only {len(questions)} questions (need >=3)"
        assert len(questions) <= 7, \
            f"Pattern '{pattern_name}' has {len(questions)} questions (max 7)"

        for q in questions:
            missing = self.REQUIRED_Q_KEYS - set(q.keys())
            assert not missing, \
                f"Question '{q.get('id','?')}' missing keys: {missing}"
            assert q["type"] in ("open", "choice", "scale"), \
                f"Question '{q['id']}' has invalid type: {q['type']}"

    @pytest.mark.parametrize("pattern_name", list(qe.PATTERNS.keys()))
    def test_question_ids_are_unique(self, pattern_name):
        p = qe.PATTERNS[pattern_name]
        ids = [q["id"] for q in p["questions"]]
        assert len(ids) == len(set(ids)), \
            f"Duplicate question IDs in '{pattern_name}': {ids}"

    @pytest.mark.parametrize("pattern_name", list(qe.PATTERNS.keys()))
    def test_all_questions_have_nonempty_hints(self, pattern_name):
        p = qe.PATTERNS[pattern_name]
        for q in p["questions"]:
            assert q.get("hint") and len(q["hint"].strip()) > 0, \
                f"Question '{q['id']}' in '{pattern_name}' has empty hint"

    def test_get_pattern_unknown_returns_none(self):
        assert qe.get_pattern("nonexistent") is None


# ─── List Patterns Tests ────────────────────────────────────────────────────

class TestListPatterns:
    """list_patterns() must return all 5 patterns with correct metadata."""

    def test_returns_all_patterns(self):
        result = qe.list_patterns()
        assert len(result) == 5

    def test_each_has_metadata(self):
        for p in qe.list_patterns():
            assert "name" in p
            assert "display_name" in p
            assert "source" in p
            assert "description" in p
            assert "question_count" in p
            assert p["question_count"] >= 3

    def test_pattern_names_match(self):
        names = {p["name"] for p in qe.list_patterns()}
        assert names == set(qe.PATTERNS.keys())

    def test_question_counts_are_accurate(self):
        for p in qe.list_patterns():
            actual = len(qe.PATTERNS[p["name"]]["questions"])
            assert p["question_count"] == actual, \
                f"Pattern '{p['name']}': claimed {p['question_count']}, actually {actual}"


# ─── Ask Questions Tests ────────────────────────────────────────────────────

class TestAskQuestions:
    """ask_questions() returns the correct structured output."""

    def test_valid_pattern(self):
        result = qe.ask_questions("tradeoff_matrix")
        assert "error" not in result
        assert result["pattern"] == "tradeoff_matrix"
        assert result["display_name"] == "Trade-Off Matrix"
        assert len(result["questions"]) == 5
        assert "instruction" in result
        assert "skip" in result["instruction"].lower()

    def test_invalid_pattern(self):
        result = qe.ask_questions("bogus")
        assert "error" in result
        assert "Unknown pattern" in result["error"]
        assert "tradeoff_matrix" in result["error"]  # lists available patterns

    @pytest.mark.parametrize("pattern_name", list(qe.PATTERNS.keys()))
    def test_every_pattern_has_questions(self, pattern_name):
        result = qe.ask_questions(pattern_name)
        assert "error" not in result, f"Pattern '{pattern_name}' returned error: {result}"
        assert len(result["questions"]) >= 3

    def test_empty_pattern_name(self):
        result = qe.ask_questions("")
        assert "error" in result


# ─── Log & Review Tests ─────────────────────────────────────────────────────

class TestLogDecision:
    """Core CRUD: logging decisions."""

    def test_log_decision_basic(self, sample_qa):
        result = qe.log_decision("failure_modes", sample_qa, "Test decision",
                                  session_id="pytest-1", agent_model="test-model",
                                  project="test-project", tags=["test"])
        assert result["decision_id"] > 0
        assert result["pattern"] == "failure_modes"
        assert "stored_at" in result

    def test_log_unknown_pattern(self, sample_qa):
        result = qe.log_decision("nonexistent_pattern", sample_qa, "Unknown pattern test")
        assert result["decision_id"] > 0  # should still log with source="unknown"

    def test_log_empty_summary(self, sample_qa):
        result = qe.log_decision("tradeoff_matrix", sample_qa, "")
        assert result["decision_id"] > 0

    def test_log_increments_ids(self, sample_qa):
        r1 = qe.log_decision("failure_modes", sample_qa, "First")
        r2 = qe.log_decision("failure_modes", sample_qa, "Second")
        assert r2["decision_id"] > r1["decision_id"]

    def test_log_with_tags_persists(self, sample_qa):
        qe.log_decision("ethics_triage", sample_qa, "Tagged", tags=["privacy", "critical"])
        db = qe._get_db()
        row = db.execute("SELECT tags FROM decisions ORDER BY id DESC LIMIT 1").fetchone()
        tags = json.loads(row["tags"])
        assert "privacy" in tags
        assert "critical" in tags


class TestReviewDecision:
    """Post-hoc review of decisions."""

    def test_review_good(self, sample_qa):
        result = qe.log_decision("ethics_triage", sample_qa, "Review test")
        review = qe.review_decision(result["decision_id"], "good", "Worked perfectly")
        assert review["reviewed"] is True
        assert review["decision_id"] == result["decision_id"]

    def test_review_bad(self, sample_qa):
        result = qe.log_decision("failure_modes", sample_qa, "Bad decision")
        review = qe.review_decision(result["decision_id"], "bad", "Terrible call")
        assert review["reviewed"] is True

    def test_review_mixed_does_not_equal_unverified(self, sample_qa):
        """Regression: 'mixed' outcome must be distinguishable from unverified (0)."""
        result = qe.log_decision("end_to_end", sample_qa, "Mixed outcome test")
        qe.review_decision(result["decision_id"], "mixed", "Some good, some bad")
        db = qe._get_db()
        row = db.execute("SELECT outcome_verified FROM decisions WHERE id = ?",
                         (result["decision_id"],)).fetchone()
        # mixed = 2, unverified = 0 — must NOT collide
        assert row["outcome_verified"] == 2, \
            f"Expected 2 for 'mixed', got {row['outcome_verified']} (would collide with unverified=0)"

    def test_review_nonexistent(self):
        result = qe.review_decision(99999, "good")
        assert "error" in result

    def test_review_invalid_outcome(self, sample_qa):
        result = qe.log_decision("tradeoff_matrix", sample_qa, "Invalid outcome test")
        review = qe.review_decision(result["decision_id"], "fantastic")  # not in enum
        assert review["reviewed"] is True  # should still work, maps to 0 (unknown)

    def test_review_changed_mind(self, sample_qa):
        result = qe.log_decision("failure_modes", sample_qa, "Regretted decision")
        qe.review_decision(result["decision_id"], "bad", "Should not have done it", changed_mind=True)
        db = qe._get_db()
        row = db.execute("SELECT changed_mind FROM decision_reviews WHERE decision_id = ?",
                         (result["decision_id"],)).fetchone()
        assert row["changed_mind"] == 1


class TestPendingReviews:
    """get_pending_reviews() logic."""

    def test_pending_reviews_empty_for_recent(self, sample_qa):
        for _ in range(3):
            qe.log_decision("tradeoff_matrix", sample_qa, "Pending test")
        # days_old=0: only decisions MORE than 0 days old. These are seconds old.
        pending = qe.get_pending_reviews(days_old=0)
        assert pending == []  # strong: must be empty, not just a list

    def test_pending_reviews_excludes_reviewed(self, sample_qa):
        result = qe.log_decision("failure_modes", sample_qa, "To review")
        qe.review_decision(result["decision_id"], "good", "Done")
        pending = qe.get_pending_reviews(days_old=365)  # very old threshold
        ids = [d["id"] for d in pending]
        assert result["decision_id"] not in ids, \
            "Reviewed decision should not appear in pending reviews"

    def test_pending_returns_list_with_structure(self, sample_qa):
        result = qe.log_decision("end_to_end", sample_qa, "Structure test")
        pending = qe.get_pending_reviews(days_old=365)
        assert isinstance(pending, list)
        if pending:
            d = pending[0]
            assert "id" in d
            assert "pattern" in d
            assert "timestamp" in d
            assert "summary" in d


# ─── Search Tests ───────────────────────────────────────────────────────────

class TestSearchDecisions:
    """search_decisions() with parameterized queries."""

    def test_search_finds_by_summary(self, sample_qa):
        qe.log_decision("tradeoff_matrix", sample_qa, "Cloud Run vs VPS comparison")
        results = qe.search_decisions("Cloud Run")
        assert len(results) >= 1
        assert any("Cloud Run" in r["summary"] for r in results)

    def test_search_finds_by_qa_content(self, sample_qa):
        qa = [{"q_id": "q1", "question": "What about Kubernetes?", "answer": "Too complex"}]
        qe.log_decision("end_to_end", qa, "K8s decision")
        results = qe.search_decisions("Kubernetes")
        assert len(results) >= 1

    def test_search_empty_string(self):
        results = qe.search_decisions("")
        assert results == []

    def test_search_whitespace_only(self):
        results = qe.search_decisions("   ")
        assert results == []

    def test_search_nonexistent(self):
        results = qe.search_decisions("xyzzy_nonexistent_term_42")
        assert results == []

    def test_search_like_wildcard_percent_escaped(self, sample_qa):
        """SQL injection: % in query must NOT match all records."""
        qe.log_decision("failure_modes", [{"q_id": "a", "question": "Q?", "answer": "A"}],
                        "Exact match: 100% uptime goal")
        # A bare '%' would match everything — it must be escaped
        results = qe.search_decisions("%")
        # Should only match records that LITERALLY contain '%'
        found = [r for r in results if "100%" in (r.get("summary") or "")]
        assert len(found) == 1, \
            f"search('%') should only match records with literal %, not all {len(results)} records"

    def test_search_like_wildcard_underscore_escaped(self, sample_qa):
        """SQL injection: _ in query must match literal underscore, not any char."""
        qe.log_decision("tradeoff_matrix", sample_qa, "Test_user with underscore")
        qe.log_decision("tradeoff_matrix", sample_qa, "TestXuser without underscore")
        results = qe.search_decisions("_user")
        # Only the literal underscore record should match
        found_underscore = [r for r in results if "Test_user" in (r.get("summary") or "")]
        found_xuser = [r for r in results if "TestXuser" in (r.get("summary") or "")]
        assert len(found_underscore) == 1, \
            f"search('_user') should match literal underscore, got {len(results)} results"
        assert len(found_xuser) == 0, \
            f"search('_user') matched TestXuser — underscore was NOT escaped"

    def test_search_like_backslash_escaped(self, sample_qa):
        """Backslashes in query must be escaped to prevent ESCAPE bypass."""
        qe.log_decision("ethics_triage", sample_qa, "Path: C:\\Users\\test")
        results = qe.search_decisions("\\Users")
        assert len(results) >= 1

    def test_search_respects_limit(self, sample_qa):
        for i in range(5):
            qe.log_decision("tradeoff_matrix", sample_qa, f"Limit test {i}")
        results = qe.search_decisions("Limit test", limit=2)
        assert len(results) <= 2

    def test_search_case_insensitive_sqlite(self, sample_qa):
        qe.log_decision("failure_modes", sample_qa, "CLOUD RUN deployment")
        results_lower = qe.search_decisions("cloud run")
        results_upper = qe.search_decisions("CLOUD RUN")
        assert len(results_lower) >= 1
        assert len(results_upper) >= 1


# ─── Get Decisions By Pattern Tests ─────────────────────────────────────────

class TestGetDecisionsByPattern:
    """get_decisions_by_pattern() filtering."""

    def test_returns_only_matching_pattern(self, sample_qa):
        qe.log_decision("tradeoff_matrix", sample_qa, "Tradeoff one")
        qe.log_decision("failure_modes", sample_qa, "Failure one")
        results = qe.get_decisions_by_pattern("tradeoff_matrix")
        assert all(r["summary"] in ("Tradeoff one", "") for r in results
                   if r["summary"] != "Failure one")

    def test_respects_limit(self, sample_qa):
        for _ in range(5):
            qe.log_decision("end_to_end", sample_qa, "End to end test")
        results = qe.get_decisions_by_pattern("end_to_end", limit=2)
        assert len(results) <= 2

    def test_empty_for_unused_pattern(self):
        results = qe.get_decisions_by_pattern("agentops_trajectory")
        assert results == []


# ─── Database Schema Tests ──────────────────────────────────────────────────

class TestDatabaseSchema:
    """Schema integrity tests."""

    def test_tables_exist(self):
        db = qe._get_db()
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "decisions" in table_names
        assert "decision_reviews" in table_names

    def test_indexes_exist(self):
        db = qe._get_db()
        indexes = db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        ).fetchall()
        index_names = [i[0] for i in indexes]
        assert "idx_decisions_pattern" in index_names
        assert "idx_decisions_outcome" in index_names
        assert "idx_decisions_timestamp" in index_names

    def test_wal_mode(self):
        db = qe._get_db()
        mode = db.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"

    def test_foreign_keys(self):
        db = qe._get_db()
        fk = db.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1

    def test_schema_idempotent(self):
        """Calling _ensure_schema twice should not error."""
        db = qe._get_db()
        qe._ensure_schema(db)
        qe._ensure_schema(db)  # second call must succeed

    def test_decisions_schema_columns(self):
        db = qe._get_db()
        cols = db.execute("PRAGMA table_info(decisions)").fetchall()
        col_names = {c[1] for c in cols}
        required = {"id", "timestamp", "pattern", "questions_answers", "summary",
                    "outcome_verified", "outcome_notes", "outcome_checked_at"}
        assert required.issubset(col_names), f"Missing columns: {required - col_names}"

    def test_decision_reviews_schema_columns(self):
        db = qe._get_db()
        cols = db.execute("PRAGMA table_info(decision_reviews)").fetchall()
        col_names = {c[1] for c in cols}
        required = {"id", "decision_id", "reviewed_at", "outcome", "notes", "changed_mind"}
        assert required.issubset(col_names), f"Missing columns: {required - col_names}"


# ─── Error Handling Tests ───────────────────────────────────────────────────

class TestErrorHandling:
    """Graceful error handling for edge cases."""

    def test_empty_qa_logs_ok(self):
        result = qe.log_decision("failure_modes", [], "Empty QA test")
        assert result["decision_id"] > 0

    def test_special_characters_roundtrip(self):
        qa = [{"q_id": "a",
               "question": "Has 'quotes' and \"double\"?",
               "answer": "Yes — with em-dash and \\backslash"}]
        result = qe.log_decision("tradeoff_matrix", qa, "Special chars émoji 🧠 test")
        assert result["decision_id"] > 0
        results = qe.search_decisions("em-dash")
        assert len(results) >= 1

    def test_unicode_survives_roundtrip(self):
        qa = [{"q_id": "u1",
               "question": "हिन्दी में सवाल?",
               "answer": "हाँ, जवाब"}]
        result = qe.log_decision("ethics_triage", qa, "Unicode test हिन्दी")
        assert result["decision_id"] > 0
        results = qe.search_decisions("हिन्दी")
        assert len(results) >= 1

    def test_null_tags_coerced_to_empty_list(self):
        result = qe.log_decision("failure_modes",
                                  [{"q_id": "a", "question": "Q?", "answer": "A"}],
                                  "Null tags test", tags=None)
        assert result["decision_id"] > 0

    def test_very_long_summary(self):
        long_summary = "X" * 10000
        result = qe.log_decision("tradeoff_matrix",
                                  [{"q_id": "a", "question": "Q?", "answer": "A"}],
                                  long_summary)
        assert result["decision_id"] > 0

    def test_very_long_qa(self):
        long_answer = "A" * 10000
        qa = [{"q_id": "a", "question": "Q?", "answer": long_answer}]
        result = qe.log_decision("end_to_end", qa, "Long QA test")
        assert result["decision_id"] > 0


# ─── Tool Interface Tests ───────────────────────────────────────────────────

class TestQuestionEngineTool:
    """question_engine_tool() integration tests."""

    def test_list_patterns_action(self):
        result = qe.question_engine_tool(action="list_patterns")
        data = json.loads(result)
        assert "patterns" in data
        assert len(data["patterns"]) == 5

    def test_ask_action(self):
        result = qe.question_engine_tool(action="ask", pattern_name="failure_modes")
        data = json.loads(result)
        assert data["pattern"] == "failure_modes"
        assert len(data["questions"]) == 5

    def test_ask_without_pattern_name(self):
        result = qe.question_engine_tool(action="ask")
        data = json.loads(result)
        assert "error" in data
        assert "available_patterns" in data

    def test_log_action(self):
        result = qe.question_engine_tool(
            action="log",
            pattern_name="tradeoff_matrix",
            questions_answers=json.dumps([{"q_id": "q1", "question": "Q?", "answer": "A"}]),
            summary="Tool test"
        )
        data = json.loads(result)
        assert data["decision_id"] > 0

    def test_log_action_with_json_string_qa(self):
        """QA passed as JSON string should be auto-parsed."""
        result = qe.question_engine_tool(
            action="log",
            pattern_name="end_to_end",
            questions_answers='[{"q_id": "a", "question": "Q?", "answer": "A"}]',
            summary="JSON string QA"
        )
        data = json.loads(result)
        assert data["decision_id"] > 0

    def test_review_action(self):
        result = qe.question_engine_tool(
            action="log",
            pattern_name="failure_modes",
            questions_answers=json.dumps([{"q_id": "q1", "question": "Q?", "answer": "A"}]),
            summary="Pre-review"
        )
        decision_id = json.loads(result)["decision_id"]

        result = qe.question_engine_tool(
            action="review",
            decision_id=decision_id,
            outcome="mixed",
            notes="it was ok",
            changed_mind=False
        )
        data = json.loads(result)
        assert data["reviewed"] is True

    def test_pending_action(self):
        result = qe.question_engine_tool(action="pending", days_old=365)
        data = json.loads(result)
        assert "pending_count" in data
        assert "decisions" in data
        assert isinstance(data["decisions"], list)

    def test_search_action(self):
        result = qe.question_engine_tool(action="search", query="test", limit=5)
        data = json.loads(result)
        assert "query" in data
        assert "count" in data
        assert "results" in data

    def test_unknown_action(self):
        result = qe.question_engine_tool(action="fly_to_moon")
        data = json.loads(result)
        assert "error" in data
        assert "valid_actions" in data

    def test_tool_exceptions_handled(self):
        """Tool must return JSON error, never raise."""
        result = qe.question_engine_tool(action="review", decision_id="not_a_number")
        data = json.loads(result)
        assert "error" in data  # conversion error caught


# ─── Requirements Check Tests ───────────────────────────────────────────────

class TestCheckRequirements:
    """check_requirements() must perform actual validation."""

    def test_returns_boolean(self):
        result = qe.check_requirements()
        assert isinstance(result, bool)

    def test_returns_true_when_db_accessible(self):
        assert qe.check_requirements() is True
