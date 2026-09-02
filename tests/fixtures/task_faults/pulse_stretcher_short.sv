module pulse_stretcher #(
  parameter integer PULSE_CYCLES = 4
) (
  input wire clk,
  input wire rst,
  input wire trigger,
  output reg active
);
  localparam integer COUNT_WIDTH = $clog2(PULSE_CYCLES + 1);
  reg [COUNT_WIDTH-1:0] remaining;
  always @(posedge clk) begin
    if (rst) begin
      active <= 0;
      remaining <= 0;
    end else if (trigger) begin
      active <= 1;
      remaining <= PULSE_CYCLES - 1;
    end else if (active && remaining == 1) begin
      active <= 0;
      remaining <= 0;
    end else if (active) begin
      remaining <= remaining - 1'b1;
    end
  end
endmodule
