import os
import sys

from smooth_image import smooth_image_file

input_file = sys.argv[1]
output_file = os.path.splitext(input_file)[0] + "-smoothed.png"

smooth_image_file(input_file, output_file)
