import logging
import os
import sys
import time
from pathlib import Path

from src.restore_pipeline import RestorePipeline, check_for_errors


def setup_logging(log_level) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=log_level,
    )


if __name__ == "__main__":
    setup_logging(logging.INFO)

    SCALE = 4
    image_file = Path(sys.argv[1])
    upscale_file = Path(sys.argv[2])
    out_file = Path(sys.argv[3])

    out_dir = os.path.dirname(out_file)
    if not os.path.isdir(out_dir):
        print(f'ERROR: Can\'t find output directory: "{out_dir}".')
        sys.exit(1)

    work_dir = os.path.join("/tmp/", "working")
    os.makedirs(work_dir, exist_ok=True)

    input_image_dir = os.path.dirname(image_file)
    input_image_stem = Path(image_file).stem

    start_restore = time.time()

    restore_process = RestorePipeline(work_dir, image_file, upscale_file, SCALE, out_file)
    restore_process.do_part1()
    restore_process.do_part2_memory_hungry()
    restore_process.do_part3()
    restore_process.do_part4_memory_hungry()

    logging.info(f'\nTime taken to restore all files": {int(time.time() - start_restore)}s.')

    check_for_errors([restore_process])
