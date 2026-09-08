# Asynchronous Toggle Handshake

Design a synthesizable SystemVerilog module named `async_handshake` that moves
one source-domain event at a time into an asynchronous destination clock domain.
The interface uses source clock/reset `src_clk`/`src_rst`, destination
clock/reset `dst_clk`/`dst_rst`, source input `src_send`, source outputs
`src_accept` and `src_busy`, and destination output `dst_pulse`.

A source event is accepted only on a `src_clk` rising edge when `src_rst=0`,
`src_send=1`, and no previous accepted event is outstanding. `src_accept` is a
combinational indication of that pre-edge acceptance condition. Each accepted
event must cause exactly one registered one-cycle `dst_pulse` on a later
`dst_clk` rising edge. While an event is outstanding, `src_busy=1` and further
`src_send` assertions are ignored. `src_busy` clears only after the destination
has observed the request and the acknowledgement has crossed back to source.

Use a request-toggle / acknowledgement-toggle digital protocol with two
destination-domain synchronization stages for the request and two
source-domain synchronization stages for the acknowledgement. The task verifies
digital protocol safety only; it does not claim to model metastability, MTBF,
physical CDC timing, or silicon reliability.

Both resets are synchronous active-high resets for their respective clocks. A
reset epoch is a coordinated environment operation: `src_rst` and `dst_rst`
must both be asserted before any later source acceptance, and neither may be
asserted while `src_busy=1`. Behaviour under a unilateral or in-flight reset is
outside the frozen contract. After reset, all toggle and synchronizer state is
zero and `dst_pulse=0`.
