

def create_selector_verilog(masklist):
    fields = "dcba"
    terms = []
    for mask in masklist:
        andterms = []
        for digit, field in zip(mask, fields):
            if (digit == "."):
                andterms.append(f"(field_{field}_is_not_f)")
            elif (digit == "*"):
                pass
            else:
                andterms.append(f"(field_{field} == 4'h{digit})")
        terms.append(" & ".join(andterms))
    selector = " | ".join(f"({x})" for x in terms)
    return selector


with open("masklist_full.txt","rt") as f:
    selectors = []
    for line in f:
        masks = line.replace("\n","").split(",")
        selectors.append(create_selector_verilog(masks))



with open("raw.sv","wt") as wf:
    selector_names = [f"selector_{i}" for i in range(len(selectors))]

    wf.write("module xxx (\n")
    wf.write("    input logic [3:0] field_a,\n")
    wf.write("    input logic [3:0] field_b,\n")
    wf.write("    input logic [3:0] field_c,\n")
    wf.write("    input logic [3:0] field_d,\n")
    wf.write("    input logic field_a_is_not_f,\n")
    wf.write("    input logic field_b_is_not_f,\n")
    wf.write("    input logic field_c_is_not_f,\n")
    wf.write("    input logic field_d_is_not_f,\n\n")
    for selector_name in selector_names:
        wf.write(f"    output logic {selector_name},\n")
    wf.write("    output logic ignore\n")
    wf.write(");\n")

    for selector_name, selector in zip(selector_names, selectors):
        wf.write(f"    assign {selector_name} = {selector};\n")
    wf.write("endmodule\n")
