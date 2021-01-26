#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import os
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--analysis_dir", required=True)
args = parser.parse_args()



print("[HYPERSIM: VISUALIZE_CAMERA_TRAJECTORY_STATISTICS] Begin...")



metadata_camera_trajectories_csv_file = os.path.join(args.analysis_dir, "metadata_camera_trajectories.csv")

df = pd.read_csv(metadata_camera_trajectories_csv_file)
camera_trajectories = df.to_records()

scene_types = [
    "Living room",
    "Dining room",
    "Kitchen",
    "Bedroom",
    "Bathroom",
    "Office (home)",
    "Office",
    "Office (waiting area)",
    "Office (building foyer)",
    "Office (conference room)",
    "Restaurant",
    "Retail space",
    "Hotel lobby",
    "Hall",
    "Transit station",
    "Lecture theater",
    "Library",
    "Art gallery",
    "Courtyard",
    "Staircase",
    "Hallway",
    "Other",
    "OUTSIDE VIEWING AREA (BAD INITIALIZATION)",
    "OUTSIDE VIEWING AREA (BAD TRAJECTORY)" ]

scene_type_name_to_id_map = dict([ (scene_types[i],i) for i in range(len(scene_types)) ])
scene_type_id_to_name_map = dict([ (i,scene_types[i]) for i in range(len(scene_types)) ])

scene_type_names = [ c["Scene type"] for c in camera_trajectories ]
scene_type_ids   = [ scene_type_name_to_id_map[n] for n in scene_type_names ]

scene_type_hist_n_bins         = len(scene_type_id_to_name_map)
scene_type_hist_min_bin_center = 0
scene_type_hist_max_bin_center = len(scene_type_id_to_name_map)-1

H, H_edges = histogram(scene_type_ids, bins=scene_type_hist_n_bins, range=(scene_type_hist_min_bin_center - 0.5, scene_type_hist_max_bin_center + 0.5))

tick_label = [ scene_type_id_to_name_map[i] for i in sort(list(scene_type_id_to_name_map.keys())) ]
barh(arange(scene_type_hist_min_bin_center, scene_type_hist_max_bin_center+1), H, tick_label=tick_label)
gca().invert_yaxis()
title("Distribution of scene types")
xlabel("Frequency")
ylabel("Scene type")
show()



print("[HYPERSIM: VISUALIZE_CAMERA_TRAJECTORY_STATISTICS] Finished.")
