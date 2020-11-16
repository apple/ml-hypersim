#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import glob
import ntpath
import os
import posixpath
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("--in_file", required=True)
parser.add_argument("--out_file", required=True)
parser.add_argument("--include_files", required=True)
parser.add_argument("--shared_asset_dir", required=True)
parser.add_argument("--platform_when_rendering", required=True)
parser.add_argument("--shared_asset_dir_when_rendering", required=True)
args = parser.parse_args()

assert os.path.exists(args.in_file)
assert args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix" or args.platform_when_rendering == "windows"

if args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix":
    os_path_module_when_rendering = posixpath
else:
    os_path_module_when_rendering = ntpath



print("Begin...")



in_include_files = [ os.path.abspath(in_include_file) for in_include_file in sort(glob.glob(args.include_files)) ]

out_dir = os.path.dirname(args.out_file)
if out_dir == "":
    out_dir = "."

if not os.path.exists(out_dir): os.makedirs(out_dir)
if not os.path.exists(args.shared_asset_dir): os.makedirs(args.shared_asset_dir)



if os.path.abspath(args.in_file) != os.path.abspath(args.out_file):
    shutil.copy(args.in_file, args.out_file)



if len(in_include_files) == 0:
    print("No files to include.")

else:
    with open(args.out_file, "a") as f:

        include_header = "\n\n\n// [HYPERSIM: MODIFY_VRSCENE_INCLUDE_FILES]\n"
        f.write(include_header)

        in_include_files = [ os.path.abspath(in_include_file) for in_include_file in sort(glob.glob(args.include_files)) ]

        for in_include_file in in_include_files:

            include_filename                = os.path.basename(in_include_file)
            out_include_file                = os.path.join(args.shared_asset_dir, include_filename)
            out_include_file_when_rendering = os_path_module_when_rendering.join(args.shared_asset_dir_when_rendering, include_filename)

            if os.path.abspath(in_include_file) != os.path.abspath(out_include_file):
                shutil.copy(in_include_file, out_include_file)

            include_text = '#include "' + out_include_file_when_rendering + '"\n'
            f.write(include_text)



print("Finished.")
