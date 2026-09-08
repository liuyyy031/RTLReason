# AXI-Stream Packet Counter

Design a synthesizable SystemVerilog module named `axi_stream_packet_counter`.

The module observes an AXI-Stream-like channel and maintains two saturating
counters: the number of accepted beats and the number of accepted beats marked
with `tlast`.  A beat is accepted only when `tvalid` and `tready` are both high
at the sampled clock edge.  `clear` synchronously clears both counters and has
priority over an otherwise valid transfer.

Reset is synchronous, active-high, and has highest priority.  Use exactly the
ports, parameter contract, saturation behavior, and observable timing defined
in `interface_semantics.json`.
