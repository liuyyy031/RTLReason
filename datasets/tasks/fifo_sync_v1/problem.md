# Synchronous FIFO

Design a synchronous parameterized FIFO named `fifo_sync`.  It stores `DEPTH`
words of `DATA_WIDTH` bits and exposes the exact interface below.  All state
changes occur on the rising edge of `clk`.

```systemverilog
module fifo_sync #(
  parameter integer DATA_WIDTH = 8,
  parameter integer DEPTH = 4
) (
  input  wire                  clk,
  input  wire                  rst,
  input  wire                  wr_en,
  input  wire                  rd_en,
  input  wire [DATA_WIDTH-1:0] din,
  output reg  [DATA_WIDTH-1:0] dout,
  output wire                  full,
  output wire                  empty
);
```

The normative behavior is defined by `interface_semantics.json` and
`behavioral_obligations.yaml`.  A solution may use any microarchitecture that
satisfies those observable requirements.
