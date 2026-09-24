## Description: <br>
Agent runbook for Proteina-Complexa parameter sweeps through the separately installed first-party CLI and config generator. <br>

This skill is for research and development only. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
Multiple (see LICENSE) <br>
## Use Case: <br>
Developers and computational biology researchers running cartesian-product hyperparameter sweeps over Proteina-Complexa protein binder design pipelines for quality-cost optimization, ablation studies, and Pareto searches. <br>

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
- [CONFIGURATION_GUIDE.md](references/CONFIGURATION_GUIDE.md) <br>
- [EVALUATION_METRICS.md](references/EVALUATION_METRICS.md) <br>
- [INFERENCE.md](references/INFERENCE.md) <br>
- [SEARCH_METADATA.md](references/SEARCH_METADATA.md) <br>
- [SWEEP.md](references/SWEEP.md) <br>
- [hardware.md](references/hardware.md) <br>
- [sweep_axes.md](references/sweep_axes.md) <br>


## Skill Output: <br>
**Output Type(s):** [Shell commands, Configuration files, CSV analysis, JSON manifest] <br>
**Output Format:** [Markdown with inline bash code blocks] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [None] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-4-8`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
6 evaluation tasks (5 positive, 1 negative) executed with 3 attempts per task in isolated k8s-sandbox pods. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Checks for unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Final-answer correctness against the reference answer. <br>
- Discoverability: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- Effectiveness: Equal-weight mean of goal completion (goal_accuracy) and expected workflow adherence (behavior_check). <br>
- Efficiency: 50% tool-call productivity and 50% token efficiency. <br>

Underlying evaluation signals used in this run: <br>
- `security`: Unsafe operations, secret leakage, and unauthorized access. <br>
- `accuracy`: Final-answer correctness against the reference answer. <br>
- `skill_execution`: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- `goal_accuracy`: Whether the user's goal was achieved. <br>
- `behavior_check`: Whether the expected workflow behavior was followed. <br>
- `skill_efficiency`: Tool-call productivity (routing scored under Discoverability). <br>
- `token_efficiency`: Actual uncached prompt plus completion token usage. <br>



## Evaluation Results: <br>
| Dimension | Tasks | Claude Code |
|---|---:|---:|
| Overall | 6 | 91.0% |
| Security | 6 | 100.0% |
| Correctness | 6 | 96.7% |
| Discoverability | 6 | 88.0% |
| Effectiveness | 6 | 98.0% |
| Efficiency | 6 | 72.2% |

## Skill Version(s): <br>
1.1.0 (source: pyproject.toml) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
