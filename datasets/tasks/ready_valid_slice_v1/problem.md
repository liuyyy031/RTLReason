# One-Entry Ready/Valid Register Slice

Design a synthesizable SystemVerilog module named `ready_valid_slice` with one
registered storage entry. The output interface has no combinational data bypass.
`in_ready` is combinationally high when the entry is empty or the current output
will be accepted. A simultaneous output transfer and input transfer replaces the
old entry without creating a bubble. Under backpressure, output valid and data
must remain stable. Reset is synchronous and active-high.

Use exactly the interface and edge semantics in `interface_semantics.json`.
