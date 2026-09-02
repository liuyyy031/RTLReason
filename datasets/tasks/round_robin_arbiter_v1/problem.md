# Registered Round-Robin Arbiter

Design a synthesizable SystemVerilog module named `round_robin_arbiter` for four
requesters. `grant` is registered. At every rising edge, scan the sampled `req`
vector beginning at the current pointer, wrapping from requester 3 to requester
0, and register a one-hot grant for the first asserted requester. After a grant,
the next scan begins immediately after that requester. If no request is asserted,
register zero and hold the pointer. Reset is synchronous and active-high.

The task defines safety and priority behavior only; do not claim unconditional
liveness for requesters whose requests may be withdrawn.
