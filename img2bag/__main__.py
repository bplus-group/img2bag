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

import sys
from time import time
from typing import List

import jsonargparse
import jsonargparse.typing
from jsonargparse import ActionConfigFile
from jsonargparse import ArgumentParser
from jsonargparse import DefaultHelpFormatter
from jsonargparse import Namespace
from jsonargparse.typing import Path_fc
from jsonargparse.typing import PositiveFloat
from jsonargparse.typing import PositiveInt
from jsonargparse.typing import path_type
from jsonargparse.typing import restricted_string_type

from ._version import __version__
from .enums import StorageID

Path_dr = path_type('dr')


class _CustomHelpFormatter(DefaultHelpFormatter):
    def __init__(self, prog: str, width: int = 120):
        super().__init__(prog, width=width)


def _parse_arguments() -> Namespace:
    parser = ArgumentParser(formatter_class=_CustomHelpFormatter, version=__version__)

    parser.add_argument(
        '--config',
        action=ActionConfigFile,
        help='Path to a configuration file in JSON or YAML format. This file can contain predefined arguments.',
    )

    parser.add_argument(
        '--directories',
        type=List[Path_dr],  # type: ignore[valid-type]
        required=True,
        help=(
            'List of directories containing images to be processed. The number of directories must match the number of '
            "'--topics'. Usage: '--directories=[dir1,dir2]' or '--directories+=dir3' to append another directory. "
            'Quoting is required when specifying multiple directories that are separated by commas and spaces.'
        ),
    )

    parser.add_argument(
        '--topics',
        type=List[str],
        required=True,
        help=(
            'List of topics to publish images under. Each topic corresponds to a directory specified in '
            "'--directories'. Usage: '--topics=[topic1,topic2]' or '--topics+=topic3' to append another topic. "
            'Quoting is required when specifying multiple topics that are separated by commas and spaces.'
        ),
    )

    CameraInfoTopicType = restricted_string_type('CameraInfoTopicType', '^[A-Za-z/_]+$')  # noqa: N806
    parser.add_argument(
        '-c',
        '--camera-info-topic',
        type=CameraInfoTopicType,
        default='camera_info',
        help='Name of the camera info topic to include in the bag file.',
    )

    ImageSizeType = restricted_string_type('ImageSizeType', r'^(?!0$)(?!0[x,])\d+(?:[x,](?!0$)\d+)?$')  # noqa: N806
    parser.add_argument(
        '-s',
        '--image-size',
        type=ImageSizeType,
        help=(
            'Specify image size. Use "WIDTH" to maintain aspect ratio, or "WIDTHxHEIGHT" | "WIDTH,HEIGHT" to specify '
            'dimensions. Both WIDTH and HEIGHT must be positive integers greater than zero.'
        ),
    )

    parser.add_argument(
        '-ts',
        '--timestamp',
        type=PositiveInt,
        default=int(time()),
        help='Starting timestamp (Unix epoch time in seconds) for the bag file. Defaults to the current system time.',
    )

    parser.add_argument(
        '-r',
        '--rate',
        type=PositiveFloat,
        default=1.0,
        help='Playback rate of the image topics in frames per second (Hz).',
    )

    parser.add_argument(
        '-rd',
        '--recursive-dirs',
        action='store_true',
        default=False,
        help='Recursively search directories for images.',
    )

    parser.add_argument(
        '-o',
        '--output',
        type=Path_fc,
        required=True,
        help='Path to save the output bag file.',
    )

    parser.add_argument(
        '-f',
        '--format',
        type=StorageID,
        default=StorageID.MCAP,
        help='Storage format for the output bag file.',
    )

    args: Namespace = parser.parse_args()
    return args


def _parse_image_topic_pairs(directories: list[jsonargparse.typing.Path], topics: list[str]) -> list[tuple[str, str]]:  # type: ignore[name-defined]
    if len(directories) != len(topics):
        msg = (
            'Number of directories and topics must be equal, '
            f'but got {len(directories)} directories and {len(topics)} topics.'
        )
        raise ValueError(msg)

    return list(zip([d.absolute for d in directories], topics))


def _parse_image_size(image_size: str | None) -> tuple[int, int] | None:
    if not image_size:
        return None

    import re

    size = tuple(map(int, re.split(r'[x,]', image_size)))
    return (size[0], 0) if len(size) == 1 else size[:2]  # type: ignore[return-value]


def main() -> int:
    try:
        args = _parse_arguments()

        from .img2bag_converter import Img2BagConverter

        converter = Img2BagConverter(_parse_image_topic_pairs(args.directories, args.topics))

        converter.image_size = _parse_image_size(args.image_size)
        converter.start_timestamp = args.timestamp
        converter.rate = args.rate
        converter.camera_info_topic = args.camera_info_topic
        converter.recursive_dirs = args.recursive_dirs
        converter.storage_id = StorageID(args.format)

        converter.convert(args.output.absolute)

    except KeyboardInterrupt:
        sys.stderr.write('\n')
        return 1
    except Exception as e:  # noqa: BLE001
        sys.stderr.write('Error:{} {}{}\n'.format('\033[91m', '\033[0m', e))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
