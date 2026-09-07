# Programmable Periodic Timer

Design a synthesizable SystemVerilog module named `programmable_timer`.

The timer stores a programmable period and counts down only while enabled.
Loading has priority over counting. Period zero is clamped to one. When the
current remaining count is one on an enabled edge, pulse `tick` and reload the
stored period on that same edge.

Use exactly the ports and observable timing defined in
`interface_semantics.json`.
