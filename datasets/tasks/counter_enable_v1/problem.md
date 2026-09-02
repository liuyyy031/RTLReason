# Parameterized Enable/Load Counter

Design a synthesizable SystemVerilog module named `counter_enable`.

The counter has parameter `WIDTH` (default 8), a synchronous active-high reset,
a synchronous load command, and an enable command. Reset has highest priority,
then load, then enable. Enabled counting wraps modulo `2**WIDTH`. `overflow` is
a registered one-cycle pulse only when an enabled increment wraps from the
maximum value to zero.

Use exactly the ports and observable timing defined in
`interface_semantics.json`.
