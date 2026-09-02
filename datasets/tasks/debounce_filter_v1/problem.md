# Consecutive-Sample Debounce Filter

Design a synthesizable SystemVerilog module named `debounce_filter` with integer
parameter `STABLE_CYCLES` (default 3, valid values at least 2).  `noisy_in` is
already synchronous to `clk`; clock-domain synchronization and metastability
handling are outside this task.

The registered output `debounced` changes only after `noisy_in` has continuously
differed from the current output for exactly `STABLE_CYCLES` consecutive rising
edges.  It changes immediately after the edge sampling the final required
value.  Any sample equal to the current output cancels the pending transition
and clears its consecutive-sample count.  Assert registered `changed` for one
cycle exactly when `debounced` changes.  Reset is synchronous, active-high, and
sets `debounced=0`, `changed=0`.
