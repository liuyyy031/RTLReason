module programmable_timer_formal;
  localparam integer WIDTH = 4;
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg load, enable;
  (* anyseq *) reg [WIDTH-1:0] period;
  wire [WIDTH-1:0] remaining;
  wire tick;
  programmable_timer #(.WIDTH(WIDTH)) dut (.*);
  reg past_valid = 0;
  reg [WIDTH-1:0] model_period = 1, model_remaining = 1;
  reg model_tick = 0;
  wire [WIDTH-1:0] effective = period == 0 ? 1 : period;
  always @(posedge clk) begin
    past_valid <= 1; rst <= 0;
    if (past_valid) begin assert(remaining == model_remaining); assert(tick == model_tick); assert(remaining != 0); end
    if (rst) begin model_period<=1; model_remaining<=1; model_tick<=0; end
    else if (load) begin model_period<=effective; model_remaining<=effective; model_tick<=0; end
    else if (enable && model_remaining==1) begin model_remaining<=model_period; model_tick<=1; end
    else if (enable) begin model_remaining<=model_remaining-1'b1; model_tick<=0; end
    else model_tick<=0;
  end
endmodule
