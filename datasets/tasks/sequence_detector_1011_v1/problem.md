# Valid-Sampled Overlapping 1011 Sequence Detector

Design a synthesizable SystemVerilog module named `sequence_detector_1011`.
On each rising edge with `bit_valid=1`, the module consumes `bit_in`.  Assert the
registered output `match` for exactly one cycle after consuming a bit that
completes the sequence `1011`.  Overlapping matches are required: the final `1`
of one match can be the initial `1` of the next match.  For example, valid input
bits `1011011` produce two match pulses.

When `bit_valid=0`, no bit is consumed, partial-match state is held, and `match`
is cleared.  Reset is synchronous, active-high, and has highest priority.
