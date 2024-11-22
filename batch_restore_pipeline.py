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
    setup_logging(logging.INFO)

    SCALE = 4

    input_image_dir_and_stem = sys.argv[1]
    upscayl_image_dir_and_stem = sys.argv[2]
    upscayl_image_range_str = sys.argv[3]
    out_dir = sys.argv[4]

    if not os.path.isdir(out_dir):
        print(f'ERROR: Can\'t find output directory: "{out_dir}".')
        sys.exit(1)

    work_dir = os.path.join("/home/greg/Prj/workdir/restore-tests")
    os.makedirs(work_dir, exist_ok=True)

    image_range = upscayl_image_range_str.split("-")
    assert 1 <= len(image_range) <= 2
    if len(image_range) == 1:
        image_range.append(image_range[0])

    start_restore = time.time()

    restore_processes = []
    for n in range(int(image_range[0]), int(image_range[1]) + 1):
        input_image_file = Path(f"{input_image_dir_and_stem}-{n:03}.jpg")
        if not os.path.exists(input_image_file):
            print(f'ERROR: Can\'t find input image: "{input_image_file}".')
            sys.exit(1)
        upscayl_image_file = Path(f"{upscayl_image_dir_and_stem}-{n:03}.png")
        if not os.path.exists(upscayl_image_file):
            print(f'ERROR: Can\'t find upscayl image: "{upscayl_image_file}".')
            sys.exit(1)

        restore_processes.append(
            RestorePipeline(
                work_dir, out_dir, input_image_file, upscayl_image_file, SCALE
            )
        )

    for process in restore_processes:
        process.do_part1()
        process.do_part2_memory_hungry()
        process.do_part3()
        process.do_part4_memory_hungry()

    logging.info(
        f'\nTime taken to restore all files": {int(time.time() - start_restore)}s.'
    )

    check_for_errors(restore_processes)
