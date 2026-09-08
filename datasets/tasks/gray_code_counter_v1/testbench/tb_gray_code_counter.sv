module tb_gray_code_counter;
  localparam integer WIDTH = 3;
  reg clk = 0;
  reg rst = 0;
  reg en = 0;
  wire [WIDTH-1:0] gray;
  wire wrap;
  wire gray_min;
  wire wrap_min;
  reg [WIDTH-1:0] expected_index = 0;
  reg [WIDTH-1:0] previous_gray = 0;
  reg [WIDTH-1:0] difference;
  reg previous_gray_min = 0;
  integer errors = 0;
  integer step_index;

  gray_code_counter #(.WIDTH(WIDTH)) dut (.*);
  gray_code_counter #(.WIDTH(1)) dut_min (
    .clk(clk),
    .rst(rst),
    .en(en),
    .gray(gray_min),
    .wrap(wrap_min)
  );
  always #5 clk = ~clk;

  function [WIDTH-1:0] encode_gray;
    input [WIDTH-1:0] value;
    begin
      encode_gray = value ^ (value >> 1);
    end
  endfunction

  function is_onehot;
    input [WIDTH-1:0] value;
    begin
      is_onehot = (value != 0) && ((value & (value - 1'b1)) == 0);
    end
  endfunction

  task drive_edge;
    input next_rst;
    input next_en;
    begin
      @(negedge clk);
      rst = next_rst;
      en = next_en;
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
    $dumpfile("gray_code_counter.vcd");
    $dumpvars(0, tb_gray_code_counter);

    drive_edge(1, 1);
    expected_index = 0;
    previous_gray = gray;
    check(gray == 0 && wrap == 0, "O_RESET");
    check(gray == 0, "O_PRIORITY");
    check(gray_min == 0 && wrap_min == 0, "O_RESET");

    drive_edge(0, 0);
    check(gray == previous_gray && wrap == 0, "O_HOLD");
    check(gray_min == 0 && wrap_min == 0, "O_HOLD");

    for (step_index = 0; step_index < (1 << WIDTH); step_index = step_index + 1) begin
      previous_gray = gray;
      previous_gray_min = gray_min;
      expected_index = expected_index + 1'b1;
      drive_edge(0, 1);
      difference = gray ^ previous_gray;
      check(gray == encode_gray(expected_index), "O_GRAY_MAPPING");
      check(gray == encode_gray(expected_index), "O_ENABLE_STEP");
      check(is_onehot(difference), "O_SINGLE_BIT");
      check(gray_min != previous_gray_min, "O_SINGLE_BIT");
      check(wrap_min == previous_gray_min, "O_WRAP");
      if (expected_index == 0)
        check(wrap == 1, "O_WRAP");
      else
        check(wrap == 0, "O_WRAP");
    end

    previous_gray = gray;
    drive_edge(0, 0);
    check(gray == previous_gray, "O_HOLD");
    check(wrap == 0, "O_WRAP");

    drive_edge(1, 1);
    check(gray == 0 && wrap == 0, "O_RESET");
    check(gray == 0, "O_PRIORITY");
    check(gray_min == 0 && wrap_min == 0, "O_PRIORITY");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
