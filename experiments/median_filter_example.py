import os

# import subprocess
import sys

import cv2 as cv

from remove_alias_artifacts import get_median_filter

# import gmic

input_file = sys.argv[1]
output_file = os.path.splitext(input_file)[0] + "-median-filter.png"

# gmic.run(f'"{input_file}" unquantize 8,0,1,11,76 output[-1] "{output_file}"')
# subprocess.run(['gmic', f'"{input_file}"', "gcd_unquantize", "8,0,1,11,76", "output[-1]", f'"{output_file}"'])

in_image = cv.imread(input_file)
out_image = get_median_filter(in_image)

cv.imwrite(output_file, out_image)
