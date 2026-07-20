# Liminal 引擎构建交接文档

## 项目背景

产品名：**Liminal**  
定位：以塔罗牌为刺激物的数字化投射测验 + 荣格式解读  
核心机制：用户对牌面做60秒自由联想 → 语言分析 → 与牌的"标准主题空间"做比对 → 偏移方向即心理信号  
数据结构说明：见 `engine/tarot_card_schema.md`

---

## 引擎构建任务清单

### 任务1：78张牌主题空间数据集（数据层）

**输出文件：**
- `engine/cards_major.json` — 22张大阿卡纳（The Fool 到 The World）
- `engine/cards_wands.json` — 权杖14张（Ace of Wands 到 King of Wands）
- `engine/cards_cups.json` — 圣杯14张（Ace of Cups 到 King of Cups）
- `engine/cards_swords.json` — 宝剑14张（Ace of Swords 到 King of Swords）
- `engine/cards_pentacles.json` — 星币14张（Ace of Pentacles 到 King of Pentacles）

**每张牌的 JSON 结构（严格遵守）：**

```json
{
  "id": "major_00",
  "name": "The Fool",
  "system": "Waite-Smith",
  "number": 0,
  "suit": "major",
  "theme_space": {
    "emotional_tone": {
      "valence": 0.7,
      "arousal": 0.8,
      "notes": "openness, lightness, naïve joy"
    },
    "agency": {
      "score": 0.9,
      "direction": "active",
      "notes": "self-initiated movement, stepping into the unknown"
    },
    "time_orientation": {
      "past": 0.1,
      "present": 0.3,
      "future": 0.6,
      "notes": "strongly future-facing, threshold moment"
    },
    "conflict_harmony": {
      "score": 0.6,
      "notes": "internal harmony with some external risk/tension"
    },
    "relational_direction": {
      "inward": 0.3,
      "outward": 0.7,
      "notes": "oriented toward the world, not introspection"
    },
    "core_imagery": ["cliff edge", "white sun", "small dog", "bundle", "white rose", "mountain path"],
    "core_themes": ["beginning", "leap of faith", "innocence", "freedom", "risk", "potential"]
  },
  "jungian_mapping": {
    "primary_archetype": "The Child / Puer Aeternus",
    "secondary_archetype": "The Trickster",
    "shadow_aspect": "recklessness, avoidance of consequence, refusal to grow",
    "individuation_stage": "initial call — the first step away from the known",
    "complex_signals": ["avoidance of commitment words", "repeated 'beginning' or 'start' language", "absence of responsibility framing"]
  },
  "standard_meaning": {
    "upright": "New beginnings, spontaneity, a leap into the unknown with trust and openness.",
    "reversed": "Recklessness, poor judgment, naïve risk-taking without grounding."
  }
}
```

**字段规范：**
| 字段 | 类型 | 范围 | 说明 |
|---|---|---|---|
| `emotional_tone.valence` | float | 0–1 | 0=负面，1=正面 |
| `emotional_tone.arousal` | float | 0–1 | 0=平静，1=激动 |
| `agency.score` | float | 0–1 | 0=完全被动，1=完全主动 |
| `agency.direction` | enum | active / passive / ambivalent | |
| `time_orientation` | 三个float | 三值之和=1.0 | past+present+future=1 |
| `conflict_harmony.score` | float | 0–1 | 0=强冲突，1=强和谐 |
| `relational_direction` | 两个float | 两值之和=1.0 | inward+outward=1 |
| `core_imagery` | list[string] | 4–8项 | 韦特牌面的关键视觉元素 |
| `core_themes` | list[string] | 4–8项 | 该牌的核心意义词 |
| `jungian_mapping.complex_signals` | list[string] | 2–5项 | 用户语料中若出现这些模式，提示该原型活跃 |

**注意事项：**
- 基于 Waite-Smith（韦特-史密斯）系统，Arthur Edward Waite 的标准解读
- 荣格原型映射参考荣格《原型与集体无意识》《人及其象征》
- `complex_signals` 是**用户语言行为模式**的描述，不是牌的关键词（这是引擎分析时的匹配触发器）
- 所有 float 值保留1位小数
- 每个文件是一个 JSON 数组 `[{...}, {...}, ...]`

---

### 任务2：分析 Schema 设计（`engine/analysis_schema.json`）

定义引擎的输入/输出结构。

**输入 Schema：**
```json
{
  "session_id": "string",
  "card": { /* 同上述牌的完整JSON */ },
  "raw_transcript": "string — 用户语音的逐字转写，保留填充词和自我修正",
  "features": {
    "first_person_density": 0.0,
    "absolutist_words": ["always", "never", "everyone"],
    "filler_count": 0,
    "self_corrections": ["actually", "I mean", "no wait"],
    "repeated_phrases": ["being stuck", "I don't know"],
    "pause_markers": ["[pause 2.3s]", "[pause 0.8s]"],
    "negation_count": 0,
    "word_count": 0,
    "speaking_duration_seconds": 0
  }
}
```

**输出 Schema（分析层，不是最终展示文本）：**
```json
{
  "deviation_signals": [
    {
      "dimension": "agency",
      "card_value": 0.1,
      "user_value": 0.8,
      "delta": 0.7,
      "direction": "user scores significantly higher",
      "interpretation": "User systematically avoids collapse framing, orients toward reconstruction"
    }
  ],
  "active_archetypes": [
    {
      "archetype": "The Hero",
      "confidence": "medium",
      "evidence": ["repeated 'I need to fix', 'I have to handle'", "high agency score"],
      "jungian_ref": "Hero archetype — the ego's drive to overcome obstacles"
    }
  ],
  "complex_indicators": [
    {
      "type": "mother_complex",
      "signal": "5 mentions of 'protection', 'safe', 'held'",
      "strength": "moderate"
    }
  ],
  "shadow_hints": ["avoidance of words related to failure", "no acknowledgment of the Tower's destruction theme"],
  "weak_signal_flag": false,
  "weak_signal_reason": null
}
```

---

### 任务3：Prompt 架构设计（`engine/prompts/`）

三个 prompt 文件：

**`engine/prompts/feature_extraction.txt`** — 特征层 prompt（如果用 LLM 补充特征提取）

**`engine/prompts/analysis_layer.txt`** — 分析层 prompt
- 输入：特征层数据 + raw 转写 + 牌的主题空间
- 输出：严格按 output schema 的 JSON
- 语气：中立、分析性，不写给用户看
- 关键约束：每条结论必须引用用户原话作为evidence；不能编造荣格原著内容

**`engine/prompts/writing_layer.txt`** — 写作层 prompt
- 输入：分析层 JSON 输出
- 输出：给用户看的解读文本，两个部分：
  - Part 1（先展示）：荣格比较解读——用户联想的心理含义
  - Part 2（后展示）：标准牌义参考
- **语气要求（核心）**：心理咨询师风格——简洁、学术、温暖三合一；不谄媚、不废话、不堆砌比喻、无 AI 腔；像你的咨询师在和你说话
- 长度：Part 1 约 150-250 词，Part 2 约 80-120 词
- 必须大量回引用户原话（至少2处直接引用）
- 如果 `weak_signal_flag=true`，诚实说明信号不足

---

### 任务4：特征层代码（`engine/feature_extractor.py`）

Python 脚本，输入 raw 转写文本，输出特征 JSON。

**需要实现的功能：**
1. **填充词检测**：统计 "um", "uh", "like", "you know", "I mean", "sort of", "kind of", "actually", "basically" 等的出现次数和位置
2. **自我修正检测**：识别 "no wait", "I mean", "actually", "or rather", "let me rephrase" 等修正标记
3. **第一人称密度**：I/me/my/myself 的词频 / 总词数
4. **绝对化用词**：always, never, everyone, no one, everything, nothing, completely, totally, absolutely, forever, impossible
5. **重复片段**：出现2次及以上的 2-gram 或 3-gram
6. **停顿标记解析**：如果转写中有 `[pause Xs]` 格式，提取停顿时长列表
7. **否定词计数**：not, never, no, don't, won't, can't, couldn't, wouldn't, shouldn't

**输入格式：**
```python
text = "I see... um... a figure on a cliff. I don't know, it feels like they're about to fall, or maybe jump. I mean, not like in a bad way. They seem free actually."
```

**输出格式：**
```json
{
  "first_person_density": 0.12,
  "absolutist_words": [],
  "filler_count": 2,
  "fillers_found": ["um"],
  "self_corrections": ["I mean", "actually"],
  "repeated_phrases": [],
  "pause_markers": [],
  "negation_count": 2,
  "word_count": 42,
  "speaking_duration_seconds": null
}
```

---

## 文件目录结构（最终）

```
engine/
├── tarot_card_schema.md       # 数据结构说明（已完成）
├── BUILD_INSTRUCTIONS.md      # 本文件
├── cards_major.json           # 任务1-a
├── cards_wands.json           # 任务1-b
├── cards_cups.json            # 任务1-c
├── cards_swords.json          # 任务1-d
├── cards_pentacles.json       # 任务1-e
├── analysis_schema.json       # 任务2
├── feature_extractor.py       # 任务4
└── prompts/
    ├── analysis_layer.txt     # 任务3
    └── writing_layer.txt      # 任务3
```

---

## 验收标准

- 所有 JSON 文件能通过 `python -m json.tool` 验证（格式正确）
- `cards_*.json` 每个文件是合法的 JSON 数组，每张牌的 `time_orientation` 三值和为1.0，`relational_direction` 两值和为1.0
- `feature_extractor.py` 对上述示例输入产出正确的特征 JSON
- `writing_layer.txt` 的 prompt 能让 Claude Sonnet 4.5 产出符合语气要求的解读（由项目负责人主观验收）
