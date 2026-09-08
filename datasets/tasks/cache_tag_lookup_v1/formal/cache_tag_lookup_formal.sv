module cache_tag_lookup_formal;
 localparam WAYS=4,TAG_WIDTH=3,DATA_WIDTH=4,WAY_WIDTH=2;
 (* anyconst *)wire[TAG_WIDTH-1:0]lookup_tag;(* anyconst *)wire[WAYS-1:0]valid;
 (* anyconst *)wire[WAYS*TAG_WIDTH-1:0]tags;(* anyconst *)wire[WAYS*DATA_WIDTH-1:0]data;
 wire hit;wire[WAY_WIDTH-1:0]hit_way;wire[DATA_WIDTH-1:0]hit_data;
 wire[WAYS-1:0]match;
 genvar g;generate for(g=0;g<WAYS;g=g+1)begin
  assign match[g]=valid[g]&&(tags[g*TAG_WIDTH +: TAG_WIDTH]==lookup_tag);
 end endgenerate
 cache_tag_lookup #(.WAYS(WAYS),.TAG_WIDTH(TAG_WIDTH),.DATA_WIDTH(DATA_WIDTH))dut(.*);
 always @* begin
  if(match==0)assert(!hit&&hit_way==0&&hit_data==0);
  else if(match[0])assert(hit&&hit_way==0&&hit_data==data[0*DATA_WIDTH +: DATA_WIDTH]);
  else if(match[1])assert(hit&&hit_way==1&&hit_data==data[1*DATA_WIDTH +: DATA_WIDTH]);
  else if(match[2])assert(hit&&hit_way==2&&hit_data==data[2*DATA_WIDTH +: DATA_WIDTH]);
  else assert(hit&&hit_way==3&&hit_data==data[3*DATA_WIDTH +: DATA_WIDTH]);
 end
endmodule
