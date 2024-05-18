////////////////////////////////////////////////////////////////////////////////
// FpgaTop
////////////////////////////////////////////////////////////////////////////////
module FpgaTop (
    input logic clk,
    input logic clk2,
    input logic n_rst,

    // GPIO
    output logic [7:0] output_pins,
    input logic [7:0] input_pins,

    // GPIO2
    output logic [7:0] output_pins2,
    input logic [7:0] input_pins2,

    // GPIO3
    output logic [7:0] output_pins3,
    output logic       output_pins3_update,

    // GPIO4
    output logic [7:0] output_pins4,
    output logic       output_pins4_update,

    // UART
    input logic rxd,
    output logic txd,
    input logic cts,
    output logic rts,
    output logic n_tx_en,

    // SIMULATION
    input logic is_sim,

    // BUS INTERFACE MONITOR
    output logic        bus_mon_n_we,
    output logic        bus_mon_data_out_en,
    output logic        bus_mon_n_ras_a,
    output logic        bus_mon_n_ras_b,
    output logic        bus_mon_n_nren,
    output logic        bus_mon_n_cas_0,
    output logic        bus_mon_n_cas_1,
    output logic [10:0] bus_mon_addr,
    output logic [7:0]  bus_mon_data_out,
    output logic        bus_mon_bus_en

);

    logic rst;
    logic [3:0] drq;
    logic n_int;

    logic        ext_bus_tc;
    logic        ext_bus_n_we;
    logic        ext_bus_data_out_en;
    logic        ext_bus_n_ras_a;
    logic        ext_bus_n_ras_b;
    logic        ext_bus_n_nren;
    logic [3:0]  ext_bus_n_dack;
    logic        ext_bus_n_cas_0;
    logic        ext_bus_n_cas_1;
    logic [10:0] ext_bus_addr;
    logic [7:0]  ext_bus_data_out;
    logic        ext_bus_bus_en;
    logic [7:0]  ext_bus_data_in;
    logic        ext_bus_n_wait;

    logic [15:0] system_io_apb_if_paddr;
    logic [7:0]  system_io_apb_if_pwdata;
    logic        system_io_apb_if_pwrite;
    logic        system_io_apb_if_psel;
    logic        system_io_apb_if_penable;
    logic [7:0]  system_io_apb_if_prdata;
    logic        system_io_apb_if_pready;

    assign drq = 1'h0;

    assign rst =  ~ n_rst;

    BrewV1Top brew (
        .clk(clk),
        .rst(rst),
        .dram_addr(ext_bus_addr),
        .dram_bus_en(ext_bus_bus_en),
        .dram_data_in(ext_bus_data_in),
        .dram_data_out(ext_bus_data_out),
        .dram_data_out_en(ext_bus_data_out_en),
        .dram_n_cas_0(ext_bus_n_cas_0),
        .dram_n_cas_1(ext_bus_n_cas_1),
        .dram_n_dack(ext_bus_n_dack),
        .dram_n_nren(ext_bus_n_nren),
        .dram_n_ras_a(ext_bus_n_ras_a),
        .dram_n_ras_b(ext_bus_n_ras_b),
        .dram_n_wait(ext_bus_n_wait),
        .dram_n_we(ext_bus_n_we),
        .dram_tc(ext_bus_tc),

        .drq(drq),
        .n_int(n_int)
    );

    FpgaSystem system (
        .clk(clk),
        .clk2(clk2),
        .rst(rst),
        .brew_if_addr(ext_bus_addr),
        .brew_if_bus_en(ext_bus_bus_en),
        .brew_if_data_in(ext_bus_data_in),
        .brew_if_data_out(ext_bus_data_out),
        .brew_if_data_out_en(ext_bus_data_out_en),
        .brew_if_n_cas_0(ext_bus_n_cas_0),
        .brew_if_n_cas_1(ext_bus_n_cas_1),
        .brew_if_n_dack(ext_bus_n_dack),
        .brew_if_n_nren(ext_bus_n_nren),
        .brew_if_n_ras_a(ext_bus_n_ras_a),
        .brew_if_n_ras_b(ext_bus_n_ras_b),
        .brew_if_n_wait(ext_bus_n_wait),
        .brew_if_n_we(ext_bus_n_we),
        .brew_if_tc(ext_bus_tc),

        .io_apb_if_paddr    (system_io_apb_if_paddr),
        .io_apb_if_penable  (system_io_apb_if_penable),
        .io_apb_if_prdata   (system_io_apb_if_prdata),
        .io_apb_if_pready   (system_io_apb_if_pready),
        .io_apb_if_psel     (system_io_apb_if_psel),
        .io_apb_if_pwdata   (system_io_apb_if_pwdata),
        .io_apb_if_pwrite   (system_io_apb_if_pwrite),

        .output_pins(output_pins),
        .input_pins(input_pins),

        .output_pins2(output_pins2),
        .input_pins2(input_pins2),

        .is_sim(is_sim),

        .n_int(n_int)
    );

    logic uart1_psel;
    assign uart1_psel = system_io_apb_if_psel & (system_io_apb_if_paddr[15:8] == 8'h00);
    logic uart_int;
    logic [7:0] uart1_prdata;
    logic uart1_pready;

    ApbUart uart1 (
        .clk(clk2),
        .rst(rst),
        .bus_if_paddr    (system_io_apb_if_paddr[2:0]),
        .bus_if_penable  (system_io_apb_if_penable),
        .bus_if_prdata   (uart1_prdata),
        .bus_if_pready   (uart1_pready),
        .bus_if_psel     (uart1_psel),
        .bus_if_pwdata   (system_io_apb_if_pwdata),
        .bus_if_pwrite   (system_io_apb_if_pwrite),

        .interrupt  (uart_int),
        .rxd        (rxd),
        .txd        (txd),
        .cts        (cts),
        .rts        (rts),
        .n_tx_en    (n_tx_en)
    );

    logic gpio3_psel;
    assign gpio3_psel = system_io_apb_if_psel & (system_io_apb_if_paddr[15:8] == 8'h01);
    logic [7:0] gpio3_prdata;
    logic gpio3_pready;

    ApbGpio gpio3 (
        .clk(clk2),
        .rst(rst),
        .bus_if_paddr    (system_io_apb_if_paddr[2:0]),
        .bus_if_penable  (system_io_apb_if_penable),
        .bus_if_prdata   (gpio3_prdata),
        .bus_if_pready   (gpio3_pready),
        .bus_if_psel     (gpio3_psel),
        .bus_if_pwdata   (system_io_apb_if_pwdata),
        .bus_if_pwrite   (system_io_apb_if_pwrite),

        .output_port (output_pins3),
        .output_update (output_pins3_update)
    );

    logic gpio4_psel;
    assign gpio4_psel = system_io_apb_if_psel & (system_io_apb_if_paddr[15:8] == 8'h02);
    logic [7:0] gpio4_prdata;
    logic gpio4_pready;

    ApbGpio gpio4 (
        .clk(clk2),
        .rst(rst),
        .bus_if_paddr    (system_io_apb_if_paddr[2:0]),
        .bus_if_penable  (system_io_apb_if_penable),
        .bus_if_prdata   (gpio4_prdata),
        .bus_if_pready   (gpio4_pready),
        .bus_if_psel     (gpio4_psel),
        .bus_if_pwdata   (system_io_apb_if_pwdata),
        .bus_if_pwrite   (system_io_apb_if_pwrite),

        .output_port (output_pins4),
        .output_update (output_pins4_update)
    );

    assign system_io_apb_if_prdata =
        uart1_psel ? uart1_prdata :
        gpio3_psel ? gpio3_prdata :
        gpio4_psel ? gpio4_prdata :
        8'bX;

    assign system_io_apb_if_pready =
        uart1_psel ? uart1_pready :
        gpio3_psel ? gpio3_pready :
        gpio4_psel ? gpio4_pready :
        1'bX;


    assign bus_mon_n_we = ext_bus_n_we;
    assign bus_mon_data_out_en = ext_bus_data_out_en;
    assign bus_mon_n_ras_a = ext_bus_n_ras_a;
    assign bus_mon_n_ras_b = ext_bus_n_ras_b;
    assign bus_mon_n_nren = ext_bus_n_nren;
    assign bus_mon_n_cas_0 = ext_bus_n_cas_0;
    assign bus_mon_n_cas_1 = ext_bus_n_cas_1;
    assign bus_mon_addr = ext_bus_addr;
    assign bus_mon_data_out = ext_bus_data_out;
    assign bus_mon_bus_en = ext_bus_bus_en;

endmodule
