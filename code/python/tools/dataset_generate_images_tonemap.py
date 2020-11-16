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
parser.add_argument("--n_jobs", type=int)
parser.add_argument("--use_single_threaded_reference_implementation", action="store_true")
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)

path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: DATASET_GENERATE_IMAGES_TONEMAP] Begin...")



if not args.use_single_threaded_reference_implementation:
    if args.n_jobs is not None:
        n_jobs = args.n_jobs
    else:
        n_jobs = 4 # 4 parallel jobs by default; more processes don't seem to offer much speed-up
        
dataset_scenes_dir = os.path.join(args.dataset_dir, "scenes")

if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



def process_scene(s, args):

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

        print("[HYPERSIM: DATASET_GENERATE_IMAGES_TONEMAP] For scene " + scene_name + ", generating tonemapped images for camera " + camera_name + "...")

        scene_dir = os.path.abspath(os.path.join(dataset_scenes_dir, scene_name))

        current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
        cwd = os.getcwd()
        os.chdir(current_source_file_path)

        cmd = \
            _system_config.python_bin + " scene_generate_images_tonemap.py" + \
            " --scene_dir "   + scene_dir + \
            " --camera_name " + camera_name
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0

        os.chdir(cwd)



if args.use_single_threaded_reference_implementation:
    for s in scenes:
        process_scene(s, args)

if not args.use_single_threaded_reference_implementation:
    from joblib import Parallel, delayed
    Parallel(n_jobs=n_jobs, verbose=10)(delayed(process_scene)(s, args) for s in scenes)



print("[HYPERSIM: DATASET_GENERATE_IMAGES_TONEMAP] Finished.")
