# Signed ALU with Status Flags

Design a synthesizable combinational SystemVerilog module named
`signed_alu_flags`.

The ALU supports unsigned bit-vector ADD, SUB, AND, and XOR operations while
also reporting zero, negative, carry/no-borrow, and signed-overflow flags.
Outputs must respond combinationally to the current inputs.  Use exactly the
operation encoding, port widths, and flag definitions in
`interface_semantics.json`.
