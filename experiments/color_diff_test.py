from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import sRGBColor, LabColor


def sq(num: int) -> int:
    return num * num


def colors_distance(color1: sRGBColor, color2: sRGBColor) -> int:
    return (
        sq(255 * (color1.rgb_r - color2.rgb_r))
        + sq(255 * (color1.rgb_g - color2.rgb_g))
        + sq(255 * (color1.rgb_b - color2.rgb_b))
    )


#color1_rgb = sRGBColor(242 / 255.0, 252 / 255.0, 255 / 255.0)
color1_rgb = sRGBColor(223 / 255.0, 218 / 255.0, 185 / 255.0)

# color2_rgb = sRGBColor(231/255.0, 241/255.0, 247/255.0)
#color2_rgb = sRGBColor(221 / 255.0, 216 / 255.0, 198 / 255.0)
#color2_rgb = sRGBColor(238 / 255.0, 248 / 255.0, 253 / 255.0)
color2_rgb = sRGBColor(207 / 255.0, 216 / 255.0, 216 / 255.0)

color1_lab = convert_color(color1_rgb, LabColor)
color2_lab = convert_color(color2_rgb, LabColor)

delta_e = delta_e_cie2000(color1_lab, color2_lab)

print(f"Color difference delta_e = {delta_e}.")
print(f"Color difference euclid = {colors_distance(color1_rgb, color2_rgb)}.")
