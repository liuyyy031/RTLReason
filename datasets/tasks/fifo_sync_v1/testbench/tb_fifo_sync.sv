`timescale 1ns/1ps

module tb_fifo_sync;
  localparam integer DATA_WIDTH = 8;
  localparam integer DEPTH = 4;

  reg clk = 1'b0;
  reg rst = 1'b0;
  reg wr_en = 1'b0;
  reg rd_en = 1'b0;
  reg [DATA_WIDTH-1:0] din = {DATA_WIDTH{1'b0}};
  wire [DATA_WIDTH-1:0] dout;
  wire full;
  wire empty;
  integer errors = 0;

  fifo_sync #(.DATA_WIDTH(DATA_WIDTH), .DEPTH(DEPTH)) dut (
    .clk(clk), .rst(rst), .wr_en(wr_en), .rd_en(rd_en), .din(din),
    .dout(dout), .full(full), .empty(empty)
  );

  always #5 clk = ~clk;

  task automatic drive;
    input next_wr_en;
    input next_rd_en;
    input [DATA_WIDTH-1:0] next_din;
    begin
      @(negedge clk);
      wr_en = next_wr_en;
      rd_en = next_rd_en;
      din = next_din;
      @(posedge clk);
      #1;
    end
  endtask

  task automatic expect_flags;
    input expected_full;
    input expected_empty;
    begin
      if (full !== expected_full || empty !== expected_empty) begin
        $display("OBLIGATION_FAIL:O_FLAGS");
        $display("FLAG_FAIL full=%b empty=%b expected=%b/%b", full, empty,
                 expected_full, expected_empty);
        errors = errors + 1;
      end
    end
  endtask

  task automatic expect_data;
    input [DATA_WIDTH-1:0] expected;
    begin
      if (dout !== expected) begin
        $display("OBLIGATION_FAIL:O_ORDERING");
        $display("DATA_FAIL dout=%h expected=%h", dout, expected);
        errors = errors + 1;
      end
    end
  endtask

  initial begin
    $dumpfile("fifo_sync.vcd");
    $dumpvars(0, tb_fifo_sync);

    rst = 1'b1;
    drive(1'b1, 1'b1, 8'hEE);
    rst = 1'b0;
    expect_flags(1'b0, 1'b1);
    expect_data(8'h00);

    // Empty simultaneous request: write only, with no read-through.
    drive(1'b1, 1'b1, 8'hA1);
    if (empty !== 1'b0 || dout !== 8'h00) begin
      $display("OBLIGATION_FAIL:O_EMPTY_SIMULTANEOUS");
      errors = errors + 1;
    end
    expect_flags(1'b0, 1'b0);
    expect_data(8'h00);
    drive(1'b0, 1'b1, 8'h00);
    expect_data(8'hA1);
    expect_flags(1'b0, 1'b1);

    drive(1'b1, 1'b0, 8'h11);
    drive(1'b1, 1'b0, 8'h22);
    drive(1'b1, 1'b0, 8'h33);
    drive(1'b1, 1'b0, 8'h44);
    expect_flags(1'b1, 1'b0);

    // Full simultaneous request: read oldest and accept replacement.
    drive(1'b1, 1'b1, 8'h55);
    if (full !== 1'b1 || dout !== 8'h11) begin
      $display("OBLIGATION_FAIL:O_FULL_SIMULTANEOUS");
      errors = errors + 1;
    end
    expect_data(8'h11);
    expect_flags(1'b1, 1'b0);

    drive(1'b0, 1'b1, 8'h00); expect_data(8'h22);
    drive(1'b0, 1'b1, 8'h00); expect_data(8'h33);
    drive(1'b0, 1'b1, 8'h00); expect_data(8'h44);
    drive(1'b0, 1'b1, 8'h00); expect_data(8'h55);
    expect_flags(1'b0, 1'b1);

    // Illegal empty read changes neither flags nor dout.
    drive(1'b0, 1'b1, 8'h00);
    expect_data(8'h55);
    expect_flags(1'b0, 1'b1);

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $display("RTLREASON_RESULT:FAIL errors=%0d", errors);
    $fatal(1);
  end
endmodule
