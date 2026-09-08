module register_file_bypass #(
  parameter integer DATA_WIDTH = 8,
  parameter integer ADDR_WIDTH = 2
) (
  input wire clk, input wire rst, input wire we,
  input wire [ADDR_WIDTH-1:0] waddr,
  input wire [DATA_WIDTH-1:0] wdata,
  input wire [ADDR_WIDTH-1:0] raddr_a,
  input wire [ADDR_WIDTH-1:0] raddr_b,
  output wire [DATA_WIDTH-1:0] rdata_a,
  output wire [DATA_WIDTH-1:0] rdata_b
);
  localparam integer DEPTH = 1 << ADDR_WIDTH;
  reg [DATA_WIDTH-1:0] words [0:DEPTH-1];
  integer index;
  assign rdata_a = words[raddr_a];
  assign rdata_b = words[raddr_b];
  always @(posedge clk) begin
    if (rst)
      for (index = 0; index < DEPTH; index = index + 1)
        words[index] <= 0;
    else if (we)
      words[waddr] <= wdata;
  end
endmodule
