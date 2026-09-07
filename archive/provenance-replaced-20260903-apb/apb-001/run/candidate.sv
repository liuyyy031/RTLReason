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

    // Address valid check
    wire valid_addr = (paddr == 4'h0) || (paddr == 4'h4);

    // pready: constant high
    assign pready = 1'b1;

    // prdata: combinational read
    always_comb begin
        case (paddr)
            4'h0: prdata = reg0;
            4'h4: prdata = reg1;
            default: prdata = 32'd0;
        endcase
    end

    // pslverr: asserted only during access-phase transfer to invalid address
    assign pslverr = psel & penable & ~valid_addr;

    // Sequential logic: reset and write
    always_ff @(posedge clk) begin
        if (rst) begin
            reg0 <= 32'd0;
            reg1 <= 32'd0;
        end else begin
            // Write only during access phase with valid address and pwrite
            if (psel & penable & pwrite & valid_addr) begin
                if (paddr == 4'h0)
                    reg0 <= pwdata;
                else // paddr == 4'h4
                    reg1 <= pwdata;
            end
        end
    end

endmodule
