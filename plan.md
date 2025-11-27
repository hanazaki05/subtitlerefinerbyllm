
# 基于「chunk + 精简记忆」模式的字幕二次校对实现方案

> 目标：对中英文对照的 `.ass` 字幕进行二次校对  
> - 中文：翻译质量、自然度、一致性  
> - 英文：只修正大小写 / 空格 / 末尾标点，**不改词义**  
> - 保留所有 ASS 标签与排版  
> - 利用 LLM，上下文有一定「全局记忆」，但不把所有历史重复塞进请求（省 token）

---

## 1. 技术栈与基础约定

- 语言：Python 3.10+
- 依赖建议：
  - `tiktoken`（或类似库）：用来估算 token 数量
  - `python-dotenv`：管理 API Key 等配置（可选）
  - HTTP 客户端：`requests` 或官方 OpenAI SDK（视你用哪家模型）
- LLM：假设使用 OpenAI 风格 API（旧API，/v1/chat/completions,以post方式进行api访问）；假设使用 GPT5.1 

- 使用api key (OPENAI): `***REMOVED***`

- 请求方式如下:
```
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
  "model": "gpt-5.1",
  "messages": [],
  "response_format": {
    "type": "text"
  },
  "verbosity": "medium",
  "reasoning_effort": "medium",
  "store": false
}'
```


---

## 2. 项目结构（建议）

```text
project_root/
  README.md
  subtitles_refine_plan.md      # 就是本文件
  config.py                     # 配置项（API Key, 模型名, 限制等）
  main.py                       # CLI 入口，负责 orchestrate 全流程
  ass_parser.py                 # 解析 & 生成 .ass
  pairs.py                      # SubtitlePair 结构及相关处理
  chunker.py                    # chunk 切分 & token 估算
  llm_client.py                 # 统一封装 LLM 调用
  memory.py                     # global_memory 结构 & 更新 & 压缩
  prompts.py                    # system prompt / memory prompt 模板
  stats.py                      # token 使用统计 & 费用估算
  utils.py                      # 通用工具函数
  tests/
    test_ass_parser.py
    test_chunker.py
    test_memory.py
    ...
```

---

## 3. 核心数据结构设计

### 3.1 AssLine（表示一行 Dialogue）

```python
class AssLine:
    id: int              # 在 Events 中的顺序索引
    raw: str             # 原始整行文本（覆盖以防 debug）
    layer: str
    start: str           # "0:00:01.00"
    end: str             # "0:00:03.00"
    style: str
    name: str
    margin_l: str
    margin_r: str
    margin_v: str
    effect: str
    text: str            # 仅文本部分，含 {\i1}、\N 等标签
```

### 3.2 SubtitlePair（中英 pair）

```python
class SubtitlePair:
    id: int              # 对应 AssLine.id
    eng: str             # 提取出的英文部分，保留标签
    chinese: str         # 提取出的中文部分，保留标签
    meta: dict           # 可选，存 style、时间信息等
```

> 注意：`eng`/`chinese` 中只包含该语言那一行（不含 `\N` 换行），ASS 标签原样保留。

### 3.3 GlobalMemory（跨 chunk 的精简记忆）

```python
class GlobalMemory:
    glossary: list[dict]    # 术语 / 人名表
    style_notes: str        # 风格说明/口吻统一信息（短文本）
    summary: str            # 剧情/上下文简述（可选）
```

示例：

```python
glossary = [
  {"eng": "John", "zh": "约翰", "type": "person"},
  {"eng": "The Foundation", "zh": "基金会", "type": "organization"},
]
style_notes = "整体中文保持口语化，使用‘你’而不是‘您’，避免过度书面化表达。"
```

### 3.4 配置 Config

```python
class Config:
    model_name: str
    api_key: str
    max_context_tokens: int        # 模型上下文上限，如 128000
    max_output_tokens: int
    memory_token_limit: int        # GlobalMemory 最大 token（比如 2000）
    chunk_token_soft_limit: int    # 单 chunk 输入 token 软上限（如 0.8 * max_context）
    dry_run: bool                  # 是否仅处理部分数据进行测试
```

---

## 4. 整体处理流程（概览）

1. **加载配置**（API key、模型名、token 限额等）
2. **读取 .ass 文件**
3. **解析 [Events] → AssLine 列表**
4. **从 AssLine 中提取中英 pair → SubtitlePair 列表**
5. **对 SubtitlePair 列表进行 chunk 切分**（按 token 估算）
6. 初始化 `GlobalMemory` 与 token 使用统计
7. 对每个 chunk（串行）：

   1. 构造 system prompt（规则 + 精简记忆）
   2. 构造 user 内容（该 chunk 的 JSON 列表）
   3. 调用 LLM → 得到校对后的 SubtitlePair 数组（JSON）
   4. 应用结果到全局 SubtitlePair 列表
   5. 从本 chunk 的结果里提取术语/风格信息 → 更新 `GlobalMemory`
   6. 若 memory token 超限 → 调用一次 LLM 压缩记忆
   7. 记录 usage（prompt_tokens, completion_tokens）
8. 所有 chunk 处理完后：

   1. 将校对后的 SubtitlePair 合并回 AssLine
   2. 生成新的 .ass 文件内容
   3. 写出为 `xxx.refined.ass`
   4. 输出运行统计（token 用量、预估费用）
9. 可选：生成一份术语表/变更 diff 报告

---

## 5. 详细模块与实现要点

### 5.1 ass_parser.py

**职责：**

* 读取 `.ass` 文件
* 保留原始 header 区域（[Script Info]、[V4+ Styles] 等）
* 解析 [Events] 下的所有 `Dialogue:` 行为 `AssLine` 对象
* 将 `AssLine` 列表和 header 信息返回

**要点：**

* 注意 `.ass` 每个 `Dialogue:` 行的字段顺序固定：
  `Dialogue: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text`
* Text 字段中可能含有逗号，所以 split 时只能切前 9 个逗号，余下部分作为 text

* Dialogue 的 style 名称会标注原始语言信息，根据时间轴和 style 构造 `SubtitlePair` 列表，并记录 `id` 与 `meta`

**注意：**

* 可能出现：

  * 只有英文、没有中文（或反之）：只有中文的情况跳过，只有英文或者构造 pair 并把中文设置成 空
  * 多行情况：可以只支持“两行模式”，更多行直接原样交回或标记为“复杂行”

---

### 5.3 chunker.py — chunk 切分与 token 估算

**目标：**

* 将 `SubtitlePair` 列表切成若干 chunk，每个 chunk 在 LLM 调用时不会超过 token 限制。

**步骤：**

1. 函数 `estimate_pair_tokens(pair)`：

   * 使用 `tiktoken` 对构造后的 JSON 条目进行估算
     （或者粗略 `len(text) / 2` 估算）
2. 函数 `chunk_pairs(pairs, config, base_prompt_token_estimate)`：

   * `base_prompt_token_estimate`：估算固定部分的 token（system + memory 大致长度）
   * 遍历 pairs，累计 `current_tokens`：

     * 若 `base_prompt_token_estimate + current_tokens + pair_tokens` 超过 `chunk_token_soft_limit`：

       * 结束当前 chunk，开启下一个
3. 返回 `chunks: list[list[SubtitlePair]]`

---

### 5.4 prompts.py — Prompt 模板

**1）字幕校对的 system prompt**

* 内容包含：

  * 英文校对规则（仅大小写、空格、末尾标点；保留 ASS 标签）
  * 中文校对规则（语义准确、自然、字幕风格；保留 ASS 标签）
  * 输出 JSON 格式要求
  * 「不要解释，只输出 JSON」

* `build_system_prompt(global_memory: GlobalMemory) -> str`：

  * 基础规则固定文本
  * 后面附加一小段「记忆区」：

    * 术语表（简化为几行）
    * 风格说明（几句）

**2）记忆压缩的 system + user prompt**

* 当 memory 超限时，用一个单独的调用：

  * system：你是帮我压缩术语/风格信息的助手
  * user：当前 `global_memory` 的 JSON
* 要求：

  * 保留所有术语映射，但合并重复、去掉不重要条目
  * 控制在 X 字数 / Y token 内
* 输出新的更短版本 `GlobalMemory`

---

### 5.5 llm_client.py — 统一 LLM 调用

**职责：**

* 封装具体 HTTP / SDK 细节
* 提供两个主要函数：

  1. `refine_chunk(pairs_chunk, global_memory, config) -> (corrected_pairs, usage)`
  2. `compress_memory(global_memory, config) -> (new_global_memory, usage)`

**`refine_chunk` 流程：**

1. 构造 `system_content = build_system_prompt(global_memory)`

2. 将 `pairs_chunk` 转换为 JSON（数组）作为 user 内容

3. 调用 API：

   * 类似：

     ```python
     response = client.responses.create(
       model=config.model_name,
       messages=[
         {"role": "system", "content": system_content},
         {"role": "user", "content": json.dumps(pairs_chunk_json, ensure_ascii=False)}
       ],
       max_output_tokens=config.max_output_tokens,
     )
     ```

4. 从响应中解析：

   * `output_text`（LLM 返回的 JSON 字符串）
   * `usage`（prompt/completion/total tokens）

5. `json.loads(output_text)` → `corrected_pairs`

6. 返回 `corrected_pairs, usage`

**`compress_memory` 类似，只是 prompt 不同，输入/输出是 `GlobalMemory` 对象。**

---

### 5.6 memory.py — GlobalMemory 管理

**功能：**

1. `init_global_memory() -> GlobalMemory`
2. `update_global_memory(memory, corrected_pairs_chunk) -> GlobalMemory`

   * 从本 chunk 中抽取：

     * 新出现的专有名词及其中译
     * 一些常见句式/口吻（可选）
   * 方式：

     * 先用简单规则（正则）/ 稍微再调用一个小模型让它从字幕中提取术语
3. `estimate_memory_tokens(memory) -> int`
4. `compress_memory_with_llm(memory, config) -> (new_memory, usage)`

> 初版可以先写得很简单：
>
> * `glossary` 暂时人工不太复杂：比如只维持一个长度上限，超了就丢掉最早的若干条
> * 真需要时再用 LLM 做压缩

---

### 5.7 main.py — 全流程 orchestrator

伪代码结构：

```python
def main():
    config = load_config()
    
    # 1. 解析 ass
    header, ass_lines = parse_ass_file(input_path)
    
    # 2. 构建 SubtitlePair 列表
    pairs = build_pairs_from_ass_lines(ass_lines)
    
    # 3. 切 chunk（估 token）
    base_prompt_token_estimate = estimate_base_prompt_tokens(config)
    chunks = chunk_pairs(pairs, config, base_prompt_token_estimate)
    
    global_memory = init_global_memory()
    total_usage = init_usage_stats()
    
    # 4. 串行处理每个 chunk
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)} ...")
        
        corrected_pairs, usage = refine_chunk(chunk, global_memory, config)
        total_usage = accumulate_usage(total_usage, usage)
        
        # 将本 chunk 的 corrected_pairs 写回到 pairs 列表（根据 id 对应）
        apply_corrections_to_global_pairs(pairs, corrected_pairs)
        
        # 更新 memory
        global_memory = update_global_memory(global_memory, corrected_pairs)
        
        # 如 memory 超限，压缩
        if estimate_memory_tokens(global_memory) > config.memory_token_limit:
            new_memory, mem_usage = compress_memory_with_llm(global_memory, config)
            global_memory = new_memory
            total_usage = accumulate_usage(total_usage, mem_usage)
    
    # 5. pairs -> ass_lines -> 输出 .ass
    updated_ass_lines = apply_pairs_to_ass_lines(ass_lines, pairs)
    output_text = render_ass_file(header, updated_ass_lines)
    
    write_file(output_path, output_text)
    
    # 6. 打印统计
    print_usage_report(total_usage, config)
```

---

## 6. 调试与安全措施

1. **dry-run 模式**

   * 配置中加 `dry_run = True` 时：

     * 只处理前 N 条 pair 或前 1 个 chunk
   * 用于快速验证 prompt / 格式 / 标签是否被破坏

2. **结果校验**

   * 每次 LLM 返回后：

     * 确保 JSON 能正常解析
     * 每个条目 `id` 存在且唯一
     * `eng` / `chinese` 不为空（或者允许空，但要 log）

3. **标签完整性检查**

   * 可选：对每条字幕，校验 ASS 标签是否匹配：

     * 原文中的 `{\i1}` 次数 ≈ 新文本中 `{\i1}` 次数
   * 如果差异过大，给出警告日志

4. **错误处理**

   * LLM 调用失败：重试若干次，失败则中止，保存到当前进度
   * 对单 chunk 的错误，可以选择：

     * 直接跳过该 chunk 使用原字幕
     * 或者写入一个错误标记，方便后期人工处理

---

## 7. Token & 费用统计（stats.py）

* `UsageStats` 结构：

```python
class UsageStats:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```

* 每次 LLM 调用后累加
* 如果知道模型单价（可在 config 中手动配置），可估算费用并在结束打印：

```text
本次运行统计：
  prompt_tokens: 12345
  completion_tokens: 6789
  total_tokens: 19134
  预估费用: $X.XXX
```

---

## 8. CLI 入口设计（简单版）

* `python main.py input.ass output.ass`
* 可选参数：

  * `--dry-run`
  * `--max-chunks 1`
  * `--model gpt-4.1-mini`
  * `--memory-limit 2000`

使用 `argparse` 实现即可。

---



