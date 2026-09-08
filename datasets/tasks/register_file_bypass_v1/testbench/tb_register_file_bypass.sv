module tb_register_file_bypass;
  localparam integer DATA_WIDTH = 8;
  localparam integer ADDR_WIDTH = 2;
  reg clk = 0;
  reg rst = 0;
  reg we = 0;
  reg [ADDR_WIDTH-1:0] waddr = 0;
  reg [DATA_WIDTH-1:0] wdata = 0;
  reg [ADDR_WIDTH-1:0] raddr_a = 0;
  reg [ADDR_WIDTH-1:0] raddr_b = 0;
  wire [DATA_WIDTH-1:0] rdata_a;
  wire [DATA_WIDTH-1:0] rdata_b;
  wire rdata_a_min;
  wire rdata_b_min;
  integer errors = 0;

  register_file_bypass #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH)
  ) dut (.*);

  register_file_bypass #(.DATA_WIDTH(1), .ADDR_WIDTH(1)) dut_min (
    .clk(clk),
    .rst(rst),
    .we(we),
    .waddr(waddr[0]),
    .wdata(wdata[0]),
    .raddr_a(raddr_a[0]),
    .raddr_b(raddr_b[0]),
    .rdata_a(rdata_a_min),
    .rdata_b(rdata_b_min)
  );

  always #5 clk = ~clk;

  task set_inputs;
    input next_rst;
    input next_we;
    input [ADDR_WIDTH-1:0] next_waddr;
    input [DATA_WIDTH-1:0] next_wdata;
    input [ADDR_WIDTH-1:0] next_raddr_a;
    input [ADDR_WIDTH-1:0] next_raddr_b;
    begin
      @(negedge clk);
      rst = next_rst;
      we = next_we;
      waddr = next_waddr;
      wdata = next_wdata;
      raddr_a = next_raddr_a;
      raddr_b = next_raddr_b;
      #1;
    end
  endtask

  task commit_edge;
    begin
      @(posedge clk);
      #1;
    end
  endtask

  task check;
    input condition;
    input [8*32-1:0] obligation;
    begin
      if (!condition) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
    end
  endtask

  initial begin
    $dumpfile("register_file_bypass.vcd");
    $dumpvars(0, tb_register_file_bypass);

    set_inputs(1, 1, 1, 8'hA5, 1, 1);
    commit_edge();
    check(rdata_a == 0 && rdata_b == 0, "O_RESET");
    check(rdata_a_min == 0 && rdata_b_min == 0, "O_RESET");

    set_inputs(0, 1, 1, 8'hA5, 1, 1);
    check(rdata_a == 8'hA5 && rdata_b == 8'hA5, "O_DUAL_READ_COLLISION");
    check(rdata_a_min == 1 && rdata_b_min == 1, "O_BYPASS_A");
    commit_edge();
    check(rdata_a == 8'hA5 && rdata_b == 8'hA5, "O_WRITE");

    set_inputs(0, 1, 2, 8'h3C, 1, 2);
    check(rdata_a == 8'hA5, "O_COMB_READ");
    check(rdata_b == 8'h3C, "O_BYPASS_B");
    commit_edge();

    set_inputs(0, 0, 0, 0, 2, 1);
    check(rdata_a == 8'h3C && rdata_b == 8'hA5, "O_COMB_READ");
    commit_edge();
    check(rdata_a == 8'h3C && rdata_b == 8'hA5, "O_STORAGE_HOLD");

    set_inputs(1, 1, 2, 8'hFF, 2, 1);
    commit_edge();
    check(rdata_a == 0 && rdata_b == 0, "O_RESET");
    check(rdata_a_min == 0 && rdata_b_min == 0, "O_RESET");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
