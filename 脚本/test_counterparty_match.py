"""
测试对手方名称模糊匹配字典的使用
"""

import sys
sys.path.append('输出样本')

from counterparty_dict import match_counterparty, COUNTERPARTY_ALIASES

# ===================== 测试用例 =====================
test_cases = [
    # 农商行/农联社
    ("泊头市联社", "泊头市农联社"),
    ("成泰农商行", "浙江金华成泰农商行"),
    ("江南农商行资管", "江苏江南农商银行资管"),
    ("内蒙古农商行", "内蒙古农商银行"),
    ("昆山农商", "昆山农村商行"),
    ("常熟农商行", "常熟农村商行"),
    ("张家港农商行", "张家港农村商业银行"),
    ("宁晋农商行", "河北宁晋农商行"),
    ("枞阳农商行", "枞阳农商银行"),
    ("方山农商行", "方山农商银行"),
    ("紫阳农商行", "陕西紫阳农商银行"),
    ("临澧农商行", "湖南临澧农商银行"),
    ("株洲珠江农商行", "湖南株洲珠江农商银行"),
    ("岳阳农商行", "湖南岳阳农商银行"),
    ("秦都农商行", "秦都农商银行"),
    ("青田农商行", "青田农商银行"),
    
    # 券商
    ("浙商证券", "浙商证券"),
    ("方正证券", "方正证券"),
    ("平安证券", "平安证券"),
    ("华福证券", "华福证券"),
    ("华源证券", "华源证券"),
    ("财信证券", "财信证券"),
    
    # 银行
    ("华夏银行", "华夏银行"),
    ("平安银行", "平安银行"),
    ("恒丰银行", "恒丰银行"),
    ("桂林银行", "桂林银行"),
    ("南浔银行", "南浔银行"),
    ("苏州银行", "苏州银行"),
    ("成都银行", "成都银行"),
    ("瑞穗银行", "瑞穗银行"),
    ("潍坊银行", "潍坊银行"),
    ("新疆银行", "新疆银行"),
    ("吉林银行", "吉林银行"),
    ("天津银行", "天津银行"),
    ("美国上海", "美国银行"),
    
    # 其他
    ("东兴证券", "东兴证券"),
    ("申港证券", "申港证券"),
    ("西部证券", "西部证券"),
    ("华创证券", "华创证券"),
]

# ===================== 测试函数 =====================
def test_matching():
    print("="*80)
    print("对手方名称模糊匹配测试")
    print("="*80)
    print()
    
    passed = 0
    failed = 0
    
    for input_name, expected in test_cases:
        result = match_counterparty(input_name)
        status = "[OK]" if result == expected else "[Error]"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"{status} {input_name:20} -> {result:25} (期望：{expected})")
    
    # 只打印失败的，成功的省略
    if failed == 0:
        print(f"\n[OK] 所有 {passed} 个测试全部通过！")
    else:
        print(f"\n[结果] 通过：{passed}, 失败：{failed}")
    
    print()
    print("="*80)
    
    return failed == 0

def show_statistics():
    print("\n字典统计信息：")
    print("-"*80)
    print(f"标准别名映射数：{len(COUNTERPARTY_ALIASES)}")
    print()
    
    # 按类型分类统计
    bank_count = sum(1 for k in COUNTERPARTY_ALIASES if '银行' in k or '农商' in k or '农联' in k)
    security_count = sum(1 for k in COUNTERPARTY_ALIASES if '证券' in k)
    other_count = len(COUNTERPARTY_ALIASES) - bank_count - security_count
    
    print(f"  - 银行/农商行类：{bank_count}")
    print(f"  - 券商类：{security_count}")
    print(f"  - 其他：{other_count}")
    print()

if __name__ == "__main__":
    show_statistics()
    success = test_matching()
    
    if success:
        print("\n[提示] 字典可以集成到 clean_test_input.py 中使用")
        print("       在删除括号内容后，对对手方名称进行标准化")
    else:
        print("\n[警告] 部分测试未通过，请检查字典配置")
