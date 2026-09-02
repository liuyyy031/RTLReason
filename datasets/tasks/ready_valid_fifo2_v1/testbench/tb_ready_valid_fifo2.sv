module tb_ready_valid_fifo2;
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
  ready_valid_fifo2 #(.DATA_WIDTH(DATA_WIDTH)) dut (.*);
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
    input [8*40-1:0] obligation;
    begin
      if (!condition) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
    end
  endtask

  initial begin
    $dumpfile("ready_valid_fifo2.vcd");
    $dumpvars(0, tb_ready_valid_fifo2);
    step(1, 1, 8'hFF, 1);
    check(!out_valid && out_data == 0, "O_RESET");
    check(in_ready, "O_READY_VALID");

    @(negedge clk);
    rst = 0; in_valid = 1; in_data = 8'hA1; out_ready = 1;
    #1; check(!out_valid && out_data == 0, "O_EMPTY_NO_BYPASS");
    @(posedge clk); #1;
    check(out_valid && out_data == 8'hA1, "O_INPUT_ACCEPT");

    step(0, 1, 8'hB2, 0);
    check(out_valid && out_data == 8'hA1, "O_ORDERING");
    check(!in_ready, "O_READY_VALID");
    step(0, 1, 8'hCC, 0);
    check(out_valid && out_data == 8'hA1, "O_BACKPRESSURE");

    @(negedge clk);
    rst = 0; in_valid = 1; in_data = 8'hC3; out_ready = 1;
    #1; check(in_ready, "O_READY_VALID");
    @(posedge clk); #1;
    check(out_valid && out_data == 8'hB2, "O_FULL_REPLACE");
    out_ready = 0; in_valid = 0; #1;
    check(!in_ready, "O_FULL_REPLACE");
    step(0, 0, 0, 1);
    check(out_valid && out_data == 8'hC3, "O_ORDERING");
    step(0, 0, 0, 1);
    check(!out_valid && out_data == 0, "O_EMPTY_DATA");
    check(in_ready, "O_OCCUPANCY");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
