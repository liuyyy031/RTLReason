module spi_tx_formal;
  localparam integer HALF_PERIOD_CYCLES=1;
  reg clk=0; always @($global_clock) clk<=!clk;
  reg rst=1; (* anyseq *) reg start; (* anyseq *) reg [7:0] data_in;
  wire sclk,mosi,busy,done;
  spi_tx #(.HALF_PERIOD_CYCLES(HALF_PERIOD_CYCLES)) dut(.*);
  reg pv=0, msclk=0, mmosi=0, mbusy=0, mdone=0;
  reg [7:0] mword=0; reg [2:0] mbit=0; integer mhalf=0;
  always @(posedge clk) begin
    pv<=1; rst<=0;
    if(pv) begin
      assert(sclk==msclk); assert(mosi==mmosi);
      assert(busy==mbusy); assert(done==mdone);
      if(!busy) assert(sclk==0 && mosi==0);
      if(!$past(rst) && !$past(busy) && !$past(start))
        assert(!busy && !sclk && !mosi && !done);
    end
    if(rst) begin
      msclk<=0; mmosi<=0; mbusy<=0; mdone<=0; mword<=0; mbit<=0; mhalf<=0;
    end else begin
      mdone<=0;
      if(mbusy) begin
        if(mhalf==HALF_PERIOD_CYCLES-1) begin
          mhalf<=0;
          if(!msclk) msclk<=1;
          else begin
            msclk<=0;
            if(mbit==7) begin mbusy<=0; mmosi<=0; mdone<=1; end
            else begin
              mbit<=mbit+1'b1; mword<={mword[6:0],1'b0}; mmosi<=mword[6];
            end
          end
        end else mhalf<=mhalf+1;
      end else if(start) begin
        mword<=data_in; mbit<=0; mhalf<=0; msclk<=0; mmosi<=data_in[7]; mbusy<=1;
      end else begin msclk<=0; mmosi<=0; end
    end
  end
endmodule
