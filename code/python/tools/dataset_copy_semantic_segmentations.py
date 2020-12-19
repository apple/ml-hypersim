#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import fnmatch
import inspect
import os
import shutil

import path_utils
path_utils.add_path_to_sys_path("..", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import _system_config

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_dir", required=True)
parser.add_argument("--dataset_dir_out", required=True)
parser.add_argument("--scene_names")
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)

path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: DATASET_COPY_SEMANTIC_SEGMENTATIONS] Begin...")



if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



for s in scenes:

    scene_name = s["name"]

    print("[HYPERSIM: DATASET_COPY_SEMANTIC_SEGMENTATIONS] Copying semantic segmentation data for scene: " + scene_name)

    mesh_dir     = os.path.join(args.dataset_dir, "scenes", scene_name, "_detail", "mesh")
    mesh_dir_out = os.path.join(args.dataset_dir_out, "scenes", scene_name, "_detail", "mesh")

    files_to_copy = [
        "mesh_objects_si.hdf5",
        "mesh_objects_sii.hdf5",
        "metadata_objects.csv",
        "metadata_scene_annotation_tool.log",
        "metadata_semantic_colors.hdf5",
        "metadata_semantic_instance_colors.hdf5"
    ]
    
    if not os.path.exists(mesh_dir_out):
        os.makedirs(mesh_dir_out)

    for f in files_to_copy:
        in_file  = os.path.abspath(os.path.join(mesh_dir, f))
        out_file = os.path.abspath(os.path.join(mesh_dir_out, f))
        shutil.copy(in_file, out_file)



print("[HYPERSIM: DATASET_COPY_SEMANTIC_SEGMENTATIONS] Finished.")
