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
parser.add_argument("--num_images_to_select", required=True, type=int)
args = parser.parse_args()

assert os.path.exists(args.analysis_dir)



print("[HYPERSIM: DATASET_GENERATE_RANDOM_IMAGE_PATHS] Begin...")



metadata_camera_trajectories_csv_file = os.path.join(args.analysis_dir, "metadata_camera_trajectories.csv")

df = pd.read_csv(metadata_camera_trajectories_csv_file)
df = df[df["Scene type"] != "OUTSIDE VIEWING AREA (BAD TRAJECTORY)"]
df = df[df["Scene type"] != "OUTSIDE VIEWING AREA (BAD INITIALIZATION)"]
df = df.reset_index(drop=True)
camera_trajectories = df.to_records()

num_images_per_camera_trajectory = 100
num_images_to_select             = args.num_images_to_select
num_camera_trajectories          = len(camera_trajectories)

np.random.seed(0)

T = np.random.randint(0, num_camera_trajectories,          size=num_images_to_select)
F = np.random.randint(0, num_images_per_camera_trajectory, size=num_images_to_select)

i = 0
for ti,fi in zip(T,F):
    scene_name       = df.loc[ti]["Animation"][0:10]
    camera_name      = df.loc[ti]["Animation"][11:17]
    img_tonemap_file = os.path.join("scenes", scene_name, "images", "scene_" + camera_name + "_final_preview", "frame.%04d.tonemap.jpg" % fi)
    print(img_tonemap_file)



print("[HYPERSIM: DATASET_GENERATE_RANDOM_IMAGE_PATHS] Finished.")
