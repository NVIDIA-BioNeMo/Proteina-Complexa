## Description: <br>
Agent runbook for evaluating an existing PDB directory through the separately installed first-party Proteina-Complexa CLI. <br>

This skill is ready for commercial/non-commercial use. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
Apache 2.0 (code); see licenses/ for other components <br>
## Use Case: <br>
Developers and computational biologists use this skill to evaluate and score directories of pre-existing PDB protein structure files using the Proteina-Complexa pipeline's refolding, interface metrics, and designability analysis. <br>

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
- [Evaluate Config Reference](references/eval_configs.md) <br>
- [Evaluation & Analysis Guide](references/EVALUATION_METRICS.md) <br>
- [Pipeline Configuration Guide](references/CONFIGURATION_GUIDE.md) <br>
- [Hardware Requirements](references/hardware.md) <br>


## Skill Output: <br>
**Output Type(s):** [Shell commands, Analysis, Files] <br>
**Output Format:** [Markdown with inline bash code blocks and CSV/JSON result files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Per-PDB metrics CSV, pass-rate summaries, diversity cluster files, and a JSON replay manifest] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-4-8`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
4 evaluation tasks (3 positive, 1 negative), 3 attempts per task, each in an isolated k8s-sandbox pod. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Whether the skill is safe to use — checks for unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Whether the final answer is correct against the reference answer. <br>
- Discoverability: Whether the right skill was loaded and activated when needed, and decoys were avoided. <br>
- Effectiveness: Whether the skill helped complete the user's goal (50% goal accuracy + 50% behavior check). <br>
- Efficiency: Whether the skill avoided wasted tool calls and token usage (50% tool productivity + 50% token efficiency). <br>

Underlying evaluation signals used in this run: <br>
- `security`: Unsafe operations, secret leakage, and unauthorized access. <br>
- `accuracy`: Final-answer correctness against the reference answer. <br>
- `skill_execution`: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- `goal_accuracy`: Whether the user's goal was achieved. <br>
- `behavior_check`: Whether the expected workflow behavior was followed. <br>
- `skill_efficiency`: Tool-call productivity (routing scored under Discoverability). <br>
- `token_efficiency`: Actual uncached prompt plus completion token usage. <br>



## Evaluation Results: <br>
| Measure | Claude Code (Baseline → Skill Uplift) | Codex (Baseline → Skill Uplift) |
|---|---:|---:|
| Overall | 85.9% | 80.4% |
| Security | 100.0% → 100.0% (±0.0 pp) | 87.5% → 100.0% (+12.5 pp) |
| Correctness | 31.1% → 100.0% (+68.9 pp) | 45.0% → 100.0% (+55.0 pp) |
| Discoverability | 90.0% | 83.3% |
| Effectiveness | 22.8% → 55.0% (+32.2 pp) | 21.9% → 43.8% (+21.9 pp) |
| Efficiency | 84.6% | 75.0% |

## Skill Version(s): <br>
1.1.0 (source: pyproject.toml) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
