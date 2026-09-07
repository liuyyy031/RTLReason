# Ready/Valid 8-to-16 Stream Width Adapter

Design a synthesizable SystemVerilog module named `stream_width_adapter`.

Pack two accepted 8-bit input transfers into one 16-bit output word. The first
byte is the low byte and the second is the high byte. A pending output must
remain stable under backpressure. This interface deliberately has no
full-output replacement: while `out_valid` is high, `in_ready` is low even if
the output will be accepted on the current edge.

Use exactly the ports and timing in `interface_semantics.json`.
