module tb_ready_valid_slice;
  localparam integer DATA_WIDTH = 8;
  reg clk = 0;
  reg rst = 0;
  reg in_valid = 0;
  wire in_ready;
  reg [DATA_WIDTH-1:0] in_data = 0;
  wire out_valid;
  reg out_ready = 0;
  wire [DATA_WIDTH-1:0] out_data;
  integer errors = 0;
  ready_valid_slice #(.DATA_WIDTH(DATA_WIDTH)) dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input next_in_valid;
    input [DATA_WIDTH-1:0] next_data;
    input next_out_ready;
    begin
      @(negedge clk);
      rst = next_rst; in_valid = next_in_valid;
      in_data = next_data; out_ready = next_out_ready;
      @(posedge clk); #1;
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
    $dumpfile("ready_valid_slice.vcd");
    $dumpvars(0, tb_ready_valid_slice);
    step(1, 1, 8'hAA, 1);
    check(!out_valid && out_data == 0, "O_RESET");
    check(in_ready, "O_READY");

    step(0, 1, 8'hA1, 0);
    check(out_valid && out_data == 8'hA1, "O_INPUT_ACCEPT");
    check(!in_ready, "O_READY");
    step(0, 1, 8'hB2, 0);
    check(out_valid && out_data == 8'hA1, "O_BACKPRESSURE");

    step(0, 1, 8'hB2, 1);
    check(out_valid && out_data == 8'hB2, "O_REPLACE");
    check(in_ready, "O_READY");
    step(0, 0, 0, 1);
    check(!out_valid && out_data == 8'hB2, "O_DRAIN");

    @(negedge clk);
    rst = 0; in_valid = 1; in_data = 8'hC3; out_ready = 1;
    #1;
    check(!out_valid, "O_NO_BYPASS");
    @(posedge clk); #1;
    check(out_valid && out_data == 8'hC3, "O_ORDERING");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
