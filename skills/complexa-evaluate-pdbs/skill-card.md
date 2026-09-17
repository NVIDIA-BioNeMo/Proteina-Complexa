## Description: <br>
Agent runbook for evaluating an existing PDB directory through the separately installed first-party Proteina-Complexa CLI, supporting refolding, interface metrics (i_pAE, pLDDT, scRMSD), designability, and pass-rate analysis for protein binder, ligand binder, and AME designs. <br>

This skill is for research and development only. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
## Use Case: <br>
Developers and computational biologists who need to evaluate designed protein structures (PDB files) using the Proteina-Complexa evaluation pipeline — refolding with AF2, RF3, ESMFold, or Boltz2, computing interface and monomer metrics, and generating pass-rate summaries. <br>

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
- [Evaluation Configs Reference](references/eval_configs.md) <br>
- [Evaluation & Analysis Guide](references/EVALUATION_METRICS.md) <br>
- [Pipeline Configuration Guide](references/CONFIGURATION_GUIDE.md) <br>
- [Hardware Requirements](references/hardware.md) <br>
- [Inference and Search Guide](references/INFERENCE.md) <br>


## Skill Output: <br>
**Output Type(s):** [Analysis, Shell commands, Files] <br>
**Output Format:** [CSV and JSON files with Markdown summary] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Per-PDB metrics CSV, pass-rate summaries, diversity cluster files, run manifest JSON] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-4-8`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
4 evaluation tasks (3 positive, 1 negative), 3 attempts per task, each in an isolated sandbox pod. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Checks for unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Final-answer correctness against the reference answer. <br>
- Discoverability: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- Effectiveness: Goal completion (goal_accuracy, 50%) and expected workflow adherence (behavior_check, 50%). <br>
- Efficiency: Tool-call productivity (skill_efficiency, 50%) and token efficiency (token_efficiency, 50%). <br>

Underlying evaluation signals used in this run: <br>
- `security`: Unsafe operations, secret leakage, and unauthorized access. <br>
- `accuracy`: Final-answer correctness against the reference answer. <br>
- `skill_execution`: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- `goal_accuracy`: Whether the user's goal was achieved. <br>
- `behavior_check`: Whether the expected workflow behavior was followed. <br>
- `skill_efficiency`: Tool-call productivity (legacy wire id; routing scored under Discoverability). <br>
- `token_efficiency`: Actual uncached prompt plus completion token usage. <br>



## Evaluation Results: <br>
| Measure | Claude Code (Baseline → Skill) | Codex (Baseline → Skill) |
|---|---:|---:|
| Overall | 84.8% | 81.2% |
| Security | 90.0% → 100.0% (+10.0 pp) | 100.0% → 100.0% (±0.0 pp) |
| Correctness | 14.0% → 85.0% (+71.0 pp) | 30.0% → 90.0% (+60.0 pp) |
| Discoverability | 91.7% | 90.0% |
| Effectiveness | 24.3% → 58.3% (+34.0 pp) | 20.3% → 50.0% (+29.7 pp) |
| Efficiency | 88.9% | 75.7% |

## Skill Version(s): <br>
1.1.0 (source: pyproject.toml) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
