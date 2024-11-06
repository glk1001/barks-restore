import os
import time

import cv2 as cv
import numpy as np
from numba import jit

DEBUG = False
DEBUG_OUTPUT_DIR = "/tmp"

MEDIAN_BLUR_APERTURE_SIZE = 7
ADAPTIVE_THRESHOLD_BLOCK_SIZE = 21
ADAPTIVE_THRESHOLD_CONST_SUBTRACT = 12  # Careful here with including alias artifacts
SMALL_FLOAT = 0.0001

LOWER_HSV_BLACK_CUT = np.array([0, 0, 0])
HIGHER_HSV_BLACK_CUT = np.array(
    [360, 255, 150]
)  # getting this right important for thin lines


def _median_filter(
    original_image: cv.typing.MatLike, mask: cv.typing.MatLike, kernel_size: int
) -> cv.typing.MatLike:
    filtered_image = np.zeros_like(original_image)
    w = kernel_size // 2

    wrapped_image = cv.copyMakeBorder(
        original_image, w, w, w, w, cv.BORDER_CONSTANT, None, value=(255, 255, 255)
    )
    wrapped_mask = cv.copyMakeBorder(
        mask, w, w, w, w, cv.BORDER_CONSTANT, None, value=(255, 255, 255)
    )

    if DEBUG:
        cv.imwrite(
            os.path.join(DEBUG_OUTPUT_DIR, "wrapped-image.jpg"),
            wrapped_image,
        )
        cv.imwrite(
            os.path.join(DEBUG_OUTPUT_DIR, "wrapped-mask.jpg"),
            wrapped_mask,
        )

    _median_filter_core(wrapped_image, wrapped_mask, kernel_size, filtered_image)

    #    median_filter_core.parallel_diagnostics(level=4)

    return filtered_image


@jit(nopython=True, parallel=False)
def _median_filter_core(wrapped_image, wrapped_mask, kernel_size: int, filtered_image):
    image_h, image_w = filtered_image.shape[0], filtered_image.shape[1]
    w: int = kernel_size // 2

    nbrs0 = np.empty((kernel_size * kernel_size, 1), dtype=filtered_image.dtype)
    nbrs1 = np.empty((kernel_size * kernel_size, 1), dtype=filtered_image.dtype)
    nbrs2 = np.empty((kernel_size * kernel_size, 1), dtype=filtered_image.dtype)

    for i in range(w, image_h + w):
        for j in range(w, image_w + w):
            if wrapped_mask[i, j] > 0:
                filtered_image[i - w, j - w] = wrapped_image[i, j]
                continue
            num_nbrs = 0
            for x in range(i - w, i + w + 1):
                for y in range(j - w, j + w + 1):
                    if wrapped_mask[x, y] > 0:
                        continue
                    pixel = wrapped_image[x, y]
                    nbrs0[num_nbrs] = pixel[0]
                    nbrs1[num_nbrs] = pixel[1]
                    nbrs2[num_nbrs] = pixel[2]
                    num_nbrs += 1
            filtered_image[i - w, j - w] = _get_median(num_nbrs, nbrs0, nbrs1, nbrs2)


@jit(nopython=True, parallel=False)
def _get_median(num_nbrs: int, nbrs0, nbrs1, nbrs2):
    if num_nbrs == 0:
        return 0, 100, 0

    if num_nbrs == nbrs0.size:
        return np.median(nbrs0), np.median(nbrs1), np.median(nbrs2)

    return (
        np.median(nbrs0[:num_nbrs]),
        np.median(nbrs1[:num_nbrs]),
        np.median(nbrs2[:num_nbrs]),
    )


def get_median_filter(input_image: cv.typing.MatLike) -> cv.typing.MatLike:
    # color_removed_image = cv.cvtColor(input_image, cv.COLOR_BGR2HSV)
    # black_ink_mask = cv.inRange(
    #     color_removed_image, LOWER_HSV_BLACK_CUT, HIGHER_HSV_BLACK_CUT
    # )

    black_ink_mask = _get_black_ink_mask(input_image)
    if DEBUG:
        cv.imwrite(
            os.path.join(DEBUG_OUTPUT_DIR, "median-black-ink-mask.jpg"),
            black_ink_mask,
        )

    black_ink_mask_blurred_image = cv.GaussianBlur(255 - black_ink_mask, (3, 3), 0)

    ret, enlarged_black_ink_mask = cv.threshold(
        black_ink_mask_blurred_image, 200.0, 255, cv.THRESH_BINARY_INV
    )
    if DEBUG:
        cv.imwrite(
            os.path.join(DEBUG_OUTPUT_DIR, "enlarged-black-ink-mask-median.jpg"),
            enlarged_black_ink_mask,
        )

    filtered_image = _median_filter(
        input_image, enlarged_black_ink_mask, MEDIAN_BLUR_APERTURE_SIZE
    )
    if DEBUG:
        cv.imwrite(
            os.path.join(DEBUG_OUTPUT_DIR, "median-filtered-image.jpg"),
            filtered_image,
        )

    return filtered_image


def get_thickened_black_lines(
    input_image: cv.typing.MatLike, thicken_alpha: float
) -> cv.typing.MatLike:
    black_ink_mask = _get_black_ink_mask(input_image)
    if DEBUG:
        cv.imwrite(
            os.path.join(DEBUG_OUTPUT_DIR, "black-ink-mask.jpg"),
            black_ink_mask,
        )

    # black_ink_mask_blurred_image = black_ink_mask
    # black_ink_mask_blurred_image = cv.GaussianBlur(black_ink_mask, (3, 3), 0)
    # black_ink_mask_blurred_image = cv.blur(black_ink_mask, (2, 2), anchor=(-1,-1))
    # black_ink_mask_blurred_image = cv.bilateralFilter(black_ink_mask, 10, 80, 90)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (2, 2))
    black_ink_mask_blurred_image = cv.dilate(black_ink_mask, kernel, iterations=1)

    contours, hierarchy = cv.findContours(
        black_ink_mask_blurred_image, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE
    )
    black_ink_contours_mask = np.zeros_like(black_ink_mask_blurred_image)
    cv.drawContours(black_ink_contours_mask, contours, -1, (255, 255, 255), cv.FILLED)
    for c in contours:
        area = cv.contourArea(c)
        if area < 10:
            cv.drawContours(black_ink_contours_mask, [c], 0, (0, 0, 0), -1)
    # kernel = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))
    # black_ink_contours_mask = cv.erode(black_ink_contours_mask, kernel, iterations=1)
    if DEBUG:
        cv.imwrite(
            os.path.join(DEBUG_OUTPUT_DIR, "black-ink-contours-mask.jpg"),
            black_ink_contours_mask,
        )

    if DEBUG:
        black_ink_contours_outlines = np.zeros_like(black_ink_mask_blurred_image)
        cv.drawContours(black_ink_contours_outlines, contours, -1, (255, 255, 255), 1)
        cv.imwrite(
            os.path.join(DEBUG_OUTPUT_DIR, "black-ink-contours-outlines.jpg"),
            black_ink_contours_outlines,
        )

    filtered_image = input_image.copy()
    if DEBUG:
        cv.imwrite(
            os.path.join(DEBUG_OUTPUT_DIR, "filtered-image-1.jpg"), filtered_image
        )

    filtered_image[black_ink_contours_mask > 0] = (0, 0, 0)
    filtered_image = cv.GaussianBlur(filtered_image, (3, 3), sigmaX=0, sigmaY=0)
    # filtered_image = cv.blur(filtered_image, (2, 2), anchor=(-1,-1))
    if DEBUG:
        cv.imwrite(
            os.path.join(DEBUG_OUTPUT_DIR, "filtered-image-2.jpg"), filtered_image
        )

    alpha = thicken_alpha
    beta = 1.0 - alpha
    gamma = 0.0
    output_image = cv.addWeighted(filtered_image, alpha, input_image, beta, gamma)

    return output_image


def _get_black_ink_mask(image: cv.typing.MatLike) -> cv.typing.MatLike:
    gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    black_ink_mask = cv.adaptiveThreshold(
        gray_image,
        255,
        cv.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv.THRESH_BINARY_INV,
        ADAPTIVE_THRESHOLD_BLOCK_SIZE,
        ADAPTIVE_THRESHOLD_CONST_SUBTRACT,
    )

    # color_removed_image = cv.cvtColor(input_image, cv.COLOR_BGR2HSV)
    # black_ink_mask = cv.inRange(
    #     color_removed_image, LOWER_HSV_BLACK_CUT, HIGHER_HSV_BLACK_CUT
    # )

    return black_ink_mask


if __name__ == "__main__":
    DEBUG = True

    start_time = time.time()

    # src_image_file = (
    #     "/home/greg/Books/Carl Barks/Fantagraphics/"
    #     "Carl Barks Vol. 7 - Donald Duck - Lost in the Andes (Digital-Empire)/images/179.jpg"
    # )
    # src_image_file = "restore-tests/test-image-1.jpg"
    # src_image_file = "restore-tests/test-image-2.jpg"
    src_image_file = "restore-tests/test-image-3.jpg"
    # src_image_file = "restore-tests/simple-test-image.jpg"

    src_image = cv.imread(src_image_file)
    print(f"Src image shape: {src_image.shape}")

    median_filtered_image = get_median_filter(src_image)

    # thicken_line_alpha = 0.0  # depends on the comic - works for turk (test-image-1.jpg)
    thicken_line_alpha = (
        0.5  # depends on the comic - works for Sunken Yacht (test-image-2.jpg)
    )
    if thicken_line_alpha < SMALL_FLOAT:
        improved_image = median_filtered_image
    else:
        improved_image = get_thickened_black_lines(
            median_filtered_image, thicken_line_alpha
        )

    cv.imwrite(
        os.path.join(DEBUG_OUTPUT_DIR, "improved-image.jpg"),
        improved_image,
        [int(cv.IMWRITE_JPEG_QUALITY), 95],
    )

    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    print(f"Execution time: {elapsed_time} seconds")
