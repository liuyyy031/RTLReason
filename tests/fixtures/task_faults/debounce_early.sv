module debounce_filter #(
  parameter integer STABLE_CYCLES = 3
) (
  input wire clk,
  input wire rst,
  input wire noisy_in,
  output reg debounced,
  output reg changed
);
  localparam integer COUNT_WIDTH = $clog2(STABLE_CYCLES + 1);
  reg [COUNT_WIDTH-1:0] consecutive;
  always @(posedge clk) begin
    if (rst) begin
      debounced <= 0;
      changed <= 0;
      consecutive <= 0;
    end else begin
      changed <= 0;
      if (noisy_in == debounced) consecutive <= 0;
      else if (consecutive == STABLE_CYCLES - 2) begin
        debounced <= noisy_in;
        changed <= 1;
        consecutive <= 0;
      end else consecutive <= consecutive + 1'b1;
    end
  end
endmodule
