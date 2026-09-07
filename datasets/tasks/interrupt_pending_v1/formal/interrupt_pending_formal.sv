module interrupt_pending_formal;
  reg clk=0; always @($global_clock) clk<=!clk; reg rst=1; (* anyseq *) reg ack; (* anyseq *) reg [3:0] irq,mask;
  wire [3:0] pending; wire valid; wire [1:0] index; interrupt_pending dut(.*);
  reg past_valid=0; reg [3:0] model_pending=0; reg [3:0] clear_mask;
  always @* begin
    clear_mask=0;
    if(model_pending[0])clear_mask=4'b0001;else if(model_pending[1])clear_mask=4'b0010;else if(model_pending[2])clear_mask=4'b0100;else if(model_pending[3])clear_mask=4'b1000;
  end
  always @(posedge clk) begin
    past_valid<=1;rst<=0;
    if(past_valid)begin assert(pending==model_pending);assert(valid==|pending);if(valid)begin if(pending[0])assert(index==0);else if(pending[1])assert(index==1);else if(pending[2])assert(index==2);else assert(index==3);end else assert(index==0);end
    if(rst)model_pending<=0;else model_pending<=(model_pending&~(ack?clear_mask:0))|(irq&~mask);
  end
endmodule
