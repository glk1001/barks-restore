import os.path
from pathlib import Path

import cv2 as cv
import gmic
import numpy as np

from image_io import write_cv_image_file


def inpaint_image_file(
    work_dir: str,
    in_file: str,
    black_ink_mask_file: str,
    black_ink_file: str,
    out_file: str,
):
    input_image = cv.imread(in_file)
    assert input_image.shape[2] == 3
    black_ink_mask = cv.imread(black_ink_mask_file, cv.COLOR_BGR2GRAY)
    assert black_ink_mask.shape[2] == 3
    black_ink = cv.imread(black_ink_file, -1)
    assert black_ink.shape[2] == 4

    in_file_stem = Path(in_file).stem

    _, remove_mask = cv.threshold(black_ink_mask, 100, 255, cv.THRESH_BINARY_INV)
    assert remove_mask.shape[2] == 3

    _, _, r_remove_mask = cv.split(remove_mask)

    remove_mask = np.uint8(r_remove_mask)
    # logging.info(remove_mask.shape)
    remove_mask_file = os.path.join(work_dir, f"{in_file_stem}-remove-mask.png")
    write_cv_image_file(remove_mask_file, remove_mask)

    # gmic blend/remove - pipeline??
    b, g, r = cv.split(input_image)
    b = np.where(remove_mask == 255, 0, b)
    g = np.where(remove_mask == 255, 0, g)
    r = np.where(remove_mask == 255, 255, r)
    out_image = cv.merge([b, g, r])
    in_file_no_black_ink = os.path.join(work_dir, f"{in_file_stem}-input_no_black_ink.png")
    write_cv_image_file(in_file_no_black_ink, out_image)

    inpaint_removed_file = os.path.join(work_dir, f"{in_file_stem}-inpaint_removed.png")
    gmic.run(
        f'"{in_file_no_black_ink}" -fx_inpaint_matchpatch "1","5","26","5","1","255","0","0","255","1","0" output "{inpaint_removed_file}"'
    )
    #    gmic.run(f'"{in_file_no_black_ink}" -fx_inpaint_pde "80","2","15","255","0","0","255","1" output "{inpaint_removed_file}"')
    # TOO LONG    gmic.run(f'"{in_file_no_black_ink}" -fx_inpaint_patch "7","16","0.1","1.2","0","0.05","10","1","255","0","0","255","0","0" output "{inpaint_removed_file}"')

    gmic.run(
        f'"{inpaint_removed_file}" "{black_ink_file}" +channels[-1] 100% +image[0] [1],0%,0%,0,0,1,[2],255 output[-1] "{out_file}"'
    )
