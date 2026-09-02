module counter_enable #(
  parameter integer WIDTH = 8
) (
  input  wire             clk,
  input  wire             rst,
  input  wire             en,
  input  wire             load,
  input  wire [WIDTH-1:0] load_value,
  output reg  [WIDTH-1:0] count,
  output reg              overflow
);
  always @(posedge clk) begin
    if (rst) begin
      count <= {WIDTH{1'b0}};
      overflow <= 1'b0;
    end else if (load) begin
      count <= load_value;
      overflow <= 1'b0;
    end else if (en) begin
      overflow <= &count;
      count <= count + 1'b1;
    end else begin
      count <= count;
      overflow <= 1'b0;
    end
  end
endmodule
