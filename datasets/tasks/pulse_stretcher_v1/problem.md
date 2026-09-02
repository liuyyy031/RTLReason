# Parameterized Retriggerable Pulse Stretcher

Design a synthesizable SystemVerilog module named `pulse_stretcher` with integer
parameter `PULSE_CYCLES` (default 4, valid values at least 2).  A sampled high
`trigger` makes registered output `active` high immediately after that rising
edge.  The trigger edge counts as the first active cycle, so without another
trigger `active` remains high for exactly `PULSE_CYCLES` consecutive cycles.

A trigger sampled while already active restarts the full interval from that
edge without producing a low gap.  A trigger on the edge that would otherwise
expire also restarts the interval.  Reset is synchronous, active-high, and has
priority over trigger.
