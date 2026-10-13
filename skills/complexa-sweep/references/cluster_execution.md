# Cluster launch details

Use only for an explicitly requested SLURM launch with a prepared cluster and
authorized run budget. Local config reviews need no SSH, sync, or submission.

## Configure the connection

Copy the project's `slurm_utils/.user_info_example` to `.user_info` only if the
destination does not already exist. Restrict permissions with
`chmod u=rw,go= slurm_utils/.user_info`. The repository ignores this private file;
never commit it. It contains connection settings (user, host, remote root,
environment and executable paths), not passwords or API tokens. Use SSH keys
with an agent and preserve existing settings when making changes.

## Select the launcher and scope

Read the selected launcher's help in the prepared project. The local Docker
launcher is `slurm_utils/launch_protein_binder_search_from_local_docker.sh`;
the cluster Conda launcher is
`slurm_utils/launch_protein_binder_search_conda.sh`. These accept `--sweeper`
and `--override`; `complexa design` itself does not accept `--sweeper`.
Use the requested target, config, and run name explicitly. A targetless launcher
can cover all configured targets; do not broaden the requested target set.

For a sweep, first preview the grid with the project's config generator and
check the total sample/GPU budget. Then inspect the materialized configurations
before submission. Config generation alone does not validate scientific inputs
or model readiness. Track submitted jobs and stage failures through completion.

## Protect staged files and destinations

The local-to-remote flow generates configs in a unique temporary directory,
then stages them into `configs/inference_configs` and `configs/eval_configs`
under a lock before rsync. **Local data loss:** staging overwrites contents in
these generated directories and cleanup permanently removes the directories.
Keep hand-authored configs elsewhere
and preserve existing contents before launching. The lock only coordinates
launchers; it does not protect user files.

Rsync writes reviewed local code/configs to the remote run directory and the
launcher can download results locally. Both operations can overwrite files.
Inspect the actual destinations and exclusions; use dedicated run paths and
preview the rsync command with `--dry-run` when changing a destination. The
direct-on-cluster flow generates configs in place without this sync step.

Record the actual job IDs, config paths, remote run directory, downloaded result
paths, and failed stages. An accepted submission is not a completed campaign.
