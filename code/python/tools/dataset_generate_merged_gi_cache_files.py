#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import fnmatch
import inspect
import os
import pandas as pd

import path_utils
path_utils.add_path_to_sys_path("..", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import _system_config

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_dir", required=True)
parser.add_argument("--scene_names")
parser.add_argument("--camera_names")
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)

path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: DATASET_GENERATE_MERGED_GI_CACHE_FILES] Begin...")



in_scene_fileroot  = "scene"
dataset_scenes_dir = os.path.join(args.dataset_dir, "scenes")

if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



for s in scenes:

    scene_name = s["name"]
    detail_dir = os.path.join(dataset_scenes_dir, scene_name, "_detail")

    metadata_cameras_csv_file = os.path.join(detail_dir, "metadata_cameras.csv")
    df = pd.read_csv(metadata_cameras_csv_file)

    if args.camera_names is not None:
        cameras = [ c for c in df.to_records() if fnmatch.fnmatch(c["camera_name"], args.camera_names) ]
    else:
        cameras = df.to_records()

    for c in cameras:

        camera_name = c["camera_name"]

        print("[HYPERSIM: DATASET_GENERATE_MERGED_GI_CACHE_FILES] For scene " + scene_name + ", generating merged GI cache files for camera " + camera_name + "...")

        #
        # generate merged GI cache files
        #

        in_irradiance_map_files = '"' + os.path.abspath(os.path.join(detail_dir, in_scene_fileroot + "_" + camera_name + "_shared", "_hypersim_irradiance_map.*.vrmap")) + '"'
        in_light_cache_files    = '"' + os.path.abspath(os.path.join(detail_dir, in_scene_fileroot + "_" + camera_name + "_shared", "_hypersim_light_cache.*.vrlmap")) + '"'
        out_irradiance_map_file = os.path.abspath(os.path.join(detail_dir, in_scene_fileroot + "_" + camera_name + "_shared", "_hypersim_irradiance_map.vrmap"))
        out_light_cache_file    = os.path.abspath(os.path.join(detail_dir, in_scene_fileroot + "_" + camera_name + "_shared", "_hypersim_light_cache.vrlmap"))

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " generate_merged_gi_cache_files.py" + \
            " --in_irradiance_map_files " + in_irradiance_map_files + \
            " --in_light_cache_files "    + in_light_cache_files    + \
            " --out_irradiance_map_file " + out_irradiance_map_file + \
            " --out_light_cache_file "    + out_light_cache_file
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)



print("[HYPERSIM: DATASET_GENERATE_MERGED_GI_CACHE_FILES] Finished.")
