方案 ：第二次调用抽术语”实现:

---

## 1) 术语抽取 Prompt（给 `extract_terminology_from_chunk()` 用）

### System prompt（TERMS_EXTRACT_SYSTEM）(翻译成英语来写)

```text
你是一个中英字幕“术语/专名抽取器”，任务是从一组字幕对（英文+中文）中提取需要保持一致译法的条目，生成术语表。

你只做“抽取”，不要改写字幕内容。

抽取范围（只选有必要加入术语表的）：
- 人名 / 地名 / 组织机构 / 舰船与部队番号 / 项目或行动代号 / 法律条款名称 / 节目与作品名 / 专有缩写（如 JAG, NCIS）
- 固定译法的关键词（在片中反复出现且需要统一翻译）

不要抽取：
- 普通口语词（Tonight, Good evening, report 等）
- 仅是句首大写的普通词
- 纯功能词、疑问词
- 无法确定中文对应的条目（宁缺毋滥）

对每条术语，输出：
- eng: 英文术语（保留原始大小写；去掉两侧空格）
- zh: 对应的中文译法（从字幕中文中提取；去掉两侧空格）
- type: one of ["person","place","organization","title","acronym","unit","ship","project","law","other"]
- confidence: 0.0-1.0（能从字幕中明确对应则高；推测/不确定则低；低于 0.6 的不要输出）
- evidence_ids: 该术语出现的字幕 id 列表（最多 5 个，按出现顺序）

输出要求：
- 只输出 JSON 数组（list），不要输出解释、不要输出多余文字、不要使用 Markdown。
- 数组元素按首次出现顺序排列。
- 去重：同一 eng 只输出一次；若出现多个 zh，以最可信且最常见的为准。
```

### User prompt（TERMS_EXTRACT_USER_TEMPLATE）

把 chunk 的 corrected_pairs（注意：是校对后的）作为 JSON 发过去：

```text
下面是字幕对数组，每个元素包含 id、eng、chinese。请按 system 规则抽取术语表并输出 JSON 数组：

{{PAIRS_JSON}}
```

> `{{PAIRS_JSON}}` 由代码替换为 `json.dumps(corrected_pairs, ensure_ascii=False)`。

---

## 2) Codex 需要按这个方式“把术语抽取模型与主模型分开”的实现要求

你可以把下面这一段作为任务说明发给 Codex（很关键）：

### 配置分离要求（必须）

1. **主字幕校对模型**和**术语抽取模型**必须使用两套独立配置对象（或至少独立字段），例如：

   * `config.main_model`（用于 refine_chunk）
   * `config.term_model = "gpt-4o-mini"`（用于 extract_terminology_from_chunk）

2. `llm_client.py` 里提供两个不同的调用函数，且不要互相复用模型名：

   * `call_refine_model(messages, ...)` 使用 `config.main_model`
   * `call_term_model(messages, ...)` 使用 `config.term_model`

3. 术语抽取调用应当：

   * 输入：本 chunk 的 `corrected_pairs`
   * 输出：`List[TerminologyEntry]`
   * 解析失败时：返回空列表，不影响主流程（只 log）

4. 在 `update_global_memory()` 中：

   * 调用 `extract_terminology_from_chunk(corrected_pairs, llm_client, config)`
   * 将返回术语合并进 `global_memory.glossary`（去重、按 confidence 更新）

### 推荐的数据结构（TerminologyEntry）

```python
@dataclass
class TerminologyEntry:
    eng: str
    zh: str
    type: str
    confidence: float
    evidence_ids: list[int]
```

---

## 3) 小提示：更稳的“输出校验”（建议 Codex 加上）

让 Codex 在解析术语 JSON 后做校验：

* 必须是 list
* 每项必须包含 eng/zh/type/confidence/evidence_ids
* confidence >= 0.6
* eng、zh 非空
* evidence_ids 是 int list，最多 5 个

不符合就丢弃该条（或整批返回空），避免脏数据污染 glossary。

---

如果你愿意，我还可以顺手给你一份“术语合并策略”的伪代码（normalize、去重、替换规则），让 Codex 更容易一次写对。



## 术语合并策略（merge glossary）规则

### 目标

把每个 chunk 抽出来的 `new_terms: List[TerminologyEntry]` 合并进 `global_memory.glossary`，保证：

* 同一个英文术语（eng）只保留一条“最佳译法”
* 防止低质量/低置信度术语污染
* 长度可控（避免 memory 越滚越大）

---

## 1) Normalize 规则（用于 key）

### normalize_eng(s) -> key

用于判断“是不是同一个术语”。

伪代码：

```python
import re
import unicodedata

def normalize_eng(s: str) -> str:
    s = s.strip()
    s = unicodedata.normalize("NFKC", s)      # 全角半角、兼容字符归一
    # 去掉两侧标点（保留内部的 . & - ' 等，避免 A.B. 或 O'Neil 被破坏）
    s = re.sub(r"^[\s\"'“”‘’\(\)\[\]\{\}\.,:;!?-]+", "", s)
    s = re.sub(r"[\s\"'“”‘’\(\)\[\]\{\}\.,:;!?-]+$", "", s)

    # 多空格合一
    s = re.sub(r"\s+", " ", s)

    # key 使用 casefold（比 lower 更稳），但保留原始 eng 用于展示
    key = s.casefold()

    return key
```

> 说明：
>
> * `eng` 原文照存（展示用），`key` 用于去重
> * 不建议把所有标点都删掉，会误伤 `U.S.`、`O'Neil`、`F/A-18`

---

## 2) 过滤规则（先清洗 new_terms）

```python
def is_valid_term(t: TerminologyEntry) -> bool:
    if not t.eng or not t.zh:
        return False
    if t.confidence is None or t.confidence < 0.6:
        return False
    if t.type not in {"person","place","organization","title","acronym","unit","ship","project","law","other"}:
        return False
    # evidence_ids 允许为空但建议有；若有则限制数量
    if t.evidence_ids and len(t.evidence_ids) > 5:
        t.evidence_ids = t.evidence_ids[:5]
    return True
```

---

## 3) 合并主逻辑（去重 + 更新策略）

建议维护索引：`existing_map[key] -> entry_index`

```python
def merge_terms_into_glossary(glossary: list[TerminologyEntry],
                             new_terms: list[TerminologyEntry],
                             *,
                             max_glossary_size: int = 300) -> list[TerminologyEntry]:

    # 1) 建索引
    index = {}
    for i, e in enumerate(glossary):
        key = normalize_eng(e.eng)
        if key and key not in index:
            index[key] = i
        # 若 glossary 已经有重复 key，先保留先出现的，后面可做一次去重清理

    # 2) 遍历 new_terms 逐个合并
    for t in new_terms:
        if not is_valid_term(t):
            continue

        key = normalize_eng(t.eng)
        if not key:
            continue

        if key not in index:
            glossary.append(t)
            index[key] = len(glossary) - 1
            continue

        # 3) 冲突：已有同 key 的术语
        cur = glossary[index[key]]

        # 3.1 选择是否更新（替换规则）
        if should_replace(cur, t):
            # 更新：保留更好的 zh / type / confidence
            merged = merge_entry(cur, t)
            glossary[index[key]] = merged
        else:
            # 不替换：但可以合并证据 id（可选）
            glossary[index[key]] = merge_evidence_only(cur, t)

    # 4) 容量控制（裁剪）
    glossary = prune_glossary(glossary, max_glossary_size)

    # 5) 返回
    return glossary
```

---

## 4) 替换判定规则 should_replace()

核心思想：**同 key 下，优先保留更高置信度、更具体类型、更“稳定”的 zh。**

```python
TYPE_PRIORITY = {
  "person": 90,
  "organization": 80,
  "place": 75,
  "acronym": 70,
  "unit": 65,
  "ship": 60,
  "title": 55,
  "project": 50,
  "law": 45,
  "other": 10,
}

def should_replace(old: TerminologyEntry, new: TerminologyEntry) -> bool:
    # 1) 如果 old.zh 为空而 new.zh 不为空：替换
    if (not old.zh) and new.zh:
        return True

    # 2) 置信度明显更高：替换（避免频繁抖动，设阈值）
    if new.confidence >= old.confidence + 0.10:
        return True

    # 3) 同等置信度附近：更具体 type 优先（person/org/place > other）
    if abs(new.confidence - old.confidence) < 0.10:
        if TYPE_PRIORITY.get(new.type, 0) > TYPE_PRIORITY.get(old.type, 0) + 10:
            return True

    # 4) old 是 unknown/other，但 new 给出更明确 type：替换
    if old.type in {"other"} and new.type not in {"other"} and new.confidence >= old.confidence:
        return True

    # 5) 中文译法冲突时：谨慎替换
    # 如果 zh 不同，但 new 没有明显更高置信度，则不替换（避免抖动）
    if old.zh and new.zh and old.zh != new.zh:
        return new.confidence >= old.confidence + 0.15

    return False
```

---

## 5) 合并方式 merge_entry()

```python
def merge_entry(old: TerminologyEntry, new: TerminologyEntry) -> TerminologyEntry:
    # eng：保留“更标准”的一个
    # 通常保留更长、更包含信息的（例如 "Norman Delaporte" > "Norman"）
    eng = pick_better_eng(old.eng, new.eng)

    zh = new.zh if new.zh else old.zh
    type_ = new.type if TYPE_PRIORITY.get(new.type, 0) >= TYPE_PRIORITY.get(old.type, 0) else old.type
    confidence = max(old.confidence, new.confidence)

    evidence_ids = merge_ids(old.evidence_ids, new.evidence_ids, limit=5)

    return TerminologyEntry(eng=eng, zh=zh, type=type_, confidence=confidence, evidence_ids=evidence_ids)


def pick_better_eng(a: str, b: str) -> str:
    a_s, b_s = a.strip(), b.strip()
    # 偏好包含空格的全名（通常更具体）
    a_score = (1 if " " in a_s else 0, len(a_s))
    b_score = (1 if " " in b_s else 0, len(b_s))
    return a_s if a_score >= b_score else b_s


def merge_ids(a: list[int], b: list[int], limit: int = 5) -> list[int]:
    out = []
    for x in (a or []):
        if x not in out: out.append(x)
    for x in (b or []):
        if x not in out: out.append(x)
    return out[:limit]


def merge_evidence_only(old: TerminologyEntry, new: TerminologyEntry) -> TerminologyEntry:
    old.evidence_ids = merge_ids(old.evidence_ids, new.evidence_ids, limit=5)
    # confidence 可以留 old，或取 max（但不更新 zh/type）
    old.confidence = max(old.confidence, new.confidence)
    return old
```

---

## 6) 容量控制 prune_glossary()

当 glossary 超过上限（例如 300 条）时裁剪。建议按一个综合权重排序：

* 置信度越高越重要
* evidence 越多越重要（出现频率高）
* type 优先级加权（person/org/place 更重要）

```python
def prune_glossary(glossary: list[TerminologyEntry], max_size: int) -> list[TerminologyEntry]:
    if len(glossary) <= max_size:
        return glossary

    def score(t: TerminologyEntry) -> float:
        freq = len(t.evidence_ids or [])
        type_bonus = TYPE_PRIORITY.get(t.type, 0) / 100.0
        return (t.confidence or 0.0) * 10.0 + freq * 0.5 + type_bonus

    glossary_sorted = sorted(glossary, key=score, reverse=True)
    kept = glossary_sorted[:max_size]

    # 可选：再按首次出现顺序恢复（如果你想稳定显示）
    # 这里简化为保持 score 排序即可
    return kept
```

---

## 7) 把 glossary 文本化塞进 system prompt 的格式

为了节省 token，system 里不要塞完整 JSON，建议压缩成行文本：

```text
Glossary (keep translations consistent):
- JAG => 军法署 [acronym]
- Norman Delaporte => 诺曼·德拉波特 [person]
- ...
Style notes:
- 整体口语化，避免书面腔
```

> JSON 版留在 debug 文件里即可，system 用紧凑版。

glossary 在内存中使用 dataclass `TerminologyEntry` 存储；LLM I/O 和 debug 文件使用 dict/JSON。实现 `from_dict()` 与 `to_dict()`，并在合并前做字段校验和默认值填充。