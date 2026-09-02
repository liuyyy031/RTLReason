# Current-State Token Bucket

Design a synthesizable SystemVerilog module named `token_bucket` with integer
parameter `CAPACITY` (default 3, valid values at least 2).  The bucket starts
empty after synchronous active-high reset and automatically attempts to add one
token on every non-reset rising edge, saturating at `CAPACITY`.

A sampled high `req` consumes one token and produces a registered one-cycle
`grant` only when the bucket contained at least one token at the start of that
edge.  Replenishment on the same edge cannot make an empty-bucket request pass.
At a middle occupancy, simultaneous replenishment and accepted consumption
leave the count unchanged.  At full occupancy, no replenishment is accepted, so
an accepted request decreases the count by one.  Expose the registered current
token count as `tokens` using width `$clog2(CAPACITY+1)`.
