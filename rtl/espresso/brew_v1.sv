

////////////////////////////////////////////////////////////////////////////////
// Pipeline
////////////////////////////////////////////////////////////////////////////////
module brew_v1 (
    input  logic        clk,
    input  logic        rst,
    inout  logic        dram_n_nren,
    inout  logic        dram_n_ras_a,
    inout  logic        dram_n_ras_b,
    inout  logic        dram_n_cas_0,
    inout  logic        dram_n_cas_1,
    inout  logic [10:0] dram_addr,
    inout  logic        dram_n_we,
    inout  logic [7:0]  dram_data,
    input  logic        dram_n_wait,
    input  logic [3:0]  drq,
    output logic [3:0]  n_dack,
    output logic        tc,
    input  logic        n_int
);
    logic        p_dram_n_nren;
    logic        p_dram_n_ras_a;
    logic        p_dram_n_ras_b;
    logic        p_dram_n_cas_0;
    logic        p_dram_n_cas_1;
    logic [10:0] p_dram_addr;
    logic        p_dram_n_we;
    logic [7:0]  p_dram_data_out;
    logic        p_dram_data_out_en;
    logic        p_bus_en;

    BrewV1Top brew_v1_top(
        .clk                 (clk),
        .rst                 (rst),

        .dram_n_nren         (p_dram_n_nren),
        .dram_n_ras_a        (p_dram_n_ras_a),
        .dram_n_ras_b        (p_dram_n_ras_b),
        .dram_n_cas_0        (p_dram_n_cas_0),
        .dram_n_cas_1        (p_dram_n_cas_1),
        .dram_addr           (p_dram_addr),
        .dram_n_we           (p_dram_n_we),
        .dram_data_in        (dram_data),
        .dram_data_out       (p_dram_data_out),
        .dram_data_out_en    (p_dram_data_out_en),
        .dram_n_wait         (dram_n_wait),
        .dram_n_dack         (n_dack),
        .dram_tc             (tc),
        .dram_bus_en         (p_bus_en),
        .n_int               (n_int),
        .drq                 (drq)
    );

    assign dram_n_ras_a = p_bus_en ? p_dram_n_ras_a : 1'bZ;
    assign dram_n_ras_b = p_bus_en ? p_dram_n_ras_b : 1'bZ;
    assign dram_n_nren = p_bus_en ? p_dram_n_nren : 1'bZ;
    assign dram_n_cas_0 = p_bus_en ? p_dram_n_cas_0 : 1'bZ;
    assign dram_n_cas_1 = p_bus_en ? p_dram_n_cas_1 : 1'bZ;
    assign dram_addr = p_bus_en ? p_dram_addr : 11'bZ;
    assign dram_n_we = p_bus_en ? p_dram_n_we : 1'bZ;
    assign dram_data = (p_bus_en & p_dram_data_out_en) ? p_dram_data_out : 8'bZ;

endmodule
