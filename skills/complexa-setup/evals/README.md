# Setup evaluation scope

The default `evals.json` runs four self-contained offline tasks: initial UV
dotenv preparation, checkpoint inventory auditing, Docker dotenv preparation,
and an unrelated CSV analysis task. They require file operations and bounded
local probes, not a CUDA installation, Docker daemon, network access, or model
downloads. Each case declares its input files; the same inputs are staged at
`/workspace/input` in both the with-skill and baseline conditions.

The template and source excerpts in `files/project` come from the repository
revision recorded in `source_manifest.json`. Refresh the excerpts and their
hashes when the relevant source changes. The inventory, existing dotenv
overrides, and scores CSV are explicitly synthetic. No dummy model files or
mock CLI substitute for real installation or inference.

These tasks measure configuration, audit, and scope-selection behavior. A pass
does not establish that a runtime was installed, weights downloaded, Docker or
CUDA initialized, or GPU inference completed. Agents must distinguish their
actual file operations/checks from future commands and unverified prerequisites.

The previous default dataset is preserved byte-for-byte in
`full-installation.json`. To run those full installation requests, copy this
skill to an isolated evaluation directory and replace that copy's
`evals/evals.json` with `full-installation.json`. Provide a real checkout, the
CSV named by the analysis case, network access, installation credentials where
needed, suitable GPU/Docker resources, disk capacity, and a provisioning budget.
The default source resolver does not select this integration dataset.

Local fixture and CLI-contract checks (PyYAML is needed by the real CLI):

```bash
python -m unittest discover -s skills/complexa-setup/evals/tests -v
```

Changing the suite requires a fresh live evaluation and regeneration of
benchmark reports, skill cards, and signatures by CI. Existing generated
results describe the earlier suite and must not be presented as results for
these offline cases.

This change removes avoidable provisioning work from the default tasks. It
does not repair the SkillEvaluator 1.5.6 local fallback's `BASH_ENV` startup
failure or prevent remote sandbox connection failures. Those can occur before
skill instructions run; keep infrastructure errors visible rather than
treating them as scored attempts or a successful skill validation.
