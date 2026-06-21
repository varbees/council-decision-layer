# AgentOps Trajectory Check — Google Agent Guide §3

**Source:** Google Startup Technical Guide: AI Agents, Section 3
**When:** Planning multi-step agent tasks, evaluating agent reasoning paths

## The Principle

Agent failures rarely happen at the final outcome — they happen at a single
Reason, Act, or Observe step in the middle of the trajectory. Evaluating the
full reasoning path is how you catch failures before they compound.

## The 4-Layer AgentOps Evaluation Framework

### Layer 1: Component Evaluation (Deterministic)
Test the non-LLM parts: tools, parsers, API integrations.
- Does the tool handle valid/invalid/edge-case inputs?
- Does the data parser survive malformed responses?
- Do API integrations handle success, error, timeout?

### Layer 2: Trajectory Evaluation (Procedural Correctness)
This is the critical layer. Evaluate each step of the ReAct cycle:
- **Reason:** Did the agent correctly assess the goal and state? Is its hypothesis logical?
- **Act:** Did it select the RIGHT tool? Did it correctly format the arguments?
- **Observe:** Did it correctly interpret the tool output to inform the next step?

### Layer 3: Outcome Evaluation (Semantic Correctness)
Evaluate the final response:
- Is it factually accurate and grounded in retrieved information?
- Does it fully address the user's need?
- Is the tone and completeness appropriate?

### Layer 4: System Monitoring (In-Production)
Continuous monitoring of live agent performance:
- Tool failure rates, user feedback, trajectory metrics (steps/task)
- End-to-end latency, token costs
- Behavioral drift detection

## The Trajectory Check (Our Adaptation)

For each multi-step agent task, BEFORE execution:

### Step 1: Define the goal precisely
Not "deploy something" but "Deploy PhotoSelect to staging, run health checks,
verify the /api/health endpoint returns 200, and report results."

### Step 2: Map expected ReAct steps
```
R1: Parse deployment request → understand target, preconditions
A1: Run pre-deployment checks (lint, tests, build)
O1: Tests pass? Errors? → assess
R2: Based on O1, decide: proceed or abort
A2: If proceed: run deploy command
O2: Deploy output → success/failure signals
R3: If success: verify with health check
A3: curl health endpoint
O3: Response status → report
```

### Step 3: Identify failure points
At each step, what could go wrong?
- A1: Tests flaky? Build fails on missing env var?
- A2: Deploy timeout? Permission error?
- A3: Health check returns 503 (cold start)?
- Tool Selection: Agent uses `kubectl` instead of `gcloud`?
- Parameter Generation: Agent passes wrong project ID?

### Step 4: Set guardrails
- Max steps: 15 (prevent infinite loops)
- Timeout: 5 minutes
- Approval gate: Required for production deploys, destructive ops
- Input validation: Sanitize args before passing to shell

### Step 5: Define success criteria
- Component level: All tools executed without error
- Trajectory level: Steps followed logical order, no backtracking loops
- Outcome level: Health check returns 200, response is correctly reported
- Monitoring level: Latency <3min, token cost <$0.50

## Anti-Patterns

- **"The agent will figure it out":** Hope is not a strategy. Define expected paths.
- **Testing only the final output:** The trajectory is the product. Evaluate it.
- **No step limit:** Agents loop. Always cap iterations.
- **No approval gates:** Destructive actions need human confirmation.

## Google Guide Quotable

> "Moving beyond superficial 'vibe-testing' requires a rigorous engineering
> approach to ensure an agent operates safely and provides consistent value."
> — Google Agent Guide, Section 3
