import logging
import os
import sys
import time
from typing import List

from intspan import intspan

from barks_fantagraphics.comics_cmd_args import get_std_args
from barks_fantagraphics.comics_database import ComicsDatabase, PageType
from barks_fantagraphics.comics_utils import get_relpath
from src.upscale_image import upscale_image_file


def setup_logging(log_level) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=log_level,
    )


RESTORABLE_PAGE_TYPES = [
    PageType.BODY,
    PageType.FRONT_MATTER,
    PageType.BACK_MATTER,
]

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

cmd_args = get_std_args()
if not cmd_args:
    sys.exit(1)

comics_database = ComicsDatabase(cmd_args.comics_database_dir)

if cmd_args.title:
    titles = [cmd_args.title]
else:
    assert cmd_args.volume is not None
    vol_list = list(intspan(cmd_args.volume))
    titles = comics_database.get_all_story_titles_in_fantagraphics_volume(vol_list)

upscayl(titles)
