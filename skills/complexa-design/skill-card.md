## Description: <br>
Agent runbook for orchestrating an end-to-end protein, ligand-binder, or AME design through the separately installed first-party Proteina-Complexa CLI. <br>

This skill is for research and development only. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
Apache 2.0 <br>
## Use Case: <br>
Developers and computational biologists use this skill to orchestrate end-to-end protein, ligand-binder, or AME design campaigns through the first-party Proteina-Complexa CLI: selecting the matching pipeline config, validating run readiness, executing the four-stage generate/filter/evaluate/analyze pipeline, and reporting design success rate and diversity. <br>

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
- [Search and Campaign Analysis](references/search_and_analysis.md) <br>
- [Evaluation & Analysis Guide](references/EVALUATION_METRICS.md) <br>
- [Overrides Reference](references/overrides.md) <br>
- [Hardware Reference](references/hardware.md) <br>
- [Troubleshooting Reference](references/troubleshooting.md) <br>


## Skill Output: <br>
**Output Type(s):** [Shell commands, Configuration instructions, Analysis, Files] <br>
**Output Format:** [Markdown with inline bash code blocks, plus a JSON run manifest and summaries of result CSVs] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [None] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-5-5`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
9 evaluation tasks (8 positive, 1 negative), each attempt run in its own isolated sandbox pod (k8s-sandbox), 1 attempt per task; overall verdict NEUTRAL. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Whether the skill is safe to use — unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Whether the final answer is correct against the reference answer. <br>
- Discoverability: Whether the right skill was loaded and activated when needed. <br>
- Effectiveness: Whether the skill helped complete the user's goal and expected workflow (goal accuracy plus behavior check). <br>
- Efficiency: Whether the skill avoided wasted tool calls and token usage (tool productivity plus token efficiency). <br>

Underlying evaluation signals used in this run: <br>
- `security`: Unsafe operations, secret leakage, and unauthorized access. <br>
- `skill_execution`: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- `skill_efficiency`: Tool-call productivity. <br>
- `accuracy`: Final-answer correctness against the reference answer. <br>
- `goal_accuracy`: Whether the user's goal was achieved. <br>
- `behavior_check`: Whether the expected workflow behavior was followed. <br>
- `token_efficiency`: Actual uncached prompt plus completion token usage. <br>



## Evaluation Results: <br>
| Dimension | Claude Code (Baseline → Skill Uplift) | Codex (Baseline → Skill Uplift) |
|---|---|---|
| Overall | Not available | 55.0% (baseline ran; uplift unavailable) |
| Security | Not available | 100.0% → 100.0% (±0.0 points) |
| Correctness | Not available | 11.1% → 11.1% (±0.0 points) |
| Discoverability | Not available | 77.5% (baseline ran; uplift unavailable) |
| Effectiveness | Not available | 11.1% → 11.1% (±0.0 points) |
| Efficiency | Not available | 75.3% (baseline ran; uplift unavailable) |

## Skill Version(s): <br>
1.1.0 (source: pyproject.toml) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
