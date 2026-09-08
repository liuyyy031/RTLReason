# Dual-Read Register File with Write Bypass

Design a synthesizable SystemVerilog module named `register_file_bypass`.

The module contains `2**ADDR_WIDTH` registers, one synchronous write port, and
two independent combinational read ports.  Each read normally returns the
currently stored word.  During a legal write attempt, a read whose address
matches the write address must immediately return `wdata`, including before the
active edge commits the write.

Reset is synchronous, active-high, clears every stored word, and has priority
over write.  Use exactly the ports, parameter contract, bypass behavior, and
observable timing defined in `interface_semantics.json`.
