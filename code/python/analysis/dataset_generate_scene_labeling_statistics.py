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

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_dir", required=True)
parser.add_argument("--analysis_dir", required=True)
parser.add_argument("--batch_name", required=True)
parser.add_argument("--scene_names")
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)
assert os.path.exists(args.analysis_dir)

path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: DATASET_GENERATE_SCENE_LABELING_STATISTICS] Begin...")



dataset_scenes_dir = os.path.join(args.dataset_dir, "scenes")

if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



metadata_camera_trajectories_csv_file = os.path.join(args.analysis_dir, "metadata_camera_trajectories.csv")
df_camera_trajectories = pd.read_csv(metadata_camera_trajectories_csv_file).rename_axis("camera_trajectory_id").reset_index().set_index("Animation")

df_columns = ["scene_name", "labeling_time_seconds", "scene_included_in_dataset"]
df = pd.DataFrame(columns=df_columns)

def process_scene(s, args):

    global df

    scene_name = s["name"]

    scene_dir  = os.path.join(dataset_scenes_dir, scene_name)
    detail_dir = os.path.join(scene_dir, "_detail")
    mesh_dir   = os.path.join(scene_dir, "_detail", "mesh")

    metadata_cameras_csv_file = os.path.join(detail_dir, "metadata_cameras.csv")
    df_cameras = pd.read_csv(metadata_cameras_csv_file)
    cameras = df_cameras.to_records()

    # check if scene has been flagged for exclusion
    scene_included_in_dataset = False
    for c in cameras:
        camera_trajectory_name = scene_name + "_" + c["camera_name"]
        scene_type = df_camera_trajectories.loc[camera_trajectory_name]["Scene type"]
        if scene_type != "OUTSIDE VIEWING AREA (BAD INITIALIZATION)" and scene_type != "OUTSIDE VIEWING AREA (BAD TRAJECTORY)":
            scene_included_in_dataset = True
            break

    if not scene_included_in_dataset:
        print("[HYPERSIM: DATASET_GENERATE_SCENE_LABELING_STATISTICS] No good camera trajectories for scene " + scene_name + ", setting scene_included_in_dataset to False...")

    log_file = os.path.join(mesh_dir, "metadata_scene_annotation_tool.log")

    if os.path.exists(log_file):

        with open(log_file, "r") as f:
            lines = f.readlines()
        num_lines = len(lines)

        loaded_prefix_str   = "[HYPERSIM: SCENE_ANNOTATION_TOOL] Loaded scene:   "
        unloaded_prefix_str = "[HYPERSIM: SCENE_ANNOTATION_TOOL] Unloaded scene: "

        labeling_time_seconds = 0.0
        loaded_line           = ""
        unloaded_line         = ""

        for l in lines:

            assert loaded_prefix_str in l or unloaded_prefix_str in l

            if loaded_prefix_str in l:
                loaded_line = l

            elif unloaded_prefix_str in l:

                unloaded_line = l
                
                if loaded_prefix_str in loaded_line:

                    loaded_time_str   = loaded_line[len(loaded_prefix_str):].strip()
                    unloaded_time_str = unloaded_line[len(unloaded_prefix_str):].strip()
                            
                    loaded_time   = datetime.datetime.strptime(loaded_time_str,   "%a %b %d %H:%M:%S %Y")
                    unloaded_time = datetime.datetime.strptime(unloaded_time_str, "%a %b %d %H:%M:%S %Y")

                    labeling_time_seconds += (unloaded_time - loaded_time).total_seconds()
                    loaded_line   = ""
                    unloaded_line = ""

                else:
                    print("[HYPERSIM: DATASET_GENERATE_SCENE_LABELING_STATISTICS] WARNING: ENCOUNTERED UNLOAD TIME WITHOUT CORRESPONDING LOAD TIME...")
                
            else:
                print("[HYPERSIM: DATASET_GENERATE_SCENE_LABELING_STATISTICS] WARNING: UNEXPECTED LINE: " + l)

        df_curr = pd.DataFrame(columns=df_columns, data={"scene_name":[scene_name], "labeling_time_seconds":[labeling_time_seconds], "scene_included_in_dataset":[scene_included_in_dataset]})
        df = df.append(df_curr, ignore_index=True)

        labeling_time_minutes = labeling_time_seconds/60.0
        print("[HYPERSIM: DATASET_GENERATE_SCENE_LABELING_STATISTICS] " + scene_name + " (labeling time minutes = " + str(labeling_time_minutes) + ")")

    else:
        print("[HYPERSIM: DATASET_GENERATE_SCENE_LABELING_STATISTICS] WARNING: LOG FILE DOESN'T EXIST FOR SCENE: " + scene_name)



for s in scenes:
    process_scene(s, args)



batch_dir = os.path.join(args.analysis_dir, "scene_labeling_statistics", args.batch_name)
if not os.path.exists(batch_dir): os.makedirs(batch_dir)
metadata_labeling_time_csv_file = os.path.join(batch_dir, "metadata_scene_labeling_time.csv")

df.to_csv(metadata_labeling_time_csv_file, index=False)



print("[HYPERSIM: DATASET_GENERATE_SCENE_LABELING_STATISTICS] Finished.")
