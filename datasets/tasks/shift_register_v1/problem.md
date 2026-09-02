# Enabled Serial-In Shift Register

Design a synthesizable SystemVerilog module named `shift_register` with parameter
`WIDTH` (default 8). On each enabled rising edge, shift existing bits toward the
most-significant bit and insert `serial_in` into bit zero. `serial_out` always
reflects the current most-significant stored bit. Reset is synchronous,
active-high, and has priority over enable.

Use exactly the ports and timing in `interface_semantics.json`.
