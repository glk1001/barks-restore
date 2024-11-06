from typing import Set, Tuple, Dict, List
from collections import OrderedDict

import cv2 as cv
import numpy as np

from remove_alias_artifacts import get_median_filter

# FANTAGRAPHICS_COLORS = {
#     (248, 242, 226),  # cream in all
#     (152, 100, 87),  # WDCS 87, page 4, panel 1
#     (163, 99, 71),  # WDCS 87, page 4, panel 1
#     (165, 96, 80),  # WDCS 87, page 4, panel 1
#     (173, 108, 80),  # WDCS 87, page 4, panel 1
#     (176, 112, 87),  # WDCS 87, page 4, panel 1
#     (178, 161, 135),  # WDCS 87, page 4, panel 1
#     (178, 217, 224),  # WDCS 87, page 4, panel 1
#     (181, 97, 71),  # WDCS 87, page 4, panel 1
#     (183, 218, 222),  # WDCS 104, page 1, panel 8
#     (184, 160, 136),  # WDCS 87, page 4, panel 1
#     (186, 111, 80),  # WDCS 87, page 4, panel 1
#     (194, 177, 183),  # WDCS 87, page 4, panel 1
#     (203, 115, 79),  # WDCS 87, page 4, panel 1
# }
COLOR_RANGE_MIN = -4
COLOR_RANGE_MAX = -COLOR_RANGE_MIN
COLOR_RANGE = range(COLOR_RANGE_MIN, COLOR_RANGE_MAX + 1)
FANTAGRAPHICS_COLORS = {
        (255, 191, 0),  # WDCS 104, page 1, panel 8
        (255, 191, 63),  # WDCS 104, page 1, panel 8
        (0, 191, 255),  # WDCS 104, page 1, panel 8
        (0, 191, 191),  # WDCS 104, page 1, panel 8
        (0, 127, 191),  # WDCS 104, page 1, panel 8
        (191, 0, 0),  # WDCS 104, page 1, panel 8
        (255, 0, 0),  # WDCS 104, page 1, panel 8
        (255, 63, 63),  # WDCS 104, page 1, panel 8
        (255, 0, 63),  # WDCS 104, page 1, panel 8
        (255, 63, 0),  # WDCS 104, page 1, panel 8
        (191, 255, 255),    # WDCS 87, page 4, panel 1
        (191, 191, 63),    # WDCS 87, page 4, panel 1
        (191, 127, 63),    # WDCS 87, page 4, panel 1
        (191, 0, 63),    # WDCS 87, page 4, panel 1
        (0, 62, 13),  # WDCS 87, page 4, panel 1
        (0, 191, 62),  # WDCS 87, page 4, panel 1
        (188, 187, 66),  # WDCS 87, page 4, panel 1
        (189, 128, 63),  # WDCS 87, page 4, panel 1
        (191, 191, 127),  # WDCS 87, page 4, panel 1
        (191, 191, 129),  # WDCS 87, page 4, panel 1
        (191, 191, 191),  # WDCS 87, page 4, panel 1
        (191, 192, 124),  # WDCS 87, page 4, panel 1
        (192, 255, 63),  # WDCS 87, page 4, panel 1
        (195, 62, 63),  # WDCS 87, page 4, panel 1
        (255, 127, 0),  # WDCS 87, page 4, panel 1
        (255, 191, 127),  # WDCS 87, page 4, panel 1
        (255, 190, 0),  # WDCS 87, page 4, panel 1
# remnants
# (63, 63, 0),
# (63, 0, 0),
# (0, 63, 0),
#(0, 63, 63),
#(0, 0, 63),
#(63, 0, 63),

        (124, 62, 65),  # WDCS 87, page 4, panel 1
        (83, 112, 82),  # WDCS 87, page 4, panel 1
        (122, 130, 71),  # WDCS 87, page 4, panel 1
        (127, 127, 63),
        (127, 63, 63),
(127, 63, 0),
(191, 255, 127),
(191, 63, 63),
(191, 127, 127),
(127, 191, 191),
(255, 127, 63),
(255, 255, 191),
(63, 127, 127),
(63, 127, 63),
(127, 127, 0),
(191, 127, 0),
(255, 191, 191),
(127, 191, 63),
(255, 255, 127),
(191, 191, 255),
(127, 191, 127),
(191, 255, 191),
(0, 127, 0),
(63, 63, 127),
(63, 127, 0),
(127, 127, 191),
(191, 127, 191),
(127, 63, 127),
(127, 0, 0),
(63, 191, 127),
(191, 63, 0),
(63, 191, 63),
(127, 255, 191),
(255, 255, 63),
(0, 191, 127),
(255, 191, 255),
(191, 191, 0),
(255, 127, 127),
(127, 191, 0),
(0, 127, 127),
}

def get_fuzzied_fantagraphics_colors() -> Set[Tuple[int, int, int]]:
    return FANTAGRAPHICS_COLORS

    fuzzied_set = set()

    for color in FANTAGRAPHICS_COLORS:
        for r in COLOR_RANGE:
            red = min(255, max(0, color[0] + r))
            for g in COLOR_RANGE:
                green = min(255, max(0, color[1] + g))
                for b in COLOR_RANGE:
                    blue = min(255, max(0, color[2] + b))
                    fuzz_color = (red, green, blue)
                    fuzzied_set.add(fuzz_color)

    return fuzzied_set


def posterize_image(image: cv.typing.MatLike):
    n = 5

    for i in range(n):
        image[(image >= i * 255 / n) & (image < (i + 1) * 255 / n)] = i * 255 / (n - 1)


def get_posterized_colors() -> List[Tuple[int,int,int]]:
    n = 5

    all_colors = []
    for r in range(n):
        red = int(r * 255 / (n - 1))
        for g in range(n):
            green = int(g * 255 / (n - 1))
            for b in range(n):
                blue = int(b * 255 / (n - 1))
                all_colors.append((red, green, blue))

    return all_colors


def get_color_counts(image: cv.typing.MatLike) -> Dict[Tuple[int,int,int], int]:
    image_h, image_w = image.shape[0], image.shape[1]

    all_colors = dict()

    for i in range(0, image_h):  ## traverse image row
        for j in range(0, image_w):  ## traverse image col
            pixel = image[i][j]
            red = int(pixel[2])
            green = int(pixel[1])
            blue = int(pixel[0])

            color = (red, green, blue)

            if color in all_colors:
                all_colors[color] += 1
            else:
                all_colors[color] = 1

    return all_colors


def remove_colors(
    colors: Set[Tuple[int, int, int]],
    grey_img: cv.typing.MatLike,
    image: cv.typing.MatLike,
):
    image_h, image_w = image.shape[0], image.shape[1]

    threshold_red = 90
    threshold_green = 90
    threshold_blue = 90

    accepted_colors = dict()
    posterized_removed_colors = dict()
    unposterized_removed_colors = dict()

    for i in range(0, image_h):  ## traverse image row
        for j in range(0, image_w):  ## traverse image col
            pixel = image[i][j]
            red = int(pixel[2])
            green = int(pixel[1])
            blue = int(pixel[0])
            grey = int(grey_img[i][j])

            color = (red, green, blue)

            if color in colors:
                image[i][j] = (255, 255, 255)
                print(f"({i},{j}): {red},{green},{blue},{grey} - remove posterized")
                if color in posterized_removed_colors:
                    posterized_removed_colors[color] += 1
                else:
                    posterized_removed_colors[color] = 1
            elif (
                abs(red - grey) < threshold_red
                and abs(green - grey) < threshold_green
                and abs(blue - grey) < threshold_blue
            ):
                image[i][j] = pixel
                if color in accepted_colors:
                    accepted_colors[color] += 1
                else:
                    accepted_colors[color] = 1
                print(f"({i},{j}): {red},{green},{blue},{grey} - keep")
            else:
                image[i][j] = (255, 255, 255)
                print(f"({i},{j}): {red},{green},{blue},{grey} - remove unposterized")
                if color in unposterized_removed_colors:
                    unposterized_removed_colors[color] += 1
                else:
                    unposterized_removed_colors[color] = 1

    color_counts_descending = OrderedDict(sorted(accepted_colors.items(),
                                                 key=lambda kv: kv[1], reverse=True))
    with open("accepted-color-counts.txt", "w") as f:
        for color in color_counts_descending:
            f.write(f"{color}: {color_counts_descending[color]}\n")

    color_counts_descending = OrderedDict(sorted(posterized_removed_colors.items(),
                                                 key=lambda kv: kv[1], reverse=True))
    with open("posterized-removed-color-counts.txt", "w") as f:
        for color in color_counts_descending:
            f.write(f"{color}: {color_counts_descending[color]}\n")

    color_counts_descending = OrderedDict(sorted(unposterized_removed_colors.items(),
                                                 key=lambda kv: kv[1], reverse=True))
    with open("unposterized-removed-color-counts.txt", "w") as f:
        for color in color_counts_descending:
            f.write(f"{color}: {color_counts_descending[color]}\n")


# test_image = "/home/greg/Prj/github/restore-barks/experiments/test-image-1.jpg"
# out_file = "/tmp/test-image-1-out.jpg"
# test_image = "/home/greg/Prj/github/restore-barks/experiments/test-image-2.jpg"
# out_file = "/tmp/test-image-2-out.jpg"
test_image = "/home/greg/Prj/github/restore-barks/experiments/test-image-3.jpg"
out_file = "/tmp/test-image-3-out.jpg"
# test_image = "/home/greg/Books/Carl Barks/Silent Night (Gemstone)/Gemstone-cp-3/01-upscayled_upscayl_2x_ultramix_balanced.jpg"
# out_file ="/tmp/junk-out-image-big.jpg"

src_image = cv.imread(test_image)
# src_image = cv.copyMakeBorder(src_image, 10, 10, 10, 10, cv.BORDER_CONSTANT, None, value = (255,255,255))
height, width, num_channels = src_image.shape
print(f"width: {width}, height: {height}, channels: {num_channels}")

blurred_image = get_median_filter(src_image)
gray_image = cv.cvtColor(blurred_image, cv.COLOR_BGR2GRAY)

posterized_colors = get_posterized_colors()
for color in posterized_colors:
        print(f"{color}")

colors = get_fuzzied_fantagraphics_colors()

out_image = blurred_image
posterize_image(out_image)
cv.imwrite("/tmp/posterized-image.jpg", out_image)

color_counts = get_color_counts(out_image)
color_counts_descending = OrderedDict(sorted(color_counts.items(),
                                             key=lambda kv: kv[1], reverse=True))
with open("posterized-color-counts.txt", "w") as f:
    for color in color_counts_descending:
        f.write(f"{color}: {color_counts_descending[color]}\n")

remove_colors(colors, gray_image, out_image)

color_counts = get_color_counts(out_image)
color_counts_descending = OrderedDict(sorted(color_counts.items(),
                                             key=lambda kv: kv[1], reverse=True))
with open("remaining-color-counts.txt", "w") as f:
    for color in color_counts_descending:
        f.write(f"{color}: {color_counts_descending[color]}\n")

cv.imwrite(out_file, out_image)
