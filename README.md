# RTLReason 项目方案

## 1. 选题背景

大模型已经能够生成可综合 RTL，但仅用最终仿真是否通过来评价模型，会丢失大量重要信息：

- RTL 正确不代表设计过程正确，模型可能因为偶然、模板记忆或错误抵消得到正确代码；
- RTL 错误不代表每个过程阶段都错误，需要定位首个关键错误；
- 自然语言解释看似合理，不代表它与规格、状态模型、时序规则和最终 RTL 一致；
- 单独使用另一个大模型作 Judge，容易产生自评偏差、错误归因和不可复现结果；
- 如果任务的接口语义不完整，两个正确实现也可能因为 reset、latency 或边界并发语义不同而被误判。

RTLReason 的目标是建立一条可审计的评价链，把规格理解、状态建模、时序推导、候选性质和 RTL 实现连接起来，再用独立可信资产与 EDA 证据判断“哪里首先出错、错误如何传播、最终造成什么行为后果”。

## 2. 建设目标

### 2.1 总体目标

实现一个可扩展、可复现、证据驱动的 RTL 过程评测框架，支持：

- 结构化采集大模型的显式设计过程；
- 对过程条目进行正确/错误/未知三分类；
- 使用静态证据建立 evaluator-inferred dependency graph；
- 使用仿真和 Formal 判断候选 RTL 的外部行为；
- 沿冻结的依赖图定位根错误、首错阶段和受影响 obligation；
- 使用独立 Gold Validation Set 评价整个评测器；
- 形成可用于论文、项目答辩和后续工程扩展的实验数据与案例报告。

### 2.2 后续计划

可继续追求：

- 用 Hy3 自动生成 Gold 任务或 Gold Label；
- 覆盖所有 SystemVerilog 语法和工业级完整 SoC；
- 在没有 fairness assumption 时证明无条件 liveness；
- 把任意一个参考 RTL 当作唯一正确架构；
- 仅凭大模型 Judge 给出最终可信结论；
- 在缺少 EDA 工具或证据时猜测 RTL 正确性。

## 3. 核心设计原则

### 3.1 架构无关的行为 Gold

Gold 只冻结外部可观察行为，不冻结内部实现。候选 FIFO 可以使用计数器、指针环绕位或其他正确微架构。

### 3.2 接口语义先于参考模型

可信链正式定义为：

```text
Problem Specification
  → Interface Semantics
  → Behavioral Obligations
  → Reference Model
  → Simulation / Formal Oracle
```

Interface Semantics 必须明确：

- 时钟沿与输入采样相位；
- reset 同步/异步、有效电平和优先级；
- 输出延迟和有效相位；
- flags 表示 current state 还是 next state；
- 满/空时同时读写的接受规则；
- 无效操作和 reset 后输出的可观察行为。

### 3.3 独立参考模型

Reference Model 必须维护自己的期望状态，不能使用 DUT 输出的 `full/empty` 决定是否接受读写，否则 DUT 的错误会污染 Oracle。

### 3.4 动静态证据分离

Dependency Builder 只使用静态结构性证据：

- obligation mapping；
- signal/state reference；
- def-use；
- process item semantics；
- RTL traceability；
- 合法的跨阶段或阶段内顺序关系。

Simulation/Formal evidence 不参与图结构生成，只在 Evidence Attribution 阶段进入。这样可以避免“因为测试失败所以建立某条边，再用这条边解释测试失败”的循环论证。

### 3.5 Gold 与预测严格分离

项目中正式区分：

- Hy3 Claimed Dependency：候选模型自己的依赖声明；
- Evaluator-Inferred Dependency：RTLReason 的预测；
- Gold Causal Dependency：人工验证集中的关键因果依赖。

Evaluator-Inferred Dependency 不因名称中包含 inferred/verified 就自动正确。

### 3.6 Safety-first Formal

MVP 只证明可在有限反例中清楚解释的 Safety 性质。FIFO ordering 表述为：

> 当一次合法读取发生时，返回值必须等于此前尚未读取的最早合法写入值。

不无条件断言“写入的数据最终一定被读取”，因为当环境永远不发起读取时，该性质并不成立。

## 4. 总体架构

```text
┌──────────────────────── Trusted Task Assets ────────────────────────┐
│ Problem │ Interface │ Obligations │ Reference Model │ EDA Oracles  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Hy3 S1–S5 Solver │
                    └──────────────────┘
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
   Structured Process Artifact            Candidate RTL
             │                                 │
             ▼                                 ▼
   Schema/Semantic Evaluation        Simulation / Formal
             │                                 │
             ▼                                 ▼
   Static Dependency Builder          EDA Evidence Mapping
             │                                 │
             └───────────────┬─────────────────┘
                             ▼
                  Evidence Attribution
                             │
                             ▼
        Process Correctness / Root Error / First Stage
                             │
                             ▼
              Independent Gold Validation & Metrics
```

## 5. 主要模块设计

### 5.1 Trusted Task Assets

每道题使用独立目录，至少包含：

```text
problem.md
interface_semantics.json
behavioral_obligations.yaml
difficulty.json
provenance.json
reference_rtl/
testbench/
formal/
```

`provenance.json` 记录任务来源、许可证、版本和可信资产生成政策。任何被测 Hy3 输出都不得反向修改这些资产。

### 5.2 S1–S5 Process Artifact

过程条目包含：

```json
{
  "id": "S3.2",
  "claim": "accepted read/write 的定义",
  "maps_to": ["O_WRITE_ACCEPT", "O_READ_ACCEPT"],
  "claimed_dependencies": ["S2.3"],
  "reads": ["full", "empty", "wr_en", "rd_en"],
  "writes": ["write_accept", "read_accept"],
  "rtl_blocks": ["acceptance_logic"]
}
```

这些字段是显式工程产物，不要求模型输出隐藏 chain-of-thought。

### 5.3 Schema Evaluator

Schema Evaluator 负责确定性检查：

- S1–S5 是否齐全且顺序正确；
- item ID 是否唯一并与 stage 匹配；
- obligation ID 是否存在；
- dependency target 是否存在；
- 依赖是否自指、反向或形成环；
- module name 和 RTL 是否存在；
- 必要的 traceability 字段是否完整。

确定性错误可以覆盖模型 Judge，但报告必须同时保留：

- Judge 原始状态；
- deterministic effective status；
- 覆盖规则、原因和置信度。

### 5.4 Semantic Evaluator

Semantic Evaluator 根据可信规格、Interface Semantics、Behavioral Obligations 和错误分类，判断每个条目：

- correct；
- incorrect；
- unknown。

输出错误类型 L1/L2、简短证据说明和置信度。Hy3 Judge 是一种可选实现，不是 Gold。

### 5.5 Dependency Builder

目标图必须是 DAG。拟采用的 v1.1 规则如下：

1. 允许 earlier stage → later stage；
2. 允许同阶段 earlier item → later item；
3. 禁止 self edge、backward edge 和 cycle；
4. def-use、state transition、RTL traceability 可生成强因果候选；
5. obligation mapping 用于限定语义范围和增强置信度；
6. shared obligation 单独出现时只形成 association，不直接生成 causal edge；
7. Hy3 claimed edge 仅用于比较，不直接复制为 inferred edge；
8. evidence 不充分时返回 unknown/low confidence，而不是强行连边。

图结构生成后计算 digest 并冻结。后续 EDA evidence 不得改变 digest。

### 5.6 Verification Layer

Simulation Core：

- 所有任务均执行；
- 定向边界测试与随机/覆盖驱动测试结合；
- Reference Model 自行维护状态；
- failure 映射到 Behavioral Obligation；
- 保存返回码、摘要和可选波形。

Formal Core：

- 只覆盖核心子集；
- MVP 以 Safety 为主；
- 失败时保留 counterexample；
- Formal unavailable 时输出 unknown，而不是 pass。

### 5.7 Evidence Attribution

归因流程为：

```text
Simulation / Formal Failure
  → Violated Obligation
  → Affected Process Items
  → Frozen Inferred Dependency Graph
  → Candidate Error Paths
  → Root Error / First Error Stage
```

如果图、语义评审或证据不足，系统应保留 unknown，而不是给出过度确定的单一根因。

### 5.8 Gold Validation

Gold Validation Set 可以包含：

- 真实 Hy3 正确回答；
- 真实 Hy3 failure；
- 正确 RTL / 错误过程；
- 错误 RTL / 上游过程错误；
- 控制注错样本；
- 不同微架构的正确实现。

人工标注至少包括：

- `gold_rtl_correct`；
- `gold_process_correct`；
- `gold_first_error_stage`；
- `gold_root_error`；
- `gold_error_type_l1`；
- `gold_parent_dependency`；
- `gold_affected_obligation`；
- 标注者、guideline version 和 adjudication status。

开发集和 held-out test 必须分开。Prompt、阈值和规则不得根据 held-out test 调整。

## 6. 第一题 FIFO 的重点技术

### 6.1 边界并发语义

FIFO 满时同时读写，允许读写都接受；FIFO 空时同时读写，只接受写且不 bypass。该规则决定 acceptance、occupancy 和 ordering，必须同时进入 interface、obligation、reference model、testbench 和 formal harness。

### 6.2 Current-state Flags

`full/empty` 描述当前 occupancy，而不是 next state。Reference Model 根据自己的 queue 计算 flags，不能读取 DUT flags。

### 6.3 非 2 的幂深度

参考 RTL 的指针回绕显式使用 `DEPTH-1`，而不是依赖自然位宽溢出，从而支持非 2 的幂深度。

### 6.4 满状态同地址读写

满状态同时读写时，读指针与写指针可能指向同一存储地址。同步非阻塞赋值应返回旧的最早数据，同时写入替换数据，testbench 必须覆盖该行为。

### 6.5 Safety Ordering

Formal shadow model 保存独立队列状态，只在 accepted read 发生后检查 `dout` 是否等于最早未读数据，避免引入无公平性保证的 eventual-read liveness。

## 7. 错误分类

L1 分类包括：

- Specification；
- State Modeling；
- Transition Logic；
- Temporal Semantics；
- Property；
- Implementation；
- Format/Traceability。

L2 示例包括 Guard Condition Omission、Simultaneous Operation Error、Read Latency Error、Current-vs-Next State Error、Unjustified Liveness、Width or Signedness、Unsupported Dependency Claim 等。

错误分类定义保存在 `datasets/error_taxonomy.yaml`，版本变化必须记录。

## 8. 评测指标

核心指标：

1. Final RTL Accuracy；
2. Process Correctness Accuracy；
3. Process Correctness Macro-F1；
4. Stage-level First Error Localization Accuracy；
5. Process False Positive Rate；
6. Correct-RTL / Wrong-Process Recall；
7. Error Type L1 Macro-F1。

评测器诊断指标：

1. Root Error Accuracy；
2. Critical Dependency Exact Accuracy；
3. Critical Dependency Micro Precision / Recall / F1；
4. Semantic Evaluator item-level Accuracy/F1；
5. Attribution accuracy under Gold Dependency；
6. Attribution accuracy under Evaluator-Inferred Dependency。

通过拆分指标可以判断错误来自 Semantic Evaluator、Dependency Builder，还是 Attribution Algorithm。

## 9. 预期效果

- 对每个候选输出统一、可机器读取的 S1–S5 过程；
- 对 RTL 结论给出 simulation/formal 来源，而不是单一模型评分；
- 对首错定位给出 obligation、过程条目和依赖路径；
- 支持离线人工 assessments，便于独立 Gold 验证；
- 支持不同微架构，不因参考实现差异误判；
- 缺少证据时返回 unknown，降低虚假确定性；
- 实验产物包含版本、调用 metadata、图 digest 和评测报告，可复现、可审计。



## 10. 时间规划

| 日期 | 主要工作 | 交付物 | 验收条件 |
|:--|---|---|---|
| 8.23 | 冻结方法边界；修订同阶段依赖、DAG 与 association/causality 规则 | Dependency Semantics v1.1、回归测试 | 真实 Hy3 FIFO 样本不再因合法同阶段依赖误报 |
| 8.24-8.26 | 闭环 FIFO 仿真与 Formal；完善 obligation failure 映射 | Icarus/SBY 运行记录、反例样本 | 两种参考 RTL 均通过；已知错误 RTL 能被捕获 |
| 8.27 | 扩充基础任务：counter、shift register、arbiter、handshake | 约 10 道可信任务 | 每题都有 interface、obligations、reference model 和 simulation |
| 8.28-8.30 | 扩充状态机、参数化模块和时序边界任务 | 累计约 20–30 道任务 | 难度与错误类型覆盖达到预设矩阵 |
| 8.31 | 采集真实 Hy3 输出并建设 Gold Development Set | 10–20 个 adjudicated cases | 包含真实 failure、正确 RTL/错误过程等关键组合 |
| 9.1-9.2 | 校准 Semantic Evaluator、Dependency Builder 和 Attribution | 指标报告、错误案例分析 | 分模块报告误差，不使用 held-out 调参 |
| 9.3-9.4 | 建设 held-out test；扩展至目标题量 | 30–60 道题、held-out labels | 任务资产版本冻结，测试集不再参与规则修改 |
| 9.5-9.10 | 完成消融实验、文档、演示和项目交付 | 最终报告、CLI demo、案例可视化 | 从任务到报告可一键复现，关键结论有证据链 |

## 17. 验收标准

MVP 验收：

- FIFO 的可观察接口语义完整冻结；
- 两种不同参考架构通过同一可信 simulation suite；
- 独立 Python model 与可信 testbench 在边界场景一致；
- Formal Core 不包含无条件 eventual-read liveness；
- 图构建代码不接收 EDA evidence；
- EDA evidence 只在 attribution 阶段进入；
- 同阶段合法顺序依赖不被误判；
- Gold schema 能区分 inferred dependency 与 gold dependency；
- API key 不进入日志、prompt 或报告；
- Python 回归测试、JSON/YAML 校验和 CI 全部通过。

完整项目验收：

- 达到目标任务数量与难度覆盖；
- Gold Development/Held-out 划分完成；
- 关键指标可复现并附置信区间；
- 至少提供正确 RTL/错误过程、错误 RTL/上游错误、dependency builder 错边三类案例分析；
- 从 Hy3 调用、EDA 验证到最终报告可一键运行；
- 项目结论能够追溯到可信资产、过程条目、依赖图和 EDA evidence。
