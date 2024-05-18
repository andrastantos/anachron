////////////////////////////////////////////////////////////////////////////////
// Type definitions
////////////////////////////////////////////////////////////////////////////////
`define BusIfStates__idle 4'h0
`define BusIfStates__first 4'h1
`define BusIfStates__middle 4'h2
`define BusIfStates__external 4'h3
`define BusIfStates__precharge 4'h4
`define BusIfStates__non_dram_first 4'h5
`define BusIfStates__non_dram_wait 4'h6
`define BusIfStates__non_dram_dual 4'h7
`define BusIfStates__non_dram_dual_first 4'h8
`define BusIfStates__non_dram_dual_wait 4'h9
`define BusIfStates__dma_first 4'ha
`define BusIfStates__dma_wait 4'hb
`define BusIfStates__refresh 4'hc


`define Ports__fetch_port 2'h0
`define Ports__mem_port 2'h1
`define Ports__dma_port 2'h2
`define Ports__refresh_port 2'h3


`define alu_ops__a_plus_b 3'h0
`define alu_ops__a_minus_b 3'h1
`define alu_ops__a_and_b 3'h2
`define alu_ops__n_b_and_a 3'h3
`define alu_ops__a_or_b 3'h4
`define alu_ops__a_xor_b 3'h5
`define alu_ops__tpc 3'h6
`define alu_ops__pc_plus_b 3'h7


`define branch_ops__cb_eq 4'h1
`define branch_ops__cb_ne 4'h2
`define branch_ops__cb_lts 4'h3
`define branch_ops__cb_ges 4'h4
`define branch_ops__cb_lt 4'h5
`define branch_ops__cb_ge 4'h6
`define branch_ops__bb_one 4'h7
`define branch_ops__bb_zero 4'h8
`define branch_ops__swi 4'h9
`define branch_ops__stm 4'ha
`define branch_ops__pc_w 4'hb
`define branch_ops__tpc_w 4'hc


`define op_class__alu 3'h0
`define op_class__mult 3'h1
`define op_class__shift 3'h2
`define op_class__branch 3'h3
`define op_class__ld_st 3'h4


`define ldst_ops__store 1'h0
`define ldst_ops__load 1'h1


`define shifter_ops__shll 2'h0
`define shifter_ops__shlr 2'h1
`define shifter_ops__shar 2'h2


`define InstBufferStates__idle 2'h0
`define InstBufferStates__request 2'h1
`define InstBufferStates__flushing 2'h2


`define InstAssembleStates__have_0_fragments 2'h0
`define InstAssembleStates__need_1_fragments 2'h1
`define InstAssembleStates__need_2_fragments 2'h2
`define InstAssembleStates__have_all_fragments 2'h3





////////////////////////////////////////////////////////////////////////////////
// FpgaTop
////////////////////////////////////////////////////////////////////////////////
module FpgaTop (
	input logic clk,
	input logic clk2,
	input logic n_rst,
	output logic [7:0] output_pins,
	input logic [7:0] input_pins
);

	logic rst;
	logic [7:0] system_io_apb_if_prdata;
	logic system_io_apb_if_pready;
	logic [3:0] u3_output_port;
	logic u4_output_port;
	logic ext_bus_tc;
	logic ext_bus_n_we;
	logic ext_bus_data_out_en;
	logic ext_bus_n_ras_a;
	logic ext_bus_n_ras_b;
	logic ext_bus_n_nren;
	logic [3:0] ext_bus_n_dack;
	logic ext_bus_n_cas_0;
	logic ext_bus_n_cas_1;
	logic [10:0] ext_bus_addr;
	logic [7:0] ext_bus_data_out;
	logic ext_bus_bus_en;
	logic [7:0] ext_bus_data_in;
	logic ext_bus_n_wait;
	logic [15:0] system_io_apb_if_paddr;
	logic [7:0] system_io_apb_if_pwdata;
	logic system_io_apb_if_pwrite;
	logic system_io_apb_if_psel;
	logic system_io_apb_if_penable;

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

		.drq(u3_output_port),
		.n_int(u4_output_port)
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

		.io_apb_if_paddr(system_io_apb_if_paddr),
		.io_apb_if_penable(system_io_apb_if_penable),
		.io_apb_if_prdata(system_io_apb_if_prdata),
		.io_apb_if_pready(system_io_apb_if_pready),
		.io_apb_if_psel(system_io_apb_if_psel),
		.io_apb_if_pwdata(system_io_apb_if_pwdata),
		.io_apb_if_pwrite(system_io_apb_if_pwrite),

		.output_pins(output_pins),
		.input_pins(input_pins)
	);

	assign system_io_apb_if_prdata = system_io_apb_if_prdata;
	assign system_io_apb_if_pready = system_io_apb_if_pready;
	assign u3_output_port = 1'h0;
	assign u4_output_port = 1'h1;
endmodule


////////////////////////////////////////////////////////////////////////////////
// FpgaSystem
////////////////////////////////////////////////////////////////////////////////
module FpgaSystem (
	input logic clk,
	input logic clk2,
	input logic rst,
	input logic [10:0] brew_if_addr,
	input logic brew_if_bus_en,
	output logic [7:0] brew_if_data_in,
	input logic [7:0] brew_if_data_out,
	input logic brew_if_data_out_en,
	input logic brew_if_n_cas_0,
	input logic brew_if_n_cas_1,
	input logic [3:0] brew_if_n_dack,
	input logic brew_if_n_nren,
	input logic brew_if_n_ras_a,
	input logic brew_if_n_ras_b,
	output logic brew_if_n_wait,
	input logic brew_if_n_we,
	input logic brew_if_tc,

	output logic [15:0] io_apb_if_paddr,
	output logic io_apb_if_penable,
	input logic [7:0] io_apb_if_prdata,
	input logic io_apb_if_pready,
	output logic io_apb_if_psel,
	output logic [7:0] io_apb_if_pwdata,
	output logic io_apb_if_pwrite,

	output logic [7:0] output_pins,
	input logic [7:0] input_pins
);

	logic decode_input_tc;
	logic decode_input_n_we;
	logic decode_input_data_out_en;
	logic decode_input_n_ras_a;
	logic decode_input_n_ras_b;
	logic decode_input_n_nren;
	logic [3:0] decode_input_n_dack;
	logic decode_input_n_cas_0;
	logic decode_input_n_cas_1;
	logic [10:0] decode_input_addr;
	logic [7:0] decode_input_data_out;
	logic decode_input_bus_en;
	logic u3_output_port;
	logic u7_output_port;
	logic u13_output_port;
	logic u14_output_port;
	logic [7:0] dram0_addr;
	logic [7:0] dram1_addr;
	logic [7:0] decode_gpio_data_in;
	logic [7:0] dram0_data_out;
	logic [7:0] dram1_data_out;
	logic [22:0] decode_addr;
	logic decode_rom;
	logic decode_gpio;
	logic decode_io_apb;
	logic [7:0] decode_input_data_in;
	logic decode_input_n_wait;
	logic [7:0] decode_rom_data_in;
	logic [7:0] decode_io_apb_data_in;
	logic decode_io_apb_n_wait;

	always_ff @(posedge clk2) u3_output_port <= rst ? 1'h0 :  ~ brew_if_n_ras_a &  ~ brew_if_n_cas_0;
	always_ff @(posedge clk2) u7_output_port <= rst ? 1'h0 :  ~ brew_if_n_ras_a &  ~ brew_if_n_cas_1;
	assign brew_if_data_in = (u3_output_port ? dram0_data_out : 8'b0) | (u7_output_port ? dram1_data_out : 8'b0) | (u3_output_port | u7_output_port ? 8'b0 : decode_input_data_in);

	Dram dram0 (
		.clk(clk2),
		.rst(rst),
		.addr(dram0_addr),
		.data_in(brew_if_data_out),
		.data_out(dram0_data_out),
		.n_ras(brew_if_n_ras_a),
		.n_cas(brew_if_n_cas_0),
		.n_we(brew_if_n_we)
	);

	Dram_2 dram1 (
		.clk(clk2),
		.rst(rst),
		.addr(dram1_addr),
		.data_in(brew_if_data_out),
		.data_out(dram1_data_out),
		.n_ras(brew_if_n_ras_a),
		.n_cas(brew_if_n_cas_1),
		.n_we(brew_if_n_we)
	);

	AddrDecode decode (
		.clk(clk2),
		.brew_if_addr(brew_if_addr),
		.brew_if_bus_en(brew_if_bus_en),
		.brew_if_data_in(decode_input_data_in),
		.brew_if_data_out(brew_if_data_out),
		.brew_if_data_out_en(brew_if_data_out_en),
		.brew_if_n_cas_0(brew_if_n_cas_0),
		.brew_if_n_cas_1(brew_if_n_cas_1),
		.brew_if_n_dack(brew_if_n_dack),
		.brew_if_n_nren(brew_if_n_nren),
		.brew_if_n_ras_a(brew_if_n_ras_a),
		.brew_if_n_ras_b(brew_if_n_ras_b),
		.brew_if_n_wait(decode_input_n_wait),
		.brew_if_n_we(brew_if_n_we),
		.brew_if_tc(brew_if_tc),

		.addr(decode_addr),
		.rom(decode_rom),
		.rom_data_in(decode_rom_data_in),
		.rom_n_wait(u13_output_port),
		.gpio(decode_gpio),
		.gpio_data_in(decode_gpio_data_in),
		.gpio_n_wait(u14_output_port),
		.io_apb(decode_io_apb),
		.io_apb_data_in(decode_io_apb_data_in),
		.io_apb_n_wait(decode_io_apb_n_wait)
	);

	Sram rom (
		.clk(clk2),
		.rst(rst),
		.addr(decode_addr[12:0]),
		.data_in(brew_if_data_out),
		.data_out(decode_rom_data_in),
		.n_ce(decode_rom),
		.n_we(brew_if_n_we)
	);

	Gpio gpio (
		.clk(clk),
		.rst(rst),
		.data_in(brew_if_data_out),
		.data_out(decode_gpio_data_in),
		.n_ce(decode_gpio),
		.n_we(brew_if_n_we),
		.output_pins(output_pins),
		.input_pins(input_pins)
	);

	ApbBridge apb_bridge (
		.clk(clk2),
		.rst(rst),
		.apb_out_paddr(io_apb_if_paddr),
		.apb_out_penable(io_apb_if_penable),
		.apb_out_prdata(io_apb_if_prdata),
		.apb_out_pready(io_apb_if_pready),
		.apb_out_psel(io_apb_if_psel),
		.apb_out_pwdata(io_apb_if_pwdata),
		.apb_out_pwrite(io_apb_if_pwrite),

		.n_ce(decode_io_apb),
		.n_we(brew_if_n_we),
		.n_wait(decode_io_apb_n_wait),
		.addr(decode_addr[15:0]),
		.data_in(brew_if_data_out),
		.data_out(decode_io_apb_data_in)
	);

	assign decode_input_tc = brew_if_tc;
	assign decode_input_n_we = brew_if_n_we;
	assign decode_input_data_out_en = brew_if_data_out_en;
	assign decode_input_n_ras_a = brew_if_n_ras_a;
	assign decode_input_n_ras_b = brew_if_n_ras_b;
	assign decode_input_n_nren = brew_if_n_nren;
	assign decode_input_n_dack = brew_if_n_dack;
	assign decode_input_n_cas_0 = brew_if_n_cas_0;
	assign decode_input_n_cas_1 = brew_if_n_cas_1;
	assign decode_input_addr = brew_if_addr;
	assign decode_input_data_out = brew_if_data_out;
	assign decode_input_bus_en = brew_if_bus_en;
	assign u13_output_port = 1'h1;
	assign u14_output_port = 1'h1;
	assign dram0_addr = brew_if_addr[7:0];
	assign dram1_addr = brew_if_addr[7:0];
	assign brew_if_n_wait = decode_input_n_wait;
endmodule


////////////////////////////////////////////////////////////////////////////////
// ApbBridge
////////////////////////////////////////////////////////////////////////////////
module ApbBridge (
	input logic clk,
	input logic rst,
	output logic [15:0] apb_out_paddr,
	output logic apb_out_penable,
	input logic [7:0] apb_out_prdata,
	input logic apb_out_pready,
	output logic apb_out_psel,
	output logic [7:0] apb_out_pwdata,
	output logic apb_out_pwrite,

	input logic n_ce,
	input logic n_we,
	output logic n_wait,
	input logic [15:0] addr,
	input logic [7:0] data_in,
	output logic [7:0] data_out
);

	logic apb_done;
	logic served;
	logic [7:0] u23_output_port;

	always_ff @(posedge clk) apb_out_paddr <= rst ? 16'h0 :  ~ n_ce ? addr : apb_out_paddr;
	always_ff @(posedge clk) apb_out_pwdata <= rst ? 8'h0 :  ~ n_ce ? data_in : apb_out_pwdata;
	always_ff @(posedge clk) apb_out_pwrite <= rst ? 1'h0 :  ~ n_ce ?  ~ n_we : apb_out_pwrite;
	assign apb_done = apb_out_penable & apb_out_pready;
	always_ff @(posedge clk) served <= rst ? 1'h0 : n_ce ? 1'h0 : apb_done | served;
	always_ff @(posedge clk) apb_out_psel <= rst ? 1'h0 : apb_out_psel ?  ~ apb_done :  ~ n_ce &  ~ served;
	always_ff @(posedge clk) apb_out_penable <= rst ? 1'h0 : apb_out_penable ?  ~ apb_done : apb_out_psel &  ~ served;
	always_ff @(posedge clk) u23_output_port <= rst ? 8'h0 : apb_done ? apb_out_prdata : u23_output_port;
	assign data_out = apb_done ? apb_out_prdata : u23_output_port;
	assign n_wait = apb_done | n_ce | served;

endmodule


////////////////////////////////////////////////////////////////////////////////
// Gpio
////////////////////////////////////////////////////////////////////////////////
module Gpio (
	input logic clk,
	input logic rst,
	input logic [7:0] data_in,
	output logic [7:0] data_out,
	input logic n_ce,
	input logic n_we,
	output logic [7:0] output_pins,
	input logic [7:0] input_pins
);

	logic [7:0] u4_output_port;

	always_ff @(posedge clk) output_pins <= rst ? 8'h0 :  ~ n_ce &  ~ n_we ? data_in : output_pins;
	always_ff @(posedge clk) u4_output_port <= rst ? 8'h0 : input_pins;
	always_ff @(posedge clk) data_out <= rst ? 8'h0 : u4_output_port;

endmodule


////////////////////////////////////////////////////////////////////////////////
// Sram
////////////////////////////////////////////////////////////////////////////////
module Sram (
	input logic clk,
	input logic rst,
	input logic [12:0] addr,
	input logic [7:0] data_in,
	output logic [7:0] data_out,
	input logic n_ce,
	input logic n_we
);

	logic u2_output_port;

	Memory_4 mem (
		.addr(addr),
		.clk(clk),
		.data_in(data_in),
		.data_out(data_out),
		.write_en(u2_output_port)
	);

	assign u2_output_port =  ~ n_ce &  ~ n_we;
endmodule


////////////////////////////////////////////////////////////////////////////////
// AddrDecode
////////////////////////////////////////////////////////////////////////////////
module AddrDecode (
	input logic clk,
	input logic [10:0] brew_if_addr,
	input logic brew_if_bus_en,
	output logic [7:0] brew_if_data_in,
	input logic [7:0] brew_if_data_out,
	input logic brew_if_data_out_en,
	input logic brew_if_n_cas_0,
	input logic brew_if_n_cas_1,
	input logic [3:0] brew_if_n_dack,
	input logic brew_if_n_nren,
	input logic brew_if_n_ras_a,
	input logic brew_if_n_ras_b,
	output logic brew_if_n_wait,
	input logic brew_if_n_we,
	input logic brew_if_tc,

	output logic [22:0] addr,
	output logic rom,
	input logic [7:0] rom_data_in,
	input logic rom_n_wait,
	output logic gpio,
	input logic [7:0] gpio_data_in,
	input logic gpio_n_wait,
	output logic io_apb,
	input logic [7:0] io_apb_data_in,
	input logic io_apb_n_wait
);

	logic prev_n_nren;
	logic [10:0] row_addr;
	logic n_cas;
	logic n_enable;

	always_ff @(posedge clk) prev_n_nren <= brew_if_n_nren;
	always_ff @(posedge clk) row_addr <= ( ~ brew_if_n_nren & prev_n_nren ? brew_if_addr : row_addr);
	assign addr = {row_addr, brew_if_addr, brew_if_n_cas_0};
	assign n_cas = brew_if_n_cas_0 & brew_if_n_cas_1;
	assign rom = addr[22:13] != 1'h0 | n_cas |  ~ brew_if_bus_en | brew_if_n_nren;
	assign gpio = addr[22:12] != 5'h10 | n_cas |  ~ brew_if_bus_en | brew_if_n_nren;
	assign n_enable = addr[22:16] != 2'h2 | n_cas |  ~ brew_if_bus_en | brew_if_n_nren;
	assign brew_if_data_in = ( ~ rom ? rom_data_in : 8'b0) | ( ~ gpio ? gpio_data_in : 8'b0) | ( ~ n_enable ? io_apb_data_in : 8'b0) ;
	assign brew_if_n_wait = ( ~ rom ? rom_n_wait : 1'b0) | ( ~ gpio ? gpio_n_wait : 1'b0) | ( ~ n_enable ? io_apb_n_wait : 1'b0) ;

	assign io_apb = n_enable;
endmodule


////////////////////////////////////////////////////////////////////////////////
// Dram_2
////////////////////////////////////////////////////////////////////////////////
module Dram_2 (
	input logic clk,
	input logic rst,
	input logic [7:0] addr,
	input logic [7:0] data_in,
	output logic [7:0] data_out,
	input logic n_ras,
	input logic n_cas,
	input logic n_we
);

	logic prev_n_ras;
	logic [7:0] row_addr;
	logic u9_output_port;

	always_ff @(posedge clk) prev_n_ras <= rst ? 1'h0 : n_ras;
	always_ff @(posedge clk) row_addr <= rst ? 8'h0 :  ~ n_ras & prev_n_ras ? addr : row_addr;

	Memory_3 mem (
		.addr({row_addr, addr}),
		.clk(clk),
		.data_in(data_in),
		.data_out(data_out),
		.write_en(u9_output_port)
	);

	assign u9_output_port =  ~ n_cas &  ~ n_we &  ~ n_ras;
endmodule


////////////////////////////////////////////////////////////////////////////////
// Dram
////////////////////////////////////////////////////////////////////////////////
module Dram (
	input logic clk,
	input logic rst,
	input logic [7:0] addr,
	input logic [7:0] data_in,
	output logic [7:0] data_out,
	input logic n_ras,
	input logic n_cas,
	input logic n_we
);

	logic prev_n_ras;
	logic [7:0] row_addr;
	logic ram_clk;
	logic u10_output_port;

	always_ff @(posedge clk) prev_n_ras <= rst ? 1'h0 : n_ras;
	always_ff @(posedge clk) row_addr <= rst ? 8'h0 :  ~ n_ras & prev_n_ras ? addr : row_addr;
	assign ram_clk =  ~ clk;

	Memory_2 mem (
		.addr({row_addr, addr}),
		.clk(ram_clk),
		.data_in(data_in),
		.data_out(data_out),
		.write_en(u10_output_port)
	);

	assign u10_output_port =  ~ n_cas &  ~ n_we &  ~ n_ras;
endmodule


////////////////////////////////////////////////////////////////////////////////
// BrewV1Top
////////////////////////////////////////////////////////////////////////////////
module BrewV1Top (
	input logic clk,
	input logic rst,
	output logic [10:0] dram_addr,
	output logic dram_bus_en,
	input logic [7:0] dram_data_in,
	output logic [7:0] dram_data_out,
	output logic dram_data_out_en,
	output logic dram_n_cas_0,
	output logic dram_n_cas_1,
	output logic [3:0] dram_n_dack,
	output logic dram_n_nren,
	output logic dram_n_ras_a,
	output logic dram_n_ras_b,
	input logic dram_n_wait,
	output logic dram_n_we,
	output logic dram_tc,

	input logic [3:0] drq,
	input logic n_int
);

	logic u_output_port;
	logic csr_top_level_psel;
	logic csr_bus_if_psel;
	logic bus_if_reg_if_psel;
	logic dma_reg_if_psel;
	logic csr_dma_psel;
	logic [31:0] csr_if_prdata;
	logic csr_if_pready;
	logic u17_output_port;
	logic [20:0] u19_output_port;
	logic [19:0] event_cnt_0;
	logic u23_output_port;
	logic [20:0] u25_output_port;
	logic [19:0] event_cnt_1;
	logic u29_output_port;
	logic [20:0] u31_output_port;
	logic [19:0] event_cnt_2;
	logic u35_output_port;
	logic [20:0] u37_output_port;
	logic [19:0] event_cnt_3;
	logic csr_write_strobe;
	logic [31:0] u54_output_port;
	logic [31:0] top_level_prdata;
	logic [21:0] pmem_base;
	logic [21:0] pmem_limit;
	logic [21:0] dmem_base;
	logic [21:0] dmem_limit;
	logic [3:0] event_select_0;
	logic [3:0] event_select_1;
	logic [3:0] event_select_2;
	logic [3:0] event_select_3;
	logic [3:0] event_select;
	logic top_level_pready;
	logic event_fetch_wait_on_bus;
	logic event_decode_wait_on_rf;
	logic event_branch;
	logic event_load;
	logic event_store;
	logic event_execute;
	logic [11:0] ecause;
	logic event_branch_taken;
	logic event_mem_wait_on_bus;
	logic fetch_to_bus_valid;
	logic [1:0] fetch_to_bus_byte_en;
	logic [15:0] fetch_to_bus_data;
	logic fetch_to_bus_read_not_write;
	logic [30:0] fetch_to_bus_addr;
	logic [31:0] eaddr;
	logic mem_to_bus_valid;
	logic mem_to_bus_read_not_write;
	logic [1:0] mem_to_bus_byte_en;
	logic [30:0] mem_to_bus_addr;
	logic [15:0] mem_to_bus_data;
	logic csr_if_penable;
	logic bus_if_reg_if_penable;
	logic dma_reg_if_penable;
	logic csr_if_psel;
	logic csr_if_pwrite;
	logic bus_if_reg_if_pwrite;
	logic dma_reg_if_pwrite;
	logic [9:0] csr_if_paddr;
	logic [31:0] csr_if_pwdata;
	logic [31:0] bus_if_reg_if_pwdata;
	logic [31:0] dma_reg_if_pwdata;
	logic [3:0] dma_reg_if_paddr;
	logic [3:0] bus_if_reg_if_paddr;
	logic [3:0] csr_addr;
	logic [31:0] dma_reg_if_prdata;
	logic dma_to_bus_valid;
	logic [3:0] dma_to_bus_one_hot_channel;
	logic dma_to_bus_terminal_count;
	logic dma_to_bus_read_not_write;
	logic [1:0] dma_to_bus_byte_en;
	logic dma_to_bus_is_master;
	logic dma_reg_if_pready;
	logic [30:0] dma_to_bus_addr;
	logic mem_to_bus_ready;
	logic fetch_to_bus_ready;
	logic dma_to_bus_ready;
	logic [15:0] bus_to_mem_data;
	logic bus_to_mem_valid;
	logic bus_to_fetch_valid;
	logic bus_to_dma_valid;
	logic bus_if_reg_if_pready;
	logic [31:0] bus_if_reg_if_prdata;
	logic [15:0] bus_to_fetch_data;

	assign csr_dma_psel = csr_if_psel & csr_if_paddr[5:4] == 2'h2;
	assign dma_reg_if_paddr = csr_if_paddr[3:0];
	assign bus_if_reg_if_paddr = csr_if_paddr[3:0];
	assign csr_bus_if_psel = csr_if_psel & csr_if_paddr[5:4] == 1'h1;
	assign csr_if_prdata = (csr_dma_psel ? dma_reg_if_prdata : 32'b0) | (csr_bus_if_psel ? bus_if_reg_if_prdata : 32'b0) | (csr_dma_psel | csr_bus_if_psel ? 32'b0 : top_level_prdata);
	assign csr_if_pready = (csr_dma_psel ? dma_reg_if_pready : 1'b0) | (csr_bus_if_psel ? bus_if_reg_if_pready : 1'b0) | (csr_dma_psel | csr_bus_if_psel ? 1'b0 : top_level_pready);
	always @(*) begin
		case (event_select_0)
			4'd0: u17_output_port = 1'h1;
			4'd1: u17_output_port = event_fetch_wait_on_bus;
			4'd2: u17_output_port = event_decode_wait_on_rf;
			4'd3: u17_output_port = event_mem_wait_on_bus;
			4'd4: u17_output_port = event_branch_taken;
			4'd5: u17_output_port = event_branch;
			4'd6: u17_output_port = event_load;
			4'd7: u17_output_port = event_store;
			4'd8: u17_output_port = event_execute;
		endcase
	end
	always_ff @(posedge clk) event_cnt_0 <= rst ? 20'h0 : u17_output_port ? u19_output_port[19:0] : event_cnt_0;
	always @(*) begin
		case (event_select_1)
			4'd0: u23_output_port = 1'h1;
			4'd1: u23_output_port = event_fetch_wait_on_bus;
			4'd2: u23_output_port = event_decode_wait_on_rf;
			4'd3: u23_output_port = event_mem_wait_on_bus;
			4'd4: u23_output_port = event_branch_taken;
			4'd5: u23_output_port = event_branch;
			4'd6: u23_output_port = event_load;
			4'd7: u23_output_port = event_store;
			4'd8: u23_output_port = event_execute;
		endcase
	end
	always_ff @(posedge clk) event_cnt_1 <= rst ? 20'h0 : u23_output_port ? u25_output_port[19:0] : event_cnt_1;
	always @(*) begin
		case (event_select_2)
			4'd0: u29_output_port = 1'h1;
			4'd1: u29_output_port = event_fetch_wait_on_bus;
			4'd2: u29_output_port = event_decode_wait_on_rf;
			4'd3: u29_output_port = event_mem_wait_on_bus;
			4'd4: u29_output_port = event_branch_taken;
			4'd5: u29_output_port = event_branch;
			4'd6: u29_output_port = event_load;
			4'd7: u29_output_port = event_store;
			4'd8: u29_output_port = event_execute;
		endcase
	end
	always_ff @(posedge clk) event_cnt_2 <= rst ? 20'h0 : u29_output_port ? u31_output_port[19:0] : event_cnt_2;
	always @(*) begin
		case (event_select)
			4'd0: u35_output_port = 1'h1;
			4'd1: u35_output_port = event_fetch_wait_on_bus;
			4'd2: u35_output_port = event_decode_wait_on_rf;
			4'd3: u35_output_port = event_mem_wait_on_bus;
			4'd4: u35_output_port = event_branch_taken;
			4'd5: u35_output_port = event_branch;
			4'd6: u35_output_port = event_load;
			4'd7: u35_output_port = event_store;
			4'd8: u35_output_port = event_execute;
		endcase
	end
	always_ff @(posedge clk) event_cnt_3 <= rst ? 20'h0 : u35_output_port ? u37_output_port[19:0] : event_cnt_3;
	assign csr_top_level_psel = csr_if_psel & csr_if_paddr[5:4] == 1'h0;
	assign csr_addr = csr_if_paddr[3:0];
	always @(*) begin
		case (csr_addr)
			4'd0: u54_output_port = 1'h0;
			4'd1: u54_output_port = {pmem_base, 10'h0};
			4'd2: u54_output_port = {pmem_limit, 10'h0};
			4'd3: u54_output_port = {dmem_base, 10'h0};
			4'd4: u54_output_port = {dmem_limit, 10'h0};
			4'd5: u54_output_port = ecause;
			4'd6: u54_output_port = eaddr;
			4'd7: u54_output_port = {event_select, event_select_2, event_select_1, event_select_0};
			4'd8: u54_output_port = event_cnt_0;
			4'd9: u54_output_port = event_cnt_1;
			4'd10: u54_output_port = event_cnt_2;
			4'd11: u54_output_port = event_cnt_3;
		endcase
	end
	always_ff @(posedge clk) top_level_prdata <= rst ? 32'h0 : u54_output_port;
	assign csr_write_strobe = csr_top_level_psel & dma_reg_if_pwrite & dma_reg_if_penable;
	always_ff @(posedge clk) pmem_base <= rst ? 22'h0 : csr_addr == 1'h1 & csr_write_strobe ? dma_reg_if_pwdata[31:10] : pmem_base;
	always_ff @(posedge clk) pmem_limit <= rst ? 22'h0 : csr_addr == 2'h2 & csr_write_strobe ? dma_reg_if_pwdata[31:10] : pmem_limit;
	always_ff @(posedge clk) dmem_base <= rst ? 22'h0 : csr_addr == 2'h3 & csr_write_strobe ? dma_reg_if_pwdata[31:10] : dmem_base;
	always_ff @(posedge clk) dmem_limit <= rst ? 22'h0 : csr_addr == 3'h4 & csr_write_strobe ? dma_reg_if_pwdata[31:10] : dmem_limit;
	always_ff @(posedge clk) event_select_0 <= rst ? 4'h0 : csr_addr == 3'h7 & csr_write_strobe ? dma_reg_if_pwdata[3:0] : event_select_0;
	always_ff @(posedge clk) event_select_1 <= rst ? 4'h0 : csr_addr == 3'h7 & csr_write_strobe ? dma_reg_if_pwdata[7:4] : event_select_1;
	always_ff @(posedge clk) event_select_2 <= rst ? 4'h0 : csr_addr == 3'h7 & csr_write_strobe ? dma_reg_if_pwdata[11:8] : event_select_2;
	always_ff @(posedge clk) event_select <= rst ? 4'h0 : csr_addr == 3'h7 & csr_write_strobe ? dma_reg_if_pwdata[15:12] : event_select;
	assign top_level_pready = 1'h1;

	BusIf bus_if (
		.clk(clk),
		.rst(rst),
		.fetch_request_addr(fetch_to_bus_addr),
		.fetch_request_byte_en(fetch_to_bus_byte_en),
		.fetch_request_data(fetch_to_bus_data),
		.fetch_request_read_not_write(fetch_to_bus_read_not_write),
		.fetch_request_ready(fetch_to_bus_ready),
		.fetch_request_valid(fetch_to_bus_valid),

		.fetch_response_data(bus_to_fetch_data),
		.fetch_response_valid(bus_to_fetch_valid),

		.mem_request_addr(mem_to_bus_addr),
		.mem_request_byte_en(mem_to_bus_byte_en),
		.mem_request_data(mem_to_bus_data),
		.mem_request_read_not_write(mem_to_bus_read_not_write),
		.mem_request_ready(mem_to_bus_ready),
		.mem_request_valid(mem_to_bus_valid),

		.mem_response_data(bus_to_mem_data),
		.mem_response_valid(bus_to_mem_valid),

		.dma_request_addr(dma_to_bus_addr),
		.dma_request_byte_en(dma_to_bus_byte_en),
		.dma_request_is_master(dma_to_bus_is_master),
		.dma_request_one_hot_channel(dma_to_bus_one_hot_channel),
		.dma_request_read_not_write(dma_to_bus_read_not_write),
		.dma_request_ready(dma_to_bus_ready),
		.dma_request_terminal_count(dma_to_bus_terminal_count),
		.dma_request_valid(dma_to_bus_valid),

		.dma_response_valid(bus_to_dma_valid),

		.reg_if_paddr(bus_if_reg_if_paddr),
		.reg_if_penable(dma_reg_if_penable),
		.reg_if_prdata(bus_if_reg_if_prdata),
		.reg_if_pready(bus_if_reg_if_pready),
		.reg_if_psel(csr_dma_psel),
		.reg_if_pwdata(dma_reg_if_pwdata),
		.reg_if_pwrite(dma_reg_if_pwrite),

		.dram_addr(dram_addr),
		.dram_bus_en(dram_bus_en),
		.dram_data_in(dram_data_in),
		.dram_data_out(dram_data_out),
		.dram_data_out_en(dram_data_out_en),
		.dram_n_cas_0(dram_n_cas_0),
		.dram_n_cas_1(dram_n_cas_1),
		.dram_n_dack(dram_n_dack),
		.dram_n_nren(dram_n_nren),
		.dram_n_ras_a(dram_n_ras_a),
		.dram_n_ras_b(dram_n_ras_b),
		.dram_n_wait(dram_n_wait),
		.dram_n_we(dram_n_we),
		.dram_tc(dram_tc)
	);

	CpuDma dma (
		.clk(clk),
		.rst(rst),
		.bus_req_if_addr(dma_to_bus_addr),
		.bus_req_if_byte_en(dma_to_bus_byte_en),
		.bus_req_if_is_master(dma_to_bus_is_master),
		.bus_req_if_one_hot_channel(dma_to_bus_one_hot_channel),
		.bus_req_if_read_not_write(dma_to_bus_read_not_write),
		.bus_req_if_ready(dma_to_bus_ready),
		.bus_req_if_terminal_count(dma_to_bus_terminal_count),
		.bus_req_if_valid(dma_to_bus_valid),

		.bus_rsp_if_valid(bus_to_dma_valid),

		.reg_if_paddr(dma_reg_if_paddr),
		.reg_if_penable(dma_reg_if_penable),
		.reg_if_prdata(dma_reg_if_prdata),
		.reg_if_pready(dma_reg_if_pready),
		.reg_if_psel(csr_dma_psel),
		.reg_if_pwdata(dma_reg_if_pwdata),
		.reg_if_pwrite(dma_reg_if_pwrite),

		.drq(drq)
	);

	Pipeline pipeline (
		.clk(clk),
		.rst(rst),
		.fetch_to_bus_addr(fetch_to_bus_addr),
		.fetch_to_bus_byte_en(fetch_to_bus_byte_en),
		.fetch_to_bus_data(fetch_to_bus_data),
		.fetch_to_bus_read_not_write(fetch_to_bus_read_not_write),
		.fetch_to_bus_ready(fetch_to_bus_ready),
		.fetch_to_bus_valid(fetch_to_bus_valid),

		.bus_to_fetch_data(bus_to_fetch_data),
		.bus_to_fetch_valid(bus_to_fetch_valid),

		.mem_to_bus_addr(mem_to_bus_addr),
		.mem_to_bus_byte_en(mem_to_bus_byte_en),
		.mem_to_bus_data(mem_to_bus_data),
		.mem_to_bus_read_not_write(mem_to_bus_read_not_write),
		.mem_to_bus_ready(mem_to_bus_ready),
		.mem_to_bus_valid(mem_to_bus_valid),

		.bus_to_mem_data(bus_to_mem_data),
		.bus_to_mem_valid(bus_to_mem_valid),

		.csr_if_paddr(csr_if_paddr),
		.csr_if_penable(dma_reg_if_penable),
		.csr_if_prdata(csr_if_prdata),
		.csr_if_pready(csr_if_pready),
		.csr_if_psel(csr_if_psel),
		.csr_if_pwdata(dma_reg_if_pwdata),
		.csr_if_pwrite(dma_reg_if_pwrite),

		.ecause(ecause),
		.eaddr(eaddr),
		.pmem_base(pmem_base),
		.pmem_limit(pmem_limit),
		.dmem_base(dmem_base),
		.dmem_limit(dmem_limit),
		.interrupt(u_output_port),
		.fetch_wait_on_bus(event_fetch_wait_on_bus),
		.decode_wait_on_rf(event_decode_wait_on_rf),
		.mem_wait_on_bus(event_mem_wait_on_bus),
		.branch_taken(event_branch_taken),
		.branch(event_branch),
		.load(event_load),
		.store(event_store),
		.execute(event_execute)
	);

	assign u_output_port =  ~ n_int;
	assign bus_if_reg_if_psel = csr_dma_psel;
	assign dma_reg_if_psel = csr_dma_psel;
	assign u19_output_port = event_cnt_0 + 1'h1 + 21'b0;
	assign u25_output_port = event_cnt_1 + 1'h1 + 21'b0;
	assign u31_output_port = event_cnt_2 + 1'h1 + 21'b0;
	assign u37_output_port = event_cnt_3 + 1'h1 + 21'b0;
	assign event_select_3 = event_select;
	assign csr_if_penable = dma_reg_if_penable;
	assign bus_if_reg_if_penable = dma_reg_if_penable;
	assign csr_if_pwrite = dma_reg_if_pwrite;
	assign bus_if_reg_if_pwrite = dma_reg_if_pwrite;
	assign csr_if_pwdata = dma_reg_if_pwdata;
	assign bus_if_reg_if_pwdata = dma_reg_if_pwdata;
endmodule


////////////////////////////////////////////////////////////////////////////////
// Pipeline
////////////////////////////////////////////////////////////////////////////////
module Pipeline (
	input logic clk,
	input logic rst,
	output logic [30:0] fetch_to_bus_addr,
	output logic [1:0] fetch_to_bus_byte_en,
	output logic [15:0] fetch_to_bus_data,
	output logic fetch_to_bus_read_not_write,
	input logic fetch_to_bus_ready,
	output logic fetch_to_bus_valid,

	input logic [15:0] bus_to_fetch_data,
	input logic bus_to_fetch_valid,

	output logic [30:0] mem_to_bus_addr,
	output logic [1:0] mem_to_bus_byte_en,
	output logic [15:0] mem_to_bus_data,
	output logic mem_to_bus_read_not_write,
	input logic mem_to_bus_ready,
	output logic mem_to_bus_valid,

	input logic [15:0] bus_to_mem_data,
	input logic bus_to_mem_valid,

	output logic [9:0] csr_if_paddr,
	output logic csr_if_penable,
	input logic [31:0] csr_if_prdata,
	input logic csr_if_pready,
	output logic csr_if_psel,
	output logic [31:0] csr_if_pwdata,
	output logic csr_if_pwrite,

	output logic [11:0] ecause,
	output logic [31:0] eaddr,
	input logic [21:0] pmem_base,
	input logic [21:0] pmem_limit,
	input logic [21:0] dmem_base,
	input logic [21:0] dmem_limit,
	input logic interrupt,
	output logic fetch_wait_on_bus,
	output logic decode_wait_on_rf,
	output logic mem_wait_on_bus,
	output logic branch_taken,
	output logic branch,
	output logic load,
	output logic store,
	output logic execute
);

	logic [30:0] spc;
	logic [30:0] tpc;
	logic task_mode;
	logic do_branch;
	logic fetch_to_decode_valid;
	logic fetch_to_decode_av;
	logic [15:0] fetch_to_decode_inst_0;
	logic [15:0] fetch_to_decode_inst_1;
	logic [15:0] fetch_to_decode_inst_2;
	logic [1:0] fetch_to_decode_inst_len;
	logic rf_req_valid;
	logic rf_req_read1_valid;
	logic rf_req_read2_valid;
	logic rf_req_rsv_valid;
	logic [2:0] decode_to_exec_exec_unit;
	logic [2:0] decode_to_exec_alu_op;
	logic [1:0] decode_to_exec_shifter_op;
	logic [3:0] decode_to_exec_branch_op;
	logic decode_to_exec_ldst_op;
	logic [31:0] decode_to_exec_op_a;
	logic [31:0] decode_to_exec_op_b;
	logic [31:0] decode_to_exec_op_c;
	logic [1:0] decode_to_exec_inst_len;
	logic decode_to_exec_do_bse;
	logic decode_to_exec_do_wse;
	logic decode_to_exec_do_bze;
	logic decode_to_exec_do_wze;
	logic [3:0] decode_to_exec_result_reg_addr;
	logic decode_to_exec_result_reg_addr_valid;
	logic decode_to_exec_fetch_av;
	logic decode_to_exec_valid;
	logic rf_rsp_ready;
	logic fetch_to_decode_ready;
	logic [3:0] rf_req_read1_addr;
	logic [3:0] rf_req_read2_addr;
	logic [3:0] rf_req_rsv_addr;
	logic [1:0] decode_to_exec_mem_access_len;
	logic decode_to_exec_ready;
	logic execute_stage_complete;
	logic exec_to_extend_valid;
	logic [15:0] exec_to_extend_data_l;
	logic [15:0] exec_to_extend_data_h;
	logic exec_to_extend_data_en;
	logic [3:0] exec_to_extend_addr;
	logic exec_to_extend_do_bse;
	logic exec_to_extend_do_wse;
	logic exec_to_extend_do_bze;
	logic exec_to_extend_do_wze;
	logic execute_stage_do_branch;
	logic [30:0] execute_stage_tpc_out;
	logic [30:0] execute_stage_spc_out;
	logic execute_stage_task_mode_out;
	logic [11:0] execute_stage_ecause_out;
	logic [31:0] rf_write_data;
	logic [3:0] rf_write_addr;
	logic rf_write_data_en;
	logic rf_write_valid;
	logic [31:0] rf_rsp_read1_data;
	logic [31:0] rf_rsp_read2_data;
	logic rf_req_ready;
	logic rf_rsp_valid;

	assign fetch_wait_on_bus = fetch_to_bus_valid &  ~ fetch_to_bus_ready;
	assign decode_wait_on_rf = rf_req_valid &  ~ rf_req_ready;
	assign branch = decode_to_exec_exec_unit == (`op_class__branch &  ~ decode_to_exec_fetch_av);
	assign load = decode_to_exec_exec_unit == `op_class__ld_st & decode_to_exec_ldst_op == `ldst_ops__load &  ~ decode_to_exec_fetch_av;
	assign store = decode_to_exec_exec_unit == `op_class__ld_st & decode_to_exec_ldst_op == `ldst_ops__store &  ~ decode_to_exec_fetch_av;
	assign execute = decode_to_exec_ready & decode_to_exec_valid &  ~ decode_to_exec_fetch_av;
	always_ff @(posedge clk) spc <= rst ? 31'h0 : execute_stage_spc_out;
	always_ff @(posedge clk) tpc <= rst ? 31'h0 : execute_stage_tpc_out;
	always_ff @(posedge clk) task_mode <= rst ? 1'h0 : execute_stage_task_mode_out;
	always_ff @(posedge clk) ecause <= rst ? 12'h0 : execute_stage_ecause_out;
	always_ff @(posedge clk) do_branch <= rst ? 1'h0 : execute_stage_do_branch;
	assign mem_wait_on_bus = mem_to_bus_valid &  ~ mem_to_bus_ready;

	FetchStage fetch_stage (
		.clk(clk),
		.rst(rst),
		.bus_if_request_addr(fetch_to_bus_addr),
		.bus_if_request_byte_en(fetch_to_bus_byte_en),
		.bus_if_request_data(fetch_to_bus_data),
		.bus_if_request_read_not_write(fetch_to_bus_read_not_write),
		.bus_if_request_ready(fetch_to_bus_ready),
		.bus_if_request_valid(fetch_to_bus_valid),

		.bus_if_response_data(bus_to_fetch_data),
		.bus_if_response_valid(bus_to_fetch_valid),

		.decode_av(fetch_to_decode_av),
		.decode_inst_0(fetch_to_decode_inst_0),
		.decode_inst_1(fetch_to_decode_inst_1),
		.decode_inst_2(fetch_to_decode_inst_2),
		.decode_inst_len(fetch_to_decode_inst_len),
		.decode_ready(fetch_to_decode_ready),
		.decode_valid(fetch_to_decode_valid),

		.mem_base(pmem_base),
		.mem_limit(pmem_limit),
		.spc(spc),
		.tpc(tpc),
		.task_mode(task_mode),
		.do_branch(do_branch)
	);

	DecodeStage decode_stage (
		.clk(clk),
		.rst(rst),
		.fetch_av(fetch_to_decode_av),
		.fetch_inst_0(fetch_to_decode_inst_0),
		.fetch_inst_1(fetch_to_decode_inst_1),
		.fetch_inst_2(fetch_to_decode_inst_2),
		.fetch_inst_len(fetch_to_decode_inst_len),
		.fetch_ready(fetch_to_decode_ready),
		.fetch_valid(fetch_to_decode_valid),

		.output_port_alu_op(decode_to_exec_alu_op),
		.output_port_branch_op(decode_to_exec_branch_op),
		.output_port_do_bse(decode_to_exec_do_bse),
		.output_port_do_bze(decode_to_exec_do_bze),
		.output_port_do_wse(decode_to_exec_do_wse),
		.output_port_do_wze(decode_to_exec_do_wze),
		.output_port_exec_unit(decode_to_exec_exec_unit),
		.output_port_fetch_av(decode_to_exec_fetch_av),
		.output_port_inst_len(decode_to_exec_inst_len),
		.output_port_ldst_op(decode_to_exec_ldst_op),
		.output_port_mem_access_len(decode_to_exec_mem_access_len),
		.output_port_op_a(decode_to_exec_op_a),
		.output_port_op_b(decode_to_exec_op_b),
		.output_port_op_c(decode_to_exec_op_c),
		.output_port_ready(decode_to_exec_ready),
		.output_port_result_reg_addr(decode_to_exec_result_reg_addr),
		.output_port_result_reg_addr_valid(decode_to_exec_result_reg_addr_valid),
		.output_port_shifter_op(decode_to_exec_shifter_op),
		.output_port_valid(decode_to_exec_valid),

		.reg_file_req_read1_addr(rf_req_read1_addr),
		.reg_file_req_read1_valid(rf_req_read1_valid),
		.reg_file_req_read2_addr(rf_req_read2_addr),
		.reg_file_req_read2_valid(rf_req_read2_valid),
		.reg_file_req_ready(rf_req_ready),
		.reg_file_req_rsv_addr(rf_req_rsv_addr),
		.reg_file_req_rsv_valid(rf_req_rsv_valid),
		.reg_file_req_valid(rf_req_valid),

		.reg_file_rsp_read1_data(rf_rsp_read1_data),
		.reg_file_rsp_read2_data(rf_rsp_read2_data),
		.reg_file_rsp_ready(rf_rsp_ready),
		.reg_file_rsp_valid(rf_rsp_valid),

		.do_branch(do_branch)
	);

	ExecuteStage execute_stage (
		.clk(clk),
		.rst(rst),
		.input_port_alu_op(decode_to_exec_alu_op),
		.input_port_branch_op(decode_to_exec_branch_op),
		.input_port_do_bse(decode_to_exec_do_bse),
		.input_port_do_bze(decode_to_exec_do_bze),
		.input_port_do_wse(decode_to_exec_do_wse),
		.input_port_do_wze(decode_to_exec_do_wze),
		.input_port_exec_unit(decode_to_exec_exec_unit),
		.input_port_fetch_av(decode_to_exec_fetch_av),
		.input_port_inst_len(decode_to_exec_inst_len),
		.input_port_ldst_op(decode_to_exec_ldst_op),
		.input_port_mem_access_len(decode_to_exec_mem_access_len),
		.input_port_op_a(decode_to_exec_op_a),
		.input_port_op_b(decode_to_exec_op_b),
		.input_port_op_c(decode_to_exec_op_c),
		.input_port_ready(decode_to_exec_ready),
		.input_port_result_reg_addr(decode_to_exec_result_reg_addr),
		.input_port_result_reg_addr_valid(decode_to_exec_result_reg_addr_valid),
		.input_port_shifter_op(decode_to_exec_shifter_op),
		.input_port_valid(decode_to_exec_valid),

		.output_port_addr(exec_to_extend_addr),
		.output_port_data_en(exec_to_extend_data_en),
		.output_port_data_h(exec_to_extend_data_h),
		.output_port_data_l(exec_to_extend_data_l),
		.output_port_do_bse(exec_to_extend_do_bse),
		.output_port_do_bze(exec_to_extend_do_bze),
		.output_port_do_wse(exec_to_extend_do_wse),
		.output_port_do_wze(exec_to_extend_do_wze),
		.output_port_valid(exec_to_extend_valid),

		.bus_req_if_addr(mem_to_bus_addr),
		.bus_req_if_byte_en(mem_to_bus_byte_en),
		.bus_req_if_data(mem_to_bus_data),
		.bus_req_if_read_not_write(mem_to_bus_read_not_write),
		.bus_req_if_ready(mem_to_bus_ready),
		.bus_req_if_valid(mem_to_bus_valid),

		.bus_rsp_if_data(bus_to_mem_data),
		.bus_rsp_if_valid(bus_to_mem_valid),

		.csr_if_paddr(csr_if_paddr),
		.csr_if_penable(csr_if_penable),
		.csr_if_prdata(csr_if_prdata),
		.csr_if_pready(csr_if_pready),
		.csr_if_psel(csr_if_psel),
		.csr_if_pwdata(csr_if_pwdata),
		.csr_if_pwrite(csr_if_pwrite),

		.mem_base(dmem_base),
		.mem_limit(dmem_limit),
		.spc_in(spc),
		.spc_out(execute_stage_spc_out),
		.tpc_in(tpc),
		.tpc_out(execute_stage_tpc_out),
		.task_mode_in(task_mode),
		.task_mode_out(execute_stage_task_mode_out),
		.ecause_in(ecause),
		.ecause_out(execute_stage_ecause_out),
		.eaddr_out(eaddr),
		.do_branch(execute_stage_do_branch),
		.interrupt(interrupt),
		.complete(execute_stage_complete)
	);

	ResultExtendStage result_extend_stage (
		.input_port_addr(exec_to_extend_addr),
		.input_port_data_en(exec_to_extend_data_en),
		.input_port_data_h(exec_to_extend_data_h),
		.input_port_data_l(exec_to_extend_data_l),
		.input_port_do_bse(exec_to_extend_do_bse),
		.input_port_do_bze(exec_to_extend_do_bze),
		.input_port_do_wse(exec_to_extend_do_wse),
		.input_port_do_wze(exec_to_extend_do_wze),
		.input_port_valid(exec_to_extend_valid),

		.output_port_addr(rf_write_addr),
		.output_port_data(rf_write_data),
		.output_port_data_en(rf_write_data_en),
		.output_port_valid(rf_write_valid)
	);

	RegFile reg_file (
		.clk(clk),
		.rst(rst),
		.read_req_read1_addr(rf_req_read1_addr),
		.read_req_read1_valid(rf_req_read1_valid),
		.read_req_read2_addr(rf_req_read2_addr),
		.read_req_read2_valid(rf_req_read2_valid),
		.read_req_ready(rf_req_ready),
		.read_req_rsv_addr(rf_req_rsv_addr),
		.read_req_rsv_valid(rf_req_rsv_valid),
		.read_req_valid(rf_req_valid),

		.read_rsp_read1_data(rf_rsp_read1_data),
		.read_rsp_read2_data(rf_rsp_read2_data),
		.read_rsp_ready(rf_rsp_ready),
		.read_rsp_valid(rf_rsp_valid),

		.write_addr(rf_write_addr),
		.write_data(rf_write_data),
		.write_data_en(rf_write_data_en),
		.write_valid(rf_write_valid),

		.do_branch(do_branch)
	);

	assign branch_taken = do_branch;
endmodule


////////////////////////////////////////////////////////////////////////////////
// RegFile
////////////////////////////////////////////////////////////////////////////////
module RegFile (
	input logic clk,
	input logic rst,
	input logic [3:0] read_req_read1_addr,
	input logic read_req_read1_valid,
	input logic [3:0] read_req_read2_addr,
	input logic read_req_read2_valid,
	output logic read_req_ready,
	input logic [3:0] read_req_rsv_addr,
	input logic read_req_rsv_valid,
	input logic read_req_valid,

	output logic [31:0] read_rsp_read1_data,
	output logic [31:0] read_rsp_read2_data,
	input logic read_rsp_ready,
	output logic read_rsp_valid,

	input logic [3:0] write_addr,
	input logic [31:0] write_data,
	input logic write_data_en,
	input logic write_valid,

	input logic do_branch
);

	logic req_advance;
	logic rsp_advance;
	logic u7_output_port;
	logic outstanding_req;
	logic u13_output_port;
	logic read1_valid;
	logic [3:0] u15_output_port;
	logic [3:0] read1_addr;
	logic u20_output_port;
	logic read2_valid;
	logic [3:0] u22_output_port;
	logic [3:0] read2_addr;
	logic u27_output_port;
	logic rsv_valid;
	logic [3:0] u29_output_port;
	logic [3:0] rsv_addr;
	logic [31:0] write_data_d;
	logic u37_output_port;
	logic u42_output_port;
	logic u49_output_port;
	logic rsv_registered;
	logic u52_output_port;
	logic wait_for_read1;
	logic u74_output_port;
	logic wait_for_read2;
	logic u96_output_port;
	logic wait_for_rsv_raw;
	logic wait_for_rsv;
	logic wait_for_some;
	logic u126_output_port;
	logic wait_for_write;
	logic rsv_set_valid;
	logic rsv_clr_valid;
	logic u146_output_port;
	logic u160_output_port;
	logic u174_output_port;
	logic u188_output_port;
	logic u202_output_port;
	logic u216_output_port;
	logic u230_output_port;
	logic u244_output_port;
	logic u258_output_port;
	logic u272_output_port;
	logic u286_output_port;
	logic u300_output_port;
	logic u314_output_port;
	logic u328_output_port;
	logic u342_output_port;
	logic wait_for_write_d;
	logic out_buf_full;
	logic [31:0] mem1_port2_data_out;
	logic [31:0] mem2_port2_data_out;
	logic [14:0] rsv_board;

	assign rsp_advance = read_rsp_ready & read_rsp_valid;
	assign req_advance = read_req_ready & read_req_valid;
	always_ff @(posedge clk) u7_output_port <= rst ? 1'h0 : req_advance ? 1'h1 : rsp_advance ? 1'h0 : outstanding_req;
	assign outstanding_req = req_advance |  ~ rsp_advance & u7_output_port;
	always_ff @(posedge clk) u13_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : req_advance ? read_req_read1_valid : read1_valid;
	assign read1_valid = req_advance ? read_req_read1_valid : u13_output_port;
	always_ff @(posedge clk) u15_output_port <= rst ? 4'h0 : req_advance ? read_req_read1_addr : u15_output_port;
	always_ff @(posedge clk) u20_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : req_advance ? read_req_read2_valid : read2_valid;
	assign read2_valid = req_advance ? read_req_read2_valid : u20_output_port;
	always_ff @(posedge clk) u22_output_port <= rst ? 4'h0 : req_advance ? read_req_read2_addr : u22_output_port;
	always_ff @(posedge clk) u27_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : req_advance ? read_req_rsv_valid : rsv_valid;
	assign rsv_valid = req_advance ? read_req_rsv_valid : u27_output_port;
	always_ff @(posedge clk) u29_output_port <= rst ? 4'h0 : req_advance ? read_req_rsv_addr : u29_output_port;
	always_ff @(posedge clk) write_data_d <= rst ? 32'h0 : write_data;
	assign read1_addr = req_advance ? read_req_read1_addr : u15_output_port;
	always_ff @(posedge clk) u37_output_port <= rst ? 1'h0 : write_addr == read1_addr & write_valid & write_data_en;
	assign read_rsp_read1_data = u37_output_port ? write_data_d : mem1_port2_data_out;
	assign read2_addr = req_advance ? read_req_read2_addr : u22_output_port;
	always_ff @(posedge clk) u42_output_port <= rst ? 1'h0 : write_addr == read2_addr & write_valid & write_data_en;
	assign read_rsp_read2_data = u42_output_port ? write_data_d : mem2_port2_data_out;
	always_ff @(posedge clk) u49_output_port <= rst ? 1'h0 : rsv_set_valid ?  ~ wait_for_rsv_raw : req_advance ? 1'h0 : rsv_registered;
	assign rsv_registered =  ~ req_advance & u49_output_port;
	always @(*) begin
		case (read1_addr)
			4'd0: u52_output_port = rsv_board[0];
			4'd1: u52_output_port = rsv_board[1];
			4'd2: u52_output_port = rsv_board[2];
			4'd3: u52_output_port = rsv_board[3];
			4'd4: u52_output_port = rsv_board[4];
			4'd5: u52_output_port = rsv_board[5];
			4'd6: u52_output_port = rsv_board[6];
			4'd7: u52_output_port = rsv_board[7];
			4'd8: u52_output_port = rsv_board[8];
			4'd9: u52_output_port = rsv_board[9];
			4'd10: u52_output_port = rsv_board[10];
			4'd11: u52_output_port = rsv_board[11];
			4'd12: u52_output_port = rsv_board[12];
			4'd13: u52_output_port = rsv_board[13];
			4'd14: u52_output_port = rsv_board[14];
		endcase
	end
	always @(*) begin
		case (read2_addr)
			4'd0: u74_output_port = rsv_board[0];
			4'd1: u74_output_port = rsv_board[1];
			4'd2: u74_output_port = rsv_board[2];
			4'd3: u74_output_port = rsv_board[3];
			4'd4: u74_output_port = rsv_board[4];
			4'd5: u74_output_port = rsv_board[5];
			4'd6: u74_output_port = rsv_board[6];
			4'd7: u74_output_port = rsv_board[7];
			4'd8: u74_output_port = rsv_board[8];
			4'd9: u74_output_port = rsv_board[9];
			4'd10: u74_output_port = rsv_board[10];
			4'd11: u74_output_port = rsv_board[11];
			4'd12: u74_output_port = rsv_board[12];
			4'd13: u74_output_port = rsv_board[13];
			4'd14: u74_output_port = rsv_board[14];
		endcase
	end
	assign rsv_addr = req_advance ? read_req_rsv_addr : u29_output_port;
	always @(*) begin
		case (rsv_addr)
			4'd0: u96_output_port = rsv_board[0];
			4'd1: u96_output_port = rsv_board[1];
			4'd2: u96_output_port = rsv_board[2];
			4'd3: u96_output_port = rsv_board[3];
			4'd4: u96_output_port = rsv_board[4];
			4'd5: u96_output_port = rsv_board[5];
			4'd6: u96_output_port = rsv_board[6];
			4'd7: u96_output_port = rsv_board[7];
			4'd8: u96_output_port = rsv_board[8];
			4'd9: u96_output_port = rsv_board[9];
			4'd10: u96_output_port = rsv_board[10];
			4'd11: u96_output_port = rsv_board[11];
			4'd12: u96_output_port = rsv_board[12];
			4'd13: u96_output_port = rsv_board[13];
			4'd14: u96_output_port = rsv_board[14];
		endcase
	end
	assign wait_for_rsv_raw = outstanding_req & rsv_valid & u96_output_port &  ~ (write_addr == rsv_addr & write_valid);
	assign wait_for_read1 = outstanding_req & read1_valid & u52_output_port &  ~ (write_addr == read1_addr & write_valid);
	assign wait_for_read2 = outstanding_req & read2_valid & u74_output_port &  ~ (write_addr == read2_addr & write_valid);
	assign wait_for_rsv = wait_for_rsv_raw &  ~ rsv_registered;
	assign wait_for_some = wait_for_read1 | wait_for_read2 | wait_for_rsv;
	always_ff @(posedge clk) u126_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (req_advance | write_valid) ? wait_for_some : wait_for_write;
	assign wait_for_write = (req_advance | write_valid) ? wait_for_some : u126_output_port;
	assign rsv_set_valid = rsv_valid &  ~ wait_for_write & outstanding_req;
	assign rsv_clr_valid = write_valid &  ~ wait_for_rsv;
	always_ff @(posedge clk) u146_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 1'h0) ? 1'h1 : (rsv_clr_valid & write_addr == 1'h0) ? 1'h0 : rsv_board[0];
	always_ff @(posedge clk) u160_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 1'h1) ? 1'h1 : (rsv_clr_valid & write_addr == 1'h1) ? 1'h0 : rsv_board[1];
	always_ff @(posedge clk) u174_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 2'h2) ? 1'h1 : (rsv_clr_valid & write_addr == 2'h2) ? 1'h0 : rsv_board[2];
	always_ff @(posedge clk) u188_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 2'h3) ? 1'h1 : (rsv_clr_valid & write_addr == 2'h3) ? 1'h0 : rsv_board[3];
	always_ff @(posedge clk) u202_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 3'h4) ? 1'h1 : (rsv_clr_valid & write_addr == 3'h4) ? 1'h0 : rsv_board[4];
	always_ff @(posedge clk) u216_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 3'h5) ? 1'h1 : (rsv_clr_valid & write_addr == 3'h5) ? 1'h0 : rsv_board[5];
	always_ff @(posedge clk) u230_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 3'h6) ? 1'h1 : (rsv_clr_valid & write_addr == 3'h6) ? 1'h0 : rsv_board[6];
	always_ff @(posedge clk) u244_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 3'h7) ? 1'h1 : (rsv_clr_valid & write_addr == 3'h7) ? 1'h0 : rsv_board[7];
	always_ff @(posedge clk) u258_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 4'h8) ? 1'h1 : (rsv_clr_valid & write_addr == 4'h8) ? 1'h0 : rsv_board[8];
	always_ff @(posedge clk) u272_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 4'h9) ? 1'h1 : (rsv_clr_valid & write_addr == 4'h9) ? 1'h0 : rsv_board[9];
	always_ff @(posedge clk) u286_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 4'ha) ? 1'h1 : (rsv_clr_valid & write_addr == 4'ha) ? 1'h0 : rsv_board[10];
	always_ff @(posedge clk) u300_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 4'hb) ? 1'h1 : (rsv_clr_valid & write_addr == 4'hb) ? 1'h0 : rsv_board[11];
	always_ff @(posedge clk) u314_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 4'hc) ? 1'h1 : (rsv_clr_valid & write_addr == 4'hc) ? 1'h0 : rsv_board[12];
	always_ff @(posedge clk) u328_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 4'hd) ? 1'h1 : (rsv_clr_valid & write_addr == 4'hd) ? 1'h0 : rsv_board[13];
	always_ff @(posedge clk) u342_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : (rsv_set_valid & rsv_addr == 4'he) ? 1'h1 : (rsv_clr_valid & write_addr == 4'he) ? 1'h0 : rsv_board[14];
	always_ff @(posedge clk) out_buf_full <= rst ? 1'h0 : do_branch ? 1'h0 : req_advance ? 1'h1 : rsp_advance ? 1'h0 : out_buf_full;
	always_ff @(posedge clk) wait_for_write_d <= rst ? 1'h0 : do_branch ? 1'h0 : wait_for_write;
	assign read_req_ready =  ~ wait_for_write_d & (read_rsp_ready |  ~ out_buf_full);
	assign read_rsp_valid =  ~ wait_for_write_d & out_buf_full;
	assign rsv_board = {u342_output_port, u328_output_port, u314_output_port, u300_output_port, u286_output_port, u272_output_port, u258_output_port, u244_output_port, u230_output_port, u216_output_port, u202_output_port, u188_output_port, u174_output_port, u160_output_port, u146_output_port};

	SimpleDualPortMemory mem1 (
		.port1_addr(write_addr),
		.port1_clk(clk),
		.port2_addr(read1_addr),
		.port2_clk(clk),
		.port1_write_en(write_valid & write_data_en),
		.port1_data_in(write_data),
		.port2_data_out(mem1_port2_data_out)
	);

	SimpleDualPortMemory_2 mem2 (
		.port1_addr(write_addr),
		.port1_clk(clk),
		.port2_addr(read2_addr),
		.port2_clk(clk),
		.port1_write_en(write_valid & write_data_en),
		.port1_data_in(write_data),
		.port2_data_out(mem2_port2_data_out)
	);

endmodule


////////////////////////////////////////////////////////////////////////////////
// SimpleDualPortMemory_2
////////////////////////////////////////////////////////////////////////////////
module SimpleDualPortMemory_2 (
	input logic [3:0] port1_addr,
	input logic port1_clk,
	input logic [3:0] port2_addr,
	input logic port2_clk,
	input logic port1_write_en,
	input logic [31:0] port1_data_in,
	output logic [31:0] port2_data_out
);

	reg [31:0] mem [0:15];

	always @(posedge port1_clk) begin
		if (port1_write_en) begin
			mem[port1_addr] <= port1_data_in;
		end
	end

	logic [3:0] port2_addr_reg;
	always @(posedge port1_clk) begin
		port2_addr_reg <= port2_addr;
	end
	assign port2_data_out = mem[port2_addr_reg];


endmodule


////////////////////////////////////////////////////////////////////////////////
// SimpleDualPortMemory
////////////////////////////////////////////////////////////////////////////////
module SimpleDualPortMemory (
	input logic [3:0] port1_addr,
	input logic port1_clk,
	input logic [3:0] port2_addr,
	input logic port2_clk,
	input logic port1_write_en,
	input logic [31:0] port1_data_in,
	output logic [31:0] port2_data_out
);

	reg [31:0] mem [0:15];

	always @(posedge port1_clk) begin
		if (port1_write_en) begin
			mem[port1_addr] <= port1_data_in;
		end
	end

	logic [3:0] port2_addr_reg;
	always @(posedge port1_clk) begin
		port2_addr_reg <= port2_addr;
	end
	assign port2_data_out = mem[port2_addr_reg];


endmodule


////////////////////////////////////////////////////////////////////////////////
// ResultExtendStage
////////////////////////////////////////////////////////////////////////////////
module ResultExtendStage (
	input logic [3:0] input_port_addr,
	input logic input_port_data_en,
	input logic [15:0] input_port_data_h,
	input logic [15:0] input_port_data_l,
	input logic input_port_do_bse,
	input logic input_port_do_bze,
	input logic input_port_do_wse,
	input logic input_port_do_wze,
	input logic input_port_valid,

	output logic [3:0] output_port_addr,
	output logic [31:0] output_port_data,
	output logic output_port_data_en,
	output logic output_port_valid
);

	assign output_port_data = 
		(input_port_do_bse ? ({input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7], input_port_data_l[7:0]}) : 32'b0) | 
		(input_port_do_wse ? ({input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15], input_port_data_l[15:0]}) : 32'b0) | 
		(input_port_do_bze ? input_port_data_l[7:0] : 32'b0) | 
		(input_port_do_wze ? input_port_data_l[15:0] : 32'b0) | 
		(input_port_do_bse | input_port_do_wse | input_port_do_bze | input_port_do_wze ? 32'b0 : ({input_port_data_h, input_port_data_l}));
	assign output_port_addr = input_port_addr;
	assign output_port_data_en = input_port_data_en;
	assign output_port_valid = input_port_valid;

endmodule


////////////////////////////////////////////////////////////////////////////////
// ExecuteStage
////////////////////////////////////////////////////////////////////////////////
module ExecuteStage (
	input logic clk,
	input logic rst,
	input logic [2:0] input_port_alu_op,
	input logic [3:0] input_port_branch_op,
	input logic input_port_do_bse,
	input logic input_port_do_bze,
	input logic input_port_do_wse,
	input logic input_port_do_wze,
	input logic [2:0] input_port_exec_unit,
	input logic input_port_fetch_av,
	input logic [1:0] input_port_inst_len,
	input logic input_port_ldst_op,
	input logic [1:0] input_port_mem_access_len,
	input logic [31:0] input_port_op_a,
	input logic [31:0] input_port_op_b,
	input logic [31:0] input_port_op_c,
	output logic input_port_ready,
	input logic [3:0] input_port_result_reg_addr,
	input logic input_port_result_reg_addr_valid,
	input logic [1:0] input_port_shifter_op,
	input logic input_port_valid,

	output logic [3:0] output_port_addr,
	output logic output_port_data_en,
	output logic [15:0] output_port_data_h,
	output logic [15:0] output_port_data_l,
	output logic output_port_do_bse,
	output logic output_port_do_bze,
	output logic output_port_do_wse,
	output logic output_port_do_wze,
	output logic output_port_valid,

	output logic [30:0] bus_req_if_addr,
	output logic [1:0] bus_req_if_byte_en,
	output logic [15:0] bus_req_if_data,
	output logic bus_req_if_read_not_write,
	input logic bus_req_if_ready,
	output logic bus_req_if_valid,

	input logic [15:0] bus_rsp_if_data,
	input logic bus_rsp_if_valid,

	output logic [9:0] csr_if_paddr,
	output logic csr_if_penable,
	input logic [31:0] csr_if_prdata,
	input logic csr_if_pready,
	output logic csr_if_psel,
	output logic [31:0] csr_if_pwdata,
	output logic csr_if_pwrite,

	input logic [21:0] mem_base,
	input logic [21:0] mem_limit,
	input logic [30:0] spc_in,
	output logic [30:0] spc_out,
	input logic [30:0] tpc_in,
	output logic [30:0] tpc_out,
	input logic task_mode_in,
	output logic task_mode_out,
	input logic [11:0] ecause_in,
	output logic [11:0] ecause_out,
	output logic [31:0] eaddr_out,
	output logic do_branch,
	input logic interrupt,
	output logic complete
);

	logic branch_input_interrupt;
	logic [30:0] pc;
	logic s1_was_branch;
	logic s2_was_branch;
	logic multi_cycle_exec_lockout;
	logic stage_1_reg_en;
	logic s1_alu_output_f_carry;
	logic branch_input_f_carry;
	logic s1_alu_output_f_overflow;
	logic branch_input_f_overflow;
	logic s1_alu_output_f_sign;
	logic branch_input_f_sign;
	logic s1_alu_output_f_zero;
	logic branch_input_f_zero;
	logic [31:0] s1_alu_output_result;
	logic s1_ldst_output_mem_av;
	logic branch_input_mem_av;
	logic s1_ldst_output_mem_unaligned;
	logic branch_input_mem_unaligned;
	logic [31:0] s1_ldst_output_phy_addr;
	logic [31:0] mem_input_addr;
	logic [30:0] s1_branch_target_output_branch_addr;
	logic [30:0] branch_input_branch_addr;
	logic [30:0] s1_branch_target_output_straight_addr;
	logic [31:0] s1_shifter_output_result;
	logic [2:0] s1_exec_unit;
	logic [3:0] branch_input_opcode;
	logic [3:0] s1_branch_op;
	logic s1_ldst_op;
	logic [31:0] mem_input_data;
	logic [31:0] branch_input_op_a;
	logic [31:0] s1_op_a;
	logic [31:0] branch_input_op_b;
	logic [31:0] s1_op_b;
	logic [31:0] s1_op_c;
	logic s1_do_bse;
	logic s1_do_wse;
	logic s1_do_bze;
	logic s1_do_wze;
	logic [3:0] s1_result_reg_addr;
	logic s1_result_reg_addr_valid;
	logic branch_input_fetch_av;
	logic s1_fetch_av;
	logic [30:0] branch_input_tpc;
	logic [30:0] s1_tpc;
	logic [30:0] branch_input_spc;
	logic [30:0] s1_spc;
	logic branch_input_task_mode;
	logic s1_task_mode;
	logic [1:0] mem_input_access_len;
	logic [1:0] s1_mem_access_len;
	logic [30:0] s2_pc;
	logic block_mem;
	logic mem_input_valid;
	logic stage_2_ready;
	logic stage_2_valid;
	logic u72_output_port;
	logic u75_output_port;
	logic stage_2_reg_en;
	logic branch_input_is_branch_insn;
	logic mem_input_read_not_write;
	logic [31:0] result;
	logic s2_result_reg_addr_valid;
	logic u94_output_port;
	logic [2:0] s2_exec_unit;
	logic s2_ldst_op;
	logic [15:0] u101_output_port;
	logic [15:0] u106_output_port;
	logic [30:0] straight_tpc_out;
	logic [30:0] straight_spc_out;
	logic stage_1_fsm_out_reg_en;
	logic stage_1_valid;
	logic stage_1_fsm_input_ready;
	logic alu_output_f_zero;
	logic alu_output_f_carry;
	logic alu_output_f_overflow;
	logic [31:0] alu_output_result;
	logic alu_output_f_sign;
	logic ldst_output_mem_av;
	logic ldst_output_mem_unaligned;
	logic [31:0] ldst_output_phy_addr;
	logic [30:0] branch_target_output_straight_addr;
	logic [30:0] branch_target_output_branch_addr;
	logic [31:0] shifter_output_result;
	logic [31:0] mult_output_result;
	logic stage_2_fsm_out_reg_en;
	logic stage_2_fsm_output_valid;
	logic stage_2_fsm_input_ready;
	logic branch_output_is_exception;
	logic [30:0] branch_output_tpc;
	logic [30:0] branch_output_spc;
	logic branch_output_spc_changed;
	logic branch_output_tpc_changed;
	logic branch_output_task_mode_changed;
	logic branch_output_task_mode;
	logic branch_output_do_branch;
	logic [11:0] branch_output_ecause;
	logic mem_input_ready;
	logic s2_mem_output_valid;
	logic [15:0] s2_mem_output_data_l;
	logic [15:0] s2_mem_output_data_h;

	always_ff @(posedge clk) s1_was_branch <= rst ? 1'h0 : do_branch;
	always_ff @(posedge clk) multi_cycle_exec_lockout <= rst ? 1'h0 : input_port_ready & input_port_valid & input_port_exec_unit == `op_class__mult &  ~ input_port_fetch_av;
	assign input_port_ready =  ~ multi_cycle_exec_lockout &  ~ s1_was_branch & stage_1_fsm_input_ready;
	assign stage_1_reg_en =  ~ multi_cycle_exec_lockout &  ~ s1_was_branch & stage_1_fsm_out_reg_en;
	assign pc = task_mode_in ? tpc_in : spc_in;
	always_ff @(posedge clk) branch_input_f_carry <= rst ? 1'h0 : stage_1_reg_en ? alu_output_f_carry : branch_input_f_carry;
	always_ff @(posedge clk) branch_input_f_overflow <= rst ? 1'h0 : stage_1_reg_en ? alu_output_f_overflow : branch_input_f_overflow;
	always_ff @(posedge clk) branch_input_f_sign <= rst ? 1'h0 : stage_1_reg_en ? alu_output_f_sign : branch_input_f_sign;
	always_ff @(posedge clk) branch_input_f_zero <= rst ? 1'h0 : stage_1_reg_en ? alu_output_f_zero : branch_input_f_zero;
	always_ff @(posedge clk) s1_alu_output_result <= rst ? 32'h0 : stage_1_reg_en ? alu_output_result : s1_alu_output_result;
	always_ff @(posedge clk) branch_input_mem_av <= rst ? 1'h0 : stage_1_reg_en ? ldst_output_mem_av : branch_input_mem_av;
	always_ff @(posedge clk) branch_input_mem_unaligned <= rst ? 1'h0 : stage_1_reg_en ? ldst_output_mem_unaligned : branch_input_mem_unaligned;
	always_ff @(posedge clk) mem_input_addr <= rst ? 32'h0 : stage_1_reg_en ? ldst_output_phy_addr : mem_input_addr;
	always_ff @(posedge clk) branch_input_branch_addr <= rst ? 31'h0 : stage_1_reg_en ? branch_target_output_branch_addr : branch_input_branch_addr;
	always_ff @(posedge clk) s1_branch_target_output_straight_addr <= rst ? 31'h0 : stage_1_reg_en ? branch_target_output_straight_addr : s1_branch_target_output_straight_addr;
	always_ff @(posedge clk) s1_shifter_output_result <= rst ? 32'h0 : stage_1_reg_en ? shifter_output_result : s1_shifter_output_result;
	always_ff @(posedge clk) s1_task_mode <= rst ? 1'h0 : stage_1_reg_en ? task_mode_in : s1_task_mode;
	always_ff @(posedge clk) s1_spc <= rst ? 31'h0 : stage_1_reg_en ? spc_in : s1_spc;
	always_ff @(posedge clk) s1_tpc <= rst ? 31'h0 : stage_1_reg_en ? tpc_in : s1_tpc;
	always_ff @(posedge clk) s1_fetch_av <= rst ? 1'h0 : stage_1_reg_en ? input_port_fetch_av : s1_fetch_av;
	assign block_mem = branch_input_mem_av | branch_input_mem_unaligned | s1_fetch_av;
	always_ff @(posedge clk) s1_exec_unit <= rst ? 3'h0 : stage_1_reg_en ? input_port_exec_unit : s1_exec_unit;
	assign mem_input_valid = stage_1_valid &  ~ block_mem & s1_exec_unit == `op_class__ld_st;
	assign stage_2_ready = (s1_exec_unit == `op_class__ld_st &  ~ block_mem) ? mem_input_ready : stage_2_fsm_input_ready;
	always_ff @(posedge clk) s2_was_branch <= rst ? 1'h0 : s1_was_branch;
	assign stage_2_valid = ((s2_exec_unit == `op_class__ld_st &  ~ block_mem) ? s2_mem_output_valid : stage_2_fsm_output_valid) &  ~ s2_was_branch;
	always_ff @(posedge clk) u75_output_port <= rst ? 1'h0 : do_branch;
	assign stage_2_reg_en = stage_1_valid & stage_2_ready &  ~ u75_output_port;
	always_ff @(posedge clk) s1_branch_op <= rst ? 4'h0 : stage_1_reg_en ? input_port_branch_op : s1_branch_op;
	always_ff @(posedge clk) s1_op_a <= rst ? 32'h0 : stage_1_reg_en ? input_port_op_a : s1_op_a;
	always_ff @(posedge clk) s1_op_b <= rst ? 32'h0 : stage_1_reg_en ? input_port_op_b : s1_op_b;
	assign branch_input_is_branch_insn = s1_exec_unit == `op_class__branch;
	always_ff @(posedge clk) s1_ldst_op <= rst ? 1'h0 : stage_1_reg_en ? input_port_ldst_op : s1_ldst_op;
	assign mem_input_read_not_write = s1_exec_unit == `op_class__ld_st & s1_ldst_op == `ldst_ops__load;
	always_ff @(posedge clk) s1_mem_access_len <= rst ? 2'h0 : stage_1_reg_en ? input_port_mem_access_len : s1_mem_access_len;
	always_ff @(posedge clk) s1_result_reg_addr_valid <= rst ? 1'h0 : stage_1_reg_en ? input_port_result_reg_addr_valid : s1_result_reg_addr_valid;
	always_ff @(posedge clk) s2_result_reg_addr_valid <= rst ? 1'h0 : stage_2_reg_en ? s1_result_reg_addr_valid : s2_result_reg_addr_valid;
	always_ff @(posedge clk) u94_output_port <= rst ? 1'h0 : stage_2_reg_en;
	assign output_port_valid = stage_2_valid & s2_result_reg_addr_valid & (u94_output_port | s2_mem_output_valid);
	always_ff @(posedge clk) s2_exec_unit <= rst ? 3'h0 : stage_2_reg_en ? s1_exec_unit : s2_exec_unit;
	always_ff @(posedge clk) s2_ldst_op <= rst ? 1'h0 : stage_2_reg_en ? s1_ldst_op : s2_ldst_op;
	assign result = (s1_exec_unit == `op_class__alu ? s1_alu_output_result : 32'b0) | (s1_exec_unit == `op_class__mult ? mult_output_result : 32'b0) | (s1_exec_unit == `op_class__shift ? s1_shifter_output_result : 32'b0) ;
	always_ff @(posedge clk) u101_output_port <= rst ? 16'h0 : stage_2_reg_en ? result[15:0] : u101_output_port;
	assign output_port_data_l = s2_exec_unit == `op_class__ld_st ? s2_mem_output_data_l : u101_output_port;
	always_ff @(posedge clk) u106_output_port <= rst ? 16'h0 : stage_2_reg_en ? result[31:16] : u106_output_port;
	assign output_port_data_h = s2_exec_unit == `op_class__ld_st ? s2_mem_output_data_h : u106_output_port;
	always_ff @(posedge clk) output_port_data_en <= rst ? 1'h0 : stage_2_reg_en ?  ~ branch_output_do_branch : output_port_data_en;
	always_ff @(posedge clk) s1_result_reg_addr <= rst ? 4'h0 : stage_1_reg_en ? input_port_result_reg_addr : s1_result_reg_addr;
	always_ff @(posedge clk) output_port_addr <= rst ? 4'h0 : stage_2_reg_en ? s1_result_reg_addr : output_port_addr;
	always_ff @(posedge clk) s1_do_bse <= rst ? 1'h0 : stage_1_reg_en ? input_port_do_bse : s1_do_bse;
	always_ff @(posedge clk) output_port_do_bse <= rst ? 1'h0 : stage_2_reg_en ? s1_do_bse : output_port_do_bse;
	always_ff @(posedge clk) s1_do_wse <= rst ? 1'h0 : stage_1_reg_en ? input_port_do_wse : s1_do_wse;
	always_ff @(posedge clk) output_port_do_wse <= rst ? 1'h0 : stage_2_reg_en ? s1_do_wse : output_port_do_wse;
	always_ff @(posedge clk) s1_do_bze <= rst ? 1'h0 : stage_1_reg_en ? input_port_do_bze : s1_do_bze;
	always_ff @(posedge clk) output_port_do_bze <= rst ? 1'h0 : stage_2_reg_en ? s1_do_bze : output_port_do_bze;
	always_ff @(posedge clk) s1_do_wze <= rst ? 1'h0 : stage_1_reg_en ? input_port_do_wze : s1_do_wze;
	always_ff @(posedge clk) output_port_do_wze <= rst ? 1'h0 : stage_2_reg_en ? s1_do_wze : output_port_do_wze;
	assign do_branch = branch_output_do_branch & stage_2_reg_en;
	assign straight_tpc_out = stage_1_reg_en ? task_mode_in ? branch_target_output_straight_addr : tpc_in : tpc_in;
	assign tpc_out = s1_was_branch ? tpc_in : (stage_2_reg_en & branch_output_tpc_changed) ? branch_output_tpc : straight_tpc_out;
	assign straight_spc_out = stage_1_reg_en ?  ~ (task_mode_out | task_mode_in) ? branch_target_output_straight_addr : spc_in : spc_in;
	assign spc_out = s1_was_branch ? spc_in : (stage_2_reg_en & branch_output_spc_changed) ? branch_output_spc : straight_spc_out;
	assign task_mode_out = s1_was_branch ? task_mode_in : (stage_2_reg_en & branch_output_task_mode_changed) ? branch_output_task_mode : task_mode_in;
	assign ecause_out = (stage_2_reg_en &  ~ s1_was_branch) ? ecause_in | branch_output_ecause : ecause_in;
	always_ff @(posedge clk) eaddr_out <= rst ? 32'h0 : branch_output_is_exception &  ~ do_branch ? (input_port_fetch_av | input_port_exec_unit == `op_class__branch & input_port_branch_op == `branch_ops__swi) ? ldst_output_phy_addr : pc : eaddr_out;
	always_ff @(posedge clk) s1_op_c <= rst ? 32'h0 : stage_1_reg_en ? input_port_op_c : s1_op_c;
	assign s2_pc = s1_task_mode ? s1_tpc : s1_spc;

	ForwardBufLogic stage_1_fsm (
		.clock_port(clk),
		.reset_port(rst),
		.input_valid( ~ multi_cycle_exec_lockout &  ~ s1_was_branch & input_port_valid),
		.input_ready(stage_1_fsm_input_ready),
		.output_valid(stage_1_valid),
		.output_ready(stage_2_ready),
		.out_reg_en(stage_1_fsm_out_reg_en),
		.clear(do_branch)
	);

	AluUnit alu_unit (
		.clk(clk),
		.rst(rst),
		.input_port_op_a(input_port_op_a),
		.input_port_op_b(input_port_op_b),
		.input_port_opcode(input_port_alu_op),
		.input_port_pc(pc),
		.input_port_tpc(tpc_in),

		.output_port_f_carry(alu_output_f_carry),
		.output_port_f_overflow(alu_output_f_overflow),
		.output_port_f_sign(alu_output_f_sign),
		.output_port_f_zero(alu_output_f_zero),
		.output_port_result(alu_output_result)
	);

	LoadStoreUnit ldst_unit (
		.clk(clk),
		.rst(rst),
		.input_port_is_ldst(input_port_exec_unit == `op_class__ld_st),
		.input_port_mem_access_len(input_port_mem_access_len),
		.input_port_mem_base(mem_base),
		.input_port_mem_limit(mem_limit),
		.input_port_op_b(input_port_op_b),
		.input_port_op_c(input_port_op_c),
		.input_port_task_mode(task_mode_in),

		.output_port_mem_av(ldst_output_mem_av),
		.output_port_mem_unaligned(ldst_output_mem_unaligned),
		.output_port_phy_addr(ldst_output_phy_addr)
	);

	BranchTargetUnit branch_target_unit (
		.input_port_inst_len(input_port_inst_len),
		.input_port_op_c(input_port_op_c),
		.input_port_pc(pc),

		.output_port_branch_addr(branch_target_output_branch_addr),
		.output_port_straight_addr(branch_target_output_straight_addr)
	);

	ShifterUnit shifter_unit (
		.clk(clk),
		.rst(rst),
		.input_port_op_a(input_port_op_a),
		.input_port_op_b(input_port_op_b),
		.input_port_opcode(input_port_shifter_op),

		.output_port_result(shifter_output_result)
	);

	MultUnit mult_unit (
		.clk(clk),
		.rst(rst),
		.input_port_op_a(input_port_op_a),
		.input_port_op_b(input_port_op_b),
		.input_port_valid(stage_1_reg_en),

		.output_port_result(mult_output_result)
	);

	ForwardBufLogic_2 stage_2_fsm (
		.clock_port(clk),
		.reset_port(rst),
		.input_valid(stage_1_valid),
		.input_ready(stage_2_fsm_input_ready),
		.output_valid(stage_2_fsm_output_valid),
		.output_ready(u72_output_port),
		.out_reg_en(stage_2_fsm_out_reg_en),
		.clear(do_branch)
	);

	BranchUnit branch_unit (
		.input_port_branch_addr(branch_input_branch_addr),
		.input_port_f_carry(branch_input_f_carry),
		.input_port_f_overflow(branch_input_f_overflow),
		.input_port_f_sign(branch_input_f_sign),
		.input_port_f_zero(branch_input_f_zero),
		.input_port_fetch_av(s1_fetch_av),
		.input_port_interrupt(interrupt),
		.input_port_is_branch_insn(branch_input_is_branch_insn),
		.input_port_mem_av(branch_input_mem_av),
		.input_port_mem_unaligned(branch_input_mem_unaligned),
		.input_port_op_a(s1_op_a),
		.input_port_op_b(s1_op_b),
		.input_port_opcode(s1_branch_op),
		.input_port_spc(s1_spc),
		.input_port_task_mode(s1_task_mode),
		.input_port_tpc(s1_tpc),

		.output_port_do_branch(branch_output_do_branch),
		.output_port_ecause(branch_output_ecause),
		.output_port_is_exception(branch_output_is_exception),
		.output_port_spc(branch_output_spc),
		.output_port_spc_changed(branch_output_spc_changed),
		.output_port_task_mode(branch_output_task_mode),
		.output_port_task_mode_changed(branch_output_task_mode_changed),
		.output_port_tpc(branch_output_tpc),
		.output_port_tpc_changed(branch_output_tpc_changed)
	);

	MemoryStage memory_unit (
		.clk(clk),
		.rst(rst),
		.input_port_access_len(s1_mem_access_len),
		.input_port_addr(mem_input_addr),
		.input_port_data(s1_op_a),
		.input_port_read_not_write(mem_input_read_not_write),
		.input_port_ready(mem_input_ready),
		.input_port_valid(mem_input_valid),

		.output_port_data_h(s2_mem_output_data_h),
		.output_port_data_l(s2_mem_output_data_l),
		.output_port_valid(s2_mem_output_valid),

		.bus_req_if_addr(bus_req_if_addr),
		.bus_req_if_byte_en(bus_req_if_byte_en),
		.bus_req_if_data(bus_req_if_data),
		.bus_req_if_read_not_write(bus_req_if_read_not_write),
		.bus_req_if_ready(bus_req_if_ready),
		.bus_req_if_valid(bus_req_if_valid),

		.bus_rsp_if_data(bus_rsp_if_data),
		.bus_rsp_if_valid(bus_rsp_if_valid),

		.csr_if_paddr(csr_if_paddr),
		.csr_if_penable(csr_if_penable),
		.csr_if_prdata(csr_if_prdata),
		.csr_if_pready(csr_if_pready),
		.csr_if_psel(csr_if_psel),
		.csr_if_pwdata(csr_if_pwdata),
		.csr_if_pwrite(csr_if_pwrite)
	);

	assign branch_input_interrupt = interrupt;
	assign s1_alu_output_f_carry = branch_input_f_carry;
	assign s1_alu_output_f_overflow = branch_input_f_overflow;
	assign s1_alu_output_f_sign = branch_input_f_sign;
	assign s1_alu_output_f_zero = branch_input_f_zero;
	assign s1_ldst_output_mem_av = branch_input_mem_av;
	assign s1_ldst_output_mem_unaligned = branch_input_mem_unaligned;
	assign s1_ldst_output_phy_addr = mem_input_addr;
	assign s1_branch_target_output_branch_addr = branch_input_branch_addr;
	assign branch_input_opcode = s1_branch_op;
	assign mem_input_data = s1_op_a;
	assign branch_input_op_a = s1_op_a;
	assign branch_input_op_b = s1_op_b;
	assign branch_input_fetch_av = s1_fetch_av;
	assign branch_input_tpc = s1_tpc;
	assign branch_input_spc = s1_spc;
	assign branch_input_task_mode = s1_task_mode;
	assign mem_input_access_len = s1_mem_access_len;
	assign complete = stage_2_valid;
	assign u72_output_port = (s2_exec_unit == `op_class__ld_st & s2_ldst_op == `ldst_ops__load &  ~ block_mem) ? s2_mem_output_valid : 1'h1;
endmodule


////////////////////////////////////////////////////////////////////////////////
// MemoryStage
////////////////////////////////////////////////////////////////////////////////
module MemoryStage (
	input logic clk,
	input logic rst,
	input logic [1:0] input_port_access_len,
	input logic [31:0] input_port_addr,
	input logic [31:0] input_port_data,
	input logic input_port_read_not_write,
	output logic input_port_ready,
	input logic input_port_valid,

	output logic [15:0] output_port_data_h,
	output logic [15:0] output_port_data_l,
	output logic output_port_valid,

	output logic [30:0] bus_req_if_addr,
	output logic [1:0] bus_req_if_byte_en,
	output logic [15:0] bus_req_if_data,
	output logic bus_req_if_read_not_write,
	input logic bus_req_if_ready,
	output logic bus_req_if_valid,

	input logic [15:0] bus_rsp_if_data,
	input logic bus_rsp_if_valid,

	output logic [9:0] csr_if_paddr,
	output logic csr_if_penable,
	input logic [31:0] csr_if_prdata,
	input logic csr_if_pready,
	output logic csr_if_psel,
	output logic [31:0] csr_if_pwdata,
	output logic csr_if_pwrite
);

	logic input_advance;
	logic bus_request_advance;
	logic multi_cycle;
	logic next_active;
	logic active;
	logic pending;
	logic gap;
	logic csr_select;
	logic u46_output_port;
	logic is_csr;
	logic [30:0] next_addr;
	logic [15:0] data_store;
	logic u87_output_port;
	logic [1:0] u91_output_port;
	logic csr_pen;
	logic csr_active;
	logic u112_output_port;
	logic [9:0] u116_output_port;
	logic [31:0] u121_output_port;
	logic [1:0] byte_en;

	assign input_advance = input_port_ready & input_port_valid;
	always_ff @(posedge clk) multi_cycle <= rst ? 1'h0 : input_advance ? input_port_access_len == 2'h2 &  ~ is_csr : multi_cycle;
	assign bus_request_advance = bus_req_if_ready & bus_req_if_valid;
	assign next_active = (input_port_access_len == 2'h2 &  ~ is_csr & input_advance) ? 1'h1 : bus_request_advance ? 1'h0 : active;
	always_ff @(posedge clk) active <= rst ? 1'h0 : next_active;
	always_ff @(posedge clk) pending <= rst ? 1'h0 : (input_port_access_len == 2'h2 &  ~ is_csr & input_advance & input_port_read_not_write) ? 1'h1 : bus_rsp_if_valid ? 1'h0 : pending;
	always_ff @(posedge clk) gap <= rst ? 1'h0 : (input_port_access_len != 2'h2 &  ~ is_csr & input_advance | active &  ~ next_active) ? 1'h1 : 1'h0;
	assign csr_select = input_port_addr[31:30] == 1'h1;
	always_ff @(posedge clk) u46_output_port <= rst ? 1'h0 : input_advance ? csr_select : output_port_valid ? 1'h0 : is_csr;
	assign is_csr = input_advance ? csr_select : u46_output_port;
	assign input_port_ready = bus_req_if_ready &  ~ active &  ~ gap | csr_select & input_port_valid &  ~ csr_active;
	assign bus_req_if_valid = (input_port_valid &  ~ csr_select | active) &  ~ gap;
	assign output_port_valid = bus_rsp_if_valid &  ~ pending | csr_pen & csr_if_pready &  ~ csr_if_pwrite;
	always_ff @(posedge clk) data_store <= rst ? 16'h0 : input_advance ? input_port_data[31:16] : (bus_rsp_if_valid & pending) ? bus_rsp_if_data : data_store;
	always_ff @(posedge clk) u87_output_port <= rst ? 1'h0 : input_port_ready & input_port_valid ? input_port_read_not_write : u87_output_port;
	assign bus_req_if_read_not_write = (input_port_ready & input_port_valid) ? input_port_read_not_write : u87_output_port;
	always_ff @(posedge clk) u91_output_port <= rst ? 2'h0 : input_port_ready & input_port_valid ? byte_en : u91_output_port;
	assign bus_req_if_byte_en = (input_port_ready & input_port_valid) ? byte_en : u91_output_port;
	always_ff @(posedge clk) next_addr <= rst ? 31'h0 : input_advance ? input_port_addr[31:1] | 1'h1 : next_addr;
	assign bus_req_if_addr = input_advance ? input_port_addr[31:1] : next_addr;
	assign bus_req_if_data = input_advance ? input_port_data[15:0] : data_store;
	assign output_port_data_l = csr_pen ? csr_if_prdata[15:0] : multi_cycle ? data_store : bus_rsp_if_data;
	assign output_port_data_h = csr_pen ? csr_if_prdata[31:16] : bus_rsp_if_data;
	always_ff @(posedge clk) csr_pen <= rst ? 1'h0 : input_advance ? is_csr : (csr_if_pready & is_csr) ? 1'h0 : csr_pen;
	always_ff @(posedge clk) csr_active <= rst ? 1'h0 : csr_if_psel;
	assign csr_if_psel = input_advance & is_csr | csr_pen;
	always_ff @(posedge clk) u112_output_port <= rst ? 1'h0 : input_port_ready & input_port_valid ?  ~ input_port_read_not_write : u112_output_port;
	assign csr_if_pwrite = (input_port_ready & input_port_valid) ?  ~ input_port_read_not_write : u112_output_port;
	always_ff @(posedge clk) u116_output_port <= rst ? 10'h0 : input_port_ready & input_port_valid ? input_port_addr[11:2] : u116_output_port;
	assign csr_if_paddr = (input_port_ready & input_port_valid) ? input_port_addr[11:2] : u116_output_port;
	always_ff @(posedge clk) u121_output_port <= rst ? 32'h0 : input_port_ready & input_port_valid ? input_port_data : u121_output_port;
	assign csr_if_pwdata = (input_port_ready & input_port_valid) ? input_port_data : u121_output_port;
	assign byte_en = {input_port_access_len != 1'h0 | input_port_addr[0], input_port_access_len != 1'h0 |  ~ input_port_addr[0]};

	assign csr_if_penable = csr_pen;
endmodule


////////////////////////////////////////////////////////////////////////////////
// BranchUnit
////////////////////////////////////////////////////////////////////////////////
module BranchUnit (
	input logic [30:0] input_port_branch_addr,
	input logic input_port_f_carry,
	input logic input_port_f_overflow,
	input logic input_port_f_sign,
	input logic input_port_f_zero,
	input logic input_port_fetch_av,
	input logic input_port_interrupt,
	input logic input_port_is_branch_insn,
	input logic input_port_mem_av,
	input logic input_port_mem_unaligned,
	input logic [31:0] input_port_op_a,
	input logic [31:0] input_port_op_b,
	input logic [3:0] input_port_opcode,
	input logic [30:0] input_port_spc,
	input logic input_port_task_mode,
	input logic [30:0] input_port_tpc,

	output logic output_port_do_branch,
	output logic [11:0] output_port_ecause,
	output logic output_port_is_exception,
	output logic [30:0] output_port_spc,
	output logic output_port_spc_changed,
	output logic output_port_task_mode,
	output logic output_port_task_mode_changed,
	output logic [30:0] output_port_tpc,
	output logic output_port_tpc_changed
);

	logic condition_result;
	logic is_exception;
	logic in_mode_branch;
	logic [30:0] branch_target;
	logic [30:0] spc_branch_target;
	logic [10:0] exception_mask;
	logic [11:0] interrupt_mask;
	logic u21_output_port;
	logic u18_output_port;

	assign is_exception = input_port_is_branch_insn & input_port_opcode == `branch_ops__swi | input_port_mem_av | input_port_mem_unaligned | input_port_fetch_av;
	assign condition_result = input_port_is_branch_insn & (
		(input_port_opcode == `branch_ops__cb_eq ? input_port_f_zero : 1'b0) | 
		(input_port_opcode == `branch_ops__cb_ne ?  ~ input_port_f_zero : 1'b0) | 
		(input_port_opcode == `branch_ops__cb_lts ? input_port_f_sign != input_port_f_overflow : 1'b0) | 
		(input_port_opcode == `branch_ops__cb_ges ? input_port_f_sign == input_port_f_overflow : 1'b0) | 
		(input_port_opcode == `branch_ops__cb_lt ? input_port_f_carry : 1'b0) | 
		(input_port_opcode == `branch_ops__cb_ge ?  ~ input_port_f_carry : 1'b0) | 
		(input_port_opcode == `branch_ops__bb_one ? u18_output_port : 1'b0) | 
		(input_port_opcode == `branch_ops__bb_zero ?  ~ u21_output_port : 1'b0) );
	assign spc_branch_target = (input_port_is_branch_insn & input_port_opcode == `branch_ops__pc_w) ? input_port_op_a[31:1] : input_port_branch_addr;
	assign output_port_spc = is_exception ? 1'h0 : spc_branch_target;
	assign in_mode_branch = 
		(input_port_is_branch_insn & input_port_opcode == `branch_ops__pc_w ? 1'h1 : 1'b0) | 
		(input_port_is_branch_insn & input_port_opcode == `branch_ops__tpc_w ? input_port_task_mode : 1'b0) | 
		(is_exception ?  ~ input_port_task_mode : 1'b0) | 
		(input_port_is_branch_insn & input_port_opcode == `branch_ops__stm ? 1'h0 : 1'b0) | 
		(input_port_is_branch_insn & input_port_opcode == `branch_ops__pc_w | input_port_is_branch_insn & input_port_opcode == `branch_ops__tpc_w | is_exception | input_port_is_branch_insn & input_port_opcode == `branch_ops__stm ? 1'b0 : condition_result);
	assign output_port_spc_changed =  ~ input_port_task_mode & (is_exception | in_mode_branch);
	assign branch_target = (input_port_is_branch_insn & input_port_opcode == `branch_ops__pc_w ? input_port_op_a[31:1] : 31'b0) | (input_port_is_branch_insn & input_port_opcode == `branch_ops__tpc_w ? input_port_op_a[31:1] : 31'b0) | (input_port_is_branch_insn & input_port_opcode == `branch_ops__stm ? input_port_tpc : 31'b0) | (input_port_is_branch_insn & input_port_opcode == `branch_ops__pc_w | input_port_is_branch_insn & input_port_opcode == `branch_ops__tpc_w | input_port_is_branch_insn & input_port_opcode == `branch_ops__stm ? 31'b0 : ((is_exception | input_port_interrupt) ? input_port_tpc : input_port_branch_addr));
	assign output_port_tpc_changed = input_port_task_mode ? in_mode_branch | is_exception | input_port_interrupt : input_port_is_branch_insn & input_port_opcode == `branch_ops__tpc_w;
	assign output_port_task_mode_changed = input_port_task_mode ? is_exception | input_port_interrupt : input_port_is_branch_insn & input_port_opcode == `branch_ops__stm;
	assign output_port_task_mode = input_port_task_mode ^ output_port_task_mode_changed;
	assign output_port_do_branch = in_mode_branch | output_port_task_mode_changed;
	assign exception_mask = input_port_fetch_av ? 11'h400 : ((input_port_is_branch_insn & input_port_opcode == `branch_ops__swi) ? (1'h1 << input_port_op_a[2:0]) + 8'b0 : 1'h0) | (input_port_mem_av ? 10'h200 : 1'h0) | (input_port_mem_unaligned ? 9'h100 : 1'h0);
	assign interrupt_mask = (input_port_interrupt & input_port_task_mode) ? 12'h800 : 1'h0;
	assign output_port_ecause = exception_mask | interrupt_mask;

	DecoratorModule_6 u21 (
		.output_port(u21_output_port),
		.word(input_port_op_a),
		.bit_code(input_port_op_b)
	);

	DecoratorModule_7 u18 (
		.output_port(u18_output_port),
		.word(input_port_op_a),
		.bit_code(input_port_op_b)
	);

	assign output_port_is_exception = is_exception;
	assign output_port_tpc = branch_target;
endmodule


////////////////////////////////////////////////////////////////////////////////
// MultUnit
////////////////////////////////////////////////////////////////////////////////
module MultUnit (
	input logic clk,
	input logic rst,
	input logic [31:0] input_port_op_a,
	input logic [31:0] input_port_op_b,
	input logic input_port_valid,

	output logic [31:0] output_port_result
);

	logic [31:0] partial_11;
	logic [31:0] u3_output_port;
	logic [31:0] u6_output_port;
	logic [31:0] s1_partial_11;
	logic [15:0] s1_partial_12;
	logic [15:0] s1_partial_21;
	logic [33:0] u17_output_port;

	assign partial_11 = input_port_op_a[15:0] * input_port_op_b[15:0];
	always_ff @(posedge clk) s1_partial_12 <= rst ? 16'h0 : input_port_valid ? u3_output_port[15:0] : s1_partial_12;
	always_ff @(posedge clk) s1_partial_21 <= rst ? 16'h0 : input_port_valid ? u6_output_port[15:0] : s1_partial_21;
	always_ff @(posedge clk) s1_partial_11 <= rst ? 32'h0 : input_port_valid ? partial_11 : s1_partial_11;
	assign output_port_result = u17_output_port[31:0];

	assign u3_output_port = input_port_op_a[31:16] * input_port_op_b[15:0] + 32'b0;
	assign u6_output_port = input_port_op_a[15:0] * input_port_op_b[31:16] + 32'b0;
	assign u17_output_port = s1_partial_11 + ({s1_partial_12 + s1_partial_21 + 17'b0, 16'h0}) + 34'b0;
endmodule


////////////////////////////////////////////////////////////////////////////////
// ShifterUnit
////////////////////////////////////////////////////////////////////////////////
module ShifterUnit (
	input logic clk,
	input logic rst,
	input logic [31:0] input_port_op_a,
	input logic [31:0] input_port_op_b,
	input logic [1:0] input_port_opcode,

	output logic [31:0] output_port_result
);

	logic signed [31:0] signed_a;
	logic signed [63:0] u13_output_port;

	assign signed_a = input_port_op_a;
	assign output_port_result = u13_output_port[31:0];

	assign u13_output_port = (input_port_opcode == `shifter_ops__shll ? (input_port_op_a << input_port_op_b[4:0]) + 63'b0 : 64'b0) | (input_port_opcode == `shifter_ops__shlr ? input_port_op_a >> input_port_op_b[4:0] : 64'b0) | (input_port_opcode == `shifter_ops__shar ? $signed(signed_a >>> input_port_op_b[4:0]) : 64'b0) ;
endmodule


////////////////////////////////////////////////////////////////////////////////
// BranchTargetUnit
////////////////////////////////////////////////////////////////////////////////
module BranchTargetUnit (
	input logic [1:0] input_port_inst_len,
	input logic [31:0] input_port_op_c,
	input logic [30:0] input_port_pc,

	output logic [30:0] output_port_branch_addr,
	output logic [30:0] output_port_straight_addr
);

	logic [31:0] u18_output_port;
	logic [31:0] u21_output_port;

	assign output_port_branch_addr = u18_output_port[30:0];
	assign output_port_straight_addr = u21_output_port[30:0];

	assign u18_output_port = input_port_pc + ({input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[15:1]}) + 32'b0;
	assign u21_output_port = input_port_pc + input_port_inst_len + 32'b0 + 1'h1;
endmodule


////////////////////////////////////////////////////////////////////////////////
// LoadStoreUnit
////////////////////////////////////////////////////////////////////////////////
module LoadStoreUnit (
	input logic clk,
	input logic rst,
	input logic input_port_is_ldst,
	input logic [1:0] input_port_mem_access_len,
	input logic [21:0] input_port_mem_base,
	input logic [21:0] input_port_mem_limit,
	input logic [31:0] input_port_op_b,
	input logic [31:0] input_port_op_c,
	input logic input_port_task_mode,

	output logic output_port_mem_av,
	output logic output_port_mem_unaligned,
	output logic [31:0] output_port_phy_addr
);

	logic [32:0] u_output_port;
	logic [32:0] u5_output_port;
	logic mem_av;
	logic u14_output_port;
	logic mem_unaligned;
	logic [31:0] u6_output_port;

	always @(*) begin
		case (input_port_mem_access_len)
			2'd0: u14_output_port = 1'h0;
			2'd1: u14_output_port = u6_output_port[0];
			2'd2: u14_output_port = u6_output_port[0] | u6_output_port[1];
			2'd3: u14_output_port = 1'h1;
		endcase
	end
	assign output_port_phy_addr = u5_output_port[31:0];
	assign mem_av = input_port_task_mode & input_port_is_ldst & u6_output_port[31:10] > input_port_mem_limit;
	assign mem_unaligned = input_port_is_ldst & u14_output_port;

	assign u_output_port = input_port_op_b + input_port_op_c + 33'b0;
	assign u5_output_port = u_output_port[31:0] + (input_port_task_mode ? (input_port_mem_base << 4'ha) + 32'b0 : 1'h0) + 33'b0;
	assign output_port_mem_av = mem_av;
	assign output_port_mem_unaligned = mem_unaligned;
	assign u6_output_port = u_output_port[31:0];
endmodule


////////////////////////////////////////////////////////////////////////////////
// AluUnit
////////////////////////////////////////////////////////////////////////////////
module AluUnit (
	input logic clk,
	input logic rst,
	input logic [31:0] input_port_op_a,
	input logic [31:0] input_port_op_b,
	input logic [2:0] input_port_opcode,
	input logic [30:0] input_port_pc,
	input logic [30:0] input_port_tpc,

	output logic output_port_f_carry,
	output logic output_port_f_overflow,
	output logic output_port_f_sign,
	output logic output_port_f_zero,
	output logic [31:0] output_port_result
);

	logic c_in;
	logic [31:0] xor_b;
	logic [31:0] b;
	logic [31:0] a;
	logic [32:0] sum;
	logic [31:0] and_result;
	logic [31:0] xor_result;
	logic use_adder;
	logic use_and;
	logic [32:0] adder_result;

	assign c_in = input_port_opcode == `alu_ops__a_minus_b;
	assign xor_b = (input_port_opcode == `alu_ops__a_minus_b | input_port_opcode == `alu_ops__n_b_and_a) ? 32'hffffffff : 1'h0;
	assign a = input_port_opcode == `alu_ops__pc_plus_b ? ({input_port_pc, 1'h0}) : input_port_op_a;
	assign b = xor_b ^ input_port_op_b;
	assign use_adder = input_port_opcode == `alu_ops__a_plus_b | input_port_opcode == `alu_ops__a_minus_b;
	assign sum = a + b + 33'b0 + c_in;
	assign use_and = input_port_opcode == `alu_ops__a_and_b | input_port_opcode == `alu_ops__n_b_and_a;
	assign and_result = a & b;
	assign xor_result = input_port_op_a ^ input_port_op_b;
	assign adder_result = 
		(use_adder ? sum : 33'b0) | 
		(input_port_opcode == `alu_ops__a_or_b ? input_port_op_a | input_port_op_b : 33'b0) | 
		(use_and ? and_result : 33'b0) | 
		(input_port_opcode == `alu_ops__a_xor_b ? xor_result : 33'b0) | 
		(input_port_opcode == `alu_ops__tpc ? ({input_port_tpc, 1'h0}) : 33'b0) | 
		(input_port_opcode == `alu_ops__pc_plus_b ? sum : 33'b0) ;
	assign output_port_result = adder_result[31:0];
	assign output_port_f_zero = xor_result == 1'h0;
	assign output_port_f_sign = adder_result[31];
	assign output_port_f_carry = adder_result[32] ^ input_port_opcode == `alu_ops__a_minus_b;
	assign output_port_f_overflow = input_port_op_a[31] != input_port_op_b[31] & input_port_op_a[31] != adder_result[31];

endmodule


////////////////////////////////////////////////////////////////////////////////
// ForwardBufLogic_2
////////////////////////////////////////////////////////////////////////////////
module ForwardBufLogic_2 (
	input logic clock_port,
	input logic reset_port,
	input logic input_valid,
	output logic input_ready,
	output logic output_valid,
	input logic output_ready,
	output logic out_reg_en,
	input logic clear
);

	logic buf_valid;

	assign out_reg_en = input_valid & input_ready;
	always_ff @(posedge clock_port) buf_valid <= reset_port ? 1'h0 : clear ? 1'h0 : (input_valid & input_ready) ? 1'h1 : (output_ready & buf_valid) ? 1'h0 : buf_valid;
	assign input_ready =  ~ buf_valid | output_ready;

	assign output_valid = buf_valid;
endmodule


////////////////////////////////////////////////////////////////////////////////
// ForwardBufLogic
////////////////////////////////////////////////////////////////////////////////
module ForwardBufLogic (
	input logic clock_port,
	input logic reset_port,
	input logic input_valid,
	output logic input_ready,
	output logic output_valid,
	input logic output_ready,
	output logic out_reg_en,
	input logic clear
);

	logic buf_valid;

	assign out_reg_en = input_valid & input_ready;
	always_ff @(posedge clock_port) buf_valid <= reset_port ? 1'h0 : clear ? 1'h0 : (input_valid & input_ready) ? 1'h1 : (output_ready & buf_valid) ? 1'h0 : buf_valid;
	assign input_ready =  ~ buf_valid | output_ready;

	assign output_valid = buf_valid;
endmodule


////////////////////////////////////////////////////////////////////////////////
// DecodeStage
////////////////////////////////////////////////////////////////////////////////
module DecodeStage (
	input logic clk,
	input logic rst,
	input logic fetch_av,
	input logic [15:0] fetch_inst_0,
	input logic [15:0] fetch_inst_1,
	input logic [15:0] fetch_inst_2,
	input logic [1:0] fetch_inst_len,
	output logic fetch_ready,
	input logic fetch_valid,

	output logic [2:0] output_port_alu_op,
	output logic [3:0] output_port_branch_op,
	output logic output_port_do_bse,
	output logic output_port_do_bze,
	output logic output_port_do_wse,
	output logic output_port_do_wze,
	output logic [2:0] output_port_exec_unit,
	output logic output_port_fetch_av,
	output logic [1:0] output_port_inst_len,
	output logic output_port_ldst_op,
	output logic [1:0] output_port_mem_access_len,
	output logic [31:0] output_port_op_a,
	output logic [31:0] output_port_op_b,
	output logic [31:0] output_port_op_c,
	input logic output_port_ready,
	output logic [3:0] output_port_result_reg_addr,
	output logic output_port_result_reg_addr_valid,
	output logic [1:0] output_port_shifter_op,
	output logic output_port_valid,

	output logic [3:0] reg_file_req_read1_addr,
	output logic reg_file_req_read1_valid,
	output logic [3:0] reg_file_req_read2_addr,
	output logic reg_file_req_read2_valid,
	input logic reg_file_req_ready,
	output logic [3:0] reg_file_req_rsv_addr,
	output logic reg_file_req_rsv_valid,
	output logic reg_file_req_valid,

	input logic [31:0] reg_file_rsp_read1_data,
	input logic [31:0] reg_file_rsp_read2_data,
	output logic reg_file_rsp_ready,
	input logic reg_file_rsp_valid,

	input logic do_branch
);

	logic [31:0] field_e;
	logic field_a_is_f;
	logic field_b_is_f;
	logic field_c_is_f;
	logic field_d_is_f;
	logic [31:0] tiny_ofs;
	logic [3:0] tiny_field_a;
	logic [4:0] u40_output_port;
	logic [31:0] ones_field_a;
	logic mask_for_rd_eq_ra_lsl_rb;
	logic mask_for_rd_eq_ra_lsr_rb;
	logic mask_for_rd_eq_ra_asr_rb;
	logic mask_for_rd_eq_field_e_lsl_rb;
	logic mask_for_rd_eq_field_e_lsr_rb;
	logic mask_for_rd_eq_field_e_asr_rb;
	logic mask_for_rd_eq_ra_lsl_field_e;
	logic mask_for_rd_eq_ra_lsr_field_e;
	logic mask_for_rd_eq_ra_asr_field_e;
	logic mask_for_rd_eq_ra_times_rb;
	logic mask_for_rd_eq_field_e_times_rb;
	logic mask_for_rd_eq_field_e_times_ra;
	logic mask_for_swi;
	logic mask_for_stm;
	logic mask_for_woi;
	logic mask_for_sii;
	logic mask_for_fence;
	logic mask_for_pc_eq_rd;
	logic mask_for_tpc_eq_rd;
	logic mask_for_rd_eq_pc;
	logic mask_for_rd_eq_tpc;
	logic mask_for_sii_1;
	logic mask_for_rd_eq_tiny_field_a;
	logic mask_for_rd_eq_pc_plus_field_atimes2;
	logic mask_for_rd_eq_minus_ra;
	logic mask_for_rd_eq_notra;
	logic mask_for_rd_eq_bse_ra;
	logic mask_for_rd_eq_wse_ra;
	logic mask_for_sii_2;
	logic mask_for_rd_eq_ra_xor_rb;
	logic mask_for_rd_eq_ra_or_rb;
	logic mask_for_rd_eq_ra_and_rb;
	logic mask_for_rd_eq_ra_plus_rb;
	logic mask_for_rd_eq_ra_minus_rb;
	logic mask_for_rd_eq_notra_and_rb;
	logic mask_for_rd_eq_tiny_rb_plus_field_a;
	logic mask_for_rd_eq_value;
	logic mask_for_pc_eq_value;
	logic mask_for_tpc_eq_value;
	logic mask_for_sii_3;
	logic mask_for_sii_4;
	logic mask_for_rd_eq_field_e_xor_rb;
	logic mask_for_rd_eq_field_e_or_rb;
	logic mask_for_rd_eq_field_e_and_rb;
	logic mask_for_rd_eq_field_e_plus_rb;
	logic mask_for_rd_eq_field_e_minus_rb;
	logic mask_for_sii_5;
	logic mask_for_sii_6;
	logic mask_for_rd_eq_short_value;
	logic mask_for_pc_eq_short_value;
	logic mask_for_tpc_eq_short_value;
	logic mask_for_rd_eq_field_e_xor_ra;
	logic mask_for_rd_eq_field_e_or_ra;
	logic mask_for_rd_eq_field_e_and_ra;
	logic mask_for_rd_eq_field_e_plus_ra;
	logic mask_for_rd_eq_field_e_minus_ra;
	logic mask_for_sii_7;
	logic mask_for_sii_8;
	logic mask_for_if_ra_eq_0;
	logic mask_for_if_ra_ne_0;
	logic mask_for_if_ra_lt_0;
	logic mask_for_if_ra_ge_0;
	logic mask_for_if_ra_gt_0;
	logic mask_for_if_ra_le_0;
	logic mask_for_sii_9;
	logic mask_for_sii_10;
	logic mask_for_if_ra_eq_0_1;
	logic mask_for_if_ra_ne_0_1;
	logic mask_for_if_ra_lt_0_1;
	logic mask_for_if_ra_ge_0_1;
	logic mask_for_if_ra_gt_0_1;
	logic mask_for_if_ra_le_0_1;
	logic mask_for_sii_11;
	logic mask_for_if_rb_eq_ra;
	logic mask_for_if_rb_ne_ra;
	logic mask_for_if_signed_rb_lt_ra;
	logic mask_for_if_signed_rb_ge_ra;
	logic mask_for_if_rb_lt_ra;
	logic mask_for_if_rb_ge_ra;
	logic mask_for_sii_12;
	logic mask_for_sii_13;
	logic mask_for_if_rb_eq_ra_1;
	logic mask_for_if_rb_ne_ra_1;
	logic mask_for_if_signed_rb_lt_ra_1;
	logic mask_for_if_signed_rb_ge_ra_1;
	logic mask_for_if_rb_lt_ra_1;
	logic mask_for_if_rb_ge_ra_1;
	logic mask_for_if_ra_bit__eq_1;
	logic mask_for_if_rb_bit__eq_0;
	logic mask_for_mem_raplustiny_ofstimes4_eq_rd;
	logic mask_for_rd_eq_mem_raplustiny_ofstimes4;
	logic mask_for_sii_14;
	logic mask_for_sii_15;
	logic mask_for_sii_16;
	logic mask_for_sii_17;
	logic mask_for_rd_eq_mem8_ra;
	logic mask_for_rd_eq_mem16_ra;
	logic mask_for_rd_eq_mem32_ra;
	logic mask_for_rd_eq_memll32_ra;
	logic mask_for_mem8_ra_eq_rd;
	logic mask_for_mem16_ra_eq_rd;
	logic mask_for_mem32_ra_eq_rd;
	logic mask_for_memsr32_ra_eq_rd;
	logic mask_for_rd_eq_smem8_ra;
	logic mask_for_rd_eq_smem16_ra;
	logic mask_for_sii_18;
	logic mask_for_sii_19;
	logic mask_for_sii_20;
	logic mask_for_sii_21;
	logic mask_for_sii_22;
	logic mask_for_sii_23;
	logic mask_for_rd_eq_mem8_raplusfield_e;
	logic mask_for_rd_eq_mem16_raplusfield_e;
	logic mask_for_rd_eq_mem32_raplusfield_e;
	logic mask_for_rd_eq_memll32_raplusfield_e;
	logic mask_for_mem8_raplusfield_e_eq_rd;
	logic mask_for_mem16_raplusfield_e_eq_rd;
	logic mask_for_mem32_raplusfield_e_eq_rd;
	logic mask_for_memsr32_raplusfield_e_eq_rd;
	logic mask_for_rd_eq_smem8_raplusfield_e;
	logic mask_for_rd_eq_smem16_raplusfield_e;
	logic mask_for_sii_24;
	logic mask_for_sii_25;
	logic mask_for_sii_26;
	logic mask_for_rd_eq_mem8_field_e;
	logic mask_for_rd_eq_mem16_field_e;
	logic mask_for_rd_eq_mem32_field_e;
	logic mask_for_rd_eq_memll32_field_e;
	logic mask_for_mem8_field_e_eq_rd;
	logic mask_for_mem16_field_e_eq_rd;
	logic mask_for_mem32_field_e_eq_rd;
	logic mask_for_memsr32_field_e_eq_rd;
	logic mask_for_rd_eq_smem8_field_e;
	logic mask_for_rd_eq_smem16_field_e;
	logic mask_for_sii_27;
	logic mask_for_sii_28;
	logic mask_for_sii_29;
	logic expr;
	logic mask_expr;
	logic group_1_for_exec_unit;
	logic group_2_for_exec_unit;
	logic group_3_for_exec_unit;
	logic group_4_for_exec_unit;
	logic group_5_for_exec_unit;
	logic [2:0] exec_unit;
	logic group_1_for_alu_op;
	logic group_2_for_alu_op;
	logic group_3_for_alu_op;
	logic group_4_for_alu_op;
	logic group_5_for_alu_op;
	logic group_6_for_alu_op;
	logic group_7_for_alu_op;
	logic group_8_for_alu_op;
	logic [2:0] alu_op;
	logic group_1_for_shifter_op;
	logic group_2_for_shifter_op;
	logic group_3_for_shifter_op;
	logic [1:0] shifter_op;
	logic group_1_for_branch_op;
	logic group_2_for_branch_op;
	logic group_3_for_branch_op;
	logic group_4_for_branch_op;
	logic group_5_for_branch_op;
	logic group_6_for_branch_op;
	logic group_7_for_branch_op;
	logic group_8_for_branch_op;
	logic group_9_for_branch_op;
	logic group_10_for_branch_op;
	logic group_11_for_branch_op;
	logic group_12_for_branch_op;
	logic [3:0] branch_op;
	logic group_1_for_ldst_op;
	logic group_2_for_ldst_op;
	logic ldst_op;
	logic group_1_for_rd1_addr;
	logic group_2_for_rd1_addr;
	logic group_3_for_rd1_addr;
	logic [3:0] rd1_addr;
	logic group_1_for_res_addr;
	logic [3:0] res_addr;
	logic group_1_for_rd2_addr;
	logic group_2_for_rd2_addr;
	logic group_3_for_rd2_addr;
	logic [3:0] rd2_addr;
	logic group_1_for_use_reg_a;
	logic use_reg_a;
	logic group_1_for_use_reg_b;
	logic use_reg_b;
	logic group_1_for_op_a;
	logic group_2_for_op_a;
	logic group_3_for_op_a;
	logic group_4_for_op_a;
	logic group_5_for_op_a;
	logic [31:0] op_a;
	logic group_1_for_op_b;
	logic group_2_for_op_b;
	logic group_3_for_op_b;
	logic group_4_for_op_b;
	logic [31:0] op_b;
	logic group_1_for_op_c;
	logic group_2_for_op_c;
	logic group_3_for_op_c;
	logic [31:0] op_c;
	logic group_1_for_mem_len;
	logic group_2_for_mem_len;
	logic group_3_for_mem_len;
	logic [1:0] mem_len;
	logic group_1_for_bse;
	logic bse;
	logic group_1_for_wse;
	logic wse;
	logic group_1_for_bze;
	logic bze;
	logic group_1_for_wze;
	logic wze;
	logic group_1_for_read1_needed;
	logic read1_needed;
	logic group_1_for_read2_needed;
	logic read2_needed;
	logic group_1_for_rsv_needed;
	logic rsv_needed;
	logic register_outputs;
	logic u1795_output_port;
	logic [31:0] u1796_output_port;
	logic u1798_output_port;
	logic [31:0] u1799_output_port;
	logic [1:0] u1802_output_port;
	logic [3:0] u22_output_port;
	logic [3:0] field_a_plus_one;

	assign tiny_ofs = {fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7:1], 2'h0};
	assign field_a_plus_one = u40_output_port[3:0];
	assign field_d_is_f = fetch_inst_0[15:12] == 4'hf;
	assign field_b_is_f = fetch_inst_0[7:4] == 4'hf;
	assign field_a_is_f = fetch_inst_0[3:0] == 4'hf;
	assign field_c_is_f = fetch_inst_0[11:8] == 4'hf;
	assign mask_for_rd_eq_ra_lsl_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h6 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_lsr_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h7 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_asr_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'h8 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_lsl_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h6 &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_field_e_lsr_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h7 &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_field_e_asr_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'h8 &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_ra_lsl_field_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h6 & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_lsr_field_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h7 & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_asr_field_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'h8 & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_times_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'h9 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_times_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'h9 &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_field_e_times_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'h9 & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_swi = 1'h1 & fetch_inst_0[15:12] < 4'h8 & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 & fetch_inst_0[3:0] == 1'h0;
	assign mask_for_stm = 1'h1 & fetch_inst_0[15:12] == 4'h8 & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 & fetch_inst_0[3:0] == 1'h0;
	assign mask_for_woi = 1'h1 & fetch_inst_0[15:12] == 4'h9 & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 & fetch_inst_0[3:0] == 1'h0;
	assign mask_for_sii = 1'h1 & fetch_inst_0[15:12] > 4'h9 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 & fetch_inst_0[3:0] == 1'h0;
	assign mask_for_pc_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 & fetch_inst_0[3:0] == 2'h2;
	assign mask_for_tpc_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 & fetch_inst_0[3:0] == 2'h3;
	assign mask_for_sii_1 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 & fetch_inst_0[3:0] > 3'h5 &  ~ field_a_is_f;
	assign mask_for_sii_2 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] > 3'h6 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_pc_eq_value = 1'h1 & fetch_inst_0[15:12] == 2'h2 & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'he & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_tpc_eq_value = 1'h1 & fetch_inst_0[15:12] == 2'h3 & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'he & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_sii_3 = 1'h1 & fetch_inst_0[15:12] == 4'h8 & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'he & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_sii_4 = 1'h1 & fetch_inst_0[15:12] == 4'h9 & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'he & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_sii_5 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'ha &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_sii_6 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hb &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_pc_eq_short_value = 1'h1 & fetch_inst_0[15:12] == 2'h2 & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'hf & fetch_inst_0[3:0] == 4'he;
	assign mask_for_tpc_eq_short_value = 1'h1 & fetch_inst_0[15:12] == 2'h3 & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'hf & fetch_inst_0[3:0] == 4'he;
	assign mask_for_sii_7 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'ha & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_sii_8 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hb & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_if_ra_eq_0 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 &  ~ field_a_is_f;
	assign mask_for_if_ra_ne_0 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h1 &  ~ field_a_is_f;
	assign mask_for_if_ra_lt_0 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 2'h2 &  ~ field_a_is_f;
	assign mask_for_if_ra_ge_0 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 2'h3 &  ~ field_a_is_f;
	assign mask_for_if_ra_gt_0 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 3'h4 &  ~ field_a_is_f;
	assign mask_for_if_ra_le_0 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 3'h5 &  ~ field_a_is_f;
	assign mask_for_sii_9 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 3'h6 &  ~ field_a_is_f;
	assign mask_for_sii_10 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 3'h7 &  ~ field_a_is_f;
	assign mask_for_if_ra_eq_0_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'h8 &  ~ field_a_is_f;
	assign mask_for_if_ra_ne_0_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'h9 &  ~ field_a_is_f;
	assign mask_for_if_ra_lt_0_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'ha &  ~ field_a_is_f;
	assign mask_for_if_ra_ge_0_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'hb &  ~ field_a_is_f;
	assign mask_for_if_ra_gt_0_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'hc &  ~ field_a_is_f;
	assign mask_for_if_ra_le_0_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'hd &  ~ field_a_is_f;
	assign mask_for_sii_11 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'he &  ~ field_a_is_f;
	assign mask_for_if_rb_eq_ra = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 1'h1 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_ne_ra = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 2'h2 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_signed_rb_lt_ra = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 2'h3 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_signed_rb_ge_ra = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 3'h4 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_lt_ra = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 3'h5 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_ge_ra = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 3'h6 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_sii_12 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 3'h7 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_sii_13 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 4'h8 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_eq_ra_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 4'h9 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_ne_ra_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 4'ha &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_signed_rb_lt_ra_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 4'hb &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_signed_rb_ge_ra_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 4'hc &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_lt_ra_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 4'hd &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_ge_ra_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf & fetch_inst_0[11:8] == 4'he &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_ra_bit__eq_1 = 1'h1 & fetch_inst_0[15:12] == 4'hf &  ~ field_c_is_f & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_if_rb_bit__eq_0 = 1'h1 & fetch_inst_0[15:12] == 4'hf &  ~ field_c_is_f &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_sii_14 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 1'h0 &  ~ field_a_is_f;
	assign mask_for_sii_15 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 1'h1 &  ~ field_a_is_f;
	assign mask_for_sii_16 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 2'h2 &  ~ field_a_is_f;
	assign mask_for_sii_17 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 2'h3 &  ~ field_a_is_f;
	assign mask_for_sii_18 = 1'h1 & fetch_inst_0[15:12] == 1'h1 & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'he &  ~ field_a_is_f;
	assign mask_for_sii_19 = 1'h1 & fetch_inst_0[15:12] == 2'h2 & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'he &  ~ field_a_is_f;
	assign mask_for_sii_20 = 1'h1 & fetch_inst_0[15:12] == 2'h3 & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'he &  ~ field_a_is_f;
	assign mask_for_sii_21 = 1'h1 & fetch_inst_0[15:12] == 1'h1 & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'he &  ~ field_a_is_f;
	assign mask_for_sii_22 = 1'h1 & fetch_inst_0[15:12] == 2'h2 & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'he &  ~ field_a_is_f;
	assign mask_for_sii_23 = 1'h1 & fetch_inst_0[15:12] == 2'h3 & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'he &  ~ field_a_is_f;
	assign mask_for_sii_24 = 1'h1 & fetch_inst_0[15:12] == 1'h1 & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'he &  ~ field_a_is_f;
	assign mask_for_sii_25 = 1'h1 & fetch_inst_0[15:12] == 2'h2 & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'he &  ~ field_a_is_f;
	assign mask_for_sii_26 = 1'h1 & fetch_inst_0[15:12] == 2'h3 & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'he &  ~ field_a_is_f;
	assign mask_for_sii_27 = 1'h1 & fetch_inst_0[15:12] == 1'h1 & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'he & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_sii_28 = 1'h1 & fetch_inst_0[15:12] == 2'h2 & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'he & fetch_inst_0[3:0] == 4'hf;
	assign mask_expr = 1'h1 & fetch_inst_0[15:12] == 2'h3 & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'he & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_fence = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 & fetch_inst_0[3:0] == 1'h1;
	assign mask_for_rd_eq_pc = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 & fetch_inst_0[3:0] == 3'h4;
	assign mask_for_rd_eq_tpc = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 & fetch_inst_0[3:0] == 3'h5;
	assign mask_for_rd_eq_tiny_field_a = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h1 &  ~ field_a_is_f;
	assign mask_for_rd_eq_pc_plus_field_atimes2 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 2'h2 &  ~ field_a_is_f;
	assign mask_for_rd_eq_minus_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 2'h3 &  ~ field_a_is_f;
	assign mask_for_rd_eq_notra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 3'h4 &  ~ field_a_is_f;
	assign mask_for_rd_eq_bse_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 3'h5 &  ~ field_a_is_f;
	assign mask_for_rd_eq_wse_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 3'h6 &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_xor_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h1 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_or_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 2'h2 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_and_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 2'h3 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_plus_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h4 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_minus_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h5 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_notra_and_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'ha &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_tiny_rb_plus_field_a = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hb &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_value = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 1'h0 & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_field_e_xor_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h1 &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_field_e_or_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 2'h2 &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_field_e_and_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 2'h3 &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_field_e_plus_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h4 &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_field_e_minus_rb = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h5 &  ~ field_b_is_f & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_short_value = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h0 & fetch_inst_0[7:4] == 4'hf & fetch_inst_0[3:0] == 1'h0;
	assign mask_for_rd_eq_field_e_xor_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 1'h1 & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_or_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 2'h2 & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_and_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 2'h3 & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_plus_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h4 & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_minus_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 3'h5 & fetch_inst_0[7:4] == 4'hf &  ~ field_a_is_f;
	assign mask_for_mem_raplustiny_ofstimes4_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hc;
	assign mask_for_rd_eq_mem_raplustiny_ofstimes4 = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hd;
	assign mask_for_rd_eq_mem8_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 3'h4 &  ~ field_a_is_f;
	assign mask_for_rd_eq_mem16_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 3'h5 &  ~ field_a_is_f;
	assign mask_for_rd_eq_mem32_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 3'h6 &  ~ field_a_is_f;
	assign mask_for_rd_eq_memll32_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 3'h7 &  ~ field_a_is_f;
	assign mask_for_mem8_ra_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'h8 &  ~ field_a_is_f;
	assign mask_for_mem16_ra_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'h9 &  ~ field_a_is_f;
	assign mask_for_mem32_ra_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'ha &  ~ field_a_is_f;
	assign mask_for_memsr32_ra_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'hb &  ~ field_a_is_f;
	assign mask_for_rd_eq_smem8_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'hc &  ~ field_a_is_f;
	assign mask_for_rd_eq_smem16_ra = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'he & fetch_inst_0[7:4] == 4'hd &  ~ field_a_is_f;
	assign mask_for_rd_eq_mem8_raplusfield_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 3'h4 &  ~ field_a_is_f;
	assign mask_for_rd_eq_mem16_raplusfield_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 3'h5 &  ~ field_a_is_f;
	assign mask_for_rd_eq_mem32_raplusfield_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 3'h6 &  ~ field_a_is_f;
	assign mask_for_rd_eq_memll32_raplusfield_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 3'h7 &  ~ field_a_is_f;
	assign mask_for_mem8_raplusfield_e_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'h8 &  ~ field_a_is_f;
	assign mask_for_mem16_raplusfield_e_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'h9 &  ~ field_a_is_f;
	assign mask_for_mem32_raplusfield_e_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'ha &  ~ field_a_is_f;
	assign mask_for_memsr32_raplusfield_e_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'hb &  ~ field_a_is_f;
	assign mask_for_rd_eq_smem8_raplusfield_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'hc &  ~ field_a_is_f;
	assign mask_for_rd_eq_smem16_raplusfield_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'hd &  ~ field_a_is_f;
	assign mask_for_rd_eq_mem8_field_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 3'h4 & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_mem16_field_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 3'h5 & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_mem32_field_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 3'h6 & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_memll32_field_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 3'h7 & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_mem8_field_e_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'h8 & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_mem16_field_e_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'h9 & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_mem32_field_e_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'ha & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_memsr32_field_e_eq_rd = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'hb & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_smem8_field_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'hc & fetch_inst_0[3:0] == 4'hf;
	assign mask_for_rd_eq_smem16_field_e = 1'h1 &  ~ field_d_is_f & fetch_inst_0[11:8] == 4'hf & fetch_inst_0[7:4] == 4'hd & fetch_inst_0[3:0] == 4'hf;
	assign group_1_for_exec_unit = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e;
	assign group_2_for_exec_unit = mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra;
	assign group_3_for_exec_unit = mask_for_swi | mask_for_stm | mask_for_woi | mask_for_sii | mask_for_pc_eq_rd | mask_for_tpc_eq_rd | mask_for_sii_1 | mask_for_sii_2 | mask_for_pc_eq_value | mask_for_tpc_eq_value | mask_for_sii_3 | mask_for_sii_4 | mask_for_sii_5 | mask_for_sii_6 | mask_for_pc_eq_short_value | mask_for_tpc_eq_short_value | mask_for_sii_7 | mask_for_sii_8 | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_sii_9 | mask_for_sii_10 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_sii_11 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_sii_12 | mask_for_sii_13 | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_if_ra_bit__eq_1 | mask_for_if_rb_bit__eq_0 | mask_for_sii_14 | mask_for_sii_15 | mask_for_sii_16 | mask_for_sii_17 | mask_for_sii_18 | mask_for_sii_19 | mask_for_sii_20 | mask_for_sii_21 | mask_for_sii_22 | mask_for_sii_23 | mask_for_sii_24 | mask_for_sii_25 | mask_for_sii_26 | mask_for_sii_27 | mask_for_sii_28 | mask_expr;
	assign group_4_for_exec_unit = mask_for_fence | mask_for_rd_eq_pc | mask_for_rd_eq_tpc | mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_pc_plus_field_atimes2 | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_notra_and_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_rd_eq_value | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_short_value | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra;
	assign group_5_for_exec_unit = mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
	assign group_1_for_alu_op = mask_for_woi | mask_for_rd_eq_minus_ra | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_field_e_minus_ra | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1;
	assign group_2_for_alu_op = mask_for_rd_eq_pc | mask_for_rd_eq_pc_plus_field_atimes2;
	assign group_3_for_alu_op = mask_for_rd_eq_tpc;
	assign group_4_for_alu_op = mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_value | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_short_value | mask_for_rd_eq_field_e_or_ra;
	assign group_5_for_alu_op = mask_for_rd_eq_notra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_xor_ra;
	assign group_6_for_alu_op = mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_and_ra;
	assign group_7_for_alu_op = mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_plus_ra;
	assign group_8_for_alu_op = mask_for_rd_eq_notra_and_rb;
	assign group_1_for_shifter_op = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_ra_lsl_field_e;
	assign group_2_for_shifter_op = mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_ra_lsr_field_e;
	assign group_3_for_shifter_op = mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_asr_field_e;
	assign group_1_for_branch_op = mask_for_swi | mask_for_sii | mask_for_sii_1 | mask_for_sii_2 | mask_for_sii_3 | mask_for_sii_4 | mask_for_sii_5 | mask_for_sii_6 | mask_for_sii_7 | mask_for_sii_8 | mask_for_sii_9 | mask_for_sii_10 | mask_for_sii_11 | mask_for_sii_12 | mask_for_sii_13 | mask_for_sii_14 | mask_for_sii_15 | mask_for_sii_16 | mask_for_sii_17 | mask_for_sii_18 | mask_for_sii_19 | mask_for_sii_20 | mask_for_sii_21 | mask_for_sii_22 | mask_for_sii_23 | mask_for_sii_24 | mask_for_sii_25 | mask_for_sii_26 | mask_for_sii_27 | mask_for_sii_28 | mask_expr;
	assign group_2_for_branch_op = mask_for_stm;
	assign group_3_for_branch_op = mask_for_woi | mask_for_if_ra_eq_0 | mask_for_if_ra_eq_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_eq_ra_1;
	assign group_4_for_branch_op = mask_for_pc_eq_rd | mask_for_pc_eq_value | mask_for_pc_eq_short_value;
	assign group_5_for_branch_op = mask_for_tpc_eq_rd | mask_for_tpc_eq_value | mask_for_tpc_eq_short_value;
	assign group_6_for_branch_op = mask_for_if_ra_ne_0 | mask_for_if_ra_ne_0_1 | mask_for_if_rb_ne_ra | mask_for_if_rb_ne_ra_1;
	assign group_7_for_branch_op = mask_for_if_ra_lt_0 | mask_for_if_ra_gt_0 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_gt_0_1 | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_lt_ra_1;
	assign group_8_for_branch_op = mask_for_if_ra_ge_0 | mask_for_if_ra_le_0 | mask_for_if_ra_ge_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_signed_rb_ge_ra | mask_for_if_signed_rb_ge_ra_1;
	assign group_9_for_branch_op = mask_for_if_rb_lt_ra | mask_for_if_rb_lt_ra_1;
	assign group_10_for_branch_op = mask_for_if_rb_ge_ra | mask_for_if_rb_ge_ra_1;
	assign group_11_for_branch_op = mask_for_if_ra_bit__eq_1;
	assign group_12_for_branch_op = mask_for_if_rb_bit__eq_0;
	assign group_1_for_ldst_op = mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd;
	assign group_2_for_ldst_op = mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
	assign group_1_for_rd1_addr = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e | mask_for_rd_eq_ra_times_rb | mask_for_woi | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_notra_and_rb | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_ra_bit__eq_1;
	assign group_2_for_rd1_addr = mask_for_pc_eq_rd | mask_for_tpc_eq_rd | mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd;
	assign group_3_for_rd1_addr = mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_if_rb_bit__eq_0;
	assign group_1_for_res_addr = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e | mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra | mask_for_rd_eq_pc | mask_for_rd_eq_tpc | mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_pc_plus_field_atimes2 | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_notra_and_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_rd_eq_value | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_short_value | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
	assign group_1_for_rd2_addr = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_woi | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_notra_and_rb | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb;
	assign group_2_for_rd2_addr = mask_for_rd_eq_field_e_times_ra | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e;
	assign group_3_for_rd2_addr = mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4;
	assign tiny_field_a = 4'hc | fetch_inst_0[0];
	assign group_1_for_use_reg_a = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e | mask_for_rd_eq_ra_times_rb | mask_for_woi | mask_for_pc_eq_rd | mask_for_tpc_eq_rd | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_notra_and_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_if_ra_bit__eq_1 | mask_for_if_rb_bit__eq_0 | mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd;
	assign group_1_for_use_reg_b = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra | mask_for_woi | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_notra_and_rb | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e;
	assign group_1_for_op_a = mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra | mask_for_rd_eq_value | mask_for_pc_eq_value | mask_for_tpc_eq_value | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_short_value | mask_for_pc_eq_short_value | mask_for_tpc_eq_short_value | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra;
	assign field_e = fetch_inst_len == 2'h2 ? ({fetch_inst_2, fetch_inst_1}) : ({fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1});
	assign group_2_for_op_a = mask_for_swi;
	assign group_3_for_op_a = mask_for_sii | mask_for_sii_1 | mask_for_sii_2 | mask_for_sii_3 | mask_for_sii_4 | mask_for_sii_5 | mask_for_sii_6 | mask_for_sii_7 | mask_for_sii_8 | mask_for_sii_9 | mask_for_sii_10 | mask_for_sii_11 | mask_for_sii_12 | mask_for_sii_13 | mask_for_sii_14 | mask_for_sii_15 | mask_for_sii_16 | mask_for_sii_17 | mask_for_sii_18 | mask_for_sii_19 | mask_for_sii_20 | mask_for_sii_21 | mask_for_sii_22 | mask_for_sii_23 | mask_for_sii_24 | mask_for_sii_25 | mask_for_sii_26 | mask_for_sii_27 | mask_for_sii_28 | mask_expr;
	assign group_4_for_op_a = mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_minus_ra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1;
	assign group_5_for_op_a = mask_for_rd_eq_notra;
	assign group_1_for_op_b = mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e;
	assign group_2_for_op_b = mask_for_rd_eq_pc | mask_for_rd_eq_value | mask_for_rd_eq_short_value | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
	assign group_3_for_op_b = mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_pc_plus_field_atimes2 | mask_for_rd_eq_tiny_rb_plus_field_a;
	assign ones_field_a = u22_output_port[3] ? ({field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one}) : fetch_inst_0[3:0];
	assign group_4_for_op_b = mask_for_if_ra_bit__eq_1 | mask_for_if_rb_bit__eq_0;
	assign group_1_for_op_c = mask_for_woi | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra;
	assign group_2_for_op_c = mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_if_ra_bit__eq_1 | mask_for_if_rb_bit__eq_0 | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
	assign group_3_for_op_c = mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4;
	assign group_1_for_mem_len = mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd;
	assign group_2_for_mem_len = mask_for_rd_eq_mem8_ra | mask_for_mem8_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_mem8_field_e | mask_for_mem8_field_e_eq_rd | mask_for_rd_eq_smem8_field_e;
	assign group_3_for_mem_len = mask_for_rd_eq_mem16_ra | mask_for_mem16_ra_eq_rd | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem16_raplusfield_e | mask_for_mem16_raplusfield_e_eq_rd | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_mem16_field_e | mask_for_mem16_field_e_eq_rd | mask_for_rd_eq_smem16_field_e;
	assign group_1_for_bse = mask_for_rd_eq_bse_ra | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem8_field_e;
	assign group_1_for_wse = mask_for_rd_eq_wse_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_smem16_field_e;
	assign group_1_for_bze = mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem8_field_e;
	assign group_1_for_wze = mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem16_field_e;
	assign group_1_for_read1_needed = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e | mask_for_rd_eq_ra_times_rb | mask_for_woi | mask_for_pc_eq_rd | mask_for_tpc_eq_rd | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_notra_and_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_if_ra_bit__eq_1 | mask_for_if_rb_bit__eq_0 | mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd;
	assign group_1_for_read2_needed = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra | mask_for_woi | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_notra_and_rb | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e;
	assign group_1_for_rsv_needed = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e | mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra | mask_for_rd_eq_pc | mask_for_rd_eq_tpc | mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_pc_plus_field_atimes2 | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_notra_and_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_rd_eq_value | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_short_value | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
	assign reg_file_req_valid = fetch_valid &  ~ do_branch;
	assign rd1_addr = (group_1_for_rd1_addr ? fetch_inst_0[3:0] : 4'b0) | (group_2_for_rd1_addr ? fetch_inst_0[15:12] : 4'b0) | (group_3_for_rd1_addr ? fetch_inst_0[7:4] : 4'b0) ;
	assign reg_file_req_read1_addr = rd1_addr;
	assign read1_needed = fetch_av ? 1'h0 : (group_1_for_read1_needed ? 1'h1 : 1'b0) | (group_1_for_read1_needed ? 1'b0 : 1'h0);
	assign reg_file_req_read1_valid = read1_needed &  ~ do_branch;
	assign rd2_addr = (group_1_for_rd2_addr ? fetch_inst_0[7:4] : 4'b0) | (group_2_for_rd2_addr ? fetch_inst_0[3:0] : 4'b0) | (group_3_for_rd2_addr ? tiny_field_a : 4'b0) ;
	assign reg_file_req_read2_addr = rd2_addr;
	assign read2_needed = fetch_av ? 1'h0 : (group_1_for_read2_needed ? 1'h1 : 1'b0) | (group_1_for_read2_needed ? 1'b0 : 1'h0);
	assign reg_file_req_read2_valid = read2_needed &  ~ do_branch;
	assign res_addr = (group_1_for_res_addr ? fetch_inst_0[15:12] : 4'b0) ;
	assign reg_file_req_rsv_addr = res_addr;
	assign rsv_needed = fetch_av ? 1'h0 : (group_1_for_rsv_needed ? 1'h1 : 1'b0) | (group_1_for_rsv_needed ? 1'b0 : 1'h0);
	assign reg_file_req_rsv_valid = rsv_needed &  ~ do_branch;
	assign exec_unit = 
		(group_1_for_exec_unit ? `op_class__shift : 3'b0) | 
		(group_2_for_exec_unit ? `op_class__mult : 3'b0) | 
		(group_3_for_exec_unit ? `op_class__branch : 3'b0) | 
		(group_4_for_exec_unit ? `op_class__alu : 3'b0) | 
		(group_5_for_exec_unit ? `op_class__ld_st : 3'b0) ;
	assign register_outputs = reg_file_req_ready & reg_file_req_valid;
	always_ff @(posedge clk) output_port_exec_unit <= rst ? 3'h0 : register_outputs ? exec_unit : output_port_exec_unit;
	assign alu_op = 
		(group_1_for_alu_op ? `alu_ops__a_minus_b : 3'b0) | 
		(group_2_for_alu_op ? `alu_ops__pc_plus_b : 3'b0) | 
		(group_3_for_alu_op ? `alu_ops__tpc : 3'b0) | 
		(group_4_for_alu_op ? `alu_ops__a_or_b : 3'b0) | 
		(group_5_for_alu_op ? `alu_ops__a_xor_b : 3'b0) | 
		(group_6_for_alu_op ? `alu_ops__a_and_b : 3'b0) | 
		(group_7_for_alu_op ? `alu_ops__a_plus_b : 3'b0) | 
		(group_8_for_alu_op ? `alu_ops__n_b_and_a : 3'b0) ;
	always_ff @(posedge clk) output_port_alu_op <= rst ? 3'h0 : register_outputs ? alu_op : output_port_alu_op;
	assign shifter_op = (group_1_for_shifter_op ? `shifter_ops__shll : 2'b0) | (group_2_for_shifter_op ? `shifter_ops__shlr : 2'b0) | (group_3_for_shifter_op ? `shifter_ops__shar : 2'b0) ;
	always_ff @(posedge clk) output_port_shifter_op <= rst ? 2'h0 : register_outputs ? shifter_op : output_port_shifter_op;
	assign branch_op = 
		(group_1_for_branch_op ? `branch_ops__swi : 4'b0) | 
		(group_2_for_branch_op ? `branch_ops__stm : 4'b0) | 
		(group_3_for_branch_op ? `branch_ops__cb_eq : 4'b0) | 
		(group_4_for_branch_op ? `branch_ops__pc_w : 4'b0) | 
		(group_5_for_branch_op ? `branch_ops__tpc_w : 4'b0) | 
		(group_6_for_branch_op ? `branch_ops__cb_ne : 4'b0) | 
		(group_7_for_branch_op ? `branch_ops__cb_lts : 4'b0) | 
		(group_8_for_branch_op ? `branch_ops__cb_ges : 4'b0) | 
		(group_9_for_branch_op ? `branch_ops__cb_lt : 4'b0) | 
		(group_10_for_branch_op ? `branch_ops__cb_ge : 4'b0) | 
		(group_11_for_branch_op ? `branch_ops__bb_one : 4'b0) | 
		(group_12_for_branch_op ? `branch_ops__bb_zero : 4'b0) ;
	always_ff @(posedge clk) output_port_branch_op <= rst ? 4'h0 : register_outputs ? branch_op : output_port_branch_op;
	assign ldst_op = (group_1_for_ldst_op ? `ldst_ops__store : 1'b0) | (group_2_for_ldst_op ? `ldst_ops__load : 1'b0) ;
	always_ff @(posedge clk) output_port_ldst_op <= rst ? 1'h0 : register_outputs ? ldst_op : output_port_ldst_op;
	assign use_reg_a = (group_1_for_use_reg_a ? 1'h1 : 1'b0) | (group_1_for_use_reg_a ? 1'b0 : 1'h0);
	assign op_a = 
		(group_1_for_op_a ? field_e : 32'b0) | 
		(group_2_for_op_a ? fetch_inst_0[15:12] : 32'b0) | 
		(group_3_for_op_a ? 3'h7 : 32'b0) | 
		(group_4_for_op_a ? 1'h0 : 32'b0) | 
		(group_5_for_op_a ? 32'hffffffff : 32'b0) ;
	always_ff @(posedge clk) u1795_output_port <= rst ? 1'h0 : register_outputs ? use_reg_a : u1795_output_port;
	always_ff @(posedge clk) u1796_output_port <= rst ? 32'h0 : register_outputs ? op_a : u1796_output_port;
	assign output_port_op_a = u1795_output_port ? reg_file_rsp_read1_data : u1796_output_port;
	assign use_reg_b = (group_1_for_use_reg_b ? 1'h1 : 1'b0) | (group_1_for_use_reg_b ? 1'b0 : 1'h0);
	assign op_b = 
		(group_1_for_op_b ? field_e : 32'b0) | 
		(group_2_for_op_b ? 1'h0 : 32'b0) | 
		(group_3_for_op_b ? ones_field_a : 32'b0) | 
		(group_4_for_op_b ? fetch_inst_0[11:8] : 32'b0) ;
	always_ff @(posedge clk) u1798_output_port <= rst ? 1'h0 : register_outputs ? use_reg_b : u1798_output_port;
	always_ff @(posedge clk) u1799_output_port <= rst ? 32'h0 : register_outputs ? op_b : u1799_output_port;
	assign output_port_op_b = u1798_output_port ? reg_file_rsp_read2_data : u1799_output_port;
	assign op_c = (group_1_for_op_c ? 1'h0 : 32'b0) | (group_2_for_op_c ? field_e : 32'b0) | (group_3_for_op_c ? tiny_ofs : 32'b0) ;
	always_ff @(posedge clk) output_port_op_c <= rst ? 32'h0 : register_outputs ? op_c : output_port_op_c;
	assign mem_len = (group_1_for_mem_len ? 2'h2 : 2'b0) | (group_2_for_mem_len ? 1'h0 : 2'b0) | (group_3_for_mem_len ? 1'h1 : 2'b0) ;
	always_ff @(posedge clk) u1802_output_port <= rst ? 2'h0 : register_outputs ? mem_len : u1802_output_port;
	always_ff @(posedge clk) output_port_inst_len <= rst ? 2'h0 : register_outputs ? fetch_inst_len : output_port_inst_len;
	assign bse = (group_1_for_bse ? 1'h1 : 1'b0) | (group_1_for_bse ? 1'b0 : 1'h0);
	always_ff @(posedge clk) output_port_do_bse <= rst ? 1'h0 : register_outputs ? bse : output_port_do_bse;
	assign wse = (group_1_for_wse ? 1'h1 : 1'b0) | (group_1_for_wse ? 1'b0 : 1'h0);
	always_ff @(posedge clk) output_port_do_wse <= rst ? 1'h0 : register_outputs ? wse : output_port_do_wse;
	assign bze = (group_1_for_bze ? 1'h1 : 1'b0) | (group_1_for_bze ? 1'b0 : 1'h0);
	always_ff @(posedge clk) output_port_do_bze <= rst ? 1'h0 : register_outputs ? bze : output_port_do_bze;
	assign wze = (group_1_for_wze ? 1'h1 : 1'b0) | (group_1_for_wze ? 1'b0 : 1'h0);
	always_ff @(posedge clk) output_port_do_wze <= rst ? 1'h0 : register_outputs ? wze : output_port_do_wze;
	always_ff @(posedge clk) output_port_result_reg_addr <= rst ? 4'h0 : register_outputs ? res_addr : output_port_result_reg_addr;
	always_ff @(posedge clk) output_port_result_reg_addr_valid <= rst ? 1'h0 : register_outputs ? rsv_needed : output_port_result_reg_addr_valid;
	always_ff @(posedge clk) output_port_fetch_av <= rst ? 1'h0 : register_outputs ? fetch_av : output_port_fetch_av;
	assign output_port_valid = reg_file_rsp_valid;
	assign reg_file_rsp_ready = output_port_ready;
	assign fetch_ready = reg_file_req_ready;
	assign output_port_mem_access_len = u1802_output_port;

	assign u40_output_port = fetch_inst_0[3:0] + 1'h1 + 5'b0;
	assign mask_for_sii_29 = mask_expr;
	assign expr = mask_expr;
	assign u22_output_port = fetch_inst_0[3:0];
endmodule


////////////////////////////////////////////////////////////////////////////////
// FetchStage
////////////////////////////////////////////////////////////////////////////////
module FetchStage (
	input logic clk,
	input logic rst,
	output logic [30:0] bus_if_request_addr,
	output logic [1:0] bus_if_request_byte_en,
	output logic [15:0] bus_if_request_data,
	output logic bus_if_request_read_not_write,
	input logic bus_if_request_ready,
	output logic bus_if_request_valid,

	input logic [15:0] bus_if_response_data,
	input logic bus_if_response_valid,

	output logic decode_av,
	output logic [15:0] decode_inst_0,
	output logic [15:0] decode_inst_1,
	output logic [15:0] decode_inst_2,
	output logic [1:0] decode_inst_len,
	input logic decode_ready,
	output logic decode_valid,

	input logic [21:0] mem_base,
	input logic [21:0] mem_limit,
	input logic [30:0] spc,
	input logic [30:0] tpc,
	input logic task_mode,
	input logic do_branch
);

	logic inst_buf_queue_av;
	logic inst_buf_queue_valid;
	logic [15:0] inst_buf_queue_data;
	logic [4:0] inst_buf_queue_free_cnt;
	logic inst_buf_queue_ready;
	logic inst_queue_assemble_valid;
	logic inst_queue_assemble_av;
	logic [15:0] inst_queue_assemble_data;
	logic inst_queue_assemble_ready;

	InstBuffer inst_buf (
		.clk(clk),
		.rst(rst),
		.bus_if_request_addr(bus_if_request_addr),
		.bus_if_request_byte_en(bus_if_request_byte_en),
		.bus_if_request_data(bus_if_request_data),
		.bus_if_request_read_not_write(bus_if_request_read_not_write),
		.bus_if_request_ready(bus_if_request_ready),
		.bus_if_request_valid(bus_if_request_valid),

		.bus_if_response_data(bus_if_response_data),
		.bus_if_response_valid(bus_if_response_valid),

		.queue_av(inst_buf_queue_av),
		.queue_data(inst_buf_queue_data),
		.queue_ready(inst_buf_queue_ready),
		.queue_valid(inst_buf_queue_valid),

		.queue_free_cnt(inst_buf_queue_free_cnt),
		.mem_base(mem_base),
		.mem_limit(mem_limit),
		.spc(spc),
		.tpc(tpc),
		.task_mode(task_mode),
		.do_branch(do_branch)
	);

	InstQueue inst_queue (
		.clk(clk),
		.rst(rst),
		.inst_av(inst_buf_queue_av),
		.inst_data(inst_buf_queue_data),
		.inst_ready(inst_buf_queue_ready),
		.inst_valid(inst_buf_queue_valid),

		.queue_free_cnt(inst_buf_queue_free_cnt),
		.assemble_av(inst_queue_assemble_av),
		.assemble_data(inst_queue_assemble_data),
		.assemble_ready(inst_queue_assemble_ready),
		.assemble_valid(inst_queue_assemble_valid),

		.do_branch(do_branch)
	);

	InstAssemble inst_assemble (
		.clk(clk),
		.rst(rst),
		.inst_buf_av(inst_queue_assemble_av),
		.inst_buf_data(inst_queue_assemble_data),
		.inst_buf_ready(inst_queue_assemble_ready),
		.inst_buf_valid(inst_queue_assemble_valid),

		.decode_av(decode_av),
		.decode_inst_0(decode_inst_0),
		.decode_inst_1(decode_inst_1),
		.decode_inst_2(decode_inst_2),
		.decode_inst_len(decode_inst_len),
		.decode_ready(decode_ready),
		.decode_valid(decode_valid),

		.do_branch(do_branch)
	);

endmodule


////////////////////////////////////////////////////////////////////////////////
// InstAssemble
////////////////////////////////////////////////////////////////////////////////
module InstAssemble (
	input logic clk,
	input logic rst,
	input logic inst_buf_av,
	input logic [15:0] inst_buf_data,
	output logic inst_buf_ready,
	input logic inst_buf_valid,

	output logic decode_av,
	output logic [15:0] decode_inst_0,
	output logic [15:0] decode_inst_1,
	output logic [15:0] decode_inst_2,
	output logic [1:0] decode_inst_len,
	input logic decode_ready,
	output logic decode_valid,

	input logic do_branch
);

	logic u5_output_port;
	logic u12_output_port;
	logic u19_output_port;
	logic u26_output_port;
	logic u29_output_port;
	logic u31_output_port;
	logic u34_output_port;
	logic u38_output_port;
	logic u41_output_port;
	logic u44_output_port;
	logic u48_output_port;
	logic u56_output_port;
	logic u64_output_port;
	logic u72_output_port;
	logic u76_output_port;
	logic u79_output_port;
	logic terminal_fsm_state;
	logic fetch_ready;
	logic fsm_advance;
	logic fetch_av;
	logic [15:0] inst_reg_0;
	logic [15:0] inst_reg_1;
	logic [15:0] inst_reg_2;
	logic [1:0] inst_len_reg;
	logic [1:0] inst_len;
	logic [1:0] fsm_state;
	logic [1:0] decode_fsm_next_state;

	assign terminal_fsm_state = fsm_state == `InstAssembleStates__have_all_fragments;
	assign fetch_ready =  ~ terminal_fsm_state | decode_ready | do_branch;
	assign decode_valid = terminal_fsm_state &  ~ do_branch;
	assign fsm_advance =  ~ terminal_fsm_state & inst_buf_valid & fetch_ready | terminal_fsm_state & decode_ready;
	always_ff @(posedge clk) fetch_av <= rst ? 1'h0 : fsm_advance ? (fsm_state == `InstAssembleStates__have_0_fragments | fsm_state == `InstAssembleStates__have_all_fragments) ? inst_buf_av : fetch_av : fetch_av;
	always_ff @(posedge clk) inst_reg_0 <= rst ? 16'h0 : fsm_advance ? (fsm_state == `InstAssembleStates__have_0_fragments | fsm_state == `InstAssembleStates__have_all_fragments) ? inst_buf_data : inst_reg_0 : inst_reg_0;
	always_ff @(posedge clk) inst_reg_1 <= rst ? 16'h0 : fsm_advance ? (fsm_state == `InstAssembleStates__need_1_fragments & inst_len_reg == 1'h1 | fsm_state == `InstAssembleStates__need_2_fragments) ? inst_buf_data : inst_reg_1 : inst_reg_1;
	always_ff @(posedge clk) inst_reg_2 <= rst ? 16'h0 : fsm_advance ? inst_buf_data : inst_reg_2;
	always_ff @(posedge clk) inst_len_reg <= rst ? 2'h0 : fsm_advance ? (fsm_state == `InstAssembleStates__have_0_fragments | fsm_state == `InstAssembleStates__have_all_fragments) ? inst_len : inst_len_reg : inst_len_reg;

	FSM_3 decode_fsm (
		.clock_port(clk),
		.reset_port(rst),
		.reset_value(`InstAssembleStates__have_0_fragments),
		.state(fsm_state),
		.next_state(decode_fsm_next_state),
		.default_state(`InstAssembleStates__have_0_fragments),
		.input_have_0_fragments_to_have_all_fragments(u5_output_port),
		.input_have_0_fragments_to_have_all_fragments_1(u12_output_port),
		.input_have_0_fragments_to_need_1_fragments(u19_output_port),
		.input_have_0_fragments_to_need_2_fragments(u26_output_port),
		.input_have_0_fragments_to_have_0_fragments(u29_output_port),
		.input_have_0_fragments_to_have_0_fragments_1(do_branch),
		.input_need_1_fragments_to_have_all_fragments(u31_output_port),
		.input_need_1_fragments_to_need_1_fragments(u34_output_port),
		.input_need_1_fragments_to_have_0_fragments(do_branch),
		.input_need_2_fragments_to_need_1_fragments(u38_output_port),
		.input_need_2_fragments_to_have_all_fragments(u41_output_port),
		.input_need_2_fragments_to_need_2_fragments(u44_output_port),
		.input_need_2_fragments_to_have_0_fragments(do_branch),
		.input_have_all_fragments_to_have_all_fragments(u48_output_port),
		.input_have_all_fragments_to_have_all_fragments_1(u56_output_port),
		.input_have_all_fragments_to_need_1_fragments(u64_output_port),
		.input_have_all_fragments_to_need_2_fragments(u72_output_port),
		.input_have_all_fragments_to_have_0_fragments(u76_output_port),
		.input_have_all_fragments_to_have_all_fragments_2(u79_output_port),
		.input_have_all_fragments_to_have_0_fragments_1(do_branch)
	);

	DecoratorModule_5 u (
		.output_port(inst_len),
		.inst_word(inst_buf_data)
	);

	assign u5_output_port =  ~ do_branch & fsm_advance & inst_buf_av;
	assign u12_output_port =  ~ do_branch & fsm_advance &  ~ inst_buf_av & inst_len == 1'h0;
	assign u19_output_port =  ~ do_branch & fsm_advance &  ~ inst_buf_av & inst_len == 1'h1;
	assign u26_output_port =  ~ do_branch & fsm_advance &  ~ inst_buf_av & inst_len == 2'h2;
	assign u29_output_port =  ~ do_branch &  ~ fsm_advance;
	assign u31_output_port =  ~ do_branch & fsm_advance;
	assign u34_output_port =  ~ do_branch &  ~ fsm_advance;
	assign u38_output_port =  ~ do_branch & fsm_advance &  ~ inst_buf_av;
	assign u41_output_port =  ~ do_branch & fsm_advance & inst_buf_av;
	assign u44_output_port =  ~ do_branch &  ~ fsm_advance;
	assign u48_output_port =  ~ do_branch & fsm_advance & inst_buf_valid & inst_buf_av;
	assign u56_output_port =  ~ do_branch & fsm_advance & inst_buf_valid &  ~ inst_buf_av & inst_len == 1'h0;
	assign u64_output_port =  ~ do_branch & fsm_advance & inst_buf_valid &  ~ inst_buf_av & inst_len == 1'h1;
	assign u72_output_port =  ~ do_branch & fsm_advance & inst_buf_valid &  ~ inst_buf_av & inst_len == 2'h2;
	assign u76_output_port =  ~ do_branch & fsm_advance &  ~ inst_buf_valid;
	assign u79_output_port =  ~ do_branch &  ~ fsm_advance;
	assign inst_buf_ready = fetch_ready;
	assign decode_av = fetch_av;
	assign decode_inst_0 = inst_reg_0;
	assign decode_inst_1 = inst_reg_1;
	assign decode_inst_2 = inst_reg_2;
	assign decode_inst_len = inst_len_reg;
endmodule


////////////////////////////////////////////////////////////////////////////////
// DecoratorModule_7
////////////////////////////////////////////////////////////////////////////////
module DecoratorModule_7 (
	output logic output_port,
	input logic [31:0] word,
	input logic [31:0] bit_code
);

	assign output_port = 
		(bit_code == 1'h0 ? word[0] : 1'b0) | 
		(bit_code == 1'h1 ? word[1] : 1'b0) | 
		(bit_code == 2'h2 ? word[2] : 1'b0) | 
		(bit_code == 2'h3 ? word[3] : 1'b0) | 
		(bit_code == 3'h4 ? word[4] : 1'b0) | 
		(bit_code == 3'h5 ? word[5] : 1'b0) | 
		(bit_code == 3'h6 ? word[6] : 1'b0) | 
		(bit_code == 3'h7 ? word[7] : 1'b0) | 
		(bit_code == 4'h8 ? word[8] : 1'b0) | 
		(bit_code == 4'h9 ? word[9] : 1'b0) | 
		(bit_code == 4'ha ? word[14] : 1'b0) | 
		(bit_code == 4'hb ? word[15] : 1'b0) | 
		(bit_code == 4'hc ? word[16] : 1'b0) | 
		(bit_code == 4'hd ? word[30] : 1'b0) | 
		(bit_code == 4'he ? word[31] : 1'b0) ;

endmodule


////////////////////////////////////////////////////////////////////////////////
// DecoratorModule_6
////////////////////////////////////////////////////////////////////////////////
module DecoratorModule_6 (
	output logic output_port,
	input logic [31:0] word,
	input logic [31:0] bit_code
);

	assign output_port = 
		(bit_code == 1'h0 ? word[0] : 1'b0) | 
		(bit_code == 1'h1 ? word[1] : 1'b0) | 
		(bit_code == 2'h2 ? word[2] : 1'b0) | 
		(bit_code == 2'h3 ? word[3] : 1'b0) | 
		(bit_code == 3'h4 ? word[4] : 1'b0) | 
		(bit_code == 3'h5 ? word[5] : 1'b0) | 
		(bit_code == 3'h6 ? word[6] : 1'b0) | 
		(bit_code == 3'h7 ? word[7] : 1'b0) | 
		(bit_code == 4'h8 ? word[8] : 1'b0) | 
		(bit_code == 4'h9 ? word[9] : 1'b0) | 
		(bit_code == 4'ha ? word[14] : 1'b0) | 
		(bit_code == 4'hb ? word[15] : 1'b0) | 
		(bit_code == 4'hc ? word[16] : 1'b0) | 
		(bit_code == 4'hd ? word[30] : 1'b0) | 
		(bit_code == 4'he ? word[31] : 1'b0) ;

endmodule


////////////////////////////////////////////////////////////////////////////////
// DecoratorModule_5
////////////////////////////////////////////////////////////////////////////////
module DecoratorModule_5 (
	output logic [1:0] output_port,
	input logic [15:0] inst_word
);

	logic [3:0] u_output_port;
	logic [3:0] u3_output_port;
	logic [3:0] u6_output_port;
	logic [3:0] u9_output_port;
	logic [3:0] u15_output_port;
	logic [3:0] u18_output_port;
	logic [3:0] u23_output_port;
	logic [3:0] u26_output_port;
	logic [3:0] u29_output_port;
	logic [3:0] u35_output_port;
	logic [3:0] u38_output_port;

	assign output_port = {(u_output_port == 4'hf | u3_output_port == 4'hf & (u6_output_port != 4'hf | u9_output_port == 4'hf) | u15_output_port == 4'he & u18_output_port == 4'hf | u23_output_port < 4'hc & (u26_output_port == 4'hf | u29_output_port == 4'hf)) &  ~ (u35_output_port == 4'hf | u38_output_port != 4'hf), (u_output_port == 4'hf | u3_output_port == 4'hf & (u6_output_port != 4'hf | u9_output_port == 4'hf) | u15_output_port == 4'he & u18_output_port == 4'hf | u23_output_port < 4'hc & (u26_output_port == 4'hf | u29_output_port == 4'hf)) & (u35_output_port == 4'hf | u38_output_port != 4'hf)};

	DecoratorModule u (
		.output_port(u_output_port),
		.inst_word(inst_word)
	);

	DecoratorModule_2 u3 (
		.output_port(u3_output_port),
		.inst_word(inst_word)
	);

	DecoratorModule_3 u6 (
		.output_port(u6_output_port),
		.inst_word(inst_word)
	);

	DecoratorModule_4 u9 (
		.output_port(u9_output_port),
		.inst_word(inst_word)
	);

	DecoratorModule_2 u15 (
		.output_port(u15_output_port),
		.inst_word(inst_word)
	);

	DecoratorModule_4 u18 (
		.output_port(u18_output_port),
		.inst_word(inst_word)
	);

	DecoratorModule_2 u23 (
		.output_port(u23_output_port),
		.inst_word(inst_word)
	);

	DecoratorModule_3 u26 (
		.output_port(u26_output_port),
		.inst_word(inst_word)
	);

	DecoratorModule_4 u29 (
		.output_port(u29_output_port),
		.inst_word(inst_word)
	);

	DecoratorModule u35 (
		.output_port(u35_output_port),
		.inst_word(inst_word)
	);

	DecoratorModule_4 u38 (
		.output_port(u38_output_port),
		.inst_word(inst_word)
	);

endmodule


////////////////////////////////////////////////////////////////////////////////
// DecoratorModule_4
////////////////////////////////////////////////////////////////////////////////
module DecoratorModule_4 (
	output logic [3:0] output_port,
	input logic [15:0] inst_word
);

	assign output_port = inst_word[3:0];

endmodule


////////////////////////////////////////////////////////////////////////////////
// DecoratorModule_3
////////////////////////////////////////////////////////////////////////////////
module DecoratorModule_3 (
	output logic [3:0] output_port,
	input logic [15:0] inst_word
);

	assign output_port = inst_word[7:4];

endmodule


////////////////////////////////////////////////////////////////////////////////
// DecoratorModule_2
////////////////////////////////////////////////////////////////////////////////
module DecoratorModule_2 (
	output logic [3:0] output_port,
	input logic [15:0] inst_word
);

	assign output_port = inst_word[11:8];

endmodule


////////////////////////////////////////////////////////////////////////////////
// DecoratorModule
////////////////////////////////////////////////////////////////////////////////
module DecoratorModule (
	output logic [3:0] output_port,
	input logic [15:0] inst_word
);

	assign output_port = inst_word[15:12];

endmodule


////////////////////////////////////////////////////////////////////////////////
// InstQueue
////////////////////////////////////////////////////////////////////////////////
module InstQueue (
	input logic clk,
	input logic rst,
	input logic inst_av,
	input logic [15:0] inst_data,
	output logic inst_ready,
	input logic inst_valid,

	output logic [4:0] queue_free_cnt,
	output logic assemble_av,
	output logic [15:0] assemble_data,
	input logic assemble_ready,
	output logic assemble_valid,

	input logic do_branch
);

	logic dec;
	logic inc;
	logic signed [6:0] u3_output_port;
	logic [4:0] empty_cnt;

	assign inc = assemble_ready & assemble_valid;
	assign dec = inst_ready & inst_valid;
	always_ff @(posedge clk) empty_cnt <= rst ? 5'h10 : do_branch ? 5'h10 : u3_output_port[4:0];
	initial empty_cnt <= 5'h10;

	Fifo fifo (
		.input_port_av(inst_av),
		.input_port_data(inst_data),
		.input_port_ready(inst_ready),
		.input_port_valid(inst_valid),

		.output_port_av(assemble_av),
		.output_port_data(assemble_data),
		.output_port_ready(assemble_ready),
		.output_port_valid(assemble_valid),

		.clock_port(clk),
		.reset_port(rst),
		.clear(do_branch)
	);

	assign u3_output_port = empty_cnt + inc + 6'b0 - dec + 7'b0;
	assign queue_free_cnt = empty_cnt;
endmodule


////////////////////////////////////////////////////////////////////////////////
// Fifo
////////////////////////////////////////////////////////////////////////////////
module Fifo (
	input logic input_port_av,
	input logic [15:0] input_port_data,
	output logic input_port_ready,
	input logic input_port_valid,

	output logic output_port_av,
	output logic [15:0] output_port_data,
	input logic output_port_ready,
	output logic output_port_valid,

	input logic clock_port,
	input logic reset_port,
	input logic clear
);

	logic input_data_av;
	logic [15:0] input_data_data;
	logic push;
	logic pop;
	logic push_will_wrap;
	logic pop_will_wrap;
	logic [3:0] next_push_addr;
	logic [3:0] next_pop_addr;
	logic next_looped;
	logic next_empty_or_full;
	logic next_empty;
	logic next_full;
	logic [3:0] push_addr;
	logic [3:0] pop_addr;
	logic empty;
	logic full;
	logic looped;
	logic u93_output_port;
	logic out_data_selector;
	logic u95_output_port_av;
	logic [15:0] u95_output_port_data;
	logic output_data_av;
	logic [15:0] output_data_data;
	logic buffer_mem_port2_data_out_av;
	logic [15:0] buffer_mem_port2_data_out_data;

	assign input_port_ready =  ~ full;
	assign output_port_valid =  ~ empty;
	assign push_will_wrap = push_addr == 4'hf;
	assign push =  ~ full & input_port_valid;
	assign next_push_addr = push ? 4'(push_will_wrap ? 1'h0 : push_addr + 1'h1 + 5'b0) : push_addr;
	assign pop_will_wrap = pop_addr == 4'hf;
	assign pop =  ~ empty & output_port_ready;
	assign next_pop_addr = pop ? 4'(pop_will_wrap ? 1'h0 : pop_addr + 1'h1 + 5'b0) : pop_addr;
	assign next_looped = 
		(push != 1'h1 & pop != 1'h1 ? looped : 1'b0) | 
		(push == 1'h1 & pop != 1'h1 ? push_will_wrap ? 1'h1 : looped : 1'b0) | 
		(push != 1'h1 & pop == 1'h1 ? pop_will_wrap ? 1'h0 : looped : 1'b0) | 
		(push == 1'h1 & pop == 1'h1 ? 
		(push_will_wrap != 1'h1 & pop_will_wrap != 1'h1 ? looped : 1'b0) | 
		(push_will_wrap == 1'h1 & pop_will_wrap != 1'h1 ? 1'h1 : 1'b0) | 
		(push_will_wrap != 1'h1 & pop_will_wrap == 1'h1 ? 1'h0 : 1'b0) | 
		(push_will_wrap == 1'h1 & pop_will_wrap == 1'h1 ? looped : 1'b0)  : 1'b0) ;
	assign next_empty_or_full = next_push_addr == next_pop_addr;
	assign next_empty = next_empty_or_full ?  ~ next_looped : 1'h0;
	assign next_full = next_empty_or_full ? next_looped : 1'h0;
	always_ff @(posedge clock_port) push_addr <= reset_port ? 4'h0 : clear ? 1'h0 : next_push_addr;
	always_ff @(posedge clock_port) pop_addr <= reset_port ? 4'h0 : clear ? 1'h0 : next_pop_addr;
	always_ff @(posedge clock_port) empty <= reset_port ? 1'h1 : clear ? 1'h1 : next_empty;
	initial empty <= 1'h1;
	always_ff @(posedge clock_port) full <= reset_port ? 1'h0 : clear ? 1'h0 : next_full;
	always_ff @(posedge clock_port) looped <= reset_port ? 1'h0 : clear ? 1'h0 : next_looped;
	always_ff @(posedge clock_port) u93_output_port <= reset_port ? 1'h0 : push;
	assign out_data_selector = push_addr == next_pop_addr & u93_output_port;
	always_ff @(posedge clock_port) u95_output_port_av <= reset_port ? 1'h0 : input_port_av;
	always_ff @(posedge clock_port) u95_output_port_data <= reset_port ? 16'h0 : input_port_data;
	assign output_data_av = out_data_selector ? u95_output_port_av : buffer_mem_port2_data_out_av;
	assign output_data_data = out_data_selector ? u95_output_port_data : buffer_mem_port2_data_out_data;

	Memory buffer_mem (
		.port1_addr(push_addr),
		.port1_clk(clock_port),
		.port2_addr(next_pop_addr),
		.port2_clk(clock_port),
		.port1_data_in_av(input_port_av),
		.port1_data_in_data(input_port_data),

		.port1_write_en(push),
		.port2_data_out_av(buffer_mem_port2_data_out_av),
		.port2_data_out_data(buffer_mem_port2_data_out_data)
	);

	assign input_data_av = input_port_av;
	assign input_data_data = input_port_data;
	assign output_port_av = output_data_av;
	assign output_port_data = output_data_data;
endmodule


////////////////////////////////////////////////////////////////////////////////
// Memory_4
////////////////////////////////////////////////////////////////////////////////
module Memory_4 (
	input logic [12:0] addr,
	input logic clk,
	input logic [7:0] data_in,
	output logic [7:0] data_out,
	input logic write_en
);

	logic [7:0] mem [0:8191];
	initial begin
		$readmemh("q_fpga_top/rom.rom_mef", mem);
	end

	always @(posedge clk) begin
		if (write_en) begin
			mem[addr] <= data_in;
		end
		data_out <= mem[addr];
	end

endmodule


////////////////////////////////////////////////////////////////////////////////
// Memory_3
////////////////////////////////////////////////////////////////////////////////
module Memory_3 (
	input logic [15:0] addr,
	input logic clk,
	input logic [7:0] data_in,
	output logic [7:0] data_out,
	input logic write_en
);

	logic [7:0] mem [0:65535];
	initial begin
		$readmemh("q_fpga_top/blinky.dram1_mef", mem);
	end

	logic [15:0] addr_reg;
	always @(posedge clk) begin
		if (write_en) begin
			mem[addr] <= data_in;
		end
		addr_reg <= addr;
	end
	assign data_out = mem[addr_reg];

endmodule


////////////////////////////////////////////////////////////////////////////////
// Memory_2
////////////////////////////////////////////////////////////////////////////////
module Memory_2 (
	input logic [15:0] addr,
	input logic clk,
	input logic [7:0] data_in,
	output logic [7:0] data_out,
	input logic write_en
);

	logic [7:0] mem [0:65535];
	initial begin
		$readmemh("q_fpga_top/blinky.dram0_mef", mem);
	end

	logic [15:0] addr_reg;
	always @(posedge clk) begin
		if (write_en) begin
			mem[addr] <= data_in;
		end
		addr_reg <= addr;
	end
	assign data_out = mem[addr_reg];

endmodule


////////////////////////////////////////////////////////////////////////////////
// Memory
////////////////////////////////////////////////////////////////////////////////
module Memory (
	input logic [3:0] port1_addr,
	input logic port1_clk,
	input logic [3:0] port2_addr,
	input logic port2_clk,
	input logic port1_data_in_av,
	input logic [15:0] port1_data_in_data,

	input logic port1_write_en,
	output logic port2_data_out_av,
	output logic [15:0] port2_data_out_data
);

	logic [16:0] real_mem_port2_data_out;

	reg [16:0] mem [0:15];

	always @(posedge port1_clk) begin
		if (port1_write_en) begin
			mem[port1_addr] <= {port1_data_in_av, port1_data_in_data};
		end
	end

	always @(posedge port1_clk) begin
		real_mem_port2_data_out <= mem[port2_addr];
	end

	assign {port2_data_out_av, port2_data_out_data} = real_mem_port2_data_out;

endmodule


////////////////////////////////////////////////////////////////////////////////
// InstBuffer
////////////////////////////////////////////////////////////////////////////////
module InstBuffer (
	input logic clk,
	input logic rst,
	output logic [30:0] bus_if_request_addr,
	output logic [1:0] bus_if_request_byte_en,
	output logic [15:0] bus_if_request_data,
	output logic bus_if_request_read_not_write,
	input logic bus_if_request_ready,
	output logic bus_if_request_valid,

	input logic [15:0] bus_if_response_data,
	input logic bus_if_response_valid,

	output logic queue_av,
	output logic [15:0] queue_data,
	input logic queue_ready,
	output logic queue_valid,

	input logic [4:0] queue_free_cnt,
	input logic [21:0] mem_base,
	input logic [21:0] mem_limit,
	input logic [30:0] spc,
	input logic [30:0] tpc,
	input logic task_mode,
	input logic do_branch
);

	logic branch_req;
	logic advance_request;
	logic [32:0] u3_output_port;
	logic [30:0] branch_target;
	logic task_mode_fetch;
	logic [31:0] u8_output_port;
	logic [30:0] fetch_addr;
	logic fetch_page_limit;
	logic fetch_av;
	logic [2:0] u29_output_port;
	logic signed [2:0] u33_output_port;
	logic [1:0] next_outstanding_request;
	logic [1:0] outstanding_request;
	logic start_new_request;
	logic signed [5:0] u68_output_port;
	logic [4:0] req_len;
	logic req_av;
	logic u91_output_port;
	logic u97_output_port;
	logic u100_output_port;
	logic u103_output_port;
	logic u104_output_port;
	logic [1:0] state;
	logic [1:0] next_state;

	assign branch_target = task_mode ? u3_output_port[30:0] : spc;
	always_ff @(posedge clk) task_mode_fetch <= rst ? 1'h0 : do_branch ? task_mode : task_mode_fetch;
	assign advance_request = bus_if_request_valid & bus_if_request_ready;
	always_ff @(posedge clk) fetch_addr <= rst ? 31'h0 : do_branch ? branch_target : u8_output_port[30:0];
	always_ff @(posedge clk) fetch_page_limit <= rst ? 1'h0 : state == `InstBufferStates__idle ? 1'h0 :  ~ fetch_addr[6:0] == 1'h0;
	assign next_outstanding_request = 
		(advance_request & bus_if_response_valid ? outstanding_request : 2'b0) | 
		(advance_request &  ~ bus_if_response_valid ? u29_output_port[1:0] : 2'b0) | 
		( ~ advance_request & bus_if_response_valid ? u33_output_port[1:0] : 2'b0) | 
		( ~ advance_request &  ~ bus_if_response_valid ? outstanding_request : 2'b0) ;
	always_ff @(posedge clk) outstanding_request <= rst ? 2'h0 : next_outstanding_request;
	assign start_new_request = (queue_free_cnt >= 4'h8 &  ~ do_branch | do_branch & next_outstanding_request == 1'h0) & state == `InstBufferStates__idle | state == `InstBufferStates__flushing & next_outstanding_request == 1'h0 | state == `InstBufferStates__request & do_branch & next_outstanding_request == 1'h0;
	always_ff @(posedge clk) req_len <= rst ? 4'h8 : start_new_request ? do_branch ? 4'h8 : queue_free_cnt : advance_request ? req_len > 1'h0 ? u68_output_port[4:0] : 1'h0 : req_len;
	initial req_len <= 4'h8;
	assign fetch_av = task_mode_fetch & fetch_addr[30:10] > mem_limit;
	always_ff @(posedge clk) req_av <= rst ? 1'h0 : start_new_request ? fetch_av : req_av;
	assign bus_if_request_valid = state == `InstBufferStates__request &  ~ fetch_page_limit;
	assign bus_if_request_addr = fetch_addr[30:0];
	assign queue_valid = bus_if_response_valid & state != `InstBufferStates__flushing;
	assign bus_if_request_byte_en = 2'h3;
	assign bus_if_request_data = 16'hx;
	assign bus_if_request_read_not_write = 1'h1;
	assign queue_data = bus_if_response_data;

	FSM_2 fsm (
		.clock_port(clk),
		.reset_port(rst),
		.reset_value(`InstBufferStates__idle),
		.state(state),
		.next_state(next_state),
		.default_state(`InstBufferStates__idle),
		.input_idle_to_request(start_new_request),
		.input_idle_to_flushing(u91_output_port),
		.input_request_to_idle(u97_output_port),
		.input_request_to_flushing(u100_output_port),
		.input_request_to_request(u103_output_port),
		.input_flushing_to_request(u104_output_port)
	);

	assign branch_req = do_branch;
	assign u3_output_port = tpc + (mem_base << 4'ha) + 32'b0 + 33'b0;
	assign u8_output_port = fetch_addr + advance_request + 32'b0;
	assign u29_output_port = outstanding_request + 1'h1 + 3'b0;
	assign u33_output_port = outstanding_request - 1'h1 + 3'b0;
	assign u68_output_port = req_len - 1'h1 + 6'b0;
	assign queue_av = req_av;
	assign u91_output_port = do_branch & next_outstanding_request != 1'h0;
	assign u97_output_port =  ~ do_branch & ( ~ bus_if_request_valid | req_len == 1'h0);
	assign u100_output_port = do_branch & next_outstanding_request != 1'h0;
	assign u103_output_port = do_branch & next_outstanding_request == 1'h0;
	assign u104_output_port = next_outstanding_request == 1'h0;
endmodule


////////////////////////////////////////////////////////////////////////////////
// CpuDma
////////////////////////////////////////////////////////////////////////////////
module CpuDma (
	input logic clk,
	input logic rst,
	output logic [30:0] bus_req_if_addr,
	output logic [1:0] bus_req_if_byte_en,
	output logic bus_req_if_is_master,
	output logic [3:0] bus_req_if_one_hot_channel,
	output logic bus_req_if_read_not_write,
	input logic bus_req_if_ready,
	output logic bus_req_if_terminal_count,
	output logic bus_req_if_valid,

	input logic bus_rsp_if_valid,
	input logic [3:0] reg_if_paddr,
	input logic reg_if_penable,
	output logic [31:0] reg_if_prdata,
	output logic reg_if_pready,
	input logic reg_if_psel,
	input logic [31:0] reg_if_pwdata,
	input logic reg_if_pwrite,

	input logic [3:0] drq
);

	logic tc_reg;
	logic reg_write_strobe;
	logic [3:0] served_dma_channel;
	logic u7_output_port;
	logic u9_output_port;
	logic u13_output_port;
	logic u15_output_port;
	logic u19_output_port;
	logic u21_output_port;
	logic u25_output_port;
	logic u27_output_port;
	logic [3:0] prev_drq;
	logic ch_0_served;
	logic [31:0] ch_0_addr;
	logic [31:0] ch_0_limit;
	logic ch_0_single;
	logic ch_0_read_not_write;
	logic ch_0_is_master;
	logic ch_0_high_priority;
	logic ch_0_req_polarity;
	logic ch_0_req_no_cdc;
	logic ch_0_active;
	logic ch_0_int_pending;
	logic u103_output_port;
	logic ch_0_req_pending;
	logic ch_1_served;
	logic [31:0] ch_1_addr;
	logic [31:0] ch_1_limit;
	logic ch_1_single;
	logic ch_1_read_not_write;
	logic ch_1_is_master;
	logic ch_1_high_priority;
	logic ch_1_req_polarity;
	logic ch_1_req_no_cdc;
	logic ch_1_active;
	logic ch_1_int_pending;
	logic u178_output_port;
	logic ch_1_req_pending;
	logic ch_2_served;
	logic [31:0] ch_2_addr;
	logic [31:0] ch_2_limit;
	logic ch_2_single;
	logic ch_2_read_not_write;
	logic ch_2_is_master;
	logic ch_2_high_priority;
	logic ch_2_req_polarity;
	logic ch_2_req_no_cdc;
	logic ch_2_active;
	logic ch_2_int_pending;
	logic u253_output_port;
	logic ch_2_req_pending;
	logic ch_3_served;
	logic [31:0] ch_3_addr;
	logic [31:0] ch_3_limit;
	logic ch_3_single;
	logic ch_3_read_not_write;
	logic ch_3_is_master;
	logic ch_3_high_priority;
	logic ch_3_req_polarity;
	logic ch_3_req_no_cdc;
	logic ch_3_active;
	logic ch_3_int_pending;
	logic u328_output_port;
	logic ch_3_req_pending;
	logic member;
	logic [3:0] ch_read_not_writes;
	logic [31:0] u353_output_port;
	logic req_pendig;
	logic [3:0] high_pri_req_pending;
	logic [3:0] low_pri_req_pending;
	logic high_pri_selected;
	logic [3:0] selected_dma_channel;
	logic [31:0] selected_addr;
	logic [31:0] selected_limit;
	logic tc;
	logic [32:0] u390_output_port;
	logic [31:0] next_addr;
	logic [3:0] read_not_writes;
	logic u433_output_port;
	logic [3:0] high_pri_selected_dma_channel;
	logic u435_output_port;
	logic [3:0] low_pri_selected_dma_channel;
	logic [3:0] drq_1;
	logic priority_change;

	always_ff @(posedge clk) u7_output_port <= rst ? 1'h0 : drq[0];
	always_ff @(posedge clk) u9_output_port <= rst ? 1'h0 : u7_output_port;
	always_ff @(posedge clk) u13_output_port <= rst ? 1'h0 : drq[1];
	always_ff @(posedge clk) u15_output_port <= rst ? 1'h0 : u13_output_port;
	always_ff @(posedge clk) u19_output_port <= rst ? 1'h0 : drq[2];
	always_ff @(posedge clk) u21_output_port <= rst ? 1'h0 : u19_output_port;
	always_ff @(posedge clk) u25_output_port <= rst ? 1'h0 : drq[3];
	always_ff @(posedge clk) u27_output_port <= rst ? 1'h0 : u25_output_port;
	always_ff @(posedge clk) served_dma_channel <= rst ? 4'h0 : bus_req_if_ready & req_pendig ? selected_dma_channel : served_dma_channel;
	assign reg_write_strobe = reg_if_psel & reg_if_pwrite & reg_if_penable;
	assign ch_0_served = served_dma_channel[0] & bus_rsp_if_valid;
	always_ff @(posedge clk) ch_0_addr <= rst ? 32'h0 : (reg_if_paddr == 1'h0 & reg_write_strobe) ? reg_if_pwdata : ch_0_served ? next_addr : ch_0_addr;
	always_ff @(posedge clk) ch_0_limit <= rst ? 32'h0 : reg_if_paddr == 1'h1 & reg_write_strobe ? reg_if_pwdata : ch_0_limit;
	always_ff @(posedge clk) ch_0_single <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[0] : ch_0_single;
	always_ff @(posedge clk) ch_0_read_not_write <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[1] : ch_0_read_not_write;
	always_ff @(posedge clk) ch_0_is_master <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[2] : ch_0_is_master;
	always_ff @(posedge clk) ch_0_high_priority <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[3] : ch_0_high_priority;
	always_ff @(posedge clk) ch_0_req_polarity <= rst ? 1'h0 : reg_if_paddr == 4'hb & reg_write_strobe ? reg_if_pwdata[0] : ch_0_req_polarity;
	always_ff @(posedge clk) ch_0_req_no_cdc <= rst ? 1'h0 : reg_if_paddr == 4'hb & reg_write_strobe ? reg_if_pwdata[1] : ch_0_req_no_cdc;
	always_ff @(posedge clk) tc_reg <= rst ? 1'h0 : bus_req_if_ready & req_pendig ? tc : tc_reg;
	always_ff @(posedge clk) ch_0_active <= rst ? 1'h0 : (reg_if_paddr == 1'h0 & reg_write_strobe) ? 1'h1 : ch_0_served ?  ~ tc_reg : ch_0_active;
	always_ff @(posedge clk) ch_0_int_pending <= rst ? 1'h0 : (tc_reg & ch_0_served) ? 1'h1 : (reg_if_paddr == 4'h8 & reg_write_strobe & reg_if_pwdata[0]) ? 1'h0 : ch_0_int_pending;
	always_ff @(posedge clk) prev_drq <= rst ? 4'h0 : drq_1;
	always_ff @(posedge clk) u103_output_port <= rst ? 1'h0 : (drq_1[0] &  ~ prev_drq[0]) ? 1'h1 : ch_0_served ? 1'h0 : ch_0_req_pending;
	assign ch_0_req_pending = ch_0_active & ((ch_0_single &  ~ ch_0_is_master) ? drq_1[0] : u103_output_port);
	assign ch_1_served = served_dma_channel[1] & bus_rsp_if_valid;
	always_ff @(posedge clk) ch_1_addr <= rst ? 32'h0 : (reg_if_paddr == 2'h2 & reg_write_strobe) ? reg_if_pwdata : ch_1_served ? next_addr : ch_1_addr;
	always_ff @(posedge clk) ch_1_limit <= rst ? 32'h0 : reg_if_paddr == 2'h3 & reg_write_strobe ? reg_if_pwdata : ch_1_limit;
	always_ff @(posedge clk) ch_1_single <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[4] : ch_1_single;
	always_ff @(posedge clk) ch_1_read_not_write <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[5] : ch_1_read_not_write;
	always_ff @(posedge clk) ch_1_is_master <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[6] : ch_1_is_master;
	always_ff @(posedge clk) ch_1_high_priority <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[7] : ch_1_high_priority;
	always_ff @(posedge clk) ch_1_req_polarity <= rst ? 1'h0 : reg_if_paddr == 4'hb & reg_write_strobe ? reg_if_pwdata[4] : ch_1_req_polarity;
	always_ff @(posedge clk) ch_1_req_no_cdc <= rst ? 1'h0 : reg_if_paddr == 4'hb & reg_write_strobe ? reg_if_pwdata[5] : ch_1_req_no_cdc;
	always_ff @(posedge clk) ch_1_active <= rst ? 1'h0 : (reg_if_paddr == 2'h2 & reg_write_strobe) ? 1'h1 : ch_1_served ?  ~ tc_reg : ch_1_active;
	always_ff @(posedge clk) ch_1_int_pending <= rst ? 1'h0 : (tc_reg & ch_1_served) ? 1'h1 : (reg_if_paddr == 4'h8 & reg_write_strobe & reg_if_pwdata[1]) ? 1'h0 : ch_1_int_pending;
	always_ff @(posedge clk) u178_output_port <= rst ? 1'h0 : (drq_1[1] &  ~ prev_drq[1]) ? 1'h1 : ch_1_served ? 1'h0 : ch_1_req_pending;
	assign ch_1_req_pending = ch_1_active & ((ch_1_single &  ~ ch_1_is_master) ? drq_1[1] : u178_output_port);
	assign ch_2_served = served_dma_channel[2] & bus_rsp_if_valid;
	always_ff @(posedge clk) ch_2_addr <= rst ? 32'h0 : (reg_if_paddr == 3'h4 & reg_write_strobe) ? reg_if_pwdata : ch_2_served ? next_addr : ch_2_addr;
	always_ff @(posedge clk) ch_2_limit <= rst ? 32'h0 : reg_if_paddr == 3'h5 & reg_write_strobe ? reg_if_pwdata : ch_2_limit;
	always_ff @(posedge clk) ch_2_single <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[8] : ch_2_single;
	always_ff @(posedge clk) ch_2_read_not_write <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[9] : ch_2_read_not_write;
	always_ff @(posedge clk) ch_2_is_master <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[10] : ch_2_is_master;
	always_ff @(posedge clk) ch_2_high_priority <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[11] : ch_2_high_priority;
	always_ff @(posedge clk) ch_2_req_polarity <= rst ? 1'h0 : reg_if_paddr == 4'hb & reg_write_strobe ? reg_if_pwdata[8] : ch_2_req_polarity;
	always_ff @(posedge clk) ch_2_req_no_cdc <= rst ? 1'h0 : reg_if_paddr == 4'hb & reg_write_strobe ? reg_if_pwdata[9] : ch_2_req_no_cdc;
	always_ff @(posedge clk) ch_2_active <= rst ? 1'h0 : (reg_if_paddr == 3'h4 & reg_write_strobe) ? 1'h1 : ch_2_served ?  ~ tc_reg : ch_2_active;
	always_ff @(posedge clk) ch_2_int_pending <= rst ? 1'h0 : (tc_reg & ch_2_served) ? 1'h1 : (reg_if_paddr == 4'h8 & reg_write_strobe & reg_if_pwdata[2]) ? 1'h0 : ch_2_int_pending;
	always_ff @(posedge clk) u253_output_port <= rst ? 1'h0 : (drq_1[2] &  ~ prev_drq[2]) ? 1'h1 : ch_2_served ? 1'h0 : ch_2_req_pending;
	assign ch_2_req_pending = ch_2_active & ((ch_2_single &  ~ ch_2_is_master) ? drq_1[2] : u253_output_port);
	assign ch_3_served = served_dma_channel[3] & bus_rsp_if_valid;
	always_ff @(posedge clk) ch_3_addr <= rst ? 32'h0 : (reg_if_paddr == 3'h6 & reg_write_strobe) ? reg_if_pwdata : ch_3_served ? next_addr : ch_3_addr;
	always_ff @(posedge clk) ch_3_limit <= rst ? 32'h0 : reg_if_paddr == 3'h7 & reg_write_strobe ? reg_if_pwdata : ch_3_limit;
	always_ff @(posedge clk) ch_3_single <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[12] : ch_3_single;
	always_ff @(posedge clk) ch_3_read_not_write <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[13] : ch_3_read_not_write;
	always_ff @(posedge clk) ch_3_is_master <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[14] : ch_3_is_master;
	always_ff @(posedge clk) ch_3_high_priority <= rst ? 1'h0 : reg_if_paddr == 4'ha & reg_write_strobe ? reg_if_pwdata[15] : ch_3_high_priority;
	always_ff @(posedge clk) ch_3_req_polarity <= rst ? 1'h0 : reg_if_paddr == 4'hb & reg_write_strobe ? reg_if_pwdata[12] : ch_3_req_polarity;
	always_ff @(posedge clk) ch_3_req_no_cdc <= rst ? 1'h0 : reg_if_paddr == 4'hb & reg_write_strobe ? reg_if_pwdata[13] : ch_3_req_no_cdc;
	always_ff @(posedge clk) ch_3_active <= rst ? 1'h0 : (reg_if_paddr == 3'h6 & reg_write_strobe) ? 1'h1 : ch_3_served ?  ~ tc_reg : ch_3_active;
	always_ff @(posedge clk) ch_3_int_pending <= rst ? 1'h0 : (tc_reg & ch_3_served) ? 1'h1 : (reg_if_paddr == 4'h8 & reg_write_strobe & reg_if_pwdata[3]) ? 1'h0 : ch_3_int_pending;
	always_ff @(posedge clk) u328_output_port <= rst ? 1'h0 : (drq_1[3] &  ~ prev_drq[3]) ? 1'h1 : ch_3_served ? 1'h0 : member;
	assign member = ch_3_active & ((ch_3_single &  ~ ch_3_is_master) ? drq_1[3] : u328_output_port);
	always @(*) begin
		case (reg_if_paddr)
			4'd0: u353_output_port = ch_0_addr;
			4'd1: u353_output_port = ch_0_limit;
			4'd2: u353_output_port = ch_1_addr;
			4'd3: u353_output_port = ch_1_limit;
			4'd4: u353_output_port = ch_2_addr;
			4'd5: u353_output_port = ch_2_limit;
			4'd6: u353_output_port = ch_3_addr;
			4'd7: u353_output_port = ch_3_limit;
			4'd8: u353_output_port = {ch_3_int_pending, ch_2_int_pending, ch_1_int_pending, ch_0_int_pending};
			4'd9: u353_output_port = {1'h0, 1'h0, member, ch_3_active, 1'h0, 1'h0, ch_2_req_pending, ch_2_active, 1'h0, 1'h0, ch_1_req_pending, ch_1_active, 1'h0, 1'h0, ch_0_req_pending, ch_0_active};
			4'd10: u353_output_port = {ch_3_is_master, ch_3_high_priority, ch_3_read_not_write, ch_3_single, ch_2_is_master, ch_2_high_priority, ch_2_read_not_write, ch_2_single, ch_1_is_master, ch_1_high_priority, ch_1_read_not_write, ch_1_single, ch_0_is_master, ch_0_high_priority, ch_0_read_not_write, ch_0_single};
			4'd11: u353_output_port = {ch_3_req_polarity, ch_3_req_no_cdc, 1'h0, 1'h0, ch_2_req_polarity, ch_2_req_no_cdc, 1'h0, 1'h0, ch_1_req_polarity, ch_1_req_no_cdc, 1'h0, 1'h0, ch_0_req_polarity, ch_0_req_no_cdc, 1'h0, 1'h0};
		endcase
	end
	always_ff @(posedge clk) reg_if_prdata <= rst ? 32'h0 : u353_output_port;
	assign high_pri_req_pending = {member & ch_3_high_priority, ch_2_req_pending & ch_2_high_priority, ch_1_req_pending & ch_1_high_priority, ch_0_req_pending & ch_0_high_priority};
	assign low_pri_req_pending = {member &  ~ ch_3_high_priority, ch_2_req_pending &  ~ ch_2_high_priority, ch_1_req_pending &  ~ ch_1_high_priority, ch_0_req_pending &  ~ ch_0_high_priority};
	assign high_pri_selected = high_pri_req_pending != 1'h0;
	assign selected_dma_channel = high_pri_selected ? high_pri_selected_dma_channel : low_pri_selected_dma_channel;
	assign selected_addr = 
		(selected_dma_channel[0] ? ch_0_addr : 32'b0) | 
		(selected_dma_channel[1] ? ch_1_addr : 32'b0) | 
		(selected_dma_channel[2] ? ch_2_addr : 32'b0) | 
		(selected_dma_channel[3] ? ch_3_addr : 32'b0) | 
		(selected_dma_channel[0] | selected_dma_channel[1] | selected_dma_channel[2] | selected_dma_channel[3] ? 32'b0 : 1'h0);
	assign selected_limit = 
		(selected_dma_channel[0] ? ch_0_limit : 32'b0) | 
		(selected_dma_channel[1] ? ch_1_limit : 32'b0) | 
		(selected_dma_channel[2] ? ch_2_limit : 32'b0) | 
		(selected_dma_channel[3] ? ch_3_limit : 32'b0) | 
		(selected_dma_channel[0] | selected_dma_channel[1] | selected_dma_channel[2] | selected_dma_channel[3] ? 32'b0 : 1'h0);
	assign tc =  ~ (selected_addr < selected_limit);
	always_ff @(posedge clk) next_addr <= rst ? 32'h0 : bus_req_if_ready & req_pendig ? u390_output_port[31:0] : next_addr;
	assign req_pendig = ch_0_req_pending | ch_1_req_pending | ch_2_req_pending | member;
	assign ch_read_not_writes = {ch_3_read_not_write, ch_2_read_not_write, ch_1_read_not_write, ch_0_read_not_write};
	assign read_not_writes = ch_read_not_writes & selected_dma_channel;
	assign bus_req_if_read_not_write = read_not_writes[0] | read_not_writes[1] | read_not_writes[2] | read_not_writes[3];
	assign bus_req_if_byte_en = 
		(selected_dma_channel[0] ? ({ch_0_addr[0],  ~ ch_0_addr[0]}) : 2'b0) | 
		(selected_dma_channel[1] ? ({ch_1_addr[0],  ~ ch_1_addr[0]}) : 2'b0) | 
		(selected_dma_channel[2] ? ({ch_2_addr[0],  ~ ch_2_addr[0]}) : 2'b0) | 
		(selected_dma_channel[3] ? ({ch_3_addr[0],  ~ ch_3_addr[0]}) : 2'b0) | 
		(selected_dma_channel[0] | selected_dma_channel[1] | selected_dma_channel[2] | selected_dma_channel[3] ? 2'b0 : 1'h0);
	assign bus_req_if_addr = selected_addr[31:1];
	assign bus_req_if_is_master = 
		(selected_dma_channel[0] ? ch_0_is_master : 1'b0) | 
		(selected_dma_channel[1] ? ch_1_is_master : 1'b0) | 
		(selected_dma_channel[2] ? ch_2_is_master : 1'b0) | 
		(selected_dma_channel[3] ? ch_3_is_master : 1'b0) | 
		(selected_dma_channel[0] | selected_dma_channel[1] | selected_dma_channel[2] | selected_dma_channel[3] ? 1'b0 : 1'h0);
	assign drq_1 = {ch_3_req_polarity ^ (ch_3_req_no_cdc ? drq[3] : u27_output_port), ch_2_req_polarity ^ (ch_2_req_no_cdc ? drq[2] : u21_output_port), ch_1_req_polarity ^ (ch_1_req_no_cdc ? drq[1] : u15_output_port), ch_0_req_polarity ^ (ch_0_req_no_cdc ? drq[0] : u9_output_port)};
	assign reg_if_pready = 1'h1;

	RoundRobinArbiter high_pri_arbiter (
		.clk(clk),
		.rst(rst),
		.requestors(high_pri_req_pending),
		.grants(high_pri_selected_dma_channel),
		.advance(bus_rsp_if_valid & high_pri_selected),
		.restart(u433_output_port)
	);

	RoundRobinArbiter_2 low_pri_arbiter (
		.clk(clk),
		.rst(rst),
		.requestors(low_pri_req_pending),
		.grants(low_pri_selected_dma_channel),
		.advance(bus_rsp_if_valid &  ~ high_pri_selected),
		.restart(u435_output_port)
	);

	assign ch_3_req_pending = member;
	assign bus_req_if_valid = req_pendig;
	assign bus_req_if_one_hot_channel = selected_dma_channel;
	assign bus_req_if_terminal_count = tc;
	assign u390_output_port = selected_addr + 1'h1 + 33'b0;
	assign u433_output_port = 1'h0;
	assign u435_output_port = 1'h0;
	assign priority_change = bus_rsp_if_valid;
endmodule


////////////////////////////////////////////////////////////////////////////////
// RoundRobinArbiter_2
////////////////////////////////////////////////////////////////////////////////
module RoundRobinArbiter_2 (
	input logic clk,
	input logic rst,
	input logic [3:0] requestors,
	output logic [3:0] grants,
	input logic advance,
	input logic restart
);

	logic [2:0] next_mask;
	logic [2:0] mask;
	logic [3:0] masked_requestors;
	logic [3:0] masked_selector;
	logic [3:0] unmasked_selector;

	assign next_mask = mask[0] ? 1'h0 : mask >> 1'h1 | 3'h4;
	always_ff @(posedge clk) mask <= rst ? 3'h0 : restart ? 1'h0 : advance ? next_mask : mask;
	assign masked_requestors = requestors &  ~ ({mask, 1'h0});
	assign masked_selector = masked_requestors[3] ? 4'h8 : masked_requestors[2] ? 3'h4 : masked_requestors[1] ? 2'h2 : masked_requestors[0] ? 1'h1 : 1'h0;
	assign unmasked_selector = requestors[3] ? 4'h8 : requestors[2] ? 3'h4 : requestors[1] ? 2'h2 : requestors[0] ? 1'h1 : 1'h0;
	assign grants = masked_selector == 1'h0 ? unmasked_selector : masked_selector;

endmodule


////////////////////////////////////////////////////////////////////////////////
// RoundRobinArbiter
////////////////////////////////////////////////////////////////////////////////
module RoundRobinArbiter (
	input logic clk,
	input logic rst,
	input logic [3:0] requestors,
	output logic [3:0] grants,
	input logic advance,
	input logic restart
);

	logic [2:0] next_mask;
	logic [2:0] mask;
	logic [3:0] masked_requestors;
	logic [3:0] masked_selector;
	logic [3:0] unmasked_selector;

	assign next_mask = mask[0] ? 1'h0 : mask >> 1'h1 | 3'h4;
	always_ff @(posedge clk) mask <= rst ? 3'h0 : restart ? 1'h0 : advance ? next_mask : mask;
	assign masked_requestors = requestors &  ~ ({mask, 1'h0});
	assign masked_selector = masked_requestors[3] ? 4'h8 : masked_requestors[2] ? 3'h4 : masked_requestors[1] ? 2'h2 : masked_requestors[0] ? 1'h1 : 1'h0;
	assign unmasked_selector = requestors[3] ? 4'h8 : requestors[2] ? 3'h4 : requestors[1] ? 2'h2 : requestors[0] ? 1'h1 : 1'h0;
	assign grants = masked_selector == 1'h0 ? unmasked_selector : masked_selector;

endmodule


////////////////////////////////////////////////////////////////////////////////
// BusIf
////////////////////////////////////////////////////////////////////////////////
module BusIf (
	input logic clk,
	input logic rst,
	input logic [30:0] fetch_request_addr,
	input logic [1:0] fetch_request_byte_en,
	input logic [15:0] fetch_request_data,
	input logic fetch_request_read_not_write,
	output logic fetch_request_ready,
	input logic fetch_request_valid,

	output logic [15:0] fetch_response_data,
	output logic fetch_response_valid,

	input logic [30:0] mem_request_addr,
	input logic [1:0] mem_request_byte_en,
	input logic [15:0] mem_request_data,
	input logic mem_request_read_not_write,
	output logic mem_request_ready,
	input logic mem_request_valid,

	output logic [15:0] mem_response_data,
	output logic mem_response_valid,

	input logic [30:0] dma_request_addr,
	input logic [1:0] dma_request_byte_en,
	input logic dma_request_is_master,
	input logic [3:0] dma_request_one_hot_channel,
	input logic dma_request_read_not_write,
	output logic dma_request_ready,
	input logic dma_request_terminal_count,
	input logic dma_request_valid,

	output logic dma_response_valid,
	input logic [3:0] reg_if_paddr,
	input logic reg_if_penable,
	output logic [31:0] reg_if_prdata,
	output logic reg_if_pready,
	input logic reg_if_psel,
	input logic [31:0] reg_if_pwdata,
	input logic reg_if_pwrite,

	output logic [10:0] dram_addr,
	output logic dram_bus_en,
	input logic [7:0] dram_data_in,
	output logic [7:0] dram_data_out,
	output logic dram_data_out_en,
	output logic dram_n_cas_0,
	output logic dram_n_cas_1,
	output logic [3:0] dram_n_dack,
	output logic dram_n_nren,
	output logic dram_n_ras_a,
	output logic dram_n_ras_b,
	input logic dram_n_wait,
	output logic dram_n_we,
	output logic dram_tc
);

	logic reg_write_strobe;
	logic [7:0] refresh_divider;
	logic u11_output_port;
	logic refresh_disable;
	logic [1:0] dram_bank_size;
	logic dram_bank_swap;
	logic refresh_tc;
	logic refresh_req;
	logic signed [8:0] u34_output_port;
	logic [7:0] refresh_counter;
	logic [10:0] refresh_addr;
	logic [1:0] arb_port_comb;
	logic [1:0] u54_output_port;
	logic [1:0] arb_port_select;
	logic req_ready;
	logic refresh_rsp;
	logic req_valid;
	logic start;
	logic [30:0] req_addr;
	logic [15:0] req_data;
	logic req_read_not_write;
	logic [1:0] req_byte_en;
	logic req_advance;
	logic req_dram;
	logic req_nram;
	logic req_dma;
	logic req_ext;
	logic req_rfsh;
	logic [3:0] dma_ch;
	logic tc;
	logic signed [4:0] u118_output_port;
	logic [3:0] wait_states_store;
	logic signed [4:0] u133_output_port;
	logic [3:0] wait_states;
	logic waiting;
	logic two_cycle_nram_access;
	logic nram_access;
	logic u151_output_port;
	logic u152_output_port;
	logic u153_output_port;
	logic u154_output_port;
	logic u155_output_port;
	logic u157_output_port;
	logic u158_output_port;
	logic u159_output_port;
	logic u160_output_port;
	logic u161_output_port;
	logic u162_output_port;
	logic u164_output_port;
	logic u167_output_port;
	logic u168_output_port;
	logic u169_output_port;
	logic u170_output_port;
	logic u171_output_port;
	logic u172_output_port;
	logic u173_output_port;
	logic u174_output_port;
	logic dram_bank;
	logic [10:0] row_addr;
	logic [10:0] col_addr;
	logic read_not_write;
	logic data_out_en;
	logic [1:0] u192_output_port;
	logic [1:0] byte_en;
	logic [15:0] data_out;
	logic dram_ras_active;
	logic u219_output_port;
	logic dram_n_ras_a_1;
	logic u226_output_port;
	logic dram_n_ras_b_1;
	logic n_nren;
	logic [3:0] u254_output_port;
	logic [3:0] n_dack;
	logic nr_cas_logic;
	logic nr_cas_logic_0;
	logic nr_cas_logic_1;
	logic nr_n_cas_0;
	logic nr_n_cas_1;
	logic cas_n_window_a_0;
	logic cas_n_window_a_1;
	logic cas_n_window_b_0;
	logic cas_n_window_c_1;
	logic cas_n_window_b_1;
	logic dram_n_cas_0_1;
	logic dram_n_cas_1_1;
	logic [10:0] u404_output_port;
	logic [10:0] dram_addr_1;
	logic [7:0] data_out_low;
	logic [7:0] data_out_high;
	logic read_active;
	logic [7:0] data_in_low;
	logic [7:0] ndram_data_in_high;
	logic [7:0] u460_output_port;
	logic [7:0] data_in_high;
	logic [15:0] u467_output_port;
	logic [15:0] resp_data;
	logic u473_output_port;
	logic u478_output_port;
	logic [10:0] input_row_addr;
	logic [3:0] state;
	logic [3:0] next_state;

	assign reg_write_strobe = reg_if_psel & reg_if_pwrite & reg_if_penable;
	always_ff @(posedge clk) u11_output_port <= rst ? 1'h0 : reg_if_paddr == 1'h0 & reg_write_strobe ? reg_if_pwdata[8] : u11_output_port;
	always_ff @(posedge clk) dram_bank_swap <= rst ? 1'h0 : reg_if_paddr == 1'h0 & reg_write_strobe ? reg_if_pwdata[11] : dram_bank_swap;
	always_ff @(posedge clk) dram_bank_size <= rst ? 2'h0 : reg_if_paddr == 1'h0 & reg_write_strobe ? reg_if_pwdata[10:9] : dram_bank_size;
	assign refresh_disable =  ~ u11_output_port;
	assign refresh_tc = refresh_counter == 1'h0;
	always_ff @(posedge clk) refresh_req <= rst ? 1'h0 : (refresh_tc &  ~ refresh_disable) ? 1'h1 : refresh_rsp ? 1'h0 : refresh_req;
	always_ff @(posedge clk) refresh_divider <= rst ? 8'h0 : reg_if_paddr == 1'h0 & reg_write_strobe ? reg_if_pwdata[7:0] : refresh_divider;
	always_ff @(posedge clk) refresh_counter <= rst ? 8'h0 : refresh_tc ? refresh_divider : refresh_req ? refresh_counter : u34_output_port[7:0];
	always_ff @(posedge clk) refresh_addr <= rst ? 11'h0 : refresh_rsp ? 11'(refresh_addr + 1'h1 + 12'b0) : refresh_addr;
	assign arb_port_comb = refresh_req ? `Ports__refresh_port : dma_request_valid ? `Ports__dma_port : mem_request_valid ? `Ports__mem_port : `Ports__fetch_port;
	always_ff @(posedge clk) u54_output_port <= rst ? 2'h0 : state == `BusIfStates__idle ? arb_port_comb : u54_output_port;
	assign arb_port_select = state == `BusIfStates__idle ? arb_port_comb : u54_output_port;
	assign req_ready = state == `BusIfStates__idle | state == `BusIfStates__first | state == `BusIfStates__middle;
	assign refresh_rsp = state == `BusIfStates__refresh;
	assign mem_request_ready = req_ready & arb_port_select == `Ports__mem_port;
	assign fetch_request_ready = req_ready & arb_port_select == `Ports__fetch_port;
	assign dma_request_ready = req_ready & arb_port_select == `Ports__dma_port | state == `BusIfStates__external;
	always @(*) begin
		case (arb_port_select)
			2'd0: req_valid = fetch_request_valid;
			2'd1: req_valid = mem_request_valid;
			2'd2: req_valid = dma_request_valid;
			2'd3: req_valid = 1'h1;
		endcase
	end
	assign start = state == `BusIfStates__idle & req_valid;
	assign req_addr = (arb_port_select == 0 ? fetch_request_addr : 31'b0) | (arb_port_select == 1 ? mem_request_addr : 31'b0) | (arb_port_select == 2 ? dma_request_addr : 31'b0);
	assign req_data = (arb_port_select == 0 ? fetch_request_data : 16'b0) | (arb_port_select == 1 ? mem_request_data : 16'b0) | (arb_port_select == 2 ? $signed(1'bX) : 16'b0);
	assign req_read_not_write = (arb_port_select == 0 ? fetch_request_read_not_write : 1'b0) | (arb_port_select == 1 ? mem_request_read_not_write : 1'b0) | (arb_port_select == 2 ? dma_request_read_not_write : 1'b0);
	assign req_byte_en = (arb_port_select == 0 ? fetch_request_byte_en : 2'b0) | (arb_port_select == 1 ? mem_request_byte_en : 2'b0) | (arb_port_select == 2 ? dma_request_byte_en : 2'b0);
	always_ff @(posedge clk) wait_states_store <= rst ? 4'h0 : start ? u118_output_port[3:0] : wait_states_store;
	always_ff @(posedge clk) wait_states <= rst ? 4'h0 : start ? u118_output_port[3:0] : wait_states == 1'h0 ? state == `BusIfStates__non_dram_dual ? wait_states_store : 1'h0 : u133_output_port[3:0];
	assign req_nram = req_addr[30:29] == 1'h0 & (arb_port_select == `Ports__mem_port | arb_port_select == `Ports__fetch_port);
	always_ff @(posedge clk) two_cycle_nram_access <= rst ? 1'h0 : start ? req_byte_en == 2'h3 & req_nram : two_cycle_nram_access;
	always_ff @(posedge clk) nram_access <= rst ? 1'h0 : start ? req_nram : nram_access;
	assign req_ext = arb_port_select == `Ports__dma_port & dma_request_is_master;
	assign req_dma = arb_port_select == `Ports__dma_port &  ~ dma_request_is_master;
	assign req_dram = req_addr[30:29] != 1'h0 & (arb_port_select == `Ports__mem_port | arb_port_select == `Ports__fetch_port);
	assign req_rfsh = arb_port_select == `Ports__refresh_port;
	assign waiting =  ~ dram_n_wait | wait_states != 1'h0;
	always @(*) begin
		case (dram_bank_size)
			2'd0: u174_output_port = req_addr[22];
			2'd1: u174_output_port = req_addr[20];
			2'd2: u174_output_port = req_addr[18];
			2'd3: u174_output_port = req_addr[16];
		endcase
	end
	always_ff @(posedge clk) dram_bank <= rst ? 1'h0 : start ? u174_output_port : dram_bank;
	assign input_row_addr = req_addr[21:11];
	always_ff @(posedge clk) row_addr <= rst ? 11'h0 : start ? req_rfsh ? refresh_addr : input_row_addr : row_addr;
	assign req_advance = req_valid & req_ready;
	always_ff @(posedge clk) col_addr <= rst ? 11'h0 : req_advance ? req_addr[10:0] : col_addr;
	always_ff @(posedge clk) read_not_write <= rst ? 1'h1 : start ? req_read_not_write : read_not_write;
	initial read_not_write <= 1'h1;
	always_ff @(posedge clk) data_out_en <= rst ? 1'h0 : start ?  ~ req_read_not_write & arb_port_select != `Ports__dma_port : data_out_en;
	always_ff @(posedge clk) u192_output_port <= rst ? 2'h0 : req_advance ? req_byte_en : u192_output_port;
	assign byte_en = req_advance ? req_byte_en : u192_output_port;
	always_ff @(posedge clk) data_out <= rst ? 16'h0 : req_advance ? req_byte_en[0] ? req_data : ({req_data[7:0], req_data[7:0]}) : data_out;
	assign dram_ras_active = next_state == `BusIfStates__first | next_state == `BusIfStates__middle | next_state == `BusIfStates__precharge | next_state == `BusIfStates__dma_first | next_state == `BusIfStates__dma_wait;
	always_ff @(posedge clk) u219_output_port <= rst ? 1'h0 : dram_ras_active & dram_bank == dram_bank_swap | next_state == `BusIfStates__refresh;
	always_ff @(posedge clk) u226_output_port <= rst ? 1'h0 : dram_ras_active & dram_bank != dram_bank_swap | next_state == `BusIfStates__refresh;
	always_ff @(posedge clk) n_nren <= rst ? 1'h1 : next_state != `BusIfStates__non_dram_first & next_state != `BusIfStates__non_dram_wait & next_state != `BusIfStates__non_dram_dual_first & next_state != `BusIfStates__non_dram_dual_wait;
	initial n_nren <= 1'h1;
	always_ff @(posedge clk) dma_ch <= rst ? 4'h0 : start ? dma_request_one_hot_channel : dma_ch;
	always_ff @(posedge clk) u254_output_port <= rst ? 4'h0 : (state == `BusIfStates__dma_first | state == `BusIfStates__dma_wait & waiting | state == `BusIfStates__external & req_valid & req_ext) ? dma_ch : 1'h0;
	assign n_dack =  ~ u254_output_port;
	assign nr_cas_logic = state == `BusIfStates__non_dram_dual_first | state == `BusIfStates__non_dram_first | state == `BusIfStates__dma_first | waiting & (state == `BusIfStates__non_dram_dual_wait | state == `BusIfStates__non_dram_wait | state == `BusIfStates__dma_wait);
	assign nr_cas_logic_0 = nr_cas_logic & ( ~ two_cycle_nram_access | state == `BusIfStates__non_dram_first | state == `BusIfStates__non_dram_wait | state == `BusIfStates__dma_first | state == `BusIfStates__dma_wait);
	always_ff @(posedge clk) nr_n_cas_0 <= rst ? 1'h1 :  ~ nr_cas_logic_0 |  ~ byte_en[0];
	initial nr_n_cas_0 <= 1'h1;
	assign nr_cas_logic_1 = nr_cas_logic & ( ~ two_cycle_nram_access | state == `BusIfStates__non_dram_dual_first | state == `BusIfStates__non_dram_dual_wait | state == `BusIfStates__dma_first | state == `BusIfStates__dma_wait);
	always_ff @(posedge clk) nr_n_cas_1 <= rst ? 1'h1 :  ~ nr_cas_logic_1 |  ~ byte_en[1];
	initial nr_n_cas_1 <= 1'h1;
	always_ff @(posedge clk) cas_n_window_a_0 <= rst ? 1'h1 :  ~ byte_en[0] | next_state == `BusIfStates__idle | next_state == `BusIfStates__precharge | next_state == `BusIfStates__non_dram_first | next_state == `BusIfStates__non_dram_wait | next_state == `BusIfStates__non_dram_dual | next_state == `BusIfStates__non_dram_dual_first | next_state == `BusIfStates__non_dram_dual_wait | next_state == `BusIfStates__dma_first | next_state == `BusIfStates__dma_wait;
	initial cas_n_window_a_0 <= 1'h1;
	always_ff @(posedge clk) cas_n_window_a_1 <= rst ? 1'h1 :  ~ byte_en[1] | next_state == `BusIfStates__idle | next_state == `BusIfStates__precharge | next_state == `BusIfStates__non_dram_first | next_state == `BusIfStates__non_dram_wait | next_state == `BusIfStates__non_dram_dual | next_state == `BusIfStates__non_dram_dual_first | next_state == `BusIfStates__non_dram_dual_wait | next_state == `BusIfStates__dma_first | next_state == `BusIfStates__dma_wait;
	initial cas_n_window_a_1 <= 1'h1;
	always_ff @(negedge clk) cas_n_window_b_0 <= rst ? 1'h1 : cas_n_window_a_0;
	initial cas_n_window_b_0 <= 1'h1;
	always_ff @(posedge clk) cas_n_window_c_1 <= rst ? 1'h1 : cas_n_window_a_1;
	initial cas_n_window_c_1 <= 1'h1;
	always_ff @(negedge clk) cas_n_window_b_1 <= rst ? 1'h1 : cas_n_window_a_1;
	initial cas_n_window_b_1 <= 1'h1;
	assign dram_n_ras_a_1 =  ~ u219_output_port;
	assign dram_n_ras_b_1 =  ~ u226_output_port;
	assign dram_n_cas_0_1 = cas_n_window_a_0 | cas_n_window_b_0 | clk;
	assign dram_n_cas_0 = dram_n_cas_0_1 & nr_n_cas_0;
	assign dram_n_cas_1_1 = cas_n_window_b_1 | cas_n_window_c_1 |  ~ clk;
	assign dram_n_cas_1 = dram_n_cas_1_1 & nr_n_cas_1;
	always_ff @(negedge clk) u404_output_port <= rst ? 11'h0 : col_addr;
	assign dram_addr_1 = ((state == `BusIfStates__first | state == `BusIfStates__non_dram_first | state == `BusIfStates__non_dram_dual_first | state == `BusIfStates__dma_first | state == `BusIfStates__refresh) & clk) ? row_addr : u404_output_port;
	always_ff @(negedge clk) data_out_low <= rst ? 8'h0 : nram_access ? (two_cycle_nram_access & (nr_cas_logic_1 |  ~ nr_n_cas_1)) ? data_out[15:8] : data_out[7:0] : data_out[7:0];
	always_ff @(posedge clk) data_out_high <= rst ? 8'h0 : nram_access ? (two_cycle_nram_access & nr_cas_logic_1) ? data_out[15:8] : data_out[7:0] : data_out[15:8];
	assign dram_data_out = clk ? data_out_high : data_out_low;
	always_ff @(posedge clk) tc <= rst ? 1'h0 : start ? dma_request_terminal_count : tc;
	assign dram_bus_en = state != `BusIfStates__external;
	assign read_active = (state == `BusIfStates__first | state == `BusIfStates__middle | state == `BusIfStates__dma_wait &  ~ waiting | state == `BusIfStates__non_dram_wait &  ~ waiting &  ~ two_cycle_nram_access | state == `BusIfStates__non_dram_dual_wait &  ~ waiting) & read_not_write;
	always_ff @(posedge clk) data_in_low <= rst ? 8'h0 : state == `BusIfStates__non_dram_wait | state == `BusIfStates__first | state == `BusIfStates__middle ? dram_data_in : data_in_low;
	always_ff @(negedge clk) u460_output_port <= rst ? 8'h0 : dram_data_in;
	always_ff @(posedge clk) ndram_data_in_high <= rst ? 8'h0 : state == `BusIfStates__non_dram_dual_wait ? dram_data_in : ndram_data_in_high;
	assign data_in_high = two_cycle_nram_access ? ndram_data_in_high : u460_output_port;
	always @(*) begin
		case (byte_en)
			2'd0: u467_output_port = $signed(1'bX);
			2'd1: u467_output_port = {8'h0, data_in_low};
			2'd2: u467_output_port = {8'h0, data_in_high};
			2'd3: u467_output_port = {data_in_high, data_in_low};
		endcase
	end
	always_ff @(posedge clk) resp_data <= rst ? 16'h0 : u467_output_port;
	always_ff @(posedge clk) u473_output_port <= rst ? 1'h0 : read_active & arb_port_select == `Ports__mem_port;
	always_ff @(posedge clk) mem_response_valid <= rst ? 1'h0 : u473_output_port;
	always_ff @(posedge clk) u478_output_port <= rst ? 1'h0 : read_active & arb_port_select == `Ports__fetch_port;
	always_ff @(posedge clk) fetch_response_valid <= rst ? 1'h0 : u478_output_port;
	assign dma_response_valid = state == `BusIfStates__dma_wait &  ~ waiting;
	assign reg_if_pready = 1'h1;
	assign reg_if_prdata = {dram_bank_swap, dram_bank_size, refresh_disable, refresh_counter};
	assign fetch_response_data = resp_data;

	FSM fsm (
		.clock_port(clk),
		.reset_port(rst),
		.reset_value(`BusIfStates__idle),
		.state(state),
		.next_state(next_state),
		.default_state(`BusIfStates__idle),
		.input_idle_to_external(u151_output_port),
		.input_idle_to_non_dram_first(u152_output_port),
		.input_idle_to_dma_first(u153_output_port),
		.input_idle_to_first(u154_output_port),
		.input_idle_to_refresh(u155_output_port),
		.input_external_to_idle(u157_output_port),
		.input_external_to_idle_1(u158_output_port),
		.input_first_to_precharge(u159_output_port),
		.input_first_to_middle(req_valid),
		.input_middle_to_precharge(u160_output_port),
		.input_precharge_to_idle(u161_output_port),
		.input_non_dram_first_to_non_dram_wait(u162_output_port),
		.input_non_dram_wait_to_non_dram_wait(waiting),
		.input_non_dram_wait_to_non_dram_dual(u164_output_port),
		.input_non_dram_wait_to_idle(u167_output_port),
		.input_non_dram_dual_to_non_dram_dual_first(u168_output_port),
		.input_non_dram_dual_first_to_non_dram_dual_wait(u169_output_port),
		.input_non_dram_dual_wait_to_non_dram_dual_wait(waiting),
		.input_non_dram_dual_wait_to_idle(u170_output_port),
		.input_dma_first_to_dma_wait(u171_output_port),
		.input_dma_wait_to_dma_wait(waiting),
		.input_dma_wait_to_idle(u172_output_port),
		.input_refresh_to_idle(u173_output_port)
	);

	assign u34_output_port = refresh_counter - 1'h1 + 9'b0;
	assign dram_tc = tc;
	assign u118_output_port = req_addr[28:25] - 1'h1 + 5'b0;
	assign u133_output_port = wait_states - (state == `BusIfStates__dma_wait | state == `BusIfStates__non_dram_dual_wait | state == `BusIfStates__non_dram_wait) + 5'b0;
	assign u151_output_port = req_valid & req_ext;
	assign u152_output_port = req_valid & req_nram;
	assign u153_output_port = req_valid & req_dma;
	assign u154_output_port = req_valid & req_dram;
	assign u155_output_port = req_valid & req_rfsh;
	assign u157_output_port = req_valid &  ~ req_ext;
	assign u158_output_port =  ~ req_valid;
	assign u159_output_port =  ~ req_valid;
	assign u160_output_port =  ~ req_valid;
	assign u161_output_port = 1'h1;
	assign u162_output_port = 1'h1;
	assign u164_output_port =  ~ waiting & two_cycle_nram_access;
	assign u167_output_port =  ~ waiting &  ~ two_cycle_nram_access;
	assign u168_output_port = 1'h1;
	assign u169_output_port = 1'h1;
	assign u170_output_port =  ~ waiting;
	assign u171_output_port = 1'h1;
	assign u172_output_port =  ~ waiting;
	assign u173_output_port = 1'h1;
	assign dram_n_we = read_not_write;
	assign dram_data_out_en = data_out_en;
	assign dram_n_ras_a = dram_n_ras_a_1;
	assign dram_n_ras_b = dram_n_ras_b_1;
	assign dram_n_nren = n_nren;
	assign dram_n_dack = n_dack;
	assign dram_addr = dram_addr_1;
	assign mem_response_data = resp_data;
endmodule


////////////////////////////////////////////////////////////////////////////////
// FSM_3
////////////////////////////////////////////////////////////////////////////////
module FSM_3 (
	input logic clock_port,
	input logic reset_port,
	input logic [1:0] reset_value,
	output logic [1:0] state,
	output logic [1:0] next_state,
	input logic [1:0] default_state,
	input logic input_have_0_fragments_to_have_all_fragments,
	input logic input_have_0_fragments_to_have_all_fragments_1,
	input logic input_have_0_fragments_to_need_1_fragments,
	input logic input_have_0_fragments_to_need_2_fragments,
	input logic input_have_0_fragments_to_have_0_fragments,
	input logic input_have_0_fragments_to_have_0_fragments_1,
	input logic input_need_1_fragments_to_have_all_fragments,
	input logic input_need_1_fragments_to_need_1_fragments,
	input logic input_need_1_fragments_to_have_0_fragments,
	input logic input_need_2_fragments_to_need_1_fragments,
	input logic input_need_2_fragments_to_have_all_fragments,
	input logic input_need_2_fragments_to_need_2_fragments,
	input logic input_need_2_fragments_to_have_0_fragments,
	input logic input_have_all_fragments_to_have_all_fragments,
	input logic input_have_all_fragments_to_have_all_fragments_1,
	input logic input_have_all_fragments_to_need_1_fragments,
	input logic input_have_all_fragments_to_need_2_fragments,
	input logic input_have_all_fragments_to_have_0_fragments,
	input logic input_have_all_fragments_to_have_all_fragments_2,
	input logic input_have_all_fragments_to_have_0_fragments_1
);

	logic [1:0] local_state;
	logic [1:0] local_next_state;

	always_ff @(posedge clock_port) local_state <= reset_port ? reset_value : local_next_state;
	initial local_state <= reset_value;

	FSMLogic_3 fsm_logic (
		.state(local_state),
		.next_state(local_next_state),
		.default_state(default_state),
		.input_have_0_fragments_to_have_all_fragments(input_have_0_fragments_to_have_all_fragments),
		.input_have_0_fragments_to_have_all_fragments_1(input_have_0_fragments_to_have_all_fragments_1),
		.input_have_0_fragments_to_need_1_fragments(input_have_0_fragments_to_need_1_fragments),
		.input_have_0_fragments_to_need_2_fragments(input_have_0_fragments_to_need_2_fragments),
		.input_have_0_fragments_to_have_0_fragments(input_have_0_fragments_to_have_0_fragments),
		.input_have_0_fragments_to_have_0_fragments_1(input_have_0_fragments_to_have_0_fragments_1),
		.input_need_1_fragments_to_have_all_fragments(input_need_1_fragments_to_have_all_fragments),
		.input_need_1_fragments_to_need_1_fragments(input_need_1_fragments_to_need_1_fragments),
		.input_need_1_fragments_to_have_0_fragments(input_have_0_fragments_to_have_0_fragments_1),
		.input_need_2_fragments_to_need_1_fragments(input_need_2_fragments_to_need_1_fragments),
		.input_need_2_fragments_to_have_all_fragments(input_need_2_fragments_to_have_all_fragments),
		.input_need_2_fragments_to_need_2_fragments(input_need_2_fragments_to_need_2_fragments),
		.input_need_2_fragments_to_have_0_fragments(input_have_0_fragments_to_have_0_fragments_1),
		.input_have_all_fragments_to_have_all_fragments(input_have_all_fragments_to_have_all_fragments),
		.input_have_all_fragments_to_have_all_fragments_1(input_have_all_fragments_to_have_all_fragments_1),
		.input_have_all_fragments_to_need_1_fragments(input_have_all_fragments_to_need_1_fragments),
		.input_have_all_fragments_to_need_2_fragments(input_have_all_fragments_to_need_2_fragments),
		.input_have_all_fragments_to_have_0_fragments(input_have_all_fragments_to_have_0_fragments),
		.input_have_all_fragments_to_have_all_fragments_2(input_have_all_fragments_to_have_all_fragments_2),
		.input_have_all_fragments_to_have_0_fragments_1(input_have_0_fragments_to_have_0_fragments_1)
	);

	assign state = local_state;
	assign next_state = local_next_state;
endmodule


////////////////////////////////////////////////////////////////////////////////
// FSM_2
////////////////////////////////////////////////////////////////////////////////
module FSM_2 (
	input logic clock_port,
	input logic reset_port,
	input logic [1:0] reset_value,
	output logic [1:0] state,
	output logic [1:0] next_state,
	input logic [1:0] default_state,
	input logic input_idle_to_request,
	input logic input_idle_to_flushing,
	input logic input_request_to_idle,
	input logic input_request_to_flushing,
	input logic input_request_to_request,
	input logic input_flushing_to_request
);

	logic [1:0] local_state;
	logic [1:0] local_next_state;

	always_ff @(posedge clock_port) local_state <= reset_port ? reset_value : local_next_state;
	initial local_state <= reset_value;

	FSMLogic_2 fsm_logic (
		.state(local_state),
		.next_state(local_next_state),
		.default_state(default_state),
		.input_idle_to_request(input_idle_to_request),
		.input_idle_to_flushing(input_idle_to_flushing),
		.input_request_to_idle(input_request_to_idle),
		.input_request_to_flushing(input_request_to_flushing),
		.input_request_to_request(input_request_to_request),
		.input_flushing_to_request(input_flushing_to_request)
	);

	assign state = local_state;
	assign next_state = local_next_state;
endmodule


////////////////////////////////////////////////////////////////////////////////
// FSM
////////////////////////////////////////////////////////////////////////////////
module FSM (
	input logic clock_port,
	input logic reset_port,
	input logic [3:0] reset_value,
	output logic [3:0] state,
	output logic [3:0] next_state,
	input logic [3:0] default_state,
	input logic input_idle_to_external,
	input logic input_idle_to_non_dram_first,
	input logic input_idle_to_dma_first,
	input logic input_idle_to_first,
	input logic input_idle_to_refresh,
	input logic input_external_to_idle,
	input logic input_external_to_idle_1,
	input logic input_first_to_precharge,
	input logic input_first_to_middle,
	input logic input_middle_to_precharge,
	input logic input_precharge_to_idle,
	input logic input_non_dram_first_to_non_dram_wait,
	input logic input_non_dram_wait_to_non_dram_wait,
	input logic input_non_dram_wait_to_non_dram_dual,
	input logic input_non_dram_wait_to_idle,
	input logic input_non_dram_dual_to_non_dram_dual_first,
	input logic input_non_dram_dual_first_to_non_dram_dual_wait,
	input logic input_non_dram_dual_wait_to_non_dram_dual_wait,
	input logic input_non_dram_dual_wait_to_idle,
	input logic input_dma_first_to_dma_wait,
	input logic input_dma_wait_to_dma_wait,
	input logic input_dma_wait_to_idle,
	input logic input_refresh_to_idle
);

	logic [3:0] local_state;
	logic [3:0] local_next_state;

	always_ff @(posedge clock_port) local_state <= reset_port ? reset_value : local_next_state;
	initial local_state <= reset_value;

	FSMLogic fsm_logic (
		.state(local_state),
		.next_state(local_next_state),
		.default_state(default_state),
		.input_idle_to_external(input_idle_to_external),
		.input_idle_to_non_dram_first(input_idle_to_non_dram_first),
		.input_idle_to_dma_first(input_idle_to_dma_first),
		.input_idle_to_first(input_idle_to_first),
		.input_idle_to_refresh(input_idle_to_refresh),
		.input_external_to_idle(input_external_to_idle),
		.input_external_to_idle_1(input_external_to_idle_1),
		.input_first_to_precharge(input_first_to_precharge),
		.input_first_to_middle(input_first_to_middle),
		.input_middle_to_precharge(input_middle_to_precharge),
		.input_precharge_to_idle(input_precharge_to_idle),
		.input_non_dram_first_to_non_dram_wait(input_non_dram_first_to_non_dram_wait),
		.input_non_dram_wait_to_non_dram_wait(input_non_dram_wait_to_non_dram_wait),
		.input_non_dram_wait_to_non_dram_dual(input_non_dram_wait_to_non_dram_dual),
		.input_non_dram_wait_to_idle(input_non_dram_wait_to_idle),
		.input_non_dram_dual_to_non_dram_dual_first(input_non_dram_dual_to_non_dram_dual_first),
		.input_non_dram_dual_first_to_non_dram_dual_wait(input_non_dram_dual_first_to_non_dram_dual_wait),
		.input_non_dram_dual_wait_to_non_dram_dual_wait(input_non_dram_wait_to_non_dram_wait),
		.input_non_dram_dual_wait_to_idle(input_non_dram_dual_wait_to_idle),
		.input_dma_first_to_dma_wait(input_dma_first_to_dma_wait),
		.input_dma_wait_to_dma_wait(input_non_dram_wait_to_non_dram_wait),
		.input_dma_wait_to_idle(input_dma_wait_to_idle),
		.input_refresh_to_idle(input_refresh_to_idle)
	);

	assign state = local_state;
	assign next_state = local_next_state;
endmodule


////////////////////////////////////////////////////////////////////////////////
// FSMLogic_3
////////////////////////////////////////////////////////////////////////////////
module FSMLogic_3 (
	input logic [1:0] state,
	output logic [1:0] next_state,
	input logic [1:0] default_state,
	input logic input_have_0_fragments_to_have_all_fragments,
	input logic input_have_0_fragments_to_have_all_fragments_1,
	input logic input_have_0_fragments_to_need_1_fragments,
	input logic input_have_0_fragments_to_need_2_fragments,
	input logic input_have_0_fragments_to_have_0_fragments,
	input logic input_have_0_fragments_to_have_0_fragments_1,
	input logic input_need_1_fragments_to_have_all_fragments,
	input logic input_need_1_fragments_to_need_1_fragments,
	input logic input_need_1_fragments_to_have_0_fragments,
	input logic input_need_2_fragments_to_need_1_fragments,
	input logic input_need_2_fragments_to_have_all_fragments,
	input logic input_need_2_fragments_to_need_2_fragments,
	input logic input_need_2_fragments_to_have_0_fragments,
	input logic input_have_all_fragments_to_have_all_fragments,
	input logic input_have_all_fragments_to_have_all_fragments_1,
	input logic input_have_all_fragments_to_need_1_fragments,
	input logic input_have_all_fragments_to_need_2_fragments,
	input logic input_have_all_fragments_to_have_0_fragments,
	input logic input_have_all_fragments_to_have_all_fragments_2,
	input logic input_have_all_fragments_to_have_0_fragments_1
);

	logic [1:0] state_have_0_fragments_selector;
	logic [1:0] state_need_1_fragments_selector;
	logic [1:0] state_need_2_fragments_selector;
	logic [1:0] state_have_all_fragments_selector;

	assign state_have_0_fragments_selector = 
		(input_have_0_fragments_to_have_all_fragments ? `InstAssembleStates__have_all_fragments : 2'b0) | 
		(input_have_0_fragments_to_have_all_fragments_1 ? `InstAssembleStates__have_all_fragments : 2'b0) | 
		(input_have_0_fragments_to_need_1_fragments ? `InstAssembleStates__need_1_fragments : 2'b0) | 
		(input_have_0_fragments_to_need_2_fragments ? `InstAssembleStates__need_2_fragments : 2'b0) | 
		(input_have_0_fragments_to_have_0_fragments ? `InstAssembleStates__have_0_fragments : 2'b0) | 
		(input_have_0_fragments_to_have_0_fragments_1 ? `InstAssembleStates__have_0_fragments : 2'b0) | 
		(input_have_0_fragments_to_have_all_fragments | input_have_0_fragments_to_have_all_fragments_1 | input_have_0_fragments_to_need_1_fragments | input_have_0_fragments_to_need_2_fragments | input_have_0_fragments_to_have_0_fragments | input_have_0_fragments_to_have_0_fragments_1 ? 2'b0 : `InstAssembleStates__have_0_fragments);
	assign state_need_1_fragments_selector = (input_need_1_fragments_to_have_all_fragments ? `InstAssembleStates__have_all_fragments : 2'b0) | (input_need_1_fragments_to_need_1_fragments ? `InstAssembleStates__need_1_fragments : 2'b0) | (input_have_0_fragments_to_have_0_fragments_1 ? `InstAssembleStates__have_0_fragments : 2'b0) | (input_need_1_fragments_to_have_all_fragments | input_need_1_fragments_to_need_1_fragments | input_have_0_fragments_to_have_0_fragments_1 ? 2'b0 : `InstAssembleStates__need_1_fragments);
	assign state_need_2_fragments_selector = 
		(input_need_2_fragments_to_need_1_fragments ? `InstAssembleStates__need_1_fragments : 2'b0) | 
		(input_need_2_fragments_to_have_all_fragments ? `InstAssembleStates__have_all_fragments : 2'b0) | 
		(input_need_2_fragments_to_need_2_fragments ? `InstAssembleStates__need_2_fragments : 2'b0) | 
		(input_have_0_fragments_to_have_0_fragments_1 ? `InstAssembleStates__have_0_fragments : 2'b0) | 
		(input_need_2_fragments_to_need_1_fragments | input_need_2_fragments_to_have_all_fragments | input_need_2_fragments_to_need_2_fragments | input_have_0_fragments_to_have_0_fragments_1 ? 2'b0 : `InstAssembleStates__need_2_fragments);
	assign state_have_all_fragments_selector = 
		(input_have_all_fragments_to_have_all_fragments ? `InstAssembleStates__have_all_fragments : 2'b0) | 
		(input_have_all_fragments_to_have_all_fragments_1 ? `InstAssembleStates__have_all_fragments : 2'b0) | 
		(input_have_all_fragments_to_have_all_fragments_2 ? `InstAssembleStates__have_all_fragments : 2'b0) | 
		(input_have_all_fragments_to_need_1_fragments ? `InstAssembleStates__need_1_fragments : 2'b0) | 
		(input_have_all_fragments_to_need_2_fragments ? `InstAssembleStates__need_2_fragments : 2'b0) | 
		(input_have_all_fragments_to_have_0_fragments ? `InstAssembleStates__have_0_fragments : 2'b0) | 
		(input_have_0_fragments_to_have_0_fragments_1 ? `InstAssembleStates__have_0_fragments : 2'b0) | 
		(input_have_all_fragments_to_have_all_fragments | input_have_all_fragments_to_have_all_fragments_1 | input_have_all_fragments_to_have_all_fragments_2 | input_have_all_fragments_to_need_1_fragments | input_have_all_fragments_to_need_2_fragments | input_have_all_fragments_to_have_0_fragments | input_have_0_fragments_to_have_0_fragments_1 ? 2'b0 : `InstAssembleStates__have_all_fragments);
	assign next_state = 
		(state == `InstAssembleStates__have_0_fragments ? state_have_0_fragments_selector : 2'b0) | 
		(state == `InstAssembleStates__need_1_fragments ? state_need_1_fragments_selector : 2'b0) | 
		(state == `InstAssembleStates__need_2_fragments ? state_need_2_fragments_selector : 2'b0) | 
		(state == `InstAssembleStates__have_all_fragments ? state_have_all_fragments_selector : 2'b0) | 
		(state == `InstAssembleStates__have_0_fragments | state == `InstAssembleStates__need_1_fragments | state == `InstAssembleStates__need_2_fragments | state == `InstAssembleStates__have_all_fragments ? 2'b0 : default_state);

endmodule


////////////////////////////////////////////////////////////////////////////////
// FSMLogic_2
////////////////////////////////////////////////////////////////////////////////
module FSMLogic_2 (
	input logic [1:0] state,
	output logic [1:0] next_state,
	input logic [1:0] default_state,
	input logic input_idle_to_request,
	input logic input_idle_to_flushing,
	input logic input_request_to_idle,
	input logic input_request_to_flushing,
	input logic input_request_to_request,
	input logic input_flushing_to_request
);

	logic [1:0] state_idle_selector;
	logic [1:0] state_request_selector;
	logic [1:0] state_flushing_selector;

	assign state_idle_selector = (input_idle_to_request ? `InstBufferStates__request : 2'b0) | (input_idle_to_flushing ? `InstBufferStates__flushing : 2'b0) | (input_idle_to_request | input_idle_to_flushing ? 2'b0 : `InstBufferStates__idle);
	assign state_request_selector = (input_request_to_idle ? `InstBufferStates__idle : 2'b0) | (input_request_to_flushing ? `InstBufferStates__flushing : 2'b0) | (input_request_to_request ? `InstBufferStates__request : 2'b0) | (input_request_to_idle | input_request_to_flushing | input_request_to_request ? 2'b0 : `InstBufferStates__request);
	assign state_flushing_selector = (input_flushing_to_request ? `InstBufferStates__request : 2'b0) | (input_flushing_to_request ? 2'b0 : `InstBufferStates__flushing);
	assign next_state = (state == `InstBufferStates__idle ? state_idle_selector : 2'b0) | (state == `InstBufferStates__request ? state_request_selector : 2'b0) | (state == `InstBufferStates__flushing ? state_flushing_selector : 2'b0) | (state == `InstBufferStates__idle | state == `InstBufferStates__request | state == `InstBufferStates__flushing ? 2'b0 : default_state);

endmodule


////////////////////////////////////////////////////////////////////////////////
// FSMLogic
////////////////////////////////////////////////////////////////////////////////
module FSMLogic (
	input logic [3:0] state,
	output logic [3:0] next_state,
	input logic [3:0] default_state,
	input logic input_idle_to_external,
	input logic input_idle_to_non_dram_first,
	input logic input_idle_to_dma_first,
	input logic input_idle_to_first,
	input logic input_idle_to_refresh,
	input logic input_external_to_idle,
	input logic input_external_to_idle_1,
	input logic input_first_to_precharge,
	input logic input_first_to_middle,
	input logic input_middle_to_precharge,
	input logic input_precharge_to_idle,
	input logic input_non_dram_first_to_non_dram_wait,
	input logic input_non_dram_wait_to_non_dram_wait,
	input logic input_non_dram_wait_to_non_dram_dual,
	input logic input_non_dram_wait_to_idle,
	input logic input_non_dram_dual_to_non_dram_dual_first,
	input logic input_non_dram_dual_first_to_non_dram_dual_wait,
	input logic input_non_dram_dual_wait_to_non_dram_dual_wait,
	input logic input_non_dram_dual_wait_to_idle,
	input logic input_dma_first_to_dma_wait,
	input logic input_dma_wait_to_dma_wait,
	input logic input_dma_wait_to_idle,
	input logic input_refresh_to_idle
);

	logic [3:0] state_idle_selector;
	logic [3:0] state_external_selector;
	logic [3:0] state_first_selector;
	logic [3:0] state_middle_selector;
	logic [3:0] state_precharge_selector;
	logic [3:0] state_non_dram_first_selector;
	logic [3:0] state_non_dram_wait_selector;
	logic [3:0] state_non_dram_dual_selector;
	logic [3:0] state_non_dram_dual_first_selector;
	logic [3:0] state_non_dram_dual_wait_selector;
	logic [3:0] state_dma_first_selector;
	logic [3:0] state_dma_wait_selector;
	logic [3:0] state_refresh_selector;

	assign state_idle_selector = 
		(input_idle_to_external ? `BusIfStates__external : 4'b0) | 
		(input_idle_to_non_dram_first ? `BusIfStates__non_dram_first : 4'b0) | 
		(input_idle_to_dma_first ? `BusIfStates__dma_first : 4'b0) | 
		(input_idle_to_first ? `BusIfStates__first : 4'b0) | 
		(input_idle_to_refresh ? `BusIfStates__refresh : 4'b0) | 
		(input_idle_to_external | input_idle_to_non_dram_first | input_idle_to_dma_first | input_idle_to_first | input_idle_to_refresh ? 4'b0 : `BusIfStates__idle);
	assign state_external_selector = (input_external_to_idle ? `BusIfStates__idle : 4'b0) | (input_external_to_idle_1 ? `BusIfStates__idle : 4'b0) | (input_external_to_idle | input_external_to_idle_1 ? 4'b0 : `BusIfStates__external);
	assign state_first_selector = (input_first_to_precharge ? `BusIfStates__precharge : 4'b0) | (input_first_to_middle ? `BusIfStates__middle : 4'b0) | (input_first_to_precharge | input_first_to_middle ? 4'b0 : `BusIfStates__first);
	assign state_middle_selector = (input_middle_to_precharge ? `BusIfStates__precharge : 4'b0) | (input_middle_to_precharge ? 4'b0 : `BusIfStates__middle);
	assign state_precharge_selector = (input_precharge_to_idle ? `BusIfStates__idle : 4'b0) | (input_precharge_to_idle ? 4'b0 : `BusIfStates__precharge);
	assign state_non_dram_first_selector = (input_non_dram_first_to_non_dram_wait ? `BusIfStates__non_dram_wait : 4'b0) | (input_non_dram_first_to_non_dram_wait ? 4'b0 : `BusIfStates__non_dram_first);
	assign state_non_dram_wait_selector = (input_non_dram_wait_to_non_dram_wait ? `BusIfStates__non_dram_wait : 4'b0) | (input_non_dram_wait_to_non_dram_dual ? `BusIfStates__non_dram_dual : 4'b0) | (input_non_dram_wait_to_idle ? `BusIfStates__idle : 4'b0) | (input_non_dram_wait_to_non_dram_wait | input_non_dram_wait_to_non_dram_dual | input_non_dram_wait_to_idle ? 4'b0 : `BusIfStates__non_dram_wait);
	assign state_non_dram_dual_selector = (input_non_dram_dual_to_non_dram_dual_first ? `BusIfStates__non_dram_dual_first : 4'b0) | (input_non_dram_dual_to_non_dram_dual_first ? 4'b0 : `BusIfStates__non_dram_dual);
	assign state_non_dram_dual_first_selector = (input_non_dram_dual_first_to_non_dram_dual_wait ? `BusIfStates__non_dram_dual_wait : 4'b0) | (input_non_dram_dual_first_to_non_dram_dual_wait ? 4'b0 : `BusIfStates__non_dram_dual_first);
	assign state_non_dram_dual_wait_selector = (input_non_dram_wait_to_non_dram_wait ? `BusIfStates__non_dram_dual_wait : 4'b0) | (input_non_dram_dual_wait_to_idle ? `BusIfStates__idle : 4'b0) | (input_non_dram_wait_to_non_dram_wait | input_non_dram_dual_wait_to_idle ? 4'b0 : `BusIfStates__non_dram_dual_wait);
	assign state_dma_first_selector = (input_dma_first_to_dma_wait ? `BusIfStates__dma_wait : 4'b0) | (input_dma_first_to_dma_wait ? 4'b0 : `BusIfStates__dma_first);
	assign state_dma_wait_selector = (input_non_dram_wait_to_non_dram_wait ? `BusIfStates__dma_wait : 4'b0) | (input_dma_wait_to_idle ? `BusIfStates__idle : 4'b0) | (input_non_dram_wait_to_non_dram_wait | input_dma_wait_to_idle ? 4'b0 : `BusIfStates__dma_wait);
	assign state_refresh_selector = (input_refresh_to_idle ? `BusIfStates__idle : 4'b0) | (input_refresh_to_idle ? 4'b0 : `BusIfStates__refresh);
	assign next_state = 
		(state == `BusIfStates__idle ? state_idle_selector : 4'b0) | 
		(state == `BusIfStates__external ? state_external_selector : 4'b0) | 
		(state == `BusIfStates__first ? state_first_selector : 4'b0) | 
		(state == `BusIfStates__middle ? state_middle_selector : 4'b0) | 
		(state == `BusIfStates__precharge ? state_precharge_selector : 4'b0) | 
		(state == `BusIfStates__non_dram_first ? state_non_dram_first_selector : 4'b0) | 
		(state == `BusIfStates__non_dram_wait ? state_non_dram_wait_selector : 4'b0) | 
		(state == `BusIfStates__non_dram_dual ? state_non_dram_dual_selector : 4'b0) | 
		(state == `BusIfStates__non_dram_dual_first ? state_non_dram_dual_first_selector : 4'b0) | 
		(state == `BusIfStates__non_dram_dual_wait ? state_non_dram_dual_wait_selector : 4'b0) | 
		(state == `BusIfStates__dma_first ? state_dma_first_selector : 4'b0) | 
		(state == `BusIfStates__dma_wait ? state_dma_wait_selector : 4'b0) | 
		(state == `BusIfStates__refresh ? state_refresh_selector : 4'b0) | 
		(state == `BusIfStates__idle | state == `BusIfStates__external | state == `BusIfStates__first | state == `BusIfStates__middle | state == `BusIfStates__precharge | state == `BusIfStates__non_dram_first | state == `BusIfStates__non_dram_wait | state == `BusIfStates__non_dram_dual | state == `BusIfStates__non_dram_dual_first | state == `BusIfStates__non_dram_dual_wait | state == `BusIfStates__dma_first | state == `BusIfStates__dma_wait | state == `BusIfStates__refresh ? 4'b0 : default_state);

endmodule


