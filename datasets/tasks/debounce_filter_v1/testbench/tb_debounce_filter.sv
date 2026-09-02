module tb_debounce_filter;
  localparam integer STABLE_CYCLES = 3;
  reg clk = 0;
  reg rst = 0;
  reg noisy_in = 0;
  wire debounced;
  wire changed;
  integer errors = 0;
  debounce_filter #(.STABLE_CYCLES(STABLE_CYCLES)) dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input next_noisy;
    input expected_debounced;
    input expected_changed;
    input [8*32-1:0] obligation;
    begin
      @(negedge clk); rst = next_rst; noisy_in = next_noisy;
      @(posedge clk); #1;
      if (debounced !== expected_debounced || changed !== expected_changed) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
    end
  endtask

  initial begin
    $dumpfile("debounce_filter.vcd");
    $dumpvars(0, tb_debounce_filter);

    step(1, 1, 0, 0, "O_RESET");

    // A bounce cancels two accumulated high samples.
    step(0, 1, 0, 0, "O_HOLD_BEFORE_THRESHOLD");
    step(0, 1, 0, 0, "O_HOLD_BEFORE_THRESHOLD");
    step(0, 0, 0, 0, "O_BOUNCE_CANCEL");
    step(0, 1, 0, 0, "O_HOLD_BEFORE_THRESHOLD");
    step(0, 1, 0, 0, "O_HOLD_BEFORE_THRESHOLD");
    step(0, 1, 1, 1, "O_THRESHOLD_UPDATE");
    step(0, 1, 1, 0, "O_CHANGED_PULSE");

    // Low transition obeys the same exact threshold.
    step(0, 0, 1, 0, "O_BIDIRECTIONAL");
    step(0, 0, 1, 0, "O_BIDIRECTIONAL");
    step(0, 1, 1, 0, "O_BOUNCE_CANCEL");
    step(0, 0, 1, 0, "O_HOLD_BEFORE_THRESHOLD");
    step(0, 0, 1, 0, "O_HOLD_BEFORE_THRESHOLD");
    step(0, 0, 0, 1, "O_BIDIRECTIONAL");
    step(0, 0, 0, 0, "O_CHANGED_PULSE");

    // Reset dominates a threshold-completing sample.
    step(0, 1, 0, 0, "O_HOLD_BEFORE_THRESHOLD");
    step(0, 1, 0, 0, "O_HOLD_BEFORE_THRESHOLD");
    step(1, 1, 0, 0, "O_RESET");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
