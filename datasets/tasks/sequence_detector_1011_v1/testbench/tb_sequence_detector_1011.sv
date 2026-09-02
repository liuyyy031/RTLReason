module tb_sequence_detector_1011;
  reg clk = 0;
  reg rst = 0;
  reg bit_valid = 0;
  reg bit_in = 0;
  wire match;
  integer errors = 0;
  sequence_detector_1011 dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input next_valid;
    input next_bit;
    input expected_match;
    input [8*32-1:0] obligation;
    begin
      @(negedge clk);
      rst = next_rst;
      bit_valid = next_valid;
      bit_in = next_bit;
      @(posedge clk); #1;
      if (match !== expected_match) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
    end
  endtask

  initial begin
    $dumpfile("sequence_detector_1011.vcd");
    $dumpvars(0, tb_sequence_detector_1011);

    step(1, 1, 1, 0, "O_RESET");

    // Two overlapping matches in 1011011.
    step(0, 1, 1, 0, "O_NONMATCH");
    step(0, 1, 0, 0, "O_NONMATCH");
    step(0, 1, 1, 0, "O_NONMATCH");
    step(0, 1, 1, 1, "O_MATCH_1011");
    step(0, 1, 0, 0, "O_PULSE");
    step(0, 1, 1, 0, "O_NONMATCH");
    step(0, 1, 1, 1, "O_OVERLAP");

    // Invalid cycles clear the pulse but do not consume bit_in.
    step(0, 0, 0, 0, "O_PULSE");
    step(1, 0, 0, 0, "O_RESET");
    step(0, 1, 1, 0, "O_NONMATCH");
    step(0, 0, 0, 0, "O_VALID_GATE");
    step(0, 0, 1, 0, "O_VALID_GATE");
    step(0, 1, 0, 0, "O_NONMATCH");
    step(0, 1, 1, 0, "O_NONMATCH");
    step(0, 1, 1, 1, "O_MATCH_1011");

    // Reset discards a partial prefix and dominates valid input.
    step(0, 1, 1, 0, "O_NONMATCH");
    step(0, 1, 0, 0, "O_NONMATCH");
    step(1, 1, 1, 0, "O_RESET");
    step(0, 1, 1, 0, "O_NONMATCH");
    step(0, 1, 1, 0, "O_NONMATCH");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
