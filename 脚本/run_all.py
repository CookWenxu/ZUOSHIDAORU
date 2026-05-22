"""
一键运行脚本
1. 清洗测试输入
2. 使用 DeepSeek-V4-Flash 进行测试
3. 导出 CSV 格式
4. 转换为 Excel 格式
"""

import subprocess
import sys
import os
import csv
import re

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
python_exe = sys.executable

print("="*80)
print("债券交易记录生成 - 一键测试")
print("="*80)
print()

# ===================== 步骤 1: 清洗输入 =====================
print("步骤 1/3: 清洗测试输入...")
print("-"*80)
result = subprocess.run([python_exe, os.path.join(script_dir, "clean_test_input.py")])
if result.returncode != 0:
    print("\n[Error] 清洗输入失败！")
    sys.exit(1)
print()

# ===================== 步骤 2: 运行测试 =====================
print("步骤 2/3: 运行 DeepSeek-V4-Flash 测试...")
print("-"*80)
result = subprocess.run([python_exe, os.path.join(script_dir, "test_deepseek_v4.py")])
if result.returncode != 0:
    print("\n[Error] 测试失败！")
    sys.exit(1)

# 读取并显示 Token 统计信息
import json
stats_file = os.path.join(script_dir, "..", "输出样本", "token_stats.json")
if os.path.exists(stats_file):
    with open(stats_file, "r", encoding="utf-8") as f:
        token_stats = json.load(f)
    
    print()
    print("="*80)
    print("本次 API Token 用量统计")
    print("="*80)
    print(f"  请求次数：{token_stats.get('request_count', 0)}")
    print(f"  总 Token 数：{token_stats.get('total_tokens', 0):,}")
    print(f"  提示 Token：{token_stats.get('prompt_tokens', 0):,}")
    print(f"  完成 Token：{token_stats.get('completion_tokens', 0):,}")
    print()
    print("费用估算（人民币）：")
    print(f"  提示费用：￥{token_stats.get('input_cost', 0):.4f}")
    print(f"  完成费用：￥{token_stats.get('output_cost', 0):.4f}")
    print(f"  总费用：￥{token_stats.get('total_cost', 0):.4f}")
    print("="*80)
print()

# ===================== 步骤 3: 导出 CSV =====================
print("步骤 3/4: 导出 CSV 格式...")
print("-"*80)

# CSV 配置
input_file = "输出样本/测试结果_deepseek_v4.txt"
output_csv = "输出样本/测试结果_deepseek_v4.csv"

# 解析测试结果
with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

# 分割每个测试用例
test_cases = re.split(r'={80,}', content)

records = []

for case in test_cases:
    case = case.strip()
    if not case:
        continue
    
    # 提取输入
    input_match = re.search(r'输入 \d+:\n(.*?)(?=输出:|$)', case, re.DOTALL)
    if not input_match:
        continue
    input_text = input_match.group(1).strip()
    
    # 提取输出
    output_match = re.search(r'输出:\n(.*?)$', case, re.DOTALL)
    if not output_match:
        continue
    output_text = output_match.group(1).strip()
    
    # 解析输出中的交易记录
    lines = output_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line or line == '交易记录:':
            continue
        
        # 解析交易记录行（用 | 分隔）
        parts = [p.strip() for p in line.split('|') if p.strip()]
        
        if len(parts) >= 7:
            record = {
                '输入': input_text,
                '交易方向': parts[0],
                '结算速度': parts[1],
                '对手方': parts[2],
                '交易日': parts[3],
                '债券代码': parts[4],
                '金额 (万)': parts[5],
                '收益率 (%)': parts[6],
                '备注': parts[7] if len(parts) > 7 else ''
            }
            records.append(record)

# 写入 CSV
if records:
    # 定义 CSV 列头
    fieldnames = ['输入', '交易方向', '结算速度', '对手方', '交易日', '债券代码', '金额 (万)', '收益率 (%)', '备注']
    
    # 写入 CSV
    with open(output_csv, "w", encoding="utf-8-sig", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"[OK] 已写入 {len(records)} 条记录")
    print(f"CSV 文件已保存至：{output_csv}")
else:
    print("[Warning] 未解析到任何记录！")

print()

# ===================== 步骤 4: 转换为 Excel =====================
print("步骤 4/4: 转换为 Excel 格式...")
print("-"*80)

output_excel = "输出样本/测试结果_deepseek_v4.xlsx"

try:
    import pandas as pd
    
    # 读取 CSV 文件
    df = pd.read_csv(output_csv, encoding='utf-8-sig')
    
    # 创建 Excel Writer 对象
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        # 写入数据
        df.to_excel(writer, index=False, sheet_name='测试结果')
        
        # 自动调整列宽
        worksheet = writer.sheets['测试结果']
        for i, col in enumerate(df.columns):
            # 计算列宽（基于列名和数据的最大长度）
            max_length = max(
                len(str(col)),
                df[col].astype(str).map(len).max() if len(df) > 0 else 0
            )
            # 设置列宽（最大 50，最小 10）
            adjusted_width = min(max(max_length + 2, 10), 50)
            worksheet.column_dimensions[chr(65 + i)].width = adjusted_width
    
    print(f"[OK] 已保存 {len(df)} 行数据到 Excel")
    print(f"Excel 文件已保存至：{output_excel}")
except ImportError:
    print("[Warning] 未安装 pandas 或 openpyxl，跳过 Excel 转换")
    print("  如需安装，请运行：pip install pandas openpyxl")
except Exception as e:
    print(f"[Error] Excel 转换失败：{e}")

print()

# ===================== 完成 =====================
print()
print("="*80)
print("[OK] 全部完成！")
print("="*80)
print()
print("结果文件：")
print("  - 清洗后的输入：输出样本/测试输入_cleaned.txt")
print("  - 测试结果：输出样本/测试结果_deepseek_v4.txt")
print("  - CSV 分列文件：输出样本/测试结果_deepseek_v4.csv")
print("  - Excel 文件：输出样本/测试结果_deepseek_v4.xlsx")
print()
