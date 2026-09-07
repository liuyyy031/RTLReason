# Saturating Up/Down Counter

Design a synthesizable SystemVerilog module named `saturating_counter`.

The parameterized counter updates on the rising clock edge when `en` is high.
`up=1` requests an increment and `up=0` requests a decrement. Unlike a modular
counter, it must hold at the maximum and minimum values instead of wrapping.
The boundary flags describe the current registered count.

Use exactly the ports and observable timing defined in
`interface_semantics.json`.
