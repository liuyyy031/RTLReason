# Registered Grant-Hold Fixed-Priority Arbiter

Design a synthesizable SystemVerilog module named `grant_hold_arbiter` for four
requesters.  `grant[3:0]` is registered and one-hot-or-zero.  When idle, sample
`req` on the rising edge and grant the asserted requester with the lowest index.
Once nonzero, grant must remain unchanged until a sampled high `accept`, even if
the winning requester withdraws its request or other requests change.

An accepted grant clears after that edge.  Do not select a replacement request
on the same completion edge; selection resumes on a later idle edge.  `accept`
while idle does not block normal request selection.  Reset is synchronous,
active-high, and has highest priority.
