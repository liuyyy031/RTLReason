module register_file_bypass_formal;
  localparam integer DATA_WIDTH = 4;
  localparam integer ADDR_WIDTH = 2;
  localparam integer DEPTH = 1 << ADDR_WIDTH;
  reg clk = 0;
  always @($global_clock) clk <= !clk;

  reg rst = 1;
  (* anyseq *) reg we;
  (* anyseq *) reg [ADDR_WIDTH-1:0] waddr;
  (* anyseq *) reg [DATA_WIDTH-1:0] wdata;
  (* anyseq *) reg [ADDR_WIDTH-1:0] raddr_a;
  (* anyseq *) reg [ADDR_WIDTH-1:0] raddr_b;
  wire [DATA_WIDTH-1:0] rdata_a;
  wire [DATA_WIDTH-1:0] rdata_b;

  register_file_bypass #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH)
  ) dut (.*);

  reg past_valid = 0;
  reg [DATA_WIDTH-1:0] model_words [0:DEPTH-1];
  integer index;

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;

    if (past_valid) begin
      // O_COMB_READ, O_BYPASS_A, O_BYPASS_B, O_DUAL_READ_COLLISION
      assert(
        rdata_a == ((!rst && we && raddr_a == waddr)
          ? wdata : model_words[raddr_a])
      );
      assert(
        rdata_b == ((!rst && we && raddr_b == waddr)
          ? wdata : model_words[raddr_b])
      );
    end

    if (rst) begin
      // O_RESET
      for (index = 0; index < DEPTH; index = index + 1)
        model_words[index] <= 0;
    end else if (we) begin
      // O_WRITE; unaddressed entries establish O_STORAGE_HOLD
      model_words[waddr] <= wdata;
    end
  end
endmodule
