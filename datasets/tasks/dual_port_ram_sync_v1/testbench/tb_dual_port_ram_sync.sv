module tb_dual_port_ram_sync;
  localparam integer DATA_WIDTH = 8;
  localparam integer ADDR_WIDTH = 2;
  reg clk = 0;
  reg rst = 0;
  reg wr_en = 0;
  reg [ADDR_WIDTH-1:0] wr_addr = 0;
  reg [DATA_WIDTH-1:0] wr_data = 0;
  reg rd_en = 0;
  reg [ADDR_WIDTH-1:0] rd_addr = 0;
  wire [DATA_WIDTH-1:0] rd_data;
  integer errors = 0;

  dual_port_ram_sync #(
    .DATA_WIDTH(DATA_WIDTH), .ADDR_WIDTH(ADDR_WIDTH)
  ) dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input next_wr_en;
    input [ADDR_WIDTH-1:0] next_wr_addr;
    input [DATA_WIDTH-1:0] next_wr_data;
    input next_rd_en;
    input [ADDR_WIDTH-1:0] next_rd_addr;
    input [DATA_WIDTH-1:0] expected_data;
    input [8*32-1:0] obligation;
    begin
      @(negedge clk);
      rst = next_rst;
      wr_en = next_wr_en;
      wr_addr = next_wr_addr;
      wr_data = next_wr_data;
      rd_en = next_rd_en;
      rd_addr = next_rd_addr;
      @(posedge clk); #1;
      if (rd_data !== expected_data) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
    end
  endtask

  initial begin
    $dumpfile("dual_port_ram_sync.vcd");
    $dumpvars(0, tb_dual_port_ram_sync);

    step(1, 1, 1, 8'hAA, 1, 1, 8'h00, "O_RESET");
    step(0, 0, 0, 8'h00, 1, 1, 8'h00, "O_RESET");

    // Write does not change rd_data, and a later read returns the word.
    step(0, 1, 1, 8'hA1, 0, 0, 8'h00, "O_HOLD");
    step(0, 0, 0, 8'h00, 1, 1, 8'hA1, "O_READ");

    // Same-address read/write is read-first, then the new value is visible.
    step(0, 1, 1, 8'hB2, 1, 1, 8'hA1, "O_READ_FIRST");
    step(0, 0, 0, 8'h00, 1, 1, 8'hB2, "O_WRITE");

    // Different addresses operate independently in one cycle.
    step(0, 1, 2, 8'hC3, 1, 1, 8'hB2, "O_INDEPENDENT_PORTS");
    step(0, 0, 0, 8'h00, 1, 2, 8'hC3, "O_WRITE");

    // Disabled read holds despite address activity and writes elsewhere.
    step(0, 1, 3, 8'hD4, 0, 0, 8'hC3, "O_HOLD");
    step(0, 0, 0, 8'h00, 1, 3, 8'hD4, "O_READ_LATENCY");

    // Reset clears both output and array contents.
    step(1, 0, 0, 8'h00, 0, 0, 8'h00, "O_RESET");
    step(0, 0, 0, 8'h00, 1, 1, 8'h00, "O_RESET");
    step(0, 0, 0, 8'h00, 1, 3, 8'h00, "O_RESET");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
