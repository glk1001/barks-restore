import concurrent.futures
import os.path
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, List

import cv2 as cv
import numpy as np

from potrace_to_svg import image_file_to_svg

COMIC_WHITE_R = 249
COMIC_WHITE_G = 242
COMIC_WHITE_B = 226


def change_color(path_node, color: Tuple[int, int, int]):
    color = f"rgba({color[2]},{color[1]},{color[0]},1.0)"
    for elem in path_node:
        elem.attrib["fill"] = color


def get_svg_file_list(dir_name: str, file_stem: str, num_files: int) -> List[str]:
    file_list = []
    for index in range(0, num_files):
        svg_file = os.path.join(dir_name, f"{file_stem}-{index:02}.svg")
        file_list.append(svg_file)

    return file_list


def get_kmeans_clusters(
    srce_image: cv.typing.MatLike, K: int
) -> Tuple[cv.typing.MatLike, : cv.typing.MatLike]:
    image_data = srce_image.reshape((-1, 3))
    # print(len(np.unique(image_data, axis=0)), 'unique RGB values out of', image_data.shape[0], 'pixels')
    image_data = np.float32(image_data)

    # define criteria, number of clusters(K) and apply kmeans()
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, color_labels, rgb_centers = cv.kmeans(
        image_data, K, None, criteria, 10, cv.KMEANS_RANDOM_CENTERS
    )
    print(
        f"ret = {ret}, label.shape = {color_labels.shape}, center.shape = {rgb_centers.shape}"
    )

    rgb_centers = np.uint8(rgb_centers)
    print(rgb_centers)

    return color_labels, rgb_centers


def generate_svg_files(
    image_shape: Tuple[int, ...],
    color_labels: cv.typing.MatLike,
    svg_file_list: List[str],
):
    bw_centers = np.array([[0, 0, 0], [255, 255, 255]])
    bw_centers = np.uint8(bw_centers)
    print(bw_centers)

    # kernel = np.ones((3, 3), np.uint8)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for index in range(0, len(svg_file_list)):
            executor.submit(
                generate_svg,
                image_shape,
                color_labels,
                index,
                bw_centers,
                svg_file_list[index],
            )


def generate_svg(
    image_shape: Tuple[int, ...],
    color_labels: cv.typing.MatLike,
    index: int,
    bw_centers: cv.typing.MatLike,
    svg_file: str,
):
    single_color = np.where(color_labels == index, 0, 1)
    single_color_image = bw_centers[single_color.flatten()]
    # print(len(np.unique(res, axis=0)), 'unique RGB values out of', Z.shape[0], 'pixels')

    single_color_image = single_color_image.reshape(image_shape)
    # single_color_image = cv.erode(single_color_image, kernel, iterations=1)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    single_color_image = cv.morphologyEx(single_color_image, cv.MORPH_OPEN, kernel)
    png_file = str(Path(svg_file).with_suffix(".png"))
    cv.imwrite(png_file, single_color_image)

    print(f'Generating svg file "{svg_file}"...')
    image_file_to_svg(png_file, svg_file)


def get_layered_svg_file(
    rgb_centers: cv.typing.MatLike,
    svg_file_list: List[str],
    black_ink_svg: str,
    out_svg: str,
):
    base_image = None
    for index in range(0, len(svg_file_list)):
        image_part = ET.parse(svg_file_list[index]).getroot()
        change_color(image_part, rgb_centers[index])
        if index == 0:
            base_image = image_part
        else:
            for elem in image_part:
                assert base_image is not None
                base_image.append(elem)

    image_part = ET.parse(black_ink_svg).getroot()
    for elem in image_part:
        base_image.append(elem)

    ET.ElementTree(base_image).write(out_svg)


def get_black_ink_image(srce_image: cv.typing.MatLike, black_mask: cv.typing.MatLike):
    # cv.imwrite("/tmp/mask.png", mask)
    _, _, _, black_alpha_mask = cv.split(black_mask)
    black_alpha_mask = np.uint8(black_alpha_mask)
    cv.imwrite("/tmp/black_alpha_mask.png", black_alpha_mask)

    b, g, r = cv.split(srce_image)
    b = np.where(black_alpha_mask == 255, COMIC_WHITE_B, b)
    g = np.where(black_alpha_mask == 255, COMIC_WHITE_G, g)
    r = np.where(black_alpha_mask == 255, COMIC_WHITE_R, r)

    return cv.merge([b, g, r])


if __name__ == "__main__":
    srce_image_file = Path(sys.argv[1])
    black_ink_mask_file = Path(sys.argv[2])
    svg_black_ink_file = Path(sys.argv[3])
    svg_out_file = os.path.join("/tmp", f"{srce_image_file.stem}-quantized.svg")

    image = cv.imread(str(srce_image_file))
    assert image.shape[2] == 3

    black_ink_mask = cv.imread(str(black_ink_mask_file), -1)
    assert black_ink_mask.shape[2] == 4

    black_ink_image = get_black_ink_image(image, black_ink_mask)

    num_colors = 15
    labels, centers = get_kmeans_clusters(black_ink_image, num_colors)

    out_dir = os.path.dirname(svg_out_file)
    output_file_stem = Path(svg_out_file).stem
    svg_files = get_svg_file_list(out_dir, output_file_stem, num_colors)

    generate_svg_files(image.shape, labels, svg_files)

    # center = np.array(
    #     [
    #         [72, 155, 4],
    #         [58, 102, 184],
    #         [68, 102, 172],
    #         [134, 161, 180],
    #         [224, 246, 253],
    #         [82, 144, 23],
    #         [57, 142, 200],
    #         [28, 159, 240],
    #         [0, 0, 0],
    #         [182, 177, 193],
    #         [81, 205, 192],
    #         [95, 173, 204],
    #         [97, 207, 197],
    #         [223, 215, 181],
    #         [119, 184, 218],
    #         [120, 177, 242],
    #     ]
    # )
    get_layered_svg_file(centers, svg_files, str(svg_black_ink_file), svg_out_file)
