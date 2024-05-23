# This is a quick test to ensure that the compression groups
# selected are indeed sane. That is: they don't overlap, every
# possible code decodes into up to one compression group.

# NOTE: undefined instructions should not decode into any of the groups.
compression_groups = (
    ("  .X..", "_12345678abcd__"),
    ("  .X.f", "_12345678______"),
    ("  .Xf.", "_12345678______"),
    ("  X000", "0123456789a____"),
    ("  .00X", "_12345_________"),
    ("  .0X.", "_123456789__cde"),
    ("  .00f", "_______________"),
    ("  20ef", "_______________"),
    ("  30ef", "_______________"),
    ("  40ef", "_______________"),
    ("  .0f0", "_______________"),
    ("  20fe", "_______________"),
    ("  30fe", "_______________"),
    ("  40fe", "_______________"),
    ("  f0X.", "0123456789abcd_"),
    ("  fX..", "_123456789abcde"),
    ("  f.f.", "_______________"),
    ("  f..f", "_______________"),
    ("  .c.f", "_______________"),
    ("  .cf.", "_______________"),
    ("  .cff", "_______________"),
    ("  .d.f", "_______________"),
    ("  .df.", "_______________"),
    ("  .dff", "_______________"),
    ("  .eX.", "____456789abcd_"),
    ("  1ee.", "_______________"),
    ("  2ee.", "_______________"),
    ("  3ee.", "_______________"),
    ("  4ee.", "_______________"),
    ("  .fX.", "____456789abcd_"),
    ("  1fe.", "_______________"),
    ("  2fe.", "_______________"),
    ("  3fe.", "_______________"),
    ("  4fe.", "_______________"),
    ("  .0f8", "_______________"),
    ("  .0f9", "_______________"),
    ("  .fXf", "____456789abcd_"),
    ("  1fef", "_______________"),
    ("  2fef", "_______________"),
    ("  3fef", "_______________"),
    ("  4fef", "_______________"),
)

def match(num: str, grp: str, x_match: str):
    grp = grp.strip()
    for (digit, g_digit) in zip(num, grp):
        if g_digit == "." and digit != "f": continue
        if g_digit == "X" and digit != "f":
            if digit in x_match: continue
            return False
        if g_digit != digit: return False
    return True

for i in range(0x10000):
    num = f"{i:04x}"
    found_grp = None
    for (grp, x_match) in compression_groups:
        if not match(num, grp, x_match): continue
        if found_grp is not None:
            print(f"code {num} matches grups {found_grp} and {grp}")
        found_grp = grp
    if found_grp is None:
        print(f"Code {num} doesn't match any groups")
