# 塔罗牌主题空间数据结构说明

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

## 偏移分析逻辑

用户语料映射到同一维度空间后，计算与该牌 `theme_space` 各维度的偏差：
- **高偏移维度**（差值 > 0.3）= 分析重点，是心理信号
- **零偏移维度** = 可能是用户与牌的主题高度共鸣，或语料信号弱

例：The Tower 的 `agency.score = 0.1`（极度被动），若用户语料显示 `agency.score = 0.8`（强主动），偏移 = 0.7，说明用户在"崩塌主题"下系统性回避了被动位置，倾向于重建/掌控叙事。
