import sys

from src.potrace_to_svg import image_file_to_svg
from src.image_io import svg_file_to_png

if __name__ == "__main__":
    input_image_file = sys.argv[1]
    output_svg_file = f"{input_image_file}.svg"
    output_png_file = f"{output_svg_file}.png"

    image_file_to_svg(input_image_file, output_svg_file)

    svg_file_to_png(output_svg_file, output_png_file)
