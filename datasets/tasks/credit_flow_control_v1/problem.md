# Credit-Based Flow Control

Design a synthesizable SystemVerilog module named `credit_flow_control` with
integer parameter `MAX_CREDITS` (default 3, valid values at least 1). The module
tracks the number of credits currently available to a sender. A synchronous,
active-high reset has highest priority and restores the count to `MAX_CREDITS`.

On each non-reset rising edge, a sampled high `send_req` consumes one credit
only when the pre-edge credit count is nonzero. The combinational output
`send_accept` is high exactly when `rst` is low, `send_req` is high, and the
current count is nonzero. A sampled high `credit_return` returns one credit,
subject to saturation at `MAX_CREDITS`.

When an accepted send and a credit return occur on the same edge, the count is
unchanged. This rule also applies at the full boundary: the accepted send frees
one slot, so the simultaneous return restores that slot and the count remains
full. At zero credits, a simultaneous `send_req` and `credit_return` must not
accept the send; the return raises the count from zero to one. A return without
an accepted send while already full is ignored.

Expose the registered current count as `credits` with width
`$clog2(MAX_CREDITS+1)`, plus combinational current-state flags `empty` and
`full`. `CREDIT_WIDTH` is derived from `MAX_CREDITS` and is not a public
parameter.
