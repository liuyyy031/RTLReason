# RTLReason 人工 Gold 标注指南 v1.0

## 1. 独立性与盲审

标注者可以审查 Hy3 的真实输出，但不能让被评 Hy3 或同一次 Judge 调用决定 Gold 标签。标注前只打开 `review_packets/` 中的盲审包和对应任务的可信资产，不查看候选记录中的 `evaluator_prediction`、既有归因结果或指标结果。

可信资产包括 `problem.md`、`interface_semantics.json`、`behavioral_obligations.yaml`、独立 reference model、testbench、formal harness 和 EDA evidence。参考 RTL 只是帮助核对语义，不能把内部微架构当成唯一正确答案。

## 2. 标注顺序

1. 先核对任务、接口语义和 behavioral obligations。
2. 独立判断最终 RTL 是否满足可观察行为，填写 `gold_rtl_correct`。
3. 逐项审查 S1–S5 claim，独立判断整个显式过程是否正确，填写 `gold_process_correct`。
4. 若过程错误，定位最早能够解释后续错误的过程条目，填写首错阶段和根错误。
5. 按 `datasets/error_taxonomy.yaml` 填写 L1/L2。
6. 只标注关键因果父边，不把“映射到同一 obligation”本身当作因果依赖。
7. 填写受影响 obligation。RTL 正确但过程错误时，该数组可以为空。
8. 保存标注文件后才可解除盲审，由工具将人工 Gold 与评测器预测合并。

## 3. 关键字段判定

- `gold_rtl_correct`：可信仿真与 Formal 的结论；工具不可用或证据不足时，不应强行裁决，应补证据后再标注。
- `gold_process_correct`：所有对正确实现有实质影响的 S1–S5 claim 是否正确。最终 RTL 正确不代表过程一定正确。
- `gold_first_error_stage`：根错误所在阶段，例如 `S3`。
- `gold_root_error`：最早的根错误条目，例如 `S3.2`，不是最显眼的下游症状。
- `gold_parent_dependency`：人工确认的关键直接因果边。普通样本中的 Evaluator-Inferred Graph 仍然只是预测。
- `gold_affected_obligation`：由错误实际破坏的可信行为义务；不要仅凭文本共同提及而添加。

## 4. 正确 RTL / 错误过程

这是合法且重要的一类样本。例如某个 S3 claim 漏掉满/空或同时握手分支，但 S5 RTL 另外实现了正确分支。此时应标注：

- `gold_rtl_correct = true`；
- `gold_process_correct = false`；
- 根错误指向错误的过程条目；
- 若没有任何 RTL 行为义务被破坏，`gold_affected_obligation = []`。

## 5. 裁决状态

- `single_annotated`：一名独立标注者完成，可进入 development set。
- `adjudicated`：至少两份独立标注发生分歧后完成裁决，或按项目约定完成双人复核；只有此状态可进入 held-out set。

标注者必须填写稳定的 `annotator_id` 和 `guideline_version`。模板中的 `null` 布尔值必须替换为明确的 `true` 或 `false`。
