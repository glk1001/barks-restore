import logging
import os
import time
from pathlib import Path
from typing import List

import cv2 as cv

from image_io import resize_image_file, write_cv_image_file
from inpaint import inpaint_image_file
from potrace_to_svg import image_file_to_svg, svg_file_to_png
from remove_alias_artifacts import get_median_filter
from remove_colors import remove_colors_from_image
from smooth_image import smooth_image_file
from upscale_image import upscale_image_file


class RestorePipeline:
    def __init__(
        self, work_dir: str, out_dir: str, srce_file: Path, upscale_srce_file: Path, scale: int
    ):
        self.work_dir = work_dir
        self.out_dir = out_dir
        self.srce_file = srce_file
        self.upscale_srce_file = upscale_srce_file
        self.scale = scale
        self.errors_occurred = False

        if not os.path.isdir(self.work_dir):
            raise Exception(f'Directory not found: "{self.work_dir}".')
        if not os.path.isdir(self.out_dir):
            raise Exception(f'Directory not found: "{self.out_dir}".')
        if not os.path.exists(self.upscale_srce_file):
            raise Exception(f'File not found: "{self.upscale_srce_file}".')

        self.upscale_image_stem = upscale_srce_file.stem
        self.removed_artifacts_file = os.path.join(
            work_dir, f"{self.upscale_image_stem}-median-filtered.png"
        )
        self.removed_colors_file = os.path.join(
            work_dir, f"{self.upscale_image_stem}-color-removed.png"
        )
        self.smoothed_removed_colors_file = os.path.join(
            work_dir, f"{self.upscale_image_stem}-color-removed-smoothed.png"
        )
        self.svg_file = os.path.join(out_dir, f"{self.upscale_image_stem}.svg")
        self.png_of_svg_file = self.svg_file + ".png"
        self.inpainted_file = os.path.join(work_dir, f"{self.upscale_image_stem}-inpainted.png")
        self.restored_file = os.path.join(
            out_dir, f"{self.upscale_image_stem}-restored-orig-size.png"
        )

    def do_part1(self):
        self.do_remove_jpg_artifacts()
        self.do_remove_colors()

    def do_part2_memory_hungry(self):
        self.do_smooth_removed_colors()

    def do_part3(self):
        self.do_generate_svg()

    def do_part4_memory_hungry(self):
        self.do_inpaint()
        self.do_resize_restored_file()

    def do_remove_jpg_artifacts(self):
        try:
            start = time.time()
            logging.info(
                f'\nGenerating jpeg artifacts removed file "{self.removed_artifacts_file}"...'
            )

            upscale_image = cv.imread(str(self.upscale_srce_file))
            out_image = get_median_filter(upscale_image)
            write_cv_image_file(self.removed_artifacts_file, out_image)

            logging.info(
                f"Time taken to remove jpeg artifacts for"
                f' "{os.path.basename(self.removed_artifacts_file)}":'
                f" {int(time.time() - start)}s."
            )
        except Exception as e:
            self.errors_occurred = True
            logging.exception(e)

    def do_remove_colors(self):
        try:
            start = time.time()
            logging.info(f'\nGenerating color removed file "{self.removed_colors_file}"...')

            remove_colors_from_image(
                self.work_dir, self.removed_artifacts_file, self.removed_colors_file
            )

            logging.info(
                f'Time taken to remove colors for "{os.path.basename(self.removed_colors_file)}":'
                f" {int(time.time() - start)}s."
            )
        except Exception as e:
            self.errors_occurred = True
            logging.exception(e)

    def do_smooth_removed_colors(self):
        try:
            start = time.time()
            logging.info(f'\nGenerating smoothed file "{self.smoothed_removed_colors_file}"...')

            smooth_image_file(self.removed_colors_file, self.smoothed_removed_colors_file)

            logging.info(
                f'Time taken to smooth "{os.path.basename(self.smoothed_removed_colors_file)}":'
                f" {int(time.time() - start)}s."
            )
        except Exception as e:
            self.errors_occurred = True
            logging.exception(e)

    def do_generate_svg(self):
        try:
            start = time.time()
            logging.info(f'\nGenerating svg file "{self.svg_file}"...')

            image_file_to_svg(self.smoothed_removed_colors_file, self.svg_file)

            logging.info(
                f'Time taken to generate svg "{os.path.basename(self.svg_file)}":'
                f" {int(time.time() - start)}s."
            )

            logging.info(f'\nSaving svg file to png file "{self.png_of_svg_file}"...')
            svg_file_to_png(self.svg_file, self.png_of_svg_file)
        except Exception as e:
            self.errors_occurred = True
            logging.exception(e)

    def do_inpaint(self):
        try:
            start = time.time()
            logging.info(f'\nInpainting upscaled file to "{self.inpainted_file}"...')

            inpaint_image_file(
                self.work_dir,
                str(self.upscale_srce_file),
                self.removed_colors_file,
                self.png_of_svg_file,
                self.inpainted_file,
            )

            logging.info(
                f'Time taken to inpaint "{os.path.basename(self.inpainted_file)}":'
                f" {int(time.time() - start)}s."
            )
        except Exception as e:
            self.errors_occurred = True
            logging.exception(e)

    def do_resize_restored_file(self):
        try:
            logging.info(f'\nResizing restored file to "{self.restored_file}"...')

            # TODO: Save other params used in process.
            restored_file_metadata = {
                "Source file": str(self.srce_file),
                "Upscayl file": str(self.upscale_srce_file),
                "Upscayl scale": str(self.scale),
            }

            resize_image_file(
                self.inpainted_file, self.scale, self.restored_file, restored_file_metadata
            )
        except Exception as e:
            self.errors_occurred = True
            logging.exception(e)


def get_upscale_filename(out_dir: str, img_file: Path, scale: int) -> Path:
    upscale_image_stem = f"{img_file.stem}-upscayl-x{scale}"
    return Path(os.path.join(out_dir, f"{upscale_image_stem}.png"))


def do_upscale(srce_file: Path, upscale_out_file: Path):
    start = time.time()
    logging.info(f'\nProcessing "{srce_file}"...')

    logging.info(f'\nUpscaling to "{upscale_out_file}"...')
    upscale_image_file(str(srce_file), str(upscale_out_file), SCALE)

    if not os.path.exists(upscale_out_file):
        raise Exception(f'File not found: "{upscale_out_file}".')

    logging.info(
        f'Time taken to upscale "{os.path.basename(upscale_out_file)}":'
        f" {int(time.time() - start)}s."
    )


def check_file_exists(proc: RestorePipeline, file: str):
    if not os.path.exists(file):
        logging.error(f'Could not find output artifact "{file}".')
        proc.errors_occurred = True


def check_for_errors(restore_procs: List[RestorePipeline]):
    for proc in restore_procs:
        check_file_exists(proc, proc.removed_artifacts_file)
        check_file_exists(proc, proc.removed_colors_file)
        check_file_exists(proc, proc.smoothed_removed_colors_file)
        check_file_exists(proc, proc.svg_file)
        check_file_exists(proc, proc.png_of_svg_file)
        check_file_exists(proc, proc.inpainted_file)
        check_file_exists(proc, proc.restored_file)

        if proc.errors_occurred:
            logging.error(f'Errors occurred while processing "{proc.upscale_srce_file}".')
