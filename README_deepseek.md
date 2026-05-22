# DeepSeek-V4-Flash 使用指南

## 📋 一、获取 API Key

### 1. 注册 DeepSeek 账号
1. 访问：https://platform.deepseek.com
2. 点击"注册"完成账号创建
3. 完成实名认证（需要手机号）

### 2. 充值
1. 进入"控制台" → "充值"
2. 建议首次充值 ¥50-100
3. 新注册用户可能有免费额度

### 3. 获取 API Key
1. 进入"控制台" → "API Keys"
2. 点击"创建新的 API Key"
3. 复制并保存（只显示一次）

## 💰 二、价格说明

### DeepSeek-V4-Flash 定价
- **输入**：¥0.002 / 千 tokens
- **输出**：¥0.008 / 千 tokens

### 测试成本估算
以 7 条测试数据为例：
- 每条输入：约 50 tokens
- 每条输出：约 200 tokens
- 总成本：7 × (50×0.002 + 200×0.008) / 1000 = **约 ¥0.01**

### 大规模使用成本
假设每天处理 100 条交易：
- 每月成本：100 × 30 × ¥0.002 = **约 ¥6/月**

## 🔧 三、配置脚本

### 1. 修改 API Key
打开 `脚本/test_deepseek_v4.py`，找到第 13 行：

```python
API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxx"  # 替换为你的 API Key
```

替换为你从 DeepSeek 平台获取的 API Key。

### 2. 安装依赖
```bash
pip install openai
```

## ▶️ 四、运行测试

### 1. 准备测试数据
确保 `输出样本/测试输入.txt` 包含测试数据

### 2. 运行脚本
```bash
cd "d:\Trae CN\量化文件夹\做市导入"
python 脚本/test_deepseek_v4.py
```

### 3. 查看结果
结果保存在 `输出样本/测试结果_deepseek_v4.txt`

## 📊 五、预期输出示例

**输入：**
```
1)  6.67Y   250025  1.60  4000  04.24+0  广州银行 (对话  IDeal 发) 出给 江苏启东农商行 (请求)
```

**预期输出：**
```
交易记录:
买入 | 广州银行 | 2026-04-24 | 250025 | 4000 | 1.60 | 上家广州银行，下家启东农商行，履行做市商职责，上下家不偏离。
卖出 | 江苏启东农村商业银行 | 2026-04-24 | 250025 | 4000 | 1.60 | 上家广州银行，下家启东农商行，履行做市商职责，上下家不偏离。
```

## ⚡ 六、优势对比

| 特性 | DeepSeek-V4-Flash | Qwen1.5-1.8B (本地) |
|------|------------------|---------------------|
| **一对多输出** | ✅ 支持 | ❌ 不支持 |
| **日期格式** | ✅ 正确 | ❌ 需后处理 |
| **债券代码** | ✅ 纯数字 | ❌ 需后处理 |
| **对手方识别** | ✅ 准确 | ⚠️ 有时错误 |
| **成本** | ¥0.01/次 | 免费（但效果差） |
| **速度** | <1 秒 | ~30 秒 |
| **需要训练** | ❌ 不需要 | ✅ 需要 |

## 🚀 七、集成到生产环境

### 批量处理脚本
创建 `batch_process.py`：

```python
from openai import OpenAI
import json

client = OpenAI(api_key="your-key", base_url="https://api.deepseek.com")

def process_trade(input_text):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是债券交易助手..."},
            {"role": "user", "content": input_text}
        ]
    )
    return response.choices[0].message.content

# 批量处理
with open("input.txt", "r", encoding="utf-8") as f:
    inputs = [line.strip() for line in f]

results = []
for inp in inputs:
    output = process_trade(inp)
    results.append({"input": inp, "output": output})

with open("output.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
```

## 🔒 八、安全建议

1. **不要硬编码 API Key**
   - 使用环境变量：`os.environ.get("DEEPSEEK_API_KEY")`
   - 或使用配置文件（加入 .gitignore）

2. **设置使用限额**
   - 在 DeepSeek 平台设置每月消费上限
   - 开启消费提醒

3. **监控使用情况**
   - 定期检查 API 调用日志
   - 发现异常及时冻结 API Key

## 📞 九、常见问题

### Q: API 调用失败怎么办？
A: 检查：
1. API Key 是否正确
2. 网络连接是否正常
3. 账户余额是否充足
4. 查看错误信息（通常在 exception 中）

### Q: 输出格式不符合预期？
A: 调整 SYSTEM_PROMPT，提供更详细的示例

### Q: 如何降低使用成本？
A: 
1. 优化 prompt，减少不必要的输出
2. 使用缓存，避免重复调用
3. 批量处理，减少 API 调用次数

## 📚 十、参考资料

- DeepSeek 官方文档：https://platform.deepseek.com/docs
- API 定价：https://platform.deepseek.com/pricing
- OpenAI Python SDK: https://github.com/openai/openai-python
