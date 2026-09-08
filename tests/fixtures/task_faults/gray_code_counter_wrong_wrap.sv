module gray_code_counter #(
  parameter integer WIDTH = 4
) (
  input wire clk,
  input wire rst,
  input wire en,
  output wire [WIDTH-1:0] gray,
  output reg wrap
);
  reg [WIDTH-1:0] index;
  assign gray = index ^ (index >> 1);
  always @(posedge clk) begin
    if (rst) begin
      index <= 0;
      wrap <= 0;
    end else if (en) begin
      wrap <= (index == 0);
      index <= index + 1'b1;
    end else begin
      wrap <= 0;
    end
  end
endmodule
