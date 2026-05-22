"""
预处理测试输入文本
1. 删除所有括号内的内容（包括圆括号）
2. 对对手方名称进行模糊匹配标准化
"""

import re
import sys

# 导入模糊匹配字典
sys.path.append('输出样本')
from counterparty_dict import match_counterparty

# ===================== 配置区域 =====================
# 获取脚本所在目录的父目录（项目根目录）
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

INPUT_FILE = os.path.join(PROJECT_ROOT, "输出样本", "测试输入.txt")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "输出样本", "测试输入_cleaned.txt")

print(f"[DEBUG] 脚本目录: {SCRIPT_DIR}")
print(f"[DEBUG] 项目根目录: {PROJECT_ROOT}")
print(f"[DEBUG] 输入文件路径: {INPUT_FILE}")

# ===================== 处理函数 =====================
def remove_parentheses_content(text):
    """
    删除文本中所有圆括号及其内容（包括中文和英文括号）
    
    例如：
    - "广州银行 (对话  IDeal 发)" → "广州银行"
    - "江苏启东农商行 (请求)" → "江苏启东农商行"
    - "平安银行 5K(对话，池)" → "平安银行 5K"
    """
    # 删除所有圆括号及其内容（包括中文括号（）和英文括号 ()）
    # 先处理中文括号
    cleaned = re.sub(r'[（][^）]*[）]', '', text)
    # 再处理英文括号
    cleaned = re.sub(r'\([^)]*\)', '', cleaned)
    
    # 清理多余的空格（将多个连续空格替换为单个空格）
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip()

def extract_counterparties(text):
    """
    从文本中提取对手方名称
    
    例如：
    - "1）9.82Y 260005 1.75 1.1E 05.06+0 平安证券 出给 山东高青农商行"
    提取：["平安证券", "山东高青农商行"]
    """
    parties = []
    
    # 模式 1：提取"出给"之前的对手方
    match = re.search(r'[\d)）Y\s]+[\d\.]+[\s]+[\d\.]+[\s]+[\d\.E\s]+[\d\.\+]+\s+(.+?)\s+出给', text)
    if match:
        before_section = match.group(1)
        # 分割多个对手方（按 + 号）
        parts = re.split(r'\+', before_section)
        for part in parts:
            # 提取括号前的名称（去除数字和单位）
            party_match = re.search(r'([\u4e00-\u9fa5A-Za-z]+)', part.strip())
            if party_match:
                parties.append(party_match.group(1))
    
    # 模式 2：提取"出给"之后的对手方
    match = re.search(r'出给\s+(.+?)(?:,|$)', text)
    if match:
        after_section = match.group(1)
        # 分割多个对手方
        parts = re.split(r'\+', after_section)
        for part in parts:
            party_match = re.search(r'([\u4e00-\u9fa5A-Za-z]+)', part.strip())
            if party_match:
                parties.append(party_match.group(1))
    
    return parties

def standardize_counterparties(text):
    """
    标准化文本中的对手方名称
    
    例如：
    - "泊头市联社 出给 山西证券" → "泊头市农联社 出给 山西证券"
    - "成泰农商行 出给 华福证券" → "浙江金华成泰农商行 出给 华福证券"
    """
    # 提取所有对手方名称
    parties = extract_counterparties(text)
    
    # 对每个对手方进行模糊匹配
    for party in parties:
        standard_party = match_counterparty(party)
        if standard_party != party:
            # 替换为标准化名称
            text = text.replace(party, standard_party)
    
    return text

def normalize_amount(amount):
    """
    标准化数量，确保都带单位
    - 5 → 5K（默认单位为K）
    - 5K → 5K（保持不变）
    - 5k → 5K（统一大写）
    - 5E → 5E（保持不变）
    - 5e → 5E（统一大写）
    """
    if re.match(r'^\d+$', amount):
        return f"{amount}K"
    elif re.match(r'^\d+[Kk]$', amount, re.IGNORECASE):
        return f"{amount[:-1].upper()}K"
    elif re.match(r'^\d+[Ee]$', amount, re.IGNORECASE):
        return f"{amount[:-1].upper()}E"
    return amount

def parse_split_amounts(text):
    """
    识别并处理同一机构的拆单情况
    
    拆单标识词：拆、分、拆单（出现在机构名和数量之间）
    如果机构名后直接跟多个数量（用+分隔），也视为拆单
    
    例如：
    - "淮安农商行拆2+1+1K 请求" → "淮安农商行 2K 请求+淮安农商行 1K 请求+淮安农商行 1K 请求"
    - "陕西榆林农商行 请求 分5K+2K" → "陕西榆林农商行 5K 请求+陕西榆林农商行 2K 请求"
    - "浙商泰隆商行1+1K" → "浙商泰隆商行 1K+浙商泰隆商行 1K"
    - "天风证券拆1+3" → "天风证券 1K+天风证券 3K"
    """
    
    org_pattern = r'[\u4e00-\u9fa5A-Za-z]+(?:银行|证券|基金|联社|商行|农信|农商行|农商银行|有限|股份|公司)'
    split_keywords = r'拆|分|拆单'
    amount_pattern = r'\d+[KkEe]?'
    
    def extract_tag_and_amounts(remaining):
        """从剩余文本中提取标签和数量"""
        amounts = []
        tag = ""
        parts = remaining.split('+')
        
        for i, part in enumerate(parts):
            part = part.strip()
            tag_match = re.search(r'\s+(请求|对话|发请求)$', part)
            if tag_match:
                if i == len(parts) - 1:
                    tag = tag_match.group(1)
                    part = part[:tag_match.start()].strip()
            
            amount_match = re.match(rf'^({amount_pattern})', part)
            if amount_match:
                amounts.append(amount_match.group(1))
        
        return tag, amounts
    
    def replace_with_split(org_name, amounts, tag=""):
        """构建拆单后的字符串，每个部分都要带标签"""
        result_parts = []
        for amount in amounts:
            normalized = normalize_amount(amount)
            if tag:
                result_parts.append(f"{org_name} {normalized} {tag}")
            else:
                result_parts.append(f"{org_name} {normalized}")
        return " + ".join(result_parts)
    
    result = text
    
    # 模式1：机构名 + 拆单关键词 + 数量+数量+... + 可选标签
    # 例如：淮安农商行拆2+1+1K 请求
    pattern1 = re.compile(
        rf'({org_pattern})'
        rf'({split_keywords})'
        rf'\s*'
        rf'([\d+KkEe\+]+)'
        rf'(?:\s+(请求|对话|发请求))?'
    )
    
    for match in pattern1.finditer(result):
        org_name = match.group(1)
        amounts_str = match.group(3).strip()
        tag = match.group(4) if match.group(4) else ""
        _, amounts = extract_tag_and_amounts(amounts_str)
        replacement = replace_with_split(org_name, amounts, tag)
        result = result[:match.start()] + replacement + result[match.end():]
        break
    
    # 模式2：机构名 + 可选标签 + 拆单关键词 + 数量+数量+...
    # 例如：陕西榆林农商行 请求 分5K+2K
    pattern2 = re.compile(
        rf'({org_pattern})'
        rf'\s+(请求|对话|发请求)'
        rf'\s+({split_keywords})'
        rf'\s*'
        rf'([\d+KkEe\+]+)'
    )
    
    for match in pattern2.finditer(result):
        org_name = match.group(1)
        tag = match.group(2)
        all_amounts_part = match.group(4).strip()
        _, amounts = extract_tag_and_amounts(all_amounts_part)
        replacement = replace_with_split(org_name, amounts, tag)
        result = result[:match.start()] + replacement + result[match.end():]
        break
    
    # 模式3：机构名后直接跟数量（无拆单关键词，但有多个用+连接的数量）
    # 例如：浙商泰隆商行1+1K
    pattern3 = re.compile(
        rf'({org_pattern})'
        rf'\s*'
        rf'(\d+[KkEe]?)'
        rf'\+'
        rf'([\d+KkEe\+]+)'
    )
    
    for match in pattern3.finditer(result):
        org_name = match.group(1)
        first_amount = match.group(2)
        rest_amounts = match.group(3).strip()
        
        all_amounts = [first_amount]
        tag, additional = extract_tag_and_amounts(rest_amounts)
        all_amounts.extend(additional)
        
        replacement = replace_with_split(org_name, all_amounts, tag)
        result = result[:match.start()] + replacement + result[match.end():]
        break
    
    return result

def clean_bank_names(text):
    """
    清洗银行名称，将"农商行"自动补全为"农商银行"
    注意：只替换不在标准名称字典中的文本，避免破坏已标准化的名称
    
    例如：
    - "山东高青农商行" → "山东高青农商银行"
    - "江苏洪泽农商行" → "江苏洪泽农商银行"
    - "淮北农商行" → "淮北农商行"（保持不变，因为是标准名称）
    """
    import re
    
    # 获取所有标准名称
    from counterparty_dict import COUNTERPARTY_ALIASES
    
    result = text
    # 找到所有匹配"XX农商行"的模式（XX不包含"农商银行"）
    pattern = re.compile(r'([\u4e00-\u9fa5]+?)农商行(?!银行)')
    
    for match in pattern.finditer(text):
        full_match = match.group(0)  # 如 "淮北农商行"
        
        # 如果完整匹配不在标准名称中，才进行替换
        if full_match not in COUNTERPARTY_ALIASES:
            prefix = match.group(1)      # 如 "淮北"
            result = result.replace(full_match, prefix + "农商银行")
    
    return result

# ===================== 主流程 =====================
print("读取测试输入文件...")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

print(f"读取了 {len(lines)} 条数据\n")

print("开始处理...\n")
cleaned_lines = []
replacement_count = 0

for i, line in enumerate(lines, 1):
    original = line
    
    # 步骤 1: 删除括号内容
    cleaned = remove_parentheses_content(line)
    
    # 步骤 2: 标准化对手方名称（先标准化，以便拆单匹配）
    cleaned = standardize_counterparties(cleaned)
    
    # 步骤 3: 识别并处理拆单情况
    cleaned = parse_split_amounts(cleaned)
    
    # 步骤 4: 将"农商行"替换为"农商银行"
    cleaned_before_bank = cleaned
    cleaned = clean_bank_names(cleaned)
    
    # 统计替换次数
    if cleaned != cleaned_before_bank:
        replacement_count += 1
    
    cleaned_lines.append(cleaned)
    
    print(f"[{i}/{len(lines)}]")
    try:
        print(f"    原始：{original}")
        print(f"    清洗：{cleaned}")
    except UnicodeEncodeError:
        # 如果无法显示，跳过打印
        pass
    print()

print(f"\n数据清洗统计：")
print(f"  共替换 {replacement_count} 处 '农商行' → '农商银行'")

# ===================== 保存结果 =====================
print(f"保存结果到 {OUTPUT_FILE}...")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for line in cleaned_lines:
        f.write(line + "\n")

print(f"\n[OK] 处理完成！")
print(f"    共处理 {len(cleaned_lines)} 条数据")
print(f"    结果已保存至：{OUTPUT_FILE}")

# ===================== 示例对比 =====================
print("\n" + "="*80)
print("处理前后对比示例：")
print("="*80)
for i in range(min(3, len(lines))):
    print(f"\n示例 {i+1}:")
    try:
        print(f"  处理前：{lines[i]}")
        print(f"  处理后：{cleaned_lines[i]}")
    except UnicodeEncodeError:
        # 如果无法显示，跳过
        pass
