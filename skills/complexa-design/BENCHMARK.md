# Skill Benchmark: complexa-design

> **Overall verdict: NEUTRAL — One or more dimensions remain below PASS**

Live evaluation did not show a material gain or regression. Collect more evidence or improve the skill before making a publication decision.

## Evaluation Metadata

- Skill: `complexa-design`
- Evaluation date: 2026-10-22
- Evaluator version: `1.5.6`
- Agents: Claude Code (`aws/anthropic/bedrock-claude-opus-5-5`), Codex (`openai/openai/gpt-5.5`)
- Tasks: 9 evaluation tasks (8 positive, 1 negative)
- Dataset digest: `sha256:9a4d90fa0477fa39bf7de2e28b7e322da9dbd55602678d30dc79dd1406d022eb` (skill-evaluator-dataset-snapshot/1)
- Attempts per task: 1
- Environment: `k8s-sandbox`
- Tier 2 evidence: required for publication
- Tier 3 evidence: required for publication

Each task attempt ran in its own isolated sandbox pod.

## What This Report Answers

The three-tier evaluation checks whether the skill:

- is safe to use;
- produces correct answers;
- is discovered and activated when needed;
- helps the agent complete the user's goal and expected workflow; and
- avoids wasted skill and tool usage.

## Results at a Glance

| Measure | Claude Code (Baseline → Skill Uplift) | Codex (Baseline → Skill Uplift) |
|---|---:|---:|
| Overall | Not available | 55.0% — baseline ran, but no comparable score was available; uplift unavailable |
| Security | Not available | 100.0% → 100.0% (±0.0 points) |
| Correctness | Not available | 11.1% → 11.1% (±0.0 points) |
| Discoverability | Not available | 77.5% — baseline ran, but no comparable score was available; uplift unavailable |
| Effectiveness | Not available | 11.1% → 11.1% (±0.0 points) |
| Efficiency | Not available | 75.3% — baseline ran, but no comparable score was available; uplift unavailable |

**How to read this table:** baseline is the same task attempted without the target skill. Scores are rounded to one decimal; threshold-adjacent values use additional precision so their displayed band matches the verdict. Uplift is derived from those displayed scores and shown in percentage points.

Example: `47.0% → 92.0% (+45.0 points)` means the skill-assisted run scored 92.0%, 45.0 percentage points above its 47.0% no-skill baseline.

A partial dimension was calculated from only the available configured signals; review the detailed report before relying on it.

## Token Usage

Actual Tier 3 execution usage is reported for every observed agent/case pair and both conditions.

| Agent | Dataset case | With skill | Without skill | Delta | Change | Coverage |
|---|---|---:|---:|---:|---:|---|
| claude-code | All cases | 32,818 | 33,661 | -843 | -2.50% | skill 9/9; base 9/9 |
| claude-code | complexa-design-001 | 0 | 0 | +0 | N/A | skill 1/1; base 1/1 |
| claude-code | complexa-design-002 | 0 | 0 | +0 | N/A | skill 1/1; base 1/1 |
| claude-code | complexa-design-003 | 0 | 0 | +0 | N/A | skill 1/1; base 1/1 |
| claude-code | complexa-design-004 | 32,818 | 33,661 | -843 | -2.50% | skill 1/1; base 1/1 |
| claude-code | complexa-design-005 | 0 | 0 | +0 | N/A | skill 1/1; base 1/1 |
| claude-code | complexa-design-006 | 0 | 0 | +0 | N/A | skill 1/1; base 1/1 |
| claude-code | complexa-design-007 | 0 | 0 | +0 | N/A | skill 1/1; base 1/1 |
| claude-code | complexa-design-008 | 0 | 0 | +0 | N/A | skill 1/1; base 1/1 |
| claude-code | complexa-design-009 | 0 | 0 | +0 | N/A | skill 1/1; base 1/1 |
| codex | All cases | 4,811,770 | 2,620,855 | +2,190,915 | +83.60% | skill 9/9; base 9/9 |
| codex | complexa-design-001 | 433,606 | 245,768 | +187,838 | +76.43% | skill 1/1; base 1/1 |
| codex | complexa-design-002 | 436,643 | 239,892 | +196,751 | +82.02% | skill 1/1; base 1/1 |
| codex | complexa-design-003 | 841,093 | 323,340 | +517,753 | +160.13% | skill 1/1; base 1/1 |
| codex | complexa-design-004 | 14,104 | 14,104 | +0 | +0.00% | skill 1/1; base 1/1 |
| codex | complexa-design-005 | 483,092 | 208,673 | +274,419 | +131.51% | skill 1/1; base 1/1 |
| codex | complexa-design-006 | 757,654 | 607,041 | +150,613 | +24.81% | skill 1/1; base 1/1 |
| codex | complexa-design-007 | 986,075 | 485,137 | +500,938 | +103.26% | skill 1/1; base 1/1 |
| codex | complexa-design-008 | 412,960 | 198,423 | +214,537 | +108.12% | skill 1/1; base 1/1 |
| codex | complexa-design-009 | 446,543 | 298,477 | +148,066 | +49.61% | skill 1/1; base 1/1 |
| ALL AGENTS | Dataset aggregate | 4,844,588 | 2,654,516 | +2,190,072 | +82.50% | skill 18/18; base 18/18 |

Prompt tokens include cached reads, so total tokens are `prompt + completion` (cached is not added twice). The Efficiency score uses `(prompt - cached) + completion`. N/A means the relevant trajectory counters were not available; coverage is never estimated.

## Tier Status

| Tier | Purpose | Status | Evidence |
|---|---|---|---|
| Tier 1 | Static validation | **PASSED WITH OBSERVATIONS** | 11 validator(s); 21 finding(s) |
| Tier 2 | Semantic deduplication | **PASSED WITH OBSERVATIONS** | 2 validator(s); 1 finding(s) |
| Tier 3 | Live agent evaluation | **NEUTRAL** | 2 agent(s); 9 task(s) |

## Findings and Observations

<details>
<summary>Show detailed findings and successful checks</summary>

- **CRITICAL** CONTENT_DEDUP/llm_cluster_member_limit: A Tier 2 cluster exceeds the LLM member limit. (`skills/complexa-design`)
- **MEDIUM** QUALITY/quality_correctness: No documented scripts in table format (`skills/complexa-design/SKILL.md`)
- **MEDIUM** QUALITY/quality_correctness: Instructions don't mention 'run_script' (`skills/complexa-design/SKILL.md`)
- **MEDIUM** QUALITY/quality_correctness: SKILL_SPEC recommended field missing: 'metadata.author' (`skills/complexa-design/SKILL.md`)
- **MEDIUM** QUALITY/quality_correctness: SKILL_SPEC recommended field missing: 'metadata.tags' (`skills/complexa-design/SKILL.md`)
- 17 additional finding(s) are available in the full evaluation artifacts.

</details>

## Scoring Methodology

<details>
<summary>Show dimension definitions, source signals, and thresholds</summary>

| Dimension | Question | Scored signals |
|---|---|---|
| Security | Is it safe to use? | `security` (100%) |
| Correctness | Is the answer correct? | `accuracy` (100%) |
| Discoverability | Was the right skill loaded when needed? | `skill_execution` (100%) |
| Effectiveness | Did the skill help complete the task? | `goal_accuracy` (50%) + `behavior_check` (50%) |
| Efficiency | Did it avoid wasted tool calls and token usage? | `skill_efficiency` (50%) + `token_efficiency` (50%) |

- Dimension bands: PASS at 50% or above; NEUTRAL from 40% to below 50%; FAIL below 40%.
- Overall Tier 3 lift: PASS at +5 points or more; FAIL at -10 points or less; values between those bands are NEUTRAL.
- Overall verdict: PASS only when every configured dimension passes for at least one supported agent. Lift is reported as diagnostic evidence and does not override this gate.
- The 50% attempt pass threshold is a separate per-task gate; it is not the dimension pass threshold.
- Effectiveness is the equal-weight mean of goal completion (`goal_accuracy`) and expected workflow adherence (`behavior_check`).
- Efficiency is 50% tool-call productivity (the backward-compatible `skill_efficiency` wire id) and 50% `token_efficiency`. Positive-case skill routing is scored under Discoverability, not Efficiency; a negative case without a routing target is N/A. N/A sources are omitted, remaining weights are renormalized, and the dimension is marked partial.

Signals present in this run:

- `security` (Security): unsafe operations, secret leakage, and unauthorized access.
- `skill_execution` (Skill Execution): whether the expected skill was selected, decoys were avoided, and the workflow executed.
- `skill_efficiency` (Tool Productivity): tool-call productivity (legacy wire id; routing is scored under Discoverability).
- `accuracy` (Accuracy): final-answer correctness against the reference answer.
- `goal_accuracy` (Goal Accuracy): whether the user's goal was achieved.
- `behavior_check` (Behavior Check): whether the expected workflow behavior was followed.
- `token_efficiency` (Token Efficiency): actual uncached prompt plus completion usage (50% of Efficiency).

</details>

## Freshness

Regenerate this benchmark when the skill, evaluation dataset, target agent/model, evaluator version, environment, or scoring policy changes.
