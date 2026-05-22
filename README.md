# 债券交易记录生成系统

基于 DeepSeek-V4-Flash API 的债券交易记录自动化生成工具。

## 功能特点

- 🚀 **API 集成**：集成 DeepSeek-V4-Flash API，快速生成结构化交易记录
- ✅ **输入验证**：AI 驱动的智能输入要素验证（债券代码、收益率、金额、结算速度、交易对手）
- 📅 **动态日期**：自动使用当前日期，支持指定交易日
- 📊 **多格式输出**：支持 TXT 和 CSV 格式输出
- 🔒 **安全配置**：使用环境变量管理 API Key

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/NortonLiWH/Bond_info_transfer.git
cd Bond_info_transfer
```

### 2. 安装依赖

```bash
pip install openai python-dotenv
```

### 3. 配置 API Key

复制 `.env.example` 为 `.env`，并填入你的 DeepSeek API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```
DEEPSEEK_API_KEY=your_api_key_here
```

获取 API Key：https://platform.deepseek.com/

### 4. 运行程序

```bash
python 脚本/test_deepseek_v4.py
```

## 输入格式

标准输入格式示例：

```
260005 1.745 5000 +0 沭阳农商行 出给 阳高县联社
```

**必要要素：**
1. **债券代码**：6 位数字（如 260005）
2. **收益率**：小数格式（如 1.745）
3. **金额**：数字或带单位（如 5000、3.8E、5K）
4. **结算速度**：+0 或 +1
5. **交易对手**：包含"出给"关键词

**复杂示例：**
```
1) 9.79Y 260005 1.745 5000 05.14+0 常德农商行 出给 浙江苍南农商行 2k+江苏阜宁农商行 2k+银河证券 1k
```

## 输出格式

### TXT 格式
```
交易记录:
买入 | T+0 | 沭阳农商行 | 2026-05-14 | 260005 | 3000 | 1.744 | 上家沭阳农商行，下家阳高县联社，履行做市商职责，上下家不偏离。
卖出 | T+0 | 阳高县联社 | 2026-05-14 | 260005 | 3000 | 1.744 | 上家沭阳农商行，下家阳高县联社，履行做市商职责，上下家不偏离。
```

### CSV 格式
包含字段：交易方向 | 结算速度 | 对手方 | 交易日 | 债券代码 | 金额 (万) | 收益率 (%) | 备注

## 项目结构

```
Bond_info_transfer/
├── 脚本/
│   ├── test_deepseek_v4.py    # 主程序
│   └── run_all.py             # CSV 生成脚本
├── 训练数据/                   # 训练数据文件
├── 输出样本/                   # 输出结果文件
├── .env                        # API Key 配置（不上传）
├── .env.example                # API Key 模板
├── .gitignore                  # Git 忽略规则
└── README.md                   # 项目说明
```

## 输入验证规则

系统会自动验证输入要素：
- ✅ 债券代码：6 位数字
- ✅ 收益率：小数格式（区分于金额）
- ✅ 金额：整数或带 E/K 单位
- ✅ 结算速度：+0 或 +1
- ✅ 交易对手：包含"出给"

**验证失败示例：**
```
输入：260005 3.8E 05.14+0 承德银行 出给 国泰海通证券
错误：缺少必要要素：收益率（3.8E 是金额而非收益率）
```

## Token 用量统计

程序会自动统计 API Token 使用情况并估算费用：
- 提示 Token 用量
- 完成 Token 用量
- 总费用估算（人民币）

统计信息保存至 `输出样本/token_stats.json`

## 常见问题

### Q: 如何获取 DeepSeek API Key？
A: 访问 https://platform.deepseek.com/ 注册并获取 API Key

### Q: 为什么输出中包含 API Key？
A: 请使用 `.env` 文件配置 API Key，不要硬编码在代码中

### Q: 如何修改输出格式？
A: 编辑 `test_deepseek_v4.py` 中的 `SYSTEM_PROMPT` 模板

## 技术栈

- Python 3.x
- DeepSeek-V4-Flash API
- OpenAI Python SDK
- python-dotenv

## 费用说明

DeepSeek-V4-Flash API 价格：
- 输入：￥0.0005 / 1K tokens
- 输出：￥0.001 / 1K tokens

## License

MIT License

## 联系方式

如有问题，请提交 Issue 或联系作者。

---

**Made with ❤️ by NortonLiWH**
