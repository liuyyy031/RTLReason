# Fixed-Latency Multicycle Unsigned Multiplier

Design a synthesizable SystemVerilog module `multicycle_multiply_ctrl` with
integer parameter `WIDTH` (default 8, valid values at least 1). Inputs are
`clk`, synchronous active-high `rst`, one-cycle request `start`, and unsigned
operands `a` and `b`. Outputs are `busy`, one-cycle `done`, and the registered
`2*WIDTH`-bit `result`.

An idle edge with `start=1` accepts a transaction, captures both operands, sets
`busy=1`, and does not perform an iteration on that acceptance edge. Exactly
one shift-add iteration executes on each subsequent rising edge while busy.
Exactly `WIDTH` such busy edges are executed. On the WIDTH-th busy edge, commit
the complete product atomically to `result`, clear `busy`, and pulse `done`.

While busy, all `start`, `a`, and `b` changes are ignored. `result` remains
unchanged from acceptance through the first WIDTH-1 busy edges and holds after
completion until a later completion or reset. Reset has highest priority and
clears all state and outputs, including `result`.
