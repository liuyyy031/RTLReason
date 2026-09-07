module saturating_counter #(
  parameter integer WIDTH = 8
) (
  input wire clk, input wire rst, input wire en, input wire up,
  output reg [WIDTH-1:0] count, output wire at_min, output wire at_max
);
  assign at_min = (count == 0);
  assign at_max = &count;
  always @(posedge clk) begin
    if (rst) count <= 0;
    else if (en) count <= up ? count + 1'b1 : count - 1'b1;
  end
endmodule
