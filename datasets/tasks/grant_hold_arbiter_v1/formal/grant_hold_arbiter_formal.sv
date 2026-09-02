module grant_hold_arbiter_formal;
  reg clk = 0;
  always @($global_clock) clk <= !clk;
  reg rst = 1;
  (* anyseq *) reg [3:0] req;
  (* anyseq *) reg accept;
  wire [3:0] grant;
  grant_hold_arbiter dut (.*);

  reg past_valid = 0;
  reg [3:0] model_grant = 0;

  function automatic [3:0] model_select;
    input [3:0] requests;
    begin
      if (requests[0]) model_select = 4'b0001;
      else if (requests[1]) model_select = 4'b0010;
      else if (requests[2]) model_select = 4'b0100;
      else if (requests[3]) model_select = 4'b1000;
      else model_select = 4'b0000;
    end
  endfunction

  always @(posedge clk) begin
    past_valid <= 1;
    rst <= 0;
    if (past_valid) begin
      assert(grant == model_grant);
      assert(grant == 0 || (grant & (grant - 1'b1)) == 0);
      if ($past(rst)) assert(grant == 0);
      if (!$past(rst) && $past(model_grant) != 0 && !$past(accept))
        assert(grant == $past(model_grant));
    end

    if (rst) begin
      model_grant <= 0;
    end else if (model_grant != 0) begin
      if (accept) model_grant <= 0;
    end else begin
      model_grant <= model_select(req);
    end
  end
endmodule
