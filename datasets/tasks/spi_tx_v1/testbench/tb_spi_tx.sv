module tb_spi_tx;
  reg clk=0, rst=0, start=0; reg [7:0] data_in=0;
  wire sclk, mosi, busy, done;
  wire sclk_min, mosi_min, busy_min, done_min;
  reg prev_sclk=0, prev_sclk_min=0;
  reg [7:0] received=0, received_min=0;
  integer rises=0, rises_min=0, cycles=0, errors=0;
  reg saw_done=0, saw_done_min=0;
  spi_tx #(.HALF_PERIOD_CYCLES(2)) dut (.*);
  spi_tx #(.HALF_PERIOD_CYCLES(1)) dut_min(
    .clk(clk),.rst(rst),.start(start),.data_in(data_in),
    .sclk(sclk_min),.mosi(mosi_min),.busy(busy_min),.done(done_min));
  always #5 clk=~clk;

  task tick; input nrst; input nstart; input [7:0] ndata; begin
    @(negedge clk); rst=nrst; start=nstart; data_in=ndata;
    @(posedge clk); #1;
    if (!prev_sclk && sclk) begin received={received[6:0],mosi}; rises=rises+1; end
    if (!prev_sclk_min && sclk_min) begin
      received_min={received_min[6:0],mosi_min}; rises_min=rises_min+1;
    end
    if (done) saw_done=1;
    if (done_min) saw_done_min=1;
    prev_sclk=sclk; prev_sclk_min=sclk_min;
  end endtask
  task check; input condition; input [8*32-1:0] obligation; begin
    if (!condition) begin errors=errors+1; $display("OBLIGATION_FAIL:%0s",obligation); end
  end endtask

  initial begin
    $dumpfile("spi_tx.vcd"); $dumpvars(0,tb_spi_tx);
    tick(1,1,8'hA6);
    check(!busy && !done && !sclk && !mosi,"O_RESET");
    tick(0,1,8'hA6);
    check(busy && !sclk && mosi,"O_START");
    cycles=0;
    while ((busy || busy_min) && cycles < 50) begin
      tick(0,(cycles==4),8'hFF);
      if (cycles==4)
        check(mosi==0,"O_BUSY_IGNORE");
      cycles=cycles+1;
    end
    check(rises==8 && received==8'hA6,"O_MSB_FIRST");
    check(rises_min==8 && received_min==8'hA6,"O_MSB_FIRST");
    check(saw_done && saw_done_min,"O_DONE");
    check(!busy && !sclk && !mosi,"O_COMPLETE");
    tick(0,0,0);
    check(!done && !done_min,"O_DONE");
    check(!busy && !sclk && !mosi && !done,"O_IDLE");
    check(!busy_min && !sclk_min && !mosi_min && !done_min,"O_IDLE");

    tick(0,1,8'h5A); tick(0,0,0); tick(1,0,0);
    check(!busy && !done && !sclk && !mosi,"O_RESET");
    if(errors==0) begin $display("RTLREASON_RESULT:PASS"); $finish; end
    $fatal(1,"RTLREASON_RESULT:FAIL errors=%0d",errors);
  end
endmodule
