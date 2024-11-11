import os
import time
from pathlib import Path

import cv2 as cv
import gmic

from inpaint import inpaint_image_file
from potrace_to_svg import image_file_to_svg, svg_file_to_png
from remove_colors import remove_colors_from_image
from smooth_image import smooth_image_file
from upscale_image import upscale_image_file

out_dir = "/home/greg/Prj/workdir/restore-tests"
os.makedirs(out_dir, exist_ok=True)

test_image_files = [
    #Path("/home/greg/Prj/github/restore-barks/experiments/test-image-1.jpg"),
    Path("/home/greg/Prj/github/restore-barks/experiments/test-image-2.jpg"),
    Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3.jpg"),
]
# test_image_file = Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3-noise-reduction.jpg")
# test_image_file = Path("/home/greg/Books/Carl Barks/Silent Night (Gemstone)/Gemstone-cp-3/01-upscayled_upscayl_2x_ultramix_balanced.jpg")

scale = 4

for image_file in test_image_files:
    start = time.time()
    print(f'\nProcessing "{image_file}"...')

    upscale_image_stem = f"{image_file.stem}-upscayl-x{scale}"

    upscale_file = os.path.join(out_dir, f"{upscale_image_stem}.jpg")
    print(f'\nUpscaling to "{upscale_file}"...')
    upscale_start = time.time()
    upscale_image_file(str(image_file), upscale_file, scale)
    print(f"Time taken to upscale: {int(time.time() - upscale_start)}s.")

    upscale_image = cv.imread(str(upscale_file))
    print(f'\nRemoving colors from upscaled file "{upscale_file}"...')
    # height, width, num_channels = upscale_image.shape
    # print(f"width: {width}, height: {height}, channels: {num_channels}")
    remove_colors_start = time.time()
    removed_colors_file = remove_colors_from_image(
        out_dir, upscale_image_stem, upscale_image
    )
    print(f"Time taken to remove colors: {int(time.time() - remove_colors_start)}s.")

    smoothed_file = os.path.join(
        out_dir, f"{os.path.splitext(removed_colors_file)[0]+'-smoothed.png'}"
    )
    print(f'\nBefore svg, generating smoothed file "{smoothed_file}"...')
    smooth_start = time.time()
    smooth_image_file(removed_colors_file, smoothed_file)
    print(f"Time taken to smooth: {int(time.time() - smooth_start)}s.")

    svg_file = os.path.join(out_dir, f"{upscale_image_stem}.svg")
    print(f'\nGenerating svg file "{svg_file}"...')
    svg_start = time.time()
    image_file_to_svg(smoothed_file, svg_file)
    print(f"Time taken to generate svg: {int(time.time() - svg_start)}s.")

    png_of_svg_file = os.path.join(out_dir, f"{svg_file}.png")
    print(f'\nSaving svg file to png file "{png_of_svg_file}"...')
    svg_file_to_png(svg_file, png_of_svg_file)

    # Check if gmic flat colors is available
    # Convert back to original size - save a color image and a b/w image
    inpainted_file = os.path.join(out_dir, f"{upscale_image_stem}-inpainted.png")
    print(f'\nInpainting upscaled file to "{inpainted_file}"...')
    inpaint_start = time.time()
    inpaint_image_file(
        upscale_file, removed_colors_file, png_of_svg_file, inpainted_file
    )
    print(f"Time taken to inpaint: {int(time.time() - inpaint_start)}s.")

    restored_file = os.path.join(
        out_dir, f"{upscale_image_stem}-restored-orig-size.png"
    )
    print(f'\nRestoring original size file to "{restored_file}"...')
    scale_percent = 25 if scale == 4 else 50
    gmic.run(
        f'"{inpainted_file}" +resize[-1] {scale_percent}%,{scale_percent}%,1,3,2'
        f' output[-1] "{restored_file}"'
    )

    print(
        f'\nTime taken to process "{os.path.basename(image_file)}": {int(time.time() - start)}s.'
    )
