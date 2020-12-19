#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import os
import pandas as pd

import path_utils

parser = argparse.ArgumentParser()
parser.add_argument("--analysis_dir", required=True)
args = parser.parse_args()

assert os.path.exists(args.analysis_dir)



print("[HYPERSIM: DATASET_GENERATE_IMAGE_METADATA] Begin...")



num_images_per_camera_trajectory = 100

metadata_images_flagged_txt_file = os.path.join(args.analysis_dir, "metadata_images_flagged.txt")
metadata_images_csv_file         = os.path.join(args.analysis_dir, "metadata_images.csv")

metadata_camera_trajectories_csv_file = os.path.join(args.analysis_dir, "metadata_camera_trajectories.csv")
df_camera_trajectories = pd.read_csv(metadata_camera_trajectories_csv_file).rename_axis("camera_trajectory_id")
camera_trajectories = df_camera_trajectories.to_records()



# initialize dict of lists for frames to exclude
frames_ids_excluded_flagged = {}

for c in camera_trajectories:

    animation_name = c["Animation"]

    scene_name  = animation_name[0:10]
    camera_name = animation_name[11:17]

    assert scene_name.startswith("ai_")
    assert camera_name.startswith("cam_")

    frames_ids_excluded_flagged[(scene_name, camera_name)] = []



# fill lists of frames to exclude
scene_name_current  = None
camera_name_current = None
frame_id_current    = None

for line in open(metadata_images_flagged_txt_file, "r"):

    line = line.strip()

    assert line == "" or line.startswith("ai_") or line.startswith("scene_cam_") or line.startswith("frame.")

    if line == "":
        continue
    if line.startswith("ai_"):
        scene_name_current = line[0:10]
    if line.startswith("scene_cam_"):
        camera_name_current = line[6:12]
    if line.startswith("frame."):
        assert scene_name_current is not None and camera_name_current is not None
        frame_id_current = int(line[6:10])
        frames_ids_excluded_flagged[(scene_name_current, camera_name_current)].append(frame_id_current)



# create dataframe
df_columns = ["scene_name", "camera_name", "frame_id", "included_in_public_release", "exclude_reason"]
df = pd.DataFrame(columns=df_columns)

for c in camera_trajectories:

    animation_name = c["Animation"]

    scene_name  = animation_name[0:10]
    camera_name = animation_name[11:17]

    assert scene_name.startswith("ai_")
    assert camera_name.startswith("cam_")

    print("[HYPERSIM: DATASET_GENERATE_IMAGE_METADATA] Processing scene: " + scene_name)

    scene_names  = [ scene_name for i in range(num_images_per_camera_trajectory) ]
    camera_names = [ camera_name for i in range(num_images_per_camera_trajectory) ]
    frame_ids    = range(num_images_per_camera_trajectory)

    if c["Scene type"] == "OUTSIDE VIEWING AREA (BAD INITIALIZATION)":
        included_in_public_release = [ False for i in range(num_images_per_camera_trajectory) ]
        exclude_reason             = [ "OUTSIDE VIEWING AREA (BAD INITIALIZATION)" for i in range(num_images_per_camera_trajectory) ]
    elif c["Scene type"] == "OUTSIDE VIEWING AREA (BAD TRAJECTORY)":
        included_in_public_release = [ False for i in range(num_images_per_camera_trajectory) ]
        exclude_reason             = [ "OUTSIDE VIEWING AREA (BAD TRAJECTORY)" for i in range(num_images_per_camera_trajectory) ]
    else:
        frames_ids_excluded_flagged_ = array(frames_ids_excluded_flagged[(scene_name, camera_name)])
        included_in_public_release   = logical_not(in1d(frame_ids, frames_ids_excluded_flagged_))
        exclude_reason               = [ "" if included_in_public_release[i] else "CONTENT FLAGGED FOR REMOVAL" for i in range(num_images_per_camera_trajectory) ]

    df_ = pd.DataFrame(
        columns=df_columns,
        data={"scene_name"                 : scene_names,
              "camera_name"                : camera_names,
              "frame_id"                   : frame_ids,
              "included_in_public_release" : included_in_public_release,
              "exclude_reason"             : exclude_reason})

    df = df.append(df_)

included_in_public_release_counts = df.included_in_public_release.value_counts()
print("[HYPERSIM: DATASET_GENERATE_IMAGE_METADATA] Images included in public release: " + str(included_in_public_release_counts[True]))



df.to_csv(metadata_images_csv_file, index=False)



print("[HYPERSIM: DATASET_GENERATE_IMAGE_METADATA] Finished.")
