# RTLReason M5 实验协议 v1.0

## 1. 目标

M5 用独立人工 Gold 验证三件事：最终 RTL 判断是否可靠、过程正确性判断是否可靠、Root Error 与关键依赖定位是否可靠。真实 Hy3 输出可以进入数据集，但被测 Hy3、同一次 Hy3 Judge 和 RTLReason 推断图都不能决定 Gold。

## 2. 数据划分

- `development`：用于发现评测器错误、修正规则和校准 prompt。允许 `single_annotated` 或 `adjudicated`。
- `held_out`：只用于冻结版本后的最终评测，必须为 `adjudicated`。不得根据 held-out 结果修改 prompt、依赖规则、阈值或题目资产后继续报告同一测试集结果。
- 同一个 Hy3 回答、同一人工注错来源的近重复变体不得跨 development 与 held-out。
- 任务层级由 `datasets/task_manifest.json` 冻结，不根据实验结果临时调整。

## 3. 盲审

标注者先查看 `review_packets/` 盲审包和可信任务资产，不查看 `evaluator_prediction`。标签锁定后，才使用 `promote-case` 将 Gold 与预测放入同一记录。正确 RTL/错误过程、错误 RTL/上游错误、完全正确过程都应纳入。

## 4. Baseline

- `EDA-only`：以最终 RTL 判断代替过程正确性，不提供 Root Error。它用于证明仅看代码通过无法发现“正确 RTL/错误过程”。
- `Semantic-only`：使用逐项语义 Judge 的最早错误，不使用依赖图和 Evidence Attribution，也不预测关键依赖。
- `Full RTLReason`：使用 Semantic、冻结的 Evaluator-Inferred Dependency Graph 和 EDA Evidence Attribution。

三个方法使用同一 Gold 记录与同一 EDA RTL 结论，禁止为不同方法选择不同样本。

## 5. 核心报告

总体和 basic/intermediate/hard 每层分别报告：

- Final RTL Accuracy；
- Process Correctness Accuracy 与 Macro-F1；
- Stage-level First Error Localization Accuracy；
- Process False Positive Rate；
- Correct-RTL/Wrong-Process Recall；
- Error Type L1 Macro-F1；
- Root Error Accuracy；
- Critical Dependency Precision、Recall、F1 和 Exact Accuracy。

分母为零的指标必须显示 `null`，不能写成 0。报告同时给出每层 case count，避免小样本百分比造成误导。

## 6. 分模块错误分析

对每个 Full RTLReason 错误案例依次判断：

1. Semantic Evaluator 是否把过程条目判错；
2. Dependency Builder 是否建立了错误或遗漏的关键边；
3. Attribution 是否在给定图和 evidence 下选错根因；
4. EDA evidence 是否映射到了错误 obligation；
5. Gold 是否存在标注分歧并需要再次裁决。

普通样本的 Evaluator-Inferred Graph 始终是预测。只有 Gold Validation Set 中人工标注的关键依赖可用于计算依赖准确率。

## 7. 评测器版本快照

人工 Gold 一旦晋升不得为适配新评测器而改写。Development 校准后，使用 `snapshot-gold` 将同一冻结候选的新 `report.json` 与原 Gold 标签组合成实验快照；命令会校验重评的 `process.json` 与 Gold 中的候选完全一致，并记录 Gold/report 哈希、Semantic Prompt 版本和 Dependency Graph digest。

Baseline 必须基于同一评测器版本的快照目录计算。原始 Gold 记录保留首次预测，仅用于审计，不用手工覆盖其中的 `predicted_*` 字段。
