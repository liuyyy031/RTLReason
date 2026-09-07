# RTLReason 人工 Gold 标注指南 v1.1

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

### 3.1 S4 Candidate Property 的 reset 作用域

为避免把正确的自然语言性质因接口作用域约定不同而误判，v1.1 冻结以下规则：

1. 描述普通运行行为的 S4 property 默认只在相关采样沿 `rst` 未断言时评价，等价于形式验证中的 `disable iff (rst)`。不能仅因条目没有重复写出 `!rst` 就判为错误。
2. 明确描述 reset、reset release、包括 reset 在内的所有周期，或声称某条件是全局唯一原因的性质，按其字面作用域评价，不适用上述默认豁免。
3. 默认 reset 作用域只排除当前 reset 采样沿，不自动补全历史有效性。涉及 previous、past、delay、首次 reset 后样本或跨周期因果的性质，必须确认所引用历史属于当前 reset epoch；必要时要求 past-valid 或无中间 reset 条件。
4. 默认 reset 作用域不会自动补充 `enable`、`load`、`valid/ready`、优先级、地址有效性或 simultaneous-operation 条件。这些条件缺失并存在非 reset 反例时，仍是实质性过程错误。
5. S1～S3 的局部 transition 描述可以结合同阶段已经明确给出的优先级上下文理解；但任何条目若与该上下文直接矛盾，仍应判错。
6. 当旧 Root Error 仅由缺少显式 reset guard 得出时，应撤销该 Root 并继续检查后续条目，不能直接假定整个过程正确。

这一定义只改变性质的默认作用域，不改变 frozen interface semantics、behavioral obligations 或 trusted EDA evidence。

## 4. 正确 RTL / 错误过程

这是合法且重要的一类样本。例如某个 S3 claim 漏掉满/空或同时握手分支，但 S5 RTL 另外实现了正确分支。此时应标注：

- `gold_rtl_correct = true`；
- `gold_process_correct = false`；
- 根错误指向错误的过程条目；
- 若没有任何 RTL 行为义务被破坏，`gold_affected_obligation = []`。

## 5. 裁决状态

- `single_annotated`：一名独立标注者完成，可进入 development set。
- `adjudicated`：至少两份独立标注发生分歧后完成裁决，或按项目约定完成双人复核；只有此状态可进入 held-out set。

标注者必须填写稳定的 `annotator_id` 和 `guideline_version`。自 v1.1 起，列入 `readjudication/v1.1-s4-scope.json` 的旧 S4 标注只有在 `guideline_version = "1.1"` 下重新裁决后才能晋升。模板中的 `null` 布尔值必须替换为明确的 `true` 或 `false`。
