# Two-Entry Ready/Valid Elastic FIFO

Design a synthesizable SystemVerilog module named `ready_valid_fifo2` with exactly
two storage entries and parameter `DATA_WIDTH` (default 8). It connects ready/valid
input and output interfaces, preserves FIFO order, has no combinational data
bypass, remains stable under output backpressure, and permits a full queue to
accept a new input when the current head is consumed on the same edge.

Use the exact current-state flags, simultaneous-transfer rules, reset values, and
observable data timing frozen in `interface_semantics.json`.
