# Skill Benchmark: complexa-target

> **Overall verdict: NEUTRAL — One or more dimensions remain below PASS**

Live evaluation did not show a material gain or regression. Collect more evidence or improve the skill before making a publication decision.

## Evaluation Metadata

- Skill: `complexa-target`
- Evaluation date: 2026-09-17
- Evaluator version: `1.5.6`
- Agents: Claude Code (`aws/anthropic/bedrock-claude-opus-4-8`), Codex (`openai/openai/gpt-5.5`)
- Tasks: 4 evaluation tasks (3 positive, 1 negative)
- Dataset digest: `sha256:9501fe4a4a90ef80d10b747a8c7319c28b3e706b8909d8abb2f8462b3e9edf9d` (skill-evaluator-dataset-snapshot/1)
- Attempts per task: 3
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
| Overall | 95.2% — baseline ran, but no comparable score was available; uplift unavailable | 81.6% — baseline ran, but no comparable score was available; uplift unavailable |
| Security | 100.0% → 100.0% (±0.0 points) | 50.0% → 50.0% (±0.0 points) |
| Correctness | 100.0% → 100.0% (±0.0 points) | 100.0% → 100.0% (±0.0 points) |
| Discoverability | 95.0% — baseline ran, but no comparable score was available; uplift unavailable | 90.0% — baseline ran, but no comparable score was available; uplift unavailable |
| Effectiveness | 95.0% → 100.0% (+5.0 points) | 85.0% → 93.8% (+8.8 points) |
| Efficiency | 80.8% — baseline ran, but no comparable score was available; uplift unavailable | 74.1% — baseline ran, but no comparable score was available; uplift unavailable |

**How to read this table:** baseline is the same task attempted without the target skill. Scores are rounded to one decimal; threshold-adjacent values use additional precision so their displayed band matches the verdict. Uplift is derived from those displayed scores and shown in percentage points.

Example: `47.0% → 92.0% (+45.0 points)` means the skill-assisted run scored 92.0%, 45.0 percentage points above its 47.0% no-skill baseline.

A partial dimension was calculated from only the available configured signals; review the detailed report before relying on it.

## Token Usage

Actual Tier 3 execution usage is reported for every observed agent/case pair and both conditions.

| Agent | Dataset case | With skill | Without skill | Delta | Change | Coverage |
|---|---|---:|---:|---:|---:|---|
| claude-code | All cases | 1,657,978 | 1,920,071 | -262,093 | -13.65% | skill 4/4; base 4/4 |
| claude-code | complexa-target-001 | 458,613 | 420,680 | +37,933 | +9.02% | skill 1/1; base 1/1 |
| claude-code | complexa-target-002 | 498,456 | 751,346 | -252,890 | -33.66% | skill 1/1; base 1/1 |
| claude-code | complexa-target-003 | 460,575 | 514,090 | -53,515 | -10.41% | skill 1/1; base 1/1 |
| claude-code | complexa-target-004 | 240,334 | 233,955 | +6,379 | +2.73% | skill 1/1; base 1/1 |
| codex | All cases | 702,726 | 497,049 | +205,677 | +41.38% | skill 4/4; base 4/4 |
| codex | complexa-target-001 | 254,842 | 190,848 | +63,994 | +33.53% | skill 1/1; base 1/1 |
| codex | complexa-target-002 | 232,588 | 106,585 | +126,003 | +118.22% | skill 1/1; base 1/1 |
| codex | complexa-target-003 | 104,305 | 58,716 | +45,589 | +77.64% | skill 1/1; base 1/1 |
| codex | complexa-target-004 | 110,991 | 140,900 | -29,909 | -21.23% | skill 1/1; base 1/1 |
| ALL AGENTS | Dataset aggregate | 2,360,704 | 2,417,120 | -56,416 | -2.33% | skill 8/8; base 8/8 |

Prompt tokens include cached reads, so total tokens are `prompt + completion` (cached is not added twice). The Efficiency score uses `(prompt - cached) + completion`. N/A means the relevant trajectory counters were not available; coverage is never estimated.

## Tier Status

| Tier | Purpose | Status | Evidence |
|---|---|---|---|
| Tier 1 | Static validation | **PASSED WITH OBSERVATIONS** | 11 validator(s); 11 finding(s) |
| Tier 2 | Semantic deduplication | **PASSED** | 2 validator(s); 0 finding(s) |
| Tier 3 | Live agent evaluation | **NEUTRAL** | 2 agent(s); 4 task(s) |

## Findings and Observations

<details>
<summary>Show detailed findings and successful checks</summary>

- **MEDIUM** QUALITY/quality_correctness: SKILL_SPEC recommended field missing: 'metadata.author' (`skills/complexa-target/SKILL.md`)
- **MEDIUM** QUALITY/quality_correctness: SKILL_SPEC recommended field missing: 'metadata.tags' (`skills/complexa-target/SKILL.md`)
- **MEDIUM** SCHEMA/body_recommended_section: Missing recommended section: '## Instructions' (`skills/complexa-target/SKILL.md`)
- **MEDIUM** SCHEMA/body_recommended_section: Missing recommended section: '## Examples' (`skills/complexa-target/SKILL.md`)
- **MEDIUM** SCHEMA/author_missing: Author not specified in metadata (`skills/complexa-target/SKILL.md`)
- 6 additional finding(s) are available in the full evaluation artifacts.

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
