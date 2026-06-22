#!/usr/bin/env python3
"""随手记账单转换工作流入口（自适应单入口）。

寻根顺序：
1. 优先用 skill 包内 engine/（自包含模式，可脱离宿主仓库独立运行）。
2. 包内缺失时回退宿主仓库 src/（宿主仓库内开发模式）。

两条路径产出同一份 merged_账单.xlsx。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILES = (
    "category_mapping.json",
    "category_mapping_income.json",
    "accounts.json",
)


def in_virtual_environment() -> bool:
    return bool(getattr(sys, "real_prefix", None)) or sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def find_repo_root(explicit: str | None = None) -> Path | None:
    """查找宿主仓库根目录（含 src/main.py、src/merge.py）。找不到返回 None。"""
    if explicit:
        root = Path(explicit).resolve()
        if is_repo_root(root):
            return root
        raise SystemExit(f"Not a Sui converter repository root: {root}")
    candidates = [Path.cwd().resolve(), *SKILL_DIR.parents]
    for candidate in candidates:
        if is_repo_root(candidate):
            return candidate
    return None


def is_repo_root(path: Path) -> bool:
    return (path / "src" / "main.py").is_file() and (path / "src" / "merge.py").is_file()


def resolve_engine(explicit_repo_root: str | None = None) -> tuple[Path, Path, str]:
    """返回 (engine_dir, config_dir, source_label)。

    优先包内 engine/，回退宿主 src/。
    """
    bundled_engine = SKILL_DIR / "engine" / "main.py"
    bundled_config = SKILL_DIR / "config"
    if bundled_engine.is_file():
        return SKILL_DIR / "engine", bundled_config, "包内 engine/（自包含）"

    repo_root = find_repo_root(explicit_repo_root)
    if repo_root is None:
        raise SystemExit(
            "找不到转换引擎：skill 包内没有 engine/main.py，也无法定位宿主仓库（含 src/main.py）。\n"
            "若在宿主仓库内运行，请确认工作目录；若在独立环境运行，请先运行 sync_engine.py 建立包内引擎。"
        )
    return repo_root / "src", repo_root / "config", f"宿主 {repo_root}/src/"


def validate_config(config_dir: Path) -> None:
    for filename in CONFIG_FILES:
        path = config_dir / filename
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)
        print(f"OK {path}")


def load_engine(engine_dir: Path):
    """把引擎目录注入 sys.path 并返回 (SuiConverter, merge_excel_files)。"""
    engine_path = str(engine_dir)
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    from main import SuiConverter  # type: ignore
    from merge import merge_excel_files  # type: ignore
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
    parser = argparse.ArgumentParser(description="Run Sui bill conversion (adaptive: bundled engine first, repo fallback).")
    parser.add_argument("--input", default="input", help="Input statement file or directory. Default: input")
    parser.add_argument("--output", default="output", help="Output directory. Default: output")
    parser.add_argument("--merged-name", default="merged_账单.xlsx", help="Merged workbook filename. Default: merged_账单.xlsx")
    parser.add_argument("--repo-root", default=None, help="Repository root (fallback only). Auto-detected by default.")
    parser.add_argument("--skip-merge", action="store_true", help="Only run parsing, skip merge.")
    parser.add_argument("--skip-config-check", action="store_true", help="Skip JSON config validation.")
    parser.add_argument("--prefer-repo", action="store_true", help="强制用宿主仓库引擎，忽略包内 engine/。")
    parser.add_argument(
        "--allow-global-python",
        action="store_true",
        help="Allow running outside a virtual environment.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not in_virtual_environment() and not args.allow_global_python:
        print("Refusing to run outside a virtual environment.")
        print("Activate .venv first, or pass --allow-global-python.")
        return 2

    if args.prefer_repo:
        repo_root = find_repo_root(args.repo_root)
        if repo_root is None:
            raise SystemExit("--prefer-repo 指定，但找不到宿主仓库。")
        engine_dir = repo_root / "src"
        config_dir = repo_root / "config"
        source_label = f"宿主 {repo_root}/src/（强制）"
    else:
        engine_dir, config_dir, source_label = resolve_engine(args.repo_root)

    print(f"引擎来源：{source_label}")

    if not args.skip_config_check:
        validate_config(config_dir)

    SuiConverter, merge_excel_files = load_engine(engine_dir)

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
