module programmable_timer #(
  parameter integer WIDTH = 8
) (
  input  wire             clk,
  input  wire             rst,
  input  wire             load,
  input  wire [WIDTH-1:0] period,
  input  wire             enable,
  output reg  [WIDTH-1:0] remaining,
  output reg              tick
);
  reg [WIDTH-1:0] stored_period;
  wire [WIDTH-1:0] effective_period = (period == 0) ? {{(WIDTH-1){1'b0}}, 1'b1} : period;
  always @(posedge clk) begin
    if (rst) begin
      stored_period <= {{(WIDTH-1){1'b0}}, 1'b1};
      remaining <= {{(WIDTH-1){1'b0}}, 1'b1};
      tick <= 1'b0;
    end else if (load) begin
      stored_period <= effective_period;
      remaining <= effective_period;
      tick <= 1'b0;
    end else if (enable) begin
      if (remaining == {{(WIDTH-1){1'b0}}, 1'b1}) begin
        remaining <= stored_period;
        tick <= 1'b1;
      end else begin
        remaining <= remaining - 1'b1;
        tick <= 1'b0;
      end
    end else begin
      tick <= 1'b0;
    end
  end
endmodule
