# Registered Rising-Edge Detector

Design a synthesizable SystemVerilog module named `rising_edge_detector`. On
each rising clock edge, sample `signal_in` and assert registered output `pulse`
for exactly one cycle when the new sample is `1` and the preceding accepted
sample was `0`. Holding the input high must not create repeated pulses, and a
falling edge must not create a pulse.

Reset is synchronous, active-high, and has highest priority. Reset clears both
the output pulse and the remembered sample to `0`. Consequently, if
`signal_in=1` on the first non-reset edge, that edge is treated as a rising
edge and produces a pulse.
