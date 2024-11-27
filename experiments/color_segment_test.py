import concurrent.futures
import json
import logging
import os.path
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, Dict

import cv2 as cv
import gmic
import numpy as np
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import sRGBColor, LabColor

from potrace_to_svg import image_file_to_svg


# Patch for 'colormath' package not being up to date with numpy.
def patch_asscalar(a):
    return a.item()


setattr(np, "asscalar", patch_asscalar)


BgrColor = Tuple[int, int, int]
LabelDict = Dict[int, Tuple[int, BgrColor, LabColor]]

COMIC_WHITE_R = 249
COMIC_WHITE_G = 242
COMIC_WHITE_B = 226


def setup_logging(log_level: int) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=log_level,
    )


def change_color(path_node: ET.Element, bgr_color: BgrColor) -> None:
    rgb_color = f"rgba({bgr_color[2]},{bgr_color[1]},{bgr_color[0]},1.0)"
    for elem in path_node:
        elem.attrib["fill"] = rgb_color


def get_svg_files(
    dir_name: str, file_stem: str, label_colors_and_counts: LabelDict
) -> Dict[int, Path]:
    file_list = {}
    for index in label_colors_and_counts:
        svg_file = Path(os.path.join(dir_name, f"{file_stem}-{index:02}.svg"))
        file_list[index] = svg_file

    return file_list


def get_kmeans_clusters(
    srce_image: cv.typing.MatLike, K: int
) -> Tuple[cv.typing.MatLike, cv.typing.MatLike]:
    start = time.time()

    image_data = srce_image.reshape((-1, 3))
    # print(len(np.unique(image_data, axis=0)), 'unique RGB values out of', image_data.shape[0], 'pixels')
    image_data = np.float32(image_data)

    # define criteria, number of clusters(K) and apply kmeans()
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 10, 3.0)
    compactness, color_labels, bgr_centers = cv.kmeans(
        image_data, K, None, criteria, 10, cv.KMEANS_RANDOM_CENTERS
    )
    logging.info(f"kmeans.compactness = {compactness}")

    bgr_centers = np.uint8(bgr_centers)

    logging.info(f"\nTime taken to get kmeans for image:" f" {int(time.time() - start)}s.")

    return color_labels, bgr_centers


# def sq(num: int) -> int:
#     return num * num


def colors_are_close(color1: LabColor, color2: LabColor) -> bool:
    cutoff = 3.0
    return delta_e_cie2000(color1, color2) < cutoff

    # return (
    #     sq(color1[0] - color2[0])
    #     + sq(color1[1] - color2[1])
    #     + sq(color1[2] - color2[2])
    #     < 18 * 18
    # )


def optimize_labels(
    label_colors_and_counts: LabelDict,
    color_labels: cv.typing.MatLike,
    bgr_centers: cv.typing.MatLike,
) -> Tuple[LabelDict, cv.typing.MatLike, cv.typing.MatLike]:
    new_label_colors_and_counts = {}
    new_color_labels = color_labels

    centers_to_remove = []
    for index in label_colors_and_counts:
        index_count = label_colors_and_counts[index][0]
        if index_count == 0:
            continue

        index_bgr_color = label_colors_and_counts[index][1]
        index_lab_color = label_colors_and_counts[index][2]
        for other_index in label_colors_and_counts:
            if index == other_index:
                continue
            other_index_count = label_colors_and_counts[other_index][0]
            if other_index_count == 0:
                continue
            other_index_bgr_color = label_colors_and_counts[other_index][1]
            other_index_lab_color = label_colors_and_counts[other_index][2]
            if colors_are_close(index_lab_color, other_index_lab_color):
                index_count = label_colors_and_counts[index][0]
                label_colors_and_counts[index] = (
                    index_count + other_index_count,
                    index_bgr_color,
                    index_lab_color,
                )
                label_colors_and_counts[other_index] = (
                    0,
                    other_index_bgr_color,
                    other_index_lab_color,
                )
                new_color_labels = np.where(
                    new_color_labels == other_index, index, new_color_labels
                )
                centers_to_remove.append(other_index)

        new_label_colors_and_counts[index] = label_colors_and_counts[index]

    new_bgr_centers = np.delete(bgr_centers, centers_to_remove, 0)

    return new_label_colors_and_counts, new_color_labels, new_bgr_centers


def generate_svg_files(
    image_shape: Tuple[int, ...],
    color_labels: cv.typing.MatLike,
    svg_file_list: Dict[int, Path],
) -> None:
    start = time.time()

    bw_centers = np.array([[0, 0, 0], [255, 255, 255]])
    bw_centers = np.uint8(bw_centers)

    # kernel = np.ones((3, 3), np.uint8)
    with concurrent.futures.ProcessPoolExecutor(2) as executor:
        for index in svg_file_list:
            executor.submit(
                generate_svg,
                image_shape,
                color_labels,
                index,
                bw_centers,
                svg_file_list[index],
            )

    logging.info(
        f'\nTime taken to generate all {len(svg_file_list)} svg files":'
        f" {int(time.time() - start)}s."
    )


def generate_svg(
    image_shape: Tuple[int, ...],
    color_labels: cv.typing.MatLike,
    index: int,
    bw_centers: cv.typing.MatLike,
    svg_file: Path,
) -> None:
    start = time.time()

    single_color = np.where(color_labels == index, 0, 1)
    single_color_image = bw_centers[single_color.flatten()]
    # print(len(np.unique(res, axis=0)), 'unique RGB values out of', Z.shape[0], 'pixels')

    single_color_image = single_color_image.reshape(image_shape)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    single_color_image = cv.morphologyEx(single_color_image, cv.MORPH_OPEN, kernel)
    png_file = Path(svg_file).with_suffix(".png")
    cv.imwrite(str(png_file), single_color_image)

    blur_image_file(png_file, png_file)

    logging.info(f'Generating svg file "{svg_file}"...')
    image_file_to_svg(str(png_file), str(svg_file))

    logging.info(f'\nTime taken to generate "{svg_file}":' f" {int(time.time() - start)}s.")


def blur_image_file(in_file: Path, out_file: Path) -> None:
    blur_std_dev = 5  # nice smoothness
    blur_boundary_policy = 0  # 0 = Dirichlet (off-image pixels black); 1 = Neumann (off = edge)
    blur_kernel_type = 1  # 0 = quasi-Guassian; 1 = true Guassian
    blur_params = f"{blur_std_dev},{blur_boundary_policy},{blur_kernel_type}"

    threshold_percent = 50  # keeps color within black lines
    threshold_softness = 1  # 1 = 'soft' - also nice smoothness
    threshold_params = f"{threshold_percent}%,{threshold_softness}"

    gmic.run(
        f'"{in_file}"'
        f" -blur[-1] {blur_params}"
        f" -threshold[-1] {threshold_params} normalize[-1] 0,255"
        f' -output[-1] "{out_file}"'
    )


def get_layered_svg_file(
    label_colors_and_counts: LabelDict,
    svg_file_list: Dict[int, Path],
    black_ink_svg: Path,
    out_svg: Path,
) -> None:
    start = time.time()

    base_image = None
    for index in label_colors_and_counts:
        image_part = ET.parse(svg_file_list[index]).getroot()
        bgr_color = label_colors_and_counts[index][1]
        change_color(image_part, bgr_color)
        if base_image is None:
            base_image = image_part
        else:
            for elem in image_part:
                assert base_image is not None
                base_image.append(elem)

    image_part = ET.parse(black_ink_svg).getroot()
    for elem in image_part:
        base_image.append(elem)

    ET.ElementTree(base_image).write(out_svg)

    logging.info(
        f'\nTime taken to layer all {len(svg_file_list)} svg files":'
        f" {int(time.time() - start)}s."
    )


def get_label_colors_and_counts(
    color_labels: cv.typing.MatLike, bgr_centers: cv.typing.MatLike
) -> LabelDict:
    unique, counts = np.unique(color_labels, return_counts=True)
    label_counts = dict(zip(unique, counts))
    # Sort descending so color with higher count is layered first.
    label_counts = dict(sorted(label_counts.items(), key=lambda item: item[1], reverse=True))

    label_colors_and_counts = {}
    for label in label_counts:
        bgr_color = (
            int(bgr_centers[label][0]),
            int(bgr_centers[label][1]),
            int(bgr_centers[label][2]),
        )
        lab_color = convert_color(
            sRGBColor(bgr_color[2] / 255.0, bgr_color[1] / 255.0, bgr_color[0] / 255.0),
            LabColor,
        )
        label_colors_and_counts[int(label)] = (
            int(label_counts[label]),
            bgr_color,
            lab_color,
        )

    return label_colors_and_counts


def get_black_ink_image(
    srce_image: cv.typing.MatLike, black_mask: cv.typing.MatLike
) -> cv.typing.MatLike:
    # cv.imwrite("/tmp/mask.png", mask)
    _, _, _, black_alpha_mask = cv.split(black_mask)
    black_alpha_mask = np.uint8(black_alpha_mask)
    cv.imwrite("/tmp/black_alpha_mask.png", black_alpha_mask)

    b, g, r = cv.split(srce_image)
    b = np.where(black_alpha_mask == 255, COMIC_WHITE_B, b)
    g = np.where(black_alpha_mask == 255, COMIC_WHITE_G, g)
    r = np.where(black_alpha_mask == 255, COMIC_WHITE_R, r)

    return cv.merge([b, g, r])


def save_as_json(label_colors_and_counts: LabelDict, json_file: Path) -> None:
    def json_serialize(obj):
        if isinstance(obj, LabColor):
            return obj.lab_l, obj.lab_a, obj.lab_b
        return obj

    json_object = json.dumps(label_colors_and_counts, indent=4, default=json_serialize)

    with open(json_file, "w") as f:
        f.write(json_object)


if __name__ == "__main__":
    setup_logging(logging.INFO)

    srce_image_file = Path(sys.argv[1])
    black_ink_mask_file = Path(sys.argv[2])
    svg_black_ink_file = Path(sys.argv[3])
    svg_out_file = Path(os.path.join("/tmp", f"{srce_image_file.stem}-quantized.svg"))

    num_colors = 15

    image = cv.imread(str(srce_image_file))
    assert image.shape[2] == 3

    black_ink_mask = cv.imread(str(black_ink_mask_file), -1)
    assert black_ink_mask.shape[2] == 4
    black_ink_image = get_black_ink_image(image, black_ink_mask)

    labels, centers = get_kmeans_clusters(black_ink_image, num_colors)

    out_dir = os.path.dirname(svg_out_file)

    label_dict = get_label_colors_and_counts(labels, centers)
    label_json_file = Path(os.path.join(out_dir, f"{svg_out_file.stem}-unoptimized.json"))
    save_as_json(label_dict, label_json_file)
    print(centers)

    label_dict, labels, centers = optimize_labels(label_dict, labels, centers)
    label_json_file = svg_out_file.with_suffix(".json")
    save_as_json(label_dict, label_json_file)
    print(centers)

    svg_files = get_svg_files(out_dir, svg_out_file.stem, label_dict)

    generate_svg_files(image.shape, labels, svg_files)

    get_layered_svg_file(label_dict, svg_files, svg_black_ink_file, svg_out_file)
