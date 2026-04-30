#!/usr/bin/env python3
"""Run the Sui bill conversion workflow without duplicating parser logic."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


CONFIG_FILES = (
    "category_mapping.json",
    "category_mapping_income.json",
    "accounts.json",
)


def in_virtual_environment() -> bool:
    return bool(getattr(sys, "real_prefix", None)) or sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def find_repo_root(explicit: str | None = None) -> Path:
    if explicit:
        root = Path(explicit).resolve()
        if is_repo_root(root):
            return root
        raise SystemExit(f"Not a Sui converter repository root: {root}")

    candidates = [Path.cwd().resolve(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if is_repo_root(candidate):
            return candidate
    raise SystemExit("Could not locate repository root containing src/main.py, src/merge.py, and requirements.txt")


def is_repo_root(path: Path) -> bool:
    return (
        (path / "src" / "main.py").is_file()
        and (path / "src" / "merge.py").is_file()
        and (path / "requirements.txt").is_file()
    )


def validate_config(repo_root: Path) -> None:
    for filename in CONFIG_FILES:
        path = repo_root / "config" / filename
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)
        print(f"OK config/{filename}")


def run_command(command: list[str], repo_root: Path, allow_global_python: bool) -> int:
    print("+ " + " ".join(command))
    stdin = "y\n" if allow_global_python and command[1].endswith("main.py") else None
    completed = subprocess.run(command, cwd=repo_root, text=True, input=stdin)
    return completed.returncode


def install_dependencies(repo_root: Path) -> int:
    command = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    print("+ " + " ".join(command))
    return subprocess.run(command, cwd=repo_root).returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Sui bill conversion and optional merge.")
    parser.add_argument("--input", default="input", help="Input statement file or directory. Default: input")
    parser.add_argument("--output", default="output", help="Output directory. Default: output")
    parser.add_argument("--merged-name", default=None, help="Optional merged workbook filename for src/merge.py")
    parser.add_argument("--repo-root", default=None, help="Repository root. Auto-detected by default.")
    parser.add_argument("--skip-merge", action="store_true", help="Only run src/main.py, skip src/merge.py.")
    parser.add_argument("--skip-config-check", action="store_true", help="Skip JSON config validation.")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies before conversion.")
    parser.add_argument(
        "--allow-global-python",
        action="store_true",
        help="Allow running outside a virtual environment. This answers src/main.py's prompt with yes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(args.repo_root)

    if not in_virtual_environment() and not args.allow_global_python:
        print("Refusing to run outside a virtual environment.")
        print("Activate .venv first, or pass --allow-global-python if you intentionally want global Python.")
        return 2

    if args.install_deps:
        result = install_dependencies(repo_root)
        if result != 0:
            return result

    if not args.skip_config_check:
        validate_config(repo_root)

    input_path = str(Path(args.input))
    output_path = str(Path(args.output))
    result = run_command([sys.executable, "src/main.py", input_path, output_path], repo_root, args.allow_global_python)
    if result != 0 or args.skip_merge:
        return result

    merge_command = [sys.executable, "src/merge.py", output_path]
    if args.merged_name:
        merge_command.append(args.merged_name)
    return run_command(merge_command, repo_root, args.allow_global_python)


if __name__ == "__main__":
    raise SystemExit(main())
