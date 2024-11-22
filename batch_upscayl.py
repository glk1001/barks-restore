import os
import sys
from pathlib import Path

from experiments.upscale_image import upscale_image_file

if __name__ == "__main__":
    scale = 4

    input_image_dir_and_stem = sys.argv[1]
    input_image_range_str = sys.argv[2]
    out_dir = sys.argv[3]

    if not os.path.isdir(out_dir):
        print(f'ERROR: Can\'t find output directory: "{out_dir}".')
        sys.exit(1)

    input_image_range = input_image_range_str.split("-")
    assert 1 <= len(input_image_range) <= 2
    if len(input_image_range) == 1:
        input_image_range.append(input_image_range[0])

    for n in range(int(input_image_range[0]), int(input_image_range[1]) + 1):
        input_image_file = f"{input_image_dir_and_stem}-{n:03}.jpg"
        if not os.path.exists(input_image_file):
            print(f'ERROR: Can\'t find input image: "{input_image_file}".')
            sys.exit(1)

        input_image_stem = Path(input_image_dir_and_stem).stem
        output_upscayl_file = os.path.join(
            out_dir, f"{input_image_stem}-upscayl-x{scale}-{n:03}.png"
        )

        if os.path.exists(output_upscayl_file):
            print(f'ERROR: Can\'t overwrite target file: "{output_upscayl_file}".')
            sys.exit(1)

        upscale_image_file(input_image_file, output_upscayl_file, scale)
