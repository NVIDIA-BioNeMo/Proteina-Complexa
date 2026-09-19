## Description: <br>
Agent runbook for orchestrating an end-to-end protein, ligand-binder, or AME design through the separately installed first-party Proteina-Complexa CLI. <br>

This skill is for research and development only. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
Apache 2.0 (code), CC-BY-4.0 (datasets), NVIDIA Open Model License (weights) <br>
## Use Case: <br>
Developers and computational biology researchers use this skill to orchestrate end-to-end protein binder, ligand-binder, or AME design campaigns through the Proteina-Complexa CLI. <br>

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
- [Pipeline Configuration Guide](references/CONFIGURATION_GUIDE.md) <br>
- [Evaluation & Analysis Guide](references/EVALUATION_METRICS.md) <br>
- [Inference and Search Guide](references/INFERENCE.md) <br>
- [Search Metadata Tags](references/SEARCH_METADATA.md) <br>
- [Sweep System](references/SWEEP.md) <br>
- [Hardware Reference](references/hardware.md) <br>
- [Overrides Reference](references/overrides.md) <br>
- [Pipeline Reference](references/pipelines.md) <br>
- [Troubleshooting Reference](references/troubleshooting.md) <br>


## Skill Output: <br>
**Output Type(s):** [Shell commands, Configuration instructions, Files, Analysis] <br>
**Output Format:** [Markdown with inline bash code blocks] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [JSON manifest and CSV result files] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-4-8`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
4 evaluation tasks (3 positive, 1 negative) with 3 attempts per task in isolated k8s-sandbox pods. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Checks for unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Verifies final-answer correctness against the reference answer. <br>
- Discoverability: Checks whether the expected skill was selected and the workflow executed. <br>
- Effectiveness: Equal-weight mean of goal completion and expected workflow adherence. <br>
- Efficiency: Tool-call productivity (50%) and token efficiency (50%). <br>

Underlying evaluation signals used in this run: <br>
- `security`: Detects unsafe operations, secret leakage, and unauthorized access. <br>
- `accuracy`: Final-answer correctness against the reference answer. <br>
- `skill_execution`: Whether the expected skill was selected and decoys were avoided. <br>
- `goal_accuracy`: Whether the user's goal was achieved. <br>
- `behavior_check`: Whether the expected workflow behavior was followed. <br>
- `skill_efficiency`: Tool-call productivity across the run. <br>
- `token_efficiency`: Actual uncached prompt plus completion token usage. <br>



## Evaluation Results: <br>
| Measure | Claude Code (Baseline → Skill Uplift) | Codex (Baseline → Skill Uplift) |
|---|---:|---:|
| Overall | 90.5% | 90.3% |
| Security | 75.0% → 100.0% (+25.0 points) | 100.0% → 100.0% (±0.0 points) |
| Correctness | 100.0% → 100.0% (±0.0 points) | 100.0% → 100.0% (±0.0 points) |
| Discoverability | 81.7% | 83.3% |
| Effectiveness | 100.0% → 100.0% (±0.0 points) | 100.0% → 98.8% (-1.2 points) |
| Efficiency | 70.8% | 69.6% |

## Skill Version(s): <br>
1.1.0 (source: pyproject.toml) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
