`timescale 1ns/1ns

module top();

    logic clk;
    logic clk2;
    logic n_rst;

    // GPIO
    logic [7:0] input_pins;
    logic [7:0] output_pins;
    logic [7:0] input_pins2;
    logic [7:0] output_pins2;

    // GPIO3
    logic [7:0] output_pins3;
    logic       output_pins3_update;

    // GPIO4
    logic [7:0] output_pins4;
    logic       output_pins4_update;

    // UART
    logic rxd;
    logic txd;
    logic cts;
    logic rts;
    logic n_tx_en;

    // SIMULATION
    logic is_sim;

    // BUS INTERFACE
    logic        bus_mon_n_we;
    logic        bus_mon_data_out_en;
    logic        bus_mon_n_ras_a;
    logic        bus_mon_n_ras_b;
    logic        bus_mon_n_nren;
    logic        bus_mon_n_cas_0;
    logic        bus_mon_n_cas_1;
    logic [10:0] bus_mon_addr;
    logic [7:0]  bus_mon_data_out;
    logic        bus_mon_bus_en;


    FpgaTop dut(.*);

    initial begin
        clk = 1;
        clk2 = 1;
    end

    assign is_sim = 1'b1;

    always #10 clk2 = ~clk2;
    always #40 clk = ~clk;

    assign cts = 0;

    always @(posedge output_pins4_update) begin
        $write("\n");
        $display("==================== TERMINATING WITH EXIT CODE %d =============", output_pins4);
        $finish;
    end

    always @(posedge output_pins3_update) begin
        $write("%c", output_pins3);
        $fflush();
    end

    initial begin
        $display("Reset applied");
        n_rst = 0;
        #500;
        n_rst = 1;
        $display("Reset removed");
        //#30006 n_rst = 0;
        //#28660 n_rst = 0;
        //$display("Reset applied");
        //#30104 n_rst = 1;
        //$display("Reset removed");
    end

    initial begin
        $dumpfile("anacron_fpga.vcd");
        $dumpvars(0,top);
        #(1000*1000*1000);
        $display("Timeout on simulation");
        $finish;
    end
endmodule
