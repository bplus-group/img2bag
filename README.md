<!-- PROJECT LOGO -->
<br/>
<div align="center">
  <a href="https://www.b-plus.com/de/home">
    <img src="https://www.b-plus.com/fileadmin/data_storage/images/b-plus_Logo.png" alt="Logo" width="150" height="150">
  </a>

  <h3 align="center">img2bag</h3>

  <p align="center">
    Command-line utility for converting images to ROS2 bag files
    <br/>
    <a href="#quickstart">Quickstart</a>
    ·
    <a href="https://github.com/bplus-group/img2bag/issues">Report Bug</a>
    ·
    <a href="https://github.com/bplus-group/img2bag/issues">Request Feature</a>
  </p>
</div>
<br/>

<!-- PROJECT SHIELDS -->
<div align="center">

  [![LinkedIn][linkedin-shield]][linkedin-url]
  [![Stars][star-shield]][star-url]

</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#quickstart">Quickstart</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#using-the-command-line-interface">Using the command-line interface</a></li>
      </ul>
    </li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>

---

# img2bag

## Quickstart

### Installation

With the use of the [rosbag2_py](https://index.ros.org/p/rosbag2_py/) library, you will need to have a ROS2 distribution
installed on your system. Additionally, *img2bag* requires an installation of Python 3.8+ and pip, along with the
following ROS2 packages:

```bash
ros-${ROS_DISTRO}-ros2bag
ros-${ROS_DISTRO}-rosbag2-storage-mcap
```

To install *img2bag* using pip:

- locate and download the latest `.whl` file from the [GitHub releases](https://github.com/bplus-group/img2bag/releases)
- run:

```bash
python3 -m pip install img2bag-<version>-py3-none-any.whl
```

- or without downloading:
```bash
python3 -m pip install https://github.com/bplus-group/img2bag/releases/download/<version>/img2bag-<version>-py3-none-any.whl
```

>[!NOTE]
>Replace `<version>` with the latest version number from the [GitHub releases](https://github.com/bplus-group/img2bag/releases)

From source:

```bash
python3 -m pip install git+https://github.com/bplus-group/img2bag
```

As a 0-dependency (except for ROS2 and appropriate ROS2 packages) [zipapp](https://docs.python.org/3/library/zipapp.html):

- locate and download the `.pyz` file from the [GitHub releases](https://github.com/bplus-group/img2bag/releases)
- run `python3 img2bag-#.#.#.pyz` ... in place of `img2bag` ...

<p align="right"><a href="#top">Back to top</a></p>

### Using the command-line interface

**basic example**

```bash
img2bag --directories=[./images] --topics=[/image] --output mybag
```

> [!NOTE]
> Images within the directories are sorted using natural order respecting the file paths with OS-Generated names.
>
> e.g.:
> ```bash
> img2bag --directories=[./images] --topics=[/image] --recursive-dirs --output mybag
> ```
>
> ```plaintext
> ./images/1.png
> ./images/2.png
> ./images/3.png
> ./images/subfolder/subfolder_2/001.png
> ./images/subfolder/subfolder_2/2.png
> ./images/subfolder/subfolder_2/03.png
> ./images/subfolder/subfolder_3/1.png
> ./images/subfolder/subfolder_3/image2.png
> ./images/subfolder/subfolder_3/image 3.png
> ./images/subfolder/subfolder (4)/1738915422.288516.png
> ./images/subfolder/subfolder (4)/1738915434.2312446.png
> ./images/subfolder/subfolder (4)/1738915444.8668082.png
> ```

```plaintext
Working on topic '/image' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:17

Saved ROS bag file to '/mybag'.
```

**advanced example**
  - process images from multiple directories
  - upscale/downscale images to a width of 1280 pixels while maintaining aspect ratio
  - publish images at a rate of 5 Hz
  - save the bag file in SQLite3 format

```bash
img2bag --directories=[./images_1,./images_2] \
        --topics=[/sensor/camera_1/image,/sensor/camera_2/image] \
        --image-size=1280 \
        --rate=5 \
        --format SQLITE3 \
        --output mybag
```

```plaintext
[INFO] [1738647810.973381809] [rosbag2_storage]: Opened database '/mybag/mybag_0.db3' for READ_WRITE.
Working on topic '/sensor/camera_1/image' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:09
Working on topic '/sensor/camera_2/image' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:10

Saved ROS bag file to '/mybag'.
```

#### Using a configuration file
Instead of specifying parameters in the command line, you can define them in a configuration file for easier reuse and
better readability.

##### Generating a Configuration File
To create a template configuration file, run:

```bash
img2bag --print_config > config.yaml
```

Example configuration file (`config.yaml`):

```yaml
verbose: false                     # Enable verbose output (optional)
directories: null                  # List of image directories (required)
topics: null                       # List of ROS topics to publish images under (required)
camera_info_topic: camera_info     # Topic for camera info messages (optional)
image_size: null                   # Resize images (e.g., 1280 or 1920x1080, optional)
timestamp: 1738648875              # Timestamp for images [Unix epoch time] (optional)
rate: 1.0                          # Image publishing rate [Hz] (optional)
recursive_dirs: false              # Recursively search directories for images (optional)
output: null                       # output bag file name (required)
format: MCAP                       # Storage format [SQLITE3, MCAP] (optional)
```

##### Using a Configuration File
Once configured, run the following command to generate a bag file using the settings from `config.yaml`:

```bash
img2bag --config config.yaml
```

##### Overriding Configuration File Parameters
You can override specific parameters from the configuration file by passing them as command-line arguments.
For example, to change the image size and output filename while keeping other settings from `config.yaml`:

`config.yaml`:

```yaml
directories:
  - ./images_1
  - ./images_2
topics:
  - /sensor/camera_1/image
  - /sensor/camera_2/image
format: MCAP
```

```bash
img2bag --config config.yaml --image-size=1920x1080 --output mybag
```

#### Options

For more advanced options while converting:

```plaintext
  -h, --help            Show this help message and exit.
  --version             Print version and exit.
  --verbose             Enable verbose output. (default: False)
  --config CONFIG       Path to a configuration file in JSON or YAML format. This file can contain predefined arguments.
  --print_config[=flags]
                        Print the configuration after applying all other arguments and exit. The optional flags
                        customizes the output and are one or more keywords separated by comma. The supported flags are:
                        comments, skip_default, skip_null.
  --directories DIRECTORIES, --directories+ DIRECTORIES
                        List of directories containing images to be processed. The number of directories must match the
                        number of '--topics'. Usage: '--directories=[dir1,dir2]' or '--directories+=dir3' to append
                        another directory. Images within the directories are sorted using natural order respecting the
                        file paths with OS-Generated names. Quoting is required when specifying multiple directories
                        that are separated by commas and spaces. (required, type: List[Path_dr])
  --topics TOPICS, --topics+ TOPICS
                        List of topics to publish images under. Each topic corresponds to a directory specified in '--
                        directories'. Usage: '--topics=[topic1,topic2]' or '--topics+=topic3' to append another topic.
                        Quoting is required when specifying multiple topics that are separated by commas and spaces.
                        (required, type: List[str])
  -c CAMERA_INFO_TOPIC, --camera-info-topic CAMERA_INFO_TOPIC
                        Name of the camera info topic to include in the bag file. (type: CameraInfoTopicType, default:
                        camera_info)
  -s IMAGE_SIZE, --image-size IMAGE_SIZE
                        Specify image size. Use "WIDTH" to maintain aspect ratio, or "WIDTHxHEIGHT" | "WIDTH,HEIGHT" to
                        specify dimensions. Both WIDTH and HEIGHT must be positive integers greater than zero. (type:
                        ImageSizeType, default: null)
  -ts TIMESTAMP, --timestamp TIMESTAMP
                        Starting timestamp (Unix epoch time in seconds) for the bag file. Defaults to the current system
                        time. (type: PositiveInt, default: 1739166685)
  -r RATE, --rate RATE  Playback rate of the image topics in frames per second (Hz). (type: PositiveFloat, default: 1.0)
  -rd, --recursive-dirs
                        Recursively search directories for images. (default: False)
  -o OUTPUT, --output OUTPUT
                        Path to save the output bag file. (required, type: Path_fc)
  -f {SQLITE3,MCAP}, --format {SQLITE3,MCAP}
                        Storage format for the output bag file. (type: StorageID, default: MCAP)
```
<p align="right"><a href="#top">Back to top</a></p>

## Contributing

If you have a suggestion that would improve this, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!


1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/NewFeature`)
3. Commit your Changes (`git commit -m 'Add some NewFeature'`)
4. Push to the Branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

<p align="right"><a href="#top">Back to top</a></p>

## License

All code, unless otherwise noted, is licensed under the MIT License. See [`LICENSE`](https://github.com/bplus-group/img2bag/blob/master/LICENSE) for more information.

<p align="right"><a href="#top">Back to top</a></p>


<!---Links And Images -->
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&color=808080
[linkedin-url]: https://de.linkedin.com/company/b-plus-group
[star-shield]: https://img.shields.io/github/stars/bplus-group/img2bag.svg?style=for-the-badge&color=144E73&labelColor=808080
[star-url]: https://github.com/bplus-group/img2bag
