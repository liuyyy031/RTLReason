module uart_rx_formal;
    localparam integer CLKS_PER_BIT = 4;
    localparam integer HALF_CLKS = CLKS_PER_BIT / 2;
    localparam [1:0] IDLE = 0, START = 1, DATA = 2, STOP = 3;

    reg clk = 0;
    always @($global_clock) clk <= !clk;
    reg rst = 1;
    (* anyseq *) reg rx;
    wire [7:0] data_out;
    wire data_valid, framing_error, busy;

    reg [1:0] model_state = IDLE;
    reg [$clog2(CLKS_PER_BIT+1)-1:0] model_count = 0;
    reg [2:0] model_bit_index = 0;
    reg [7:0] model_shift = 0;
    reg [7:0] model_data = 0;
    reg model_valid = 0;
    reg model_error = 0;
    reg model_busy = 0;
    reg past_valid = 0;

    uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) dut (.*);

    always @(posedge clk) begin
        past_valid <= 1;
        rst <= 0;
        if (past_valid) begin
            assert(data_out == model_data);
            assert(data_valid == model_valid);
            assert(framing_error == model_error);
            assert(busy == model_busy);
            assert(!(data_valid && $past(data_valid)));
            assert(!framing_error || data_valid);
        end

        if (rst) begin
            model_state <= IDLE;
            model_count <= 0;
            model_bit_index <= 0;
            model_shift <= 0;
            model_data <= 0;
            model_valid <= 0;
            model_error <= 0;
            model_busy <= 0;
        end else begin
            model_valid <= 0;
            model_error <= 0;
            case (model_state)
                IDLE: begin
                    model_busy <= 0;
                    model_count <= 0;
                    if (!rx) begin
                        model_state <= START;
                        model_busy <= 1;
                    end
                end
                START: begin
                    if (model_count == HALF_CLKS-1) begin
                        model_count <= 0;
                        if (!rx) begin
                            model_state <= DATA;
                            model_bit_index <= 0;
                        end else begin
                            model_state <= IDLE;
                            model_busy <= 0;
                        end
                    end else begin
                        model_count <= model_count + 1'b1;
                    end
                end
                DATA: begin
                    if (model_count == CLKS_PER_BIT-1) begin
                        model_count <= 0;
                        model_shift[model_bit_index] <= rx;
                        if (model_bit_index == 7)
                            model_state <= STOP;
                        else
                            model_bit_index <= model_bit_index + 1'b1;
                    end else begin
                        model_count <= model_count + 1'b1;
                    end
                end
                STOP: begin
                    if (model_count == CLKS_PER_BIT-1) begin
                        model_count <= 0;
                        model_data <= model_shift;
                        model_valid <= 1;
                        model_error <= !rx;
                        model_state <= IDLE;
                        model_busy <= 0;
                    end else begin
                        model_count <= model_count + 1'b1;
                    end
                end
            endcase
        end
    end
endmodule
