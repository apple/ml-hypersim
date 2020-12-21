#!/usr/bin/env python3
#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

import os
import argparse
import requests
import zipfile

# Increase download speed
zipfile.ZipExtFile.MIN_READ_SIZE = 2 ** 20


class WebFile:
    def __init__(self, url, session):
        with session.head(url) as response:
            size = int(response.headers["content-length"])

        self.url = url
        self.session = session
        self.offset = 0
        self.size = size

    def seekable(self):
        return True

    def tell(self):
        return self.offset

    def available(self):
        return self.size - self.offset

    def seek(self, offset, whence=0):
        if whence == 0:
            self.offset = offset
        elif whence == 1:
            self.offset = min(self.offset + offset, self.size)
        elif whence == 2:
            self.offset = max(0, self.size + offset)

    def read(self, n=None):
        if n is None:
            n = self.available()
        else:
            n = min(n, self.available())

        end_inclusive = self.offset + n - 1

        headers = {
            "Range": f"bytes={self.offset}-{end_inclusive}",
        }

        with self.session.get(self.url, headers=headers) as response:
            data = response.content

        self.offset += len(data)

        return data


URL_NUMBERS = {
    1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    2: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    3: [1, 2, 4, 5, 6, 7, 8, 9, 10],
    4: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    5: [1, 3, 4, 5, 6, 7, 8, 9, 10],
    6: [1, 2, 3, 4, 6, 7, 8, 9, 10],
    7: [1, 2, 4, 5, 6, 7, 8, 9, 10],
    8: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    9: [1, 2, 3, 4, 5, 6, 7, 8, 9],
    10: [1, 2, 3, 4, 5, 6, 7, 8, 9],
    11: [1, 3, 4, 5, 6, 7, 8, 9, 10],
    12: [1, 4, 5, 7, 9, 10],
    13: [1, 2, 3, 4, 7, 9, 10],
    14: [3, 6, 10],
    15: [1, 3, 4, 5, 6, 7, 8, 9, 10],
    16: [1, 2, 3, 4, 5, 6, 7, 9, 10],
    17: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    18: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    19: [1, 2, 3, 4, 6, 7, 8, 9],
    21: [1, 2, 3, 7, 8, 9, 10],
    22: [1, 2, 3, 4, 5, 6, 7, 9, 10],
    23: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    24: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
    26: [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    27: [1, 3, 4, 5, 6, 7, 8, 9, 10],
    28: [1, 2, 3, 4, 5, 6, 8, 9],
    29: [1, 2, 3, 4, 5],
    30: [1, 2, 3, 4, 5, 7, 8, 9, 10],
    31: [1, 3, 4, 6, 7, 8, 9, 10],
    32: [1, 2, 3, 4, 5, 7, 8, 9],
    33: [1, 2, 4, 5, 7, 8, 9, 10],
    34: [1, 2, 3, 5],
    35: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    36: [1, 2, 3, 5, 6, 7, 8, 10],
    37: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    38: [2, 4, 5, 6, 7, 9, 10],
    39: [2, 3, 4, 5, 6, 7, 8, 9, 10],
    41: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    42: [1, 2, 3, 4, 5],
    43: [2, 3, 4, 5, 6, 7, 8, 9, 10],
    44: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    45: [1, 4, 5, 6, 8, 10],
    46: [1, 2, 3, 4, 5, 6, 7, 8],
    47: [1, 2, 3, 4, 5, 6, 7, 8, 9],
    48: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    50: [1, 2, 3, 4, 5],
    51: [1, 2, 3, 4, 5],
    52: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    53: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 16, 17, 18, 19, 20],
    54: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    55: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
}


def list_urls():
    for i, numbers in URL_NUMBERS.items():
        for j in numbers:
            url = f"https://docs-assets.developer.apple.com/ml-research/datasets/hypersim/v1/scenes/ai_{i:03d}_{j:03d}.zip"

            yield url


def download_files(args):
    session = requests.session()

    # For each zip file
    for url in list_urls():
        f = WebFile(url, session)

        z = zipfile.ZipFile(f)

        # for each file in zip file
        for entry in z.infolist():

            # skip directories in zip file (will be created automatically)
            if entry.is_dir():
                continue

            path = os.path.join(args.directory, entry.filename)

            contains_all_words = all(
                word in entry.filename for words in args.contains for word in words
            )

            if contains_all_words:
                if os.path.isfile(path) and not args.overwrite:
                    print("File already exists:", path)
                else:
                    print("Downloading:", path)

                    z.extract(entry.filename, args.directory)
            else:
                if not args.silent:
                    print("Skipping:", path)


def main():
    epilog = """

download the first preview of each scene:

    ./dataset_download_images_partial.py --contains scene_cam_00_final_preview --contains frame.0000.color.jpg --silent

    """
    parser = argparse.ArgumentParser(
        epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default="downloads",
        help="directory to download to",
    )
    parser.add_argument(
        "-o", "--overwrite", action="store_true", help="overwrite existing files"
    )
    parser.add_argument(
        "-c",
        "--contains",
        nargs="*",
        action="append",
        default=[],
        help="only download file if name contains specific word(s)",
    )
    parser.add_argument(
        "-s", "--silent", action="store_true", help="only print downloaded files"
    )

    args = parser.parse_args()

    download_files(args)


if __name__ == "__main__":
    main()
