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

from pathlib import Path
from pathlib import PurePath
from time import time
from typing import TYPE_CHECKING

import natsort
import numpy as np
from builtin_interfaces.msg import Time
from natsort import natsorted
from PIL import Image as PILImage
from rclpy.serialization import serialize_message
from rich import print as rprint
from rich.progress import track
from rosbag2_py import ConverterOptions
from rosbag2_py import SequentialWriter
from rosbag2_py import StorageOptions
from rosbag2_py import TopicMetadata
from sensor_msgs.msg import CameraInfo
from sensor_msgs.msg import Image
from std_msgs.msg import Header

from .enums import StorageID
from .utils import get_flatten_calibration_matrices
from .utils import get_frame_id_from_topic
from .utils import resize_image
from .utils import split_unix_timestamp

if TYPE_CHECKING:
    from collections.abc import Sequence


class Img2BagConverter:
    """
    Converts a sequence of images into a ROS 2 bag file.

    Parameters
    ----------
    image_topic_pairs : Sequence[tuple[Path | str, str]]
        A sequence of tuples, where each tuple consists of an image directory
        path and the corresponding image topic name.
    """

    def __init__(self, image_topic_pairs: Sequence[tuple[Path | str, str]]) -> None:
        self._image_topic_pairs = image_topic_pairs
        self._rosbag_writer: SequentialWriter

        self._verbose: bool = False
        self._camera_info_topic: str = 'camera_info'
        self._imgsz: tuple[int, int] | None = None
        self._start_timestamp: float = time()
        self._rate: float = 1.0
        self._recursive_dirs: bool = False
        self._storage_id: StorageID = StorageID.MCAP

    @property
    def verbose(self) -> bool:
        """
        Get the verbosity flag for enabling detailed output.

        Returns
        -------
        bool
            `True` if verbose output is enabled, `False` otherwise.
        """
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool) -> None:  # numpydoc ignore=GL08
        self._verbose = value

    @property
    def image_size(self) -> tuple[int, int] | None:
        """
        Get the target image size for resizing.

        If one dimension is <= 0, the other is adjusted to maintain the aspect ratio.

        Returns
        -------
        tuple[int, int] | None
            The target (width, height) for resizing, or `None` if resizing is disabled.
        """
        return self._imgsz

    @image_size.setter
    def image_size(self, value: tuple[int, int] | None) -> None:  # numpydoc ignore=GL08
        self._imgsz = value

    @property
    def start_timestamp(self) -> float:
        """
        Get the Unix timestamp marking the start of the bag file.

        Returns
        -------
        float
            The start timestamp in Unix epoch time (seconds).
        """
        return self._start_timestamp

    @start_timestamp.setter
    def start_timestamp(self, value: float) -> None:  # numpydoc ignore=GL08
        self._start_timestamp = value

    @property
    def rate(self) -> float:
        """
        Get the playback rate for the image topics in frames per second (Hz).

        Returns
        -------
        float
            The playback rate in Hz.
        """
        return self._rate

    @rate.setter
    def rate(self, value: float) -> None:  # numpydoc ignore=GL08
        self._rate = abs(value)

    @property
    def camera_info_topic(self) -> str:
        """
        Get the topic name for publishing camera info messages.

        Returns
        -------
        str
            The camera info topic name.
        """
        return self._camera_info_topic

    @camera_info_topic.setter
    def camera_info_topic(self, value: str) -> None:  # numpydoc ignore=GL08
        self._camera_info_topic = value

    @property
    def recursive_dirs(self) -> bool:
        """
        Get the flag indicating whether to recursively search for images in subdirectories.

        Returns
        -------
        bool
            `True` if subdirectories should be searched, `False` otherwise.
        """
        return self._recursive_dirs

    @recursive_dirs.setter
    def recursive_dirs(self, value: bool) -> None:  # numpydoc ignore=GL08
        self._recursive_dirs = value

    @property
    def storage_id(self) -> StorageID:
        """
        Get the storage backend used for the ROS bag file.

        Returns
        -------
        StorageID
            The selected storage backend (e.g., `StorageID.SQLITE3` or `StorageID.MCAP`).
        """
        return self._storage_id

    @storage_id.setter
    def storage_id(self, value: StorageID) -> None:  # numpydoc ignore=GL08
        self._storage_id = value

    def _register_topics(self, frame_id: str, img_topic: str) -> tuple[str, str]:
        """
        Register image and camera info topics with the rosbag writer.

        Parameters
        ----------
        frame_id : str
            The frame ID for the topics.
        img_topic : str
            The name of the image topic.

        Returns
        -------
        tuple[str, str]
            The full names of the image and camera info topics.
        """
        camera_info_topic_name = str(PurePath(f'/{frame_id}', self._camera_info_topic))
        image_topic_name = f'/{img_topic.lstrip("/")}'

        self._rosbag_writer.create_topic(
            TopicMetadata(name=image_topic_name, type='sensor_msgs/msg/Image', serialization_format='cdr'),
        )
        self._rosbag_writer.create_topic(
            TopicMetadata(name=camera_info_topic_name, type='sensor_msgs/msg/CameraInfo', serialization_format='cdr'),
        )

        return image_topic_name, camera_info_topic_name

    def _create_image_camera_info_messages(self, file_path: Path, header: Header) -> tuple[Image, CameraInfo]:
        """
        Generate image and camera info messages from an image file.

        Parameters
        ----------
        file_path : Path
            Path to the image file.
        header : Header
            ROS message header containing timestamp and frame ID.

        Returns
        -------
        tuple[Image, CameraInfo]
            Image message and corresponding camera info message.
        """
        with PILImage.open(file_path) as img_org:
            img = resize_image(img_org, self._imgsz) if self._imgsz else img_org

            image_encoding_map = {
                'RGB': 'rgb8',
                'RGBA': 'rgba8',
                'L': 'mono8',
            }
            if img.mode not in image_encoding_map:
                msg = f"Unsupported image mode '{img.mode}' for file '{file_path}'. Skipping..."
                raise UserWarning(msg)

            img_msg = Image(
                header=header,
                height=img.height,
                width=img.width,
                encoding=image_encoding_map.get(img.mode, 'rgb8'),
                is_bigendian=False,
                step=img.width * len(img.getbands()),
                data=np.frombuffer(img.tobytes(), dtype=np.uint8),
            )

            d, k, r, p = get_flatten_calibration_matrices(img.size)
            camera_info_msg = CameraInfo(
                header=header,
                height=img.height,
                width=img.width,
                distortion_model='plumb_bob',
                d=d,
                k=k,
                r=r,
                p=p,
            )

        return img_msg, camera_info_msg

    def _convert_image_to_topic(self, image_dir: Path, topic: str) -> None:
        """
        Convert images from a directory into a ROS bag topic.

        Parameters
        ----------
        image_dir : Path
            Directory containing the images to convert.
        topic : str
            Name of the ROS image topic.
        """
        frame_id = get_frame_id_from_topic(topic)

        image_topic_name, camera_info_topic_name = self._register_topics(frame_id, topic)
        sec, nsec = split_unix_timestamp(self._start_timestamp)

        image_files = [
            f
            for f in (Path(image_dir).rglob('**/*') if self._recursive_dirs else Path(image_dir).iterdir())
            if f.is_file()
        ]
        image_files = natsorted(
            image_files,
            key=lambda s: (str(s.absolute()).replace(' ', '_'), s.name),
            alg=natsort.ns.PATH | natsort.ns.IGNORECASE | natsort.ns.REAL,
        )

        for file_path in track(
            image_files,
            description=f"Working on topic '{image_topic_name}'",
            total=len(image_files),
        ):
            if self._verbose:
                rprint(f"Parsing: '{file_path}'")

            header = Header(stamp=Time(sec=sec, nanosec=nsec), frame_id=frame_id)
            try:
                img_msg, camera_info_msg = self._create_image_camera_info_messages(file_path, header)
            except (OSError, SyntaxError, UserWarning) as e:
                rprint(f"[yellow]WARNING: '{e}'[/yellow]")
                continue

            timestamp = int(sec * 1e9 + nsec)
            self._rosbag_writer.write(image_topic_name, serialize_message(img_msg), timestamp)
            self._rosbag_writer.write(camera_info_topic_name, serialize_message(camera_info_msg), timestamp)

            sec, nsec = split_unix_timestamp((sec + 1 / self._rate) + nsec * 1e-9)

    def convert(self, output: Path | str) -> None:
        """
        Convert the specified image directories into a ROS bag file.

        Parameters
        ----------
        output : Path | str
            The output path for the generated ROS bag file.
        """
        self._rosbag_writer = SequentialWriter()
        self._rosbag_writer.open(
            StorageOptions(uri=str(output), storage_id=self._storage_id.value),
            ConverterOptions(input_serialization_format='cdr', output_serialization_format='cdr'),
        )

        for image_dir, topic in self._image_topic_pairs:
            self._convert_image_to_topic(Path(image_dir), topic)

        rprint(f"\n[bold green]Saved ROS bag file to '{output}'.[/bold green]")

        del self._rosbag_writer
        self._rosbag_writer = None
