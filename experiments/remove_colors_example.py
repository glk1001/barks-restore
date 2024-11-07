import os
from pathlib import Path

import cv2 as cv

from remove_colors import remove_colors_from_image

# posterized_colors = get_posterized_colors()
# for color in posterized_colors:
#         print(f"{color}")


out_dir = "/home/greg/Prj/workdir/restore-tests"
os.makedirs(out_dir, exist_ok=True)

test_image_files = [
    # Path(
    #     "/home/greg/Prj/github/restore-barks/experiments/test-image-2-upscayl-2x-ultramix-balanced.jpg"
    # ),
    Path(
        "/home/greg/Prj/github/restore-barks/experiments/test-image-2-upscayl-4x-ultramix-balanced.jpg"
    ),
    # Path("/home/greg/Prj/github/restore-barks/experiments/test-image-1.jpg"),
    # Path("/home/greg/Prj/github/restore-barks/experiments/test-image-2.jpg"),
    # Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3.jpg"),
]
# test_image_file = Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3-noise-reduction.jpg")
# test_image_file = Path("/home/greg/Books/Carl Barks/Silent Night (Gemstone)/Gemstone-cp-3/01-upscayled_upscayl_2x_ultramix_balanced.jpg")

for image_file in test_image_files:
    print(f'Processing "{image_file}"...')

    src_image = cv.imread(str(image_file))

    height, width, num_channels = src_image.shape
    print(f"width: {width}, height: {height}, channels: {num_channels}")

    remove_colors_from_image(out_dir, image_file.stem, src_image)
