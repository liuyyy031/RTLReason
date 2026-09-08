module tb_cache_tag_lookup;
 localparam WAYS=4,TW=3,DW=8,WW=2;
 reg[TW-1:0] lookup_tag=0;reg[WAYS-1:0]valid=0;
 reg[WAYS*TW-1:0]tags=0;reg[WAYS*DW-1:0]data=0;
 wire hit;wire[WW-1:0]hit_way;wire[DW-1:0]hit_data;integer errors=0;
 wire hit_min;wire hit_way_min;wire[DW-1:0]hit_data_min;
 cache_tag_lookup #(.WAYS(WAYS),.TAG_WIDTH(TW),.DATA_WIDTH(DW))dut(.*);
 cache_tag_lookup #(.WAYS(2),.TAG_WIDTH(TW),.DATA_WIDTH(DW))dut_min(
  .lookup_tag(lookup_tag),.valid(valid[1:0]),.tags(tags[2*TW-1:0]),
  .data(data[2*DW-1:0]),.hit(hit_min),.hit_way(hit_way_min),.hit_data(hit_data_min));
 task check;input c;input[8*32-1:0]o;begin if(!c)begin errors=errors+1;$display("OBLIGATION_FAIL:%0s",o);end end endtask
 initial begin
  $dumpfile("cache_tag_lookup.vcd");$dumpvars(0,tb_cache_tag_lookup);
  tags[0*TW +: TW]=3'd3;data[0*DW +: DW]=8'h10;
  tags[1*TW +: TW]=3'd5;data[1*DW +: DW]=8'h21;
  tags[2*TW +: TW]=3'd5;data[2*DW +: DW]=8'h42;
  tags[3*TW +: TW]=3'd7;data[3*DW +: DW]=8'h83;
  lookup_tag=5;valid=0;#1;check(!hit&&hit_way==0&&hit_data==0,"O_MISS");
  valid=4'b0100;#1;check(hit&&hit_way==2&&hit_data==8'h42,"O_SINGLE_HIT");
  valid=4'b0110;#1;check(hit&&hit_way==1&&hit_data==8'h21,"O_MULTI_HIT_PRIORITY");
  check(hit_min&&hit_way_min==1&&hit_data_min==8'h21,"O_COMBINATIONAL");
  lookup_tag=3;valid=4'b0001;#1;check(hit&&hit_way==0&&hit_data==8'h10,"O_PACKING");
  lookup_tag=7;valid=4'b1000;#1;check(hit&&hit_way==3&&hit_data==8'h83,"O_SINGLE_HIT");
  lookup_tag=5;valid=4'b1001;#1;check(!hit&&hit_way==0&&hit_data==0,"O_VALID_MATCH");
  if(errors==0)begin $display("RTLREASON_RESULT:PASS");$finish;end
  $fatal(1,"RTLREASON_RESULT:FAIL errors=%0d",errors);
 end
endmodule
