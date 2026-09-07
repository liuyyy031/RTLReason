module apb_register_bank (
    input  logic        clk,
    input  logic        rst,
    input  logic        psel,
    input  logic        penable,
    input  logic        pwrite,
    input  logic [3:0]  paddr,
    input  logic [31:0] pwdata,
    output logic        pready,
    output logic [31:0] prdata,
    output logic        pslverr
);

    // Registers
    logic [31:0] reg0, reg1;

    // Address decode
    logic valid_addr;
    assign valid_addr = (paddr == 4'h0) || (paddr == 4'h4);

    // Read data
    assign prdata = (paddr == 4'h0) ? reg0 :
                    (paddr == 4'h4) ? reg1 :
                    32'h0;

    // Error signal
    assign pslverr = psel & penable & ~valid_addr;

    // Always ready
    assign pready = 1'b1;

    // Sequential logic
    always_ff @(posedge clk) begin
        if (rst) begin
            reg0 <= 32'h0;
            reg1 <= 32'h0;
        end else if (psel & penable & pwrite & valid_addr) begin
            if (paddr == 4'h0)
                reg0 <= pwdata;
            else // paddr == 4'h4
                reg1 <= pwdata;
        end
    end

endmodule
