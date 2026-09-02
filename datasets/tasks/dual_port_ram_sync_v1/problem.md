# Synchronous Dual-Port RAM with Read-First Collision Semantics

Design a synthesizable SystemVerilog module named `dual_port_ram_sync` with one
synchronous write port and one synchronous registered read port. The memory has
`2**ADDR_WIDTH` words of `DATA_WIDTH` bits.

On a rising edge with `wr_en=1`, write `wr_data` to `wr_addr`. On a rising edge
with `rd_en=1`, update registered `rd_data` with the value stored at `rd_addr`
immediately before that edge. Therefore, when a read and write target the same
address on the same edge, the read returns the old value (read-first), while the
new value is visible to later reads. When `rd_en=0`, `rd_data` holds.

Reset is synchronous, active-high, and has highest priority. It clears
`rd_data` and every memory word to zero; no read or write is accepted on a reset
edge.
