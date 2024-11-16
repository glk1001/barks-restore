import logging
import os
import sys
import time
from pathlib import Path

from experiments.restore_pipeline import RestorePipeline, check_for_errors


def setup_logging(log_level) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=log_level,
    )


if __name__ == "__main__":
    SCALE = 4
    image_file = Path(sys.argv[1])
    upscale_file = Path(sys.argv[2])

    out_dir = os.path.dirname(upscale_file)
    work_dir = os.path.join("/tmp/", "working")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)

    setup_logging(logging.INFO)

    input_image_dir = os.path.dirname(image_file)
    input_image_stem = Path(image_file).stem

    start_restore = time.time()

    restore_process = RestorePipeline(work_dir, out_dir, image_file, upscale_file, SCALE)
    restore_process.do_part1()
    restore_process.do_part2_memory_hungry()
    restore_process.do_part3()
    restore_process.do_part4_memory_hungry()

    logging.info(f'\nTime taken to restore all files": {int(time.time() - start_restore)}s.')

    check_for_errors([restore_process])
