module ready_valid_slice #(
  parameter integer DATA_WIDTH = 8
) (
  input wire clk, rst, in_valid,
  output wire in_ready,
  input wire [DATA_WIDTH-1:0] in_data,
  output reg out_valid,
  input wire out_ready,
  output reg [DATA_WIDTH-1:0] out_data
);
  assign in_ready = !out_valid;
  always @(posedge clk) begin
    if (rst) begin out_valid <= 0; out_data <= 0; end
    else if (in_ready && in_valid) begin
      out_valid <= 1; out_data <= in_data;
    end else if (out_valid && out_ready) begin
      out_valid <= 0;
    end
  end
endmodule
