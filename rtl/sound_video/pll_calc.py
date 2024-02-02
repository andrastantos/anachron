# Calculate PLL settings for a desired frequency
# Good online resource for video timings: https://tomverbeure.github.io/video_timings_calculator
#  ... and of course: http://tinyvga.com/vga-timing
# The standard for CVT (coordinated video timing): https://glenwing.github.io/docs/VESA-CVT-1.2.pdf
# This defines the pixel clock precision (CLOCK_STEP) to be 0.25MHz.
# There are a set of standard timings as well: https://glenwing.github.io/docs/VESA-DMT-1.13.pdf
# For DMT, the tolerance appears to be +/-0.5%

f_in = 8
modes = (
    ("320x200@60 CVT",   5.000, 0.5, "MHz"),
    ("640x480@60 DMT",  25.175, 0.5, "%"),
    ("640x480@50 CVT",  20.750, 0.5, "MHz"),
    ("640x480@60 CVT",  25.250, 0.5, "MHz"),
    ("800x600@60 DMT",  40.000, 0.5, "%"),
    ("800x600@60 CVT",  40.000, 0.5, "MHz"),
    ("1024x768@60 DMT", 65.000, 0.5, "%"),
    ("1024x768@60 CVT", 68.000, 0.5, "MHz"),
    ("768x576@60 ???",  34.960, 0.5, "%")
)

vco_min = 400
vco_max = 1000
clkin_min = 3
clkin_max = 400

idiv_values = range(1,65)
fbdiv_values = range(1,65)
vcodiv_values = (2,4,8,16,32,48, 64, 80, 96, 112, 128)
sdiv_values = range(1,128) # NOTE: if sdiv is 1, that means we're using CLKOUT, not CLKOUTD

dvi_out = True

for v_info, f_out, accuracy, accuracy_type in modes:
    if dvi_out:
        f_out *= 5 # For the serializer, we actually need to generate 5x the pixel clock

    best_idiv = None
    best_fbdiv = None
    best_vcodiv = None
    best_sdiv = None
    best_freq = None
    best_error = None

    for sdiv in sdiv_values:
        for idiv in idiv_values:
            for fbdiv in fbdiv_values:
                for vcodiv in vcodiv_values:
                    f_cmp = f_in / idiv
                    if f_cmp < clkin_min: continue
                    if f_cmp > clkin_max: continue
                    f_vco = f_cmp * vcodiv * fbdiv
                    if f_vco < vco_min: continue
                    if f_vco > vco_max: continue
                    f_actual = f_vco / vcodiv / sdiv
                    error = abs(f_out - f_actual)
                    if best_error is None or best_error > error:
                        best_error = error
                        best_freq = f_actual
                        best_idiv = idiv
                        best_fbdiv = fbdiv
                        best_vcodiv = vcodiv
                        best_sdiv = sdiv
    if accuracy_type == "%":
        good_enough = abs(best_freq / f_out - 1) < (accuracy / 100)
    elif accuracy_type == "MHz":
        good_enough = best_error < accuracy
    else:
        good_enough = True
    print(f"For video mode {v_info}, output freq {f_out}: we get actual {best_freq} with idiv={best_idiv}, fbdiv={best_fbdiv}, vcodiv={best_vcodiv}, sdiv={best_sdiv}; is it good? {good_enough}")

