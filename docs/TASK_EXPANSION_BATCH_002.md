# RTLReason Task Expansion Batch 002

## 1. 目的与实验地位

Batch 002 将可信任务从20道扩展到30道，并用于建设 task-level challenge held-out。新增任务必须在任何 Hy3 候选生成前完成可信资产建设、独立审查和哈希冻结。

本批任务是根据现有覆盖盲区主动设计的 challenge set，不是从真实 RTL 任务总体中随机抽样，因此可以检验跨任务语义泛化，但不能据此估计无偏总体准确率。

Batch 001 的标签和预测不得用于修改 v1.5。若开发 v1.6，只能使用 Development、单元测试和另建的开发样本；v1.6 必须在生成或审阅 Batch 002 的 Hy3 回答前冻结。Batch 002 完成 Gold 后，对冻结版本只进行一次正式评测。

## 2. 预注册任务

原建议中的 `skid_buffer_v1`、`priority_hold_v1` 和 `programmable_divider_v1` 分别与现有 `ready_valid_slice_v1`、`grant_hold_arbiter_v1` 和 `programmable_timer_v1` 高度重叠，已从本批移除。

| task_id | 层级 | family | 核心可观察行为 | 关键边界 |
| --- | --- | --- | --- | --- |
| `gray_code_counter_v1` | basic | encoding_counter | enable控制的模计数及Gray编码输出 | reset、hold、wrap、相邻码单比特变化 |
| `signed_alu_flags_v1` | basic | combinational_alu | add/sub/and/xor及Z/N/C/V标志 | signed overflow、sub no-borrow、全零与最高位 |
| `register_file_bypass_v1` | intermediate | register_file | 同步写、组合双读、同周期write-through | 双读端口、地址冲突、reset/写优先级 |
| `axi_stream_packet_counter_v1` | intermediate | stream_monitor | 仅在valid/ready握手时统计beat和TLAST packet | stall、TLAST、clear与transfer同拍、计数饱和或wrap语义 |
| `spi_tx_v1` | intermediate | serial_protocol | MODE0、MSB-first、固定分频的单字节发送 | start/busy、首末bit时序、done脉冲、busy期间start |
| `cache_tag_lookup_v1` | intermediate | associative_lookup | 多路valid/tag比较并返回hit/way/data | miss、单hit、多hit确定性优先级 |
| `credit_flow_control_v1` | intermediate | flow_control | credit驱动的发送接受及credit return | zero/full、consume+return、重复return禁止溢出 |
| `async_handshake_v1` | hard | cdc_protocol | request/ack toggle跨双时钟域传递单个事件 | 独立reset、同步级、源端重发限制、禁止丢失/重复 |
| `uart_rx_v1` | hard | serial_protocol | 固定参数8N1接收、中心采样、data_valid与framing error | start确认、8位次序、stop、背靠背frame |
| `multicycle_multiply_ctrl_v1` | hard | multicycle_datapath | unsigned乘法事务的start/busy/done/result提交 | 固定迭代数、busy期间start、结果保持、完成边沿 |

目标分布为2道basic、5道intermediate、3道hard。`register_file_bypass_v1` 作为第一批的lower-intermediate模板题，但在正式manifest中归入intermediate。

## 3. 分批实施顺序

### 第一批：生产流水线模板

1. `gray_code_counter_v1`
2. `axi_stream_packet_counter_v1`
3. `register_file_bypass_v1`

三题分别覆盖编码状态、流协议边界和存储冲突。第一批全部通过准入检查后，才能复制结构到后续任务。

### 第二批：中等复杂度扩展

1. `signed_alu_flags_v1`
2. `spi_tx_v1`
3. `cache_tag_lookup_v1`
4. `credit_flow_control_v1`

### 第三批：高风险时序任务

1. `async_handshake_v1`
2. `uart_rx_v1`
3. `multicycle_multiply_ctrl_v1`

若 OSS CAD Suite 的多时钟Formal不能形成清晰、可复现的数字时序模型，`async_handshake_v1` 不得降格准入；应保留为blocked task或以另一个非CDC任务替换，并更新预注册版本与理由。

## 4. 每题必须具备的资产

目录严格沿用现有任务格式：

```text
datasets/tasks/<task_id>/
├── problem.md
├── interface_semantics.json
├── behavioral_obligations.yaml
├── difficulty.json
├── provenance.json
├── verification.json
├── reference_rtl/<module>.sv
├── testbench/tb_<module>.sv
└── formal/<module>_formal.sv
```

此外，如果任务存在适合架构无关计算的状态模型，应在 `src/rtlreason/reference/` 增加Python Reference Model及对应单元测试。Reference RTL只能是可信验证入口，不能成为候选必须采用的微架构。

## 5. Interface Semantics 必须冻结的内容

每题至少明确：

- 端口、宽度、参数有效范围；
- clock edge和输入采样/输出观察时点；
- reset同步性、有效电平、优先级及reset后可观察值；
- current-state与next-state定义；
- acceptance条件和被拒绝输入的因果语义；
- 同拍操作优先级；
- hold/stability具体约束哪些状态或输出；
- 组合输出、注册输出及读写延迟；
- wrap、saturate、clamp或error行为；
- 未定义/不保证行为，避免测试隐含微架构要求。

`async_handshake_v1` 还必须声明两个时钟的Formal调度假设和reset关系。它只验证数字协议安全性，不宣称验证亚稳态、MTBF、物理CDC时序或真实硅可靠性。

## 6. Behavioral Obligations 粒度

每题建议6至10个obligations，覆盖适用的：

- reset；
- normal operation；
- acceptance/gating；
- boundary；
- simultaneous operation；
- hold/stability；
- timing；
- ordering/data correctness。

Obligation必须描述外部可观察行为，不能规定内部寄存器命名、状态编码或某一种Reference RTL结构。

## 7. Formal 的 Safety/Liveness 边界

Formal Core默认只纳入Safety：

- 非法输入不会被接受；
- 接受事件发生时，状态更新正确；
- 输出transfer发生时，数据等于最早尚未消费的合法输入；
- stall期间规定的输出保持稳定；
- occupancy/counter/credit范围一致；
- reset、优先级和同时操作正确；
- pulse、边沿和固定有限窗口时序正确。

禁止无条件写入：

```text
accepted_input -> eventually output_transfer
request -> eventually service
start_bit -> eventually complete_frame
```

如果未来确需Liveness，必须单独列出fairness/eventual-progress assumptions并与Safety指标分开。对于buffer/stream任务，MVP只验证“合法输出发生时的数据、顺序和唯一性”，不要求下游永久阻塞时仍最终消费。

## 8. Simulation 与 Formal 覆盖要求

Directed Simulation至少覆盖：

1. normal path；
2. reset与reset priority；
3. boundary；
4. simultaneous operation（若适用）；
5. parameter minimum/maximum或代表性边界；
6. hold/stall；
7. 至少一个连续事务或背靠背事务。

Formal Harness要求每个核心Safety obligation至少有可追踪的assertion/cover或明确的bounded checker。不能用一次总失败不加区分地声称所有obligation均被击中。

## 9. Known-bad Regression

每题准入前至少准备2个彼此独立的已知错误：

- 一个普通功能/边界错误，trusted Simulation必须捕获；
- 一个时序、并发或状态不变量错误，Formal必须捕获，Simulation也可同时捕获。

每个mutation必须记录：

- mutation id；
- 被破坏的精确语义；
- 预期失败obligation；
- 实际Simulation/Formal结果；
- 失败是否发生在编译、运行或property检查阶段。

不得把编译不通过的简单语法错误作为每题唯一的known-bad。

## 10. Trusted Task Admission Checklist

每题只有全部满足下列条件才能加入 `datasets/task_manifest.json`：

- [ ] Problem与Interface一致；
- [ ] Interface可观察时序无未冻结歧义；
- [ ] Obligations覆盖主要行为且不绑定Reference微架构；
- [ ] Reference RTL编译通过；
- [ ] Reference Simulation通过；
- [ ] Reference Formal Safety通过；
- [ ] 每个核心obligation具有可追踪验证证据；
- [ ] 至少2个known-bad按预期被捕获；
- [ ] reset边界已验证；
- [ ] simultaneous operation已验证（若适用）；
- [ ] parameter边界已验证（若适用）；
- [ ] 独立审阅者确认Problem/Interface/Obligation/Reference一致；
- [ ] Hy3尚未生成该题候选；
- [ ] 所有可信资产SHA-256已冻结。

准入状态变化：

```text
planned -> assets_complete -> independently_reviewed -> trusted_frozen
```

只有 `trusted_frozen` 才能加入正式manifest并允许Hy3生成候选。

当前进度（2026-09-07）：

- `gray_code_counter_v1`、`axi_stream_packet_counter_v1` 和
  `register_file_bypass_v1` 均已完成Reference Model、Reference RTL、
  Simulation、Formal Safety和每题2个known-bad的技术验证；
- 独立审阅者 `LT001` 于2026-09-07确认三题Problem、Interface、Obligations
  和Reference RTL一致，无需修改；
- 第一批3道题已晋升为 `trusted_frozen` 并加入正式manifest；
- Batch 002的10道新增题均已冻结；Hy3候选生成仍等待独立的生成计划、
  模型配置和评测器快照冻结，因此当前继续禁止；
- 第二批的 `signed_alu_flags_v1` 已完成WIDTH=4全输入穷举、
  WIDTH=2最小参数、组合Formal及2个独立flag故障验证；
- 独立审阅者 `LT001` 确认该题无需修改，已晋升为
  `trusted_frozen` 并加入正式manifest；
- `spi_tx_v1` 已达到 `assets_complete`：MODE0逐边沿时序、MSB-first、
  HALF_PERIOD最小参数、busy期start忽略、完成边沿和done脉冲已经
  Simulation/Formal及2个known-bad验证；首轮审阅要求补充独立 `O_IDLE`，
  补充quiescent-idle语义、仿真检查和Formal assertion后复审通过，
  已晋升为 `trusted_frozen`；
- `cache_tag_lookup_v1` 已达到 `assets_complete`：valid-tag匹配、最低way
  优先、多命中、miss输出、packed way顺序及最小WAYS参数已经Reference
  Model、Simulation/Formal和2个known-bad验证；首轮审阅指出 `WAY_WIDTH`
  不应是公开可覆盖参数，现已改为由 `WAYS` 直接派生并完成全套复验，
  独立复审通过后已晋升为 `trusted_frozen`；
- `credit_flow_control_v1` 已达到 `assets_complete`：current-state发送接受、
  consume+return同拍、空时禁止return lookahead、满时return替换已消费credit、
  饱和和最小MAX_CREDITS参数均通过Reference Model、Simulation/Formal及
  2个known-bad验证；首轮审阅补充 `acceptance.return` 的 `!rst` guard后，
  独立复审通过后已晋升为 `trusted_frozen`；
- `async_handshake_v1` 已通过风险门槛：使用固定、可复现的双时钟数字调度
  （source每个formal microstep切换，destination每两个microstep切换）的
  multiclock BMC depth 32；其范围明确限于数字协议安全，且2个CDC known-bad
  均被Simulation/Formal检出，独立审阅通过后已晋升为 `trusted_frozen`。
- `uart_rx_v1` 已达到 `assets_complete`：8N1 start中心确认、8位LSB-first
  采样、stop中心采样、false start、单周期valid和framing error均通过
  Simulation及depth 96 Formal oracle；2个known-bad均被双路径检出；首轮
  审阅已澄清 `O_LSB_FIRST` 的最终字节提交语义，现等待复审。
- `uart_rx_v1` 复审通过后已晋升为 `trusted_frozen`；
- `multicycle_multiply_ctrl_v1` 已达到 `assets_complete`：接受边沿不迭代、
  WIDTH个busy边沿、busy期间start忽略、原子结果提交、done脉冲和WIDTH=1
  边界均通过Simulation/Formal及2个known-bad验证；独立审阅通过后已晋升
  为 `trusted_frozen`，Batch 002可信资产建设完成。
- 逐项准入证据和SHA-256记录见各任务目录下的 `admission.json`。

## 11. Batch 002 生成与评测禁区

在10道题全部可信冻结、候选模型配置和评测器版本同时冻结前：

- 不调用Hy3生成候选；
- 不建立人工Gold；
- 不运行Semantic Judge；
- 不根据Reference RTL措辞优化solver prompt；
- 不因预计难度更改任务层级。

正式生成时，每题保留第一次有效模型输出，运行trusted Simulation/Formal并生成blind review packet。双人独立审阅后晋升Gold，再对冻结评测器进行一次性评测。
