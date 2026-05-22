"""
将 Data_Input_2.0.csv 转换为 train_data_processed_v3.json 格式
"""

import csv
import json
import re
from datetime import datetime, timedelta

INPUT_FILE = "输出样本/Data_Input_2.0.csv"
OUTPUT_FILE = "输出样本/train_data_processed_v4.json"

def parse_output_line(line):
    """
    解析输出行，使用空格分割
    格式：买入/卖出 对手方 日期 债券名称 (代码) 金额 收益率 备注
    例如：买入 浙商证券股份有限公司 46125 25 超长特别国债 02(2500002) 2000 2.275 上家...
    """
    try:
        line = line.strip()
        if not line:
            return None
        
        # 使用空格分割
        parts = line.split()
        
        if len(parts) < 7:
            return None
        
        direction = parts[0]  # 买入/卖出
        
        if direction not in ['买入', '卖出']:
            return None
        
        counterparty = parts[1]  # 对手方
        excel_date = parts[2]  # Excel 日期数字
        
        # 债券名称 + 代码（格式：25 超长特别国债 02(2500002)）
        bond_with_code = parts[3]
        
        # 提取债券代码
        bond_code_match = re.search(r'\((\d+)\)', bond_with_code)
        if not bond_code_match:
            return None
        
        bond_code = bond_code_match.group(1)
        
        # 金额、收益率、备注
        amount = parts[4]
        yield_rate = parts[5]
        remark = ' '.join(parts[6:])
        
        # 转换日期
        try:
            base_date = datetime(1899, 12, 30)
            target_date = base_date + timedelta(days=int(excel_date))
            trade_date = target_date.strftime("%Y-%m-%d")
        except:
            trade_date = excel_date
        
        return {
            'direction': direction,
            'counterparty': counterparty,
            'trade_date': trade_date,
            'bond_code': bond_code,
            'amount': amount,
            'yield_rate': yield_rate,
            'remark': remark
        }
    except Exception as e:
        return None

def format_output_text(records):
    if not records:
        return ""
    lines = ["交易记录:"]
    for record in records:
        line = f"{record['direction']} | {record['counterparty']} | {record['trade_date']} | {record['bond_code']} | {record['amount']} | {record['yield_rate']} | {record['remark']}"
        lines.append(line)
    return '\n'.join(lines)

def main():
    print("="*80)
    print("CSV 转 JSON - 训练数据预处理")
    print("="*80)
    print()
    
    print(f"读取 CSV 文件：{INPUT_FILE}")
    data = []
    
    with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)  # 读取表头
        
        print(f"列名：{headers}")
        print()
        
        row_count = 0
        
        for row in reader:
            row_count += 1
            
            if len(row) < 2:
                continue
            
            input_text = row[0].strip() if len(row) > 0 else ''
            
            if not input_text:
                continue
            
            output_records = []
            
            # 读取输出 1 到输出 6 (列索引 1-6)
            for i in range(1, min(7, len(row))):
                output_text = row[i].strip()
                
                if output_text:
                    record = parse_output_line(output_text)
                    if record:
                        output_records.append(record)
            
            if output_records:
                json_record = {
                    'input': input_text,
                    'output': format_output_text(output_records)
                }
                data.append(json_record)
    
    print(f"读取了 {row_count} 行数据")
    print(f"成功转换 {len(data)} 条记录")
    print()
    
    print(f"保存 JSON 文件：{OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"[OK] 已保存 {len(data)} 条记录")
    print()
    print("="*80)
    print("[OK] 转换完成！")
    print("="*80)

if __name__ == "__main__":
    main()
