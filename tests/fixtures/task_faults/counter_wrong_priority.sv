module counter_enable #(
  parameter integer WIDTH = 8
) (
  input wire clk, rst, en, load,
  input wire [WIDTH-1:0] load_value,
  output reg [WIDTH-1:0] count,
  output reg overflow
);
  always @(posedge clk) begin
    if (rst) begin count <= 0; overflow <= 0; end
    else if (en) begin overflow <= &count; count <= count + 1'b1; end
    else if (load) begin count <= load_value; overflow <= 0; end
    else overflow <= 0;
  end
endmodule
