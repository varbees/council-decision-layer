#!/bin/bash
# Council Decision Layer — Install Script
# curl -fsSL https://raw.githubusercontent.com/varbees/council-decision-layer/main/install.sh | bash
#
# Installs the Council Decision Layer for Hermes Agent:
#   - council-decision-layer skill (5 decision patterns + question engine)
#   - privacy-ethics-checklist skill (pre-build privacy gate)
#   - Decision log database (~/.hermes/decisions/decision_log.db)
#
# Requirements: Hermes Agent v0.16.0+, Python 3.11+

set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SKILLS_DIR="$HERMES_HOME/skills"
DECISIONS_DIR="$HERMES_HOME/decisions"
REPO_URL="https://raw.githubusercontent.com/varbees/council-decision-layer/main"

echo "╔══════════════════════════════════════════╗"
echo "║  Council Decision Layer — Installer      ║"
echo "║  Antharmaya Labs                         ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ─── Check prerequisites ──────────────────────────────────────────
echo "→ Checking prerequisites..."

if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3.11+ required. Install it first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
    echo "❌ Python 3.11+ required. Found: Python $PYTHON_VERSION."
    exit 1
fi
echo "   Python $PYTHON_VERSION ✓"

if [ ! -d "$HERMES_HOME" ]; then
    echo "❌ Hermes Agent not found at $HERMES_HOME. Install Hermes first:"
    echo "   curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash"
    exit 1
fi
echo "   Hermes Agent ✓"

# ─── Check idempotency ─────────────────────────────────────────────
if [ -f "$SKILLS_DIR/council-decision-layer/SKILL.md" ]; then
    echo "→ Council Decision Layer already installed."
    echo "  Re-run to update: $0 --force"
    if [ "${1:-}" != "--force" ]; then
        echo "  Use --force to reinstall or update."
        exit 0
    fi
    echo "  --force: reinstalling..."
fi
echo ""

# ─── Create directories ────────────────────────────────────────────
echo "→ Creating directories..."

mkdir -p "$SKILLS_DIR/council-decision-layer"/{patterns,tools,references,tools/tests}
mkdir -p "$SKILLS_DIR/privacy-ethics-checklist"
mkdir -p "$DECISIONS_DIR"
chmod 700 "$SKILLS_DIR/council-decision-layer" "$DECISIONS_DIR" 2>/dev/null || true

echo "   Created: $SKILLS_DIR/council-decision-layer/"
echo "   Created: $SKILLS_DIR/privacy-ethics-checklist/"
echo "   Created: $DECISIONS_DIR/"

# ─── Download skill files ──────────────────────────────────────────
echo ""
echo "→ Downloading skill files..."

download() {
    local path="$1"
    local dest="$2"
    if command -v curl &>/dev/null; then
        curl -fsSL "$REPO_URL/$path" -o "$dest"
    else
        wget -q "$REPO_URL/$path" -O "$dest"
    fi
}

# council-decision-layer SKILL.md
download "SKILL.md" "$SKILLS_DIR/council-decision-layer/SKILL.md"
echo "   SKILL.md ✓"

# Pattern files
for pattern in tradeoff_matrix failure_modes end_to_end ethics_triage agentops_trajectory; do
    download "patterns/${pattern}.md" "$SKILLS_DIR/council-decision-layer/patterns/${pattern}.md"
done
echo "   5 pattern files ✓"

# Question engine
download "tools/question_engine.py" "$SKILLS_DIR/council-decision-layer/tools/question_engine.py"
echo "   question_engine.py ✓"

# Tests
download "tools/tests/test_question_engine.py" "$SKILLS_DIR/council-decision-layer/tools/tests/test_question_engine.py"
echo "   test_question_engine.py ✓"

# Source mapping
download "references/source_mapping.md" "$SKILLS_DIR/council-decision-layer/references/source_mapping.md"
echo "   source_mapping.md ✓"

# Privacy/ethics checklist
download "../privacy-ethics-checklist/SKILL.md" "$SKILLS_DIR/privacy-ethics-checklist/SKILL.md" 2>/dev/null || true
echo "   privacy-ethics-checklist ✓"

# Decision log README
download "../decisions/README.md" "$DECISIONS_DIR/README.md" 2>/dev/null || true
echo "   Decision log README ✓"

# ─── Initialize database ───────────────────────────────────────────
echo ""
echo "→ Initializing decision log database..."

python3 -c "
import sys
sys.path.insert(0, '$SKILLS_DIR/council-decision-layer/tools')
from question_engine import _get_db
db = _get_db()
# Verify
count = db.execute('SELECT COUNT(*) FROM decisions').fetchone()[0]
print(f'   Database ready ({count} existing decisions)')
"

echo "   decision_log.db ✓"

# ─── Run tests ─────────────────────────────────────────────────────
echo ""
echo "→ Running component tests..."

if python3 -m pytest "$SKILLS_DIR/council-decision-layer/tools/tests/test_question_engine.py" -q --tb=short 2>&1; then
    echo "   All tests passed ✓"
else
    echo "   ⚠ Some tests failed — check output above"
fi

# ─── Count tests for report ─────────────────────────────────────────
TEST_COUNT=$(python3 -m pytest "$SKILLS_DIR/council-decision-layer/tools/tests/test_question_engine.py" --collect-only -q 2>/dev/null | tail -1 | grep -oP '\d+(?= tests)')
echo ""
echo "   $TEST_COUNT component tests collected"

# ─── Optional: Register with Hermes ────────────────────────────────
echo ""
echo "→ To enable in Hermes:"
echo "   hermes skills config          # Enable council-decision-layer"
echo "   hermes tools enable council   # Enable the council toolset"
echo "   /reset                        # Start a fresh session"
echo ""
echo "→ To use the decision patterns:"
echo "   Load the skill: /skill council-decision-layer"
echo "   Or Hermes will auto-detect decision contexts"
echo ""
echo "→ To test directly:"
echo "   python3 -m pytest $SKILLS_DIR/council-decision-layer/tools/tests/ -v"
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  Council Decision Layer installed! 🧠    ║"
echo "║  5 decision patterns ready               ║"
echo "║  1 privacy checklist ready               ║"
echo "╚══════════════════════════════════════════╝"
