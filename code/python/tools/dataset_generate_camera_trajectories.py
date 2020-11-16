#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import fnmatch
import inspect
import os

import path_utils
path_utils.add_path_to_sys_path("..", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import _system_config

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_dir", required=True)
parser.add_argument("--scene_names")
parser.add_argument("--n_jobs", type=int)
parser.add_argument("--use_single_threaded_reference_implementation", action="store_true")
parser.add_argument("--use_python_reference_implementation", action="store_true")
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)

path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: DATASET_GENERATE_CAMERA_TRAJECTORIES] Begin...")



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
    scene_dir  = os.path.abspath(os.path.join(dataset_scenes_dir, scene_name))

    if args.use_python_reference_implementation:
        use_python_reference_implementation_str = "--use_python_reference_implementation"
    else:
        use_python_reference_implementation_str = ""

    current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
    cwd = os.getcwd()
    os.chdir(current_source_file_path)

    cmd = \
        _system_config.python_bin + " scene_generate_camera_trajectories_random_walk.py" + \
        " --scene_dir " + scene_dir + \
        " " + use_python_reference_implementation_str

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



print("[HYPERSIM: DATASET_GENERATE_CAMERA_TRAJECTORIES] Finished.")
