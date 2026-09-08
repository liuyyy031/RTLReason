# Held-out Batch 002 一次性评测结果

Batch 002 在10份人工 Gold 全部完成并冻结后，使用冻结的 RTLReason evaluator v1.5 进行了一次性评测。Semantic Judge 使用 Hy3，评测输入不包含人工 Gold，评测后未修改 Gold 标签或 evaluator 规则。

本批候选并分为8份 Hy3 输出和2份 `hy4-preview` 超时恢复输出。后两份只作为跨模型补充结果，不计入纯 Hy3 的主结果。

## 总体结果

| 方法 | RTL准确率 | Process准确率 | Process Macro-F1 | Root准确率 | Dependency Micro-F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| EDA-only | 0.9000 | 0.6000 | 0.3750 | 0.0000 | — |
| Semantic-only | 0.9000 | 0.8000 | 0.7619 | 0.5000 | — |
| RTLReason完整流程 | 0.9000 | 0.8000 | 0.7619 | 0.5000 | 0.3636 |

完整流程对“RTL正确但过程错误”的召回率为0.6667；首错阶段定位准确率为0.5000。结果再次表明，单靠EDA无法发现最终RTL正确但显式推理过程错误的样本，而Semantic Evaluator能补充这部分能力。

## 按候选模型分层

| 候选模型 | 样本数 | Process准确率 | Process Macro-F1 | Root准确率 | Dependency Micro-F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hy3 | 8 | 0.8750 | 0.7949 | 0.5000 | 0.2857 |
| hy4-preview | 2 | 0.5000 | 0.6667 | 0.5000 | 0.5000 |

`hy4-preview` 只有2个样本，不应据此进行模型优劣比较。

## Case结果

- 6个Gold过程正确样本均被正确判为过程正确。
- `gray-code-001`：正确识别首错 `S4.2`，但L1错误类型与Gold不一致。
- `spi-tx-001`：正确识别首错 `S4.4` 及 `Property` 类型。
- `multiply-ctrl-001`：漏检Gold首错 `S1.4`。
- `uart-rx-001`：漏检 `S5.1` 的合法大参数宽度问题；配置内Simulation/Formal通过，因此也暴露出当前trusted EDA参数覆盖的边界。

## 解释边界

Batch 002只有10个样本，按难度或模型切分后的子集更小，因此分层数值主要用于错误分析，不用于声称统计显著性。后续规则调整只能进入新的development版本或下一批预注册评测，不能回改v1.5后重新报告本批为同一held-out结果。
