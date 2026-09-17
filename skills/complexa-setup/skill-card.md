## Description: <br>
Agent runbook for first-time Proteina-Complexa setup, dotenv configuration, runtime activation, model-weight installation, GPU preflight, and environment validation. <br>

This skill is for research and development only. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
Multiple licenses (see LICENSE file) <br>
## Use Case: <br>
Developers and researchers setting up the Proteina-Complexa protein binder design environment, including dotenv configuration, runtime selection, model checkpoint installation, and GPU preflight validation. <br>

### Deployment Geography for Use: <br>
Global <br>

## Requirements / Dependencies: <br>
**Requires API Key or External Credential:** [Optional] <br>
**Credential Type(s):** [API key] <br>

Do not include secrets in prompts/logs/output; use least-privilege credentials; rotate keys as appropriate. <br>

## Known Risks and Mitigations: <br>
Risk: Review before execution as proposals could introduce incorrect or misleading guidance into skills. <br>
Mitigation: Review and scan skill before deployment. <br>

## Reference(s): <br>
- [downloads.md](references/downloads.md) <br>
- [env_keys.md](references/env_keys.md) <br>
- [hardware.md](references/hardware.md) <br>


## Skill Output: <br>
**Output Type(s):** [Shell commands, Configuration instructions, Files] <br>
**Output Format:** [Markdown with inline bash code blocks and JSON artifacts] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces preflight.json (host snapshot) and run_manifest.json (replay-friendly setup record)] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-4-8`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
Evaluated against 4 tasks (3 positive, 1 negative), each with 3 attempts per task in isolated k8s-sandbox pods. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Checks for unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Checks final-answer correctness against the reference answer. <br>
- Discoverability: Checks whether the expected skill was selected and the workflow executed. <br>
- Effectiveness: Checks whether the user's goal was achieved and the expected workflow behavior was followed (50% goal_accuracy + 50% behavior_check). <br>
- Efficiency: Checks tool-call productivity and token efficiency (50% skill_efficiency + 50% token_efficiency). <br>

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
| Overall | 80.2% | Not available |
| Security | 87.5% → 100.0% (+12.5 points) | Not available |
| Correctness | 27.5% → 75.0% (+47.5 points) | Not available |
| Discoverability | 96.7% | Not available |
| Effectiveness | 23.8% → 47.5% (+23.7 points) | Not available |
| Efficiency | 81.6% | Not available |

## Skill Version(s): <br>
1.1.0 (source: pyproject.toml) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
