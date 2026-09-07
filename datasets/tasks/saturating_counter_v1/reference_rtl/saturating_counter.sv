module saturating_counter #(
  parameter integer WIDTH = 8
) (
  input  wire             clk,
  input  wire             rst,
  input  wire             en,
  input  wire             up,
  output reg  [WIDTH-1:0] count,
  output wire             at_min,
  output wire             at_max
);
  assign at_min = (count == {WIDTH{1'b0}});
  assign at_max = &count;

  always @(posedge clk) begin
    if (rst)
      count <= {WIDTH{1'b0}};
    else if (en && up && !at_max)
      count <= count + 1'b1;
    else if (en && !up && !at_min)
      count <= count - 1'b1;
  end
endmodule
