"""
测试 clean_test_input.py 中的模糊匹配功能
"""

import sys
sys.path.append('输出样本')
sys.path.append('脚本')

from counterparty_dict import match_counterparty

# ===================== 测试用例（来自测试输入文件） =====================
test_cases = [
    # 测试输入中的对手方
    ("平安证券", "平安证券"),
    ("山东高青农商行", "山东高青农商行"),
    ("江苏洪泽农商行", "江苏洪泽农商行"),
    ("陕西宁陕农商行", "陕西宁陕农商银行"),
    ("阳泉农商行", "阳泉农商银行"),
    ("方正证券", "方正证券"),
    ("防城港市联社", "防城港市区农联社"),
    ("爱建证券", "爱建证券"),
    ("广东清新农商行", "广东清新农村商业银行股份有限公司"),
    ("瑞穗银行", "瑞穗银行"),
    ("平安银行", "平安银行"),
    ("中信证券", "中信证券"),
    ("湖南新化农商行", "湖南新化农商行"),
    ("国元证券", "国元证券"),
    ("陕西杨凌农商行", "陕西杨凌农商行"),
    ("渣打中国", "渣打中国"),
]

# ===================== 测试函数 =====================
def test_matching():
    print("="*80)
    print("测试输入文件中的对手方名称匹配测试")
    print("="*80)
    print()
    
    passed = 0
    failed = 0
    improved = 0
    
    for input_name, expected in test_cases:
        result = match_counterparty(input_name)
        
        if result == expected:
            passed += 1
            if result != input_name:
                improved += 1
                print(f"[OK] {input_name:15} -> {result}")
            else:
                print(f"[=]  {input_name:15} -> {result}")
        else:
            failed += 1
            print(f"[Error] {input_name:15} -> {result} (期望：{expected})")
    
    print()
    print("="*80)
    print(f"测试结果：通过 {passed} 个，失败 {failed} 个")
    print(f"其中 {improved} 个名称被成功标准化")
    print("="*80)
    
    return failed == 0

if __name__ == "__main__":
    success = test_matching()
    
    if success:
        print("\n[OK] 所有测试通过！模糊匹配功能已正确集成。")
    else:
        print("\n[Warning] 部分测试未通过，请检查字典配置。")
