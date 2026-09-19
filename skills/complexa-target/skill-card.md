## Description: <br>
Add, edit, inspect, or validate Proteina-Complexa target definitions for protein binders, ligand binders, and AME motif scaffolding. <br>

This skill is ready for commercial/non-commercial use. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
## Use Case: <br>
Developers and computational biologists use this skill to register, edit, and validate protein binder, ligand binder, and AME motif scaffolding target definitions in Proteina-Complexa YAML configuration files. <br>

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
- [Target Schema Reference](references/target_schema.md) <br>
- [Hardware Requirements](references/hardware.md) <br>


## Skill Output: <br>
**Output Type(s):** [Configuration instructions, Files] <br>
**Output Format:** [YAML configuration blocks] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [None] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-4-8`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
4 evaluation tasks (3 positive, 1 negative) against dataset digest sha256:9501fe4a4a90ef80d10b747a8c7319c28b3e706b8909d8abb2f8462b3e9edf9d. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Is it safe to use? Checks for unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Is the answer correct? Final-answer correctness against the reference answer. <br>
- Discoverability: Was the right skill loaded when needed? Whether the expected skill was selected and decoys were avoided. <br>
- Effectiveness: Did the skill help complete the task? Equal-weight mean of goal completion and expected workflow adherence. <br>
- Efficiency: Did it avoid wasted tool calls and token usage? 50% tool-call productivity and 50% token efficiency. <br>

Underlying evaluation signals used in this run: <br>
- `security`: Unsafe operations, secret leakage, and unauthorized access. <br>
- `skill_execution`: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- `skill_efficiency`: Tool-call productivity (routing is scored under Discoverability). <br>
- `accuracy`: Final-answer correctness against the reference answer. <br>
- `goal_accuracy`: Whether the user's goal was achieved. <br>
- `behavior_check`: Whether the expected workflow behavior was followed. <br>
- `token_efficiency`: Actual uncached prompt plus completion token usage. <br>



## Evaluation Results: <br>
| Measure | Claude Code (Baseline → Skill Uplift) | Codex (Baseline → Skill Uplift) |
|---|---:|---:|
| Overall | 95.2% — uplift unavailable | 81.6% — uplift unavailable |
| Security | 100.0% → 100.0% (±0.0 points) | 50.0% → 50.0% (±0.0 points) |
| Correctness | 100.0% → 100.0% (±0.0 points) | 100.0% → 100.0% (±0.0 points) |
| Discoverability | 95.0% — uplift unavailable | 90.0% — uplift unavailable |
| Effectiveness | 95.0% → 100.0% (+5.0 points) | 85.0% → 93.8% (+8.8 points) |
| Efficiency | 80.8% — uplift unavailable | 74.1% — uplift unavailable |

## Skill Version(s): <br>
1.1.0 (source: pyproject.toml) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
