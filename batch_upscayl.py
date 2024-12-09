import logging
import os
import sys
import time
from typing import List

from barks_fantagraphics.comics_cmd_args import CmdArgs, CmdArgNames
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_relpath
from src.upscale_image import upscale_image_file


def setup_logging(log_level) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=log_level,
    )


SCALE = 4


def upscayl(title_list: List[str]) -> None:
    start = time.time()

    num_upscayled_files = 0
    for title in title_list:
        logging.info(f'Upscayling story "{title}"...')

        comic = comics_database.get_comic_book(title)

        srce_files = comic.get_srce_with_fixes_story_files(RESTORABLE_PAGE_TYPES)
        upscayl_files = comic.get_srce_upscayled_story_files(RESTORABLE_PAGE_TYPES)

        for srce_file, upscayl_file in zip(srce_files, upscayl_files):
            if not os.path.isfile(srce_file[0]):
                raise Exception(f'Could not find srce file: "{srce_file[0]}".')
            if os.path.isfile(upscayl_file):
                logging.warning(
                    f'Dest upscayl file exists - skipping: "{get_relpath(upscayl_file)}".'
                )
                continue

            # print(f'Upscayling srce file "{srce_file[0]}" to dest upscayl "{upscayl_file}".')
            upscale_image_file(srce_file[0], upscayl_file, SCALE)

            num_upscayled_files += 1

    logging.info(
        f"\nTime taken to upscayl all {num_upscayled_files} files: {int(time.time() - start)}s."
    )


setup_logging(logging.INFO)

cmd_args = CmdArgs("Ocr titles", CmdArgNames.TITLE | CmdArgNames.VOLUME)
args_ok, error_msg = cmd_args.args_are_valid()
if not args_ok:
    logging.error(error_msg)
    sys.exit(1)

comics_database = cmd_args.get_comics_database()

titles = cmd_args.get_titles()

upscayl(titles)
