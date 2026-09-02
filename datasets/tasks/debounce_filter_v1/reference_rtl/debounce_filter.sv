module debounce_filter #(
  parameter integer STABLE_CYCLES = 3
) (
  input  wire clk,
  input  wire rst,
  input  wire noisy_in,
  output reg  debounced,
  output reg  changed
);
  localparam integer COUNT_WIDTH = $clog2(STABLE_CYCLES + 1);
  reg [COUNT_WIDTH-1:0] consecutive;

  always @(posedge clk) begin
    if (rst) begin
      debounced <= 1'b0;
      changed <= 1'b0;
      consecutive <= {COUNT_WIDTH{1'b0}};
    end else begin
      changed <= 1'b0;
      if (noisy_in == debounced) begin
        consecutive <= {COUNT_WIDTH{1'b0}};
      end else if (consecutive == STABLE_CYCLES - 1) begin
        debounced <= noisy_in;
        changed <= 1'b1;
        consecutive <= {COUNT_WIDTH{1'b0}};
      end else begin
        consecutive <= consecutive + 1'b1;
      end
    end
  end
endmodule
