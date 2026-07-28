# Liminal v1 回归基线

此目录记录 Phase 0 冻结的 v1.1 引擎基线，用于后续 Phase 1–6 的行为比较。

## Canonical v1 口径

- `analysis_layer_output` 包含三个依次展示的部分，并直接面向用户。
- `writing_layer.txt` 是已保留的历史实验文件；v1.1 合同将写作层标记为 deferred。
- 旧版“分析层只供写作层使用、不得展示”的 schema 已废弃。
- 高偏移维度的边界统一为 `delta >= 0.3`。
- `theme_space` 数值是启发式辅助信号，不是经校准的心理测量。

## 基线范围

`manifest.json` 记录以下内容的 SHA-256：

- v1.1 分析 schema
- 分析与写作 prompt
- 三份既有 trial reading

哈希用于确认参照版本身份，不要求后续 v2 工作文件继续匹配这些哈希。基线也不代表 v2 的目标质量。

现有 trial reading 只被读取并记录哈希，没有移动、覆盖或改写。
