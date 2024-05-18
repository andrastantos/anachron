# This file contains helpers to drive the synthesis of a top-level module all the way from Silicon source to gates and reports

from typing import Sequence, Tuple, Optional, Dict
from dataclasses import dataclass

class QuartusException(Exception):
    pass

class QuartusFlow(object):
    @dataclass
    class IoAssignment(object):
        location: str
        io_standard: str

    def __init__(
        self,
        *,
        top_level: str,
        source_files: Sequence[str],
        constraint_files: Optional[Sequence[str]] = None,
        clocks: Sequence[Tuple[str, int]],
        device: str,
        target_dir="quartus",
        project_name=None,
        no_timing_report_clocks: Sequence[str] = None
    ):
        from pathlib import Path

        self.source_files = source_files
        self.clocks = clocks
        self.target_dir = Path(target_dir)
        self.project_name = project_name if project_name is not None else top_level.lower()
        self.top_level: str = top_level
        self.project_file_name = self.target_dir / f"{self.project_name}.qpf"
        self.no_timing_report_clocks = (no_timing_report_clocks, ) if isinstance(no_timing_report_clocks, str) else no_timing_report_clocks
        self.device = device
        self.constraint_files = constraint_files
        self.pin_assignments: Dict[str, QuartusFlow.IoAssignment] = {}
        self.custom_settings = []

    def add_pin_assignment(self, wire_name, pin_location, pin_io_standard):
        assert wire_name not in self.pin_assignments, f"Pin {wire_name} already has assignments"
        self.pin_assignments[wire_name] = self.IoAssignment(pin_location, pin_io_standard)

    def add_custom_setting(self, setting: str):
        self.custom_settings.append(setting)

    def generate(self):
        from datetime import datetime
        import os
        from pathlib import Path

        now_str = datetime.now().strftime('%H:%M:%S  %B %d, %Y')
        file_base_name = self.project_name

        # Step 0: create output directory
        self.target_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: generate SDC files
        if self.constraint_files is None:
            if self.clocks is not None:
                constraint_file_name = self.target_dir / f"{file_base_name}.sdc"
                with open(constraint_file_name, "wt") as clock_file:
                    for clock, speed in self.clocks:
                        clock_file.write(f"create_clock -name {clock} -period {1000/speed:.2f} [get_ports {{{clock}}}]\n")
                    clock_file.write(f"\nderive_clock_uncertainty\n")
                self.constraint_files = (constraint_file_name,)

        # Step 2: generate project file
        with open(self.project_file_name, "wt") as project_file:
            project_file.write(f"QUARTUS_VERSION = \"21.1\"\n")
            project_file.write(f"DATE = \"{now_str}\"\n")
            project_file.write(f"PROJECT_REVISION = \"{file_base_name}\"\n")

        output_directory = "output_files"
        qsf_file_name = self.target_dir / f"{file_base_name}.qsf"
        with open(qsf_file_name, "wt") as project_file:
            project_file.write(f"set_global_assignment -name FAMILY \"MAX 10\"\n")
            project_file.write(f"set_global_assignment -name DEVICE {self.device}\n")
            project_file.write(f"set_global_assignment -name TOP_LEVEL_ENTITY {self.top_level}\n")
            project_file.write(f"set_global_assignment -name ORIGINAL_QUARTUS_VERSION 21.1.0\n")
            project_file.write(f"set_global_assignment -name PROJECT_OUTPUT_DIRECTORY {output_directory}\n")
            project_file.write(f"set_global_assignment -name MIN_CORE_JUNCTION_TEMP \"0\"\n")
            project_file.write(f"set_global_assignment -name MAX_CORE_JUNCTION_TEMP 85\n")
            project_file.write(f"set_global_assignment -name ERROR_CHECK_FREQUENCY_DIVISOR 256\n")
            #project_file.write(f"set_global_assignment -name EDA_SIMULATION_TOOL "Questa Intel FPGA (Verilog)"\n")
            #project_file.write(f"set_global_assignment -name EDA_TIME_SCALE "1 ps" -section_id eda_simulation\n")
            #project_file.write(f"set_global_assignment -name EDA_OUTPUT_DATA_FORMAT "VERILOG HDL" -section_id eda_simulation\n")
            #project_file.write(f"set_global_assignment -name EDA_GENERATE_FUNCTIONAL_NETLIST OFF -section_id eda_board_design_timing\n")
            #project_file.write(f"set_global_assignment -name EDA_GENERATE_FUNCTIONAL_NETLIST OFF -section_id eda_board_design_symbol\n")
            #project_file.write(f"set_global_assignment -name EDA_GENERATE_FUNCTIONAL_NETLIST OFF -section_id eda_board_design_signal_integrity\n")
            #project_file.write(f"set_global_assignment -name EDA_GENERATE_FUNCTIONAL_NETLIST OFF -section_id eda_board_design_boundary_scan\n")
            #project_file.write(f"set_global_assignment -name POWER_PRESET_COOLING_SOLUTION ""23 MM HEAT SINK WITH 200 LFPM AIRFLOW""\n")
            #project_file.write(f"set_global_assignment -name POWER_BOARD_THERMAL_MODEL ""NONE (CONSERVATIVE)""\n")
            project_file.write(f"set_global_assignment -name PHYSICAL_SYNTHESIS_REGISTER_RETIMING ON\n")
            project_file.write(f"set_global_assignment -name FLOW_ENABLE_POWER_ANALYZER ON\n")
            if self.device.startswith("10M"):
                project_file.write(f"set_global_assignment -name INTERNAL_FLASH_UPDATE_MODE \"SINGLE COMP IMAGE WITH ERAM\"\n")
            #project_file.write(f"set_global_assignment -name POWER_DEFAULT_INPUT_IO_TOGGLE_RATE ""12.5 %""\n")
            for source in self.source_files:
                relative_source = Path(os.path.relpath(str(Path(source).absolute()), str(self.target_dir.absolute())))
                project_file.write(f"set_global_assignment -name SYSTEMVERILOG_FILE {relative_source}\n")
            if self.constraint_files is not None:
                for constraint_file_name in self.constraint_files:
                    relative_constraint = Path(os.path.relpath(str(Path(constraint_file_name).absolute()), str(self.target_dir.absolute())))
                    project_file.write(f"set_global_assignment -name SDC_FILE {relative_constraint}\n")
            #project_file.write(f"set_global_assignment -name PARTITION_NETLIST_TYPE SOURCE -section_id Top\n")
            #project_file.write(f"set_global_assignment -name PARTITION_FITTER_PRESERVATION_LEVEL PLACEMENT_AND_ROUTING -section_id Top\n")
            #project_file.write(f"set_global_assignment -name PARTITION_COLOR 16764057 -section_id Top\n")
            #project_file.write(f"set_instance_assignment -name PARTITION_HIERARCHY root_partition -to | -section_id Top\n")
            for wire, assignments in self.pin_assignments.items():
                project_file.write(f"set_location_assignment {assignments.location} -to {wire}\n")
                project_file.write(f"set_instance_assignment -name IO_STANDARD \"{assignments.io_standard}\" -to {wire}\n")
            for setting in self.custom_settings:
                project_file.write(f"{setting}\n")

        # Step 3: generate timing report TCL script
        if self.clocks is not None:
            self.tcl_name = self.target_dir / f"{file_base_name}.timing_report.tcl"
            timing_report_file = Path(output_directory) / f"{file_base_name}.timing_report.txt"
            with open(self.tcl_name, "wt") as tcl_file:
                tcl_file.write(f"set PRJ {self.project_file_name}\n")
                tcl_file.write(f"set OUT {str(timing_report_file)}\n")
                tcl_file.write(f"project_open $PRJ\n")
                tcl_file.write(f"create_timing_netlist\n")
                tcl_file.write(f"read_sdc\n")
                tcl_file.write(f"update_timing_netlist\n")
                tcl_file.write(f"report_sdc -file $OUT\n")
                tcl_file.write(f"report_clocks -file $OUT -append\n")
                tcl_file.write(f"report_clock_fmax_summary -file $OUT -append\n")
                for clock, speed in self.clocks:
                    if self.no_timing_report_clocks is None or clock not in self.no_timing_report_clocks:
                        tcl_file.write(f"report_timing -from_clock {{{clock}}} -to_clock {{{clock}}} -setup -npaths 10 -detail summary -multi_corner -file $OUT -append\n")
                for clock, speed in self.clocks:
                    if self.no_timing_report_clocks is None or clock not in self.no_timing_report_clocks:
                        tcl_file.write(f"report_timing -from_clock {{{clock}}} -to_clock {{{clock}}} -setup -npaths 10 -detail full_path -multi_corner -file $OUT -append\n")

    def run(self):
        # Step 1: run tools
        tools = ("quartus_map", "quartus_fit", "quartus_asm", "quartus_sta")
        from subprocess import run
        for tool in tools:
            cmd = (tool, str(self.project_file_name))
            print(f"")
            print(f"")
            print(f"*******************************************************************")
            print(f"* Running tool '{' '.join(cmd)}' ")
            print(f"*******************************************************************")
            result = run(cmd)
            if result.returncode != 0:
                raise QuartusException(f"Quartus tool {tool} failed with error code {result.returncode}")

        if self.clocks is not None:
            cmd = ("quartus_sta", "-t", str(self.tcl_name))
            print(f"")
            print(f"")
            print(f"*******************************************************************")
            print(f"* Running tool '{' '.join(cmd)}' ")
            print(f"*******************************************************************")
            result = run(cmd)
            if result.returncode != 0:
                raise QuartusException(f"Quartus tool {cmd[0]} failed with error code {result.returncode}")


class LatticeException(Exception):
    pass

class LatticeFlow(object):
    def __init__(self, top_level: str, source_files: Sequence[str], clocks: Sequence[Tuple[str, int]], *, target_dir="lattice", project_name=None, no_timing_report_clocks: Sequence[str] = None):
        from pathlib import Path

        self.source_files = source_files
        self.clocks = clocks
        self.target_dir = Path(target_dir)
        self.project_name = project_name if project_name is not None else top_level.lower()
        self.top_level: str = top_level
        self.project_file_name = self.target_dir / f"{self.project_name}.project"
        self.syn_project_file_name = self.target_dir / f"{self.project_name}_syn.prj"
        self.no_timing_report_clocks = (no_timing_report_clocks, ) if isinstance(no_timing_report_clocks, str) else no_timing_report_clocks
        self.device_family = "iCE40"
        self.technology = f"SBT{self.device_family}"
        self.device = "HX8K"
        self.package = "CM225"
        self.speed_grade = ""
        self.part_companion = ""

    def generate(self):
        import os
        from pathlib import Path

        file_base_name = self.project_name

        # Step 0: create output directory
        self.target_dir.mkdir(parents=True, exist_ok=True)

        output_directory = f"{self.project_name}_Implmnt"
        self.output_directory = self.target_dir / output_directory

        # Step 1: generate SDC files
        constraint_file_name = None
        if self.clocks is not None:
            constraint_file_name = self.target_dir / f"{file_base_name}.sdc"
            with open(constraint_file_name, "wt") as clock_file:
                for clock, speed in self.clocks:
                    clock_file.write(f"create_clock -name {clock} -period {1000/speed:.2f} [get_ports {{{clock}}}]\n")
                clock_file.write(f"\nderive_clock_uncertainty\n")

        # Step 2: generate project file
        with open(self.project_file_name, "wt") as project_file:
            project_file.write(f"[Project]\n")
            project_file.write(f"ProjectVersion=2.0\n")
            project_file.write(f"Version=Lattice Semiconductor Corporation iCEcube - Release: 2020.12.27943 - Build Date: Dec 9 2020 18:31:09\n")
            project_file.write(f"ProjectName={self.project_name}\n")
            project_file.write(f"Vendor=SiliconBlue\n")
            project_file.write(f"Synthesis=synplify\n")
            sources=""
            for source in self.source_files:
                relative_source = Path(os.path.relpath(str(Path(source).absolute()), str(self.target_dir.absolute())))
                if sources != "": sources += ","
                sources += f"{relative_source.as_posix()}=work"
            project_file.write(f"ProjectVFiles={sources}\n")
            constraints=""
            if constraint_file_name is not None:
                relative_constraint = Path(os.path.relpath(str(Path(constraint_file_name).absolute()), str(self.target_dir.absolute())))
                if constraints != "": constraints += ","
                constraints += f"{relative_constraint.as_posix()}"
            project_file.write(f"ProjectCFiles={constraints}\n")
            project_file.write(f"CurImplementation={output_directory}\n")
            project_file.write(f"Implementations={output_directory}\n")
            project_file.write(f"StartFromSynthesis=yes\n")
            project_file.write(f"IPGeneration=false\n")
            project_file.write(f"\n")
            project_file.write(f"[{output_directory}]\n")
            project_file.write(f"DeviceFamily={self.device_family}\n")
            project_file.write(f"Device={self.device}\n")
            project_file.write(f"DevicePackage={self.package}\n")
            project_file.write(f"DevicePower=\n")
            project_file.write(f"NetlistFile={output_directory}/{self.project_name}.edf\n")
            project_file.write(f"AdditionalEDIFFile=\n")
            project_file.write(f"IPEDIFFile=\n")
            project_file.write(f"DesignLib=\n")
            project_file.write(f"DesignView=\n")
            project_file.write(f"DesignCell=\n")
            project_file.write(f"SynthesisSDCFile={output_directory}/{self.project_name}.scf\n")
            project_file.write(f"UserPinConstraintFile=\n")
            project_file.write(f"UserSDCFile=\n")
            project_file.write(f"PhysicalConstraintFile=\n")
            project_file.write(f"BackendImplPathName=\n")
            project_file.write(f"Devicevoltage=1.14\n")
            project_file.write(f"DevicevoltagePerformance=+/-5%(datasheet default)\n")
            project_file.write(f"DeviceTemperature=85\n")
            project_file.write(f"TimingAnalysisBasedOn=Worst\n")
            project_file.write(f"OperationRange=Commercial\n")
            project_file.write(f"TypicalCustomTemperature=25\n")
            project_file.write(f"WorstCustomTemperature=85\n")
            project_file.write(f"BestCustomTemperature=0\n")
            project_file.write(f"IOBankVoltages=topBank,2.5 bottomBank,2.5 leftBank,2.5 rightBank,2.5\n")
            project_file.write(f"derValue=0.701346\n")
            project_file.write(f"TimingPathNumberStick=0\n")
            project_file.write(f"\n")
            project_file.write(f"[lse options]\n")
            project_file.write(f"CarryChain=True\n")
            project_file.write(f"CarryChainLength=0\n")
            project_file.write(f"CommandLineOptions=\n")
            project_file.write(f"EBRUtilization=100.00\n")
            project_file.write(f"FSMEncodingStyle=Auto\n")
            project_file.write(f"FixGatedClocks=True\n")
            project_file.write(f"I/OInsertion=True\n")
            project_file.write(f"IntermediateFileDump=False\n")
            project_file.write(f"LoopLimit=1950\n")
            project_file.write(f"MaximalFanout=10000\n")
            project_file.write(f"MemoryInitialValueFileSearchPath=\n")
            project_file.write(f"NumberOfCriticalPaths=3\n")
            project_file.write(f"OptimizationGoal=Area\n")
            project_file.write(f"PropagateConstants=True\n")
            project_file.write(f"RAMStyle=Auto\n")
            project_file.write(f"ROMStyle=Auto\n")
            project_file.write(f"RWCheckOnRam=False\n")
            project_file.write(f"RemoveDuplicateRegisters=True\n")
            project_file.write(f"ResolvedMixedDrivers=False\n")
            project_file.write(f"ResourceSharing=True\n")
            project_file.write(f"TargetFrequency=\n")
            project_file.write(f"TopLevelUnit={self.top_level}\n")
            project_file.write(f"UseIORegister=Auto\n")
            project_file.write(f"VHDL2008=False\n")
            project_file.write(f"VerilogIncludeSearchPath=\n")
            project_file.write(f"\n")
            project_file.write(f"[tool options]\n")
            project_file.write(f"PlacerEffortLevel=std\n")
            project_file.write(f"PlacerAutoLutCascade=yes\n")
            project_file.write(f"PlacerAutoRamCascade=yes\n")
            project_file.write(f"PlacerPowerDriven=no\n")
            project_file.write(f"PlacerAreaDriven=no\n")
            project_file.write(f"RouteWithTimingDriven=yes\n")
            project_file.write(f"RouteWithPinPermutation=yes\n")
            project_file.write(f"BitmapSPIFlashMode=yes\n")
            project_file.write(f"BitmapRAM4KInit=yes\n")
            project_file.write(f"BitmapInitRamBank=1111\n")
            project_file.write(f"BitmapOscillatorFR=low\n")
            project_file.write(f"BitmapEnableWarmBoot=yes\n")
            project_file.write(f"BitmapDisableHeader=no\n")
            project_file.write(f"BitmapSetSecurity=no\n")
            project_file.write(f"BitmapSetNoUsedIONoPullup=no\n")
            project_file.write(f"FloorPlannerShowFanInNets=yes\n")
            project_file.write(f"FloorPlannerShowFanOutNets=yes\n")
            project_file.write(f"HookTo3rdPartyTextEditor=no\n")

        with open(self.syn_project_file_name, "wt") as project_file:
            # This is the SimplifyPro project file, not the iCECube one...
            project_file.write(f"#project files\n")
            project_file.write(f"\n")
            for source in self.source_files:
                relative_source = Path(os.path.relpath(str(Path(source).absolute()), str(self.target_dir.absolute())))
                project_file.write(f"add_file -verilog -lib work \"{relative_source.as_posix()}\"\n")
            if constraint_file_name is not None:
                relative_constraint = Path(os.path.relpath(str(Path(constraint_file_name).absolute()), str(self.target_dir.absolute())))
                project_file.write(f"add_file -constraint -lib work \"{relative_constraint.as_posix()}\"\n")
            project_file.write(f"#implementation: \"{output_directory}\"\n")
            project_file.write(f"impl -add {output_directory} -type fpga\n")
            project_file.write(f"\n")
            project_file.write(f"#implementation attributes\n")
            project_file.write(f"set_option -vlog_std v2001\n")
            project_file.write(f"set_option -project_relative_includes 1\n")
            project_file.write(f"\n")
            project_file.write(f"#device options\n")
            project_file.write(f"set_option -technology {self.technology}\n")
            project_file.write(f"set_option -part {self.device_family}{self.device}\n")
            project_file.write(f"set_option -package {self.package}\n")
            project_file.write(f"set_option -speed_grade {self.speed_grade}\n")
            project_file.write(f"set_option -part_companion \"{self.part_companion}\"\n")
            project_file.write(f"\n")
            project_file.write(f"#compilation/mapping options\n")
            project_file.write(f"\n")
            project_file.write(f"# mapper_options\n")
            project_file.write(f"set_option -frequency auto\n")
            project_file.write(f"set_option -write_verilog 0\n")
            project_file.write(f"set_option -write_vhdl 0\n")
            project_file.write(f"\n")
            project_file.write(f"# Silicon Blue iCE40\n")
            project_file.write(f"set_option -maxfan 10000\n")
            project_file.write(f"set_option -disable_io_insertion 0\n")
            project_file.write(f"set_option -pipe 1\n")
            ################################ SHOULD WE CHANGE THIS ??????????????????
            project_file.write(f"set_option -retiming 0\n")
            project_file.write(f"set_option -update_models_cp 0\n")
            project_file.write(f"set_option -fixgatedclocks 2\n")
            project_file.write(f"set_option -fixgeneratedclocks 0\n")
            project_file.write(f"\n")
            project_file.write(f"# NFilter\n")
            project_file.write(f"set_option -popfeed 0\n")
            project_file.write(f"set_option -constprop 0\n")
            project_file.write(f"set_option -createhierarchy 0\n")
            project_file.write(f"\n")
            project_file.write(f"# sequential_optimization_options\n")
            project_file.write(f"set_option -symbolic_fsm_compiler 1\n")
            project_file.write(f"\n")
            project_file.write(f"# Compiler Options\n")
            project_file.write(f"set_option -compiler_compatible 0\n")
            project_file.write(f"set_option -resource_sharing 1\n")
            project_file.write(f"\n")
            project_file.write(f"#automatic place and route (vendor) options\n")
            project_file.write(f"set_option -write_apr_constraint 1\n")
            project_file.write(f"\n")
            project_file.write(f"#set result format/file last\n")
            project_file.write(f"project -result_format \"edif\"\n")
            project_file.write(f"project -result_file \"./{output_directory}/{self.project_name}.edf\"\n")
            project_file.write(f"project -log_file \"./{output_directory}/{self.project_name}.srr\"\n")
            project_file.write(f"impl -active {output_directory}\n")
            project_file.write(f"project -run synthesis -clean\n")

    def run(self):
        import os
        from pathlib import Path

        is_win32 = os.name == "nt"
        if os.name not in ("nt", "posix"):
            raise LatticeException(f"Unknown platform: {os.name}")

        if is_win32:
            tool_base = Path("C:\\lscc\\iCEcube2.2020.12")
        else:
            tool_base = Path("/opt/lscc/iCEcube2.2020.12")

        sbt_backend_path = tool_base / "sbt_backend"
        tool_path = sbt_backend_path / "bin" / ("win32" if is_win32 else "linux") / "opt"

        output_dir = self.output_directory.absolute()
        device_dev = str(sbt_backend_path / "devices" / "ICE40P08.dev")
        sbt_dir = output_dir / "sbt"
        sbt_dir.mkdir(parents=True, exist_ok=True)
        sbt_outputs_dir = sbt_dir / "outputs"
        sbt_outputs_dir.mkdir(parents=True, exist_ok=True)
        design_lib = str(sbt_dir / "netlist" / f"oadb-{self.top_level}")
        device_lib = str(sbt_backend_path / "devices" / f"{self.device_family.lower()}{self.device}.lib")
        device_name = f"{self.device_family}{self.device}"


        from subprocess import run

        my_env = os.environ.copy()
        if "SYNPLIFY_PATH" not in my_env:
            my_env["SYNPLIFY_PATH"] = str(tool_base / "synpbase")
        if "LM_LICENSE_FILE" not in my_env:
            my_env["LM_LICENSE_FILE"] = str(tool_base / "license.dat")

        def run_tool(tool, cmd):
            print(f"")
            print(f"")
            print(f"*******************************************************************")
            print(f"* Running tool '{' '.join(cmd)}' ")
            print(f"*******************************************************************")
            result = run(cmd, env=my_env)
            if result.returncode != 0:
                raise LatticeException(f"Lattice tool {tool} failed with error code {result.returncode}")

        tool = "synpwrap"
        cmd = (str(tool_path / "synpwrap" / tool), "-prj", str(self.syn_project_file_name), "-log", str(self.target_dir / "brew_v1.srr"))
        run_tool(tool, cmd)

        tool = "edifparser"
        cmd = (
            str(tool_path / tool),
            device_dev,
            str(output_dir / f"{self.project_name}.edf"),
            str(sbt_dir / "netlist"),
            f"-p{self.package}",
            "-c",
            "--devicename", device_name
        )
        run_tool(tool, cmd)

        tool = "sbtplacer"
        cmd = (
            str(tool_path / tool),
            "--des-lib", design_lib,
            "--outdir", str(sbt_outputs_dir / "placer"),
            "--device-file", device_dev,
            "--package", self.package,
            "--deviceMarketName", device_name,
            "--sdc-file", str(sbt_dir / "Temp" / "sbt_temp.sdc"),
            "--lib-file", device_lib,
            "--effort_level", "std",
            "--out-sdc-file", str(sbt_outputs_dir / "placer" / f"{self.top_level}_pl.sdc")
        )
        run_tool(tool, cmd)

        (sbt_outputs_dir / "packer").mkdir(parents=True, exist_ok=True)
        tool = "packer"
        cmd = (
            str(tool_path / tool),
            device_dev,
            design_lib,
            "--package", self.package,
            "--outdir", str(sbt_outputs_dir / "packer"),
            "--DRC_only",
            "--translator", str(sbt_backend_path / "bin" / "sdc_translator.tcl"),
            "--src_sdc_file", str(sbt_outputs_dir / "placer" / f"{self.top_level}_pl.sdc"),
            "--dst_sdc_file", str(sbt_outputs_dir / "packer" / f"{self.top_level}_pk.sdc"),
            "--devicename", device_name,
        )
        run_tool(tool, cmd)

        tool = "packer"
        cmd = (
            str(tool_path / tool),
            device_dev,
            design_lib,
            "--package", self.package,
            "--outdir", str(sbt_outputs_dir / "packer"),
            "--translator", str(sbt_backend_path / "bin" / "sdc_translator.tcl"),
            "--src_sdc_file", str(sbt_outputs_dir / "placer" / f"{self.top_level}_pl.sdc"),
            "--dst_sdc_file", str(sbt_outputs_dir / "packer" / f"{self.top_level}_pk.sdc"),
            "--devicename", device_name,
        )
        run_tool(tool, cmd)

        (sbt_outputs_dir / "simulation_netlist").mkdir(parents=True, exist_ok=True)
        tool = "sbrouter"
        cmd = (
            str(tool_path / tool),
            device_dev,
            design_lib,
            device_lib,
            str(sbt_outputs_dir / "packer" / f"{self.top_level}_pk.sdc"),
            "--outdir", str(sbt_outputs_dir / "router"),
            "--sdf_file", str(sbt_outputs_dir / "simulation_netlist" / f"{self.top_level}_sbt.sdf"),
            "--pin_permutation"
        )
        run_tool(tool, cmd)

        (sbt_outputs_dir / "netlister").mkdir(parents=True, exist_ok=True)
        tool = "netlister"
        cmd = (
            str(tool_path / tool),
            "--verilog", str(sbt_outputs_dir / "simulation_netlist" / f"{self.top_level}_sbt.v"),
            "--vhdl", str(sbt_outputs_dir / "simulation_netlist" / f"{self.top_level}_sbt.vhd"),
            "--lib", design_lib,
            "--view", "rt",
            "--device", device_dev,
            "--splitio",
            "--in-sdc-file", str(sbt_outputs_dir / "packer" / f"{self.top_level}_pk.sdc"),
            "--out-sdc-file", str(sbt_outputs_dir / "netlister" / f"{self.top_level}_sbt.sdc"),
        )
        run_tool(tool, cmd)

        (sbt_outputs_dir / "timer").mkdir(parents=True, exist_ok=True)
        tool = "sbtimer"
        cmd = (
            str(tool_path / tool),
            "--des-lib", design_lib,
            "--lib-file", device_lib,
            "--sdc-file", str(sbt_outputs_dir / "netlister" / f"{self.top_level}_sbt.sdc"),
            "--sdf-file", str(sbt_outputs_dir / "simulation_netlist" / f"{self.top_level}_sbt.sdf"),
            "--report-file", str(sbt_outputs_dir / "timer" / f"{self.top_level}_timing.rpt"),
            "--device-file", device_dev,
            "--timing-summary",
        )
        run_tool(tool, cmd)

        tool = "bitmap"
        cmd = (
            str(tool_path / tool),
            device_dev,
            "--design", design_lib,
            "--device_name", device_name,
            "--package", self.package,
            "--outdir", str(sbt_outputs_dir / "bitmap"),
            "--low_power", "on",
            "--init_ram", "on",
            "--init_ram_bank", "1111",
            "--frequency", "low",
            "--warm_boot", "on",
        )
        run_tool(tool, cmd)

