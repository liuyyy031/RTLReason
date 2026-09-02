module ready_valid_slice #(
  parameter integer DATA_WIDTH = 8
) (
  input  wire                  clk,
  input  wire                  rst,
  input  wire                  in_valid,
  output wire                  in_ready,
  input  wire [DATA_WIDTH-1:0] in_data,
  output reg                   out_valid,
  input  wire                  out_ready,
  output reg  [DATA_WIDTH-1:0] out_data
);
  assign in_ready = !out_valid || out_ready;

  always @(posedge clk) begin
    if (rst) begin
      out_valid <= 1'b0;
      out_data <= {DATA_WIDTH{1'b0}};
    end else if (in_ready) begin
      out_valid <= in_valid;
      if (in_valid)
        out_data <= in_data;
    end
  end
endmodule
