# 塔罗牌主题空间数据结构说明

> **版本说明**：以下是 P1 已实现的 v1 卡牌数据结构，当前 78 张牌 JSON 仍按此结构存储。
>
> v2 不立即修改卡牌数据；`theme_space` 将从"心理偏差标尺"降级为传统象征检索、覆盖检查和辅助判断。新的核心分析对象是用户如何重新组织象征材料。

每张牌的 JSON 结构如下：

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

## 字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `theme_space.emotional_tone.valence` | float 0–1 | 情绪效价：0=负面，1=正面 |
| `theme_space.emotional_tone.arousal` | float 0–1 | 激活度：0=平静，1=激动 |
| `theme_space.agency.score` | float 0–1 | 能动性：0=被动/受害者，1=主动/掌控者 |
| `theme_space.agency.direction` | enum | active / passive / ambivalent |
| `theme_space.time_orientation` | float 三值和为1 | 过去/当下/未来的权重分布 |
| `theme_space.conflict_harmony.score` | float 0–1 | 0=强冲突，1=强和谐 |
| `theme_space.relational_direction` | float 二值和为1 | 内向/外向导向权重 |
| `jungian_mapping.complex_signals` | list | 用户语料中出现这些信号时，提示该原型活跃 |

## v1 偏移分析逻辑（保留为基线）

用户语料映射到同一维度空间后，计算与该牌 `theme_space` 各维度的偏差：
- **高偏移维度**（差值 >= 0.3）= 分析重点，是心理信号
- **零偏移维度** = 可能是用户与牌的主题高度共鸣，或语料信号弱

例：The Tower 的 `agency.score = 0.1`（极度被动），若用户语料显示 `agency.score = 0.8`（强主动），偏移 = 0.7，说明用户在"崩塌主题"下系统性回避了被动位置，倾向于重建/掌控叙事。

上述数值未经真实标注数据或评审者一致性校准，因此只能作为启发式辅助信号，不能被表述为心理测量结果，也不能单独触发具体心理史、创伤来源或临床结论。

## v2 计划中的分析关系（尚未修改 JSON）

v2 将在独立的分析输出 schema 中记录下列关系，而不是立即改写 78 张牌数据：

- `convergence`：自然重合
- `omission`：选择性忽略
- `inversion`：意义反转
- `addition`：叙事添加
- `emotional_recoding`：情绪改写
- `agency_shift`：能动性改写
- `identification_shift`：认同移动
- `temporal_shift`：时间改写

每条关系必须同时引用用户原话和牌面/传统象征证据，并包含置信度、替代解释与反对证据。详细实施顺序见 `BUILD_INSTRUCTIONS.md`。

## v2 计划中的传统塔罗来源层（尚未修改 JSON）

现有 `standard_meaning.upright/reversed` 只能支持简短牌义，不能稳定承担独立 Traditional Tarot Layer。计划在技术修正阶段为每张牌增加或关联：

```json
{
  "source_tradition": "Rider-Waite-Smith",
  "waite_description": "",
  "waite_upright": "",
  "waite_reversed": "",
  "source_refs": [],
  "visual_inventory": [],
  "canonical_dynamic": "",
  "reversal_modes": [],
  "suit_rank_structure": "",
  "modern_psychological_rendering": ""
}
```

来源与使用原则：

- 以 A. E. Waite 的 *The Pictorial Key to the Tarot* 公版文本作为 RWS 原始依据
- 单独整理 Pamela Colman Smith 图像中可观察的视觉符号
- 原始文本作为来源基线，不直接复制成用户文案
- `canonical_dynamic` 与 `modern_psychological_rendering` 必须可追溯到来源或明确标记为 Liminal 的现代解释
- `reversal_modes` 优先表达 `blocked`、`internalized`、`excessive`、`misdirected`、`delayed`
- canonical traditional reading 不读取用户问题或自由联想
- situated traditional reading 只增加用户问题，不读取 Pass 1 心理结论
