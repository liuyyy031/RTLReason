# Framed Serial Parity Accumulator

Design a synthesizable SystemVerilog module named `serial_parity`.

While a frame is active, XOR every accepted serial bit. A frame starts on a
sampled `start` while idle and finishes on a sampled `finish` while busy. A
valid bit presented on the same edge as start or finish belongs to that frame.
On finish, publish the accumulated XOR in `parity` and pulse `done` for one
cycle. Inputs outside an active frame have no effect.

Use exactly the ports and observable timing defined in
`interface_semantics.json`.
