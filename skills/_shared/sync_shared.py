#!/usr/bin/env python3
"""Keep each complexa skill's owned copies of shared assets in sync with _shared/.

`_shared/` is the single edit point for assets used by more than one skill
(`scripts/`, hardware guidance, and shared scientific guides). Each asset has an
explicit owner set below so it is copied only into skills that need it. These
owned assets cannot be replaced by symlinks or cross-skill references: the
NVIDIA/skills catalog sparse-checks-out each skill directory on its own and
copies it with `rsync -a`, and `codex plugin add` drops symlinks on install.
Because the scientific guides cross-link one another, every skill that owns one
guide owns the complete guide set and remains self-contained.

Authors edit the canonical copy under `_shared/` and run `--write`; CI runs
`--check` to fail a PR whose owned copies drifted, whose non-owners contain an
unexpected managed copy, or whose repository-facing `docs/` alias is not the
expected symlink.

Usage:
  python3 skills/_shared/sync_shared.py --write   # refresh per-skill copies
  python3 skills/_shared/sync_shared.py --check   # verify (exit 1 on drift)
"""
from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parent.parent  # skills/
SHARED = SKILLS_ROOT / "_shared"
REPO_ROOT = SKILLS_ROOT.parent
DOCS_ROOT = REPO_ROOT / "docs"

GUIDE_OWNERS = frozenset(
    {
        "complexa-design",
        "complexa-evaluate-pdbs",
        "complexa-sweep",
    }
)

# Canonical assets and the only skills that should receive a real copy. Keep
# this map explicit: inferring ownership from prose references makes it too easy
# for a generic documentation link to copy a large guide into every skill.
SHARED_ASSET_OWNERS: dict[str, frozenset[str]] = {
    "scripts/preflight.sh": frozenset(
        {
            "complexa-design",
            "complexa-evaluate-pdbs",
            "complexa-setup",
            "complexa-sweep",
        }
    ),
    "scripts/write_manifest.py": frozenset(
        {
            "complexa-design",
            "complexa-evaluate-pdbs",
            "complexa-setup",
            "complexa-sweep",
        }
    ),
    "references/hardware.md": frozenset(
        {
            "complexa-design",
            "complexa-evaluate-pdbs",
            "complexa-setup",
            "complexa-sweep",
            "complexa-target",
        }
    ),
    "references/INFERENCE.md": GUIDE_OWNERS,
    "references/CONFIGURATION_GUIDE.md": GUIDE_OWNERS,
    "references/EVALUATION_METRICS.md": GUIDE_OWNERS,
    "references/SEARCH_METADATA.md": GUIDE_OWNERS,
    "references/SWEEP.md": GUIDE_OWNERS,
}

# Canonical shared guides must link to one another by sibling filename. Their
# ownership closure guarantees those same links work in every distributed copy.
SHARED_GUIDES = frozenset(
    {
        "references/INFERENCE.md",
        "references/CONFIGURATION_GUIDE.md",
        "references/EVALUATION_METRICS.md",
        "references/SEARCH_METADATA.md",
        "references/SWEEP.md",
    }
)

MARKDOWN_LINK_TARGET_RE = re.compile(r"]\(([^)\s]+)")

# Repository users retain the traditional docs/ paths, while the canonical
# files live under skills/ so the BAT source sync includes them.
DOC_GUIDE_ALIASES: dict[str, str] = {
    "INFERENCE.md": "../skills/_shared/references/INFERENCE.md",
    "CONFIGURATION_GUIDE.md": "../skills/_shared/references/CONFIGURATION_GUIDE.md",
    "EVALUATION_METRICS.md": "../skills/_shared/references/EVALUATION_METRICS.md",
    "SEARCH_METADATA.md": "../skills/_shared/references/SEARCH_METADATA.md",
    "SWEEP.md": "../skills/_shared/references/SWEEP.md",
}


def complexa_skills() -> list[Path]:
    return sorted(
        p for p in SKILLS_ROOT.glob("complexa-*")
        if p.is_dir() and (p / "SKILL.md").is_file()
    )


def ownership_problems(skills: list[Path]) -> list[str]:
    """Return invalid canonical paths or owner names in the explicit map."""
    problems: list[str] = []
    known_skills = {skill.name for skill in skills}
    for rel, owners in SHARED_ASSET_OWNERS.items():
        if not (SHARED / rel).is_file():
            problems.append(f"_shared: missing canonical asset {rel}")
        for owner in sorted(owners - known_skills):
            problems.append(f"ownership map: unknown skill {owner!r} for {rel}")

    guide_by_name = {Path(rel).name: rel for rel in SHARED_GUIDES}
    for rel in SHARED_GUIDES:
        source = SHARED / rel
        if not source.is_file():
            continue
        for target in MARKDOWN_LINK_TARGET_RE.findall(
            source.read_text(encoding="utf-8")
        ):
            path = target.split("#", 1)[0]
            target_rel = guide_by_name.get(Path(path).name)
            if target_rel is None:
                continue
            if path != Path(path).name:
                problems.append(
                    f"_shared/{rel}: shared-guide link {target!r} must use its "
                    "sibling filename"
                )
            missing_owners = (
                SHARED_ASSET_OWNERS[rel] - SHARED_ASSET_OWNERS[target_rel]
            )
            for owner in sorted(missing_owners):
                problems.append(
                    f"ownership map: {owner!r} receives {rel}, which links to "
                    f"unowned {target_rel}"
                )
    return problems


def sync_doc_aliases() -> int:
    """Create the repository-facing docs/ symlinks to canonical skill guides."""
    count = 0
    for name, target in DOC_GUIDE_ALIASES.items():
        alias = DOCS_ROOT / name
        if alias.is_symlink() and str(alias.readlink()) == target:
            continue
        if alias.exists() or alias.is_symlink():
            alias.unlink()
        alias.symlink_to(target)
        count += 1
    return count


def doc_alias_problems() -> list[str]:
    """Return missing, non-symlink, or incorrectly targeted docs aliases."""
    problems: list[str] = []
    for name, target in DOC_GUIDE_ALIASES.items():
        alias = DOCS_ROOT / name
        if not alias.is_symlink():
            problems.append(f"docs/{name}: expected symlink to {target}")
        elif str(alias.readlink()) != target:
            problems.append(
                f"docs/{name}: points to {alias.readlink()}, expected {target}"
            )
        elif not alias.is_file():
            problems.append(f"docs/{name}: symlink target does not exist")
    return problems


def do_write() -> int:
    skills = complexa_skills()
    problems = ownership_problems(skills)
    if problems:
        print("shared-sync configuration FAILED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    count = 0
    removed = 0
    for skill in skills:
        for rel, owners in SHARED_ASSET_OWNERS.items():
            dst = skill / rel
            if skill.name in owners:
                dst.parent.mkdir(parents=True, exist_ok=True)
                # copy2 preserves mode, e.g. +x on preflight.sh.
                shutil.copy2(SHARED / rel, dst)
                count += 1
            elif dst.exists() or dst.is_symlink():
                dst.unlink()
                removed += 1

    aliases = sync_doc_aliases()
    print(
        f"synced {count} owned shared file(s), removed {removed} unowned "
        f"copy/copies, refreshed {aliases} docs alias(es) across "
        f"{len(skills)} complexa skill(s)"
    )
    return 0


def do_check() -> int:
    skills = complexa_skills()
    problems = ownership_problems(skills)
    problems.extend(doc_alias_problems())
    for skill in skills:
        for rel, owners in SHARED_ASSET_OWNERS.items():
            dst = skill / rel
            if skill.name in owners:
                if dst.is_symlink() or not dst.is_file():
                    problems.append(
                        f"{skill.name}: missing real copy of {rel} (run --write)"
                    )
                elif not filecmp.cmp(SHARED / rel, dst, shallow=False):
                    problems.append(
                        f"{skill.name}: {rel} differs from _shared/{rel} "
                        f"(run --write)"
                    )
            elif dst.exists() or dst.is_symlink():
                problems.append(
                    f"{skill.name}: unexpected unowned copy of {rel} (run --write)"
                )
    if problems:
        print("shared-sync check FAILED:")
        for p in problems:
            print(f"  - {p}")
        print("\nFix: python3 skills/_shared/sync_shared.py --write  (and commit)")
        return 1
    print("shared-sync OK — ownership, real copies, and docs aliases match _shared/")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--write", action="store_true", help="refresh per-skill copies from _shared/"
    )
    g.add_argument(
        "--check",
        action="store_true",
        help="verify copies match _shared/ (exit 1 on drift)",
    )
    args = ap.parse_args()
    return do_write() if args.write else do_check()


if __name__ == "__main__":
    sys.exit(main())
