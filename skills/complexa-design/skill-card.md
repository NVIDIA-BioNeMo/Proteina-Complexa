## Description: <br>
Agent runbook for orchestrating an end-to-end protein, ligand-binder, or AME design through the separately installed first-party Proteina-Complexa CLI. <br>

This skill is for research and development only. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
## Use Case: <br>
Developers and computational biologists use this skill to drive the full four-stage Proteina-Complexa design pipeline (generate, filter, evaluate, analyze) for de novo protein binders, ligand binders, or AME scaffolds, selecting the correct pipeline config, validating readiness, running the CLI, and emitting a replayable run manifest with per-design success and diversity results. <br>

### Deployment Geography for Use: <br>
Global <br>

## Requirements / Dependencies: <br>
**Requires API Key or External Credential:** [Not Specified] <br>
**Credential Type(s):** [None identified] <br>

Do not include secrets in prompts/logs/output; use least-privilege credentials; rotate keys as appropriate. <br>

## Known Risks and Mitigations: <br>
Risk: Review before execution as proposals could introduce incorrect or misleading guidance into skills. <br>
Mitigation: Review and scan skill before deployment. <br>

## Reference(s): <br>
- [Pipeline Reference](references/pipelines.md) <br>
- [Inference and Search Guide](references/INFERENCE.md) <br>
- [Evaluation Metrics Guide](references/EVALUATION_METRICS.md) <br>
- [Pipeline Configuration Guide](references/CONFIGURATION_GUIDE.md) <br>
- [Overrides Reference](references/overrides.md) <br>
- [Hardware Reference](references/hardware.md) <br>
- [Troubleshooting Reference](references/troubleshooting.md) <br>
- [Sweep System](references/SWEEP.md) <br>
- [Search Metadata Tags](references/SEARCH_METADATA.md) <br>


## Skill Output: <br>
**Output Type(s):** [Shell commands, Configuration instructions, Files, Analysis] <br>
**Output Format:** [Markdown with inline bash code blocks, plus a JSON run manifest and result CSV summaries] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Writes a replayable JSON run manifest and summarizes success-rate, per-design, and diversity CSVs produced by the CLI run] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-4-8`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
4 evaluation tasks (3 positive, 1 negative), one attempt per task, each run in an isolated k8s-sandbox pod. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Is the skill safe to use? Checks for unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Is the final answer correct against the reference answer? <br>
- Discoverability: Was the expected skill selected and activated when needed while decoys were avoided? <br>
- Effectiveness: Did the skill help complete the task? Equal-weight mean of goal completion and expected workflow adherence. <br>
- Efficiency: Did the run avoid wasted tool calls and token usage? <br>

Underlying evaluation signals used in this run: <br>
- `security`: Flags unsafe operations, secret leakage, and unauthorized access. <br>
- `accuracy`: Final-answer correctness against the reference answer. <br>
- `skill_execution`: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- `goal_accuracy`: Whether the user's goal was achieved. <br>
- `behavior_check`: Whether the expected workflow behavior was followed. <br>
- `skill_efficiency`: Tool-call productivity (legacy wire id; routing is scored under Discoverability). <br>
- `token_efficiency`: Actual uncached prompt plus completion token usage. <br>



## Evaluation Results: <br>
| Measure | Claude Code (Baseline → Skill Uplift) | Codex (Baseline → Skill Uplift) |
|---|---:|---:|
| Overall | 92.1% — baseline ran, but no comparable score was available; uplift unavailable | 89.2% — baseline ran, but no comparable score was available; uplift unavailable |
| Security | 100.0% → 100.0% (±0.0 points) | 100.0% → 100.0% (±0.0 points) |
| Correctness | 100.0% → 100.0% (±0.0 points) | 100.0% → 100.0% (±0.0 points) |
| Discoverability | 86.7% — baseline ran, but no comparable score was available; uplift unavailable | 76.7% — baseline ran, but no comparable score was available; uplift unavailable |
| Effectiveness | 100.0% → 96.9% (-3.1 points) | 100.0% → 96.9% (-3.1 points) |
| Efficiency | 76.8% — baseline ran, but no comparable score was available; uplift unavailable | 72.6% — baseline ran, but no comparable score was available; uplift unavailable |

## Skill Version(s): <br>
1.1.0 (source: pyproject.toml) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
