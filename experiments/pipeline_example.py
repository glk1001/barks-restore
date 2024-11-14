import concurrent.futures
import logging
import os
import time
from pathlib import Path
from typing import Dict

import cv2 as cv

from image_io import resize_image_file, write_cv_image_file
from inpaint import inpaint_image_file
from potrace_to_svg import image_file_to_svg, svg_file_to_png
from remove_alias_artifacts import get_median_filter
from remove_colors import remove_colors_from_image
from smooth_image import smooth_image_file
from upscale_image import upscale_image_file


def setup_logging(log_level) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=log_level,
    )


def get_upscale_filename(out_dir: str, img_file: Path, scale: int) -> Path:
    upscale_image_stem = f"{img_file.stem}-upscayl-x{scale}"
    return Path(os.path.join(out_dir, f"{upscale_image_stem}.png"))


def do_upscale(srce_file: Path, upscale_out_file: Path):
    start = time.time()
    logging.info(f'\nProcessing "{srce_file}"...')

    logging.info(f'\nUpscaling to "{upscale_out_file}"...')
    upscale_image_file(str(srce_file), str(upscale_out_file), SCALE)

    logging.info(
        f'Time taken to upscale "{os.path.basename(upscale_out_file)}":'
        f" {int(time.time() - start)}s."
    )


def do_restore_process(
    work_dir: str, out_dir: str, srce_file: Path, upscale_in_file: Path, scale: int
):
    start = time.time()
    logging.info(f'\nProcessing "{upscale_in_file}"...')

    upscale_image_stem = upscale_in_file.stem
    upscale_image = cv.imread(str(upscale_in_file))

    removed_jpg_artifacts_file = os.path.join(work_dir, f"{upscale_image_stem}-median-filtered.png")
    do_remove_jpg_artifacts(upscale_image, removed_jpg_artifacts_file)

    removed_colors_file = os.path.join(work_dir, f"{upscale_image_stem}-color-removed.png")
    do_remove_colors(work_dir, removed_jpg_artifacts_file, removed_colors_file)

    smoothed_file = os.path.join(work_dir, f"{upscale_image_stem}-color-removed-smoothed.png")
    do_smooth_removed_colors(removed_colors_file, smoothed_file)

    svg_file = os.path.join(out_dir, f"{upscale_image_stem}.svg")
    png_of_svg_file = svg_file + ".png"
    do_generate_svg(smoothed_file, svg_file, png_of_svg_file)

    # Check if gmic flat colors is available
    # Convert back to original size - save a color image and a b/w image
    inpainted_file = os.path.join(work_dir, f"{upscale_image_stem}-inpainted.png")
    do_inpaint(work_dir, str(upscale_in_file), removed_colors_file, png_of_svg_file, inpainted_file)

    restored_file = os.path.join(out_dir, f"{upscale_image_stem}-restored-orig-size.jpg")
    # TODO: Save other params used in process.
    restored_file_metadata = {
        "Source file": str(srce_file),
        "Upscayl file": str(upscale_in_file),
        "Upscayl scale": str(scale),
    }
    do_resize_restored_file(inpainted_file, scale, restored_file, restored_file_metadata)

    logging.info(
        f'\nTime taken to process "{os.path.basename(srce_file)}": {int(time.time() - start)}s.'
    )


def do_remove_jpg_artifacts(upscale_image: cv.typing.MatLike, removed_artifacts_file: str):
    start = time.time()
    logging.info(f'\nGenerating jpeg artifacts removed file "{removed_artifacts_file}"...')

    out_image = get_median_filter(upscale_image)
    write_cv_image_file(removed_artifacts_file, out_image)

    logging.info(
        f'Time taken to remove jpeg artifacts for "{os.path.basename(removed_artifacts_file)}":'
        f" {int(time.time() - start)}s."
    )


def do_remove_colors(work_dir: str, removed_artifacts_file: str, removed_colors_file: str):
    start = time.time()
    logging.info(f'\nGenerating color removed file "{removed_colors_file}"...')

    remove_colors_from_image(work_dir, removed_artifacts_file, removed_colors_file)

    logging.info(
        f'Time taken to remove colors for "{os.path.basename(removed_colors_file)}":'
        f" {int(time.time() - start)}s."
    )


def do_smooth_removed_colors(removed_colors_file: str, smoothed_file: str):
    start = time.time()
    logging.info(f'\nGenerating smoothed file "{smoothed_file}"...')

    smooth_image_file(removed_colors_file, smoothed_file)

    logging.info(
        f'Time taken to smooth "{os.path.basename(smoothed_file)}":'
        f" {int(time.time() - start)}s."
    )


def do_generate_svg(smoothed_removed_colors_file: str, svg_file: str, png_of_svg_file: str):
    start = time.time()
    logging.info(f'\nGenerating svg file "{svg_file}"...')

    image_file_to_svg(smoothed_removed_colors_file, svg_file)

    logging.info(
        f'Time taken to generate svg "{os.path.basename(svg_file)}":'
        f" {int(time.time() - start)}s."
    )

    logging.info(f'\nSaving svg file to png file "{png_of_svg_file}"...')
    svg_file_to_png(svg_file, png_of_svg_file)


def do_inpaint(
    work_dir: str,
    upscale_srce_file: str,
    removed_colors_file: str,
    png_of_svg_file: str,
    inpainted_file: str,
):
    start = time.time()
    logging.info(f'\nInpainting upscaled file to "{inpainted_file}"...')

    inpaint_image_file(
        work_dir,
        upscale_srce_file,
        removed_colors_file,
        png_of_svg_file,
        inpainted_file,
    )

    logging.info(
        f'Time taken to inpaint "{os.path.basename(inpainted_file)}":'
        f" {int(time.time() - start)}s."
    )


def do_resize_restored_file(
    inpainted_file: str, scale: int, restored_file: str, metadata: Dict[str, str]
):
    logging.info(f'\nResizing restoring file to "{restored_file}"...')

    resize_image_file(inpainted_file, scale, restored_file, metadata)


OUT_DIR = "/home/greg/Prj/workdir/restore-tests"
WORK_DIR = os.path.join(OUT_DIR, "working")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

setup_logging(logging.INFO)

test_image_files = [
    Path("/home/greg/Prj/github/restore-barks/experiments/test-image-1.jpg"),
    #    Path("/home/greg/Prj/github/restore-barks/experiments/test-image-2.jpg"),
    #    Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3.jpg"),
    #    Path("/home/greg/Books/Carl Barks/Fantagraphics/Carl Barks Vol. 2 - Donald Duck - Frozen Gold (Salem-Empire)/images/007.jpg")
]
# test_image_file = Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3-noise-reduction.jpg")
# test_image_file = Path("/home/greg/Books/Carl Barks/Silent Night (Gemstone)/Gemstone-cp-3/01-upscayled_upscayl_2x_ultramix_balanced.jpg")

SCALE = 4

start_upscale = time.time()

# for image_file in test_image_files:
#     upscale_file = get_upscale_filename(OUT_DIR, image_file, SCALE)
#     do_upscale(image_file, upscale_file)

logging.info(f'\nTime taken to upscale all files": {int(time.time() - start_upscale)}s.')

start_restore = time.time()

with concurrent.futures.ProcessPoolExecutor() as executor:
    for image_file in test_image_files:
        upscale_file = get_upscale_filename(OUT_DIR, image_file, SCALE)
        executor.submit(do_restore_process, WORK_DIR, OUT_DIR, image_file, upscale_file, SCALE)

logging.info(f'\nTime taken to restore all files": {int(time.time() - start_restore)}s.')
