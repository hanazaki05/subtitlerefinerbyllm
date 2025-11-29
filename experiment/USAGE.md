# 使用指南 - main_sdk.py

完整的 OpenAI SDK 字幕处理工具使用手册。

---

## 🚀 快速开始（5分钟上手）

### 1. 确认环境

```bash
# 确认你在 experiment 目录
cd /Users/zerozaki07/Downloads/subretrans/experiment

# 确认 key 文件存在
ls -la ../key

# 确认 OpenAI SDK 已安装
../venv/bin/python -c "import openai; print('✓ SDK installed')"
```

### 2. 测试 API 连接

```bash
../venv/bin/python main_sdk.py ../example_input.ass output.ass --test-connection
```

**期望输出：**
```
Testing API connection...
✓ API connection successful!
```

### 3. 快速测试（10 对字幕）

```bash
# 非流式模式
../venv/bin/python main_sdk.py ../example_input.ass test_output.ass --dry-run

# 流式模式（推荐）
../venv/bin/python main_sdk.py ../example_input.ass test_output.ass --dry-run --streaming -v
```

### 4. 处理真实文件

```bash
# 推荐：流式模式 + 详细输出
../venv/bin/python main_sdk.py \
  ../example_input.ass \
  output_final.ass \
  --streaming \
  --pairs-per-chunk 50 \
  -v
```

---

## 📋 命令行参数

### 必需参数

- `input` - 输入的 .ass 字幕文件路径
- `output` - 输出的 .ass 字幕文件路径

### 核心功能参数

- `--streaming` - **启用流式 API**（实时显示进度，2.7x 更快感知）
- `--model MODEL` - 指定模型名称（默认：`gpt-5-mini`）
- `--dry-run` - 测试模式，仅处理前 10 对字幕
- `--test-connection` - 测试 API 连接并退出

### 分块控制参数

- `--pairs-per-chunk N` - 每个 chunk 固定包含 N 对字幕（覆盖 token-based）
- `--max-chunks N` - 最多处理 N 个 chunk（用于测试）
- `--memory-limit N` - 全局内存 token 限制（默认：4000）

### 调试输出参数

- `-v` / `--verbose` - 启用详细输出（显示时间和响应预览）
- `-vv` - 超详细输出（显示完整 API 响应）
- `-vvv` - 调试模式（包含系统提示和内存）
- `--stats SECONDS` - 统计刷新间隔秒数（默认：1.0）

---

## 📖 使用示例

### 示例 1: 测试连接

```bash
python main_sdk.py input.ass output.ass --test-connection
```

### 示例 2: 快速测试新文件

```bash
# 1. 先用 dry-run 测试（流式）
python main_sdk.py ../new_subtitle.ass test.ass --dry-run --streaming -v

# 2. 测试通过后处理完整文件
python main_sdk.py ../new_subtitle.ass output.ass --streaming -v
```

### 示例 3: 完整处理

```bash
# 非流式（标准批处理模式）
python main_sdk.py ../JAG.S04E08.zh-cn.ass output.ass

# 流式（实时反馈，推荐）
python main_sdk.py ../JAG.S04E08.zh-cn.ass output.ass --streaming -v
```

### 示例 4: 分块控制

```bash
# 固定每 chunk 50 对字幕
python main_sdk.py input.ass output.ass --pairs-per-chunk 50

# 只处理前 3 个 chunk
python main_sdk.py input.ass output.ass --max-chunks 3

# 组合使用
python main_sdk.py input.ass output.ass \
  --streaming \
  --pairs-per-chunk 30 \
  --max-chunks 5 \
  -v
```

### 示例 5: 使用不同模型

```bash
# 使用 GPT-4o
python main_sdk.py input.ass output.ass --model gpt-4o --streaming

# 使用 GPT-4o-mini（更便宜，约 15x cheaper）
python main_sdk.py input.ass output.ass --model gpt-4o-mini --streaming
```

### 示例 6: 调试问题

```bash
# 查看完整 API 响应和系统提示
python main_sdk.py input.ass output.ass \
  --dry-run \
  --streaming \
  -vvv
```

### 示例 7: 批量处理多个文件

```bash
#!/bin/bash
# batch_process.sh

for file in ../*.ass; do
    basename=$(basename "$file" .ass)
    echo "Processing $basename..."
    ../venv/bin/python main_sdk.py \
      "$file" \
      "output_${basename}.ass" \
      --streaming \
      --pairs-per-chunk 50 \
      -v
done
```

---

## 📊 输出示例

### 非流式模式输出

```
============================================================
SUBTITLE REFINEMENT TOOL (OpenAI SDK)
============================================================
Input:     ../example_input.ass
Output:    output.ass
Model:     gpt-5-mini
Mode:      Non-streaming
============================================================

Step 1: Parsing ASS file...
  Parsed 304 dialogue lines

Step 2: Building subtitle pairs...
  Created 152 subtitle pairs

Step 3: Splitting into chunks...
  Base prompt tokens: 1,234
  Chunking strategy: Token-based (max ~60,000 tokens)
  Created 3 chunks

Step 4: Processing chunks with LLM...
------------------------------------------------------------

Processing chunk 1/3 (60 pairs)...
[Chunk 1/3] (33.3% complete)
  Tokens used: 5,234 (prompt: 2,345, completion: 2,889)

...

✓ Subtitle refinement completed successfully!
```

### 流式模式输出（-v）

```
Processing chunk 1/3 (60 pairs)...
  Streaming: .............................  ← 实时进度点
[Chunk 1/3] (33.3% complete)
  Tokens used: 5,234 (prompt: 2,345, completion: 2,889)
  Time: 12.34s  ← 处理时间

  Response: [
            {
              "id": 0,
              "eng": "Hello world.",  ← 响应预览
  Reasoning tokens: 1,234  ← 推理 tokens（GPT-5）
```

---

## 📈 流式 vs 非流式对比

| 特性 | 非流式 | 流式 | 优势 |
|------|--------|------|------|
| **速度感知** | ⭐⭐ 需等待完整响应 | ⭐⭐⭐⭐⭐ 立即反馈 | **2.7x 更快** |
| **进度显示** | ❌ 无实时反馈 | ✅ 实时显示进度点 | 更好体验 |
| **总时间** | 稍快 | 基本相同 | 相差不大 |
| **用户体验** | 等待 | 实时反馈 | 显著提升 |
| **适用场景** | 批量处理 | 交互式处理 | - |
| **参数** | 默认 | `--streaming` | - |

**建议**: 除非是纯后台批处理，否则推荐使用流式模式！

---

## ⚙️ 常用参数组合

### 最快速度（测试用）

```bash
python main_sdk.py input.ass output.ass \
  --model gpt-4o-mini \
  --streaming \
  --pairs-per-chunk 100 \
  --max-chunks 3
```

### 最佳质量（生产用）

```bash
python main_sdk.py input.ass output.ass \
  --streaming \
  --pairs-per-chunk 50 \
  -v
```

### 调试模式

```bash
python main_sdk.py input.ass output.ass \
  --dry-run \
  --streaming \
  -vvv
```

### 成本控制

```bash
python main_sdk.py input.ass output.ass \
  --model gpt-4o-mini \
  --pairs-per-chunk 100 \
  --max-chunks 10
```

---

## 💰 性能优化建议

### 降低成本

```bash
# 1. 使用更便宜的模型
python main_sdk.py input.ass output.ass --model gpt-4o-mini

# 2. 限制处理数量
python main_sdk.py input.ass output.ass --max-chunks 10

# 3. 增加每个 chunk 的 pairs 数量（减少 API 调用）
python main_sdk.py input.ass output.ass --pairs-per-chunk 100
```

### 提高速度感知

```bash
# 使用流式 API（2.7x 更快感知）
python main_sdk.py input.ass output.ass --streaming -v
```

### 调试问题

```bash
# 1. 先测试连接
python main_sdk.py input.ass output.ass --test-connection

# 2. Dry-run 测试
python main_sdk.py input.ass output.ass --dry-run -v

# 3. 查看详细日志
python main_sdk.py input.ass output.ass --max-chunks 1 -vvv
```

---

## 🔧 故障排除

### 问题 1: "Key file not found"

```bash
# 检查 key 文件
ls -la ../key

# 如果不存在，创建它
echo "your-api-key-here" > ../key
```

### 问题 2: "Module 'openai' not found"

```bash
# 重新安装 OpenAI SDK
../venv/bin/pip install openai
```

### 问题 3: Input file not found

```bash
# 使用正确的相对路径
python main_sdk.py ../example_input.ass output.ass
```

### 问题 4: Memory limit exceeded

```bash
# 增加内存限制
python main_sdk.py input.ass output.ass --memory-limit 5000
```

### 问题 5: 处理速度慢

```bash
# 使用流式模式获得更快的感知速度
python main_sdk.py input.ass output.ass --streaming

# 或增加每个 chunk 的数量减少 API 调用
python main_sdk.py input.ass output.ass --pairs-per-chunk 100
```

### 问题 6: 成本太高

```bash
# 使用更便宜的模型
python main_sdk.py input.ass output.ass --model gpt-4o-mini

# 限制处理数量
python main_sdk.py input.ass output.ass --max-chunks 10

# 增大 chunk 大小减少 API 调用
python main_sdk.py input.ass output.ass --pairs-per-chunk 100
```

### 问题 7: Rate limit errors

- 程序会自动重试（3 次，指数退避：1s, 2s, 4s）
- 失败的 chunk 会被跳过，继续处理下一个
- 可以稍后重新运行处理失败的部分

---

## 🎯 完整工作流示例

```bash
# 1. 进入 experiment 目录
cd experiment

# 2. 测试 API 连接
python main_sdk.py ../example_input.ass test.ass --test-connection

# 3. Dry-run 测试（流式）
python main_sdk.py ../example_input.ass test.ass --dry-run --streaming -v

# 4. 处理真实文件（流式 + 详细输出）
python main_sdk.py ../JAG.S04E08.zh-cn.ass output_final.ass \
  --streaming \
  --pairs-per-chunk 50 \
  -v

# 5. 检查输出
ls -lh output_final.ass
diff ../JAG.S04E08.zh-cn.ass output_final.ass | head -20
```

---

## 🏆 高级用法

### 批量处理脚本

```bash
#!/bin/bash
# batch_process.sh

for file in ../*.ass; do
    basename=$(basename "$file" .ass)
    echo "Processing $basename..."
    python main_sdk.py "$file" "output_${basename}.ass" \
      --streaming \
      --pairs-per-chunk 50 \
      -v
done
```

使用方法：
```bash
chmod +x batch_process.sh
./batch_process.sh
```

### 监控处理时间

```bash
# 使用 time 命令
time python main_sdk.py ../example_input.ass output.ass --streaming
```

### 自定义日志

```bash
# 重定向输出到文件
python main_sdk.py input.ass output.ass --streaming -v 2>&1 | tee process.log
```

---

## 📊 与主项目 main.py 的区别

| 特性 | main.py | main_sdk.py |
|------|---------|-------------|
| **API 实现** | HTTP POST (requests) | OpenAI SDK |
| **流式支持** | ❌ | ✅ (`--streaming`) |
| **API key 来源** | 环境变量或 config.py | `../key` 文件 |
| **错误处理** | 手动重试 | SDK 内置 |
| **类型安全** | 基于 dict | Pydantic 模型 |
| **位置** | 项目根目录 | experiment/ 目录 |
| **使用场景** | 生产环境 | 实验和测试 |

---

## 💡 使用小技巧

1. **首次使用先 dry-run**
   ```bash
   python main_sdk.py input.ass output.ass --dry-run --streaming -v
   ```

2. **使用流式模式获得实时反馈**
   ```bash
   python main_sdk.py input.ass output.ass --streaming -v
   ```

3. **控制 chunk 大小优化成本**
   ```bash
   # 更大的 chunk = 更少的 API 调用 = 更低的成本
   python main_sdk.py input.ass output.ass --pairs-per-chunk 100
   ```

4. **使用 -v 查看处理进度**
   ```bash
   python main_sdk.py input.ass output.ass --streaming -v
   ```

5. **测试完成后再处理完整文件**
   ```bash
   # 1. 先测试
   python main_sdk.py input.ass test.ass --dry-run --streaming

   # 2. 再处理
   python main_sdk.py input.ass final.ass --streaming
   ```

---

## 📚 快速命令参考

| 需求 | 命令 |
|------|------|
| 测试连接 | `python main_sdk.py input.ass output.ass --test-connection` |
| 快速测试 | `python main_sdk.py input.ass output.ass --dry-run --streaming` |
| 完整处理（非流式） | `python main_sdk.py input.ass output.ass` |
| 完整处理（流式） | `python main_sdk.py input.ass output.ass --streaming` |
| 详细输出 | `python main_sdk.py input.ass output.ass --streaming -v` |
| 查看帮助 | `python main_sdk.py --help` |
| 限制处理数量 | `python main_sdk.py input.ass output.ass --max-chunks 5` |
| 固定 chunk 大小 | `python main_sdk.py input.ass output.ass --pairs-per-chunk 50` |
| 使用便宜模型 | `python main_sdk.py input.ass output.ass --model gpt-4o-mini` |
| 调试模式 | `python main_sdk.py input.ass output.ass --dry-run -vvv` |

---

**提示**: 首次使用建议先执行 `--dry-run --streaming -v` 测试，确认一切正常后再处理完整文件。

**更多信息**:
- 技术文档: [STREAMING_API.md](STREAMING_API.md)
- 项目总结: [SUMMARY.md](SUMMARY.md)
- 完整文档: [README.md](README.md)