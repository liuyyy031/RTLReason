# Fixed-Rate 8N1 UART Receiver

Design a synthesizable SystemVerilog module named `uart_rx` with integer parameter
`CLKS_PER_BIT` (default 4; valid values are even integers at least 2). It receives
a single asynchronous serial input `rx` using the local `clk` domain and produces
an 8-bit LSB-first word.

The format is fixed 8N1: idle high, one low start bit, eight data bits least-
significant bit first, and one high stop bit. When `rx` is first observed low in
idle on a rising edge, begin start validation. Exactly `CLKS_PER_BIT/2` later,
sample the centre of the start bit. If that sample is high, reject the false
start and return to idle. Otherwise sample each data-bit centre exactly
`CLKS_PER_BIT` clocks apart. After the eighth data sample, sample the stop-bit
centre `CLKS_PER_BIT` clocks later.

At the stop sample, `data_out` becomes the received byte and `data_valid` pulses
for exactly one clock. `framing_error` pulses on that same clock exactly when
the stop-bit sample is low. A high `rx` in idle produces no output. The receiver
may accept a following start bit after it has returned to idle; no behavior is
promised for a start bit that begins before the receiver returns to idle.

`rst` is synchronous active-high and has highest priority. Reset clears all
state, `data_out`, `data_valid`, `framing_error`, and `busy`.
