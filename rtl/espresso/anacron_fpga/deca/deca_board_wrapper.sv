////////////////////////////////////////////////////////////////////////////////
// Deca Board Wrapper
////////////////////////////////////////////////////////////////////////////////

// Pinout for USB UART board (component side, connector down, left to right):
//   DTR; RXD; TXD; VCC; CTS; GND
//   The VCC (3.3V) output is internally generated, so it's safe to connect
//   to a GPIO.clk
//
// The way we're going to hook this up is this:
//         GND - P8-2
//   rts - CTS - P8-4  - GPIO0_D[1]
//         VCC - P8-6  - GPIO0_D[3]
//   rxd - TXD - P8-8  - GPIO0_D[5]
//   txd - RXD - P8-10 - GPIO0_D[7]
//   cts - DTR - P8-12 - GPIO0_D[9]
//
// For GPIOs, we will do the following:
//
//  output_pins[0]   -         LED[0]
//  output_pins[1]   -         LED[1]
//  output_pins[2]   -         LED[2]
//  output_pins[3]   -         LED[3]
//  output_pins[4]   -         LED[4]
//  output_pins[5]   -         LED[5]
//  output_pins[6]   -         LED[6]
//  output_pins[7]   -         LED[7]
//
//  output_pins3[0]  - P8-16 - GPIO0_D[13]
//  output_pins3[1]  - P8-18 - GPIO0_D[15]
//  output_pins3[2]  - P8-20 - GPIO0_D[17]
//  output_pins3[3]  - P8-22 - GPIO0_D[19]
//  output_pins3[4]  - P8-24 - GPIO0_D[21]
//  output_pins3[5]  - P8-26 - GPIO0_D[23]
//  output_pins3[6]  - P8-28 - GPIO0_D[25]
//  output_pins3[7]  - P8-30 - GPIO0_D[27]
//
//  output_pins4[0]  - P8-32 - GPIO0_D[29]
//  output_pins4[1]  - P8-34 - GPIO0_D[31]
//  output_pins4[2]  - P8-36 - GPIO0_D[33]
//  output_pins4[3]  - P8-38 - GPIO0_D[35]
//  output_pins4[4]  - P8-40 - GPIO0_D[37]
//  output_pins4[5]  - P8-42 - GPIO0_D[39]
//  output_pins4[6]  - P8-44 - GPIO0_D[41]
//  output_pins4[7]  - P8-46 - GPIO0_D[43]

//  input_pins[0]    -         KEY[0]
//  input_pins[1]    -         SW[0]
//  input_pins[2]    - P8-3  - GPIO0_D[0]
//  input_pins[3]    - P8-5  - GPIO0_D[2]
//  input_pins[4]    - P8-7  - GPIO0_D[4]
//  input_pins[5]    - P8-9  - GPIO0_D[6]
//  input_pins[6]    - P8-11 - GPIO0_D[8]
//  input_pins[7]    - P8-13 - GPIO0_D[10]
//
//  input_pins3[0]   - P8-15 - GPIO0_D[12]
//  input_pins3[1]   - P8-17 - GPIO0_D[14]
//  input_pins3[2]   - P8-19 - GPIO0_D[16]
//  input_pins3[3]   - P8-21 - GPIO0_D[18]
//  input_pins3[4]   - P8-23 - GPIO0_D[20]
//  input_pins3[5]   - P8-25 - GPIO0_D[22]
//  input_pins3[6]   - P8-27 - GPIO0_D[24]
//  input_pins3[7]   - P8-29 - GPIO0_D[26]
//
//  input_pins4[0]   - P8-31 - GPIO0_D[28]
//  input_pins4[1]   - P8-33 - GPIO0_D[30]
//  input_pins4[2]   - P8-35 - GPIO0_D[32]
//  input_pins4[3]   - P8-37 - GPIO0_D[34]
//  input_pins4[4]   - P8-39 - GPIO0_D[36]
//  input_pins4[5]   - P8-41 - GPIO0_D[38]
//  input_pins4[6]   - P8-43 - GPIO0_D[40]
//  input_pins4[7]   - P8-45 - GPIO0_D[42]
//
//  clk              - ADC_CLK_10
//  clk2             - MAX10_CLK1_50
//
//  n_rst            -         SW[1] (pulled high, so works)

module DecaTop(
    input logic        MAX10_CLK1_50,
    input logic        ADC_CLK_10,

    //////////// KEY //////////
    input logic[1:0]   KEY,

    //////////// LED //////////
    output logic[7:0]  LED,

    //////////// SW //////////
    input logic[1:0]   SW,

    //////////// BBB Conector //////////
    //input logic        BBB_PWR_BUT,
    //input logic        BBB_SYS_RESET_n,
    inout logic[43:0]  GPIO0_D,
    inout logic[22:0]  GPIO1_D
);

    logic [22:0]cnt;
    logic [22:0]cnt2;
    logic [7:0] output_pins;

    logic clk;
    logic clk2;
    logic locked;

    slow_pll    slow_pll_inst (
        .inclk0 ( ADC_CLK_10 ),
        .c0 ( clk ), // 10MHz output clock
        .c1 ( clk2), // 50MHz output clock
        .locked ( locked )
        );

    //always @(posedge clk) begin
    //    cnt <= cnt + 1'b1;
    //end
    //always @(posedge clk2) begin
    //    cnt2 <= cnt2 + 1'b1;
    //end
    //assign GPIO1_D = {cnt[22:11], cnt2[22:11]};
    assign LED = output_pins;

    // Re-capture control signals on the falling edge of the faster clock.ADC_CLK_10
    // The rising edge of both clocks align.
    logic slow_ras_a;
    logic slow_ras_b;
    logic slow_cas_0;
    logic slow_cas_1;

    logic fast_ras_a;
    logic fast_ras_b;
    logic fast_cas_0;
    logic fast_cas_1;

    always @(negedge clk2) fast_ras_a <= slow_ras_a;
    always @(negedge clk2) fast_ras_b <= slow_ras_b;
    always @(negedge clk2) fast_cas_0 <= slow_cas_0;
    always @(negedge clk2) fast_cas_1 <= slow_cas_1;

    FpgaTop fpga_top(
        .clk(clk),
        .clk2(clk2),
        .n_rst(KEY[1]),

        .output_pins(output_pins),
        .input_pins  ({KEY[0],      SW[0],       GPIO0_D[ 0], GPIO0_D[ 2], GPIO0_D[ 4], GPIO0_D[ 6], GPIO0_D[ 8], GPIO0_D[10]}),

        //.output_pins3({GPIO0_D[13], GPIO0_D[15], GPIO0_D[17], GPIO0_D[19], GPIO0_D[21], GPIO0_D[23], GPIO0_D[25], GPIO0_D[27]}),
        //.input_pins3 ({GPIO0_D[12], GPIO0_D[14], GPIO0_D[16], GPIO0_D[18], GPIO0_D[20], GPIO0_D[22], GPIO0_D[24], GPIO0_D[26]}),

        //.output_pins4({GPIO0_D[29], GPIO0_D[31], GPIO0_D[33], GPIO0_D[35], GPIO0_D[37], GPIO0_D[39], GPIO0_D[41], GPIO0_D[43]}),
        //.input_pins4 ({GPIO0_D[28], GPIO0_D[30], GPIO0_D[32], GPIO0_D[34], GPIO0_D[36], GPIO0_D[38], GPIO0_D[40], GPIO0_D[42]}),

        .rxd(GPIO0_D[5]),
        .txd(GPIO0_D[7]),
        .cts(GPIO0_D[9]),
        .rts(GPIO0_D[1]),

        .is_sim(1'b0),

        .bus_mon_n_ras_a(slow_ras_a),
        .bus_mon_n_ras_b(slow_ras_b),
        .bus_mon_n_cas_0(slow_cas_0),
        .bus_mon_n_cas_1(slow_cas_1),
        .bus_mon_n_nren(GPIO1_D[1]),        // P9-12
        .bus_mon_n_we(GPIO1_D[3]),          // P9-14
        .bus_mon_data_out_en(GPIO1_D[5]),   // P9-16
        .bus_mon_addr(GPIO1_D[16:6]),       // P9-27 ... P9-17
        .bus_mon_data_out({
            GPIO0_D[29],                     // P8-32
            GPIO0_D[31],                     // P8-34
            GPIO0_D[33],                     // P8-36
            GPIO0_D[35],                     // P8-38
            GPIO0_D[37],                     // P8-40
            GPIO0_D[39],                     // P8-42
            GPIO0_D[41],                     // P8-44
            GPIO0_D[43]                      // P8-46
        }),
        .bus_mon_bus_en(GPIO1_D[17])         // P9-28
    );

    assign GPIO1_D[0] = fast_ras_a;       // P9-11
    assign GPIO1_D[2] = fast_cas_0;       // P9-13
    assign GPIO1_D[4] = fast_cas_1;       // P9-15

    assign GPIO1_D[21] = clk;
    assign GPIO1_D[22] = clk2;

endmodule