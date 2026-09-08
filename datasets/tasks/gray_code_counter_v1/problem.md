# Enabled Gray-Code Counter

Design a synthesizable SystemVerilog module named `gray_code_counter`.

Starting from zero, each accepted enable edge advances the observable output by
one position in the standard reflected Gray-code sequence.  The sequence wraps
after all `2**WIDTH` positions.  While disabled, the Gray output holds.  A
registered one-cycle `wrap` pulse identifies the enabled transition from the
last sequence position back to zero.

Reset is synchronous, active-high, and has highest priority.  Use exactly the
ports, parameter contract, and observable timing defined in
`interface_semantics.json`.  The internal state representation is not
prescribed.
