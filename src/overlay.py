import os.path

import gmic


def overlay_inpainted_file_with_black_ink(
    inpaint_file: str,
    black_ink_file: str,
    out_file: str,
):
    if not os.path.exists(inpaint_file):
        raise Exception(f'File not found: "{inpaint_file}".')
    if not os.path.exists(black_ink_file):
        raise Exception(f'File not found: "{black_ink_file}".')

    overlay_cmd = (
        f'"{inpaint_file}" "{black_ink_file}"'
        f" +channels[-1] 100% +image[0] [1],0%,0%,0,0,1,[2],255"
        f' output[-1] "{out_file}"'
    )
    gmic.run(overlay_cmd)
