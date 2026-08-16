# Liminal 引擎构建交接文档

> **状态说明（2026-08-17）**
>
> 本文档前半部分定义 v2 目标架构与代码改动顺序；后半部分保留 P1 已完成的 v1 文件说明，作为基线。
> v1.1 继续作为冻结基线。v2 按独立目录和契约增量实现，不覆盖 v1 文件；各阶段的“可测试版本”与“生产完成”必须分别标记。

## 项目背景

产品名：**Liminal**

定位：以塔罗牌为象征刺激物，分析用户如何重新组织象征材料，并通过荣格式扩充、补偿与超越功能生成第三意义

核心机制：用户读牌 → 系统读取用户如何重写牌 → 传统象征回来与个人读法发生对话

数据结构说明：见 `engine/tarot_card_schema.md`

---

## v2 核心原则

### 1. 技术对象是"象征转换关系"，不是用户与标准答案的距离

传统牌义不是绝对坐标，用户读法也不是偏离标准的错误。引擎需要识别：

| 关系类型 | 含义 |
|---|---|
| `convergence` | 用户未经提示自然说出牌的核心主题 |
| `omission` | 用户未提及显著象征；必须谨慎处理，不能自动等同于回避 |
| `inversion` | 用户把象征改写为其对立、反面或相反功能 |
| `addition` | 用户添加牌面不存在的动机、关系、身份或结局 |
| `emotional_recoding` | 用户改变同一象征的情绪基调 |
| `agency_shift` | 用户改变人物的主动/被动位置 |
| `identification_shift` | 用户在"我/他/旁观者"之间移动 |
| `temporal_shift` | 用户改变象征的过去/当下/未来方向 |

`theme_space` 继续作为检索、覆盖检查和辅助信号使用；未经校准的 float 与 delta 不得单独触发心理结论。

### 2. 对照是证据，荣格式解读是主要价值

每条深层解释必须保留完整证据链：

```text
原始联想
  → 牌面事实
  → 象征转换
  → 单次会话中的心理过程模式
      （思考顺序 / 情绪功能 / 适应价值 / 当前代价）
  → 首选解释
  → 替代解释 / 反对证据 / 无法判断
  → 牌的补偿
  → 问题情境中的激活方式
  → 第三意义与完整回答
```

优先使用的荣格概念依次为：投射、情结自主性、补偿、阴影、扩充、超越功能。原型命名后置，不能把荣格理论降格为固定人物标签分类。

象征转换清单本身不是最终洞见。Pass 1 必须在证据允许时把多个转换组织成一个**过程型心理模式**：用户先做什么判断、随后检查或修正什么、这个顺序在调节何种不确定性、它在什么情况下有帮助、在当前会话中可能造成什么代价。

认识等级严格分层：

1. `observation`：可核验的原话或牌面事实
2. `session_pattern`：本次联想中重复或连贯出现的组织方式
3. `situational_hypothesis`：该模式在揭晓问题中的可能作用
4. `trait_hypothesis`：跨多次会话稳定重复后才可提出
5. `developmental_origin`：需要用户历史材料或专业评估；单次塔罗联想不得推断

单次阅读默认只能形成前三级。不得从一个显眼元素直接推断稳定人格，也不得从风险语言反推成长环境、创伤来源或长期生活条件。

### 3. 两次递进解读：输入隔离，但 Pass 1 直接参与体验

**Pass 1：问题盲态并直接展示**

- 系统在此之前不采集 `user_question`
- 不得接收 `user_question`
- 先抽取象征事实，再识别转换关系，最后生成荣格式解释
- 将有共同证据的转换组织为过程型心理模式，至少描述思考顺序、情绪功能、适应价值与当前可能代价
- 输出首选解释、替代解释、支持证据、反对证据、置信度和无法判断
- 心理模式只能标记为 `session_pattern`；不得写成稳定 trait，不得推断具体童年经历、成长环境、创伤来源或临床诊断
- 读取独立生成的 canonical traditional reading，形成牌的补偿与暂时的第三意义
- 冻结结果后立即展示给用户

**问题揭晓**

- 用户阅读 Pass 1 后才输入刚才一直带着的具体问题
- 允许用户按此刻最真实的版本表达问题
- 引导文案必须说明：不需要让问题与 Pass 1 保持一致
- 记录 `question_shift`：`unchanged`、`clarified`、`shifted_focus`、`different_question`

**Pass 2：情境与共时性整合**

- 输入为冻结的 Pass 1 输出 + `user_question` + situated traditional reading
- 标明哪些发现来自盲态，哪些连接来自问题情境
- 为每个高置信度 Pass 1 模式记录 `integrated`、`held` 或 `not_relevant`，不得让关键发现无声消失
- 围绕一个中心心理轴线解释：模式如何在当前问题中被激活、为何形成困难、牌如何补偿该模式
- 如问题发生变化，区分开始时的心理焦点与揭晓时的表达
- 解释牌如何补偿、扩充或挑战用户当前意识立场
- 内部形成第三意义和有边界的方向回答；用户侧只呈现一篇完整的综合解读和一个带走的问题
- 不得修改 Pass 1 的证据或为了贴合问题重写盲态结论
- 不得用与 Pass 1 心理模式无关的通用建议占据主要篇幅；新增判断必须能追溯到冻结模式、用户问题或 situated traditional reading

Pass 1 是反思性脚手架，不是等待 Pass 2 才有意义的内部草稿。它对用户后续问题表达的影响属于产品相互作用的一部分。因此 Pass 2 不是 Pass 1 的独立验证；评测必须拆开测量 Pass 1 独立质量、问题澄清作用与 Pass 2 增量价值。

### 4. 两次主要用户输出

**Pass 1（约 600–900 个中文字符）**

1. 原始联想：可核验原话
2. 象征转换：牌面提供了什么，用户如何重写
3. 心理过程模式：思考顺序、情绪功能、适应价值与当前可能代价
4. 牌的补偿：canonical traditional reading 为当前视角带来什么另一面
5. 暂时的第三意义：在不知道现实问题时已经形成的新心理位置

**Pass 2（篇幅由完整性测试校准，初始目标约 600–900 个中文字符）**

后台分析保留盲态发现、问题变化、情境化牌义、继承映射、第三意义和方向回答等独立字段；用户界面不把这些字段机械拆开。最终只显示：

1. 一篇连续的综合解读：从冻结的心理模式出发，说明它如何进入当前问题、为何形成张力、牌如何补偿，并给出有边界的完整回答
2. 一个具体的带走问题

### 5. 独立 Traditional Tarot Layer

传统塔罗层不依赖 Codex Tarot 插件的私有实现。第一版以 A. E. Waite 的 *The Pictorial Key to the Tarot* 公版文本、Pamela Colman Smith 视觉符号表和现有 78 张牌数据为基础。

**canonical 模式**

- 输入：卡牌、正逆位
- 不读取用户问题、自由联想或 Pass 1
- 输出：稳定牌义、视觉象征、正逆位机制、来源引用

**situated 模式**

- 输入：卡牌、正逆位、用户揭晓的问题
- 不读取自由联想或 Pass 1 心理结论
- 输出：牌在具体问题中的角色、实际张力、有边界的方向和反思点

正逆位不得只写成正位的好/坏版本。优先使用：

- `blocked`
- `internalized`
- `excessive`
- `misdirected`
- `delayed`

传统层不得做确定性预测、心理诊断或无依据的单一根因推断。

### 6. 案例用于验证契约，不用于生成通用规则

单次 Wizard-of-Oz 试读只能证明某条输出链在一个案例中可能有效。代码、schema 和 prompt 不得固化该案例的具体牌面元素、问题领域、心理主题或答案措辞。

每次从人工试读提炼规则时必须通过三项检查：

- **抽象检查**：规则描述的是输入与证据关系，而不是某张牌或某位参与者的内容
- **反事实检查**：换牌、换语料或换问题后，规则仍然成立，但结论会随证据改变
- **来源检查**：稳定 trait 与发展来源不会由单次样本产生

---

## v2 代码改动计划（执行中）

截至 2026-08-17，已达到下一轮人工验证前的 Phase 3 技术闸门：

- Phase 1：v2 alpha schema、过程型心理模式、证据引用和认识边界运行时校验已实现
- Phase 2：78 张牌可通过隔离接口生成 provisional canonical reading；situated 请求/输出契约已实现。Waite 原文补全与逐牌人工审校仍属生产完成条件
- Phase 3：事实/转换、过程模式、补偿、写作四阶段 prompt 已隔离；请求构建、结构校验、组装、SHA-256 冻结及防篡改检查已实现
- 当前停止点：更换牌与问题进行真人 Pass 1 测试；测试通过后再进入 Phase 4

按以下顺序实施；每一步通过测试后再进入下一步。

### Phase 0：修复现有契约

1. 清理 `analysis_schema.json` 第 165 行开始拼接的旧版内容，使其恢复为合法 JSON
2. 冻结 v1 schema 与三份 trial reading 为回归基线
3. 统一 `> 0.3` / `>= 0.3` 的历史阈值表述
4. 记录 v1 中"分析层直接展示"与"写作层输入"的架构冲突

### Phase 1：新增关系运算与传统塔罗 Schema

建议新增顶层对象：

```json
{
  "symbolic_observations": [],
  "symbolic_transformations": [],
  "psychological_patterns": [],
  "jungian_hypotheses": [],
  "traditional_reading": {},
  "compensatory_reading": {},
  "epistemic_limits": {},
  "question_shift": null
}
```

`psychological_patterns` 至少包含：`sequence`、`emotional_function`、`adaptive_value`、`current_cost`、`evidence_transformation_ids`、`confidence`、`alternative_explanation`、`disconfirming_evidence`、`scope=session_pattern`。任何发展来源只能进入 `epistemic_limits.unsupported_inferences`。

每条 `symbolic_transformations` 至少包含：

```json
{
  "type": "inversion",
  "user_evidence": ["被这一堆木头围困住了"],
  "card_evidence": ["wands as defended boundary / record of prior battles"],
  "description": "保护结构被体验为囚禁结构",
  "confidence": "high",
  "alternative_explanation": "也可能只是依据画面构图做空间描述",
  "disconfirming_evidence": []
}
```

### Phase 2：实现 Traditional Tarot Layer

1. 导入并整理 Waite 公版基线与来源引用
2. 为每张牌补充视觉符号、正逆位机制和现代心理动态
3. 建立 canonical prompt 与结构化输出
4. 建立 situated prompt 与结构化输出
5. 验证两种模式都不会读取用户自由联想或心理结论

### Phase 3：拆分 Pass 1 内部步骤

1. 事实提取 prompt：只抽取注意、忽略、添加和语言变化
2. 关系分类 prompt：只判断象征转换，不做心理解释
3. 过程模式 prompt：把多个有证据关系组织为思考顺序、情绪功能、适应价值与当前代价；禁止从单次会话推断 trait 或发展来源
4. 荣格解释 prompt：读取冻结事实、关系与过程模式，生成有证据边界的心理假设
5. 补偿整合：读取 canonical traditional reading，生成牌的补偿与暂时的第三意义
6. 为各步骤分别建立 schema 校验与多牌型回归样本
7. Pass 1 冻结后直接写作并展示

### Phase 4：实现问题揭晓与 Pass 2

1. 新增问题揭晓 UI 与不诱导一致的引导文案
2. 保存 `question_shift`
3. 新增 context integration prompt
4. 读取 situated traditional reading
5. 建立 Pass 1 模式继承映射；每个高置信度模式必须标记 `integrated`、`held` 或 `not_relevant`
6. 围绕一个中心轴线说明模式在当前问题中的激活、困难与牌的补偿
7. 输出内部结构化第三意义、方向回答，以及用户侧“完整解读 + 结尾问题”
8. 检查 Pass 2 是否覆盖、复述、偷改或无声丢弃 Pass 1

### Phase 5：重建双阶段写作/展示层

1. 写作层只组织已有判断，不新增判断
2. Pass 1 直接展示，并将"证据铰链"做成短而清楚的模块
3. 在 Pass 1 与问题输入之间加入明确的递进台阶
4. Pass 2 以一篇连续文本展示增量整合，不把内部字段渲染成互相割裂的模块
5. 使用不同确定度表达观察、解释与假设

### Phase 6：评测 Harness

- 同语料换牌
- 同牌换语料
- Pass 1 在问题揭晓前的独立质量
- 问题变化：没变 / 更具体 / 重心变化 / 成为另一个问题
- 用户是否感到被诱导强行贴合
- Pass 2 相对 Pass 1 的增量价值
- 心理模式辨识度：用户能否准确复述“我的思考/情绪如何运作”
- Pass 1 → Pass 2 继承度：最终核心判断能否回到冻结模式与原始证据
- 解释链完整度：观察、过程、情境激活、补偿和回答之间是否连续
- 用户盲配自己的解读
- 人工评审证据支持度、解释深度和越界程度
- 共鸣评分与数日后意义评分

---

## v1 已有引擎构建任务清单（P1 基线）

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
