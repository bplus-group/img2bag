# MIT License

# Copyright (c) 2025 b-plus technologies GmbH

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# numpydoc ignore=GL08
from __future__ import annotations

import re
from pathlib import Path
from pathlib import PurePath

import numpy as np
import numpy.typing as npt
from PIL import Image as PILImage


def get_frame_id_from_topic(topic: str) -> str:
    """
    Get the frame ID from a topic.

    Parameters
    ----------
    topic : str
        The topic string.

    Returns
    -------
    str
        The frame ID.
    """
    topic_parts = topic.strip('/').split('/')[:-1]
    if not topic_parts:
        return str(PurePath(*topic.strip('/').split('/')))

    return str(PurePath(*topic_parts))


def split_unix_timestamp(timestamp: float) -> tuple[int, int]:
    """
    Split UNIX timestamp into seconds and nanoseconds.

    Parameters
    ----------
    timestamp : float
        A UNIX timestamp in float format.

    Returns
    -------
    Tuple[int, int]
        A tuple of integers representing the seconds
        and nanoseconds of the timestamp respectively.
    """
    sec: int = int(timestamp)
    nsec: int = int((timestamp * 1e9) % 1e9)

    return (sec, nsec)


def natural_sort_key(file: Path | str) -> list[int | str]:
    """
    Generate a sort key for file names to neable natural ordering.

    Parameters
    ----------
    file : Path | str
        The file path or file name to generate the sorting key for.

    Returns
    -------
    list[int | str]
        A list of integers and strings representing the decomposed components
        of the file name.
    """
    parts = re.split(r'(\d+)', str(file))
    return [int(part) if part.isdigit() else part for part in parts]


def pure_pil_alpha_to_color(image: PILImage.Image, color: tuple[int, int, int] = (0, 0, 0)) -> PILImage.Image:
    """
    Alpha composite an RGBA Image with a specified color.

    Simpler, faster version than the solutions above.

    Source: http://stackoverflow.com/a/9459208/284318

    Parameters
    ----------
    image : PILImage.Image
        The image to be converted.
    color : Tuple[int, int, int], optional
        The color r, g, b to be converted to, by default (0, 0, 0).

    Returns
    -------
    PILImage.Image
        The converted image.
    """
    image.load()  # needed for split()
    background = PILImage.new('RGB', image.size, color)
    background.paste(image, mask=image.split()[3])  # 3 is the alpha channel
    return background


def resize_image(image: PILImage.Image, size: tuple[int, int]) -> PILImage.Image:
    """
    Resize an image to the specified size. If one of the dimensions is 0,
    the other dimension is calculated to maintain the aspect ratio.

    Parameters
    ----------
    image : PILImage.Image
        The image to be resized.
    size : Tuple[int, int]
        The size to resize the image to.

    Returns
    -------
    PILImage.Image
        The resized image.
    """
    img_size = size
    if size[0] <= 0:
        img_size = (int(image.width * size[1] / image.height), size[1])
    elif size[1] <= 0:
        img_size = (size[0], int(image.height * size[0] / image.width))

    return image.resize(img_size)


def get_flatten_calibration_matrices(
    imgsz: tuple[int, int],
) -> tuple[
    npt.NDArray[np.float64],
    npt.NDArray[np.float64],
    npt.NDArray[np.float64],
    npt.NDArray[np.float64],
]:
    """
    Get the flatten calibration matrices for a camera with the specified image size.

    Parameters
    ----------
    imgsz : Tuple[int, int]
        A tuple of integers representing the image size.

    Returns
    -------
    Tuple[ndarray[np.float64], ...]
        A tuple of flattened numpy arrays representing
        the distortion, intrinsic, rotation, and projection matrices
        respectively.
    """
    d: npt.NDArray[np.float64] = np.zeros((5,), dtype=np.float64)  # distortion

    #     [fx   0  cx]
    # K = [ 0  fy  cy]
    #     [ 0   0   1]
    aspect_ratio = imgsz[1] / imgsz[0]

    K: npt.NDArray[np.float64] = np.identity(3, dtype=np.float64)  # intrinsic  # noqa: N806
    K[0, [0, 2]] = [imgsz[0], imgsz[0] / 2]
    K[1, [1, 2]] = [imgsz[1] / aspect_ratio, imgsz[1] / 2]

    R: npt.NDArray[np.float64] = np.identity(3, dtype=np.float64)  # rotation  # noqa: N806

    #     [fx   0  cx Tx]
    # P = [ 0  fy  cy Ty]
    #     [ 0   0   1  0]
    P = np.column_stack((K, np.zeros(3)))  # projection  # noqa: N806

    return d, K.flatten(), R.flatten(), P.flatten()
