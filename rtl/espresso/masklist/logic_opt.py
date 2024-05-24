"""
It really seems that this optimization process buys us about 10%
improvement in logic synthesis. The (commented-out) trivial CSE
where the comparisons are broken out into their separate wires
generated 0 difference in Quartus and a single LUT savings in
GoWin. This indicates that CSE is rather effective in the existing
synthesis tools, so not worth bothering with.

I also am running low on ideas as to how to squeeze more out
of the synthesis tools, so I think I'll give up and concentrate
instead on the integration into the Decode stage.

The idea is that - even if it doesn't help tremendously with area,
it can still help a lot with elaboration and simulation times if
the whole decode logic is abstracted into a single 'Module' instance.
"""

from silicon import *

import sys
from pathlib import Path
sys.path.append(str((Path() / "..").absolute()))
from copy import deepcopy

from synth import QuartusFlow

def mask_to_verilog(mask: str) -> str:
    fields = "dcba"
    terms = []
    for digit, field in zip(mask, fields):
        if (digit == "."):
            terms.append(f"field_{field}_is_not_f")
        elif (digit in "_*"):
            pass
        else:
            terms.append(f"(field_{field} == 4'h{digit})")
            #terms.append(f"field_{field}_is_{digit}")
    verilog = " & ".join(terms)
    if len(terms) > 1:
        verilog = "(" + verilog + ")"
    return verilog

def create_selector_verilog(selector: OrderedDict[str, OrderedDict], indent = 2):
    assert selector is not None
    terms = []
    for mask, sub_selectors in selector.items():
        vmask = "    " * indent + mask_to_verilog(mask)
        if sub_selectors is not None:
            and_terms = create_selector_verilog(sub_selectors, indent + 1)
            vmask = vmask + " & (\n" + and_terms + "\n" + "    " * indent + ")"
        terms.append(vmask)
    joiner = " |\n"
    selector = joiner.join(terms)
    return selector

def write_selectors(file, selectors, module_name):
    selector_names = [f"selector_{i}" for i in range(len(selectors))]

    file.write(f"module {module_name} (\n")
    file.write("    input logic [3:0] field_a,\n")
    file.write("    input logic [3:0] field_b,\n")
    file.write("    input logic [3:0] field_c,\n")
    file.write("    input logic [3:0] field_d,\n")
    file.write("    input logic field_a_is_not_f,\n")
    file.write("    input logic field_b_is_not_f,\n")
    file.write("    input logic field_c_is_not_f,\n")
    file.write("    input logic field_d_is_not_f,\n\n")
    for selector_name in selector_names:
        file.write(f"    output logic {selector_name},\n")
    file.write("    input logic clk\n")
    file.write(");\n")
    #for field in "abcd":
    #    for test in "0123456879abcdef":
    #        file.write(f"    logic field_{field}_is_{test};\n")
    #file.write("\n")
    #for field in "abcd":
    #    for test in "0123456879abcdef":
    #        file.write(f"    assign field_{field}_is_{test} = field_{field} == 4'h{test};\n")
    #file.write("\n\n")

    for selector_name, selector in zip(selector_names, selectors):
        vselect = create_selector_verilog(selector)
        file.write(f"    assign {selector_name} =\n{vselect};\n")
    file.write("endmodule\n")

def write_comparison_verilog(file, selectors1, selectors2, module_name):
    comparison_names = [f"comparison_{i}" for i in range(len(selectors1))]
    selector_names1 = [f"selector1_{i}" for i in range(len(selectors1))]
    selector_names2 = [f"selector2_{i}" for i in range(len(selectors2))]

    file.write(f"module {module_name} (\n")
    file.write("    input logic [3:0] field_a,\n")
    file.write("    input logic [3:0] field_b,\n")
    file.write("    input logic [3:0] field_c,\n")
    file.write("    input logic [3:0] field_d,\n")
    file.write("    input logic field_a_is_not_f,\n")
    file.write("    input logic field_b_is_not_f,\n")
    file.write("    input logic field_c_is_not_f,\n")
    file.write("    input logic field_d_is_not_f,\n\n")
    for name in comparison_names:
        file.write(f"    output logic {name},\n")
    file.write("    input logic clk\n")
    file.write(");\n")

    #for field in "abcd":
    #    for test in "0123456879abcdef":
    #        file.write(f"    logic field_{field}_is_{test};\n")
    #file.write("\n")
    #for field in "abcd":
    #    for test in "0123456879abcdef":
    #        file.write(f"    assign field_{field}_is_{test} = field_{field} == 4'h{test};\n")
    #file.write("\n\n")

    for name in selector_names1:
        file.write(f"    logic {name};\n")
    file.write("\n")
    for name in selector_names2:
        file.write(f"    logic {name};\n")
    file.write("\n")

    for name, selector in zip(selector_names1, selectors1):
        vselect = create_selector_verilog(selector)
        file.write(f"    assign {name} =\n{vselect};\n")

    file.write("\n\n\n/////////////////////////////////////////////////////////////\n\n\n")

    for name, selector in zip(selector_names2, selectors2):
        vselect = create_selector_verilog(selector)
        file.write(f"    assign {name} =\n{vselect};\n")

    file.write("\n\n\n/////////////////////////////////////////////////////////////\n\n\n")

    for name, selector1, selector2 in zip(comparison_names, selector_names1, selector_names2):
        file.write(f"    assign {name} = {selector1} ^ {selector2};\n")

    file.write("endmodule\n")


def replace_char(s: str, idx: int, c: str) -> str:
    s = list(s)
    s[idx] = c
    return "".join(s)

# Return a new selector that's grouped into as few terms as possible.
#    This is a recursive algorithm
def optimize_once(selector: OrderedDict[str, OrderedDict]) -> OrderedDict[str, OrderedDict]:
    if len(selector) == 1: return selector
    # 1. Find the most common digit in all the 'key' masks
    counts = OrderedDict()
    digits = "*.0123456789abcdef_"
    for digit in digits:
        counts[digit] = [0,0,0,0]

    for key in selector.keys():
        for position in range(4):
            counts[key[position]][position] += 1

    selected_digit = None
    selected_position = None
    max_count = -1
    for digit, count_for_pos in counts.items():
        if digit == "_": continue
        if digit == "*": continue
        for idx, count in enumerate(count_for_pos):
            if count > max_count:
                max_count = count
                selected_digit = digit
                selected_position = idx

    # There's nothing to be optimized
    if max_count == -1:
        return selector
    if max_count == 1:
        return selector

    assert max_count != 0
    assert selected_position is not None
    assert selected_position is not None

    # 2. Create a group of all the terms that match the selected digit at the selected position
    optimized_selector = OrderedDict()
    optimized_term = replace_char("____", selected_position, selected_digit)
    optimized_sub_terms = OrderedDict()
    optimized_selector[optimized_term] = optimized_sub_terms
    for term, sub_terms in selector.items():
        if term[selected_position] == selected_digit:
            term = replace_char(term, selected_position, "_")
            optimized_sub_terms[term] = sub_terms
        else:
            optimized_selector[term] = sub_terms

    return optimized_selector

def optimize_recursively(selector: OrderedDict[str, OrderedDict]) -> OrderedDict[str, OrderedDict]:
    if selector is None: return None
    while True:
        optimized_selector = optimize_once(selector)
        if optimized_selector is selector:
            break
        selector = optimized_selector
    optimized_selector = OrderedDict()
    for term, sub_selectors in selector.items():
        optimized_selector[term] = optimize_recursively(sub_selectors)
    return optimized_selector

def merge_recursively(selector: OrderedDict[str, OrderedDict]) -> OrderedDict[str, OrderedDict]:
    if selector is None: return None

    # If a term has a single sub_selector, we can merge the two
    if len(selector) == 1:
        merged_selector = OrderedDict()
        term, sub_selectors = first(selector.items())
        if len(sub_selectors) == 1:
            term2, sub_selectors = first(sub_selectors.items())
            for digit in range(4):
                assert term2[digit] == "_" or term[digit] == "_"
                if term2[digit] != "_":
                    term = replace_char(term, digit, term2[digit])
            merged_selector[term] = sub_selectors
            changed = True
        else:
            merged_selector[term] = sub_selectors
    else:
        merged_selector = selector

    final_selector = OrderedDict()
    for term, sub_selectors in merged_selector.items():
        final_selector[term] = merge_recursively(sub_selectors)
    return final_selector

def optimize(selector: OrderedDict[str, OrderedDict]) -> OrderedDict[str, OrderedDict]:
    optimized_selector = optimize_recursively(deepcopy(selector))
    #optimized_selector = merge_recursively(optimized_selector)
    return optimized_selector

with open("masklist_full.txt","rt") as f:
    selectors = []
    for line in f:
        masks = line.replace("\n","").split(",")
        selector = OrderedDict()
        for mask in masks:
            selector[mask] = None
        selectors.append(selector)

with open("unoptimized.sv","wt") as wf:
    write_selectors(wf, selectors, "unoptimized")

optimized_selectors = [optimize(s) for s in selectors]

with open("optimized.sv","wt") as wf:
    write_selectors(wf, optimized_selectors, "optimized")

with open("comp.sv", "wt") as wf:
    write_comparison_verilog(wf, selectors, optimized_selectors, "comparison")

flow = QuartusFlow(
    target_dir="comp",
    top_level="comparison",
    source_files=("comp.sv",),
    clocks=(("clk", 10),),
    project_name="comp",
    no_timing_report_clocks="clk",
    family="MAX 10",
    device="10M50DAF672C7G" # Something large with a ton of pins
)
flow.generate()
flow.run()

flow = QuartusFlow(
    target_dir="optimized",
    top_level="optimized",
    source_files=("optimized.sv",),
    clocks=(("clk", 10),),
    project_name="optimized",
    no_timing_report_clocks="clk",
    family="MAX 10",
    device="10M50DAF672C7G" # Something large with a ton of pins
)
flow.generate()
flow.run()

flow = QuartusFlow(
    target_dir="unoptimized",
    top_level="unoptimized",
    source_files=("unoptimized.sv",),
    clocks=(("clk", 10),),
    project_name="unoptimized",
    no_timing_report_clocks="clk",
    family="MAX 10",
    device="10M50DAF672C7G" # Something large with a ton of pins
)
flow.generate()
flow.run()


