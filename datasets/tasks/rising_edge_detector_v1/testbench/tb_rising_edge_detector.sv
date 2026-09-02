module tb_rising_edge_detector;
  reg clk = 0;
  reg rst = 0;
  reg signal_in = 0;
  wire pulse;
  integer errors = 0;

  rising_edge_detector dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input next_signal;
    input expected_pulse;
    input [8*32-1:0] obligation;
    begin
      @(negedge clk);
      rst = next_rst;
      signal_in = next_signal;
      @(posedge clk); #1;
      if (pulse !== expected_pulse) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
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
    $dumpfile("rising_edge_detector.vcd");
    $dumpvars(0, tb_rising_edge_detector);

    // Reset ignores a simultaneous high input and clears remembered history.
    step(1, 1, 0, "O_RESET");
    step(0, 1, 1, "O_FIRST_AFTER_RESET");
    check(pulse == 1, "O_RISE");

    // A held high level must not retrigger.
    step(0, 1, 0, "O_NO_REPEAT");
    step(0, 1, 0, "O_NO_REPEAT");

    // Falling updates history but does not pulse; the next rise pulses again.
    step(0, 0, 0, "O_FALL");
    step(0, 0, 0, "O_HISTORY");
    step(0, 1, 1, "O_RISE");
    step(0, 0, 0, "O_FALL");
    step(0, 1, 1, "O_HISTORY");

    // Reset has priority over a would-be rising detection.
    step(1, 1, 0, "O_RESET");
    step(0, 0, 0, "O_HISTORY");
    step(0, 1, 1, "O_RISE");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
