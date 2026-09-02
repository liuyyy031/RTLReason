module dual_port_ram_sync #(
  parameter integer DATA_WIDTH = 8,
  parameter integer ADDR_WIDTH = 2
) (
  input  wire                  clk,
  input  wire                  rst,
  input  wire                  wr_en,
  input  wire [ADDR_WIDTH-1:0] wr_addr,
  input  wire [DATA_WIDTH-1:0] wr_data,
  input  wire                  rd_en,
  input  wire [ADDR_WIDTH-1:0] rd_addr,
  output reg  [DATA_WIDTH-1:0] rd_data
);
  localparam integer DEPTH = (1 << ADDR_WIDTH);
  reg [DATA_WIDTH-1:0] memory [0:DEPTH-1];
  integer index;

  always @(posedge clk) begin
    if (rst) begin
      rd_data <= {DATA_WIDTH{1'b0}};
      for (index = 0; index < DEPTH; index = index + 1)
        memory[index] <= {DATA_WIDTH{1'b0}};
    end else begin
      if (wr_en)
        memory[wr_addr] <= wr_data;
      if (rd_en)
        rd_data <= memory[rd_addr];
    end
  end
endmodule
