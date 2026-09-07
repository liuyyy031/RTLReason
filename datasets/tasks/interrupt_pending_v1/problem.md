# Four-Source Interrupt Pending Controller

Design a synthesizable SystemVerilog module named `interrupt_pending`.

The controller captures unmasked interrupt samples into a four-bit pending
register. It exposes the lowest-numbered pending source. An acknowledge clears
the source selected from the current state. A new interrupt sampled for that
same source on the acknowledge edge is set-dominant and therefore remains
pending. Masking affects new capture only; it never clears existing pending
bits.

Use exactly the ports and timing in `interface_semantics.json`.
