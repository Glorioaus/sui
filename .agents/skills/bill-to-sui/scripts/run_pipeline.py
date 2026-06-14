"""
run_pipeline.py —— bill-to-sui skill 的确定性流水线封装

封装 src/ 的两阶段流程（解析 → 合并），供 skill 调用。
不修改 src/ 任何代码，通过 sys.path 注入。

用法：
    python run_pipeline.py <输入文件或目录> <输出目录> [--emit-json] [--no-merge]

输出：
    - 默认：执行完整两阶段，生成 output/merged_账单.xlsx
    --emit-json：额外生成 transactions.json（含 needs_enrichment 标记，供 LLM 增强层消费）
    --no-merge：只执行第一阶段（解析，每家独立输出），不合并
"""
import argparse
import json
import os
import sys
import shutil
from datetime import datetime

# 定位项目根目录的 src/
# 本脚本位于 .agents/skills/bill-to-sui/scripts/run_pipeline.py
# 项目根是向上一级再向上一级再向上一级的父目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


def run_parse_stage(input_path: str, output_dir: str) -> tuple[int, list[str]]:
    """
    第一阶段：解析。
    调用 src/main.py 的 SuiConverter 处理输入，生成每家独立的 _随手记.xlsx。

    返回：(处理文件数, 生成的 xlsx 文件名列表)
    """
    from main import SuiConverter

    converter = SuiConverter()
    generated_files = []

    if os.path.isfile(input_path):
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_filename = f"{base_name}_随手记.xlsx"
        output_path = os.path.join(output_dir, output_filename)
        if converter.process_file(input_path, output_path):
            generated_files.append(output_filename)
        count = 1
    else:
        # 目录批量 —— 复用 SuiConverter.process_directory 但收集文件名
        if not os.path.exists(input_path):
            print(f"错误: 输入路径不存在 {input_path}")
            return 0, []

        os.makedirs(output_dir, exist_ok=True)
        count = 0
        for filename in os.listdir(input_path):
            file_path = os.path.join(input_path, filename)
            if not os.path.isfile(file_path):
                continue
            if filename.startswith('.') or filename.startswith('~'):
                continue
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}_随手记.xlsx"
            output_path = os.path.join(output_dir, output_filename)
            if converter.process_file(file_path, output_path):
                generated_files.append(output_filename)
                count += 1

    return count, generated_files


def run_merge_stage(output_dir: str, merged_filename: str = "merged_账单.xlsx") -> str | None:
    """
    第二阶段：合并。
    调用 src/merge.py 的 merge_excel_files，生成合并后的 xlsx。

    返回：合并文件路径，失败返回 None
    """
    from merge import merge_excel_files

    merged_path = os.path.join(output_dir, merged_filename)
    merge_excel_files(output_dir, merged_path)

    return merged_path if os.path.exists(merged_path) else None


def mark_needs_enrichment(tx: dict) -> bool:
    """
    判断交易是否需要 LLM 兜底增强。
    返回 True 的条件：
    1. 落到默认兜底分类（其他杂项/其他支出 或 其他收入/意外来钱）
    2. 转账目标为通用"信用卡"（merge.py 第二轮匹配失败）
    """
    # 默认兜底分类
    if tx.get("category") in ("其他杂项",) and tx.get("subcategory") in ("其他支出",):
        return True
    if tx.get("category") == "其他收入" and tx.get("subcategory") == "意外来钱":
        return True
    # 转账目标未匹配
    if tx.get("transaction_type") == "转账" and tx.get("transfer_to_account") == "信用卡":
        return True
    return False


def emit_transactions_json(merged_path: str, source_files: list[str], output_dir: str) -> str:
    """
    从合并后的 xlsx 读取交易，标记 needs_enrichment，输出 transactions.json。

    返回：json 文件路径
    """
    from merge import read_excel_transactions

    transactions = read_excel_transactions(merged_path)

    tx_list = []
    needs_enrichment_count = 0
    for t in transactions:
        d = t.to_dict()
        d["needs_enrichment"] = mark_needs_enrichment(d)
        if d["needs_enrichment"]:
            needs_enrichment_count += 1
        tx_list.append(d)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_files": source_files,
        "merged_file": os.path.basename(merged_path),
        "stats": {
            "final_count": len(tx_list),
            "needs_enrichment": needs_enrichment_count,
        },
        "transactions": tx_list,
    }

    json_path = os.path.join(output_dir, "transactions.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n中间 JSON 已生成：{json_path}")
    print(f"  总交易: {len(tx_list)} 条")
    print(f"  待增强: {needs_enrichment_count} 条")

    return json_path


def main():
    parser = argparse.ArgumentParser(
        description="bill-to-sui 流水线：解析 → 合并 → （可选）输出中间 JSON"
    )
    parser.add_argument("input", help="输入文件或目录")
    parser.add_argument("output_dir", help="输出目录")
    parser.add_argument("--emit-json", action="store_true",
                        help="额外生成 transactions.json，供 LLM 增强层消费")
    parser.add_argument("--no-merge", action="store_true",
                        help="只解析不合并（第一阶段）")
    parser.add_argument("--merged-name", default="merged_账单.xlsx",
                        help="合并文件名（默认 merged_账单.xlsx）")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # 阶段 1：解析
    print("=" * 60)
    print("阶段 1：解析账单")
    print("=" * 60)
    count, generated = run_parse_stage(args.input, args.output_dir)
    print(f"\n解析完成：成功处理 {count} 个文件")

    if count == 0:
        print("无成功解析的文件，流程终止")
        return 1

    # 阶段 2：合并
    merged_path = None
    if not args.no_merge and count > 0:
        print("\n" + "=" * 60)
        print("阶段 2：合并处理")
        print("=" * 60)
        merged_path = run_merge_stage(args.output_dir, args.merged_name)

    # 可选：输出中间 JSON
    if args.emit_json and merged_path:
        print("\n" + "=" * 60)
        print("生成中间 JSON")
        print("=" * 60)
        emit_transactions_json(merged_path, generated, args.output_dir)

    print("\n" + "=" * 60)
    print("流水线完成")
    print("=" * 60)
    print(f"  输出目录: {args.output_dir}")
    if merged_path:
        print(f"  合并文件: {merged_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
