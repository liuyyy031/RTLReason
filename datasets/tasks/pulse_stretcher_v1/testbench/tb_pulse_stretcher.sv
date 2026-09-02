module tb_pulse_stretcher;
  localparam integer PULSE_CYCLES = 3;
  reg clk = 0;
  reg rst = 0;
  reg trigger = 0;
  wire active;
  integer errors = 0;
  pulse_stretcher #(.PULSE_CYCLES(PULSE_CYCLES)) dut (.*);
  always #5 clk = ~clk;

  task step;
    input next_rst;
    input next_trigger;
    input expected_active;
    input [8*32-1:0] obligation;
    begin
      @(negedge clk); rst = next_rst; trigger = next_trigger;
      @(posedge clk); #1;
      if (active !== expected_active) begin
        errors = errors + 1;
        $display("OBLIGATION_FAIL:%0s", obligation);
      end
    end
  endtask

  initial begin
    $dumpfile("pulse_stretcher.vcd");
    $dumpvars(0, tb_pulse_stretcher);

    step(1, 1, 0, "O_RESET");
    step(0, 0, 0, "O_IDLE");

    // Trigger edge is cycle 1 of exactly three active cycles.
    step(0, 1, 1, "O_TRIGGER");
    step(0, 0, 1, "O_DURATION");
    step(0, 0, 1, "O_DURATION");
    step(0, 0, 0, "O_DURATION");

    // Retrigger while active restarts all three cycles.
    step(0, 1, 1, "O_TRIGGER");
    step(0, 0, 1, "O_DURATION");
    step(0, 1, 1, "O_RETRIGGER");
    step(0, 0, 1, "O_RETRIGGER");
    step(0, 0, 1, "O_RETRIGGER");
    step(0, 0, 0, "O_RETRIGGER");

    // Trigger on the edge that would expire wins over expiry.
    step(0, 1, 1, "O_TRIGGER");
    step(0, 0, 1, "O_DURATION");
    step(0, 0, 1, "O_DURATION");
    step(0, 1, 1, "O_EXPIRY_PRIORITY");
    step(0, 0, 1, "O_EXPIRY_PRIORITY");
    step(0, 0, 1, "O_EXPIRY_PRIORITY");
    step(0, 0, 0, "O_EXPIRY_PRIORITY");

    // Reset dominates a simultaneous trigger.
    step(0, 1, 1, "O_TRIGGER");
    step(1, 1, 0, "O_RESET");
    step(0, 0, 0, "O_IDLE");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
