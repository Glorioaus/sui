#!/usr/bin/env python3
"""同步宿主仓库的引擎/配置/模板到 skill 包内，保持自包含副本与权威源一致。

权威源：宿主仓库的 src/、config/。
副本目标：skill 包内的 engine/、config/。

注：templates/template.xls 不被代码使用，不打进 skill 包（平台禁止 .xls）。

用法：
    python .claude/skills/sui-bill-converter/scripts/sync_engine.py         # 同步
    python .claude/skills/sui-bill-converter/scripts/sync_engine.py --check  # 只检测漂移，不复制
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_DIR.parents[2]

# (宿主相对路径, 包内相对路径) 映射
SYNC_MAP: list[tuple[str, str]] = []


def _build_sync_map() -> list[tuple[str, str]]:
    mapping: list[tuple[str, str]] = []
    for src_file in sorted((REPO_ROOT / "src").rglob("*.py")):
        if "__pycache__" in src_file.parts:
            continue
        rel = src_file.relative_to(REPO_ROOT / "src")
        mapping.append((str(Path("src") / rel), str(Path("engine") / rel)))
    for cfg in ["config/accounts.json", "config/category_mapping.json", "config/category_mapping_income.json"]:
        mapping.append((cfg, cfg))
    return mapping


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def check() -> list[tuple[str, str, str]]:
    """返回漂移列表：每项 (宿主路径, 包内路径, 状态)。

    状态：missing（包内缺失）、changed（内容不一致）、ok（一致）。
    只返回非 ok 的项。
    """
    drift: list[tuple[str, str, str]] = []
    for src_rel, dst_rel in _build_sync_map():
        src = REPO_ROOT / src_rel
        dst = SKILL_DIR / dst_rel
        if not dst.exists():
            drift.append((src_rel, dst_rel, "missing"))
            continue
        if _hash(src) != _hash(dst):
            drift.append((src_rel, dst_rel, "changed"))
    return drift


def sync() -> tuple[int, int]:
    """复制宿主到包内。返回 (复制数, 跳过数)。"""
    copied = 0
    skipped = 0
    for src_rel, dst_rel in _build_sync_map():
        src = REPO_ROOT / src_rel
        dst = SKILL_DIR / dst_rel
        if dst.exists() and _hash(src) == _hash(dst):
            skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        copied += 1
        print(f"  同步 {src_rel} -> {dst_rel}")
    return copied, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="同步宿主引擎到 skill 包，或检测漂移。")
    parser.add_argument("--check", action="store_true", help="只检测漂移，不复制。有漂移时返回非零。")
    args = parser.parse_args()

    if args.check:
        drift = check()
        if drift:
            print("检测到引擎副本与宿主漂移：")
            for src_rel, dst_rel, status in drift:
                print(f"  [{status}] {src_rel} -> {dst_rel}")
            print()
            print("请先运行同步：")
            print("  python .claude/skills/sui-bill-converter/scripts/sync_engine.py")
            print("然后再提交。")
            return 1
        print("引擎副本与宿主一致，无漂移。")
        return 0

    print("开始同步宿主引擎到 skill 包...")
    copied, skipped = sync()
    print(f"完成：复制 {copied} 个文件，跳过 {skipped} 个已一致文件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
