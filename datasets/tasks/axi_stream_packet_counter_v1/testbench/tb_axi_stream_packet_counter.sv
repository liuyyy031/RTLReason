module tb_axi_stream_packet_counter;
  localparam integer COUNT_WIDTH = 3;
  localparam [COUNT_WIDTH-1:0] MAXIMUM = {COUNT_WIDTH{1'b1}};
  reg clk = 0;
  reg rst = 0;
  reg clear = 0;
  reg tvalid = 0;
  reg tready = 0;
  reg tlast = 0;
  wire [COUNT_WIDTH-1:0] beat_count;
  wire [COUNT_WIDTH-1:0] packet_count;
  wire beat_count_min;
  wire packet_count_min;
  integer errors = 0;
  integer transfer_index;

  axi_stream_packet_counter #(.COUNT_WIDTH(COUNT_WIDTH)) dut (.*);
  axi_stream_packet_counter #(.COUNT_WIDTH(1)) dut_min (
    .clk(clk),
    .rst(rst),
    .clear(clear),
    .tvalid(tvalid),
    .tready(tready),
    .tlast(tlast),
    .beat_count(beat_count_min),
    .packet_count(packet_count_min)
  );

  always #5 clk = ~clk;

  task drive_edge;
    input next_rst;
    input next_clear;
    input next_tvalid;
    input next_tready;
    input next_tlast;
    begin
      @(negedge clk);
      rst = next_rst;
      clear = next_clear;
      tvalid = next_tvalid;
      tready = next_tready;
      tlast = next_tlast;
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
    $dumpfile("axi_stream_packet_counter.vcd");
    $dumpvars(0, tb_axi_stream_packet_counter);

    drive_edge(1, 1, 1, 1, 1);
    check(beat_count == 0 && packet_count == 0, "O_RESET");
    check(beat_count_min == 0 && packet_count_min == 0, "O_RESET");

    drive_edge(0, 0, 1, 0, 1);
    check(beat_count == 0 && packet_count == 0, "O_TRANSFER_GATE");
    drive_edge(0, 0, 0, 1, 1);
    check(beat_count == 0 && packet_count == 0, "O_HOLD");

    drive_edge(0, 0, 1, 1, 0);
    check(beat_count == 1 && packet_count == 0, "O_BEAT_COUNT");
    check(beat_count_min == 1 && packet_count_min == 0, "O_BEAT_COUNT");
    drive_edge(0, 0, 1, 1, 1);
    check(beat_count == 2 && packet_count == 1, "O_PACKET_COUNT");
    check(beat_count_min == 1 && packet_count_min == 1, "O_SATURATION");

    drive_edge(0, 1, 1, 1, 1);
    check(beat_count == 0 && packet_count == 0, "O_CLEAR");
    check(beat_count_min == 0 && packet_count_min == 0, "O_CLEAR");

    for (transfer_index = 0; transfer_index < MAXIMUM; transfer_index = transfer_index + 1)
      drive_edge(0, 0, 1, 1, 0);
    check(beat_count == MAXIMUM && packet_count == 0, "O_BEAT_COUNT");
    drive_edge(0, 0, 1, 1, 1);
    check(beat_count == MAXIMUM, "O_SATURATION");
    check(packet_count == 1, "O_PACKET_COUNT");

    for (transfer_index = 0; transfer_index < MAXIMUM + 2; transfer_index = transfer_index + 1)
      drive_edge(0, 0, 1, 1, 1);
    check(beat_count == MAXIMUM && packet_count == MAXIMUM, "O_SATURATION");
    check(beat_count_min == 1 && packet_count_min == 1, "O_SATURATION");

    drive_edge(0, 0, 1, 0, 1);
    check(beat_count == MAXIMUM && packet_count == MAXIMUM, "O_HOLD");

    if (errors == 0) begin
      $display("RTLREASON_RESULT:PASS");
      $finish;
    end
    $fatal(1, "RTLREASON_RESULT:FAIL errors=%0d", errors);
  end
endmodule
