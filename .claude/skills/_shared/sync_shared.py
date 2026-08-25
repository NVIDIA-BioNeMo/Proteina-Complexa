#!/usr/bin/env python3
"""Keep each complexa skill's hard copies of shared assets in sync with _shared/.

`_shared/` is the single edit point for assets used by more than one skill
(`scripts/preflight.sh`, `scripts/write_manifest.py`, `references/hardware.md`).
They cannot be symlinks or cross-skill references: the NVIDIA/skills catalog
sparse-checks-out each skill directory on its own and copies it with `rsync -a`,
and `codex plugin add` drops symlinks on install — so every skill must ship the
assets it uses as REAL files inside its own folder.

Authors edit the canonical copy under `_shared/` and run `--write`; CI runs
`--check` to fail a PR whose per-skill copies drifted from `_shared/`.

Usage:
  python3 .claude/skills/_shared/sync_shared.py --write   # refresh per-skill copies
  python3 .claude/skills/_shared/sync_shared.py --check   # verify (exit 1 on drift)
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parent.parent  # .claude/skills/
SHARED = SKILLS_ROOT / "_shared"

# Canonical shared assets, addressed by the skill-relative path a skill uses.
SHARED_FILES = [
    "scripts/preflight.sh",
    "scripts/write_manifest.py",
    "references/hardware.md",
]

# Files that may declare a dependency on a shared asset. The copied assets under
# scripts/ are excluded so a copy can never make a skill look like it "uses" more
# than it authored.
_DOC_SUFFIXES = {".md", ".json", ".txt", ".yaml", ".yml"}


def complexa_skills() -> list[Path]:
    return sorted(
        p for p in SKILLS_ROOT.glob("complexa-*")
        if p.is_dir() and (p / "SKILL.md").is_file()
    )


def skill_references(skill: Path, rel: str) -> bool:
    """True if the skill's authored docs mention the skill-relative path `rel`."""
    for f in skill.rglob("*"):
        if not f.is_file() or f.suffix not in _DOC_SUFFIXES:
            continue
        if "scripts" in f.relative_to(skill).parts:  # don't scan copied assets
            continue
        try:
            if rel in f.read_text(encoding="utf-8"):
                return True
        except (UnicodeDecodeError, OSError):
            continue
    return False


def needed(skill: Path):
    """Yield (rel, source_path) for each shared asset this skill references."""
    for rel in SHARED_FILES:
        src = SHARED / rel
        if src.is_file() and skill_references(skill, rel):
            yield rel, src


def do_write() -> int:
    skills = complexa_skills()
    count = 0
    for skill in skills:
        for rel, src in needed(skill):
            dst = skill / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)  # copy2 preserves mode (e.g. +x on preflight.sh)
            count += 1
    print(f"synced {count} shared file(s) across {len(skills)} complexa skill(s)")
    return 0


def do_check() -> int:
    problems: list[str] = []
    for skill in complexa_skills():
        for rel, src in needed(skill):
            dst = skill / rel
            if not dst.is_file():
                problems.append(f"{skill.name}: missing {rel} (run --write)")
            elif not filecmp.cmp(src, dst, shallow=False):
                problems.append(f"{skill.name}: {rel} differs from _shared/{rel} (run --write)")
    if problems:
        print("shared-sync check FAILED:")
        for p in problems:
            print(f"  - {p}")
        print("\nFix: python3 .claude/skills/_shared/sync_shared.py --write  (and commit)")
        return 1
    print("shared-sync OK — every per-skill copy matches _shared/")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="refresh per-skill copies from _shared/")
    g.add_argument("--check", action="store_true", help="verify copies match _shared/ (exit 1 on drift)")
    args = ap.parse_args()
    return do_write() if args.write else do_check()


if __name__ == "__main__":
    sys.exit(main())
