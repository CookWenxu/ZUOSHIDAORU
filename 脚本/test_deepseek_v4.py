"""
使用 DeepSeek-V4-Flash API 进行推理
无需训练，直接调用 API
"""

import json
import re
import os
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ===================== 配置区域 =====================
API_KEY = "sk-42f8ac0d46784358aea06abb926f3960"  # 直接设置 API Key

MODEL = "deepseek-chat"  # DeepSeek-V4-Flash
OUTPUT_FILE = "输出样本/测试结果_deepseek_v4.txt"

# ===================== 后处理函数 =====================
def convert_excel_date(excel_date_str):
    """将 Excel 日期数字转换为长日期格式"""
    try:
        if re.match(r'^\d{5}$', str(excel_date_str).strip()):
            excel_date = int(excel_date_str)
            base_date = datetime(1899, 12, 30)
            target_date = base_date + timedelta(days=excel_date)
            return target_date.strftime("%Y-%m-%d")
        return excel_date_str
    except:
        return excel_date_str

def fix_amount_format(amount_str):
    """
    修正金额格式，将错误的日期格式转回金额
    例如：1927-05-18 -> 10000 (1E)
          1927-05-17 -> 10000 (1E)
    """
    try:
        # 检查是否是日期格式
        if re.match(r'^\d{4}-\d{2}-\d{2}$', str(amount_str).strip()):
            # 尝试解析为日期
            parsed_date = datetime.strptime(str(amount_str).strip(), "%Y-%m-%d")
            # Excel 日期 44684 = 1922-05-18，这是 1E 被错误解析的结果
            # 实际上 1E 应该 = 10000 万
            excel_date = (parsed_date - datetime(1899, 12, 30)).days
            # 如果 Excel 日期在 40000-50000 范围，很可能是 1E 被误解析
            if 40000 <= excel_date <= 50000:
                return "10000"  # 1E = 10000 万
        # 其他情况，尝试提取数字
        amount_str = str(amount_str).strip()
        # 如果包含"1E"或"1e"，直接替换为 10000
        if '1e' in amount_str.lower() and '10000' not in amount_str:
            return amount_str.lower().replace('1e', '10000')
        return amount_str
    except:
        return str(amount_str)

def extract_bond_code(bond_text):
    """提取债券代码中的纯数字部分"""
    try:
        match = re.search(r'\((\d+)\)', bond_text)
        if match:
            return match.group(1)
        match = re.search(r'\b(\d{6})\b', bond_text)
        if match:
            return match.group(1)
        return bond_text
    except:
        return bond_text

def postprocess_output(text):
    """对模型输出进行后处理"""
    lines = text.split('\n')
    
    # 检查是否是 Markdown 表格格式
    is_markdown_table = any('---' in line for line in lines)
    
    if is_markdown_table:
        return convert_markdown_table_to_standard(lines)
    
    # 非表格格式，按原逻辑处理
    processed_lines = []
    for line in lines:
        if not line.strip():
            processed_lines.append(line)
            continue
        
        parts = line.split('|')
        if len(parts) >= 5:
            for idx in range(len(parts)):
                part = parts[idx].strip()
                # 第 1 个字段是日期（索引 2）
                if idx == 2 and re.match(r'^\d{5}$', part):
                    parts[idx] = convert_excel_date(part)
                # 第 4 个字段是金额（索引 4），需要修正日期错误
                if idx == 4:
                    parts[idx] = fix_amount_format(part)
                # 债券代码处理
                if re.search(r'[\u4e00-\u9fa5]', part) and re.search(r'\(\d+\)', part):
                    parts[idx] = extract_bond_code(part)
            line = ' | '.join(parts)
        
        processed_lines.append(line)
    
    return '\n'.join(processed_lines)

def convert_markdown_table_to_standard(lines):
    """将 Markdown 表格转换为标准格式"""
    output_lines = ['交易记录:']
    
    for line in lines:
        if not line.strip() or '---' in line:
            continue
        
        if '交易方向' in line or '对手方' in line:
            continue
        
        parts = [p.strip() for p in line.split('|') if p.strip()]
        
        if len(parts) >= 7:
            direction = parts[0]
            counterparty = parts[1]
            date = parts[2]
            bond = parts[3]
            amount = parts[4]
            rate = parts[5]
            note = parts[6]
            
            date = convert_excel_date(date)
            bond = extract_bond_code(bond)
            amount = fix_amount_format(amount)  # 修正金额格式
            rate = re.sub(r'[^\d.]', '', str(rate))
            
            output_line = f"{direction} | {counterparty} | {date} | {bond} | {amount} | {rate} | {note}"
            output_lines.append(output_line)
    
    return '\n'.join(output_lines)

# ===================== 动态生成 Prompt 模板 =====================
# 获取今天的日期
today_date = datetime.now().strftime("%Y-%m-%d")

SYSTEM_PROMPT = f"""你是一个债券交易记录生成助手。

你的任务是根据输入的交易信息，生成结构化的交易记录。

## 核心规则

### 0. 输入要素验证（重要！）
在生成交易记录前，首先检查输入是否包含以下**基本要素**：
1. **债券代码**：6 位数字（如 260005、250215）
2. **收益率**：小数格式（如 2.237、1.8455、1.8285）
3. **金额**：数字，可能带 E/K 等单位（如 3.8E、5K、10000），或直接是整数（如 2000）
4. **结算速度**：+0 或 +1
5. **交易对手**：包含"出给"关键词

**识别规则**：
- **收益率位置**：通常在债券代码之后，金额之前
  - 例 1：`260005 1.745 5000` → 1.745 是收益率，5000 是金额
  - 例 2：`250215 1.8285 2000` → 1.8285 是收益率，2000 是金额
  - 例 3：`260005 3.8E` → 缺少收益率（3.8E 是金额）
  
- **区分收益率和金额**：
  - 收益率：纯小数，通常 1-4 之间（如 1.5、2.237、3.85）
  - 金额：整数或带单位（如 2000、3.8E、5K、10000）
  - 如果小数后面紧跟 E/K 等单位，则是金额而非收益率
  
**重要**：
- 输入验证**只检查基本要素是否存在**，**不检查**金额匹配、交易对手分配等复杂逻辑
- 如果缺少上述任何一个要素，返回：`[输入验证失败] 缺少必要要素：[具体缺少的要素]`
- 如果要素齐全，**直接生成交易记录**，不要在验证阶段进行额外分析

### 1. 理解"出给"的含义
"A 出给 B" 表示：
- 你从 A **买入**债券（A 是卖出方）
- 你向 B **卖出**债券（B 是买入方）
- 你是做交易的中间人，每一组交易的买入与卖出价格一致、数量也一致

例如：
- 一对一交易："广州银行 出给 江苏启东农商行" = 买入广州银行 + 卖出江苏启东农商行
- 多对一交易："邢台银行 + 方正证券 出给 平安银行" = 买入邢台银行 + 买入方正证券 + 卖出平安银行
- 一对多交易："爱建证券 出给 平安银行 + 平安证券 " = 买入爱建证券 + 卖出平安银行 + 卖出平安证券
- 多对多交易："爱建证券 + 平安银行 出给 平安银行 + 平安证券 " = 买入爱建证券 + 买入平安银行 + 卖出平安银行 + 卖出平安证券
- 重复对手交易："爱建证券 出给 平安银行 + 平安银行 " = 买入爱建证券 + 卖出平安银行 + 卖出平安银行

### 2. 金额单位转换
- "1E" = 1 亿 = 10000 万
- "5K" = 5000 万
- "2k" = 2000 万
- "3K" = 3000 万
- 数字直接出现（如 4000）= 4000 万

### 3. 输出格式
第一行："交易记录:"
后续每行：交易方向 | 结算速度 | 对手方 | 交易日 | 债券代码 | 金额 (万) | 收益率 (%) | 备注

### 4. N对N输出
如果输入中有有N个对手方,其中买入方有A个,卖出方有B个，必须输出N=A+B行：
- A 行买入（从 A 个上家买入）
- B 行卖出（卖给 B 个下家）

## 示例

输入：
1)  29.04Y  2500002  2.275  4k  04.13+0  浙商证券股份有限公司 2k+ 江苏江南农商行资管 2k 出给 方正证券3k + 平安银行 1k

解析：
- 上家：浙商证券股份有限公司 (2000 万)、江苏江南农商行资管 (2000 万)
- 下家：方正证券 (4000 万)、平安银行 (1000 万)
- 债券：2500002
- 收益率：2.275%
- 日期：2026-04-13
- 结算速度：T+0

输出：
交易记录:
买入 | T+0 | 浙商证券股份有限公司 | 2026-04-13 | 2500002 | 2000 | 2.275 | 上家浙商证券、江苏江南农商行资管，下家方正证券、平安银行，履行做市商职责，上下家不偏离。
买入 | T+0 | 江苏江南农商银行资管 | 2026-04-13 | 2500002 | 2000 | 2.275 | 上家浙商证券、江苏江南农商行资管，下家方正证券、平安银行，履行做市商职责，上下家不偏离。
卖出 | T+0 | 方正证券 | 2026-04-13 | 2500002 | 4000 | 2.275 | 上家浙商证券、江苏江南农商行资管，下家方正证券、平安银行，履行做市商职责，上下家不偏离。
卖出 | T+0 | 平安银行 | 2026-04-13 | 2500002 | 1000 | 2.275 | 上家浙商证券、江苏江南农商行资管，下家方正证券、平安银行，履行做市商职责，上下家不偏离。

输入：
1)  29.04Y  2500002  2.275  2k  +1  国泰海通证券 2k 出给 华福证券 2k

解析：
- 上家：国泰海通证券 (2000 万)
- 下家：华福证券 (2000 万)
- 债券：2500002
- 收益率：2.275%
- 日期：没有明确日期，使用今天日期 {today_date}
- 结算速度：T+1

输出：
交易记录:
买入 | T+1 | 国泰海通证券 | {today_date} | 2500002 | 2000 | 2.275 | 上家国泰海通证券证券，下家华福证券，履行做市商职责，上下家不偏离。
卖出 | T+1 | 华福证券 | {today_date} | 2500002 | 2000 | 2.275 | 上家国泰海通证券证券，下家华福证券，履行做市商职责，上下家不偏离。

### 5. 交易日确定规则（重要！）
- 如果输入中明确给出日期（如 04.13+0），则使用该日期（2026-04-13）
- 如果输入中没有日期信息（只有 +0 或 +1），则使用今天的日期：**{today_date}**

### 6. 输出检验
对每次输出结果进行检验：
1. 输入中的交易对手是否已经全部输出，且输入与输出交易对手名称一致
2. 买入方与卖出方的加总交易金额是否一致
3. 买入方与卖出方的加总交易日期是否一致
4. 买入方与卖出方的加总交易备注是否一致
5. 买入方与卖出方的加总交易收益率是否一致
6. 买入方与卖出方的加总交易债券代码是否一致
7. 检查交易日是否正确应用了上述规则
"""

# ===================== 初始化 API 客户端 =====================
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com"
)

# ===================== 读取测试输入 =====================
print("读取测试输入...")
# 优先使用清洗后的输入文件，如果不存在则使用原始文件
import os
if os.path.exists("输出样本/测试输入_cleaned.txt"):
    input_file = "输出样本/测试输入_cleaned.txt"
    print("使用清洗后的输入文件：测试输入_cleaned.txt")
else:
    input_file = "输出样本/测试输入.txt"
    print("使用原始输入文件：测试输入.txt")

with open(input_file, "r", encoding="utf-8") as f:
    test_inputs = [line.strip() for line in f if line.strip()]

print(f"读取了 {len(test_inputs)} 条测试数据\n")

# ===================== 执行测试 =====================
print("开始测试...\n")

# Token 统计
total_tokens = 0
total_prompt_tokens = 0
total_completion_tokens = 0

results = []
with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
    for i, input_text in enumerate(test_inputs, 1):
        print(f"[{i}/{len(test_inputs)}] 输入：{input_text[:60]}...")
        
        try:
            # 调用 DeepSeek API
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": input_text}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            prediction = response.choices[0].message.content.strip()
            
            # 统计 Token
            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens_for_request = usage.total_tokens
            
            total_prompt_tokens += prompt_tokens
            total_completion_tokens += completion_tokens
            total_tokens += total_tokens_for_request
            
            print(f"    预测输出：")
            print(f"    {prediction[:200]}...")
            print(f"    Token 用量：{total_tokens_for_request} (提示：{prompt_tokens}, 完成：{completion_tokens})")
            print()
            
            # 保存到文件
            f_out.write(f"输入 {i}:\n{input_text}\n\n")
            f_out.write(f"输出:\n{prediction}\n\n")
            f_out.write("=" * 80 + "\n\n")
            
            results.append({
                'input': input_text,
                'output': prediction
            })
            
        except Exception as e:
            print(f"    错误：{e}\n")
            f_out.write(f"输入 {i}:\n{input_text}\n\n")
            f_out.write(f"输出：[错误] {e}\n\n")
            f_out.write("=" * 80 + "\n\n")

# ===================== 完成 =====================
print("\n[OK] 测试完成！")
print(f"    共测试 {len(results)} 条数据")
print(f"    结果已保存至：{OUTPUT_FILE}")

# 输出 Token 统计
print()
print("="*80)
print("API Token 用量统计")
print("="*80)
print(f"  总 Token 数：{total_tokens:,}")
print(f"  提示 Token：{total_prompt_tokens:,}")
print(f"  完成 Token：{total_completion_tokens:,}")
print()

# 估算费用（DeepSeek-V4-Flash 价格：输入￥0.0005/1K tokens, 输出￥0.001/1K tokens）
input_cost = (total_prompt_tokens / 1000) * 0.0005
output_cost = (total_completion_tokens / 1000) * 0.001
total_cost = input_cost + output_cost

print("费用估算（人民币）：")
print(f"  提示费用：￥{input_cost:.4f}")
print(f"  完成费用：￥{output_cost:.4f}")
print(f"  总费用：￥{total_cost:.4f}")
print("="*80)

# 保存 Token 统计信息到文件
import json
token_stats = {
    'total_tokens': total_tokens,
    'prompt_tokens': total_prompt_tokens,
    'completion_tokens': total_completion_tokens,
    'input_cost': input_cost,
    'output_cost': output_cost,
    'total_cost': total_cost,
    'request_count': len(results)
}

stats_file = "输出样本/token_stats.json"
with open(stats_file, "w", encoding="utf-8") as f:
    json.dump(token_stats, f, ensure_ascii=False, indent=2)

print(f"\nToken 统计已保存至：{stats_file}")
