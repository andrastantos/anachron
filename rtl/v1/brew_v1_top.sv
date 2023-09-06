////////////////////////////////////////////////////////////////////////////////
// Type definitions
////////////////////////////////////////////////////////////////////////////////
`define exceptions__exc_reset 7'h0
`define exceptions__exc_hwi 7'h10
`define exceptions__exc_swi_0 7'h20
`define exceptions__exc_swi_1 7'h21
`define exceptions__exc_swi_2 7'h22
`define exceptions__exc_swi_3 7'h23
`define exceptions__exc_swi_4 7'h24
`define exceptions__exc_swi_5 7'h25
`define exceptions__exc_swi_6 7'h26
`define exceptions__exc_swi_7 7'h27
`define exceptions__exc_unknown_inst 7'h30
`define exceptions__exc_type 7'h31
`define exceptions__exc_unaligned 7'h32
`define exceptions__exc_inst_av 7'h40
`define exceptions__exc_mem_av 7'h41


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
`define BusIfStates__non_dram_last 4'ha
`define BusIfStates__dma_first 4'hb
`define BusIfStates__dma_wait 4'hc
`define BusIfStates__refresh 4'hd


`define Ports__fetch_port 2'h0
`define Ports__mem_port 2'h1
`define Ports__dma_port 2'h2
`define Ports__refresh_port 2'h3


`define alu_ops__a_plus_b 3'h0
`define alu_ops__a_minus_b 3'h1
`define alu_ops__a_and_b 3'h2
`define alu_ops__a_or_b 3'h3
`define alu_ops__a_xor_b 3'h4
`define alu_ops__tpc 3'h5
`define alu_ops__pc_plus_b 3'h6


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
`define branch_ops__unknown 4'hd


`define op_class__alu 3'h0
`define op_class__mult 3'h1
`define op_class__shift 3'h2
`define op_class__branch 3'h3
`define op_class__ld_st 3'h4


`define ldst_ops__store 2'h0
`define ldst_ops__load 2'h1
`define ldst_ops__csr_store 2'h2
`define ldst_ops__csr_load 2'h3


`define shifter_ops__shll 2'h0
`define shifter_ops__shlr 2'h1
`define shifter_ops__shar 2'h2


`define InstBufferStates__idle 1'h0
`define InstBufferStates__request 1'h1


`define InstAssembleStates__have_0_fragments 2'h0
`define InstAssembleStates__need_1_fragments 2'h1
`define InstAssembleStates__need_2_fragments 2'h2
`define InstAssembleStates__have_all_fragments 2'h3





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
	logic cpu_task_mode_csr_if_psel;
	logic csr_cpu_task_mode_psel;
	logic cpu_scheduler_mode_csr_if_psel;
	logic csr_cpu_scheduler_mode_psel;
	logic csr_event_psel;
	logic bus_if_reg_if_psel;
	logic csr_bus_if_psel;
	logic dma_reg_if_psel;
	logic csr_dma_psel;
	logic [31:0] csr_if_prdata;
	logic csr_if_pready;
	logic event_write_strobe;
	logic [4:0] u31_output_port;
	logic [20:0] u33_output_port;
	logic [19:0] event_cnt_0;
	logic [4:0] u37_output_port;
	logic [20:0] u39_output_port;
	logic [19:0] event_cnt_1;
	logic [4:0] u43_output_port;
	logic [20:0] u45_output_port;
	logic [19:0] event_cnt_2;
	logic [4:0] u49_output_port;
	logic [20:0] u51_output_port;
	logic [19:0] event_cnt_3;
	logic [4:0] u55_output_port;
	logic [20:0] u57_output_port;
	logic [19:0] event_cnt_4;
	logic [4:0] u61_output_port;
	logic [20:0] u63_output_port;
	logic [19:0] event_cnt_5;
	logic [4:0] u67_output_port;
	logic [20:0] u69_output_port;
	logic [19:0] event_cnt_6;
	logic [4:0] u73_output_port;
	logic [20:0] u75_output_port;
	logic [19:0] event_cnt_7;
	logic [19:0] u78_output_port;
	logic [19:0] u81_output_port;
	logic event_enabled;
	logic [4:0] event_select_0;
	logic [4:0] event_select_1;
	logic [4:0] event_select_2;
	logic [4:0] event_select_3;
	logic [4:0] event_select_4;
	logic [4:0] event_select_5;
	logic [4:0] event_select_6;
	logic [4:0] event_select_7;
	logic [31:0] cpu_task_mode_csr_if_prdata;
	logic [31:0] cpu_scheduler_mode_csr_if_prdata;
	logic ecause_clear_pulse;
	logic [21:0] pmem_base;
	logic [21:0] pmem_limit;
	logic [21:0] dmem_base;
	logic [21:0] dmem_limit;
	logic cpu_task_mode_csr_if_pready;
	logic cpu_scheduler_mode_csr_if_pready;
	logic event_fetch_wait_on_bus;
	logic event_decode_wait_on_rf;
	logic event_execute;
	logic event_branch;
	logic event_load;
	logic event_store;
	logic [2:0] event_inst_word;
	logic [6:0] ecause;
	logic event_branch_taken;
	logic event_mem_wait_on_bus;
	logic [4:0] event_fetch_drop;
	logic fetch_to_bus_valid;
	logic [1:0] fetch_to_bus_byte_en;
	logic [15:0] fetch_to_bus_data;
	logic fetch_to_bus_read_not_write;
	logic event_fetch;
	logic [30:0] fetch_to_bus_addr;
	logic [31:0] eaddr;
	logic mem_to_bus_valid;
	logic mem_to_bus_read_not_write;
	logic [1:0] mem_to_bus_byte_en;
	logic [30:0] mem_to_bus_addr;
	logic [15:0] mem_to_bus_data;
	logic cpu_task_mode_csr_if_penable;
	logic cpu_scheduler_mode_csr_if_penable;
	logic csr_if_penable;
	logic bus_if_reg_if_penable;
	logic dma_reg_if_penable;
	logic csr_if_psel;
	logic cpu_task_mode_csr_if_pwrite;
	logic cpu_scheduler_mode_csr_if_pwrite;
	logic csr_if_pwrite;
	logic bus_if_reg_if_pwrite;
	logic dma_reg_if_pwrite;
	logic [15:0] csr_if_paddr;
	logic [31:0] cpu_task_mode_csr_if_pwdata;
	logic [31:0] cpu_scheduler_mode_csr_if_pwdata;
	logic [31:0] csr_if_pwdata;
	logic [31:0] bus_if_reg_if_pwdata;
	logic [31:0] dma_reg_if_pwdata;
	logic [3:0] dma_reg_if_paddr;
	logic [3:0] bus_if_reg_if_paddr;
	logic [3:0] cpu_task_mode_csr_if_paddr;
	logic [7:0] cpu_scheduler_mode_csr_if_paddr;
	logic [31:0] dma_reg_if_prdata;
	logic dma_interrupt;
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
	logic event_bus_idle;
	logic [15:0] bus_to_mem_data;
	logic bus_to_mem_valid;
	logic bus_to_fetch_valid;
	logic bus_to_dma_valid;
	logic bus_if_reg_if_pready;
	logic [31:0] bus_if_reg_if_prdata;
	logic [15:0] bus_to_fetch_data;
	logic [31:0] event_prdata;

	assign csr_dma_psel = csr_if_psel & (csr_if_paddr[15:8] == 2'h3);
	assign dma_reg_if_paddr = csr_if_paddr[3:0];
	assign csr_bus_if_psel = csr_if_psel & (csr_if_paddr[15:8] == 2'h2);
	assign bus_if_reg_if_paddr = csr_if_paddr[3:0];
	assign csr_cpu_task_mode_psel = csr_if_psel & (csr_if_paddr[15:8] == 1'h0);
	assign cpu_task_mode_csr_if_paddr = csr_if_paddr[3:0];
	assign csr_cpu_scheduler_mode_psel = csr_if_psel & (csr_if_paddr[15:8] == 8'h80);
	assign cpu_scheduler_mode_csr_if_paddr = csr_if_paddr[7:0];
	assign csr_event_psel = csr_if_psel & (csr_if_paddr[15:8] == 1'h1);
	assign csr_if_prdata = 
		(csr_dma_psel ? dma_reg_if_prdata : 32'b0) | 
		(csr_bus_if_psel ? bus_if_reg_if_prdata : 32'b0) | 
		(csr_event_psel ? event_prdata : 32'b0) | 
		(csr_cpu_task_mode_psel ? cpu_task_mode_csr_if_prdata : 32'b0) | 
		(csr_cpu_scheduler_mode_psel ? cpu_scheduler_mode_csr_if_prdata : 32'b0) ;
	assign csr_if_pready = 
		(csr_dma_psel ? dma_reg_if_pready : 1'b0) | 
		(csr_bus_if_psel ? bus_if_reg_if_pready : 1'b0) | 
		(csr_event_psel ? 1'h1 : 1'b0) | 
		(csr_cpu_task_mode_psel ? cpu_task_mode_csr_if_pready : 1'b0) | 
		(csr_cpu_scheduler_mode_psel ? cpu_scheduler_mode_csr_if_pready : 1'b0) ;
	always @(*) begin
		unique case (event_select_0)
			5'd0: u31_output_port = 1'h1;
			5'd1: u31_output_port = event_fetch_wait_on_bus;
			5'd2: u31_output_port = event_decode_wait_on_rf;
			5'd3: u31_output_port = event_mem_wait_on_bus;
			5'd4: u31_output_port = event_branch_taken;
			5'd5: u31_output_port = event_branch;
			5'd6: u31_output_port = event_load;
			5'd7: u31_output_port = event_store;
			5'd8: u31_output_port = event_load | event_store;
			5'd9: u31_output_port = event_execute;
			5'd10: u31_output_port = event_bus_idle;
			5'd11: u31_output_port = event_fetch;
			5'd12: u31_output_port = event_fetch_drop;
			5'd13: u31_output_port = event_inst_word;
			default: u31_output_port = 5'hx;
		endcase
	end
	always_ff @(posedge clk) event_cnt_0 <= rst ? 20'h0 : event_enabled ? u33_output_port[19:0] : event_cnt_0;
	always @(*) begin
		unique case (event_select_1)
			5'd0: u37_output_port = 1'h1;
			5'd1: u37_output_port = event_fetch_wait_on_bus;
			5'd2: u37_output_port = event_decode_wait_on_rf;
			5'd3: u37_output_port = event_mem_wait_on_bus;
			5'd4: u37_output_port = event_branch_taken;
			5'd5: u37_output_port = event_branch;
			5'd6: u37_output_port = event_load;
			5'd7: u37_output_port = event_store;
			5'd8: u37_output_port = event_load | event_store;
			5'd9: u37_output_port = event_execute;
			5'd10: u37_output_port = event_bus_idle;
			5'd11: u37_output_port = event_fetch;
			5'd12: u37_output_port = event_fetch_drop;
			5'd13: u37_output_port = event_inst_word;
			default: u37_output_port = 5'hx;
		endcase
	end
	always_ff @(posedge clk) event_cnt_1 <= rst ? 20'h0 : event_enabled ? u39_output_port[19:0] : event_cnt_1;
	always @(*) begin
		unique case (event_select_2)
			5'd0: u43_output_port = 1'h1;
			5'd1: u43_output_port = event_fetch_wait_on_bus;
			5'd2: u43_output_port = event_decode_wait_on_rf;
			5'd3: u43_output_port = event_mem_wait_on_bus;
			5'd4: u43_output_port = event_branch_taken;
			5'd5: u43_output_port = event_branch;
			5'd6: u43_output_port = event_load;
			5'd7: u43_output_port = event_store;
			5'd8: u43_output_port = event_load | event_store;
			5'd9: u43_output_port = event_execute;
			5'd10: u43_output_port = event_bus_idle;
			5'd11: u43_output_port = event_fetch;
			5'd12: u43_output_port = event_fetch_drop;
			5'd13: u43_output_port = event_inst_word;
			default: u43_output_port = 5'hx;
		endcase
	end
	always_ff @(posedge clk) event_cnt_2 <= rst ? 20'h0 : event_enabled ? u45_output_port[19:0] : event_cnt_2;
	always @(*) begin
		unique case (event_select_3)
			5'd0: u49_output_port = 1'h1;
			5'd1: u49_output_port = event_fetch_wait_on_bus;
			5'd2: u49_output_port = event_decode_wait_on_rf;
			5'd3: u49_output_port = event_mem_wait_on_bus;
			5'd4: u49_output_port = event_branch_taken;
			5'd5: u49_output_port = event_branch;
			5'd6: u49_output_port = event_load;
			5'd7: u49_output_port = event_store;
			5'd8: u49_output_port = event_load | event_store;
			5'd9: u49_output_port = event_execute;
			5'd10: u49_output_port = event_bus_idle;
			5'd11: u49_output_port = event_fetch;
			5'd12: u49_output_port = event_fetch_drop;
			5'd13: u49_output_port = event_inst_word;
			default: u49_output_port = 5'hx;
		endcase
	end
	always_ff @(posedge clk) event_cnt_3 <= rst ? 20'h0 : event_enabled ? u51_output_port[19:0] : event_cnt_3;
	always @(*) begin
		unique case (event_select_4)
			5'd0: u55_output_port = 1'h1;
			5'd1: u55_output_port = event_fetch_wait_on_bus;
			5'd2: u55_output_port = event_decode_wait_on_rf;
			5'd3: u55_output_port = event_mem_wait_on_bus;
			5'd4: u55_output_port = event_branch_taken;
			5'd5: u55_output_port = event_branch;
			5'd6: u55_output_port = event_load;
			5'd7: u55_output_port = event_store;
			5'd8: u55_output_port = event_load | event_store;
			5'd9: u55_output_port = event_execute;
			5'd10: u55_output_port = event_bus_idle;
			5'd11: u55_output_port = event_fetch;
			5'd12: u55_output_port = event_fetch_drop;
			5'd13: u55_output_port = event_inst_word;
			default: u55_output_port = 5'hx;
		endcase
	end
	always_ff @(posedge clk) event_cnt_4 <= rst ? 20'h0 : event_enabled ? u57_output_port[19:0] : event_cnt_4;
	always @(*) begin
		unique case (event_select_5)
			5'd0: u61_output_port = 1'h1;
			5'd1: u61_output_port = event_fetch_wait_on_bus;
			5'd2: u61_output_port = event_decode_wait_on_rf;
			5'd3: u61_output_port = event_mem_wait_on_bus;
			5'd4: u61_output_port = event_branch_taken;
			5'd5: u61_output_port = event_branch;
			5'd6: u61_output_port = event_load;
			5'd7: u61_output_port = event_store;
			5'd8: u61_output_port = event_load | event_store;
			5'd9: u61_output_port = event_execute;
			5'd10: u61_output_port = event_bus_idle;
			5'd11: u61_output_port = event_fetch;
			5'd12: u61_output_port = event_fetch_drop;
			5'd13: u61_output_port = event_inst_word;
			default: u61_output_port = 5'hx;
		endcase
	end
	always_ff @(posedge clk) event_cnt_5 <= rst ? 20'h0 : event_enabled ? u63_output_port[19:0] : event_cnt_5;
	always @(*) begin
		unique case (event_select_6)
			5'd0: u67_output_port = 1'h1;
			5'd1: u67_output_port = event_fetch_wait_on_bus;
			5'd2: u67_output_port = event_decode_wait_on_rf;
			5'd3: u67_output_port = event_mem_wait_on_bus;
			5'd4: u67_output_port = event_branch_taken;
			5'd5: u67_output_port = event_branch;
			5'd6: u67_output_port = event_load;
			5'd7: u67_output_port = event_store;
			5'd8: u67_output_port = event_load | event_store;
			5'd9: u67_output_port = event_execute;
			5'd10: u67_output_port = event_bus_idle;
			5'd11: u67_output_port = event_fetch;
			5'd12: u67_output_port = event_fetch_drop;
			5'd13: u67_output_port = event_inst_word;
			default: u67_output_port = 5'hx;
		endcase
	end
	always_ff @(posedge clk) event_cnt_6 <= rst ? 20'h0 : event_enabled ? u69_output_port[19:0] : event_cnt_6;
	always @(*) begin
		unique case (event_select_7)
			5'd0: u73_output_port = 1'h1;
			5'd1: u73_output_port = event_fetch_wait_on_bus;
			5'd2: u73_output_port = event_decode_wait_on_rf;
			5'd3: u73_output_port = event_mem_wait_on_bus;
			5'd4: u73_output_port = event_branch_taken;
			5'd5: u73_output_port = event_branch;
			5'd6: u73_output_port = event_load;
			5'd7: u73_output_port = event_store;
			5'd8: u73_output_port = event_load | event_store;
			5'd9: u73_output_port = event_execute;
			5'd10: u73_output_port = event_bus_idle;
			5'd11: u73_output_port = event_fetch;
			5'd12: u73_output_port = event_fetch_drop;
			5'd13: u73_output_port = event_inst_word;
			default: u73_output_port = 5'hx;
		endcase
	end
	always_ff @(posedge clk) event_cnt_7 <= rst ? 20'h0 : event_enabled ? u75_output_port[19:0] : event_cnt_7;
	always @(*) begin
		unique case (csr_if_paddr[4:0])
			5'd0: u78_output_port = event_enabled;
			5'd1: u78_output_port = 1'h0;
			5'd2: u78_output_port = event_select_0;
			5'd3: u78_output_port = event_cnt_0;
			5'd4: u78_output_port = event_select_1;
			5'd5: u78_output_port = event_cnt_1;
			5'd6: u78_output_port = event_select_2;
			5'd7: u78_output_port = event_cnt_2;
			5'd8: u78_output_port = event_select_3;
			5'd9: u78_output_port = event_cnt_3;
			5'd10: u78_output_port = event_select_4;
			5'd11: u78_output_port = event_cnt_4;
			5'd12: u78_output_port = event_select_5;
			5'd13: u78_output_port = event_cnt_5;
			5'd14: u78_output_port = event_select_6;
			5'd15: u78_output_port = event_cnt_6;
			5'd16: u78_output_port = event_select_7;
			5'd17: u78_output_port = event_cnt_7;
			default: u78_output_port = 20'hx;
		endcase
	end
	always_ff @(posedge clk) u81_output_port <= rst ? 20'h0 : u78_output_port;
	assign event_write_strobe = csr_event_psel & dma_reg_if_pwrite & dma_reg_if_penable;
	always_ff @(posedge clk) event_enabled <= rst ? 1'h0 : (csr_if_paddr[4:0] == 1'h0) & event_write_strobe ? dma_reg_if_pwdata[0] : event_enabled;
	always_ff @(posedge clk) event_select_0 <= rst ? 5'h0 : (csr_if_paddr[4:0] == 2'h2) & event_write_strobe ? dma_reg_if_pwdata[4:0] : event_select_0;
	always_ff @(posedge clk) event_select_1 <= rst ? 5'h0 : (csr_if_paddr[4:0] == 3'h4) & event_write_strobe ? dma_reg_if_pwdata[4:0] : event_select_1;
	always_ff @(posedge clk) event_select_2 <= rst ? 5'h0 : (csr_if_paddr[4:0] == 3'h6) & event_write_strobe ? dma_reg_if_pwdata[4:0] : event_select_2;
	always_ff @(posedge clk) event_select_3 <= rst ? 5'h0 : (csr_if_paddr[4:0] == 4'h8) & event_write_strobe ? dma_reg_if_pwdata[4:0] : event_select_3;
	always_ff @(posedge clk) event_select_4 <= rst ? 5'h0 : (csr_if_paddr[4:0] == 4'ha) & event_write_strobe ? dma_reg_if_pwdata[4:0] : event_select_4;
	always_ff @(posedge clk) event_select_5 <= rst ? 5'h0 : (csr_if_paddr[4:0] == 4'hc) & event_write_strobe ? dma_reg_if_pwdata[4:0] : event_select_5;
	always_ff @(posedge clk) event_select_6 <= rst ? 5'h0 : (csr_if_paddr[4:0] == 4'he) & event_write_strobe ? dma_reg_if_pwdata[4:0] : event_select_6;
	always_ff @(posedge clk) event_select_7 <= rst ? 5'h0 : (csr_if_paddr[4:0] == 5'h10) & event_write_strobe ? dma_reg_if_pwdata[4:0] : event_select_7;
	always_ff @(posedge clk) cpu_task_mode_csr_if_prdata <= rst ? 32'h0 : ((cpu_task_mode_csr_if_paddr[0] == 1'h0) ? 32'h0 : 32'b0) | ((cpu_task_mode_csr_if_paddr[0] == 1'h1) ? 32'h0 : 32'b0) ;
	always_ff @(posedge clk) cpu_scheduler_mode_csr_if_prdata <= rst ? 32'h0 : 
		((cpu_scheduler_mode_csr_if_paddr[7:0] == 1'h0) ? ecause : 32'b0) | 
		((cpu_scheduler_mode_csr_if_paddr[7:0] == 1'h1) ? eaddr : 32'b0) | 
		((cpu_scheduler_mode_csr_if_paddr[7:0] == 8'h80) ? ({pmem_base, 10'h0}) : 32'b0) | 
		((cpu_scheduler_mode_csr_if_paddr[7:0] == 8'h81) ? ({pmem_limit, 10'h0}) : 32'b0) | 
		((cpu_scheduler_mode_csr_if_paddr[7:0] == 8'h82) ? ({dmem_base, 10'h0}) : 32'b0) | 
		((cpu_scheduler_mode_csr_if_paddr[7:0] == 8'h83) ? ({dmem_limit, 10'h0}) : 32'b0) ;
	assign ecause_clear_pulse = csr_cpu_scheduler_mode_psel & dma_reg_if_penable &  ~ dma_reg_if_pwrite & cpu_scheduler_mode_csr_if_pready & (cpu_scheduler_mode_csr_if_paddr[7:0] == 1'h0);
	always_ff @(posedge clk) pmem_base <= rst ? 22'h0 : csr_cpu_scheduler_mode_psel & dma_reg_if_penable & dma_reg_if_pwrite & cpu_scheduler_mode_csr_if_pready & (cpu_scheduler_mode_csr_if_paddr[7:0] == 8'h80) ? dma_reg_if_pwdata[31:10] : pmem_base;
	always_ff @(posedge clk) pmem_limit <= rst ? 22'h0 : csr_cpu_scheduler_mode_psel & dma_reg_if_penable & dma_reg_if_pwrite & cpu_scheduler_mode_csr_if_pready & (cpu_scheduler_mode_csr_if_paddr[7:0] == 8'h81) ? dma_reg_if_pwdata[31:10] : pmem_limit;
	always_ff @(posedge clk) dmem_base <= rst ? 22'h0 : csr_cpu_scheduler_mode_psel & dma_reg_if_penable & dma_reg_if_pwrite & cpu_scheduler_mode_csr_if_pready & (cpu_scheduler_mode_csr_if_paddr[7:0] == 8'h82) ? dma_reg_if_pwdata[31:10] : dmem_base;
	always_ff @(posedge clk) dmem_limit <= rst ? 22'h0 : csr_cpu_scheduler_mode_psel & dma_reg_if_penable & dma_reg_if_pwrite & cpu_scheduler_mode_csr_if_pready & (cpu_scheduler_mode_csr_if_paddr[7:0] == 8'h83) ? dma_reg_if_pwdata[31:10] : dmem_limit;
	assign cpu_task_mode_csr_if_pready = 1'h1;
	assign cpu_scheduler_mode_csr_if_pready = 1'h1;
	assign event_prdata = u81_output_port;

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
		.reg_if_pready(bus_if_reg_if_pready),
		.reg_if_psel(csr_bus_if_psel),
		.reg_if_pwrite(dma_reg_if_pwrite),
		.reg_if_pwdata(dma_reg_if_pwdata),
		.reg_if_prdata(bus_if_reg_if_prdata),

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
		.dram_tc(dram_tc),

		.event_bus_idle(event_bus_idle)
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
		.reg_if_pready(dma_reg_if_pready),
		.reg_if_psel(csr_dma_psel),
		.reg_if_pwrite(dma_reg_if_pwrite),
		.reg_if_pwdata(dma_reg_if_pwdata),
		.reg_if_prdata(dma_reg_if_prdata),

		.drq(drq),
		.interrupt(dma_interrupt)
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
		.csr_if_pready(csr_if_pready),
		.csr_if_psel(csr_if_psel),
		.csr_if_pwrite(dma_reg_if_pwrite),
		.csr_if_pwdata(dma_reg_if_pwdata),
		.csr_if_prdata(csr_if_prdata),

		.ecause_clear_pulse(ecause_clear_pulse),
		.ecause(ecause),
		.eaddr(eaddr),
		.pmem_base(pmem_base),
		.pmem_limit(pmem_limit),
		.dmem_base(dmem_base),
		.dmem_limit(dmem_limit),
		.interrupt(u_output_port),
		.event_fetch_wait_on_bus(event_fetch_wait_on_bus),
		.event_decode_wait_on_rf(event_decode_wait_on_rf),
		.event_mem_wait_on_bus(event_mem_wait_on_bus),
		.event_branch_taken(event_branch_taken),
		.event_branch(event_branch),
		.event_load(event_load),
		.event_store(event_store),
		.event_execute(event_execute),
		.event_fetch(event_fetch),
		.event_fetch_drop(event_fetch_drop),
		.event_inst_word(event_inst_word)
	);

	assign u_output_port =  ~ n_int;
	assign cpu_task_mode_csr_if_psel = csr_cpu_task_mode_psel;
	assign cpu_scheduler_mode_csr_if_psel = csr_cpu_scheduler_mode_psel;
	assign bus_if_reg_if_psel = csr_bus_if_psel;
	assign dma_reg_if_psel = csr_dma_psel;
	assign u33_output_port = event_cnt_0 + u31_output_port + 21'b0;
	assign u39_output_port = event_cnt_1 + u37_output_port + 21'b0;
	assign u45_output_port = event_cnt_2 + u43_output_port + 21'b0;
	assign u51_output_port = event_cnt_3 + u49_output_port + 21'b0;
	assign u57_output_port = event_cnt_4 + u55_output_port + 21'b0;
	assign u63_output_port = event_cnt_5 + u61_output_port + 21'b0;
	assign u69_output_port = event_cnt_6 + u67_output_port + 21'b0;
	assign u75_output_port = event_cnt_7 + u73_output_port + 21'b0;
	assign cpu_task_mode_csr_if_penable = dma_reg_if_penable;
	assign cpu_scheduler_mode_csr_if_penable = dma_reg_if_penable;
	assign csr_if_penable = dma_reg_if_penable;
	assign bus_if_reg_if_penable = dma_reg_if_penable;
	assign cpu_task_mode_csr_if_pwrite = dma_reg_if_pwrite;
	assign cpu_scheduler_mode_csr_if_pwrite = dma_reg_if_pwrite;
	assign csr_if_pwrite = dma_reg_if_pwrite;
	assign bus_if_reg_if_pwrite = dma_reg_if_pwrite;
	assign cpu_task_mode_csr_if_pwdata = dma_reg_if_pwdata;
	assign cpu_scheduler_mode_csr_if_pwdata = dma_reg_if_pwdata;
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

	output logic [15:0] csr_if_paddr,
	output logic csr_if_penable,
	input logic csr_if_pready,
	output logic csr_if_psel,
	output logic csr_if_pwrite,
	output logic [31:0] csr_if_pwdata,
	input logic [31:0] csr_if_prdata,

	input logic ecause_clear_pulse,
	output logic [6:0] ecause,
	output logic [31:0] eaddr,
	input logic [21:0] pmem_base,
	input logic [21:0] pmem_limit,
	input logic [21:0] dmem_base,
	input logic [21:0] dmem_limit,
	input logic interrupt,
	output logic event_fetch_wait_on_bus,
	output logic event_decode_wait_on_rf,
	output logic event_mem_wait_on_bus,
	output logic event_branch_taken,
	output logic event_branch,
	output logic event_load,
	output logic event_store,
	output logic event_execute,
	output logic event_fetch,
	output logic [4:0] event_fetch_drop,
	output logic [2:0] event_inst_word
);

	logic [6:0] u4_output_port;
	logic will_execute;
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
	logic [1:0] decode_to_exec_ldst_op;
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
	logic fetch_stage_break_burst;
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
	logic [6:0] execute_stage_ecause_out;
	logic [31:0] rf_write_data;
	logic [3:0] rf_write_addr;
	logic rf_write_data_en;
	logic rf_write_valid;
	logic [31:0] rf_rsp_read1_data;
	logic [31:0] rf_rsp_read2_data;
	logic rf_req_ready;
	logic rf_rsp_valid;

	assign event_fetch_wait_on_bus = fetch_to_bus_valid &  ~ fetch_to_bus_ready;
	assign event_decode_wait_on_rf = rf_req_valid &  ~ rf_req_ready;
	assign will_execute = decode_to_exec_ready & decode_to_exec_valid &  ~ decode_to_exec_fetch_av &  ~ execute_stage_do_branch;
	assign event_branch = will_execute & (decode_to_exec_exec_unit == `op_class__branch);
	assign event_load = will_execute & (decode_to_exec_exec_unit == `op_class__ld_st) & (decode_to_exec_ldst_op == `ldst_ops__load);
	assign event_store = will_execute & (decode_to_exec_exec_unit == `op_class__ld_st) & (decode_to_exec_ldst_op == `ldst_ops__store);
	assign event_inst_word = will_execute ? decode_to_exec_inst_len + 1'h1 + 3'b0 : 1'h0;
	always_ff @(posedge clk) spc <= rst ? 31'h0 : execute_stage_spc_out;
	always_ff @(posedge clk) tpc <= rst ? 31'h0 : execute_stage_tpc_out;
	always_ff @(posedge clk) task_mode <= rst ? 1'h0 : execute_stage_task_mode_out;
	always_ff @(posedge clk) ecause <= rst ? 7'h0 : execute_stage_ecause_out;
	always_ff @(posedge clk) do_branch <= rst ? 1'h0 : execute_stage_do_branch;
	assign event_mem_wait_on_bus = mem_to_bus_valid &  ~ mem_to_bus_ready;

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
		.do_branch(do_branch),
		.break_burst(fetch_stage_break_burst),
		.event_fetch(event_fetch),
		.event_dropped(event_fetch_drop)
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

		.do_branch(do_branch),
		.break_fetch_burst(fetch_stage_break_burst)
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
		.csr_if_pready(csr_if_pready),
		.csr_if_psel(csr_if_psel),
		.csr_if_pwrite(csr_if_pwrite),
		.csr_if_pwdata(csr_if_pwdata),
		.csr_if_prdata(csr_if_prdata),

		.mem_base(dmem_base),
		.mem_limit(dmem_limit),
		.spc_in(spc),
		.spc_out(execute_stage_spc_out),
		.tpc_in(tpc),
		.tpc_out(execute_stage_tpc_out),
		.task_mode_in(task_mode),
		.task_mode_out(execute_stage_task_mode_out),
		.ecause_in(u4_output_port),
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

	assign u4_output_port = ecause_clear_pulse ? `exceptions__exc_reset : ecause;
	assign event_execute = will_execute;
	assign event_branch_taken = do_branch;
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
	logic u51_output_port;
	logic rsv_registered;
	logic u54_output_port;
	logic wait_for_read1;
	logic u80_output_port;
	logic wait_for_read2;
	logic u106_output_port;
	logic wait_for_rsv_raw;
	logic wait_for_rsv;
	logic wait_for_some;
	logic u136_output_port;
	logic wait_for_write;
	logic rsv_set_valid;
	logic rsv_clr_valid;
	logic u158_output_port;
	logic u172_output_port;
	logic u186_output_port;
	logic u200_output_port;
	logic u214_output_port;
	logic u228_output_port;
	logic u242_output_port;
	logic u256_output_port;
	logic u270_output_port;
	logic u284_output_port;
	logic u298_output_port;
	logic u312_output_port;
	logic u326_output_port;
	logic u340_output_port;
	logic u354_output_port;
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
	always_ff @(posedge clk) u37_output_port <= rst ? 1'h0 : (write_addr == read1_addr) & write_valid & write_data_en;
	assign read_rsp_read1_data = u37_output_port ? write_data_d : mem1_port2_data_out;
	assign read2_addr = req_advance ? read_req_read2_addr : u22_output_port;
	always_ff @(posedge clk) u42_output_port <= rst ? 1'h0 : (write_addr == read2_addr) & write_valid & write_data_en;
	assign read_rsp_read2_data = u42_output_port ? write_data_d : mem2_port2_data_out;
	always_ff @(posedge clk) u51_output_port <= rst ? 1'h0 : rsv_set_valid &  ~ rsv_registered ?  ~ wait_for_rsv_raw : req_advance ? 1'h0 : rsv_registered;
	assign rsv_registered =  ~ req_advance & u51_output_port;
	always @(*) begin
		unique case (read1_addr)
			4'd0: u54_output_port = rsv_board[0];
			4'd1: u54_output_port = rsv_board[1];
			4'd2: u54_output_port = rsv_board[2];
			4'd3: u54_output_port = rsv_board[3];
			4'd4: u54_output_port = rsv_board[4];
			4'd5: u54_output_port = rsv_board[5];
			4'd6: u54_output_port = rsv_board[6];
			4'd7: u54_output_port = rsv_board[7];
			4'd8: u54_output_port = rsv_board[8];
			4'd9: u54_output_port = rsv_board[9];
			4'd10: u54_output_port = rsv_board[10];
			4'd11: u54_output_port = rsv_board[11];
			4'd12: u54_output_port = rsv_board[12];
			4'd13: u54_output_port = rsv_board[13];
			4'd14: u54_output_port = rsv_board[14];
			default: u54_output_port = 1'hx;
		endcase
	end
	assign rsv_addr = req_advance ? read_req_rsv_addr : u29_output_port;
	always @(*) begin
		unique case (read2_addr)
			4'd0: u80_output_port = rsv_board[0];
			4'd1: u80_output_port = rsv_board[1];
			4'd2: u80_output_port = rsv_board[2];
			4'd3: u80_output_port = rsv_board[3];
			4'd4: u80_output_port = rsv_board[4];
			4'd5: u80_output_port = rsv_board[5];
			4'd6: u80_output_port = rsv_board[6];
			4'd7: u80_output_port = rsv_board[7];
			4'd8: u80_output_port = rsv_board[8];
			4'd9: u80_output_port = rsv_board[9];
			4'd10: u80_output_port = rsv_board[10];
			4'd11: u80_output_port = rsv_board[11];
			4'd12: u80_output_port = rsv_board[12];
			4'd13: u80_output_port = rsv_board[13];
			4'd14: u80_output_port = rsv_board[14];
			default: u80_output_port = 1'hx;
		endcase
	end
	always @(*) begin
		unique case (rsv_addr)
			4'd0: u106_output_port = rsv_board[0];
			4'd1: u106_output_port = rsv_board[1];
			4'd2: u106_output_port = rsv_board[2];
			4'd3: u106_output_port = rsv_board[3];
			4'd4: u106_output_port = rsv_board[4];
			4'd5: u106_output_port = rsv_board[5];
			4'd6: u106_output_port = rsv_board[6];
			4'd7: u106_output_port = rsv_board[7];
			4'd8: u106_output_port = rsv_board[8];
			4'd9: u106_output_port = rsv_board[9];
			4'd10: u106_output_port = rsv_board[10];
			4'd11: u106_output_port = rsv_board[11];
			4'd12: u106_output_port = rsv_board[12];
			4'd13: u106_output_port = rsv_board[13];
			4'd14: u106_output_port = rsv_board[14];
			default: u106_output_port = 1'hx;
		endcase
	end
	assign wait_for_rsv_raw = outstanding_req & rsv_valid & u106_output_port &  ~ ((write_addr == rsv_addr) & write_valid);
	assign wait_for_read1 = outstanding_req & read1_valid & u54_output_port &  ~ ((write_addr == read1_addr) & write_valid) & ((read1_addr != rsv_addr) |  ~ rsv_registered);
	assign wait_for_read2 = outstanding_req & read2_valid & u80_output_port &  ~ ((write_addr == read2_addr) & write_valid) & ((read2_addr != rsv_addr) |  ~ rsv_registered);
	assign wait_for_rsv = wait_for_rsv_raw &  ~ rsv_registered;
	assign wait_for_some = wait_for_read1 | wait_for_read2 | wait_for_rsv;
	always_ff @(posedge clk) u136_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : req_advance | write_valid ? wait_for_some : wait_for_write;
	assign wait_for_write = req_advance | write_valid ? wait_for_some : u136_output_port;
	assign rsv_set_valid = rsv_valid &  ~ wait_for_write & outstanding_req;
	assign rsv_clr_valid = write_valid & ( ~ wait_for_rsv | (rsv_addr != write_addr));
	always_ff @(posedge clk) u158_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 1'h0) ? 1'h1 : rsv_clr_valid & (write_addr == 1'h0) ? 1'h0 : rsv_board[0];
	always_ff @(posedge clk) u172_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 1'h1) ? 1'h1 : rsv_clr_valid & (write_addr == 1'h1) ? 1'h0 : rsv_board[1];
	always_ff @(posedge clk) u186_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 2'h2) ? 1'h1 : rsv_clr_valid & (write_addr == 2'h2) ? 1'h0 : rsv_board[2];
	always_ff @(posedge clk) u200_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 2'h3) ? 1'h1 : rsv_clr_valid & (write_addr == 2'h3) ? 1'h0 : rsv_board[3];
	always_ff @(posedge clk) u214_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 3'h4) ? 1'h1 : rsv_clr_valid & (write_addr == 3'h4) ? 1'h0 : rsv_board[4];
	always_ff @(posedge clk) u228_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 3'h5) ? 1'h1 : rsv_clr_valid & (write_addr == 3'h5) ? 1'h0 : rsv_board[5];
	always_ff @(posedge clk) u242_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 3'h6) ? 1'h1 : rsv_clr_valid & (write_addr == 3'h6) ? 1'h0 : rsv_board[6];
	always_ff @(posedge clk) u256_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 3'h7) ? 1'h1 : rsv_clr_valid & (write_addr == 3'h7) ? 1'h0 : rsv_board[7];
	always_ff @(posedge clk) u270_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 4'h8) ? 1'h1 : rsv_clr_valid & (write_addr == 4'h8) ? 1'h0 : rsv_board[8];
	always_ff @(posedge clk) u284_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 4'h9) ? 1'h1 : rsv_clr_valid & (write_addr == 4'h9) ? 1'h0 : rsv_board[9];
	always_ff @(posedge clk) u298_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 4'ha) ? 1'h1 : rsv_clr_valid & (write_addr == 4'ha) ? 1'h0 : rsv_board[10];
	always_ff @(posedge clk) u312_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 4'hb) ? 1'h1 : rsv_clr_valid & (write_addr == 4'hb) ? 1'h0 : rsv_board[11];
	always_ff @(posedge clk) u326_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 4'hc) ? 1'h1 : rsv_clr_valid & (write_addr == 4'hc) ? 1'h0 : rsv_board[12];
	always_ff @(posedge clk) u340_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 4'hd) ? 1'h1 : rsv_clr_valid & (write_addr == 4'hd) ? 1'h0 : rsv_board[13];
	always_ff @(posedge clk) u354_output_port <= rst ? 1'h0 : do_branch ? 1'h0 : rsv_set_valid & (rsv_addr == 4'he) ? 1'h1 : rsv_clr_valid & (write_addr == 4'he) ? 1'h0 : rsv_board[14];
	always_ff @(posedge clk) out_buf_full <= rst ? 1'h0 : do_branch ? 1'h0 : req_advance ? 1'h1 : rsp_advance ? 1'h0 : out_buf_full;
	always_ff @(posedge clk) wait_for_write_d <= rst ? 1'h0 : do_branch ? 1'h0 : wait_for_write;
	assign read_req_ready =  ~ wait_for_write_d & (read_rsp_ready |  ~ out_buf_full);
	assign read_rsp_valid =  ~ wait_for_write_d & out_buf_full;
	assign rsv_board = {u354_output_port, u340_output_port, u326_output_port, u312_output_port, u298_output_port, u284_output_port, u270_output_port, u256_output_port, u242_output_port, u228_output_port, u214_output_port, u200_output_port, u186_output_port, u172_output_port, u158_output_port};

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

	always @(posedge port1_clk) begin
		port2_data_out <= mem[port2_addr];
	end


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

	always @(posedge port1_clk) begin
		port2_data_out <= mem[port2_addr];
	end


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
	input logic [1:0] input_port_ldst_op,
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

	output logic [15:0] csr_if_paddr,
	output logic csr_if_penable,
	input logic csr_if_pready,
	output logic csr_if_psel,
	output logic csr_if_pwrite,
	output logic [31:0] csr_if_pwdata,
	input logic [31:0] csr_if_prdata,

	input logic [21:0] mem_base,
	input logic [21:0] mem_limit,
	input logic [30:0] spc_in,
	output logic [30:0] spc_out,
	input logic [30:0] tpc_in,
	output logic [30:0] tpc_out,
	input logic task_mode_in,
	output logic task_mode_out,
	input logic [6:0] ecause_in,
	output logic [6:0] ecause_out,
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
	logic [31:0] s1_ldst_output_eff_addr;
	logic s1_ldst_output_is_csr;
	logic mem_input_is_csr;
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
	logic [1:0] s1_ldst_op;
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
	logic [31:0] s1_eff_addr;
	logic [30:0] s1_pc;
	logic [30:0] s2_pc;
	logic block_mem;
	logic mem_input_valid;
	logic stage_2_ready;
	logic stage_2_valid;
	logic u82_output_port;
	logic u85_output_port;
	logic stage_2_reg_en;
	logic branch_input_is_branch_insn;
	logic mem_input_read_not_write;
	logic [31:0] result;
	logic s2_result_reg_addr_valid;
	logic u107_output_port;
	logic [2:0] s2_exec_unit;
	logic [1:0] s2_ldst_op;
	logic [15:0] u114_output_port;
	logic [15:0] u119_output_port;
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
	logic [31:0] ldst_output_phy_addr;
	logic ldst_output_mem_av;
	logic ldst_output_mem_unaligned;
	logic ldst_output_is_csr;
	logic [31:0] ldst_output_eff_addr;
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
	logic [6:0] branch_output_ecause;
	logic branch_output_is_exception_or_interrupt;
	logic mem_input_ready;
	logic s2_mem_output_valid;
	logic [15:0] s2_mem_output_data_l;
	logic [15:0] s2_mem_output_data_h;

	always_ff @(posedge clk) s1_was_branch <= rst ? 1'h0 : do_branch;
	always_ff @(posedge clk) multi_cycle_exec_lockout <= rst ? 1'h0 : input_port_ready & input_port_valid & (input_port_exec_unit == `op_class__mult) &  ~ input_port_fetch_av;
	assign input_port_ready =  ~ multi_cycle_exec_lockout &  ~ s1_was_branch & stage_1_fsm_input_ready;
	assign stage_1_reg_en =  ~ multi_cycle_exec_lockout &  ~ s1_was_branch & stage_1_fsm_out_reg_en;
	assign pc = task_mode_in ? tpc_in : spc_in;
	always_ff @(posedge clk) branch_input_f_carry <= rst ? 1'h0 : stage_1_reg_en ? alu_output_f_carry : branch_input_f_carry;
	always_ff @(posedge clk) branch_input_f_overflow <= rst ? 1'h0 : stage_1_reg_en ? alu_output_f_overflow : branch_input_f_overflow;
	always_ff @(posedge clk) branch_input_f_sign <= rst ? 1'h0 : stage_1_reg_en ? alu_output_f_sign : branch_input_f_sign;
	always_ff @(posedge clk) branch_input_f_zero <= rst ? 1'h0 : stage_1_reg_en ? alu_output_f_zero : branch_input_f_zero;
	always_ff @(posedge clk) s1_alu_output_result <= rst ? 32'h0 : stage_1_reg_en ? alu_output_result : s1_alu_output_result;
	always_ff @(posedge clk) s1_ldst_output_eff_addr <= rst ? 32'h0 : stage_1_reg_en ? ldst_output_eff_addr : s1_ldst_output_eff_addr;
	always_ff @(posedge clk) mem_input_is_csr <= rst ? 1'h0 : stage_1_reg_en ? ldst_output_is_csr : mem_input_is_csr;
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
	assign mem_input_valid = stage_1_valid &  ~ block_mem & (s1_exec_unit == `op_class__ld_st);
	assign stage_2_ready = (s1_exec_unit == `op_class__ld_st) &  ~ block_mem ? mem_input_ready : stage_2_fsm_input_ready;
	always_ff @(posedge clk) s2_was_branch <= rst ? 1'h0 : s1_was_branch;
	assign stage_2_valid = ((s2_exec_unit == `op_class__ld_st) &  ~ block_mem ? s2_mem_output_valid : stage_2_fsm_output_valid) &  ~ s2_was_branch;
	always_ff @(posedge clk) u85_output_port <= rst ? 1'h0 : do_branch;
	assign stage_2_reg_en = stage_1_valid & stage_2_ready &  ~ u85_output_port;
	always_ff @(posedge clk) s1_branch_op <= rst ? 4'h0 : stage_1_reg_en ? input_port_branch_op : s1_branch_op;
	always_ff @(posedge clk) s1_op_a <= rst ? 32'h0 : stage_1_reg_en ? input_port_op_a : s1_op_a;
	always_ff @(posedge clk) s1_op_b <= rst ? 32'h0 : stage_1_reg_en ? input_port_op_b : s1_op_b;
	assign branch_input_is_branch_insn = s1_exec_unit == `op_class__branch;
	always_ff @(posedge clk) s1_ldst_op <= rst ? 2'h0 : stage_1_reg_en ? input_port_ldst_op : s1_ldst_op;
	assign mem_input_read_not_write = (s1_exec_unit == `op_class__ld_st) & ((s1_ldst_op == `ldst_ops__load) | (s1_ldst_op == `ldst_ops__csr_load));
	always_ff @(posedge clk) s1_mem_access_len <= rst ? 2'h0 : stage_1_reg_en ? input_port_mem_access_len : s1_mem_access_len;
	always_ff @(posedge clk) s1_result_reg_addr_valid <= rst ? 1'h0 : stage_1_reg_en ? input_port_result_reg_addr_valid : s1_result_reg_addr_valid;
	always_ff @(posedge clk) s2_result_reg_addr_valid <= rst ? 1'h0 : stage_2_reg_en ? s1_result_reg_addr_valid : s2_result_reg_addr_valid;
	always_ff @(posedge clk) u107_output_port <= rst ? 1'h0 : stage_2_reg_en;
	assign output_port_valid = stage_2_valid & s2_result_reg_addr_valid & (u107_output_port | s2_mem_output_valid);
	always_ff @(posedge clk) s2_exec_unit <= rst ? 3'h0 : stage_2_reg_en ? s1_exec_unit : s2_exec_unit;
	always_ff @(posedge clk) s2_ldst_op <= rst ? 2'h0 : stage_2_reg_en ? s1_ldst_op : s2_ldst_op;
	assign result = ((s1_exec_unit == `op_class__alu) ? s1_alu_output_result : 32'b0) | ((s1_exec_unit == `op_class__mult) ? mult_output_result : 32'b0) | ((s1_exec_unit == `op_class__shift) ? s1_shifter_output_result : 32'b0) ;
	always_ff @(posedge clk) u114_output_port <= rst ? 16'h0 : stage_2_reg_en ? result[15:0] : u114_output_port;
	assign output_port_data_l = s2_exec_unit == `op_class__ld_st ? s2_mem_output_data_l : u114_output_port;
	always_ff @(posedge clk) u119_output_port <= rst ? 16'h0 : stage_2_reg_en ? result[31:16] : u119_output_port;
	assign output_port_data_h = s2_exec_unit == `op_class__ld_st ? s2_mem_output_data_h : u119_output_port;
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
	assign tpc_out = s1_was_branch ? tpc_in : stage_2_reg_en & branch_output_tpc_changed ? branch_output_tpc : straight_tpc_out;
	assign straight_spc_out = stage_1_reg_en ?  ~ (task_mode_out | task_mode_in) ? branch_target_output_straight_addr : spc_in : spc_in;
	assign spc_out = s1_was_branch ? spc_in : stage_2_reg_en & branch_output_spc_changed ? branch_output_spc : straight_spc_out;
	assign task_mode_out = s1_was_branch ? task_mode_in : stage_2_reg_en & branch_output_task_mode_changed ? branch_output_task_mode : task_mode_in;
	assign ecause_out = stage_2_reg_en &  ~ s1_was_branch ? branch_output_is_exception_or_interrupt ? branch_output_ecause : ecause_in : ecause_in;
	assign s1_pc = s1_task_mode ? s1_tpc : s1_spc;
	always_ff @(posedge clk) s1_eff_addr <= rst ? 32'h0 : stage_1_reg_en ? ldst_output_eff_addr : s1_eff_addr;
	always_ff @(posedge clk) eaddr_out <= rst ? 32'h0 : branch_output_is_exception ? s1_fetch_av | (s1_exec_unit == `op_class__branch) & (s1_branch_op == `branch_ops__swi) ? ({s1_pc, 1'h0}) : s1_eff_addr : eaddr_out;
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
		.input_port_is_csr((input_port_ldst_op == `ldst_ops__csr_load) | (input_port_ldst_op == `ldst_ops__csr_store)),
		.input_port_is_ldst(input_port_exec_unit == `op_class__ld_st),
		.input_port_mem_access_len(input_port_mem_access_len),
		.input_port_mem_base(mem_base),
		.input_port_mem_limit(mem_limit),
		.input_port_op_b(input_port_op_b),
		.input_port_op_c(input_port_op_c),
		.input_port_task_mode(task_mode_in),

		.output_port_eff_addr(ldst_output_eff_addr),
		.output_port_is_csr(ldst_output_is_csr),
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
		.output_ready(u82_output_port),
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
		.output_port_is_exception_or_interrupt(branch_output_is_exception_or_interrupt),
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
		.input_port_is_csr(mem_input_is_csr),
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
		.csr_if_pready(csr_if_pready),
		.csr_if_psel(csr_if_psel),
		.csr_if_pwrite(csr_if_pwrite),
		.csr_if_pwdata(csr_if_pwdata),
		.csr_if_prdata(csr_if_prdata)
	);

	assign branch_input_interrupt = interrupt;
	assign s1_alu_output_f_carry = branch_input_f_carry;
	assign s1_alu_output_f_overflow = branch_input_f_overflow;
	assign s1_alu_output_f_sign = branch_input_f_sign;
	assign s1_alu_output_f_zero = branch_input_f_zero;
	assign s1_ldst_output_is_csr = mem_input_is_csr;
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
	assign u82_output_port = (s2_exec_unit == `op_class__ld_st) & ((s2_ldst_op == `ldst_ops__load) | (s2_ldst_op == `ldst_ops__csr_load)) &  ~ block_mem ? s2_mem_output_valid : 1'h1;
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
	input logic input_port_is_csr,
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

	output logic [15:0] csr_if_paddr,
	output logic csr_if_penable,
	input logic csr_if_pready,
	output logic csr_if_psel,
	output logic csr_if_pwrite,
	output logic [31:0] csr_if_pwdata,
	input logic [31:0] csr_if_prdata
);

	logic input_advance;
	logic bus_request_advance;
	logic multi_cycle;
	logic next_active;
	logic active;
	logic pending;
	logic gap;
	logic u43_output_port;
	logic is_csr;
	logic [30:0] next_addr;
	logic [15:0] data_store;
	logic u84_output_port;
	logic [1:0] u88_output_port;
	logic csr_pen;
	logic csr_active;
	logic u109_output_port;
	logic [15:0] u113_output_port;
	logic [31:0] u118_output_port;
	logic [1:0] byte_en;

	assign input_advance = input_port_ready & input_port_valid;
	always_ff @(posedge clk) multi_cycle <= rst ? 1'h0 : input_advance ? (input_port_access_len == 2'h2) &  ~ is_csr : multi_cycle;
	assign bus_request_advance = bus_req_if_ready & bus_req_if_valid;
	assign next_active = (input_port_access_len == 2'h2) &  ~ is_csr & input_advance ? 1'h1 : bus_request_advance ? 1'h0 : active;
	always_ff @(posedge clk) active <= rst ? 1'h0 : next_active;
	always_ff @(posedge clk) pending <= rst ? 1'h0 : (input_port_access_len == 2'h2) &  ~ is_csr & input_advance & input_port_read_not_write ? 1'h1 : bus_rsp_if_valid ? 1'h0 : pending;
	always_ff @(posedge clk) gap <= rst ? 1'h0 : (input_port_access_len != 2'h2) &  ~ is_csr & input_advance | active &  ~ next_active ? 1'h1 : 1'h0;
	always_ff @(posedge clk) u43_output_port <= rst ? 1'h0 : input_advance ? input_port_is_csr : output_port_valid ? 1'h0 : is_csr;
	assign is_csr = input_advance ? input_port_is_csr : u43_output_port;
	assign input_port_ready = bus_req_if_ready &  ~ active &  ~ gap | input_port_is_csr & input_port_valid &  ~ csr_active;
	assign bus_req_if_valid = (input_port_valid &  ~ input_port_is_csr | active) &  ~ gap;
	assign output_port_valid = bus_rsp_if_valid &  ~ pending | csr_pen & csr_if_pready &  ~ csr_if_pwrite;
	always_ff @(posedge clk) data_store <= rst ? 16'h0 : input_advance ? input_port_data[31:16] : bus_rsp_if_valid & pending ? bus_rsp_if_data : data_store;
	always_ff @(posedge clk) u84_output_port <= rst ? 1'h0 : input_port_ready & input_port_valid ? input_port_read_not_write : u84_output_port;
	assign bus_req_if_read_not_write = input_port_ready & input_port_valid ? input_port_read_not_write : u84_output_port;
	always_ff @(posedge clk) u88_output_port <= rst ? 2'h0 : input_port_ready & input_port_valid ? byte_en : u88_output_port;
	assign bus_req_if_byte_en = input_port_ready & input_port_valid ? byte_en : u88_output_port;
	always_ff @(posedge clk) next_addr <= rst ? 31'h0 : input_advance ? input_port_addr[31:1] | 1'h1 : next_addr;
	assign bus_req_if_addr = input_advance ? input_port_addr[31:1] : next_addr;
	assign bus_req_if_data = input_advance ? input_port_data[15:0] : data_store;
	assign output_port_data_l = csr_pen ? csr_if_prdata[15:0] : multi_cycle ? data_store : bus_rsp_if_data;
	assign output_port_data_h = csr_pen ? csr_if_prdata[31:16] : bus_rsp_if_data;
	always_ff @(posedge clk) csr_pen <= rst ? 1'h0 : input_advance ? is_csr : csr_if_pready & is_csr ? 1'h0 : csr_pen;
	always_ff @(posedge clk) csr_active <= rst ? 1'h0 : csr_if_psel;
	assign csr_if_psel = input_advance & is_csr | csr_pen;
	always_ff @(posedge clk) u109_output_port <= rst ? 1'h0 : input_port_ready & input_port_valid ?  ~ input_port_read_not_write : u109_output_port;
	assign csr_if_pwrite = input_port_ready & input_port_valid ?  ~ input_port_read_not_write : u109_output_port;
	always_ff @(posedge clk) u113_output_port <= rst ? 16'h0 : input_port_ready & input_port_valid ? input_port_addr[17:2] : u113_output_port;
	assign csr_if_paddr = input_port_ready & input_port_valid ? input_port_addr[17:2] : u113_output_port;
	always_ff @(posedge clk) u118_output_port <= rst ? 32'h0 : input_port_ready & input_port_valid ? input_port_data : u118_output_port;
	assign csr_if_pwdata = input_port_ready & input_port_valid ? input_port_data : u118_output_port;
	assign byte_en = {(input_port_access_len != 1'h0) | input_port_addr[0], (input_port_access_len != 1'h0) |  ~ input_port_addr[0]};

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
	output logic [6:0] output_port_ecause,
	output logic output_port_is_exception,
	output logic output_port_is_exception_or_interrupt,
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
	logic swi_exception;
	logic unknown_inst_exception;
	logic u21_output_port;
	logic u18_output_port;

	assign is_exception = input_port_is_branch_insn & (input_port_opcode == `branch_ops__swi) | input_port_mem_av | input_port_mem_unaligned | input_port_fetch_av;
	assign condition_result = input_port_is_branch_insn & (
		((input_port_opcode == `branch_ops__cb_eq) ? input_port_f_zero : 1'b0) | 
		((input_port_opcode == `branch_ops__cb_ne) ?  ~ input_port_f_zero : 1'b0) | 
		((input_port_opcode == `branch_ops__cb_lts) ? (input_port_f_sign != input_port_f_overflow) : 1'b0) | 
		((input_port_opcode == `branch_ops__cb_ges) ? (input_port_f_sign == input_port_f_overflow) : 1'b0) | 
		((input_port_opcode == `branch_ops__cb_lt) ? input_port_f_carry : 1'b0) | 
		((input_port_opcode == `branch_ops__cb_ge) ?  ~ input_port_f_carry : 1'b0) | 
		((input_port_opcode == `branch_ops__bb_one) ? u18_output_port : 1'b0) | 
		((input_port_opcode == `branch_ops__bb_zero) ?  ~ u21_output_port : 1'b0) );
	assign spc_branch_target = input_port_is_branch_insn & (input_port_opcode == `branch_ops__pc_w) ? input_port_op_a[31:1] : input_port_branch_addr;
	assign output_port_spc = is_exception ? 1'h0 : spc_branch_target;
	assign in_mode_branch = 
		(input_port_is_branch_insn & (input_port_opcode == `branch_ops__pc_w) ? 1'h1 : 1'b0) | 
		(input_port_is_branch_insn & (input_port_opcode == `branch_ops__tpc_w) ? input_port_task_mode : 1'b0) | 
		(is_exception ?  ~ input_port_task_mode : 1'b0) | 
		(input_port_is_branch_insn & (input_port_opcode == `branch_ops__stm) ? 1'h0 : 1'b0) | 
		(input_port_is_branch_insn & (input_port_opcode == `branch_ops__pc_w) | input_port_is_branch_insn & (input_port_opcode == `branch_ops__tpc_w) | is_exception | input_port_is_branch_insn & (input_port_opcode == `branch_ops__stm) ? 1'b0 : condition_result);
	assign output_port_spc_changed =  ~ input_port_task_mode & (is_exception | in_mode_branch);
	assign branch_target = (input_port_is_branch_insn & (input_port_opcode == `branch_ops__pc_w) ? input_port_op_a[31:1] : 31'b0) | (input_port_is_branch_insn & (input_port_opcode == `branch_ops__tpc_w) ? input_port_op_a[31:1] : 31'b0) | (input_port_is_branch_insn & (input_port_opcode == `branch_ops__stm) ? input_port_tpc : 31'b0) | (input_port_is_branch_insn & (input_port_opcode == `branch_ops__pc_w) | input_port_is_branch_insn & (input_port_opcode == `branch_ops__tpc_w) | input_port_is_branch_insn & (input_port_opcode == `branch_ops__stm) ? 31'b0 : (is_exception | input_port_interrupt ? input_port_tpc : input_port_branch_addr));
	assign output_port_tpc_changed = input_port_task_mode ? in_mode_branch | is_exception | input_port_interrupt : input_port_is_branch_insn & (input_port_opcode == `branch_ops__tpc_w);
	assign output_port_task_mode_changed = input_port_task_mode ? is_exception | input_port_interrupt : input_port_is_branch_insn & (input_port_opcode == `branch_ops__stm);
	assign output_port_task_mode = input_port_task_mode ^ output_port_task_mode_changed;
	assign output_port_do_branch = in_mode_branch | output_port_task_mode_changed;
	assign unknown_inst_exception = input_port_is_branch_insn & (input_port_opcode == `branch_ops__unknown);
	assign swi_exception = input_port_is_branch_insn & (input_port_opcode == `branch_ops__swi);
	assign output_port_ecause = unknown_inst_exception ? `exceptions__exc_unknown_inst : input_port_interrupt ? `exceptions__exc_hwi : input_port_fetch_av ? `exceptions__exc_inst_av : input_port_mem_unaligned ? `exceptions__exc_unaligned : input_port_mem_av ? `exceptions__exc_mem_av : swi_exception ? 6'h20 | input_port_op_a[2:0] : 7'hx;
	assign output_port_is_exception_or_interrupt = is_exception | input_port_task_mode & input_port_interrupt;

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

	assign u13_output_port = ((input_port_opcode == `shifter_ops__shll) ? (input_port_op_a << input_port_op_b[4:0]) + 63'b0 : 64'b0) | ((input_port_opcode == `shifter_ops__shlr) ? input_port_op_a >> input_port_op_b[4:0] : 64'b0) | ((input_port_opcode == `shifter_ops__shar) ? $signed(signed_a >>> input_port_op_b[4:0]) : 64'b0) ;
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

	logic [30:0] offset;
	logic [31:0] u18_output_port;
	logic [31:0] u21_output_port;

	assign offset = {input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[0], input_port_op_c[15:1]};
	assign output_port_branch_addr = u18_output_port[30:0];
	assign output_port_straight_addr = u21_output_port[30:0];

	assign u18_output_port = input_port_pc + offset + 32'b0;
	assign u21_output_port = input_port_pc + input_port_inst_len + 32'b0 + 1'h1;
endmodule


////////////////////////////////////////////////////////////////////////////////
// LoadStoreUnit
////////////////////////////////////////////////////////////////////////////////
module LoadStoreUnit (
	input logic clk,
	input logic rst,
	input logic input_port_is_csr,
	input logic input_port_is_ldst,
	input logic [1:0] input_port_mem_access_len,
	input logic [21:0] input_port_mem_base,
	input logic [21:0] input_port_mem_limit,
	input logic [31:0] input_port_op_b,
	input logic [31:0] input_port_op_c,
	input logic input_port_task_mode,

	output logic [31:0] output_port_eff_addr,
	output logic output_port_is_csr,
	output logic output_port_mem_av,
	output logic output_port_mem_unaligned,
	output logic [31:0] output_port_phy_addr
);

	logic [32:0] u_output_port;
	logic [32:0] u5_output_port;
	logic [31:0] phy_addr;
	logic mem_av;
	logic u27_output_port;
	logic mem_unaligned;

	assign output_port_eff_addr = u_output_port[31:0];
	always @(*) begin
		unique case (input_port_mem_access_len)
			2'd0: u27_output_port = 1'h0;
			2'd1: u27_output_port = output_port_eff_addr[0];
			2'd2: u27_output_port = output_port_eff_addr[0] | output_port_eff_addr[1];
			2'd3: u27_output_port = 1'h1;
			default: u27_output_port = 1'hx;
		endcase
	end
	assign phy_addr = input_port_is_csr ? ({input_port_op_c[15:0], 2'h0}) | (input_port_task_mode ? 18'h20000 : 1'h0) : u5_output_port[31:0];
	assign mem_av = input_port_task_mode & input_port_is_ldst & output_port_eff_addr[31:10] > input_port_mem_limit &  ~ input_port_is_csr;
	assign mem_unaligned =  ~ input_port_is_csr & input_port_is_ldst & u27_output_port;
	assign output_port_is_csr = input_port_is_csr;

	assign u_output_port = input_port_op_b + input_port_op_c + 33'b0;
	assign u5_output_port = output_port_eff_addr + (input_port_task_mode ? (input_port_mem_base << 4'ha) + 32'b0 : 1'h0) + 33'b0;
	assign output_port_phy_addr = phy_addr;
	assign output_port_mem_av = mem_av;
	assign output_port_mem_unaligned = mem_unaligned;
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
	assign xor_b = input_port_opcode == `alu_ops__a_minus_b ? 32'hffffffff : 1'h0;
	assign a = input_port_opcode == `alu_ops__pc_plus_b ? ({input_port_pc, 1'h0}) : input_port_op_a;
	assign b = xor_b ^ input_port_op_b;
	assign use_adder = (input_port_opcode == `alu_ops__a_plus_b) | (input_port_opcode == `alu_ops__a_minus_b);
	assign sum = a + b + 33'b0 + c_in;
	assign use_and = input_port_opcode == `alu_ops__a_and_b;
	assign and_result = a & b;
	assign xor_result = input_port_op_a ^ input_port_op_b;
	assign adder_result = 
		(use_adder ? sum : 33'b0) | 
		((input_port_opcode == `alu_ops__a_or_b) ? input_port_op_a | input_port_op_b : 33'b0) | 
		(use_and ? and_result : 33'b0) | 
		((input_port_opcode == `alu_ops__a_xor_b) ? xor_result : 33'b0) | 
		((input_port_opcode == `alu_ops__tpc) ? ({input_port_tpc, 1'h0}) : 33'b0) | 
		((input_port_opcode == `alu_ops__pc_plus_b) ? sum : 33'b0) ;
	assign output_port_result = adder_result[31:0];
	assign output_port_f_zero = xor_result == 1'h0;
	assign output_port_f_sign = adder_result[31];
	assign output_port_f_carry = adder_result[32] ^ (input_port_opcode == `alu_ops__a_minus_b);
	assign output_port_f_overflow = (input_port_op_a[31] != input_port_op_b[31]) & (input_port_op_a[31] != adder_result[31]);

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
	always_ff @(posedge clock_port) buf_valid <= reset_port ? 1'h0 : clear ? 1'h0 : input_valid & input_ready ? 1'h1 : output_ready & buf_valid ? 1'h0 : buf_valid;
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
	always_ff @(posedge clock_port) buf_valid <= reset_port ? 1'h0 : clear ? 1'h0 : input_valid & input_ready ? 1'h1 : output_ready & buf_valid ? 1'h0 : buf_valid;
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
	output logic [1:0] output_port_ldst_op,
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

	input logic do_branch,
	output logic break_fetch_burst
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
	logic [31:0] ones_field_a_2x;
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
	logic mask_for_pflush;
	logic mask_for_invalid_instruction;
	logic mask_for_fence;
	logic mask_for_pc_eq_rd;
	logic mask_for_tpc_eq_rd;
	logic mask_for_rd_eq_pc;
	logic mask_for_rd_eq_tpc;
	logic mask_for_invalid_instruction_1;
	logic mask_for_rd_eq_tiny_field_a;
	logic mask_for_rd_eq_pc_plus_field_atimes2;
	logic mask_for_rd_eq_minus_ra;
	logic mask_for_rd_eq_notra;
	logic mask_for_rd_eq_bse_ra;
	logic mask_for_rd_eq_wse_ra;
	logic mask_for_invalid_instruction_2;
	logic mask_for_rd_eq_ra_xor_rb;
	logic mask_for_rd_eq_ra_or_rb;
	logic mask_for_rd_eq_ra_and_rb;
	logic mask_for_rd_eq_ra_plus_rb;
	logic mask_for_rd_eq_ra_minus_rb;
	logic mask_for_rd_eq_type_name_rb;
	logic mask_for_rd_eq_tiny_rb_plus_field_a;
	logic mask_for_rd_eq_value;
	logic mask_for_pc_eq_value;
	logic mask_for_tpc_eq_value;
	logic mask_for_invalid_instruction_3;
	logic mask_for_invalid_instruction_4;
	logic mask_for_rd_eq_field_e_xor_rb;
	logic mask_for_rd_eq_field_e_or_rb;
	logic mask_for_rd_eq_field_e_and_rb;
	logic mask_for_rd_eq_field_e_plus_rb;
	logic mask_for_rd_eq_field_e_minus_rb;
	logic mask_for_invalid_instruction_5;
	logic mask_for_invalid_instruction_6;
	logic mask_for_rd_eq_short_value;
	logic mask_for_pc_eq_short_value;
	logic mask_for_tpc_eq_short_value;
	logic mask_for_rd_eq_field_e_xor_ra;
	logic mask_for_rd_eq_field_e_or_ra;
	logic mask_for_rd_eq_field_e_and_ra;
	logic mask_for_rd_eq_field_e_plus_ra;
	logic mask_for_rd_eq_field_e_minus_ra;
	logic mask_for_invalid_instruction_7;
	logic mask_for_invalid_instruction_8;
	logic mask_for_if_ra_eq_0;
	logic mask_for_if_ra_ne_0;
	logic mask_for_if_ra_lt_0;
	logic mask_for_if_ra_ge_0;
	logic mask_for_if_ra_gt_0;
	logic mask_for_if_ra_le_0;
	logic mask_for_invalid_instruction_9;
	logic mask_for_invalid_instruction_10;
	logic mask_for_if_ra_eq_0_1;
	logic mask_for_if_ra_ne_0_1;
	logic mask_for_if_ra_lt_0_1;
	logic mask_for_if_ra_ge_0_1;
	logic mask_for_if_ra_gt_0_1;
	logic mask_for_if_ra_le_0_1;
	logic mask_for_invalid_instruction_11;
	logic mask_for_if_rb_eq_ra;
	logic mask_for_if_rb_ne_ra;
	logic mask_for_if_signed_rb_lt_ra;
	logic mask_for_if_signed_rb_ge_ra;
	logic mask_for_if_rb_lt_ra;
	logic mask_for_if_rb_ge_ra;
	logic mask_for_invalid_instruction_12;
	logic mask_for_invalid_instruction_13;
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
	logic mask_for_invalid_instruction_14;
	logic mask_for_invalid_instruction_15;
	logic mask_for_invalid_instruction_16;
	logic mask_for_invalid_instruction_17;
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
	logic mask_for_invalid_instruction_18;
	logic mask_for_invalid_instruction_19;
	logic mask_for_invalid_instruction_20;
	logic mask_for_invalid_instruction_21;
	logic mask_for_invalid_instruction_22;
	logic mask_for_invalid_instruction_23;
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
	logic mask_for_invalid_instruction_24;
	logic mask_for_invalid_instruction_25;
	logic mask_for_invalid_instruction_26;
	logic mask_for_rd_eq_csr_field_e;
	logic mask_for_csr_field_e_eq_rd;
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
	logic mask_for_invalid_instruction_27;
	logic mask_for_invalid_instruction_28;
	logic mask_for_invalid_instruction_29;
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
	logic group_13_for_branch_op;
	logic [3:0] branch_op;
	logic group_1_for_ldst_op;
	logic group_2_for_ldst_op;
	logic group_3_for_ldst_op;
	logic group_4_for_ldst_op;
	logic [1:0] ldst_op;
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
	logic group_5_for_op_b;
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
	logic u1840_output_port;
	logic [31:0] u1841_output_port;
	logic u1843_output_port;
	logic [31:0] u1844_output_port;
	logic [1:0] u1847_output_port;
	logic [3:0] u22_output_port;
	logic [3:0] field_a_plus_one;

	assign tiny_ofs = {fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7], fetch_inst_0[7:1], 2'h0};
	assign field_a_plus_one = u40_output_port[3:0];
	assign ones_field_a = u22_output_port[3] ? ({field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one[3], field_a_plus_one}) : fetch_inst_0[3:0];
	assign field_d_is_f = fetch_inst_0[15:12] == 4'hf;
	assign field_b_is_f = fetch_inst_0[7:4] == 4'hf;
	assign field_a_is_f = fetch_inst_0[3:0] == 4'hf;
	assign field_c_is_f = fetch_inst_0[11:8] == 4'hf;
	assign mask_for_rd_eq_ra_lsl_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h6) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_lsr_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h7) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_asr_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'h8) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_lsl_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h6) &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_field_e_lsr_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h7) &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_field_e_asr_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'h8) &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_ra_lsl_field_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h6) & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_lsr_field_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h7) & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_asr_field_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'h8) & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_times_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'h9) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_times_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'h9) &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_field_e_times_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'h9) & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_swi = 1'h1 & fetch_inst_0[15:12] < 4'h8 & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & (fetch_inst_0[3:0] == 1'h0);
	assign mask_for_stm = 1'h1 & (fetch_inst_0[15:12] == 4'h8) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & (fetch_inst_0[3:0] == 1'h0);
	assign mask_for_woi = 1'h1 & (fetch_inst_0[15:12] == 4'h9) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & (fetch_inst_0[3:0] == 1'h0);
	assign mask_for_pflush = 1'h1 & (fetch_inst_0[15:12] == 4'ha) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & (fetch_inst_0[3:0] == 1'h0);
	assign mask_for_invalid_instruction = 1'h1 & fetch_inst_0[15:12] > 4'ha &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & (fetch_inst_0[3:0] == 1'h0);
	assign mask_for_pc_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & (fetch_inst_0[3:0] == 2'h2);
	assign mask_for_tpc_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & (fetch_inst_0[3:0] == 2'h3);
	assign mask_for_invalid_instruction_1 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & fetch_inst_0[3:0] > 3'h5 &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_2 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & fetch_inst_0[7:4] > 3'h6 &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_type_name_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'ha) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_pc_eq_value = 1'h1 & (fetch_inst_0[15:12] == 2'h2) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'he) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_tpc_eq_value = 1'h1 & (fetch_inst_0[15:12] == 2'h3) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'he) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_invalid_instruction_3 = 1'h1 & (fetch_inst_0[15:12] == 4'h8) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'he) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_invalid_instruction_4 = 1'h1 & (fetch_inst_0[15:12] == 4'h9) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'he) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_invalid_instruction_5 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'ha) &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_invalid_instruction_6 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hb) &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_pc_eq_short_value = 1'h1 & (fetch_inst_0[15:12] == 2'h2) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'hf) & (fetch_inst_0[3:0] == 4'he);
	assign mask_for_tpc_eq_short_value = 1'h1 & (fetch_inst_0[15:12] == 2'h3) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'hf) & (fetch_inst_0[3:0] == 4'he);
	assign mask_for_invalid_instruction_7 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'ha) & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_8 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hb) & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_if_ra_eq_0 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) &  ~ field_a_is_f;
	assign mask_for_if_ra_ne_0 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h1) &  ~ field_a_is_f;
	assign mask_for_if_ra_lt_0 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 2'h2) &  ~ field_a_is_f;
	assign mask_for_if_ra_ge_0 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 2'h3) &  ~ field_a_is_f;
	assign mask_for_if_ra_gt_0 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 3'h4) &  ~ field_a_is_f;
	assign mask_for_if_ra_le_0 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 3'h5) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_9 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 3'h6) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_10 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 3'h7) &  ~ field_a_is_f;
	assign mask_for_if_ra_eq_0_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'h8) &  ~ field_a_is_f;
	assign mask_for_if_ra_ne_0_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'h9) &  ~ field_a_is_f;
	assign mask_for_if_ra_lt_0_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'ha) &  ~ field_a_is_f;
	assign mask_for_if_ra_ge_0_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'hb) &  ~ field_a_is_f;
	assign mask_for_if_ra_gt_0_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'hc) &  ~ field_a_is_f;
	assign mask_for_if_ra_le_0_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'hd) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_11 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'he) &  ~ field_a_is_f;
	assign mask_for_if_rb_eq_ra = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 1'h1) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_ne_ra = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 2'h2) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_signed_rb_lt_ra = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 2'h3) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_signed_rb_ge_ra = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 3'h4) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_lt_ra = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 3'h5) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_ge_ra = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 3'h6) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_12 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 3'h7) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_13 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 4'h8) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_eq_ra_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 4'h9) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_ne_ra_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 4'ha) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_signed_rb_lt_ra_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 4'hb) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_signed_rb_ge_ra_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 4'hc) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_lt_ra_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 4'hd) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_rb_ge_ra_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) & (fetch_inst_0[11:8] == 4'he) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_if_ra_bit__eq_1 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) &  ~ field_c_is_f & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_if_rb_bit__eq_0 = 1'h1 & (fetch_inst_0[15:12] == 4'hf) &  ~ field_c_is_f &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_invalid_instruction_14 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 1'h0) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_15 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 1'h1) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_16 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 2'h2) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_17 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 2'h3) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_18 = 1'h1 & (fetch_inst_0[15:12] == 1'h1) & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'he) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_19 = 1'h1 & (fetch_inst_0[15:12] == 2'h2) & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'he) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_20 = 1'h1 & (fetch_inst_0[15:12] == 2'h3) & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'he) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_21 = 1'h1 & (fetch_inst_0[15:12] == 1'h1) & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'he) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_22 = 1'h1 & (fetch_inst_0[15:12] == 2'h2) & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'he) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_23 = 1'h1 & (fetch_inst_0[15:12] == 2'h3) & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'he) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_24 = 1'h1 & (fetch_inst_0[15:12] == 1'h1) & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'he) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_25 = 1'h1 & (fetch_inst_0[15:12] == 2'h2) & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'he) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_26 = 1'h1 & (fetch_inst_0[15:12] == 2'h3) & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'he) &  ~ field_a_is_f;
	assign mask_for_invalid_instruction_27 = 1'h1 & (fetch_inst_0[15:12] == 1'h1) & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'he) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_invalid_instruction_28 = 1'h1 & (fetch_inst_0[15:12] == 2'h2) & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'he) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_expr = 1'h1 & (fetch_inst_0[15:12] == 2'h3) & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'he) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_fence = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & (fetch_inst_0[3:0] == 1'h1);
	assign mask_for_rd_eq_pc = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & (fetch_inst_0[3:0] == 3'h4);
	assign mask_for_rd_eq_tpc = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & (fetch_inst_0[3:0] == 3'h5);
	assign mask_for_rd_eq_tiny_field_a = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h1) &  ~ field_a_is_f;
	assign mask_for_rd_eq_pc_plus_field_atimes2 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 2'h2) &  ~ field_a_is_f;
	assign mask_for_rd_eq_minus_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 2'h3) &  ~ field_a_is_f;
	assign mask_for_rd_eq_notra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 3'h4) &  ~ field_a_is_f;
	assign mask_for_rd_eq_bse_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 3'h5) &  ~ field_a_is_f;
	assign mask_for_rd_eq_wse_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 3'h6) &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_xor_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h1) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_or_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 2'h2) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_and_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 2'h3) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_plus_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h4) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_ra_minus_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h5) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_tiny_rb_plus_field_a = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hb) &  ~ field_b_is_f &  ~ field_a_is_f;
	assign mask_for_rd_eq_value = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 1'h0) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_field_e_xor_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h1) &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_field_e_or_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 2'h2) &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_field_e_and_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 2'h3) &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_field_e_plus_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h4) &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_field_e_minus_rb = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h5) &  ~ field_b_is_f & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_short_value = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'hf) & (fetch_inst_0[3:0] == 1'h0);
	assign mask_for_rd_eq_field_e_xor_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h1) & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_or_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 2'h2) & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_and_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 2'h3) & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_plus_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h4) & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_rd_eq_field_e_minus_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 3'h5) & (fetch_inst_0[7:4] == 4'hf) &  ~ field_a_is_f;
	assign mask_for_mem_raplustiny_ofstimes4_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hc);
	assign mask_for_rd_eq_mem_raplustiny_ofstimes4 = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hd);
	assign mask_for_rd_eq_mem8_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 3'h4) &  ~ field_a_is_f;
	assign mask_for_rd_eq_mem16_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 3'h5) &  ~ field_a_is_f;
	assign mask_for_rd_eq_mem32_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 3'h6) &  ~ field_a_is_f;
	assign mask_for_rd_eq_memll32_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 3'h7) &  ~ field_a_is_f;
	assign mask_for_mem8_ra_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'h8) &  ~ field_a_is_f;
	assign mask_for_mem16_ra_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'h9) &  ~ field_a_is_f;
	assign mask_for_mem32_ra_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'ha) &  ~ field_a_is_f;
	assign mask_for_memsr32_ra_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'hb) &  ~ field_a_is_f;
	assign mask_for_rd_eq_smem8_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'hc) &  ~ field_a_is_f;
	assign mask_for_rd_eq_smem16_ra = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'he) & (fetch_inst_0[7:4] == 4'hd) &  ~ field_a_is_f;
	assign mask_for_rd_eq_mem8_raplusfield_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 3'h4) &  ~ field_a_is_f;
	assign mask_for_rd_eq_mem16_raplusfield_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 3'h5) &  ~ field_a_is_f;
	assign mask_for_rd_eq_mem32_raplusfield_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 3'h6) &  ~ field_a_is_f;
	assign mask_for_rd_eq_memll32_raplusfield_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 3'h7) &  ~ field_a_is_f;
	assign mask_for_mem8_raplusfield_e_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'h8) &  ~ field_a_is_f;
	assign mask_for_mem16_raplusfield_e_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'h9) &  ~ field_a_is_f;
	assign mask_for_mem32_raplusfield_e_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'ha) &  ~ field_a_is_f;
	assign mask_for_memsr32_raplusfield_e_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'hb) &  ~ field_a_is_f;
	assign mask_for_rd_eq_smem8_raplusfield_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'hc) &  ~ field_a_is_f;
	assign mask_for_rd_eq_smem16_raplusfield_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'hd) &  ~ field_a_is_f;
	assign mask_for_rd_eq_csr_field_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'hf) & (fetch_inst_0[3:0] == 4'h8);
	assign mask_for_csr_field_e_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 1'h0) & (fetch_inst_0[7:4] == 4'hf) & (fetch_inst_0[3:0] == 4'h9);
	assign mask_for_rd_eq_mem8_field_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 3'h4) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_mem16_field_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 3'h5) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_mem32_field_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 3'h6) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_memll32_field_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 3'h7) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_mem8_field_e_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'h8) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_mem16_field_e_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'h9) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_mem32_field_e_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'ha) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_memsr32_field_e_eq_rd = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'hb) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_smem8_field_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'hc) & (fetch_inst_0[3:0] == 4'hf);
	assign mask_for_rd_eq_smem16_field_e = 1'h1 &  ~ field_d_is_f & (fetch_inst_0[11:8] == 4'hf) & (fetch_inst_0[7:4] == 4'hd) & (fetch_inst_0[3:0] == 4'hf);
	assign group_1_for_exec_unit = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e;
	assign group_2_for_exec_unit = mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra;
	assign group_3_for_exec_unit = mask_for_swi | mask_for_stm | mask_for_woi | mask_for_pflush | mask_for_invalid_instruction | mask_for_pc_eq_rd | mask_for_tpc_eq_rd | mask_for_invalid_instruction_1 | mask_for_invalid_instruction_2 | mask_for_rd_eq_type_name_rb | mask_for_pc_eq_value | mask_for_tpc_eq_value | mask_for_invalid_instruction_3 | mask_for_invalid_instruction_4 | mask_for_invalid_instruction_5 | mask_for_invalid_instruction_6 | mask_for_pc_eq_short_value | mask_for_tpc_eq_short_value | mask_for_invalid_instruction_7 | mask_for_invalid_instruction_8 | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_invalid_instruction_9 | mask_for_invalid_instruction_10 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_invalid_instruction_11 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_invalid_instruction_12 | mask_for_invalid_instruction_13 | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_if_ra_bit__eq_1 | mask_for_if_rb_bit__eq_0 | mask_for_invalid_instruction_14 | mask_for_invalid_instruction_15 | mask_for_invalid_instruction_16 | mask_for_invalid_instruction_17 | mask_for_invalid_instruction_18 | mask_for_invalid_instruction_19 | mask_for_invalid_instruction_20 | mask_for_invalid_instruction_21 | mask_for_invalid_instruction_22 | mask_for_invalid_instruction_23 | mask_for_invalid_instruction_24 | mask_for_invalid_instruction_25 | mask_for_invalid_instruction_26 | mask_for_invalid_instruction_27 | mask_for_invalid_instruction_28 | mask_expr;
	assign group_4_for_exec_unit = mask_for_fence | mask_for_rd_eq_pc | mask_for_rd_eq_tpc | mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_pc_plus_field_atimes2 | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_rd_eq_value | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_short_value | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra;
	assign group_5_for_exec_unit = mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_csr_field_e | mask_for_csr_field_e_eq_rd | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
	assign group_1_for_alu_op = mask_for_woi | mask_for_pflush | mask_for_rd_eq_minus_ra | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_field_e_minus_ra | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1;
	assign group_2_for_alu_op = mask_for_rd_eq_pc | mask_for_rd_eq_pc_plus_field_atimes2;
	assign group_3_for_alu_op = mask_for_rd_eq_tpc;
	assign group_4_for_alu_op = mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_value | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_short_value | mask_for_rd_eq_field_e_or_ra;
	assign group_5_for_alu_op = mask_for_rd_eq_notra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_xor_ra;
	assign group_6_for_alu_op = mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_and_ra;
	assign group_7_for_alu_op = mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_plus_ra;
	assign group_1_for_shifter_op = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_ra_lsl_field_e;
	assign group_2_for_shifter_op = mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_ra_lsr_field_e;
	assign group_3_for_shifter_op = mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_asr_field_e;
	assign group_1_for_branch_op = mask_for_swi;
	assign group_2_for_branch_op = mask_for_stm;
	assign group_3_for_branch_op = mask_for_woi | mask_for_if_ra_eq_0 | mask_for_if_ra_eq_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_eq_ra_1;
	assign group_4_for_branch_op = mask_for_pflush | mask_for_if_ra_ne_0 | mask_for_if_ra_ne_0_1 | mask_for_if_rb_ne_ra | mask_for_if_rb_ne_ra_1;
	assign group_5_for_branch_op = mask_for_invalid_instruction | mask_for_invalid_instruction_1 | mask_for_invalid_instruction_2 | mask_for_rd_eq_type_name_rb | mask_for_invalid_instruction_3 | mask_for_invalid_instruction_4 | mask_for_invalid_instruction_5 | mask_for_invalid_instruction_6 | mask_for_invalid_instruction_7 | mask_for_invalid_instruction_8 | mask_for_invalid_instruction_9 | mask_for_invalid_instruction_10 | mask_for_invalid_instruction_11 | mask_for_invalid_instruction_12 | mask_for_invalid_instruction_13 | mask_for_invalid_instruction_14 | mask_for_invalid_instruction_15 | mask_for_invalid_instruction_16 | mask_for_invalid_instruction_17 | mask_for_invalid_instruction_18 | mask_for_invalid_instruction_19 | mask_for_invalid_instruction_20 | mask_for_invalid_instruction_21 | mask_for_invalid_instruction_22 | mask_for_invalid_instruction_23 | mask_for_invalid_instruction_24 | mask_for_invalid_instruction_25 | mask_for_invalid_instruction_26 | mask_for_invalid_instruction_27 | mask_for_invalid_instruction_28 | mask_expr;
	assign group_6_for_branch_op = mask_for_pc_eq_rd | mask_for_pc_eq_value | mask_for_pc_eq_short_value;
	assign group_7_for_branch_op = mask_for_tpc_eq_rd | mask_for_tpc_eq_value | mask_for_tpc_eq_short_value;
	assign group_8_for_branch_op = mask_for_if_ra_lt_0 | mask_for_if_ra_gt_0 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_gt_0_1 | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_lt_ra_1;
	assign group_9_for_branch_op = mask_for_if_ra_ge_0 | mask_for_if_ra_le_0 | mask_for_if_ra_ge_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_signed_rb_ge_ra | mask_for_if_signed_rb_ge_ra_1;
	assign group_10_for_branch_op = mask_for_if_rb_lt_ra | mask_for_if_rb_lt_ra_1;
	assign group_11_for_branch_op = mask_for_if_rb_ge_ra | mask_for_if_rb_ge_ra_1;
	assign group_12_for_branch_op = mask_for_if_ra_bit__eq_1;
	assign group_13_for_branch_op = mask_for_if_rb_bit__eq_0;
	assign group_1_for_ldst_op = mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd;
	assign group_2_for_ldst_op = mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
	assign group_3_for_ldst_op = mask_for_rd_eq_csr_field_e;
	assign group_4_for_ldst_op = mask_for_csr_field_e_eq_rd;
	assign group_1_for_rd1_addr = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e | mask_for_rd_eq_ra_times_rb | mask_for_woi | mask_for_pflush | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_ra_bit__eq_1;
	assign group_2_for_rd1_addr = mask_for_pc_eq_rd | mask_for_tpc_eq_rd | mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_csr_field_e_eq_rd | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd;
	assign group_3_for_rd1_addr = mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_if_rb_bit__eq_0;
	assign group_1_for_res_addr = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e | mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra | mask_for_rd_eq_pc | mask_for_rd_eq_tpc | mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_pc_plus_field_atimes2 | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_rd_eq_value | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_short_value | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_csr_field_e | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
	assign group_1_for_rd2_addr = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_woi | mask_for_pflush | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb;
	assign group_2_for_rd2_addr = mask_for_rd_eq_field_e_times_ra | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e;
	assign group_3_for_rd2_addr = mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4;
	assign tiny_field_a = 4'hc | fetch_inst_0[0];
	assign group_1_for_use_reg_a = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e | mask_for_rd_eq_ra_times_rb | mask_for_woi | mask_for_pflush | mask_for_pc_eq_rd | mask_for_tpc_eq_rd | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_if_ra_bit__eq_1 | mask_for_if_rb_bit__eq_0 | mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_csr_field_e_eq_rd | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd;
	assign group_1_for_use_reg_b = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra | mask_for_woi | mask_for_pflush | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e;
	assign group_1_for_op_a = mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra | mask_for_rd_eq_value | mask_for_pc_eq_value | mask_for_tpc_eq_value | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_short_value | mask_for_pc_eq_short_value | mask_for_tpc_eq_short_value | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra;
	assign field_e = fetch_inst_len == 2'h2 ? ({fetch_inst_2, fetch_inst_1}) : ({fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1[15], fetch_inst_1});
	assign group_2_for_op_a = mask_for_swi;
	assign group_3_for_op_a = mask_for_invalid_instruction | mask_for_invalid_instruction_1 | mask_for_invalid_instruction_2 | mask_for_rd_eq_type_name_rb | mask_for_invalid_instruction_3 | mask_for_invalid_instruction_4 | mask_for_invalid_instruction_5 | mask_for_invalid_instruction_6 | mask_for_invalid_instruction_7 | mask_for_invalid_instruction_8 | mask_for_invalid_instruction_9 | mask_for_invalid_instruction_10 | mask_for_invalid_instruction_11 | mask_for_invalid_instruction_12 | mask_for_invalid_instruction_13 | mask_for_invalid_instruction_14 | mask_for_invalid_instruction_15 | mask_for_invalid_instruction_16 | mask_for_invalid_instruction_17 | mask_for_invalid_instruction_18 | mask_for_invalid_instruction_19 | mask_for_invalid_instruction_20 | mask_for_invalid_instruction_21 | mask_for_invalid_instruction_22 | mask_for_invalid_instruction_23 | mask_for_invalid_instruction_24 | mask_for_invalid_instruction_25 | mask_for_invalid_instruction_26 | mask_for_invalid_instruction_27 | mask_for_invalid_instruction_28 | mask_expr;
	assign group_4_for_op_a = mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_minus_ra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1;
	assign group_5_for_op_a = mask_for_rd_eq_notra;
	assign group_1_for_op_b = mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e;
	assign group_2_for_op_b = mask_for_rd_eq_pc | mask_for_rd_eq_value | mask_for_rd_eq_short_value | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_rd_eq_csr_field_e | mask_for_csr_field_e_eq_rd | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
	assign group_3_for_op_b = mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_tiny_rb_plus_field_a;
	assign group_4_for_op_b = mask_for_rd_eq_pc_plus_field_atimes2;
	assign ones_field_a_2x = {ones_field_a[30:0], 1'h0};
	assign group_5_for_op_b = mask_for_if_ra_bit__eq_1 | mask_for_if_rb_bit__eq_0;
	assign group_1_for_op_c = mask_for_woi | mask_for_pflush | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra;
	assign group_2_for_op_c = mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_if_ra_bit__eq_1 | mask_for_if_rb_bit__eq_0 | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_csr_field_e | mask_for_csr_field_e_eq_rd | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
	assign group_3_for_op_c = mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4;
	assign group_1_for_mem_len = mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_csr_field_e | mask_for_csr_field_e_eq_rd | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd;
	assign group_2_for_mem_len = mask_for_rd_eq_mem8_ra | mask_for_mem8_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_mem8_field_e | mask_for_mem8_field_e_eq_rd | mask_for_rd_eq_smem8_field_e;
	assign group_3_for_mem_len = mask_for_rd_eq_mem16_ra | mask_for_mem16_ra_eq_rd | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem16_raplusfield_e | mask_for_mem16_raplusfield_e_eq_rd | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_mem16_field_e | mask_for_mem16_field_e_eq_rd | mask_for_rd_eq_smem16_field_e;
	assign group_1_for_bse = mask_for_rd_eq_bse_ra | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem8_field_e;
	assign group_1_for_wse = mask_for_rd_eq_wse_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_smem16_field_e;
	assign group_1_for_bze = mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem8_field_e;
	assign group_1_for_wze = mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem16_field_e;
	assign group_1_for_read1_needed = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e | mask_for_rd_eq_ra_times_rb | mask_for_woi | mask_for_pflush | mask_for_pc_eq_rd | mask_for_tpc_eq_rd | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_if_ra_eq_0 | mask_for_if_ra_ne_0 | mask_for_if_ra_lt_0 | mask_for_if_ra_ge_0 | mask_for_if_ra_eq_0_1 | mask_for_if_ra_ne_0_1 | mask_for_if_ra_lt_0_1 | mask_for_if_ra_ge_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_if_ra_bit__eq_1 | mask_for_if_rb_bit__eq_0 | mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_csr_field_e_eq_rd | mask_for_mem8_field_e_eq_rd | mask_for_mem16_field_e_eq_rd | mask_for_mem32_field_e_eq_rd | mask_for_memsr32_field_e_eq_rd;
	assign group_1_for_read2_needed = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra | mask_for_woi | mask_for_pflush | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra | mask_for_if_ra_gt_0 | mask_for_if_ra_le_0 | mask_for_if_ra_gt_0_1 | mask_for_if_ra_le_0_1 | mask_for_if_rb_eq_ra | mask_for_if_rb_ne_ra | mask_for_if_signed_rb_lt_ra | mask_for_if_signed_rb_ge_ra | mask_for_if_rb_lt_ra | mask_for_if_rb_ge_ra | mask_for_if_rb_eq_ra_1 | mask_for_if_rb_ne_ra_1 | mask_for_if_signed_rb_lt_ra_1 | mask_for_if_signed_rb_ge_ra_1 | mask_for_if_rb_lt_ra_1 | mask_for_if_rb_ge_ra_1 | mask_for_mem_raplustiny_ofstimes4_eq_rd | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_mem8_ra_eq_rd | mask_for_mem16_ra_eq_rd | mask_for_mem32_ra_eq_rd | mask_for_memsr32_ra_eq_rd | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_mem8_raplusfield_e_eq_rd | mask_for_mem16_raplusfield_e_eq_rd | mask_for_mem32_raplusfield_e_eq_rd | mask_for_memsr32_raplusfield_e_eq_rd | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e;
	assign group_1_for_rsv_needed = mask_for_rd_eq_ra_lsl_rb | mask_for_rd_eq_ra_lsr_rb | mask_for_rd_eq_ra_asr_rb | mask_for_rd_eq_field_e_lsl_rb | mask_for_rd_eq_field_e_lsr_rb | mask_for_rd_eq_field_e_asr_rb | mask_for_rd_eq_ra_lsl_field_e | mask_for_rd_eq_ra_lsr_field_e | mask_for_rd_eq_ra_asr_field_e | mask_for_rd_eq_ra_times_rb | mask_for_rd_eq_field_e_times_rb | mask_for_rd_eq_field_e_times_ra | mask_for_rd_eq_pc | mask_for_rd_eq_tpc | mask_for_rd_eq_tiny_field_a | mask_for_rd_eq_pc_plus_field_atimes2 | mask_for_rd_eq_minus_ra | mask_for_rd_eq_notra | mask_for_rd_eq_bse_ra | mask_for_rd_eq_wse_ra | mask_for_rd_eq_ra_xor_rb | mask_for_rd_eq_ra_or_rb | mask_for_rd_eq_ra_and_rb | mask_for_rd_eq_ra_plus_rb | mask_for_rd_eq_ra_minus_rb | mask_for_rd_eq_tiny_rb_plus_field_a | mask_for_rd_eq_value | mask_for_rd_eq_field_e_xor_rb | mask_for_rd_eq_field_e_or_rb | mask_for_rd_eq_field_e_and_rb | mask_for_rd_eq_field_e_plus_rb | mask_for_rd_eq_field_e_minus_rb | mask_for_rd_eq_short_value | mask_for_rd_eq_field_e_xor_ra | mask_for_rd_eq_field_e_or_ra | mask_for_rd_eq_field_e_and_ra | mask_for_rd_eq_field_e_plus_ra | mask_for_rd_eq_field_e_minus_ra | mask_for_rd_eq_mem_raplustiny_ofstimes4 | mask_for_rd_eq_mem8_ra | mask_for_rd_eq_mem16_ra | mask_for_rd_eq_mem32_ra | mask_for_rd_eq_memll32_ra | mask_for_rd_eq_smem8_ra | mask_for_rd_eq_smem16_ra | mask_for_rd_eq_mem8_raplusfield_e | mask_for_rd_eq_mem16_raplusfield_e | mask_for_rd_eq_mem32_raplusfield_e | mask_for_rd_eq_memll32_raplusfield_e | mask_for_rd_eq_smem8_raplusfield_e | mask_for_rd_eq_smem16_raplusfield_e | mask_for_rd_eq_csr_field_e | mask_for_rd_eq_mem8_field_e | mask_for_rd_eq_mem16_field_e | mask_for_rd_eq_mem32_field_e | mask_for_rd_eq_memll32_field_e | mask_for_rd_eq_smem8_field_e | mask_for_rd_eq_smem16_field_e;
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
		(group_7_for_alu_op ? `alu_ops__a_plus_b : 3'b0) ;
	always_ff @(posedge clk) output_port_alu_op <= rst ? 3'h0 : register_outputs ? alu_op : output_port_alu_op;
	assign shifter_op = (group_1_for_shifter_op ? `shifter_ops__shll : 2'b0) | (group_2_for_shifter_op ? `shifter_ops__shlr : 2'b0) | (group_3_for_shifter_op ? `shifter_ops__shar : 2'b0) ;
	always_ff @(posedge clk) output_port_shifter_op <= rst ? 2'h0 : register_outputs ? shifter_op : output_port_shifter_op;
	assign branch_op = 
		(group_1_for_branch_op ? `branch_ops__swi : 4'b0) | 
		(group_2_for_branch_op ? `branch_ops__stm : 4'b0) | 
		(group_3_for_branch_op ? `branch_ops__cb_eq : 4'b0) | 
		(group_4_for_branch_op ? `branch_ops__cb_ne : 4'b0) | 
		(group_5_for_branch_op ? `branch_ops__unknown : 4'b0) | 
		(group_6_for_branch_op ? `branch_ops__pc_w : 4'b0) | 
		(group_7_for_branch_op ? `branch_ops__tpc_w : 4'b0) | 
		(group_8_for_branch_op ? `branch_ops__cb_lts : 4'b0) | 
		(group_9_for_branch_op ? `branch_ops__cb_ges : 4'b0) | 
		(group_10_for_branch_op ? `branch_ops__cb_lt : 4'b0) | 
		(group_11_for_branch_op ? `branch_ops__cb_ge : 4'b0) | 
		(group_12_for_branch_op ? `branch_ops__bb_one : 4'b0) | 
		(group_13_for_branch_op ? `branch_ops__bb_zero : 4'b0) ;
	always_ff @(posedge clk) output_port_branch_op <= rst ? 4'h0 : register_outputs ? branch_op : output_port_branch_op;
	assign ldst_op = 
		(group_1_for_ldst_op ? `ldst_ops__store : 2'b0) | 
		(group_2_for_ldst_op ? `ldst_ops__load : 2'b0) | 
		(group_3_for_ldst_op ? `ldst_ops__csr_load : 2'b0) | 
		(group_4_for_ldst_op ? `ldst_ops__csr_store : 2'b0) ;
	always_ff @(posedge clk) output_port_ldst_op <= rst ? 2'h0 : register_outputs ? ldst_op : output_port_ldst_op;
	assign use_reg_a = (group_1_for_use_reg_a ? 1'h1 : 1'b0) | (group_1_for_use_reg_a ? 1'b0 : 1'h0);
	assign op_a = 
		(group_1_for_op_a ? field_e : 32'b0) | 
		(group_2_for_op_a ? fetch_inst_0[15:12] : 32'b0) | 
		(group_3_for_op_a ? 3'h7 : 32'b0) | 
		(group_4_for_op_a ? 1'h0 : 32'b0) | 
		(group_5_for_op_a ? 32'hffffffff : 32'b0) ;
	always_ff @(posedge clk) u1840_output_port <= rst ? 1'h0 : register_outputs ? use_reg_a : u1840_output_port;
	always_ff @(posedge clk) u1841_output_port <= rst ? 32'h0 : register_outputs ? op_a : u1841_output_port;
	assign output_port_op_a = u1840_output_port ? reg_file_rsp_read1_data : u1841_output_port;
	assign use_reg_b = (group_1_for_use_reg_b ? 1'h1 : 1'b0) | (group_1_for_use_reg_b ? 1'b0 : 1'h0);
	assign op_b = 
		(group_1_for_op_b ? field_e : 32'b0) | 
		(group_2_for_op_b ? 1'h0 : 32'b0) | 
		(group_3_for_op_b ? ones_field_a : 32'b0) | 
		(group_4_for_op_b ? ones_field_a_2x : 32'b0) | 
		(group_5_for_op_b ? fetch_inst_0[11:8] : 32'b0) ;
	always_ff @(posedge clk) u1843_output_port <= rst ? 1'h0 : register_outputs ? use_reg_b : u1843_output_port;
	always_ff @(posedge clk) u1844_output_port <= rst ? 32'h0 : register_outputs ? op_b : u1844_output_port;
	assign output_port_op_b = u1843_output_port ? reg_file_rsp_read2_data : u1844_output_port;
	assign op_c = (group_1_for_op_c ? 1'h0 : 32'b0) | (group_2_for_op_c ? field_e : 32'b0) | (group_3_for_op_c ? tiny_ofs : 32'b0) ;
	always_ff @(posedge clk) output_port_op_c <= rst ? 32'h0 : register_outputs ? op_c : output_port_op_c;
	assign mem_len = (group_1_for_mem_len ? 2'h2 : 2'b0) | (group_2_for_mem_len ? 1'h0 : 2'b0) | (group_3_for_mem_len ? 1'h1 : 2'b0) ;
	always_ff @(posedge clk) u1847_output_port <= rst ? 2'h0 : register_outputs ? mem_len : u1847_output_port;
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
	assign break_fetch_burst = register_outputs & (exec_unit == `op_class__ld_st);
	assign output_port_valid = reg_file_rsp_valid;
	assign reg_file_rsp_ready = output_port_ready;
	assign fetch_ready = reg_file_req_ready;
	assign output_port_mem_access_len = u1847_output_port;

	assign u40_output_port = fetch_inst_0[3:0] + 1'h1 + 5'b0;
	assign mask_for_invalid_instruction_29 = mask_expr;
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
	input logic do_branch,
	input logic break_burst,
	output logic event_fetch,
	output logic [4:0] event_dropped
);

	logic inst_buf_queue_av;
	logic inst_buf_queue_valid;
	logic inst_buf_event_drop;
	logic [15:0] inst_buf_queue_data;
	logic [3:0] inst_buf_queue_free_cnt;
	logic [3:0] inst_queue_event_queue_flush;
	logic inst_buf_queue_ready;
	logic inst_queue_assemble_valid;
	logic inst_queue_assemble_av;
	logic [15:0] inst_queue_assemble_data;
	logic [1:0] inst_assemble_event_words_dropped;
	logic inst_queue_assemble_ready;

	assign event_dropped = inst_buf_event_drop + inst_queue_event_queue_flush + 5'b0 + inst_assemble_event_words_dropped;

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
		.do_branch(do_branch),
		.break_burst(break_burst),
		.event_fetch(event_fetch),
		.event_drop(inst_buf_event_drop)
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

		.do_branch(do_branch),
		.event_queue_flush(inst_queue_event_queue_flush)
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

		.do_branch(do_branch),
		.event_words_dropped(inst_assemble_event_words_dropped)
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

	input logic do_branch,
	output logic [1:0] event_words_dropped
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
	logic [1:0] u88_output_port;
	logic [1:0] u93_output_port;
	logic [1:0] fsm_state;
	logic [1:0] decode_fsm_next_state;

	assign u88_output_port = inst_len_reg - 1'h1 + 3'b0;
	assign u93_output_port = inst_len_reg + 1'h1 + 3'b0;
	assign event_words_dropped = do_branch ? 
		((fsm_state == `InstAssembleStates__have_0_fragments) ? 1'h0 : 2'b0) | 
		((fsm_state == `InstAssembleStates__need_1_fragments) ? inst_len_reg : 2'b0) | 
		((fsm_state == `InstAssembleStates__need_2_fragments) ? u88_output_port : 2'b0) | 
		((fsm_state == `InstAssembleStates__have_all_fragments) ? u93_output_port : 2'b0)  : 1'h0;
	assign terminal_fsm_state = fsm_state == `InstAssembleStates__have_all_fragments;
	assign fetch_ready =  ~ terminal_fsm_state | decode_ready | do_branch;
	assign decode_valid = terminal_fsm_state &  ~ do_branch;
	assign fsm_advance =  ~ terminal_fsm_state & inst_buf_valid & fetch_ready | terminal_fsm_state & decode_ready;
	always_ff @(posedge clk) fetch_av <= rst ? 1'h0 : fsm_advance ? (fsm_state == `InstAssembleStates__have_0_fragments) | (fsm_state == `InstAssembleStates__have_all_fragments) ? inst_buf_av : fetch_av : fetch_av;
	always_ff @(posedge clk) inst_reg_0 <= rst ? 16'h0 : fsm_advance ? (fsm_state == `InstAssembleStates__have_0_fragments) | (fsm_state == `InstAssembleStates__have_all_fragments) ? inst_buf_data : inst_reg_0 : inst_reg_0;
	always_ff @(posedge clk) inst_reg_1 <= rst ? 16'h0 : fsm_advance ? (fsm_state == `InstAssembleStates__need_1_fragments) & (inst_len_reg == 1'h1) | (fsm_state == `InstAssembleStates__need_2_fragments) ? inst_buf_data : inst_reg_1 : inst_reg_1;
	always_ff @(posedge clk) inst_reg_2 <= rst ? 16'h0 : fsm_advance ? inst_buf_data : inst_reg_2;
	always_ff @(posedge clk) inst_len_reg <= rst ? 2'h0 : fsm_advance ? (fsm_state == `InstAssembleStates__have_0_fragments) | (fsm_state == `InstAssembleStates__have_all_fragments) ? inst_len : inst_len_reg : inst_len_reg;

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
	assign u12_output_port =  ~ do_branch & fsm_advance &  ~ inst_buf_av & (inst_len == 1'h0);
	assign u19_output_port =  ~ do_branch & fsm_advance &  ~ inst_buf_av & (inst_len == 1'h1);
	assign u26_output_port =  ~ do_branch & fsm_advance &  ~ inst_buf_av & (inst_len == 2'h2);
	assign u29_output_port =  ~ do_branch &  ~ fsm_advance;
	assign u31_output_port =  ~ do_branch & fsm_advance;
	assign u34_output_port =  ~ do_branch &  ~ fsm_advance;
	assign u38_output_port =  ~ do_branch & fsm_advance &  ~ inst_buf_av;
	assign u41_output_port =  ~ do_branch & fsm_advance & inst_buf_av;
	assign u44_output_port =  ~ do_branch &  ~ fsm_advance;
	assign u48_output_port =  ~ do_branch & fsm_advance & inst_buf_valid & inst_buf_av;
	assign u56_output_port =  ~ do_branch & fsm_advance & inst_buf_valid &  ~ inst_buf_av & (inst_len == 1'h0);
	assign u64_output_port =  ~ do_branch & fsm_advance & inst_buf_valid &  ~ inst_buf_av & (inst_len == 1'h1);
	assign u72_output_port =  ~ do_branch & fsm_advance & inst_buf_valid &  ~ inst_buf_av & (inst_len == 2'h2);
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
		((bit_code == 1'h0) ? word[0] : 1'b0) | 
		((bit_code == 1'h1) ? word[1] : 1'b0) | 
		((bit_code == 2'h2) ? word[2] : 1'b0) | 
		((bit_code == 2'h3) ? word[3] : 1'b0) | 
		((bit_code == 3'h4) ? word[4] : 1'b0) | 
		((bit_code == 3'h5) ? word[5] : 1'b0) | 
		((bit_code == 3'h6) ? word[6] : 1'b0) | 
		((bit_code == 3'h7) ? word[7] : 1'b0) | 
		((bit_code == 4'h8) ? word[8] : 1'b0) | 
		((bit_code == 4'h9) ? word[9] : 1'b0) | 
		((bit_code == 4'ha) ? word[14] : 1'b0) | 
		((bit_code == 4'hb) ? word[15] : 1'b0) | 
		((bit_code == 4'hc) ? word[16] : 1'b0) | 
		((bit_code == 4'hd) ? word[30] : 1'b0) | 
		((bit_code == 4'he) ? word[31] : 1'b0) ;

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
		((bit_code == 1'h0) ? word[0] : 1'b0) | 
		((bit_code == 1'h1) ? word[1] : 1'b0) | 
		((bit_code == 2'h2) ? word[2] : 1'b0) | 
		((bit_code == 2'h3) ? word[3] : 1'b0) | 
		((bit_code == 3'h4) ? word[4] : 1'b0) | 
		((bit_code == 3'h5) ? word[5] : 1'b0) | 
		((bit_code == 3'h6) ? word[6] : 1'b0) | 
		((bit_code == 3'h7) ? word[7] : 1'b0) | 
		((bit_code == 4'h8) ? word[8] : 1'b0) | 
		((bit_code == 4'h9) ? word[9] : 1'b0) | 
		((bit_code == 4'ha) ? word[14] : 1'b0) | 
		((bit_code == 4'hb) ? word[15] : 1'b0) | 
		((bit_code == 4'hc) ? word[16] : 1'b0) | 
		((bit_code == 4'hd) ? word[30] : 1'b0) | 
		((bit_code == 4'he) ? word[31] : 1'b0) ;

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

	assign output_port = {((u_output_port == 4'hf) | (u3_output_port == 4'hf) & ((u6_output_port != 4'hf) | (u9_output_port == 4'hf)) | (u15_output_port == 4'he) & (u18_output_port == 4'hf) | u23_output_port < 4'hc & ((u26_output_port == 4'hf) | (u29_output_port == 4'hf))) &  ~ ((u35_output_port == 4'hf) | (u38_output_port != 4'hf)), ((u_output_port == 4'hf) | (u3_output_port == 4'hf) & ((u6_output_port != 4'hf) | (u9_output_port == 4'hf)) | (u15_output_port == 4'he) & (u18_output_port == 4'hf) | u23_output_port < 4'hc & ((u26_output_port == 4'hf) | (u29_output_port == 4'hf))) & ((u35_output_port == 4'hf) | (u38_output_port != 4'hf))};

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

	output logic [3:0] queue_free_cnt,
	output logic assemble_av,
	output logic [15:0] assemble_data,
	input logic assemble_ready,
	output logic assemble_valid,

	input logic do_branch,
	output logic [3:0] event_queue_flush
);

	logic dec;
	logic inc;
	logic signed [5:0] u3_output_port;
	logic [3:0] empty_cnt;
	logic [3:0] u11_output_port;

	assign inc = assemble_ready & assemble_valid;
	assign dec = inst_ready & inst_valid;
	always_ff @(posedge clk) empty_cnt <= rst ? 4'hb : do_branch ? 4'hb : u3_output_port[3:0];
	initial empty_cnt <= 4'hb;
	assign u11_output_port = 4'hb - empty_cnt + 5'b0;
	assign event_queue_flush = do_branch ? u11_output_port : 1'h0;

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

	assign u3_output_port = empty_cnt + inc + 5'b0 - dec + 6'b0;
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
	assign push_will_wrap = push_addr == 4'ha;
	assign push =  ~ full & input_port_valid;
	assign next_push_addr = push ? push_will_wrap ? 1'h0 : push_addr + 1'h1 : push_addr;
	assign pop_will_wrap = pop_addr == 4'ha;
	assign pop =  ~ empty & output_port_ready;
	assign next_pop_addr = pop ? pop_will_wrap ? 1'h0 : pop_addr + 1'h1 : pop_addr;
	assign next_looped = 
		((push != 1'h1) & (pop != 1'h1) ? looped : 1'b0) | 
		((push == 1'h1) & (pop != 1'h1) ? push_will_wrap ? 1'h1 : looped : 1'b0) | 
		((push != 1'h1) & (pop == 1'h1) ? pop_will_wrap ? 1'h0 : looped : 1'b0) | 
		((push == 1'h1) & (pop == 1'h1) ? 
		((push_will_wrap != 1'h1) & (pop_will_wrap != 1'h1) ? looped : 1'b0) | 
		((push_will_wrap == 1'h1) & (pop_will_wrap != 1'h1) ? 1'h1 : 1'b0) | 
		((push_will_wrap != 1'h1) & (pop_will_wrap == 1'h1) ? 1'h0 : 1'b0) | 
		((push_will_wrap == 1'h1) & (pop_will_wrap == 1'h1) ? looped : 1'b0)  : 1'b0) ;
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
	assign out_data_selector = (push_addr == next_pop_addr) & u93_output_port;
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

	input logic [3:0] queue_free_cnt,
	input logic [21:0] mem_base,
	input logic [21:0] mem_limit,
	input logic [30:0] spc,
	input logic [30:0] tpc,
	input logic task_mode,
	input logic do_branch,
	input logic break_burst,
	output logic event_fetch,
	output logic event_drop
);

	logic advance_request;
	logic [32:0] u3_output_port;
	logic [30:0] branch_target;
	logic task_mode_fetch;
	logic [31:0] u8_output_port;
	logic [30:0] fetch_addr;
	logic fetch_page_limit;
	logic fetch_av;
	logic [23:0] xor_page;
	logic out_of_page_branch;
	logic [2:0] u35_output_port;
	logic signed [2:0] u39_output_port;
	logic [1:0] next_outstanding_request;
	logic [1:0] outstanding_request;
	logic [1:0] drop_count;
	logic u59_output_port;
	logic start_new_request;
	logic signed [4:0] u63_output_port;
	logic [3:0] req_len;
	logic req_av;
	logic u94_output_port;
	logic [1:0] u51_output_port;
	logic state;
	logic next_state;

	assign branch_target = task_mode ? u3_output_port[30:0] : spc;
	always_ff @(posedge clk) task_mode_fetch <= rst ? 1'h0 : do_branch ? task_mode : task_mode_fetch;
	assign advance_request = bus_if_request_valid & bus_if_request_ready;
	always_ff @(posedge clk) fetch_addr <= rst ? 31'h0 : do_branch ? branch_target : u8_output_port[30:0];
	always_ff @(posedge clk) fetch_page_limit <= rst ? 1'h0 : state == `InstBufferStates__idle ? 1'h0 : ( ~ fetch_addr[6:0] == 1'h0);
	assign xor_page = fetch_addr[30:7] ^ branch_target[30:7];
	assign next_outstanding_request = 
		(advance_request & bus_if_response_valid ? outstanding_request : 2'b0) | 
		(advance_request &  ~ bus_if_response_valid ? u35_output_port[1:0] : 2'b0) | 
		( ~ advance_request & bus_if_response_valid ? u39_output_port[1:0] : 2'b0) | 
		( ~ advance_request &  ~ bus_if_response_valid ? outstanding_request : 2'b0) ;
	always_ff @(posedge clk) outstanding_request <= rst ? 2'h0 : next_outstanding_request;
	assign u51_output_port = drop_count - bus_if_response_valid + 3'b0;
	always_ff @(posedge clk) drop_count <= rst ? 2'h0 : do_branch ? next_outstanding_request : drop_count == 1'h0 ? 1'h0 : u51_output_port;
	assign out_of_page_branch = do_branch & (xor_page != 1'h0);
	always_ff @(posedge clk) u59_output_port <= rst ? 1'h0 : out_of_page_branch;
	assign start_new_request = queue_free_cnt > 4'h8 + next_outstanding_request | u59_output_port;
	always_ff @(posedge clk) req_len <= rst ? 4'h8 : start_new_request ? do_branch ? 4'h8 : queue_free_cnt >= 4'h8 ? 4'h8 : queue_free_cnt : break_burst ? 1'h0 : advance_request ? req_len > 1'h0 ? u63_output_port[3:0] : 1'h0 : req_len;
	initial req_len <= 4'h8;
	assign fetch_av = task_mode_fetch & fetch_addr[30:9] > mem_limit;
	always_ff @(posedge clk) req_av <= rst ? 1'h0 : start_new_request ? fetch_av : req_av;
	assign bus_if_request_valid = (state == `InstBufferStates__request) &  ~ fetch_page_limit &  ~ out_of_page_branch;
	assign bus_if_request_addr = fetch_addr[30:0];
	assign queue_valid = bus_if_response_valid & (drop_count == 1'h0) &  ~ do_branch;
	assign event_drop = bus_if_response_valid & (drop_count != 1'h0);
	assign bus_if_request_byte_en = 2'h3;
	assign bus_if_request_data = 16'hx;
	assign bus_if_request_read_not_write = 1'h1;
	assign queue_data = bus_if_response_data;
	assign event_fetch = bus_if_response_valid;

	FSM_2 fsm (
		.clock_port(clk),
		.reset_port(rst),
		.reset_value(`InstBufferStates__idle),
		.state(state),
		.next_state(next_state),
		.default_state(`InstBufferStates__idle),
		.input_idle_to_request(start_new_request),
		.input_request_to_idle(u94_output_port)
	);

	assign u3_output_port = tpc + (mem_base << 4'ha) + 32'b0 + 33'b0;
	assign u8_output_port = fetch_addr + advance_request + 32'b0;
	assign u35_output_port = outstanding_request + 1'h1 + 3'b0;
	assign u39_output_port = outstanding_request - 1'h1 + 3'b0;
	assign u63_output_port = req_len - 1'h1 + 5'b0;
	assign queue_av = req_av;
	assign u94_output_port = fetch_page_limit | (req_len == 1'h0);
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
	output logic reg_if_pready,
	input logic reg_if_psel,
	input logic reg_if_pwrite,
	input logic [31:0] reg_if_pwdata,
	output logic [31:0] reg_if_prdata,

	input logic [3:0] drq,
	output logic interrupt
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
	logic ch_0_int_enable;
	logic ch_0_is_master;
	logic ch_0_high_priority;
	logic ch_0_req_polarity;
	logic ch_0_req_no_cdc;
	logic ch_0_active;
	logic ch_0_int_pending;
	logic u109_output_port;
	logic ch_0_req_pending;
	logic ch_1_served;
	logic [31:0] ch_1_addr;
	logic [31:0] ch_1_limit;
	logic ch_1_single;
	logic ch_1_read_not_write;
	logic ch_1_int_enable;
	logic ch_1_is_master;
	logic ch_1_high_priority;
	logic ch_1_req_polarity;
	logic ch_1_req_no_cdc;
	logic ch_1_active;
	logic ch_1_int_pending;
	logic u190_output_port;
	logic ch_1_req_pending;
	logic ch_2_served;
	logic [31:0] ch_2_addr;
	logic [31:0] ch_2_limit;
	logic ch_2_single;
	logic ch_2_read_not_write;
	logic ch_2_int_enable;
	logic ch_2_is_master;
	logic ch_2_high_priority;
	logic ch_2_req_polarity;
	logic ch_2_req_no_cdc;
	logic ch_2_active;
	logic ch_2_int_pending;
	logic u271_output_port;
	logic ch_2_req_pending;
	logic ch_3_served;
	logic [31:0] ch_3_addr;
	logic [31:0] ch_3_limit;
	logic ch_3_single;
	logic ch_3_read_not_write;
	logic ch_3_int_enable;
	logic ch_3_is_master;
	logic ch_3_high_priority;
	logic ch_3_req_polarity;
	logic ch_3_req_no_cdc;
	logic ch_3_active;
	logic ch_3_int_pending;
	logic u352_output_port;
	logic ch_3_req_pending;
	logic member;
	logic [3:0] ch_read_not_writes;
	logic [31:0] u366_output_port;
	logic req_pendig;
	logic [3:0] high_pri_req_pending;
	logic [3:0] low_pri_req_pending;
	logic high_pri_selected;
	logic [3:0] selected_dma_channel;
	logic [31:0] selected_addr;
	logic [31:0] selected_limit;
	logic tc;
	logic [32:0] u404_output_port;
	logic [31:0] next_addr;
	logic [3:0] read_not_writes;
	logic u447_output_port;
	logic [3:0] high_pri_selected_dma_channel;
	logic u449_output_port;
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
	always_ff @(posedge clk) ch_0_addr <= rst ? 32'h0 : (reg_if_paddr == 1'h0) & reg_write_strobe ? reg_if_pwdata : ch_0_served ? next_addr : ch_0_addr;
	always_ff @(posedge clk) ch_0_limit <= rst ? 32'h0 : (reg_if_paddr == 1'h1) & reg_write_strobe ? reg_if_pwdata : ch_0_limit;
	always_ff @(posedge clk) ch_0_single <= rst ? 1'h0 : (reg_if_paddr == 2'h2) & reg_write_strobe ? reg_if_pwdata[0] : ch_0_single;
	always_ff @(posedge clk) ch_0_read_not_write <= rst ? 1'h0 : (reg_if_paddr == 2'h2) & reg_write_strobe ? reg_if_pwdata[1] : ch_0_read_not_write;
	always_ff @(posedge clk) ch_0_int_enable <= rst ? 1'h0 : (reg_if_paddr == 2'h2) & reg_write_strobe ? reg_if_pwdata[2] : ch_0_int_enable;
	always_ff @(posedge clk) ch_0_is_master <= rst ? 1'h0 : (reg_if_paddr == 2'h2) & reg_write_strobe ? reg_if_pwdata[3] : ch_0_is_master;
	always_ff @(posedge clk) ch_0_high_priority <= rst ? 1'h0 : (reg_if_paddr == 2'h2) & reg_write_strobe ? reg_if_pwdata[4] : ch_0_high_priority;
	always_ff @(posedge clk) ch_0_req_polarity <= rst ? 1'h0 : (reg_if_paddr == 2'h2) & reg_write_strobe ? reg_if_pwdata[5] : ch_0_req_polarity;
	always_ff @(posedge clk) ch_0_req_no_cdc <= rst ? 1'h0 : (reg_if_paddr == 2'h2) & reg_write_strobe ? reg_if_pwdata[6] : ch_0_req_no_cdc;
	always_ff @(posedge clk) tc_reg <= rst ? 1'h0 : bus_req_if_ready & req_pendig ? tc : tc_reg;
	always_ff @(posedge clk) ch_0_active <= rst ? 1'h0 : (reg_if_paddr == 1'h0) & reg_write_strobe ? 1'h1 : ch_0_served ?  ~ tc_reg : ch_0_active;
	always_ff @(posedge clk) ch_0_int_pending <= rst ? 1'h0 : tc_reg & ch_0_served & ch_0_int_enable ? 1'h1 : (reg_if_paddr == 5'h10) & reg_write_strobe & reg_if_pwdata[0] ? 1'h0 : ch_0_int_pending;
	always_ff @(posedge clk) prev_drq <= rst ? 4'h0 : drq_1;
	always_ff @(posedge clk) u109_output_port <= rst ? 1'h0 : drq_1[0] &  ~ prev_drq[0] ? 1'h1 : ch_0_served ? 1'h0 : ch_0_req_pending;
	assign ch_0_req_pending = ch_0_active & (ch_0_single &  ~ ch_0_is_master ? drq_1[0] : u109_output_port);
	assign ch_1_served = served_dma_channel[1] & bus_rsp_if_valid;
	always_ff @(posedge clk) ch_1_addr <= rst ? 32'h0 : (reg_if_paddr == 3'h4) & reg_write_strobe ? reg_if_pwdata : ch_1_served ? next_addr : ch_1_addr;
	always_ff @(posedge clk) ch_1_limit <= rst ? 32'h0 : (reg_if_paddr == 3'h5) & reg_write_strobe ? reg_if_pwdata : ch_1_limit;
	always_ff @(posedge clk) ch_1_single <= rst ? 1'h0 : (reg_if_paddr == 3'h6) & reg_write_strobe ? reg_if_pwdata[0] : ch_1_single;
	always_ff @(posedge clk) ch_1_read_not_write <= rst ? 1'h0 : (reg_if_paddr == 3'h6) & reg_write_strobe ? reg_if_pwdata[1] : ch_1_read_not_write;
	always_ff @(posedge clk) ch_1_int_enable <= rst ? 1'h0 : (reg_if_paddr == 3'h6) & reg_write_strobe ? reg_if_pwdata[2] : ch_1_int_enable;
	always_ff @(posedge clk) ch_1_is_master <= rst ? 1'h0 : (reg_if_paddr == 3'h6) & reg_write_strobe ? reg_if_pwdata[3] : ch_1_is_master;
	always_ff @(posedge clk) ch_1_high_priority <= rst ? 1'h0 : (reg_if_paddr == 3'h6) & reg_write_strobe ? reg_if_pwdata[4] : ch_1_high_priority;
	always_ff @(posedge clk) ch_1_req_polarity <= rst ? 1'h0 : (reg_if_paddr == 3'h6) & reg_write_strobe ? reg_if_pwdata[5] : ch_1_req_polarity;
	always_ff @(posedge clk) ch_1_req_no_cdc <= rst ? 1'h0 : (reg_if_paddr == 3'h6) & reg_write_strobe ? reg_if_pwdata[6] : ch_1_req_no_cdc;
	always_ff @(posedge clk) ch_1_active <= rst ? 1'h0 : (reg_if_paddr == 3'h4) & reg_write_strobe ? 1'h1 : ch_1_served ?  ~ tc_reg : ch_1_active;
	always_ff @(posedge clk) ch_1_int_pending <= rst ? 1'h0 : tc_reg & ch_1_served & ch_1_int_enable ? 1'h1 : (reg_if_paddr == 5'h10) & reg_write_strobe & reg_if_pwdata[1] ? 1'h0 : ch_1_int_pending;
	always_ff @(posedge clk) u190_output_port <= rst ? 1'h0 : drq_1[1] &  ~ prev_drq[1] ? 1'h1 : ch_1_served ? 1'h0 : ch_1_req_pending;
	assign ch_1_req_pending = ch_1_active & (ch_1_single &  ~ ch_1_is_master ? drq_1[1] : u190_output_port);
	assign ch_2_served = served_dma_channel[2] & bus_rsp_if_valid;
	always_ff @(posedge clk) ch_2_addr <= rst ? 32'h0 : (reg_if_paddr == 4'h8) & reg_write_strobe ? reg_if_pwdata : ch_2_served ? next_addr : ch_2_addr;
	always_ff @(posedge clk) ch_2_limit <= rst ? 32'h0 : (reg_if_paddr == 4'h9) & reg_write_strobe ? reg_if_pwdata : ch_2_limit;
	always_ff @(posedge clk) ch_2_single <= rst ? 1'h0 : (reg_if_paddr == 4'ha) & reg_write_strobe ? reg_if_pwdata[0] : ch_2_single;
	always_ff @(posedge clk) ch_2_read_not_write <= rst ? 1'h0 : (reg_if_paddr == 4'ha) & reg_write_strobe ? reg_if_pwdata[1] : ch_2_read_not_write;
	always_ff @(posedge clk) ch_2_int_enable <= rst ? 1'h0 : (reg_if_paddr == 4'ha) & reg_write_strobe ? reg_if_pwdata[2] : ch_2_int_enable;
	always_ff @(posedge clk) ch_2_is_master <= rst ? 1'h0 : (reg_if_paddr == 4'ha) & reg_write_strobe ? reg_if_pwdata[3] : ch_2_is_master;
	always_ff @(posedge clk) ch_2_high_priority <= rst ? 1'h0 : (reg_if_paddr == 4'ha) & reg_write_strobe ? reg_if_pwdata[4] : ch_2_high_priority;
	always_ff @(posedge clk) ch_2_req_polarity <= rst ? 1'h0 : (reg_if_paddr == 4'ha) & reg_write_strobe ? reg_if_pwdata[5] : ch_2_req_polarity;
	always_ff @(posedge clk) ch_2_req_no_cdc <= rst ? 1'h0 : (reg_if_paddr == 4'ha) & reg_write_strobe ? reg_if_pwdata[6] : ch_2_req_no_cdc;
	always_ff @(posedge clk) ch_2_active <= rst ? 1'h0 : (reg_if_paddr == 4'h8) & reg_write_strobe ? 1'h1 : ch_2_served ?  ~ tc_reg : ch_2_active;
	always_ff @(posedge clk) ch_2_int_pending <= rst ? 1'h0 : tc_reg & ch_2_served & ch_2_int_enable ? 1'h1 : (reg_if_paddr == 5'h10) & reg_write_strobe & reg_if_pwdata[2] ? 1'h0 : ch_2_int_pending;
	always_ff @(posedge clk) u271_output_port <= rst ? 1'h0 : drq_1[2] &  ~ prev_drq[2] ? 1'h1 : ch_2_served ? 1'h0 : ch_2_req_pending;
	assign ch_2_req_pending = ch_2_active & (ch_2_single &  ~ ch_2_is_master ? drq_1[2] : u271_output_port);
	assign ch_3_served = served_dma_channel[3] & bus_rsp_if_valid;
	always_ff @(posedge clk) ch_3_addr <= rst ? 32'h0 : (reg_if_paddr == 4'hc) & reg_write_strobe ? reg_if_pwdata : ch_3_served ? next_addr : ch_3_addr;
	always_ff @(posedge clk) ch_3_limit <= rst ? 32'h0 : (reg_if_paddr == 4'hd) & reg_write_strobe ? reg_if_pwdata : ch_3_limit;
	always_ff @(posedge clk) ch_3_single <= rst ? 1'h0 : (reg_if_paddr == 4'he) & reg_write_strobe ? reg_if_pwdata[0] : ch_3_single;
	always_ff @(posedge clk) ch_3_read_not_write <= rst ? 1'h0 : (reg_if_paddr == 4'he) & reg_write_strobe ? reg_if_pwdata[1] : ch_3_read_not_write;
	always_ff @(posedge clk) ch_3_int_enable <= rst ? 1'h0 : (reg_if_paddr == 4'he) & reg_write_strobe ? reg_if_pwdata[2] : ch_3_int_enable;
	always_ff @(posedge clk) ch_3_is_master <= rst ? 1'h0 : (reg_if_paddr == 4'he) & reg_write_strobe ? reg_if_pwdata[3] : ch_3_is_master;
	always_ff @(posedge clk) ch_3_high_priority <= rst ? 1'h0 : (reg_if_paddr == 4'he) & reg_write_strobe ? reg_if_pwdata[4] : ch_3_high_priority;
	always_ff @(posedge clk) ch_3_req_polarity <= rst ? 1'h0 : (reg_if_paddr == 4'he) & reg_write_strobe ? reg_if_pwdata[5] : ch_3_req_polarity;
	always_ff @(posedge clk) ch_3_req_no_cdc <= rst ? 1'h0 : (reg_if_paddr == 4'he) & reg_write_strobe ? reg_if_pwdata[6] : ch_3_req_no_cdc;
	always_ff @(posedge clk) ch_3_active <= rst ? 1'h0 : (reg_if_paddr == 4'hc) & reg_write_strobe ? 1'h1 : ch_3_served ?  ~ tc_reg : ch_3_active;
	always_ff @(posedge clk) ch_3_int_pending <= rst ? 1'h0 : tc_reg & ch_3_served & ch_3_int_enable ? 1'h1 : (reg_if_paddr == 5'h10) & reg_write_strobe & reg_if_pwdata[3] ? 1'h0 : ch_3_int_pending;
	always_ff @(posedge clk) u352_output_port <= rst ? 1'h0 : drq_1[3] &  ~ prev_drq[3] ? 1'h1 : ch_3_served ? 1'h0 : member;
	assign member = ch_3_active & (ch_3_single &  ~ ch_3_is_master ? drq_1[3] : u352_output_port);
	always @(*) begin
		unique case (reg_if_paddr)
			4'd0: u366_output_port = ch_0_addr;
			4'd1: u366_output_port = ch_0_limit;
			4'd2: u366_output_port = {ch_0_req_polarity, ch_0_req_no_cdc, ch_0_is_master, ch_0_high_priority, ch_0_read_not_write, ch_0_single};
			4'd3: u366_output_port = {ch_0_int_pending, ch_0_req_pending, ch_0_active};
			4'd4: u366_output_port = ch_1_addr;
			4'd5: u366_output_port = ch_1_limit;
			4'd6: u366_output_port = {ch_1_req_polarity, ch_1_req_no_cdc, ch_1_is_master, ch_1_high_priority, ch_1_read_not_write, ch_1_single};
			4'd7: u366_output_port = {ch_1_int_pending, ch_1_req_pending, ch_1_active};
			4'd8: u366_output_port = ch_2_addr;
			4'd9: u366_output_port = ch_2_limit;
			4'd10: u366_output_port = {ch_2_req_polarity, ch_2_req_no_cdc, ch_2_is_master, ch_2_high_priority, ch_2_read_not_write, ch_2_single};
			4'd11: u366_output_port = {ch_2_int_pending, ch_2_req_pending, ch_2_active};
			4'd12: u366_output_port = ch_3_addr;
			4'd13: u366_output_port = ch_3_limit;
			4'd14: u366_output_port = {ch_3_req_polarity, ch_3_req_no_cdc, ch_3_is_master, ch_3_high_priority, ch_3_read_not_write, ch_3_single};
			4'd15: u366_output_port = {ch_3_int_pending, member, ch_3_active};
			4'd16: u366_output_port = {ch_3_int_pending, ch_2_int_pending, ch_1_int_pending, ch_0_int_pending};
			default: u366_output_port = 32'hx;
		endcase
	end
	always_ff @(posedge clk) reg_if_prdata <= rst ? 32'h0 : u366_output_port;
	assign interrupt = ch_3_int_pending | ch_2_int_pending | ch_1_int_pending | ch_0_int_pending;
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
	always_ff @(posedge clk) next_addr <= rst ? 32'h0 : bus_req_if_ready & req_pendig ? u404_output_port[31:0] : next_addr;
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
		.restart(u447_output_port)
	);

	RoundRobinArbiter_2 low_pri_arbiter (
		.clk(clk),
		.rst(rst),
		.requestors(low_pri_req_pending),
		.grants(low_pri_selected_dma_channel),
		.advance(bus_rsp_if_valid &  ~ high_pri_selected),
		.restart(u449_output_port)
	);

	assign ch_3_req_pending = member;
	assign bus_req_if_valid = req_pendig;
	assign bus_req_if_one_hot_channel = selected_dma_channel;
	assign bus_req_if_terminal_count = tc;
	assign u404_output_port = selected_addr + 1'h1 + 33'b0;
	assign u447_output_port = 1'h0;
	assign u449_output_port = 1'h0;
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
	output logic reg_if_pready,
	input logic reg_if_psel,
	input logic reg_if_pwrite,
	input logic [31:0] reg_if_pwdata,
	output logic [31:0] reg_if_prdata,

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

	output logic event_bus_idle
);

	logic reg_write_strobe;
	logic [7:0] refresh_divider;
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
	logic u118_output_port;
	logic dram_addr_muxing;
	logic [3:0] dma_ch;
	logic tc;
	logic signed [4:0] u123_output_port;
	logic [3:0] wait_states_store;
	logic signed [4:0] u138_output_port;
	logic [3:0] wait_states;
	logic waiting;
	logic two_cycle_nram_access;
	logic nram_access;
	logic u161_output_port;
	logic u162_output_port;
	logic u163_output_port;
	logic u164_output_port;
	logic u165_output_port;
	logic u167_output_port;
	logic u168_output_port;
	logic u169_output_port;
	logic u170_output_port;
	logic u171_output_port;
	logic u172_output_port;
	logic u174_output_port;
	logic u177_output_port;
	logic u178_output_port;
	logic u179_output_port;
	logic u180_output_port;
	logic u181_output_port;
	logic u182_output_port;
	logic u183_output_port;
	logic u184_output_port;
	logic dram_bank_next;
	logic u190_output_port;
	logic dram_bank;
	logic [10:0] input_row_addr;
	logic [10:0] row_addr;
	logic [10:0] col_addr;
	logic read_not_write;
	logic data_out_en;
	logic [1:0] u216_output_port;
	logic [1:0] byte_en;
	logic [15:0] data_out;
	logic dram_ras_active;
	logic dram_ras_a;
	logic dram_ras_b;
	logic dram_n_ras_a_1;
	logic dram_n_ras_b_1;
	logic n_nren;
	logic [3:0] u278_output_port;
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
	logic [10:0] col_addr_nr;
	logic [10:0] dram_addr_1;
	logic nr_cas_logic_1_reg;
	logic [7:0] data_out_low;
	logic [7:0] data_out_high;
	logic read_active;
	logic [7:0] data_in_low;
	logic [7:0] ndram_data_in_high;
	logic [7:0] u502_output_port;
	logic [7:0] data_in_high;
	logic [15:0] u510_output_port;
	logic [15:0] resp_data;
	logic u516_output_port;
	logic u521_output_port;
	logic [10:0] u42_output_port;
	logic [3:0] state;
	logic [3:0] next_state;

	assign reg_write_strobe = reg_if_psel & reg_if_pwrite & reg_if_penable;
	always_ff @(posedge clk) dram_bank_swap <= rst ? 1'h0 : (reg_if_paddr == 1'h0) & reg_write_strobe ? reg_if_pwdata[11] : dram_bank_swap;
	always_ff @(posedge clk) dram_bank_size <= rst ? 2'h0 : (reg_if_paddr == 1'h0) & reg_write_strobe ? reg_if_pwdata[10:9] : dram_bank_size;
	always_ff @(posedge clk) refresh_disable <= rst ? 1'h0 : (reg_if_paddr == 1'h0) & reg_write_strobe ? reg_if_pwdata[8] : refresh_disable;
	assign refresh_tc = refresh_counter == 1'h0;
	always_ff @(posedge clk) refresh_req <= rst ? 1'h0 : refresh_tc &  ~ refresh_disable ? 1'h1 : refresh_rsp ? 1'h0 : refresh_req;
	always_ff @(posedge clk) refresh_divider <= rst ? 8'h80 : (reg_if_paddr == 1'h0) & reg_write_strobe ? reg_if_pwdata[7:0] : refresh_divider;
	initial refresh_divider <= 8'h80;
	always_ff @(posedge clk) refresh_counter <= rst ? 8'h0 : refresh_tc ? refresh_divider : refresh_req ? refresh_counter : u34_output_port[7:0];
	assign u42_output_port = refresh_addr + 1'h1 + 12'b0;
	always_ff @(posedge clk) refresh_addr <= rst ? 11'h0 : refresh_rsp ? u42_output_port : refresh_addr;
	assign arb_port_comb = refresh_req ? `Ports__refresh_port : dma_request_valid ? `Ports__dma_port : mem_request_valid ? `Ports__mem_port : `Ports__fetch_port;
	always_ff @(posedge clk) u54_output_port <= rst ? 2'h0 : (state == `BusIfStates__idle) ? arb_port_comb : u54_output_port;
	assign arb_port_select = state == `BusIfStates__idle ? arb_port_comb : u54_output_port;
	assign req_ready = (state == `BusIfStates__idle) | (state == `BusIfStates__first) | (state == `BusIfStates__middle);
	assign refresh_rsp = state == `BusIfStates__refresh;
	assign mem_request_ready = req_ready & (arb_port_select == `Ports__mem_port);
	assign fetch_request_ready = req_ready & (arb_port_select == `Ports__fetch_port);
	assign dma_request_ready = req_ready & (arb_port_select == `Ports__dma_port) | (state == `BusIfStates__external);
	always @(*) begin
		unique case (arb_port_select)
			2'd0: req_valid = fetch_request_valid;
			2'd1: req_valid = mem_request_valid;
			2'd2: req_valid = dma_request_valid;
			2'd3: req_valid = 1'h1;
			default: req_valid = 1'hx;
		endcase
	end
	assign start = (state == `BusIfStates__idle) & req_valid;
	assign req_addr = (arb_port_select == 0 ? fetch_request_addr : 31'b0) | (arb_port_select == 1 ? mem_request_addr : 31'b0) | (arb_port_select == 2 ? dma_request_addr : 31'b0);
	assign req_data = (arb_port_select == 0 ? fetch_request_data : 16'b0) | (arb_port_select == 1 ? mem_request_data : 16'b0) | (arb_port_select == 2 ? $signed(1'bX) : 16'b0);
	always @(*) begin
		unique case (arb_port_select)
			2'd0: req_read_not_write = fetch_request_read_not_write;
			2'd1: req_read_not_write = mem_request_read_not_write;
			2'd2: req_read_not_write = dma_request_read_not_write;
			2'd3: req_read_not_write = 1'h1;
			default: req_read_not_write = 1'hx;
		endcase
	end
	assign req_byte_en = (arb_port_select == 0 ? fetch_request_byte_en : 2'b0) | (arb_port_select == 1 ? mem_request_byte_en : 2'b0) | (arb_port_select == 2 ? dma_request_byte_en : 2'b0);
	assign req_dram = (req_addr[26:25] != 1'h0) & ((arb_port_select == `Ports__mem_port) | (arb_port_select == `Ports__fetch_port));
	assign req_dma = (arb_port_select == `Ports__dma_port) &  ~ dma_request_is_master;
	always_ff @(posedge clk) u118_output_port <= rst ? 1'h0 : start ? req_dram | req_dma : u118_output_port;
	always_ff @(posedge clk) wait_states_store <= rst ? 4'h0 : start ? u123_output_port[3:0] : wait_states_store;
	always_ff @(posedge clk) wait_states <= rst ? 4'h0 : start ? u123_output_port[3:0] : wait_states == 1'h0 ? state == `BusIfStates__non_dram_dual ? wait_states_store : 1'h0 : u138_output_port[3:0];
	assign req_nram = (req_addr[26:25] == 1'h0) & ((arb_port_select == `Ports__mem_port) | (arb_port_select == `Ports__fetch_port));
	always_ff @(posedge clk) two_cycle_nram_access <= rst ? 1'h0 : start ? (req_byte_en == 2'h3) & req_nram : two_cycle_nram_access;
	always_ff @(posedge clk) nram_access <= rst ? 1'h0 : start ? req_nram : nram_access;
	assign event_bus_idle = (state == `BusIfStates__idle) & (next_state == `BusIfStates__idle);
	assign req_ext = (arb_port_select == `Ports__dma_port) & dma_request_is_master;
	assign req_rfsh = arb_port_select == `Ports__refresh_port;
	assign waiting =  ~ dram_n_wait | (wait_states != 1'h0);
	always @(*) begin
		unique case (dram_bank_size)
			2'd0: dram_bank_next = req_addr[16];
			2'd1: dram_bank_next = req_addr[18];
			2'd2: dram_bank_next = req_addr[20];
			2'd3: dram_bank_next = req_addr[22];
			default: dram_bank_next = 1'hx;
		endcase
	end
	always_ff @(posedge clk) u190_output_port <= rst ? 1'h0 : start ? dram_bank_next : u190_output_port;
	assign dram_bank = start ? dram_bank_next : u190_output_port;
	assign dram_addr_muxing = start ? req_dram | req_dma : u118_output_port;
	assign input_row_addr = dram_addr_muxing ? ({req_addr[21], req_addr[19], req_addr[17], req_addr[15:8]}) : req_addr[21:11];
	always_ff @(posedge clk) row_addr <= rst ? 11'h0 : start ? req_rfsh ? refresh_addr : input_row_addr : row_addr;
	assign req_advance = req_valid & req_ready;
	always_ff @(posedge clk) col_addr <= rst ? 11'h0 : req_advance ? dram_addr_muxing ? ({req_addr[20], req_addr[18], req_addr[16], req_addr[7:0]}) : req_addr[10:0] : col_addr;
	always_ff @(posedge clk) read_not_write <= rst ? 1'h1 : start ? req_read_not_write : read_not_write;
	initial read_not_write <= 1'h1;
	always_ff @(posedge clk) data_out_en <= rst ? 1'h0 : start ?  ~ req_read_not_write & (arb_port_select != `Ports__dma_port) : data_out_en;
	always_ff @(posedge clk) u216_output_port <= rst ? 2'h0 : req_advance ? req_byte_en : u216_output_port;
	assign byte_en = req_advance ? req_byte_en : u216_output_port;
	always_ff @(posedge clk) data_out <= rst ? 16'h0 : req_advance ? req_byte_en[0] ? req_data : ({req_data[7:0], req_data[7:0]}) : data_out;
	assign dram_ras_active = (next_state == `BusIfStates__first) | (next_state == `BusIfStates__middle) | (next_state == `BusIfStates__precharge) | (next_state == `BusIfStates__dma_first) | (next_state == `BusIfStates__dma_wait);
	always_ff @(posedge clk) dram_ras_a <= rst ? 1'h0 : dram_ras_active & (dram_bank == dram_bank_swap) | (next_state == `BusIfStates__refresh);
	always_ff @(posedge clk) dram_ras_b <= rst ? 1'h0 : dram_ras_active & (dram_bank != dram_bank_swap) | (next_state == `BusIfStates__refresh);
	always_ff @(posedge clk) n_nren <= rst ? 1'h1 : (next_state != `BusIfStates__non_dram_first) & (next_state != `BusIfStates__non_dram_wait) & (next_state != `BusIfStates__non_dram_dual_first) & (next_state != `BusIfStates__non_dram_dual_wait);
	initial n_nren <= 1'h1;
	always_ff @(posedge clk) dma_ch <= rst ? 4'h0 : start ? dma_request_one_hot_channel : dma_ch;
	always_ff @(posedge clk) u278_output_port <= rst ? 4'h0 : (state == `BusIfStates__dma_first) | (state == `BusIfStates__dma_wait) & waiting | (state == `BusIfStates__external) & req_valid & req_ext ? dma_ch : 1'h0;
	assign n_dack =  ~ u278_output_port;
	assign nr_cas_logic = (state == `BusIfStates__non_dram_dual_first) | (state == `BusIfStates__non_dram_first) | (state == `BusIfStates__dma_first) | waiting & ((state == `BusIfStates__non_dram_dual_wait) | (state == `BusIfStates__non_dram_wait) | (state == `BusIfStates__dma_wait));
	assign nr_cas_logic_0 = nr_cas_logic & ( ~ two_cycle_nram_access | (state == `BusIfStates__non_dram_first) | (state == `BusIfStates__non_dram_wait) | (state == `BusIfStates__dma_first) | (state == `BusIfStates__dma_wait));
	always_ff @(posedge clk) nr_n_cas_0 <= rst ? 1'h1 :  ~ nr_cas_logic_0 |  ~ byte_en[0];
	initial nr_n_cas_0 <= 1'h1;
	assign nr_cas_logic_1 = nr_cas_logic & ( ~ two_cycle_nram_access | (state == `BusIfStates__non_dram_dual_first) | (state == `BusIfStates__non_dram_dual_wait) | (state == `BusIfStates__dma_first) | (state == `BusIfStates__dma_wait));
	always_ff @(posedge clk) nr_n_cas_1 <= rst ? 1'h1 :  ~ nr_cas_logic_1 |  ~ byte_en[1];
	initial nr_n_cas_1 <= 1'h1;
	always_ff @(posedge clk) cas_n_window_a_0 <= rst ? 1'h1 :  ~ byte_en[0] | (next_state == `BusIfStates__idle) | (next_state == `BusIfStates__precharge) | (next_state == `BusIfStates__non_dram_first) | (next_state == `BusIfStates__non_dram_wait) | (next_state == `BusIfStates__non_dram_dual) | (next_state == `BusIfStates__non_dram_dual_first) | (next_state == `BusIfStates__non_dram_dual_wait) | (next_state == `BusIfStates__non_dram_last) | (next_state == `BusIfStates__dma_first) | (next_state == `BusIfStates__dma_wait) | (next_state == `BusIfStates__refresh);
	initial cas_n_window_a_0 <= 1'h1;
	always_ff @(posedge clk) cas_n_window_a_1 <= rst ? 1'h1 :  ~ byte_en[1] | (next_state == `BusIfStates__idle) | (next_state == `BusIfStates__precharge) | (next_state == `BusIfStates__non_dram_first) | (next_state == `BusIfStates__non_dram_wait) | (next_state == `BusIfStates__non_dram_dual) | (next_state == `BusIfStates__non_dram_dual_first) | (next_state == `BusIfStates__non_dram_dual_wait) | (next_state == `BusIfStates__non_dram_last) | (next_state == `BusIfStates__dma_first) | (next_state == `BusIfStates__dma_wait) | (next_state == `BusIfStates__refresh);
	initial cas_n_window_a_1 <= 1'h1;
	always_ff @(negedge clk) cas_n_window_b_0 <= rst ? 1'h1 : cas_n_window_a_0;
	initial cas_n_window_b_0 <= 1'h1;
	always_ff @(posedge clk) cas_n_window_c_1 <= rst ? 1'h1 : cas_n_window_a_1;
	initial cas_n_window_c_1 <= 1'h1;
	always_ff @(negedge clk) cas_n_window_b_1 <= rst ? 1'h1 : cas_n_window_a_1;
	initial cas_n_window_b_1 <= 1'h1;
	assign dram_n_ras_a_1 =  ~ dram_ras_a;
	assign dram_n_ras_b_1 =  ~ dram_ras_b;
	assign dram_n_cas_0_1 = cas_n_window_a_0 | cas_n_window_b_0 | clk;
	assign dram_n_cas_0 = dram_n_cas_0_1 & nr_n_cas_0;
	assign dram_n_cas_1_1 = cas_n_window_b_1 | cas_n_window_c_1 |  ~ clk;
	assign dram_n_cas_1 = dram_n_cas_1_1 & nr_n_cas_1;
	always_ff @(negedge clk) col_addr_nr <= rst ? 11'h0 : col_addr;
	assign dram_addr_1 = ((state == `BusIfStates__first) | (state == `BusIfStates__non_dram_first) | (state == `BusIfStates__non_dram_dual_first) | (state == `BusIfStates__dma_first) | (state == `BusIfStates__refresh)) & clk ? row_addr : col_addr_nr;
	always_ff @(posedge clk) nr_cas_logic_1_reg <= rst ? 1'h0 : n_nren ? 1'h0 : nr_cas_logic_1_reg | nr_cas_logic_1;
	always_ff @(negedge clk) data_out_low <= rst ? 8'h0 : nram_access ? two_cycle_nram_access & (nr_cas_logic_1_reg | nr_cas_logic_1 |  ~ nr_n_cas_1) ? data_out[15:8] : data_out[7:0] : data_out[7:0];
	always_ff @(posedge clk) data_out_high <= rst ? 8'h0 : nram_access ? two_cycle_nram_access & (nr_cas_logic_1_reg | nr_cas_logic_1) ? data_out[15:8] : data_out[7:0] : data_out[15:8];
	assign dram_data_out = clk ? data_out_high : data_out_low;
	always_ff @(posedge clk) tc <= rst ? 1'h0 : start ? dma_request_terminal_count : tc;
	assign dram_bus_en = state != `BusIfStates__external;
	assign read_active = ((state == `BusIfStates__first) | (state == `BusIfStates__middle) | (state == `BusIfStates__dma_wait) &  ~ waiting | (state == `BusIfStates__non_dram_wait) &  ~ waiting &  ~ two_cycle_nram_access | (state == `BusIfStates__non_dram_dual_wait) &  ~ waiting) & read_not_write;
	always_ff @(posedge clk) data_in_low <= rst ? 8'h0 : (state == `BusIfStates__non_dram_wait) | (state == `BusIfStates__first) | (state == `BusIfStates__middle) ? dram_data_in : data_in_low;
	always_ff @(posedge clk) ndram_data_in_high <= rst ? 8'h0 : (state == `BusIfStates__non_dram_dual_wait) ? dram_data_in : ndram_data_in_high;
	always_ff @(negedge clk) u502_output_port <= rst ? 8'h0 : dram_data_in;
	assign data_in_high = nram_access ? two_cycle_nram_access ? ndram_data_in_high : data_in_low : u502_output_port;
	always @(*) begin
		unique case (byte_en)
			2'd0: u510_output_port = $signed(1'bX);
			2'd1: u510_output_port = {8'h0, data_in_low};
			2'd2: u510_output_port = {8'h0, data_in_high};
			2'd3: u510_output_port = {data_in_high, data_in_low};
			default: u510_output_port = 16'hx;
		endcase
	end
	always_ff @(posedge clk) resp_data <= rst ? 16'h0 : u510_output_port;
	always_ff @(posedge clk) u516_output_port <= rst ? 1'h0 : read_active & (arb_port_select == `Ports__mem_port);
	always_ff @(posedge clk) mem_response_valid <= rst ? 1'h0 : u516_output_port;
	always_ff @(posedge clk) u521_output_port <= rst ? 1'h0 : read_active & (arb_port_select == `Ports__fetch_port);
	always_ff @(posedge clk) fetch_response_valid <= rst ? 1'h0 : u521_output_port;
	assign dma_response_valid = (state == `BusIfStates__dma_wait) &  ~ waiting;
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
		.input_idle_to_external(u161_output_port),
		.input_idle_to_non_dram_first(u162_output_port),
		.input_idle_to_dma_first(u163_output_port),
		.input_idle_to_first(u164_output_port),
		.input_idle_to_refresh(u165_output_port),
		.input_external_to_idle(u167_output_port),
		.input_external_to_idle_1(u168_output_port),
		.input_first_to_precharge(u169_output_port),
		.input_first_to_middle(req_valid),
		.input_middle_to_precharge(u170_output_port),
		.input_precharge_to_idle(u171_output_port),
		.input_non_dram_first_to_non_dram_wait(u172_output_port),
		.input_non_dram_wait_to_non_dram_wait(waiting),
		.input_non_dram_wait_to_non_dram_dual(u174_output_port),
		.input_non_dram_wait_to_non_dram_last(u177_output_port),
		.input_non_dram_dual_to_non_dram_dual_first(u178_output_port),
		.input_non_dram_dual_first_to_non_dram_dual_wait(u179_output_port),
		.input_non_dram_dual_wait_to_non_dram_dual_wait(waiting),
		.input_non_dram_dual_wait_to_non_dram_last(u180_output_port),
		.input_non_dram_last_to_idle(u181_output_port),
		.input_dma_first_to_dma_wait(u182_output_port),
		.input_dma_wait_to_dma_wait(waiting),
		.input_dma_wait_to_idle(u183_output_port),
		.input_refresh_to_idle(u184_output_port)
	);

	assign u34_output_port = refresh_counter - 1'h1 + 9'b0;
	assign dram_tc = tc;
	assign u123_output_port = req_addr[30:27] - 1'h1 + 5'b0;
	assign u138_output_port = wait_states - ((state == `BusIfStates__dma_wait) | (state == `BusIfStates__non_dram_dual_wait) | (state == `BusIfStates__non_dram_wait)) + 5'b0;
	assign u161_output_port = req_valid & req_ext;
	assign u162_output_port = req_valid & req_nram;
	assign u163_output_port = req_valid & req_dma;
	assign u164_output_port = req_valid & req_dram;
	assign u165_output_port = req_valid & req_rfsh;
	assign u167_output_port = req_valid &  ~ req_ext;
	assign u168_output_port =  ~ req_valid;
	assign u169_output_port =  ~ req_valid;
	assign u170_output_port =  ~ req_valid;
	assign u171_output_port = 1'h1;
	assign u172_output_port = 1'h1;
	assign u174_output_port =  ~ waiting & two_cycle_nram_access;
	assign u177_output_port =  ~ waiting &  ~ two_cycle_nram_access;
	assign u178_output_port = 1'h1;
	assign u179_output_port = 1'h1;
	assign u180_output_port =  ~ waiting;
	assign u181_output_port = 1'h1;
	assign u182_output_port = 1'h1;
	assign u183_output_port =  ~ waiting;
	assign u184_output_port = 1'h1;
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
	input logic reset_value,
	output logic state,
	output logic next_state,
	input logic default_state,
	input logic input_idle_to_request,
	input logic input_request_to_idle
);

	logic local_state;
	logic local_next_state;

	always_ff @(posedge clock_port) local_state <= reset_port ? reset_value : local_next_state;
	initial local_state <= reset_value;

	FSMLogic_2 fsm_logic (
		.state(local_state),
		.next_state(local_next_state),
		.default_state(default_state),
		.input_idle_to_request(input_idle_to_request),
		.input_request_to_idle(input_request_to_idle)
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
	input logic input_non_dram_wait_to_non_dram_last,
	input logic input_non_dram_dual_to_non_dram_dual_first,
	input logic input_non_dram_dual_first_to_non_dram_dual_wait,
	input logic input_non_dram_dual_wait_to_non_dram_dual_wait,
	input logic input_non_dram_dual_wait_to_non_dram_last,
	input logic input_non_dram_last_to_idle,
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
		.input_non_dram_wait_to_non_dram_last(input_non_dram_wait_to_non_dram_last),
		.input_non_dram_dual_to_non_dram_dual_first(input_non_dram_dual_to_non_dram_dual_first),
		.input_non_dram_dual_first_to_non_dram_dual_wait(input_non_dram_dual_first_to_non_dram_dual_wait),
		.input_non_dram_dual_wait_to_non_dram_dual_wait(input_non_dram_wait_to_non_dram_wait),
		.input_non_dram_dual_wait_to_non_dram_last(input_non_dram_dual_wait_to_non_dram_last),
		.input_non_dram_last_to_idle(input_non_dram_last_to_idle),
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
		((state == `InstAssembleStates__have_0_fragments) ? state_have_0_fragments_selector : 2'b0) | 
		((state == `InstAssembleStates__need_1_fragments) ? state_need_1_fragments_selector : 2'b0) | 
		((state == `InstAssembleStates__need_2_fragments) ? state_need_2_fragments_selector : 2'b0) | 
		((state == `InstAssembleStates__have_all_fragments) ? state_have_all_fragments_selector : 2'b0) | 
		((state == `InstAssembleStates__have_0_fragments) | (state == `InstAssembleStates__need_1_fragments) | (state == `InstAssembleStates__need_2_fragments) | (state == `InstAssembleStates__have_all_fragments) ? 2'b0 : default_state);

endmodule


////////////////////////////////////////////////////////////////////////////////
// FSMLogic_2
////////////////////////////////////////////////////////////////////////////////
module FSMLogic_2 (
	input logic state,
	output logic next_state,
	input logic default_state,
	input logic input_idle_to_request,
	input logic input_request_to_idle
);

	logic state_idle_selector;
	logic state_request_selector;

	assign state_idle_selector = (input_idle_to_request ? `InstBufferStates__request : 1'b0) | (input_idle_to_request ? 1'b0 : `InstBufferStates__idle);
	assign state_request_selector = (input_request_to_idle ? `InstBufferStates__idle : 1'b0) | (input_request_to_idle ? 1'b0 : `InstBufferStates__request);
	assign next_state = ((state == `InstBufferStates__idle) ? state_idle_selector : 1'b0) | ((state == `InstBufferStates__request) ? state_request_selector : 1'b0) | ((state == `InstBufferStates__idle) | (state == `InstBufferStates__request) ? 1'b0 : default_state);

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
	input logic input_non_dram_wait_to_non_dram_last,
	input logic input_non_dram_dual_to_non_dram_dual_first,
	input logic input_non_dram_dual_first_to_non_dram_dual_wait,
	input logic input_non_dram_dual_wait_to_non_dram_dual_wait,
	input logic input_non_dram_dual_wait_to_non_dram_last,
	input logic input_non_dram_last_to_idle,
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
	logic [3:0] state_non_dram_last_selector;
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
	assign state_non_dram_wait_selector = (input_non_dram_wait_to_non_dram_wait ? `BusIfStates__non_dram_wait : 4'b0) | (input_non_dram_wait_to_non_dram_dual ? `BusIfStates__non_dram_dual : 4'b0) | (input_non_dram_wait_to_non_dram_last ? `BusIfStates__non_dram_last : 4'b0) | (input_non_dram_wait_to_non_dram_wait | input_non_dram_wait_to_non_dram_dual | input_non_dram_wait_to_non_dram_last ? 4'b0 : `BusIfStates__non_dram_wait);
	assign state_non_dram_dual_selector = (input_non_dram_dual_to_non_dram_dual_first ? `BusIfStates__non_dram_dual_first : 4'b0) | (input_non_dram_dual_to_non_dram_dual_first ? 4'b0 : `BusIfStates__non_dram_dual);
	assign state_non_dram_dual_first_selector = (input_non_dram_dual_first_to_non_dram_dual_wait ? `BusIfStates__non_dram_dual_wait : 4'b0) | (input_non_dram_dual_first_to_non_dram_dual_wait ? 4'b0 : `BusIfStates__non_dram_dual_first);
	assign state_non_dram_dual_wait_selector = (input_non_dram_wait_to_non_dram_wait ? `BusIfStates__non_dram_dual_wait : 4'b0) | (input_non_dram_dual_wait_to_non_dram_last ? `BusIfStates__non_dram_last : 4'b0) | (input_non_dram_wait_to_non_dram_wait | input_non_dram_dual_wait_to_non_dram_last ? 4'b0 : `BusIfStates__non_dram_dual_wait);
	assign state_non_dram_last_selector = (input_non_dram_last_to_idle ? `BusIfStates__idle : 4'b0) | (input_non_dram_last_to_idle ? 4'b0 : `BusIfStates__non_dram_last);
	assign state_dma_first_selector = (input_dma_first_to_dma_wait ? `BusIfStates__dma_wait : 4'b0) | (input_dma_first_to_dma_wait ? 4'b0 : `BusIfStates__dma_first);
	assign state_dma_wait_selector = (input_non_dram_wait_to_non_dram_wait ? `BusIfStates__dma_wait : 4'b0) | (input_dma_wait_to_idle ? `BusIfStates__idle : 4'b0) | (input_non_dram_wait_to_non_dram_wait | input_dma_wait_to_idle ? 4'b0 : `BusIfStates__dma_wait);
	assign state_refresh_selector = (input_refresh_to_idle ? `BusIfStates__idle : 4'b0) | (input_refresh_to_idle ? 4'b0 : `BusIfStates__refresh);
	assign next_state = 
		((state == `BusIfStates__idle) ? state_idle_selector : 4'b0) | 
		((state == `BusIfStates__external) ? state_external_selector : 4'b0) | 
		((state == `BusIfStates__first) ? state_first_selector : 4'b0) | 
		((state == `BusIfStates__middle) ? state_middle_selector : 4'b0) | 
		((state == `BusIfStates__precharge) ? state_precharge_selector : 4'b0) | 
		((state == `BusIfStates__non_dram_first) ? state_non_dram_first_selector : 4'b0) | 
		((state == `BusIfStates__non_dram_wait) ? state_non_dram_wait_selector : 4'b0) | 
		((state == `BusIfStates__non_dram_dual) ? state_non_dram_dual_selector : 4'b0) | 
		((state == `BusIfStates__non_dram_dual_first) ? state_non_dram_dual_first_selector : 4'b0) | 
		((state == `BusIfStates__non_dram_dual_wait) ? state_non_dram_dual_wait_selector : 4'b0) | 
		((state == `BusIfStates__non_dram_last) ? state_non_dram_last_selector : 4'b0) | 
		((state == `BusIfStates__dma_first) ? state_dma_first_selector : 4'b0) | 
		((state == `BusIfStates__dma_wait) ? state_dma_wait_selector : 4'b0) | 
		((state == `BusIfStates__refresh) ? state_refresh_selector : 4'b0) | 
		((state == `BusIfStates__idle) | (state == `BusIfStates__external) | (state == `BusIfStates__first) | (state == `BusIfStates__middle) | (state == `BusIfStates__precharge) | (state == `BusIfStates__non_dram_first) | (state == `BusIfStates__non_dram_wait) | (state == `BusIfStates__non_dram_dual) | (state == `BusIfStates__non_dram_dual_first) | (state == `BusIfStates__non_dram_dual_wait) | (state == `BusIfStates__non_dram_last) | (state == `BusIfStates__dma_first) | (state == `BusIfStates__dma_wait) | (state == `BusIfStates__refresh) ? 4'b0 : default_state);

endmodule


