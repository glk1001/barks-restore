import os
from pathlib import Path

import cv2 as cv

from potrace_to_svg import image_file_to_svg, svg_file_to_png
from remove_colors import remove_colors_from_image
from upscale_image import upscale_image_file

out_dir = "/home/greg/Prj/workdir/restore-tests"
os.makedirs(out_dir, exist_ok=True)

test_image_files = [
    Path("/home/greg/Prj/github/restore-barks/experiments/test-image-1.jpg"),
    # Path("/home/greg/Prj/github/restore-barks/experiments/test-image-2.jpg"),
    # Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3.jpg"),
]
# test_image_file = Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3-noise-reduction.jpg")
# test_image_file = Path("/home/greg/Books/Carl Barks/Silent Night (Gemstone)/Gemstone-cp-3/01-upscayled_upscayl_2x_ultramix_balanced.jpg")

scale = 2

for image_file in test_image_files:
    print(f'Processing "{image_file}"...')

    upscale_image_stem = f"{image_file.stem}-upscayl-x{scale}"

    upscale_file = os.path.join(out_dir, f"{upscale_image_stem}.jpg")
    print(f'\nUpscaling to "{upscale_file}"...')
    upscale_image_file(str(image_file), upscale_file, scale)

    upscale_image = cv.imread(str(upscale_file))
    print(f'\nRemoving colors from upscaled file "{upscale_file}"...')
    # height, width, num_channels = upscale_image.shape
    # print(f"width: {width}, height: {height}, channels: {num_channels}")

    removed_colors_file = remove_colors_from_image(
        out_dir, upscale_image_stem, upscale_image
    )

    svg_file = os.path.join(out_dir, f"{upscale_image_stem}.svg")
    print(f'\nGenerating svg file "{svg_file}"...')
    image_file_to_svg(removed_colors_file, svg_file)

    png_file = os.path.join(out_dir, f"{svg_file}.png")
    svg_file_to_png(svg_file, png_file)
