import sys
from pathlib import Path

from src.upscale_image import upscale_image_file

if __name__ == "__main__":
    scale = 2

    input_image_file = Path(sys.argv[1])
    output_image_file = f"{input_image_file.stem}-upscayl-x{scale}.jpg"

    upscale_image_file(str(input_image_file), output_image_file)
