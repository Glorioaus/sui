#!/usr/bin/env python3
"""Run the Sui bill conversion workflow without duplicating parser logic.

直接 import 仓库 src/ 的 SuiConverter / merge_excel_files（通过 sys.path 注入），
不复制解析逻辑，也不通过外部命令转调 src/main.py。
"""

from __future__ import annotations

import argparse
import json
import os
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


def load_engine(repo_root: Path):
    """把仓库 src/ 注入 sys.path 并返回 (SuiConverter, merge_excel_files)。"""
    src_dir = str(repo_root / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from main import SuiConverter  # 动态导入，避免复制解析逻辑
    from merge import merge_excel_files
    return SuiConverter, merge_excel_files


def run_parse(converter, input_path: str, output_dir: str) -> bool:
    """阶段 1：解析。单文件用 process_file，目录用 process_directory。"""
    if os.path.isfile(input_path):
        base = os.path.splitext(os.path.basename(input_path))[0]
        out = os.path.join(output_dir, f"{base}_随手记.xlsx")
        return bool(converter.process_file(input_path, out))
    if not os.path.isdir(input_path):
        print(f"错误：输入路径不存在 {input_path}")
        return False
    converter.process_directory(input_path, output_dir)
    return any(name.endswith("_随手记.xlsx") for name in os.listdir(output_dir))


def run_merge(merge_excel_files, output_dir: str, merged_name: str) -> int:
    """阶段 2：合并。返回 0 成功，非 0 失败。"""
    merged_path = os.path.join(output_dir, merged_name)
    try:
        merge_excel_files(output_dir, merged_path)
    except Exception as exc:  # noqa: BLE001
        print(f"合并失败：{exc}")
        return 1
    return 0 if os.path.exists(merged_path) else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Sui bill conversion and optional merge (direct import).")
    parser.add_argument("--input", default="input", help="Input statement file or directory. Default: input")
    parser.add_argument("--output", default="output", help="Output directory. Default: output")
    parser.add_argument("--merged-name", default="merged_账单.xlsx", help="Merged workbook filename. Default: merged_账单.xlsx")
    parser.add_argument("--repo-root", default=None, help="Repository root. Auto-detected by default.")
    parser.add_argument("--skip-merge", action="store_true", help="Only run parsing, skip merge.")
    parser.add_argument("--skip-config-check", action="store_true", help="Skip JSON config validation.")
    parser.add_argument(
        "--allow-global-python",
        action="store_true",
        help="Allow running outside a virtual environment.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(args.repo_root)

    if not in_virtual_environment() and not args.allow_global_python:
        print("Refusing to run outside a virtual environment.")
        print("Activate .venv first, or pass --allow-global-python.")
        return 2

    if not args.skip_config_check:
        validate_config(repo_root)

    SuiConverter, merge_excel_files = load_engine(repo_root)

    input_path = str(Path(args.input).resolve())
    output_dir = str(Path(args.output).resolve())
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("阶段 1：解析")
    print("=" * 60)
    if not run_parse(SuiConverter(), input_path, output_dir):
        print("无成功解析的文件，流程终止")
        return 1

    if args.skip_merge:
        return 0

    print("\n" + "=" * 60)
    print("阶段 2：合并")
    print("=" * 60)
    return run_merge(merge_excel_files, output_dir, args.merged_name)


if __name__ == "__main__":
    raise SystemExit(main())
