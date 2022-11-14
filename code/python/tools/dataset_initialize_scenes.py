#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import distutils.dir_util
import glob
import fnmatch
import inspect
import os
import shutil

import path_utils
path_utils.add_path_to_sys_path("..", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import _system_config

assert _system_config.decompress_bin != ""
assert _system_config.asset_file_ext != ""

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_dir", required=True)
parser.add_argument("--downloads_dir", required=True)
parser.add_argument("--dataset_dir_to_copy")
parser.add_argument("--scene_names")
args = parser.parse_args()

assert os.path.exists(args.downloads_dir)

if args.dataset_dir_to_copy is not None:
    assert os.path.exists(args.dataset_dir_to_copy)



print("[HYPERSIM: DATASET_INITIALIZE_SCENES] Begin...")



if not os.path.exists(args.dataset_dir): os.makedirs(args.dataset_dir)



# Copy from dataset_dir_to_copy, which can be used to copy config files that are checked
# into a code repository. Note that we handle the "scenes" dir in a special case later in
# this file.
if args.dataset_dir_to_copy is not None:
    dataset_dir_copy_global_allow_list = ["_dataset_config.py", "_vray_user_params.py"]
    dataset_dir_to_copy_contents = sort(glob.glob(os.path.join(args.dataset_dir_to_copy, "*")))
    for c in dataset_dir_to_copy_contents:
        if os.path.basename(c) in dataset_dir_copy_global_allow_list:
            if os.path.isfile(c):
                print("[HYPERSIM: DATASET_INITIALIZE_SCENES] Copying " + c + "...")
                shutil.copy(c, args.dataset_dir)
            if os.path.isdir(c):
                print("[HYPERSIM: DATASET_INITIALIZE_SCENES] Copying " + c + "...")
                distutils.dir_util.copy_tree(c, args.dataset_dir) # can't use shutil.copytree because I want to overwrite files if they exist



# needs to happen after the initial copy step, because _dataset_config.py is probably among the files getting copied
path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



dataset_scenes_dir = os.path.join(args.dataset_dir, "scenes")

if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



for s in scenes:

    scene_name         = s["name"]
    scene_archive_file = s["archive_file"]
    scene_dir          = os.path.join(dataset_scenes_dir, scene_name)

    assert scene_archive_file != ""

    print("[HYPERSIM: DATASET_INITIALIZE_SCENES] Initializing scene: " + scene_name)

    # Handle the special case of copying the "scenes" dir here.
    if args.dataset_dir_to_copy is not None:
        scene_dir_to_copy = os.path.join(args.dataset_dir_to_copy, "scenes", scene_name)
        if os.path.exists(scene_dir_to_copy):
            print("[HYPERSIM: DATASET_INITIALIZE_SCENES] Copying " + scene_dir_to_copy + "...")
            distutils.dir_util.copy_tree(scene_dir_to_copy, scene_dir) # can't use shutil.copytree because I want to overwrite files if they exist

    scene_asset_dir = os.path.join(scene_dir, "_asset")

    if os.path.exists(scene_asset_dir):
        print("[HYPERSIM: DATASET_INITIALIZE_SCENES] Extract destination folder already exists, skipping...")

    else:
        os.makedirs(scene_asset_dir)

        in_file = os.path.join(args.downloads_dir, scene_archive_file)
        print("[HYPERSIM: DATASET_INITIALIZE_SCENES] Extracting " + in_file + "...")

        cmd = _system_config.decompress_bin + \
            " x " + '"' + in_file + '"' \
            " -o" + '"' + scene_asset_dir + '"'
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        asset_file = os.path.join(scene_asset_dir, s["asset_file"] + "." + _system_config.asset_file_ext)
        print("[HYPERSIM: DATASET_INITIALIZE_SCENES] Verifying that asset file exists: " + asset_file)
        assert os.path.exists(asset_file)

        print("")



print("[HYPERSIM: DATASET_INITIALIZE_SCENES] Finished.")
