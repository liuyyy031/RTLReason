module dual_port_ram_sync_formal;
  localparam integer DATA_WIDTH = 4;
  localparam integer ADDR_WIDTH = 2;
  localparam integer DEPTH = (1 << ADDR_WIDTH);
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg wr_en;
  (* anyseq *) reg [ADDR_WIDTH-1:0] wr_addr;
  (* anyseq *) reg [DATA_WIDTH-1:0] wr_data;
  (* anyseq *) reg rd_en;
  (* anyseq *) reg [ADDR_WIDTH-1:0] rd_addr;
  wire [DATA_WIDTH-1:0] rd_data;

  dual_port_ram_sync #(
    .DATA_WIDTH(DATA_WIDTH), .ADDR_WIDTH(ADDR_WIDTH)
  ) dut (.*);

  reg past_valid = 0;
  reg [DATA_WIDTH-1:0] model_memory [0:DEPTH-1];
  reg [DATA_WIDTH-1:0] model_rd_data = 0;
  integer index;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;

    if (past_valid) begin
      assert(rd_data == model_rd_data);
      if ($past(rst)) assert(rd_data == 0);
    end

    if (rst) begin
      model_rd_data <= 0;
      for (index = 0; index < DEPTH; index = index + 1)
        model_memory[index] <= 0;
    end else begin
      if (wr_en)
        model_memory[wr_addr] <= wr_data;
      if (rd_en)
        model_rd_data <= model_memory[rd_addr];
    end
  end
endmodule
