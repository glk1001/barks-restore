import os
from typing import Set, Tuple, Dict, List
from collections import OrderedDict
from pathlib import Path

import cv2 as cv
import numpy as np

from remove_alias_artifacts import get_median_filter

NUM_POSTERIZE_LEVELS = 5
NUM_POSTERIZE_EXCEPTION_LEVELS = 2
FIRST_LEVEL = int(255 / (NUM_POSTERIZE_LEVELS - 1))


def posterize_image(image: cv.typing.MatLike):
    for i in range(NUM_POSTERIZE_LEVELS):
        image[(image >= i * 255 / NUM_POSTERIZE_LEVELS) & (image < (i + 1) * 255 / NUM_POSTERIZE_LEVELS)] = i * 255 / (NUM_POSTERIZE_LEVELS - 1)


def get_posterized_colors() -> Set[Tuple[int, int, int]]:
    all_colors = set()
    for r in range(NUM_POSTERIZE_LEVELS):
        red = int(r * 255 / (NUM_POSTERIZE_LEVELS - 1))
        for g in range(NUM_POSTERIZE_LEVELS):
            green = int(g * 255 / (NUM_POSTERIZE_LEVELS - 1))
            for b in range(NUM_POSTERIZE_LEVELS):
                blue = int(b * 255 / (NUM_POSTERIZE_LEVELS - 1))
                all_colors.add((red, green, blue))

    return all_colors


def get_posterized_color_exceptions() -> Set[Tuple[int, int, int]]:
    all_colors = set()
    for r in range(NUM_POSTERIZE_EXCEPTION_LEVELS+1):
        red = r * FIRST_LEVEL
        for g in range(NUM_POSTERIZE_EXCEPTION_LEVELS+1):
            green = g * FIRST_LEVEL
            for b in range(NUM_POSTERIZE_EXCEPTION_LEVELS+1):
                blue = b  * FIRST_LEVEL
                all_colors.add((red, green, blue))

    return all_colors


def get_colors_to_remove() -> Set[Tuple[int, int, int]]:
    posterized_colors = get_posterized_colors()
    return posterized_colors - get_posterized_color_exceptions()


COLORS_TO_REMOVE = get_colors_to_remove()


def get_color_counts(image: cv.typing.MatLike) -> Dict[Tuple[int, int, int], int]:
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
                pass
                # image[i][j] = (255, 255, 255)
                # print(f"({i},{j}): {red},{green},{blue},{grey} - remove unposterized")
                # if color in unposterized_removed_colors:
                #     unposterized_removed_colors[color] += 1
                # else:
                #     unposterized_removed_colors[color] = 1

    color_counts_descending = OrderedDict(
        sorted(accepted_colors.items(), key=lambda kv: kv[1], reverse=True)
    )
    with open(os.path.join(out_dir, out_filename + "-accepted-color-counts.txt"), "w") as f:
        for color in color_counts_descending:
            f.write(f"{color}: {color_counts_descending[color]}\n")

    color_counts_descending = OrderedDict(
        sorted(posterized_removed_colors.items(), key=lambda kv: kv[1], reverse=True)
    )
    with open(os.path.join(out_dir, out_filename + "-posterized-removed-color-counts.txt"), "w") as f:
        for color in color_counts_descending:
            f.write(f"{color}: {color_counts_descending[color]}\n")

    color_counts_descending = OrderedDict(
        sorted(unposterized_removed_colors.items(), key=lambda kv: kv[1], reverse=True)
    )
    with open(os.path.join(out_dir, out_filename + "-unposterized-removed-color-counts.txt"), "w") as f:
        for color in color_counts_descending:
            f.write(f"{color}: {color_counts_descending[color]}\n")


out_dir = "/home/greg/Prj/workdir/restore-tests"
os.makedirs(out_dir, exist_ok=True)

#test_image_file = Path("/home/greg/Prj/github/restore-barks/experiments/test-image-1.jpg")
test_image_file = Path("/home/greg/Prj/github/restore-barks/experiments/test-image-2.jpg")
#test_image_file = Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3.jpg")
#test_image_file = Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3-noise-reduction.jpg")
# test_image_file = Path("/home/greg/Books/Carl Barks/Silent Night (Gemstone)/Gemstone-cp-3/01-upscayled_upscayl_2x_ultramix_balanced.jpg")

out_filename = test_image_file.stem

out_image_file = os.path.join(out_dir, out_filename + "-color-removed.jpg")

src_image = cv.imread(str(test_image_file))
# src_image = cv.copyMakeBorder(src_image, 10, 10, 10, 10, cv.BORDER_CONSTANT, None, value = (255,255,255))
height, width, num_channels = src_image.shape
print(f"width: {width}, height: {height}, channels: {num_channels}")

blurred_image = get_median_filter(src_image)
gray_image = cv.cvtColor(blurred_image, cv.COLOR_BGR2GRAY)

# posterized_colors = get_posterized_colors()
# for color in posterized_colors:
#         print(f"{color}")


out_image = blurred_image
posterize_image(out_image)
cv.imwrite(os.path.join(out_dir, out_filename + "-posterized.jpg"), out_image)

color_counts = get_color_counts(out_image)
color_counts_descending = OrderedDict(
    sorted(color_counts.items(), key=lambda kv: kv[1], reverse=True)
)
with open(os.path.join(out_dir, out_filename + "-posterized-color-counts.txt"), "w") as f:
    for color in color_counts_descending:
        f.write(f"{color}: {color_counts_descending[color]}\n")

remove_colors(COLORS_TO_REMOVE, gray_image, out_image)

color_counts = get_color_counts(out_image)
color_counts_descending = OrderedDict(
    sorted(color_counts.items(), key=lambda kv: kv[1], reverse=True)
)
with open(os.path.join(out_dir, out_filename + "-remaining-color-counts.txt"), "w") as f:
    for color in color_counts_descending:
        f.write(f"{color}: {color_counts_descending[color]}\n")

cv.imwrite(out_image_file, out_image)
