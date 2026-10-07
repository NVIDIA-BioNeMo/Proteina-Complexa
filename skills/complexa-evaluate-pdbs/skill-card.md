## Description: <br>
Agent runbook for evaluating an existing PDB directory through the separately installed first-party Proteina-Complexa CLI, computing interface metrics (i_pAE, pLDDT, scRMSD), designability, and pass-rate summaries across protein binder, ligand binder, and motif binder result types. <br>

This skill is ready for commercial/non-commercial use. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
Multiple licenses (see LICENSE) <br>
## Use Case: <br>
Developers and computational biologists use this skill to evaluate protein structure designs by refolding PDB files with AF2, RF3, ESMFold, or Boltz2 backends and computing interface quality metrics, designability scores, and pass-rate summaries against configurable thresholds. <br>

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
- [eval_configs.md](references/eval_configs.md) <br>
- [hardware.md](references/hardware.md) <br>
- [EVALUATION_METRICS.md](references/EVALUATION_METRICS.md) <br>
- [CONFIGURATION_GUIDE.md](references/CONFIGURATION_GUIDE.md) <br>
- [INFERENCE.md](references/INFERENCE.md) <br>


## Skill Output: <br>
**Output Type(s):** [Analysis, Files, Shell commands] <br>
**Output Format:** [CSV files with per-PDB metrics, JSON pass-rate summaries, and a replay manifest] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [None] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-4-8`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
4 evaluation tasks (3 positive, 1 negative), each in an isolated k8s-sandbox pod. Evaluator version 1.5.6. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Checks for unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Final-answer correctness against a reference answer. <br>
- Discoverability: Whether the expected skill was selected, decoys avoided, and the workflow executed. <br>
- Effectiveness: Goal completion (50%) plus expected workflow adherence (50%). <br>
- Efficiency: Tool-call productivity (50%) plus token efficiency (50%). <br>

Underlying evaluation signals used in this run: <br>
- `security`: Unsafe operations, secret leakage, and unauthorized access. <br>
- `accuracy`: Final-answer correctness against the reference answer. <br>
- `skill_execution`: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- `goal_accuracy`: Whether the user's goal was achieved. <br>
- `behavior_check`: Whether the expected workflow behavior was followed. <br>
- `skill_efficiency`: Tool-call productivity. <br>
- `token_efficiency`: Actual uncached prompt plus completion token usage. <br>



## Evaluation Results: <br>
| Measure | Claude Code | Codex |
|---|---:|---:|
| Overall | 88.2% | 82.3% |
| Security | 100.0% (±0.0 pt uplift) | 100.0% (+25.0 pt uplift) |
| Correctness | 100.0% (+60.0 pt uplift) | 100.0% (+65.0 pt uplift) |
| Discoverability | 88.3% | 85.0% |
| Effectiveness | 65.0% (+35.4 pt uplift) | 51.3% (+18.8 pt uplift) |
| Efficiency | 87.5% | 75.3% |

## Skill Version(s): <br>
1.1.0 (source: pyproject.toml) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
