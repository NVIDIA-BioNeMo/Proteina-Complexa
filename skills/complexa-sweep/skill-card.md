## Description: <br>
Agent runbook for Proteina-Complexa parameter sweeps through the separately installed first-party CLI and config generator. <br>

This skill is for research and development only. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
Multiple licenses (see LICENSE) <br>
## Use Case: <br>
Developers and computational biologists use this skill to run systematic cartesian-product parameter sweeps over Proteina-Complexa protein design pipelines, enabling hyperparameter tuning, ablation studies, success-rate ranking, and Pareto-optimal configuration searches. <br>

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
- [Sweep System](references/SWEEP.md) <br>
- [Sweep Axes Catalogue](references/sweep_axes.md) <br>
- [Pipeline Configuration Guide](references/CONFIGURATION_GUIDE.md) <br>
- [Evaluation & Analysis Guide](references/EVALUATION_METRICS.md) <br>
- [Inference and Search Guide](references/INFERENCE.md) <br>
- [Search Metadata Tags](references/SEARCH_METADATA.md) <br>
- [Hardware Requirements](references/hardware.md) <br>


## Skill Output: <br>
**Output Type(s):** [Shell commands, Configuration files, CSV data, JSON manifest] <br>
**Output Format:** [YAML sweep configs, CSV summary tables, and JSON run manifests with terminal output] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [None] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-4-8`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
4 evaluation tasks (3 positive, 1 negative), each run in an isolated sandbox pod. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Whether the skill is safe to use, checking for unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Whether the skill produces correct answers against the reference answer. <br>
- Discoverability: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- Effectiveness: Whether the skill helps complete the user's goal (50% goal completion + 50% expected workflow adherence). <br>
- Efficiency: Whether the skill avoids wasted tool calls and token usage (50% tool-call productivity + 50% token efficiency). <br>

Underlying evaluation signals used in this run: <br>
- `security`: Checks for unsafe operations, secret leakage, and unauthorized access. <br>
- `accuracy`: Final-answer correctness against the reference answer. <br>
- `skill_execution`: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- `goal_accuracy`: Whether the user's goal was achieved. <br>
- `behavior_check`: Whether the expected workflow behavior was followed. <br>
- `skill_efficiency`: Tool-call productivity (routing scored under Discoverability). <br>
- `token_efficiency`: Actual uncached prompt plus completion token usage. <br>



## Evaluation Results: <br>
| Measure | Claude Code (Baseline → Skill Uplift) | Codex (Baseline → Skill Uplift) |
|---|---:|---:|
| Overall | Not available | 75.8% — baseline ran, but no comparable score was available; uplift unavailable |
| Security | Not available | 50.0% → 75.0% (+25.0 points) |
| Correctness | Not available | 45.0% → 80.0% (+35.0 points) |
| Discoverability | Not available | 81.7% — baseline ran, but no comparable score was available; uplift unavailable |
| Effectiveness | Not available | 41.9% → 63.8% (+21.9 points) |
| Efficiency | Not available | 78.4% — baseline ran, but no comparable score was available; uplift unavailable |

## Skill Version(s): <br>
1.1.0 (source: pyproject.toml) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
