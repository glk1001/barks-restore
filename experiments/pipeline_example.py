import concurrent.futures
import logging
import os
import time
from pathlib import Path
from typing import List

from restore_pipeline import RestorePipeline, check_for_errors
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

    if not os.path.exists(upscale_out_file):
        raise Exception(f'File not found: "{upscale_out_file}".')

    logging.info(
        f'Time taken to upscale "{os.path.basename(upscale_out_file)}":'
        f" {int(time.time() - start)}s."
    )


OUT_DIR = "/home/greg/Prj/workdir/restore-tests"
WORK_DIR = os.path.join(OUT_DIR, "working")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

setup_logging(logging.INFO)

# FANTA_DIR = "/home/greg/Books/Carl Barks/Fantagraphics/Carl Barks Vol. 2 - Donald Duck - Frozen Gold (Salem-Empire)/images"
FANTA_DIR = "/home/greg/Books/Carl Barks/Fantagraphics/Carl Barks Vol. 7 - Donald Duck - Lost in the Andes (Digital-Empire)/images"

test_image_files = [
    # Path("/home/greg/Prj/github/restore-barks/experiments/test-image-1.jpg"),
    # Path("/home/greg/Prj/github/restore-barks/experiments/test-image-2.jpg"),
    # Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3.jpg"),
    Path(os.path.join(FANTA_DIR, "179.jpg")),
    Path(os.path.join(FANTA_DIR, "180.jpg")),
    Path(os.path.join(FANTA_DIR, "181.jpg")),
    Path(os.path.join(FANTA_DIR, "182.jpg")),
    Path(os.path.join(FANTA_DIR, "183.jpg")),
    Path(os.path.join(FANTA_DIR, "184.jpg")),
    Path(os.path.join(FANTA_DIR, "185.jpg")),
    Path(os.path.join(FANTA_DIR, "186.jpg")),
    Path(os.path.join(FANTA_DIR, "187.jpg")),
    Path(os.path.join(FANTA_DIR, "188.jpg")),
    # Path(os.path.join(FANTA_DIR, "007.jpg")),
    # Path(os.path.join(FANTA_DIR, "008.jpg")),
    # Path(os.path.join(FANTA_DIR, "009.jpg")),
    # Path(os.path.join(FANTA_DIR, "010.jpg")),
    # Path(os.path.join(FANTA_DIR, "011.jpg")),
    # Path(os.path.join(FANTA_DIR, "012.jpg")),
    # Path(os.path.join(FANTA_DIR, "013.jpg")),
    # Path(os.path.join(FANTA_DIR, "014.jpg")),
    # Path(os.path.join(FANTA_DIR, "015.jpg")),
    # Path(os.path.join(FANTA_DIR, "016.jpg")),
    # Path(os.path.join(FANTA_DIR, "017.jpg")),
    # Path(os.path.join(FANTA_DIR, "018.jpg")),
    # Path(os.path.join(FANTA_DIR, "019.jpg")),
    # Path(os.path.join(FANTA_DIR, "020.jpg")),
    # Path(os.path.join(FANTA_DIR, "021.jpg")),
    # Path(os.path.join(FANTA_DIR, "022.jpg")),
    # Path(os.path.join(FANTA_DIR, "023.jpg")),
    # Path(os.path.join(FANTA_DIR, "024.jpg")),
    # Path(os.path.join(FANTA_DIR, "025.jpg")),
    # Path(os.path.join(FANTA_DIR, "026.jpg")),
    # Path(os.path.join(FANTA_DIR, "027.jpg")),
    # Path(os.path.join(FANTA_DIR, "028.jpg")),
    # Path(os.path.join(FANTA_DIR, "029.jpg")),
    # Path(os.path.join(FANTA_DIR, "030.jpg")),
]
# test_image_file = Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3-noise-reduction.jpg")
# test_image_file = Path("/home/greg/Books/Carl Barks/Silent Night (Gemstone)/Gemstone-cp-3/01-upscayled_upscayl_2x_ultramix_balanced.jpg")

SCALE = 4

start_upscale = time.time()

for image_file in test_image_files:
    if not os.path.exists(image_file):
        raise Exception(f'File not found: "{image_file}".')
    upscale_file = get_upscale_filename(OUT_DIR, image_file, SCALE)
    do_upscale(image_file, upscale_file)

logging.info(f'\nTime taken to upscale all files": {int(time.time() - start_upscale)}s.')


start_restore = time.time()

restore_processes = []
for image_file in test_image_files:
    upscale_file = get_upscale_filename(OUT_DIR, image_file, SCALE)
    restore_processes.append(RestorePipeline(WORK_DIR, OUT_DIR, image_file, upscale_file, SCALE))


part1_max_workers = 10


def run_restore_part1(restore_process: RestorePipeline):
    restore_process.do_part1()


part2_max_workers = 3


def run_restore_part2(restore_process: RestorePipeline):
    restore_process.do_part2_memory_hungry()


part3_max_workers = 10


def run_restore_part3(restore_process: RestorePipeline):
    restore_process.do_part3()


part4_max_workers = 1


def run_restore_part4(restore_process: RestorePipeline):
    restore_process.do_part4_memory_hungry()


with concurrent.futures.ProcessPoolExecutor(part1_max_workers) as executor:
    for process in restore_processes:
        executor.submit(run_restore_part1, process)

with concurrent.futures.ProcessPoolExecutor(part2_max_workers) as executor:
    for process in restore_processes:
        executor.submit(run_restore_part2, process)

with concurrent.futures.ProcessPoolExecutor(part3_max_workers) as executor:
    for process in restore_processes:
        executor.submit(run_restore_part3, process)

with concurrent.futures.ProcessPoolExecutor(part4_max_workers) as executor:
    for process in restore_processes:
        executor.submit(run_restore_part4, process)


logging.info(f'\nTime taken to restore all files": {int(time.time() - start_restore)}s.')

check_for_errors(restore_processes)
