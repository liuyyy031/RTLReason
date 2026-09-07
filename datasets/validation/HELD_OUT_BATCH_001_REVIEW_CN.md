# Held-out Batch 001 独立盲审说明

## 批次状态

- 冻结清单：`datasets/validation/HELD_OUT_BATCH_001.json`
- 样本数量：20（basic 6、intermediate 9、hard 5）
- 候选模型：Hy3，经 Tencent Cloud TokenHub 调用
- 独立 request_id：20/20
- 候选来源：20/20 `real_hy3`
- Semantic Judge：20/20 `not_run`
- 可信 Evidence：20/20 同时附有 Simulation 和 Formal
- 候选/盲审包审计：67/67 全池配对，无预测或 Gold 字段泄漏
- 当前 Held-out Gold：20；本批已完成独立复核并全部晋升为 `adjudicated`

本批是“已见可信任务上的未见模型回答”，因此只能用于样本级 held-out 评估，不能单独证明对新任务的泛化能力。

## 审阅边界

审阅者只应打开：

1. 本表列出的 `.review.json`；
2. 对应 `datasets/tasks/<task_id>/` 下的可信 problem、interface semantics、behavioral obligations；
3. 必要时可信 testbench/formal harness，但不得用候选修改可信资产。

审阅期间不得打开：

- `datasets/validation/candidates/` 中对应完整候选记录；
- `runs/evaluator-v1.*`、Development 指标或历史错误分析；
- 任何 `evaluator_prediction`、预测 Root Error 或既有 Gold；
- 同任务的 Development 回答和人工标注。

每份样本需要独立复核并形成 `status = "adjudicated"` 的最终 annotation，之后才能执行：

```powershell
python -m rtlreason promote-case `
  --candidate datasets\validation\candidates\heldout-candidate-<slug>-001.json `
  --annotation datasets\validation\held_out_annotations\heldout-candidate-<slug>-001.human.json `
  --split held_out `
  --output datasets\validation\held_out\<slug>-001.json
```

全部 Gold 已在运行 v1.5 Semantic Judge 前冻结。看到 Held-out 结果后不得据此修改 v1.5 再重复报告同一测试集。

## 待审样本

| 层级 | 任务 | 盲审包 |
| --- | --- | --- |
| basic | `counter_enable_v1` | `review_packets/heldout-candidate-counter-001.review.json` |
| basic | `shift_register_v1` | `review_packets/heldout-candidate-shift-001.review.json` |
| basic | `rising_edge_detector_v1` | `review_packets/heldout-candidate-rising-edge-001.review.json` |
| basic | `saturating_counter_v1` | `review_packets/heldout-candidate-saturating-001.review.json` |
| basic | `serial_parity_v1` | `review_packets/heldout-candidate-serial-parity-001.review.json` |
| basic | `programmable_timer_v1` | `review_packets/heldout-candidate-timer-001.review.json` |
| intermediate | `round_robin_arbiter_v1` | `review_packets/heldout-candidate-arbiter-001.review.json` |
| intermediate | `ready_valid_slice_v1` | `review_packets/heldout-candidate-ready-valid-001.review.json` |
| intermediate | `sequence_detector_1011_v1` | `review_packets/heldout-candidate-sequence-001.review.json` |
| intermediate | `pulse_stretcher_v1` | `review_packets/heldout-candidate-pulse-001.review.json` |
| intermediate | `grant_hold_arbiter_v1` | `review_packets/heldout-candidate-grant-hold-001.review.json` |
| intermediate | `debounce_filter_v1` | `review_packets/heldout-candidate-debounce-001.review.json` |
| intermediate | `token_bucket_v1` | `review_packets/heldout-candidate-token-bucket-001.review.json` |
| intermediate | `interrupt_pending_v1` | `review_packets/heldout-candidate-interrupt-001.review.json` |
| intermediate | `stream_width_adapter_v1` | `review_packets/heldout-candidate-width-adapter-001.review.json` |
| hard | `fifo_sync_v1` | `review_packets/heldout-candidate-fifo-001.review.json` |
| hard | `request_ack_timeout_v1` | `review_packets/heldout-candidate-request-ack-001.review.json` |
| hard | `ready_valid_fifo2_v1` | `review_packets/heldout-candidate-fifo2-001.review.json` |
| hard | `dual_port_ram_sync_v1` | `review_packets/heldout-candidate-dual-port-ram-001.review.json` |
| hard | `apb_register_bank_v1` | `review_packets/heldout-candidate-apb-001.review.json` |

## 不得重采样的已知现象

- `sequence-001`：trusted Simulation 为 fail，bounded Formal 为 pass。该分歧已经写入盲审包，样本必须保留并由人工结合具体 Evidence 与任务义务裁决。
- `debounce-001`：有 3 条 `UNKNOWN_OBLIGATION` schema issue，原因是候选把 process item id 写入 `maps_to`。这是候选过程的可观察问题，不是任务资产或打包故障。

这些现象不能作为删除、替换或重新调用 Hy3 的理由。
